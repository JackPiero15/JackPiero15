"""Review sheet of the 9:16 crop of every shot: source frame + green box of the visible window.

Usage: python crop_sheet.py <piece> [fmt=vertical] [out.jpg]
Works for "sync" and "montage" shots. Read the box against faces/action, fix "cx" in the JSON, repeat.
Measure crop centres on THIS sheet (labels are true source pixels); estimates taken from a downscaled
image need rescaling - that mistake cut faces once.
"""
import json
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"

name = sys.argv[1]
fmt = sys.argv[2] if len(sys.argv) > 2 else "vertical"
p = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
c = p[fmt]
sw, sh = c["src_w"], c["src_h"]
TW = 320
TH = round(TW * sh / sw)
k = TW / sw
win = (1080 / 2) / (1920 / sh) * k          # half visible width at "fill height" scale, in tile px
shots = c["shots"]
dur = c["out"] - c["in"]
tiles = []
for i, s in enumerate(shots):
    if "k" in s or "t0" in s:
        t0 = s.get("t0", s["k"][0] * c.get("beat", 1) if "k" in s else 0)
        t1 = s.get("t1", s["k"][1] * c.get("beat", 1) if "k" in s else dur)
        src = s["src"] + (t1 - t0) / 2
    else:
        t0 = s["t"]
        t1 = shots[i + 1]["t"] if i + 1 < len(shots) else dur
        mid = (t0 + t1) / 2
        src = (s["src"] + (mid - t0)) if "src" in s else mid + c["in"] + c.get("video_offset", 0)
    raw = subprocess.run([FF, "-v", "error", "-ss", f"{src:.3f}", "-i", os.path.join(ROOT, c["video_file"]),
                          "-frames:v", "1", "-vf", f"scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    if len(raw) != TW * TH * 3:
        continue
    im = Image.frombytes("RGB", (TW, TH), raw)
    d = ImageDraw.Draw(im)
    for g in range(1, 8):
        x = g * TW / 8
        d.line([(x, 0), (x, TH)], fill=(110, 110, 110))
        d.text((x + 2, TH - 12), str(round(x / k)), fill=(255, 255, 0))
    cx = s.get("cx", sw / 2)
    cx = cx[0] if isinstance(cx, list) else cx
    d.rectangle([cx * k - win, 0, cx * k + win, TH - 1], outline=(0, 255, 0), width=2)
    d.rectangle([0, 0, 150, 12], fill=(0, 0, 0))
    d.text((2, 1), f"{i} t{t0:.1f}{' C' if 'src' in s and 't' in s else ''} cx{cx:.0f}", fill=(255, 255, 0))
    tiles.append(im)
cols = 6
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * TW, rows * TH))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * TW, (i // cols) * TH))
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "review", f"{name}_{fmt}_crops.jpg")
os.makedirs(os.path.dirname(out), exist_ok=True)
sheet.save(out, quality=85)
print(out)
