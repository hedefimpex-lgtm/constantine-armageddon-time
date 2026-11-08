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
    while time.monotonic()<end:
        try:
            adb("shell","uiautomator","dump","/sdcard/constantine-ui.xml")
            tree=ET.fromstring(adb("exec-out","cat","/sdcard/constantine-ui.xml"))
            for node in tree.iter("node"):
                label=" ".join([node.get("text",""),node.get("content-desc","")]).casefold()
                if text.casefold() in label:
                    return tuple(map(int,re.findall(r"\d+",node.get("bounds",""))))
        except (ET.ParseError,subprocess.SubprocessError):
            pass
        time.sleep(1)
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
