"""Background-render QA stills and a contact sheet for one format of one piece.

Usage: python qa_stills.py <piece> <vertical|horizontal> <blend> [every_nth] [extra frames]
Frames: middle of every subtitle and 3 frames into every shot (thinned by every_nth for long songs).
A separate background Blender renders the stills, so the interactive Blender is never touched.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
BLENDER = os.environ.get("BLENDER") or shutil.which("blender") or r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
SCENE_SUFFIX = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_16x9"}

name, fmt, blend = sys.argv[1], sys.argv[2], sys.argv[3]
nth = int(sys.argv[4]) if len(sys.argv) > 4 else 1
piece = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
cfg = piece[fmt]
timing = json.load(open(os.path.join(ROOT, "subs", piece["id"], fmt, "timing.json"), encoding="utf-8"))
num, den = cfg.get("fps", piece["fps"])
fps = num / den
f = lambda s: 1 + round(s * fps)
frames = {f((t["in"] + t["out"]) / 2) for t in timing[::nth]}
for s in cfg["shots"][::nth]:
    m0 = s.get("t", s.get("t0", s["k"][0] * cfg.get("beat", 1) if "k" in s else 0))
    frames.add(f(m0) + 3)
frames.add(1)
frames.add(round((cfg["out"] - cfg["in"]) * fps))
if len(sys.argv) > 5:
    frames |= {int(x) for x in sys.argv[5].split(",")}
out = os.path.join(ROOT, "review", f"{name}_{fmt}")
os.makedirs(out, exist_ok=True)
for old in glob.glob(os.path.join(out, "f_*.png")):
    os.remove(old)
subprocess.run([BLENDER, "-b", blend, "-S", f"{piece['scene']}_{SCENE_SUFFIX[fmt]}", "-o", os.path.join(out, "f_####"),
                "-F", "PNG", "-f", ",".join(str(x) for x in sorted(frames))], check=True, capture_output=True)

files = sorted(glob.glob(os.path.join(out, "f_*.png")))
vert = fmt == "vertical"
tw, th = (216, 384) if vert else (384, 216)
cols = 8 if vert else 5
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, fp in enumerate(files):
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(Image.open(fp).convert("RGB").resize((tw, th)), (x, y))
    d.rectangle([x, y, x + 44, y + 13], fill=(0, 0, 0))
    d.text((x + 2, y + 1), os.path.basename(fp)[2:6], fill=(255, 255, 0))
    sx = tw / (1080 if vert else 1920)
    if vert:   # editorial safe area x 100-900, y 260-1450
        d.rectangle([x + 100 * sx, y + 260 * sx, x + 900 * sx, y + 1450 * sx], outline=(0, 255, 0))
    else:      # 120 px sides, 130 px bottom
        d.rectangle([x + 120 * sx, y + 60 * sx, x + 1800 * sx, y + 950 * sx], outline=(0, 255, 0))
path = os.path.join(ROOT, "review", f"{name}_{fmt}_sheet.jpg")
sheet.save(path, quality=88)
print(len(files), "stills ->", path)
