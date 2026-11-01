"""QA of a delivered MP4: stream properties, black-frame scan, and a still at every subtitle change.

Usage: python final_qa.py <piece> <vertical|horizontal>
Stills come from the encoded deliverable (not from Blender), 0.25 s after each subtitle appears.
"""
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
OUT = {"vertical": ("vertical", "VERTICAL"), "horizontal": ("youtube", "YOUTUBE_COMPLETO_16x9")}

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
name, fmt = sys.argv[1], sys.argv[2]
piece = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
folder, suf = OUT[fmt]
mp4 = os.path.join(ROOT, folder, f"{piece['id']}_{suf}.mp4")
info = subprocess.run([FF, "-hide_banner", "-i", mp4], capture_output=True, text=True, encoding="utf-8",
                      errors="replace").stderr
streams = [l.strip() for l in info.splitlines() if "Stream #" in l or "Duration" in l]
bd = subprocess.run([FF, "-hide_banner", "-nostats", "-i", mp4, "-vf", "blackdetect=d=0.05:pix_th=0.08", "-an",
                     "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
timing = json.load(open(os.path.join(ROOT, "subs", piece["id"], fmt, "timing.json"), encoding="utf-8"))
vert = fmt == "vertical"
tw, th = (180, 320) if vert else (320, 180)
tiles = []
for t in timing:
    ts = t["in"] + 0.25
    raw = subprocess.run([FF, "-v", "error", "-ss", f"{ts:.3f}", "-i", mp4, "-frames:v", "1", "-vf", f"scale={tw}:{th}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) != tw * th * 3:
        continue
    im = Image.frombytes("RGB", (tw, th), raw)
    ImageDraw.Draw(im).text((3, 2), f"{ts:.1f}", fill=(255, 255, 0))
    tiles.append(im)
cols = 10 if vert else 6
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, max(1, rows) * th))
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
path = os.path.join(ROOT, "review", f"final_{piece['id']}_{suf}.jpg")
sheet.save(path, quality=86)
res = {"file": mp4, "streams": streams, "black_intervals": blacks, "stills": len(tiles), "sheet": path}
json.dump(res, open(os.path.join(ROOT, "export", f"{piece['id']}_{suf}_qa.json"), "w"), indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
