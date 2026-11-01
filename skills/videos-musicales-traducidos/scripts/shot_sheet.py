"""Mid-frame of every shot between t0 and t1, with an x grid (source px) to pick 9:16 crop centres.

Usage: python shot_sheet.py video.mp4 out.jpg t0 t1 cut1,cut2,...
"""
import shutil
import os
import subprocess
import sys

from PIL import Image, ImageDraw

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
video, out, t0, t1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
cuts = [float(c) for c in sys.argv[5].split(",") if t0 < float(c) < t1]
bounds = [t0] + cuts + [t1]
tiles = []
for a, b in zip(bounds, bounds[1:]):
    mid = (a + b) / 2
    raw = subprocess.run([FF, "-v", "error", "-ss", f"{mid:.3f}", "-i", video, "-frames:v", "1",
                          "-vf", "scale=480:270", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    im = Image.frombytes("RGB", (480, 270), raw)
    d = ImageDraw.Draw(im)
    for i in range(1, 12):
        x = i * 40
        d.line([(x, 0), (x, 270)], fill=(255, 255, 255) if i % 3 == 0 else (120, 120, 120), width=1)
        if i % 3 == 0:
            d.text((x + 2, 255), str(i * 160), fill=(255, 255, 0))
    d.rectangle([0, 0, 130, 14], fill=(0, 0, 0))
    d.text((3, 2), f"{a:.2f}-{b:.2f}", fill=(255, 255, 0))
    tiles.append(im)
cols = 5
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 480, rows * 270))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * 480, (i // cols) * 270))
sheet.save(out, quality=88)
print(len(tiles), "shots")
