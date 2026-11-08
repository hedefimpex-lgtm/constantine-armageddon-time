"""Collect filenames, bounded headers and resource references from an unpacked game."""
from collections import Counter
from pathlib import Path
import json
import math
import re
import struct
import sys
import zipfile
import zlib

CONTAINERS = {".raw", ".bin", ".dat", ".adf", ".old"}
REFERENCE = re.compile(rb"[A-Za-z0-9_./%\\-]{4,}")
EXTENSION = re.compile(r"\.([A-Za-z][A-Za-z0-9_]{0,7})$")
RESOURCE = re.compile(r"actor|anim|armature|bone|charact|creature|geometr|height|istanbul|karakoy|level|material|mesh|model|motion|physic|scene|skelet|skin|terrain|texture|tile|world|zone", re.I)
SAMPLE = 128 * 1024


def references(data):
    """Filename matches are observations; they are not evidence of a loaded asset."""
    found = set()
    for match in REFERENCE.finditer(data):
        token = match[0]
        if len(token) > 160 or token.startswith((b"http", b"www.")):
            continue
        name = token.decode("ascii")
        if EXTENSION.search(name):
            found.add(name)
    return sorted(found)


def windows(path, size):
    offsets = {0}
    if size > SAMPLE:
        offsets.update((size//2,max(0,size-SAMPLE)))
    with path.open("rb") as f:
        for pos in sorted(offsets):
            f.seek(pos)
            yield pos, f.read(SAMPLE)


def compressed_prefix(block):
    # Check the small set of common zlib/gzip offsets at the start of the file.
    for pos in range(min(65,len(block)-2)):
        cmf, flags = block[pos:pos+2]
        gzip = (cmf,flags)==(0x1f,0x8b)
        if not gzip and not (cmf&15==8 and cmf>>4<=7 and (cmf*256+flags)%31==0):
            continue
        try:
            dec=zlib.decompressobj(31 if gzip else 15)
            plain=dec.decompress(block[pos:],SAMPLE)
        except zlib.error:
            continue
        if len(plain)>=32:
            return {"offset":pos,"codec":"gzip" if gzip else "zlib",
                    "validated_to_eof":dec.eof,"sample_bytes":len(plain),
                    "head_hex":plain[:32].hex(),"references":references(plain)[:80]}
    return None


def measure(path, root):
    size=path.stat().st_size
    row={"path":path.relative_to(root).as_posix(),"bytes":size}
    ext=path.suffix.lower()
    if ext not in CONTAINERS | {".xml", ".dds", ".exe", ".dll"}:
        return row
    with path.open("rb") as f:
        first=f.read(SAMPLE)
    row["head_hex"]=first[:32].hex()
    if ext==".dds" and first[:4]==b"DDS " and len(first)>=128:
        height,width=struct.unpack_from("<II",first,12)
        row.update(width=width,height=height,fourcc=first[84:88].decode("ascii","replace"))
        return row
    if ext in CONTAINERS:
        freq=Counter(first)
        row["first_window_entropy"]=round(-sum((n/len(first))*math.log2(n/len(first)) for n in freq.values()),3)
        row["head_le32"]=[n[0] for n in struct.iter_unpack("<I",first[:min(32,len(first))//4*4])]
        flat={}
        for off,block in windows(path,size):
            names=references(block)
            if names: flat[str(off)]=names[:80]
        if flat: row["references_by_window"]=flat
        comp=compressed_prefix(first)
        if comp: row["compressed_prefix"]=comp
        if first.startswith(b"PK\x03\x04") and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                entries=z.infolist()
                row["zip_count"]=len(entries)
                row["zip_names"]=sorted(i.filename for i in entries)[:200]
    if ext in {".exe",".dll",".xml"} and size<=16*1024*1024:
        data=path.read_bytes()
        names=set(references(data))
        wide_strings=re.findall(rb"(?:[\x20-\x7e]\x00){4,}",data)
        for s in wide_strings:
            names.update(references(s[::2]))
        row["file_references"]=sorted(names)[:1600]
        if ext==".exe":
            row["resource_identifiers"]=sorted(set(
                x.decode("ascii") for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_]{4,90}",data)
                if RESOURCE.search(x.decode("ascii"))))[:1400]
    return row


def main(root, output):
    files=sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink())
    rows=[measure(path,root) for path in files]
    output.write_text(json.dumps({"samples_per_container":"First, middle and last 128 KiB; bounded reference lists",
                                  "files":rows},ensure_ascii=False,separators=(",",":"))+"\n")
    print(len(rows),"files scanned")


if __name__=="__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]))
