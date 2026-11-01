"""Extract every audio track of every .mov/.mp4 in a folder to 16 kHz mono WAV and report levels.

extract_audio.py <videos_dir> <out_dir>
Writes <name>_t<N>.wav and audio_tracks.json (rms, peak, % of active seconds per track) so you can see
which OBS track carries the full mix (often both tracks are identical) and which one is mic-only.
"""
import av, sys, os, wave, json
import numpy as np

src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
report = {}
for name in sorted(os.listdir(src_dir)):
    if not name.lower().endswith((".mov", ".mp4", ".mkv")):
        continue
    path = os.path.join(src_dir, name)
    base = os.path.splitext(name)[0].replace(" ", "_")
    with av.open(path) as c:
        n_audio = len(c.streams.audio)
    report[name] = []
    for ti in range(n_audio):
        c = av.open(path)
        st = c.streams.audio[ti]
        rs = av.AudioResampler(format="s16", layout="mono", rate=16000)
        chunks = []
        for frame in c.decode(st):
            for f in rs.resample(frame):
                chunks.append(f.to_ndarray().reshape(-1))
        for f in rs.resample(None):
            chunks.append(f.to_ndarray().reshape(-1))
        c.close()
        pcm = np.concatenate(chunks).astype(np.int16)
        out = os.path.join(out_dir, f"{base}_t{ti+1}.wav")
        with wave.open(out, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
            w.writeframes(pcm.tobytes())
        x = pcm.astype(np.float32) / 32768.0
        sec = x[: len(x) // 16000 * 16000].reshape(-1, 16000)
        sec_db = 20 * np.log10(np.sqrt((sec ** 2).mean(axis=1)) + 1e-12)
        report[name].append({
            "track": ti + 1, "wav": out, "seconds": round(len(x) / 16000, 1),
            "rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1),
            "peak_dbfs": round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 1),
            "active_pct": round(float((sec_db > -40).mean() * 100), 1),
        })
        print(name, report[name][-1], flush=True)
json.dump(report, open(os.path.join(out_dir, "audio_tracks.json"), "w"), indent=2)
