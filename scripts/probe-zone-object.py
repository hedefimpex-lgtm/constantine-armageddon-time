"""Probe one zone and named ADF records without exporting the game's assets."""
from array import array
from collections import Counter
import hashlib
import json
import math
import mmap
from pathlib import Path
import re
import statistics
import struct
import sys
import zlib

TARGETS = ("AGAH.ADF", "AGOP.ADF", "BALIKCI.ADF", "ID_ITEM_BOX.ADF")
U32 = struct.Struct("<I")
FLOAT = struct.Struct("<f")


def hexdigest(block):
    return hashlib.sha256(block).hexdigest()


def terrain(base):
    bins = (base / "zone00.bin").read_bytes()
    heights = (base / "zone00_height.bin").read_bytes()
    side = math.isqrt(len(bins))
    if side*side != len(bins) or len(heights) != 4*len(bins):
        raise ValueError("Unexpected zone00 pair dimensions")
    a = array("f")
    a.frombytes(heights)
    if sys.byteorder != "little":
        a.byteswap()
    active = [(i,a[i]) for i in range(0,len(a),37) if math.isfinite(a[i]) and a[i] != 0]
    valid = sorted(v for _,v in active)
    diffs = {}
    for stride in (1, 1023, 1024, 1025, side-1, side, side+1, 4095, 4096, 4097, 38111):
        sample = [abs(v-a[i+stride]) for i,v in active if i+stride<len(a) and math.isfinite(a[i+stride])]
        if sample:
            diffs[str(stride)]={"mean":round(statistics.mean(sample),7),"median":round(statistics.median(sample),7)}
    quantiles = [valid[round((len(valid)-1)*k)] for k in (0,.01,.25,.5,.75,.99,1)] if valid else []
    return {"pair_sha256":[hexdigest(bins),hexdigest(heights)],"lengths":[len(bins),len(heights)],
            "candidate_square_side":side,"float32_le_nonfinite":sum(not math.isfinite(x) for x in a),
            "float32_le_subnormal":sum(0 < abs(x) < 1.17549435e-38 for x in a),
            "float32_le_nonzero":sum(x!=0 for x in a),"nonzero_sample_count":len(active),
            "nonzero_quantiles":quantiles,"difference_by_stride":diffs,
            "zone_byte_counts":dict(sorted(Counter(bins).items()))}


def adf_head(data):
    return len(data)>=32 and data[:4]==b"root" and 0 < U32.unpack_from(data,4)[0] <= 32


def payload_starts(mm):
    raw = [m.start() for m in re.finditer(b"root",mm) if adf_head(mm[m.start():m.start()+96])]
    zipped = []
    for m in re.finditer(b"\x78[\x01\x5e\x9c\xda]",mm):
        pos = m.start()
        try:
            head=zlib.decompressobj().decompress(mm[pos:pos+4096],128)
        except zlib.error:
            continue
        if adf_head(head):
            zipped.append(pos)
    return sorted(set(raw+zipped)), set(zipped)


def find_name_rule(mm, names, markers):
    """Require cross-record matches. Return all equally supported, different mappings."""
    if not markers or len(names)<5:
        return []
    anchors = set(markers)
    tests = names[:120]
    rules = []
    for origin in ("start","end"):
        for delta in (range(-20,245) if origin=="start" else range(-8,161)):
            coords=[(start if origin=="start" else end)+delta for _,start,end in tests]
            if min(coords)<0: continue
            values=[U32.unpack_from(mm,p)[0] for p in coords]
            if len(set(values))<max(5,len(values)//2): continue
            bases = {0,markers[0]}
            for value in values[:6]:
                for mark in markers[:12]:
                    if 0 <= mark-value <= max(markers[0]+4096,4*1024*1024):
                        bases.add(mark-value)
            for base in bases:
                matches={v+base for v in values if v+base in anchors}
                if len(matches) < max(5,0.8*len(tests)): continue
                rules.append({"from":origin,"delta":delta,"base":base,"matches":len(matches),"tested":len(tests)})
    if not rules:return []
    best=max(r['matches'] for r in rules)
    return [r for r in rules if r['matches']==best]


def traits(data):
    # Only describe model file references and structure. Do not export model geometry.
    names={m[0].decode("ascii") for m in re.finditer(rb"[A-Za-z0-9_./\\-]{1,95}\.(?:dds|max|adf)\b",data,re.I)}
    joints={m[0].decode("ascii") for m in re.finditer(rb"(?:Bip0[0-9]|Bone)[A-Za-z0-9 _.\-]{0,32}(?=\x00)",data,re.I)}
    return {"texture_or_source_labels":sorted(names)[:55],"joint_labels":sorted(joints)[:45],"head_hex":data[:36].hex()}


def objects(base):
    path=base/"objects.dat"
    with path.open("rb") as fp,mmap.mmap(fp.fileno(),0,access=mmap.ACCESS_READ) as mm:
        markers,zipped=payload_starts(mm)
        stop=min(markers[0] if markers else len(mm),4*1024*1024)
        names=[(m.group(0)[:-1].decode("ascii"),m.start(),m.end()) for m in
               re.finditer(rb"[A-Za-z0-9_./\\-]{1,100}\.ADF\x00",mm[:stop],re.I)]
        rules=find_name_rule(mm,names,markers)
        report={"size":len(mm),"sha256":hashlib.sha256(mm).hexdigest(),"initial_header_hex":mm[:192].hex(),
                "index_scan_bytes":stop,"name_count":len(names),"first_names":names[:12],
                "root_count":len(markers)-len(zipped),"zlib_root_count":len(zipped),
                "first_payload_offsets":markers[:16],"offset_rules":rules,"targets":{}}
        report["self_named_payload_samples"]=[]
        for idx,pos in enumerate(markers):
            end=markers[idx+1] if idx+1<len(markers) else len(mm)
            sample=mm[pos:min(end,pos+512*1024)]
            if pos in zipped:
                try:
                    sample=zlib.decompressobj().decompress(sample,512*1024)
                except zlib.error:
                    continue
            if not any(name.split(".")[0].lower().encode("ascii") in sample.lower() for name in TARGETS):
                continue
            labels=traits(sample)
            named=[n for n in labels["texture_or_source_labels"] if
                   any(t.split(".")[0].lower() in n.lower() for t in TARGETS)]
            if named and len(report["self_named_payload_samples"])<24:
                report["self_named_payload_samples"].append({"payload_offset":pos,"labels":named})
        for target in TARGETS:
            matches=[(s,e) for name,s,e in names if name.upper()==target]
            observations=[]
            for s,e in matches[:4]:
                row={"name_at":s,"end":e,"index_before_hex":mm[max(0,s-32):s].hex(),
                     "index_after_hex":mm[e:e+160].hex()}
                addrs=sorted({U32.unpack_from(mm,(s if r["from"]=="start" else e)+r["delta"])[0]+r["base"] for r in rules})
                row["candidate_offsets"]=addrs
                if len(addrs)==1 and addrs[0] in markers:
                    pos=addrs[0];nextpos=next((m for m in markers if m>pos),len(mm))
                    block=mm[pos:min(nextpos,pos+16*1024*1024)]
                    row.update(payload_offset=pos,codec="raw")
                    if pos in zipped:
                        dec=zlib.decompressobj()
                        block=dec.decompress(block,32*1024*1024)
                        row.update(codec="zlib",complete_stream=dec.eof)
                    row.update(traits(block))
                observations.append(row)
            report["targets"][target]=observations
        return report


def main(root,out):
    base=root/"app"/"base"
    report={"zone00":terrain(base),"objects":objects(base)}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("Zone samples",report["zone00"]["nonzero_sample_count"],"index labels",report["objects"]["name_count"],
          "root signatures",report["objects"]["root_count"],"zlib signatures",report["objects"]["zlib_root_count"])


if __name__=="__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]))
