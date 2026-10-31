import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
model = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=4)
for path in sys.argv[2:]:
    lang = "es" if "de_mi" in path else "en"
    pcm = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
    audio = np.frombuffer(pcm, np.float32)
    segs, info = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False,
                                  beam_size=5, condition_on_previous_text=False)
    out = []
    for s in segs:
        out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                    "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 2)} for w in s.words]})
    dst = path.replace("media/audio", "work").replace(".mp3", f".{sys.argv[1]}.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok", dst, flush=True)
