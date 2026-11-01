"""Final delivery: Blender's video-only render + the song segment from the original file.

Usage: python mux.py <piece> <vertical|horizontal>
- Measures integrated loudness / true peak of the exact segment (with its fades).
- Applies gain only (no compression): towards -14 LUFS, never above -1 dBTP.
- Encodes audio once: AAC LC stereo 48 kHz 256 kb/s; video stream copied (no re-encode); +faststart.
- Re-measures the delivered file and writes export/<name>.json with the numbers actually obtained.
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
OUT = {"vertical": ("vertical", "VERTICAL"), "horizontal": ("youtube", "YOUTUBE_COMPLETO_16x9")}


def loudness(args):
    p = subprocess.run([FF, "-hide_banner", "-nostats", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    d = json.loads(m.group(0))
    return float(d["input_i"]), float(d["input_tp"]), float(d["input_lra"])


def main():
    name, fmt = sys.argv[1], sys.argv[2]
    piece = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
    cfg = piece[fmt]
    num, den = cfg.get("fps", piece["fps"])
    fps = num / den
    a_in = round(cfg["in"] * fps) / fps
    a_out = round(cfg["out"] * fps) / fps
    dur = a_out - a_in
    fi, fo = max(1, round(cfg.get("fade_in", 0.04) * fps)) / fps, max(1, round(cfg.get("fade_out", 0.08) * fps)) / fps
    fades = f"afade=t=in:st=0:d={fi:.4f}:curve=qsin,afade=t=out:st={dur - fo:.4f}:d={fo:.4f}:curve=qsin"
    audio = os.path.join(ROOT, piece["audio_file"])
    seg = ["-ss", f"{a_in:.4f}", "-t", f"{dur:.4f}", "-i", audio]
    I, TP, LRA = loudness([*seg, "-af", fades + ",loudnorm=print_format=json", "-f", "null", "-"])
    gain = min(-14.0 - I, -1.3 - TP)          # 0.3 dB margin for AAC overs
    folder, suf = OUT[fmt]
    os.makedirs(os.path.join(ROOT, folder), exist_ok=True)
    out = os.path.join(ROOT, folder, f"{piece['id']}_{suf}.mp4")
    video = os.path.join(ROOT, "render", f"{piece['id']}_{suf}_video.mp4")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", video, *seg,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-af", f"{fades},volume={gain:.2f}dB,aresample=48000:filter_size=64:cutoff=0.97",
                    "-c:a", "aac", "-b:a", "256k", "-ac", "2", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    I2, TP2, LRA2 = loudness(["-i", out, "-af", "loudnorm=print_format=json", "-vn", "-f", "null", "-"])
    info = {"file": out, "segment_src_s": [round(a_in, 3), round(a_out, 3)], "duration_s": round(dur, 3),
            "source_segment": {"I_LUFS": I, "TP_dBTP": TP, "LRA": LRA}, "gain_dB": round(gain, 2),
            "delivered": {"I_LUFS": I2, "TP_dBTP": TP2, "LRA": LRA2}}
    os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
    json.dump(info, open(os.path.join(ROOT, "export", f"{piece['id']}_{suf}.json"), "w"), indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
