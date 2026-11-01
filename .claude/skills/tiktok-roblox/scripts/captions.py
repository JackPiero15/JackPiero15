"""Map Whisper phrases onto each scene's timeline (scene seconds) and estimate the speaker by pitch.

captions.py <edit_decisions.json> <audio_16k_dir> <captions_raw.json>
<audio_16k_dir> holds the WAVs from extract_audio.py; edit_decisions.json "wavs16k" maps source key -> file name
(e.g. {"B": "2026-10-25_19-33-37_t1.wav"}). Each phrase gets a median f0 and a 2-cluster speaker guess
(spk 0/1). Pitch is only a hint: check it against the dialogue logic and the person on screen.
"""
import json, sys, os, wave
import numpy as np

dec = json.load(open(sys.argv[1], encoding="utf-8-sig"))
wav_dir, out_path = sys.argv[2], sys.argv[3]
SR = 16000
audio = {}
for k, fn in dec["wavs16k"].items():
    with wave.open(os.path.join(wav_dir, fn)) as w:
        audio[k] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def f0_of(x):
    n, hop, lo, hi = 640, 320, SR // 400, SR // 75
    vals = []
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        if ac[0] <= 0:
            continue
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] / ac[0] > 0.45:
            vals.append(SR / lag)
    return float(np.median(vals)) if len(vals) >= 3 else None


trans = {k: json.load(open(p, encoding="utf-8")) for k, p in dec["transcripts"].items()}
result = {}
for scene, segs in dec["scenes"].items():
    phrases, t_off = [], 0.0
    for key, a, b in segs:
        for p in trans[key]:
            ws = [w for w in p["words"] if w["s"] >= a - 0.05 and w["e"] <= b + 0.05]
            if not ws:
                continue
            s0, s1 = ws[0]["s"], ws[-1]["e"]
            phrases.append({
                "t0": round(t_off + max(s0, a) - a, 2), "t1": round(t_off + min(s1, b) - a, 2),
                "f0": f0_of(audio[key][int(s0 * SR):int(s1 * SR)]),
                "words": [{"w": w["w"].strip(), "s": round(t_off + max(w["s"], a) - a, 2),
                           "e": round(t_off + min(w["e"], b) - a, 2)} for w in ws],
            })
        t_off += b - a
    f0s = np.array([np.log(p["f0"]) for p in phrases if p["f0"]])
    if len(f0s) >= 2:
        c = np.array([f0s.min(), f0s.max()])
        for _ in range(20):
            lab = np.abs(f0s[:, None] - c[None, :]).argmin(1)
            c = np.array([f0s[lab == j].mean() if (lab == j).any() else c[j] for j in range(2)])
        for p in phrases:
            p["spk"] = int(np.abs(np.log(p["f0"]) - c).argmin()) if p["f0"] else None
    result[scene] = phrases
    print("==", scene)
    for i, p in enumerate(phrases):
        print(f"  [{i:2d}] {p['t0']:6.2f}-{p['t1']:6.2f} f0={p['f0'] and round(p['f0'])!s:>5} spk={p.get('spk')} "
              + " ".join(f"{j}:{w['w']}" for j, w in enumerate(p["words"])))
json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
