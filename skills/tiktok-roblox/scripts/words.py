"""Print word-level timestamps of a transcript JSON between two times (to place cuts on word boundaries).

words.py <transcript.json> <start_s> <end_s>
Tip: in PowerShell set $env:PYTHONIOENCODING="utf-8" so accents print correctly.
"""
import json, sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
a, b = float(sys.argv[2]), float(sys.argv[3])
for s in d:
    if s["e"] < a or s["s"] > b:
        continue
    print("  " + " ".join("{}[{:.2f}-{:.2f}]".format(w["w"].strip(), w["s"], w["e"]) for w in s["words"]))
