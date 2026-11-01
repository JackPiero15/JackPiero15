"""Beat-anchored montage from a pool of clean takes (when the footage is NOT the song's own video).

Usage: python gen_montage.py <piece> <vertical|horizontal>
Reads piece[fmt]["montage"]:
  {"beat": 0.54, "phase": 0.43, "end": 194.2,            # seconds; end = montage length
   "pools": {"SOFA": {"takes": [[6.64, 10.67], [55.40, 59.43]], "desc": "chica en el sofa", "cx": 560}, ...},
   "plan": [["intro", [["PIE", 2], ["SOFA", 7]]], ["verso 1", [...]], ...],   # (pool, beats)
   "section_k": [0, 28, 92, ...],                         # beat index where each plan section starts
   "fillers": ["SIL", "SINK", "SOFA"]}                    # long takes used if a section runs short
Takes must be CLEAN: no cut, flash or black frame inside (find them with shot_sheet.py + luma_runs.py).
Each repeat of a pool takes the next take or a later in-point, so repeats are never identical.
Every section is anchored to its own beat, so short takes never make the edit drift off the song.
Writes piece[fmt]["shots"] as {"t0", "t1", "src", "desc", "cx"?}.
"""
import json
import math
import os
import sys

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()
MARGIN = 0.04


def main():
    name, fmt = sys.argv[1], sys.argv[2]
    path = os.path.join(ROOT, "pieces", name + ".json")
    piece = json.load(open(path, encoding="utf-8"))
    M = piece[fmt]["montage"]
    beat, phase, end = M["beat"], M["phase"], M["end"]
    pools = M["pools"]
    plan, section_k, fillers = M["plan"], M["section_k"], M.get("fillers", [])
    cursor = {k: [0, v["takes"][0][0]] for k, v in pools.items()}

    def take(pool, beats):
        takes = pools[pool]["takes"]
        i, pos = cursor[pool]
        for _ in range(len(takes) + 1):
            s, e = takes[i]
            if e - pos >= min(beats * beat, e - s) - 1e-6 and e - pos > 0.6:
                break
            i = (i + 1) % len(takes)
            pos = takes[i][0]
        e = takes[i][1]
        return i, pos, e, max(1, math.floor((e - pos) / beat + 1e-6))

    shots = []
    for si, (section, seq) in enumerate(plan):
        k = section_k[si]
        k_end = section_k[si + 1] if si + 1 < len(section_k) else None
        queue = [list(x) for x in seq] + [[fillers[j % len(fillers)], 8] for j in range(6)] if fillers else list(seq)
        first = True
        while queue:
            pool, beats = queue.pop(0)
            i, src, e, avail = take(pool, beats)
            beats = min(beats, avail) if k_end is None else min(beats, avail, k_end - k)
            if beats <= 0:
                break
            t0 = shots[-1]["t1"] if shots else 0.0
            t1 = min(phase + (k + beats) * beat, end)
            if src + (t1 - t0) > e + MARGIN:
                t1 = t0 + (e - src)
            shot = {"t0": round(t0, 3), "t1": round(t1, 3), "src": round(src, 3),
                    "desc": (f"[{section}] " if first else "") + pools[pool].get("desc", pool)}
            if "cx" in pools[pool]:
                shot["cx"] = pools[pool]["cx"]
            shots.append(shot)
            first = False
            k = round((t1 - phase) / beat)
            nxt = src + (t1 - t0) + 0.6
            takes = pools[pool]["takes"]
            if nxt + 0.6 > e:
                i, nxt = (i + 1) % len(takes), takes[(i + 1) % len(takes)][0]
            cursor[pool] = [i, nxt]
            if (k_end is not None and k >= k_end) or t1 >= end - 0.01:
                break
    if shots[-1]["t1"] < end - 0.01:
        print("WARNING: plan ends at", shots[-1]["t1"], "< end", end, "- add takes to the last section")
    piece[fmt]["shots"] = shots
    json.dump(piece, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for sh in shots:
        print(f'{sh["t0"]:7.2f}-{sh["t1"]:7.2f} src {sh["src"]:7.2f}  {sh["desc"]}')
    print(len(shots), "shots, end", shots[-1]["t1"])


if __name__ == "__main__":
    main()
