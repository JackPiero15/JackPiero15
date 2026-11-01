"""Measure duration, loudness and peak of sound effects / songs, and the Blender volume to reach a target.

sfx_measure.py <dir> <file> [file ...] [--target -16]
Prints {dur, lufs, peak, vol}: vol is the linear strip.volume that brings the file to the target LUFS.
Targets used in practice: -16 for SFX in silences, -15 for the intro song, -27 for laughs under speech,
-32 for a music bed under dialogue (voice stem sits at -14).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loudness import decode, lufs, peak_db, gain_for  # noqa: E402

args = sys.argv[1:]
target = -16.0
if "--target" in args:
    i = args.index("--target"); target = float(args[i + 1]); del args[i:i + 2]
d, names = args[0], args[1:]
out = {}
for name in names:
    x = decode(os.path.join(d, name))
    L = lufs(x)
    out[name] = {"dur": round(x.shape[1] / 48000, 2), "lufs": L, "peak": peak_db(x), "vol": gain_for(L, target)}
    print(name, out[name], flush=True)
print(json.dumps({"target_lufs": target}))
