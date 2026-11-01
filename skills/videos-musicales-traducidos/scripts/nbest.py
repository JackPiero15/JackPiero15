"""N-best hypotheses for short windows (doubtful sung lines), vocal-band input.

Usage: python nbest.py in.wav model t0-t1 [t0-t1 ...]
"""
import shutil
import os
import subprocess
import sys

import ctranslate2
import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.feature_extractor import FeatureExtractor

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def vocal_band(path, t0, t1):
    cmd = [FF, "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", path,
           "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=150,lowpass=f=6000,dynaudnorm=f=150",
           "-ar", "16000", "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    src, name = sys.argv[1], sys.argv[2]
    wm = WhisperModel(name, device="cpu", compute_type="int8")
    tok = wm.hf_tokenizer
    fe = FeatureExtractor(feature_size=wm.model.n_mels)
    sot = [tok.token_to_id(t) for t in ("<|startoftranscript|>", "<|en|>", "<|transcribe|>", "<|notimestamps|>")]
    for win in sys.argv[3:]:
        t0, t1 = map(float, win.split("-"))
        a = vocal_band(src, t0, t1)
        feats = fe(np.pad(a, (0, max(0, 480000 - len(a))))[:480000])
        sv = ctranslate2.StorageView.from_array(feats[np.newaxis, :, :3000].astype(np.float32))
        r = wm.model.generate(sv, [sot], beam_size=10, num_hypotheses=6, return_scores=True)[0]
        print(f"== {t0:.2f}-{t1:.2f}")
        for ids, sc in zip(r.sequences_ids, r.scores):
            print(f"   {sc:7.3f}  {tok.decode(ids).strip()}")


if __name__ == "__main__":
    main()
