"""Second-opinion transcription of a time window, line by line.

Vocal-focused input: mid channel (L+R), band-passed 150-6000 Hz with ffmpeg, then each
window is transcribed by several faster-whisper models so disagreements stand out.
Also prints an RMS envelope (100 ms) of the vocal band so line edges can be checked.

Usage: python recheck_lines.py in.wav t0 t1 out.json
"""
import json
import shutil
import os
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def vocal_band(path, t0, t1):
    cmd = [FF, "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", path,
           "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=150,lowpass=f=6000,dynaudnorm=f=150",
           "-ar", "16000", "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def main():
    sys.stdout.reconfigure(encoding="utf-8")      # whisper may emit emoji on instrumentals
    src, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    audio = vocal_band(src, t0, t1)
    res = {"t0": t0, "t1": t1, "models": {}}
    for name in ("medium", "small"):
        m = WhisperModel(name, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(audio, language="en", word_timestamps=True, beam_size=8,
                               condition_on_previous_text=False, vad_filter=False)
        lines = []
        for s in segs:
            ws = [{"w": w.word, "s": round(w.start + t0, 3), "e": round(w.end + t0, 3),
                   "p": round(w.probability, 3)} for w in (s.words or [])]
            lines.append({"start": round(s.start + t0, 3), "end": round(s.end + t0, 3),
                          "text": s.text.strip(), "words": ws})
            low = [w["w"].strip() for w in ws if w["p"] < 0.5]
            print(f"[{name}] {s.start + t0:7.2f}-{s.end + t0:7.2f} {s.text.strip()}"
                  + (f"   (low conf: {', '.join(low)})" if low else ""), flush=True)
        res["models"][name] = lines
    hop = 1600
    rms = [float(np.sqrt(np.mean(audio[i:i + hop] ** 2))) for i in range(0, len(audio) - hop, hop)]
    res["rms_100ms"] = [round(v, 4) for v in rms]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
