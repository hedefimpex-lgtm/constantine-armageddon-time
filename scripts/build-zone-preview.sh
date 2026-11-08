#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
base=${1:?Extracted app/base directory is required}
output=${2:?Output directory is required}
mkdir -p "$output"
output=$(cd "$output" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/scripts" "$tmp/mobile"
cp -R "$root/android" "$tmp/android"
cp "$root/scripts/build-android.sh" "$tmp/scripts/"
python3 "$root/scripts/write-zone-page.py" "$base" "$tmp/mobile/index.html"
python3 - "$tmp" <<'PY'
from pathlib import Path
import sys,xml.etree.ElementTree as ET
stage=Path(sys.argv[1])
android="http://schemas.android.com/apk/res/android"
ET.register_namespace("android",android)
manifest=stage/"android/AndroidManifest.xml"
tree=ET.parse(manifest);root=tree.getroot();root.set("package","com.constantine.zoneviewer")
root.find("application").set("{"+android+"}label","Constantine · Arazi Testi")
for child in root.findall("uses-permission"):
    root.remove(child)
tree.write(manifest,encoding="utf-8",xml_declaration=True)
p=stage/"android/src/com/constantine/mobile/GameActivity.java"
p.write_text(p.read_text().replace("package com.constantine.mobile;","package com.constantine.zoneviewer;"))
PY
bash "$tmp/scripts/build-android.sh"
cp "$tmp/build/constantine-android.apk" "$output/constantine-zone00-test.apk"
cp "$tmp/mobile/index.html" "$output/zone00.html"
