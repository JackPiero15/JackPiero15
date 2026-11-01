"""Locate burned-in coloured text (e.g. yellow lyrics) across a video: union box, typical box, gaps.

Usage: python locate_text_color.py video.mp4 t0 t1 [yellow|white]
Coordinates are reported in 1920x1080 space (frames are scaled to 1080p for the scan); convert to the
video's own pixels or to your 9:16 crop before placing a covering plate.
"""
import os
import shutil
import subprocess
import sys

import numpy as np

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
video, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rule = sys.argv[4] if len(sys.argv) > 4 else "yellow"
W, H = 1920, 1080
raw = subprocess.run([FF, "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", video, "-vf",
                      f"fps=4,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.int16)
r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
m = ((r > 215) & (g > 215) & (b > 215)) if rule == "white" else ((r > 170) & (g > 150) & (b < 110) & (r - b > 90))
boxes, missing = [], []
for i in range(len(fr)):
    ys, xs = np.nonzero(m[i])
    t = t0 + i / 4
    if len(xs) > 40:
        boxes.append((t, *np.percentile(xs, [1, 99]), *np.percentile(ys, [1, 99])))
    else:
        missing.append(round(t, 2))
if not boxes:
    sys.exit("no text of that colour found")
a = np.array([bx[1:] for bx in boxes])
print(f"frames with text: {len(boxes)}/{len(fr)}")
print("union box  x %.0f-%.0f  y %.0f-%.0f" % (a[:, 0].min(), a[:, 1].max(), a[:, 2].min(), a[:, 3].max()))
print("p5-p95 box x %.0f-%.0f  y %.0f-%.0f" % (np.percentile(a[:, 0], 5), np.percentile(a[:, 1], 95),
                                             np.percentile(a[:, 2], 5), np.percentile(a[:, 3], 95)))
print("times without text:", missing[:80])
