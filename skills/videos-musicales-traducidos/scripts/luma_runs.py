"""Find black / near-black stretches of a video (to cover them or avoid them as in-points).

Usage: python luma_runs.py video.mp4 [threshold=18.5] [t0] [t1]
Prints "a-b,a-b,..." (seconds) ready for gen_sync_shots.py. Luma is the mean Y (0-255) of a 64x36
thumbnail. 18.5 catches real black; ~21.5 also catches very dark night shots - LOOK at those before
covering them: a dark shot with the singer visible is content, not a flash.
"""
import os
import re
import shutil
import subprocess
import sys

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"

video = sys.argv[1]
thr = float(sys.argv[2]) if len(sys.argv) > 2 else 18.5
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
t1 = float(sys.argv[4]) if len(sys.argv) > 4 else None
cmd = [FF, "-hide_banner", "-ss", str(t0), "-i", video]
if t1:
    cmd += ["-t", str(t1 - t0)]
cmd += ["-vf", "scale=64:36,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-an", "-f", "null", "-"]
out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.splitlines()
vals = []
for i in range(0, len(out) - 1, 2):
    m = re.search(r"pts_time:([\d.]+)", out[i])
    if m:
        vals.append((float(m.group(1)) + t0, float(out[i + 1].split("=")[1])))
fr = (vals[1][0] - vals[0][0]) if len(vals) > 1 else 1 / 24
runs, cur = [], None
for t, y in vals:
    if y < thr:
        cur = [cur[0], t] if cur else [t, t]
    elif cur:
        runs.append(cur)
        cur = None
if cur:
    runs.append(cur)
print(",".join(f"{a:.2f}-{b + fr:.2f}" for a, b in runs))
