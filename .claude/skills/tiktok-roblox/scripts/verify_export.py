"""Verify an exported MP4 without ffmpeg.exe: streams, loudness, peaks, A/V start, and a stills sheet.

verify_export.py <video.mp4> <sheet.jpg> <t1> [t2 ...] [--probe t0:t1 ...]
- stills at the given seconds (pick the intro, each meme, each end card) -> look at the sheet
- --probe a:b prints the RMS dBFS in that window (check that an added SFX sounds and a removed one is gone)
Pass criteria for TikTok: 1080x1920, 30 fps, h264 yuv420p, AAC 48 kHz, -14 LUFS +-1, peak <= -1 dB,
audio and video both starting at 0.0.
"""
import av, sys, os, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loudness import decode, lufs, peak_db  # noqa: E402

args = sys.argv[1:]
probes = []
if "--probe" in args:
    i = args.index("--probe"); probes = args[i + 1:]; args = args[:i]
path, sheet_path = args[0], args[1]
times = [float(t) for t in args[2:]]

c = av.open(path)
v, a = c.streams.video[0], c.streams.audio[0]
info = {
    "size_mb": round(os.path.getsize(path) / 1e6, 1), "duration_s": round(c.duration / 1e6, 2),
    "video": {"codec": v.codec_context.name, "profile": v.codec_context.profile, "w": v.codec_context.width,
              "h": v.codec_context.height, "fps": float(v.average_rate), "frames": v.frames,
              "bitrate_mbps": round((v.bit_rate or 0) / 1e6, 1), "pix_fmt": v.codec_context.pix_fmt,
              "start_s": float(v.start_time * v.time_base) if v.start_time is not None else None},
    "audio": {"codec": a.codec_context.name, "sr": a.codec_context.sample_rate,
              "bitrate_kbps": round((a.bit_rate or 0) / 1e3),
              "start_s": float(a.start_time * a.time_base) if a.start_time is not None else None},
}
c.close()
x = decode(path)
info["audio"]["lufs"] = lufs(x)
info["audio"]["peak_db"] = peak_db(x)
mono = x.mean(axis=0)
info["probes"] = {}
for p in probes:
    t0, t1 = (float(s) for s in p.split(":"))
    seg = mono[int(t0 * 48000):int(t1 * 48000)]
    info["probes"][p] = round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)

if times:
    c = av.open(path); vs = c.streams.video[0]
    thumbs = []
    for t in times:
        c.seek(int(t / vs.time_base), stream=vs, backward=True)
        for fr in c.decode(vs):
            if fr.time is not None and fr.time >= t - 0.02:
                thumbs.append((t, fr.to_image().resize((270, 480)))); break
    c.close()
    cols = min(len(thumbs), 5)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 500), "black")
    d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(thumbs):
        x0, y0 = (i % cols) * 270, (i // cols) * 500
        sheet.paste(im, (x0, y0)); d.text((x0 + 4, y0 + 484), f"{int(t // 60)}:{t % 60:04.1f}", fill="yellow")
    sheet.save(sheet_path, quality=85)
print(json.dumps(info, indent=1))
