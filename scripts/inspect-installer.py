#!/usr/bin/env python3
"""Hash the complete installer and inspect the executable portion with REA."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def read_exact(stream, count):
    block = stream.read(count)
    if len(block) != count:
        raise ValueError("Eksik PE başlığı")
    return block


def section_layout(stream, size):
    if read_exact(stream, 2) != b"MZ":
        raise ValueError("Dosyada MZ imzası bulunamadı")
    stream.seek(60)
    pe = struct.unpack("<I", read_exact(stream, 4))[0]
    stream.seek(pe)
    if read_exact(stream, 4) != b"PE\0\0":
        raise ValueError("Geçersiz PE imzası")
    machine, count, _, _, _, opt_size, _ = struct.unpack("<HHIIIHH", read_exact(stream, 20))
    if not 1 <= count <= 96 or not 64 <= opt_size <= 4096:
        raise ValueError("Geçersiz bölüm tablosu")
    opt = read_exact(stream, opt_size)
    if struct.unpack_from("<H", opt)[0] not in (0x10B, 0x20B):
        raise ValueError("Desteklenmeyen PE türü")
    end = max(stream.tell()+count*40, struct.unpack_from("<I", opt, 60)[0])
    sections = []
    for _ in range(count):
        section = read_exact(stream, 40)
        raw_size, offset = struct.unpack_from("<II", section, 16)
        if raw_size:
            end = max(end, offset + raw_size)
        sections.append(section[:8].split(b"\0")[0].decode("ascii", "replace"))
    if end > size or end > 128*1024*1024:
        raise ValueError("PE görüntüsü geçerli inceleme sınırını aşıyor")
    return machine, sections, end


def inspect(source, output, rea):
    with source.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        stream.seek(0)
        machine, sections, end = section_layout(stream, size)
        stream.seek(0)
        image = read_exact(stream, end)
    with tempfile.TemporaryDirectory() as directory:
        extracted = Path(directory) / "pe-image.exe"
        extracted.write_bytes(image)
        proc = subprocess.run([rea, "inspect-pe-imports", str(extracted),
                               "--max-file-bytes", str(max(67108864,end)), "--format", "json"],
                              check=True, text=True, capture_output=True, timeout=180)
        evidence = json.loads(proc.stdout)
    result = {"input":source.name, "bytes":size, "sha256":digest, "machine":hex(machine),
              "sections":sections, "pe_file_bytes":end, "trailing_bytes":size-end,
              "pe_image_sha256":hashlib.sha256(image).hexdigest(),
              "scope":"REA examines the PE headers and on-disk sections. The appended installer payload is outside this import analysis.",
              "rea_version":subprocess.check_output([rea,"--version"],text=True).strip(),
              "rea_imports":evidence}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{source.name}: {size} bytes, SHA-256 {digest}, {len(sections)} PE sections, {size-end} trailing bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--rea",default="rea")
    args=parser.parse_args()
    inspect(args.source,args.output,args.rea)
