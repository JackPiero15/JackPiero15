"""Turn captions_raw.json into short on-screen caption chunks.

caption_chunks.py <captions_raw.json> <captions.json> [--fixes caption_fixes.json]
caption_fixes.json (optional), indices as printed by captions.py ([phrase] word_index:word):
  {"M4_feminismo_916": {"fixes": [[2, 0, "mido"], [2, 1, null], [2, 2, "1.90,"]], "speakers": "AAAB..."}}
  - a fix replaces a word (null deletes it): typos from Whisper, capitalisation, censoring ("v*rga").
  - "speakers" is optional (one letter per phrase); captions are white by default anyway.
Chunks: up to 4 words / 20 chars, break on . ? ! (and on commas after 3 words), never leave a word alone.
"""
import json, sys

raw = json.load(open(sys.argv[1], encoding="utf-8"))
out_path = sys.argv[2]
fixes_all = {}
if "--fixes" in sys.argv:
    fixes_all = json.load(open(sys.argv[sys.argv.index("--fixes") + 1], encoding="utf-8-sig"))
MAX_WORDS, MAX_CHARS, GAP, HOLD, MIN_DUR, MERGE_CHARS = 4, 20, 0.35, 0.35, 0.45, 24

out = {}
for scene, phrases in raw.items():
    cfg = fixes_all.get(scene, {})
    fx = {(p, w): t for p, w, t in cfg.get("fixes", [])}
    spk_s = cfg.get("speakers", "")
    chunks = []
    for pi, p in enumerate(phrases):
        spk = spk_s[pi] if pi < len(spk_s) else "A"
        words = []
        for wi, w in enumerate(p["words"]):
            t = fx.get((pi, wi), w["w"])
            if t is not None:
                words.append({"w": t, "s": w["s"], "e": w["e"]})
        cur, pch = [], []
        for w in words:
            text = " ".join(x["w"] for x in cur + [w])
            if cur and (len(cur) >= MAX_WORDS or len(text) > MAX_CHARS or w["s"] - cur[-1]["e"] > GAP):
                pch.append(cur); cur = []
            cur.append(w)
            end = w["w"].rstrip('"')[-1:]
            if end in ".?!" or (end == "," and len(cur) >= 3):
                pch.append(cur); cur = []
        if cur:
            pch.append(cur)
        merged = []
        for c in pch:
            if merged and (len(c) == 1 or len(merged[-1]) == 1) and \
                    len(" ".join(x["w"] for x in merged[-1] + c)) <= MERGE_CHARS and c[0]["s"] - merged[-1][-1]["e"] <= 1.0:
                merged[-1] = merged[-1] + c
            else:
                merged.append(c)
        chunks.extend((c, spk) for c in merged)
    caps = []
    for i, (ws, spk) in enumerate(chunks):
        t0, t1 = ws[0]["s"], ws[-1]["e"] + HOLD
        if i + 1 < len(chunks):
            t1 = min(t1, chunks[i + 1][0][0]["s"])
        caps.append({"t0": round(t0, 2), "t1": round(max(t1, t0 + MIN_DUR), 2), "spk": spk,
                     "text": " ".join(w["w"] for w in ws)})
    for a, b in zip(caps, caps[1:]):
        a["t1"] = min(a["t1"], b["t0"])
    out[scene] = caps
    print("==", scene, len(caps))
    for c in caps:
        print(f"  {c['t0']:6.2f}-{c['t1']:6.2f} {c['spk']} {c['text']}")
json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
