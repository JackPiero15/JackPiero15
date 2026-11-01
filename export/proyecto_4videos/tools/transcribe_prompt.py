import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=4)
pcm = subprocess.run(["ffmpeg","-v","error","-i",sys.argv[2],"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
audio = np.frombuffer(pcm, np.float32)
prompt = open(sys.argv[3], encoding="utf-8").read()
segs, _ = m.transcribe(audio, language=sys.argv[5], word_timestamps=True, initial_prompt=prompt,
                       beam_size=5, condition_on_previous_text=True, vad_filter=True,
                       vad_parameters={"min_silence_duration_ms": 300, "threshold": 0.3})
out=[{"start":s.start,"end":s.end,"text":s.text.strip(),"words":[{"w":w.word,"s":round(w.start,2),"e":round(w.end,2),"p":round(w.probability,2)} for w in s.words]} for s in segs]
json.dump(out, open(sys.argv[4],"w",encoding="utf-8"), ensure_ascii=False, indent=1)
for s in out: print(f"{s['start']:6.2f}-{s['end']:6.2f} {s['text']}")
