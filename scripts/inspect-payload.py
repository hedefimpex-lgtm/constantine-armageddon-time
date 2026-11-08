#!/usr/bin/env python3
"""Inventory installed executables and report static imports without running the game."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile

def inspect(installer, rea, out):
    with tempfile.TemporaryDirectory() as folder:
        unpack = subprocess.run(["innoextract","--silent","--extract","--output-dir",folder,str(installer)],
                                text=True,capture_output=True,timeout=600)
        if unpack.returncode:
            raise RuntimeError("innoextract: "+unpack.stderr[-1800:])
        root = Path(folder)
        items = sorted(p for p in root.rglob("*") if not p.is_symlink() and p.is_file())
        extensions = Counter(p.suffix.lower() or "(none)" for p in items)
        executables = [p for p in items if p.suffix.lower()==".exe"]
        result = {"file_count":len(items),"file_types":dict(extensions.most_common()),
                  "executables":[p.relative_to(root).as_posix() for p in executables],"inspected":[]}
        for path in executables[:40]:
            if path.stat().st_size>64*1024**2:
                continue
            proc=subprocess.run([rea,"inspect-pe-imports",str(path),"--format","json"],
                                capture_output=True,text=True,timeout=120)
            row={"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size}
            if proc.returncode:
                row["status"]="REA could not parse this executable"
            else:
                evidence=json.loads(proc.stdout)
                data=evidence["normalized_result"]
                row.update({"status":"parsed","sha256":data["artifact"]["sha256"],
                            "architecture":data["architecture"],"format":data["format"],
                            "dlls":[item["name"] for item in data["imports"]],
                            "delay_dlls":[item["name"] for item in data["delay_imports"]],
                            "evidence_id":evidence["evidence_id"]})
            result["inspected"].append(row)
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
        print("Inventory:",len(items),"files;",len(executables),"executables")


if __name__ == "__main__":
    inspect(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]))
