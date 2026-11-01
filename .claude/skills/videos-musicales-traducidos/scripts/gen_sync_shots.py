"""Shot list for a lip-synced piece (footage = the song's own video), covering black gaps.

Usage: python gen_sync_shots.py <piece> <fmt> <cuts.txt> <black_runs> [cx_default]
  cuts.txt   : one cut time (s) per line, any order (scene detection)
  black_runs : "a-b,a-b,..." source seconds where the original video is black
Rules: gaps of <= 2 frames -> the next shot starts early with its own frames (video leads <= 67 ms
until the next cut); longer gaps -> an ambient cutaway from piece[fmt]["cutaways"] (no singing on
screen, so no false lip-sync), each use taking a later in-point. Writes piece[fmt]["shots"].
"""
import json
import os
import sys

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
name, fmt, cuts_file, runs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
path = os.path.join(ROOT, "pieces", name + ".json")
piece = json.load(open(path, encoding="utf-8"))
cfg = piece[fmt]
num, den = cfg.get("fps", piece["fps"])
fr = den / num
a_in, a_out = cfg["in"], cfg["out"]
cx_default = float(sys.argv[5]) if len(sys.argv) > 5 else cfg["src_w"] / 2
old_cx = {round(s["t"], 2): s["cx"] for s in cfg.get("shots", []) if "cx" in s and "src" not in s}

cuts = sorted({round(float(x), 2) for x in open(cuts_file).read().split()})
black = [tuple(map(float, r.split("-"))) for r in runs.split(",") if r]
pool = [list(c) for c in cfg["cutaways"]]          # [start, end, cx]
ptr = [c[0] for c in pool]
use = 0

events = []   # (src_time, kind, extra)
for c in cuts:
    if a_in < c < a_out:
        events.append((c, "cut", None))
for a, b in black:
    if b <= a_in or a >= a_out:
        continue
    events.append((max(a, a_in), "black", min(b, a_out)))
events.sort()

shots = [{"t": 0.0}]
skip_until = -1
for src_t, kind, extra in events:
    if src_t < skip_until:
        continue
    t = round(src_t - a_in, 3)
    if kind == "cut":
        if t - shots[-1]["t"] < 2.5 * fr:
            continue
        shots.append({"t": t})
        continue
    b = extra
    n_frames = round((b - src_t) / fr)
    if n_frames <= 2:
        # start the following material now, with its own (post-gap) frames
        shots.append({"t": t, "src": round(b, 3), "desc": "salto de negro (<=2 f)"})
    else:
        dur = b - src_t
        for _ in range(len(pool)):
            k = use % len(pool)
            use += 1
            if ptr[k] + dur <= pool[k][1]:
                break
            ptr[k] = pool[k][0]
            if ptr[k] + dur <= pool[k][1]:
                break
        shots.append({"t": t, "src": round(ptr[k], 3), "cx": pool[k][2], "desc": "plano ambiental sobre negro"})
        ptr[k] += dur + 0.5
        shots.append({"t": round(b - a_in, 3)})       # back in sync after the gap
    skip_until = b - 0.01
# merge shots that ended up shorter than 3 frames
clean = []
for s in shots:
    if clean and s["t"] - clean[-1]["t"] < 2.5 * fr and "src" not in clean[-1]:
        clean[-1] = s
    else:
        clean.append(s)
for s in clean:
    if "cx" not in s:
        s["cx"] = old_cx.get(round(s["t"], 2), cx_default)
cfg["shots"] = clean
json.dump(piece, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(clean), "shots;", sum(1 for s in clean if "src" in s), "covering black gaps")
for i, s in enumerate(clean):
    print(i, s)
