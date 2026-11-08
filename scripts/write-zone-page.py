"""Create an offline terrain view from the original zone00 mask and heights."""
import argparse
import json
from pathlib import Path
from original_assets import terrain_mesh,zone_data


def write_page(base,target,step):
    mask,height=zone_data(base)
    vertices,faces=terrain_mesh(mask,height,step)
    mesh={"vertices":vertices,"triangles":[[i-1 for i in face] for face in faces]}
    source=Path(__file__).resolve().parents[1]/"analysis"/"viewer"/"zone00.html"
    template=source.read_text(encoding="utf-8")
    if template.count("__ZONE_MESH__")!=1:
        raise ValueError("Missing terrain data placeholder")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(template.replace("__ZONE_MESH__",json.dumps(mesh,separators=(",",":"),allow_nan=False)),encoding="utf-8")
    print(f"Preview from original samples: {len(vertices)} vertices, {len(faces)} triangles, step {step}")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base",type=Path)
    parser.add_argument("html",type=Path)
    parser.add_argument("--step",type=int,default=16)
    args=parser.parse_args()
    write_page(args.base,args.html,args.step)
