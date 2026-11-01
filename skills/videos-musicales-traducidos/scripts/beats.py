"""Tempo + beat grid of a song (spectral-flux onsets, autocorrelation).

Usage: python beats.py in.wav t0 t1 [show_from-show_to ...]
"""
import sys
import wave

import numpy as np

w = wave.open(sys.argv[1])
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32).mean(1) / 32768
t0, t1 = float(sys.argv[2]), float(sys.argv[3])
hop, n = 441, 2048
frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
S = np.log1p(np.abs(np.fft.rfft(frames, axis=1)) * 100)
flux = np.concatenate([[0], np.maximum(0, np.diff(S, axis=0)).sum(1)])
fps = sr / hop
o = np.maximum(flux - np.convolve(flux, np.ones(20) / 20, mode="same"), 0)
seg = o[int(t0 * fps):int(t1 * fps)]
ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
lags = np.arange(len(ac)) / fps
rng = (lags > 60 / 180) & (lags < 60 / 70)
P = lags[rng][np.argmax(ac[rng])]
offs = np.arange(0, P, 1 / fps)
end = len(x) / sr
scores = [o[(np.arange(of, end - 0.1, P) * fps).astype(int)].sum() for of in offs]
ph = offs[int(np.argmax(scores))]
print(f"beat {P:.4f} s  bpm {60 / P:.2f}  phase {ph:.3f}")
grid = np.arange(ph, end, P)
for win in sys.argv[4:]:
    a, b = map(float, win.split("-"))
    print(win, [round(g, 2) for g in grid if a <= g <= b])
