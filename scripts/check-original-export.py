"""Check a local export against the source and record metadata instead of game files."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zlib
from original_assets import export, read_index, read_member, zone_data

TEXTURE = re.compile(rb"[\w./\\-]{1,120}\.dds\x00",re.I)
SOURCE = re.compile(rb"[\w./\\-]{1,120}\.max\x00",re.I)
JOINT = re.compile(rb"(?:(?:Bip|Bone)\d{0,3})[A-Za-z0-9 ._-]{0,48}\x00",re.I)
SELECTED=("AGAH.ADF","AGOP.ADF","BALIKCI.ADF","AKTAR.ADF","ID_ITEM_BOX.ADF")


def strings(pattern, data):
    return sorted({m[0][:-1].decode("ascii") for m in pattern.finditer(data)})


def format_info(data):
    decoded=data
    encoding="stored"
    for pos in range(min(len(data)-1,65)):
        a,b=data[pos:pos+2]
        if not ((a&15)==8 and a>>4<=7 and (a*256+b)%31==0):
            continue
        try:
            dec=zlib.decompressobj()
            sample=dec.decompress(data[pos:],16*1024*1024)
        except zlib.error:
            continue
        if dec.eof and sample.startswith(b"root"):
            decoded=sample;encoding=f"zlib at {pos}";break
    return {"first_32_bytes":data[:32].hex(),"encoding":encoding,"root_tag":decoded[:4]==b"root",
            "root_word_4":int.from_bytes(decoded[4:8],"little") if decoded[:4]==b"root" else None,
            "texture_labels":strings(TEXTURE,decoded)[:80],"source_labels":strings(SOURCE,decoded)[:40],
            "joint_labels":strings(JOINT,decoded)[:50]}


def validate_obj(path,mask,height):
    n=0;faces=0
    for line in path.read_text().splitlines():
        fields=line.split()
        if fields and fields[0]=="v":
            x,y,z=int(fields[1]),float(fields[2]),int(fields[3])
            i=z*2048+x
            if not mask[i] or abs(height[i]-y)>1e-6:
                raise ValueError("OBJ vertex disagrees with original terrain")
            n+=1
        if fields and fields[0]=="f":
            ids=list(map(int,fields[1:]))
            if len(ids)!=3 or not all(1<=i<=n for i in ids):
                raise ValueError("Invalid OBJ triangle indices")
            faces+=1
    if not n or not faces:
        raise ValueError("Empty terrain mesh")
    return {"vertices":n,"triangles":faces,"step":16}


def check(base,out):
    mask,height=zone_data(base)
    mismatch=sum(bool(m)!=(h!=0) for m,h in zip(mask,height))
    archive=base/"objects.dat"
    entries,end=read_index(archive)
    textures,error=[],None
    try:
        textures,_=read_index(base/"textures_1.DAT")
    except ValueError as exc:
        error=str(exc)
    texture_names={e.path.rsplit("/",1)[-1].lower() for e in textures}
    rows={}
    for name in SELECTED:
        e,payload=read_member(archive,entries,name)
        info=format_info(payload)
        references=[t for t in info["texture_labels"] if t.replace("\\","/").rsplit("/",1)[-1].lower() in texture_names]
        rows[name]={"path":e.path,"offset":e.offset,"length":e.size,"sha256":hashlib.sha256(payload).hexdigest(),
                    "resolved_texture_names":references,**info}
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/"local-export"
        export(base,output,16,"AGAH.ADF")
        obj=validate_obj(output/"zone00.obj",mask,height)
        agah=output/rows["AGAH.ADF"]["path"].rsplit("/",1)[-1]
        if hashlib.sha256(agah.read_bytes()).hexdigest()!=rows["AGAH.ADF"]["sha256"]:
            raise ValueError("Exported ADF differs from its indexed member")
    result={"zone00":{"mask_height_support_mismatches":mismatch,"mask_counts":dict(Counter(mask)),**obj},
            "objects":{"entries":len(entries),"index_end":end,"folders":dict(Counter(
                e.path.rsplit("/",1)[0] for e in entries)),"selected":rows},
            "textures":{"entries":len(textures),"index_error":error}}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("Original terrain and indexed ADF export verified",obj,rows["AGAH.ADF"]["path"])


if __name__=="__main__":
    check(Path(sys.argv[1]),Path(sys.argv[2]))
