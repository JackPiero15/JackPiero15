"""Transcribe 16 kHz mono WAVs with faster-whisper (Spanish, word timestamps) -> <name>.json + readable <name>.txt.

transcribe.py <out_dir> <wav> [wav ...]
Env: WMODEL (default "small"), WLANG (default "es"). Run in the background: ~6 min per 20 min of audio on CPU.
Audio is passed as a numpy array because faster-whisper's own av.open() call breaks with PyAV 19.
"""
import sys, os, json, time, wave
import numpy as np
from faster_whisper import WhisperModel

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
model = WhisperModel(os.environ.get("WMODEL", "small"), device="cpu", compute_type="int8")
for wav in sys.argv[2:]:
    t0 = time.time()
    with wave.open(wav) as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, language=os.environ.get("WLANG", "es"), word_timestamps=True,
                                  vad_filter=True, vad_parameters={"min_silence_duration_ms": 400}, beam_size=5)
    data = []
    base = os.path.splitext(os.path.basename(wav))[0]
    with open(os.path.join(out_dir, base + ".txt"), "w", encoding="utf-8") as txt:
        for s in segs:
            words = [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)} for w in (s.words or [])]
            data.append({"s": round(s.start, 2), "e": round(s.end, 2), "text": s.text.strip(), "words": words})
            m, sec = divmod(s.start, 60)
            txt.write(f"[{int(m):02d}:{sec:05.2f}-{s.end:7.2f}] {s.text.strip()}\n")
            txt.flush()
    json.dump(data, open(os.path.join(out_dir, base + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(base, "done", round(time.time() - t0), "s", flush=True)
