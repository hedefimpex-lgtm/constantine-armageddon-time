"""Exercise the packaged offline game on the Android emulator via accessibility."""
from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

def adb(*args):
    return subprocess.check_output(["adb",*args],timeout=25)

def find_label(text, timeout=50):
    end=time.monotonic()+timeout
    last_xml=b""
    while time.monotonic()<end:
        try:
            adb("shell","uiautomator","dump","/sdcard/constantine-ui.xml")
            last_xml=adb("exec-out","cat","/sdcard/constantine-ui.xml")
            tree=ET.fromstring(last_xml)
            for node in tree.iter("node"):
                label=" ".join([node.get("text",""),node.get("content-desc","")]).casefold()
                if text.casefold() in label and len(label.strip())<80:
                    bounds=tuple(map(int,re.findall(r"-?\d+",node.get("bounds",""))))
                    if len(bounds)==4 and bounds[2]>bounds[0] and bounds[3]>bounds[1]:
                        return bounds
        except (ET.ParseError,subprocess.SubprocessError):
            pass
        time.sleep(1)
    (out/"device-state.xml").write_bytes(last_xml)
    (out/"device-failure.png").write_bytes(adb("exec-out","screencap","-p"))
    (out/"webview.log").write_bytes(adb("logcat","-d","-s","chromium","AndroidRuntime"))
    raise RuntimeError("Android ekranında bulunamadı: "+text)

apk=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
adb("install","-r",str(apk))
print(adb("shell","am","start","-W","-n","com.constantine.mobile/.GameActivity").decode())
x1,y1,x2,y2=find_label("Tek başına oyna")
(out/"android-menu.png").write_bytes(adb("exec-out","screencap","-p"))
adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2))
find_label("Rıhtım Nöbeti")
find_label("Röleyi etkinleştir")
(out/"android-rihtim.png").write_bytes(adb("exec-out","screencap","-p"))
print("APK opened the offline map and showed the relay control.")
