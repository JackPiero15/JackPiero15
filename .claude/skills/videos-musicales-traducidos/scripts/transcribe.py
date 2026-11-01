"""Transcribe a song with faster-whisper (word timestamps) -> JSON.

Usage: python transcribe.py in.wav out.json [model]
Audio is decoded with PyAV into numpy (faster-whisper's own av.open breaks with PyAV 19).
"""
import json
import sys

import av
import numpy as np
from faster_whisper import WhisperModel


def load_16k_mono(path):
    c = av.open(path)
    rs = av.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks = []
    for fr in c.decode(audio=0):
        for o in rs.resample(fr):
            chunks.append(o.to_ndarray().reshape(-1))
    for o in rs.resample(None):
        chunks.append(o.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def main():
    src, out = sys.argv[1], sys.argv[2]
    model_name = sys.argv[3] if len(sys.argv) > 3 else "medium"
    audio = load_16k_mono(src)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, info = model.transcribe(
        audio, language="en", word_timestamps=True, vad_filter=False,
        beam_size=5, condition_on_previous_text=False,
    )
    data = []
    for s in segs:
        data.append({
            "start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
            "words": [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3),
                       "p": round(w.probability, 3)} for w in (s.words or [])],
        })
        print(f"{s.start:7.2f}-{s.end:7.2f}  {s.text.strip()}", flush=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"model": model_name, "segments": data}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
