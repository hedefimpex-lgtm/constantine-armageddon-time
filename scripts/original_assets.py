"""Export the zone00 terrain mesh and one original SKYF member from a local installation."""
import argparse
from array import array
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ZONE_BYTES = 2048 * 2048
MASK_SHA256 = "0df71c6c7891704bf838957d10f57332d4ad3f5a8afb865f11a5cc14fda95faa"
HEIGHT_SHA256 = "7a22bc09b0ccca02c7fc75cf182e8cfdee8b777492e416667950c47f016ab34d"
OBJECTS_SHA256 = "fd72b8e69d5d811bc4e9e1ca9bcc200d21c71497128072de2e2ca0e65a75afb2"
INSTALLER_SHA256 = "6fcfaaf85872fd7b88ca9eecef3d865e595ebc48a879fe9a6369812e440411c8"
DIRECTORY = struct.Struct("<64sHH")
MEMBER = struct.Struct("<128sII")


@dataclass(frozen=True)
class Entry:
    path: str
    offset: int
    size: int


def digest(path):
    with path.open("rb") as fp:
        return hashlib.file_digest(fp,"sha256").hexdigest()


def read_struct(fp, fmt):
    data = fp.read(fmt.size)
    if len(data)!=fmt.size:
        raise ValueError("Truncated SKYF directory")
    return fmt.unpack(data)


def name_field(field):
    raw=field.split(b"\0",1)[0]
    if not raw or raw in (b".",b"..") or any(c<32 or c in b"/\\:" for c in raw):
        raise ValueError("Invalid SKYF name field")
    return raw.decode("cp1254",errors="replace")


def parse_index(path, files_first):
    size=path.stat().st_size
    entries=[]
    nodes=0
    def directory(fp, parent="", depth=0):
        nonlocal nodes
        nodes+=1
        if nodes>20000 or depth>32:
            raise ValueError("SKYF nesting limit exceeded")
        raw, children, count=read_struct(fp,DIRECTORY)
        name=name_field(raw)
        folder=f"{parent}/{name}" if parent else name
        def files():
            for _ in range(count):
                field,offset,length=read_struct(fp,MEMBER)
                member_name=name_field(field)
                if offset+length>size or len(entries)>=150000:
                    raise ValueError("Invalid SKYF member extent")
                entries.append(Entry(folder+"/"+member_name,offset,length))
        if files_first:
            files()
        for _ in range(children):
            directory(fp,folder,depth+1)
        if not files_first:
            files()
    with path.open("rb") as fp:
        if fp.read(6)!=b"SKYF\x01\x00":
            raise ValueError("Expected SKYF version 1")
        directory(fp)
        index_end=fp.tell()
    if not entries or index_end!=min(e.offset for e in entries) or len({e.path for e in entries})!=len(entries):
        raise ValueError("SKYF directory did not end at the first data record")
    end=index_end
    for e in sorted(entries,key=lambda item:(item.offset,item.size)):
        if e.offset<end:
            raise ValueError("Overlapping SKYF member extents")
        end=e.offset+e.size
    return entries,index_end


def read_index(path):
    layouts=[]
    errors=[]
    for files_first in (True,False):
        try:
            table=parse_index(path,files_first)
        except ValueError as error:
            errors.append(str(error))
            continue
        if table not in layouts:
            layouts.append(table)
    if len(layouts)!=1:
        raise ValueError("No unique SKYF layout: "+" / ".join(errors))
    return layouts[0]


def read_member(path,entries,name):
    # Resolve complete paths when supplied; never guess among duplicate basenames.
    name=name.casefold()
    matches=[e for e in entries if (e.path if "/" in name else e.path.rsplit("/",1)[-1]).casefold()==name]
    if len(matches)!=1:
        raise ValueError("Expected one exact SKYF member: "+name)
    entry=matches[0]
    with path.open("rb") as fp:
        fp.seek(entry.offset)
        data=fp.read(entry.size)
    if len(data)!=entry.size:
        raise ValueError("Truncated SKYF payload")
    return entry,data


def zone_data(base):
    mask=(base/"zone00.bin").read_bytes()
    raw=(base/"zone00_height.bin").read_bytes()
    if len(mask)!=ZONE_BYTES or hashlib.sha256(mask).hexdigest()!=MASK_SHA256:
        raise ValueError("zone00 mask differs from the verified version")
    if len(raw)!=4*ZONE_BYTES or hashlib.sha256(raw).hexdigest()!=HEIGHT_SHA256:
        raise ValueError("zone00 height differs from the verified version")
    heights=array("f")
    heights.frombytes(raw)
    if sys.byteorder!="little":
        heights.byteswap()
    if any(not math.isfinite(h) for h in heights):
        raise ValueError("Non-finite terrain sample")
    return mask,heights


def terrain_mesh(mask,heights,step):
    side=math.isqrt(len(mask))
    if len(mask)!=side*side or len(heights)!=len(mask) or not 1<=step<side:
        raise ValueError("Invalid zone raster or sample spacing")
    coords=list(range(0,side-1,step))+[side-1]
    vertices=[]
    indices={}
    faces=[]
    for row in coords:
        for col in coords:
            index=row*side+col
            if mask[index]:
                vertices.append((col,heights[index],row))
                indices[row,col]=len(vertices)
    for row,next_row in zip(coords,coords[1:]):
        for col,next_col in zip(coords,coords[1:]):
            corners=[indices.get(key) for key in ((row,col),(next_row,col),(row,next_col),(next_row,next_col))]
            a,b,c,d=corners
            if all(corners):
                faces.extend(((a,b,c),(c,b,d)))
    if not faces:
        raise ValueError("No faces at selected sample spacing")
    return vertices,faces


def write_obj(file,vertices,faces):
    with file.open("w",encoding="ascii") as out:
        out.write("# zone00; X=column, Y=stored height, Z=row; horizontal unit=one cell\n")
        for x,y,z in vertices:
            out.write(f"v {x} {y:.9g} {z}\n")
        for a,b,c in faces:
            out.write(f"f {a} {b} {c}\n")


def export(base,output,step,member):
    mask,heights=zone_data(base)
    vertices,faces=terrain_mesh(mask,heights,step)
    archive=base/"objects.dat"
    if digest(archive)!=OBJECTS_SHA256:
        raise ValueError("Object container differs from the verified version")
    entries,_=read_index(archive)
    entry,data=read_member(archive,entries,member)
    # A new directory prevents replacing a user's existing export.
    output.mkdir(parents=True,exist_ok=False)
    try:
        write_obj(output/"zone00.obj",vertices,faces)
        (output/entry.path.rsplit("/",1)[-1]).write_bytes(data)
    except Exception:
        # Only files created inside this new export directory are removed.
        for item in output.iterdir():
            item.unlink()
        output.rmdir()
        raise
    print(f"{len(vertices)} vertices, {len(faces)} triangles; {entry.path}: {entry.size} bytes")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--installer",type=Path)
    source.add_argument("--base",type=Path,help="Existing extracted app/base folder")
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--step",type=int,default=16)
    parser.add_argument("--member",default="AGAH.ADF")
    args=parser.parse_args()
    if args.base:
        export(args.base,args.out,args.step,args.member)
        return
    if digest(args.installer)!=INSTALLER_SHA256:
        raise SystemExit("Installer SHA-256 differs from the verified release.")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["innoextract","--silent","--extract","--output-dir",tmp,str(args.installer.resolve())],check=True)
        export(Path(tmp)/"app"/"base",args.out,args.step,args.member)


if __name__=="__main__":
    main()
