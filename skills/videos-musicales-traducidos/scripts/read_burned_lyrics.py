"""Extract every distinct burned-in lyric caption of a lyric video into contact sheets you can read.

Usage: python read_burned_lyrics.py video.mp4 x y w h out_prefix [rgb_rule]
  x y w h   : caption region in the video's own pixel coords (find it with locate_text_color.py)
  rgb_rule  : "yellow" (default) or "white"
Writes <out_prefix>_00.png, _01.png ... (60 captions per sheet, with appear time in seconds).
Official burned-in lyrics are the best verification source for a sung transcription.
"""
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def mask_of(f16, rule):
    r, g, b = f16[..., 0], f16[..., 1], f16[..., 2]
    if rule == "white":
        return (r > 215) & (g > 215) & (b > 215)
    return (r > 170) & (g > 150) & (b < 110)


def main():
    video, x0, y0, w, h, prefix = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
    rule = sys.argv[7] if len(sys.argv) > 7 else "yellow"
    raw = subprocess.run([FF, "-v", "error", "-i", video, "-vf", f"fps=8,crop={w}:{h}:{x0}:{y0}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    masks = mask_of(fr.astype(np.int16), rule)
    caps, prev = [], None
    for i, m in enumerate(masks):
        if m.sum() < 60:
            prev = None
            continue
        if prev is None or (m ^ prev).sum() > 0.35 * max(m.sum(), prev.sum()):
            caps.append((i / 8, i))
        prev = m
    print(len(caps), "captions")
    tw = 450
    th = max(20, round(h * tw / w))
    tiles = []
    for t, i in caps:
        im = Image.fromarray(fr[min(i + 2, len(fr) - 1)]).resize((tw, th))
        c = Image.new("RGB", (tw + 70, th))
        c.paste(im, (70, 0))
        ImageDraw.Draw(c).text((3, th // 2 - 6), f"{t:6.2f}", fill=(255, 255, 255))
        tiles.append(c)
    per = 60
    for k in range(0, len(tiles), per):
        chunk = tiles[k:k + per]
        cols = 3
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (tw + 70), rows * th))
        for j, t in enumerate(chunk):
            sheet.paste(t, ((j // rows) * (tw + 70), (j % rows) * th))
        sheet.save(f"{prefix}_{k // per:02d}.png")


if __name__ == "__main__":
    main()
