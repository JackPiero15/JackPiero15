"""Build one leveled dialogue stem per scene from edit_decisions.json (PyAV / libavfilter, no ffmpeg.exe).

level_audio.py <edit_decisions.json> <out_dir>
Chain: 10 ms fades on every cut -> phrase-level gain riding (each Whisper phrase to the median, max +-10 dB,
so a quiet and a loud voice-chat speaker end up even) -> highpass 80 Hz -> gentle dynaudnorm ->
loudnorm -14 LUFS -> alimiter -1.5 dBFS. Writes <scene>_voz_nivelada.wav (48 kHz stereo) and levels.json.
Env: SCENES=a,b (only these scenes), DYN=<dynaudnorm options>.
"""
import av, sys, os, json, wave
from fractions import Fraction
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loudness import SR, decode, lufs, peak_db  # noqa: E402

CHAIN = [
    ("highpass", "f=80"),
    ("dynaudnorm", os.environ.get("DYN", "f=300:g=15:p=0.9:m=4:s=0")),
    ("loudnorm", "I=-14:TP=-1.5:LRA=7"),
    ("aresample", "48000"),
    ("alimiter", "limit=0.84:attack=5:release=60:level=disabled"),
]


def run_chain(x):
    g = av.filter.Graph()
    src = g.add_abuffer(format="fltp", sample_rate=SR, layout="stereo", time_base=Fraction(1, SR))
    nodes = [src] + [g.add(n, a) for n, a in CHAIN] + [g.add("abuffersink")]
    for u, v in zip(nodes, nodes[1:]):
        u.link_to(v)
    g.configure()
    out, pts, hop = [], 0, 4800

    def drain():
        while True:
            try:
                f = g.pull()
            except (av.BlockingIOError, av.EOFError):
                return
            out.append(f.to_ndarray().reshape(2, -1) if f.format.is_planar else f.to_ndarray().reshape(-1, 2).T)

    for i in range(0, x.shape[1], hop):
        chunk = np.ascontiguousarray(x[:, i:i + hop])
        fr = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
        fr.sample_rate, fr.pts, fr.time_base = SR, pts, Fraction(1, SR)
        pts += chunk.shape[1]
        g.push(fr)
        drain()
    g.push(None)
    drain()
    y = np.concatenate(out, axis=1).astype(np.float32)
    return y[:, : x.shape[1]] if y.shape[1] >= x.shape[1] else np.pad(y, ((0, 0), (0, x.shape[1] - y.shape[1])))


def phrases_for(segs, trans):
    """Whisper phrases clipped to the cuts, in stem time (seconds)."""
    out, t0 = [], 0.0
    for key, a, b in segs:
        for p in trans.get(key, []):
            s, e = max(p["s"], a), min(p["e"], b)
            if e - s > 0.25:
                out.append((t0 + s - a, t0 + e - a))
        t0 += b - a
    return out


def phrase_db(x, phrases):
    m = x.mean(axis=0)
    return [20 * np.log10(np.sqrt(np.mean(m[int(s * SR):int(e * SR)] ** 2)) + 1e-12) for s, e in phrases]


def ride(x, phrases, max_db=10.0, ramp_s=0.08):
    if not phrases:
        return x
    lv = np.array(phrase_db(x, phrases))
    gains = np.clip(float(np.median(lv)) - lv, -max_db, max_db)
    env = np.zeros(x.shape[1], dtype=np.float32)
    for (s, e), gdb in zip(phrases, gains):
        env[int(s * SR):int(e * SR)] = gdb
    r = int(ramp_s * SR)
    env = np.convolve(env, np.ones(r, dtype=np.float32) / r, mode="same")
    return x * (10 ** (env / 20))[None, :]


def spread(vals):
    v = np.array(vals)
    return round(float(np.percentile(v, 90) - np.percentile(v, 10)), 1) if len(v) else 0.0


dec = json.load(open(sys.argv[1], encoding="utf-8-sig"))
out_dir = sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
trans = {k: json.load(open(p, encoding="utf-8")) for k, p in dec.get("transcripts", {}).items()}
only = set(filter(None, os.environ.get("SCENES", "").split(",")))
fade = int(0.010 * SR)
ramp = np.linspace(0, 1, fade, dtype=np.float32)
report = {}
for scene, segs in dec["scenes"].items():
    if only and scene not in only:
        continue
    parts = []
    for key, a, b in segs:
        x = decode(dec["sources"][key], a, b)
        x[:, :fade] *= ramp
        x[:, -fade:] *= ramp[::-1]
        parts.append(x)
    raw = np.concatenate(parts, axis=1)
    phr = phrases_for(segs, trans)
    lev = run_chain(ride(raw, phr))
    path = os.path.join(out_dir, f"{scene}_voz_nivelada.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(lev, -1, 1).T * 32767).astype(np.int16).tobytes())
    report[scene] = {
        "wav": path, "seconds": round(raw.shape[1] / SR, 2), "frases": len(phr),
        "antes": {"lufs": lufs(raw), "pico_db": peak_db(raw), "dif_frases_db": spread(phrase_db(raw, phr))},
        "despues": {"lufs": lufs(lev), "pico_db": peak_db(lev), "dif_frases_db": spread(phrase_db(lev, phr))},
    }
    print(scene, report[scene]["antes"], "->", report[scene]["despues"], flush=True)
json.dump(report, open(os.path.join(out_dir, "levels.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
