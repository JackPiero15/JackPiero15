"""Bake lightweight 9:16 clips (1080x1920) for every cut in edit_decisions.json.

bake_clips.py <edit_decisions.json> <out_dir> [scene ...]
Each clip = blurred, darkened fill background + centered stage crop (voice-chat panel removed) with the
foreground zoom alternating per cut (hides jump cuts), plus HANDLE seconds of media on both sides so the
cut can still be trimmed in Blender. Video only: dialogue comes from the leveled stem.
Writes/updates clips_manifest.json: [{file, frames, handle_in, handle_out, cut_frames, scale}] per scene.

Framing comes from edit_decisions.json "framing" (all optional):
  {"fps": 30, "crop_x": [705, 1215], "crop_y": {"C": 40}, "scales": [1.5, 1.65], "bg_dark": 0.55, "handle": 0.5}
crop_x = visible source columns (find the character's x and where the chat starts in a contact sheet);
crop_y = rows to cut top/bottom for a source with black bars.
This is a CPU encode (~17 fps on an i5-13600KF) and is light on the disk: prefer it to live crops/blur in Blender.
"""
import av, sys, os, json, time
from fractions import Fraction
from PIL import Image, ImageFilter, ImageEnhance

dec = json.load(open(sys.argv[1], encoding="utf-8-sig"))
out_dir = sys.argv[2]
only = set(sys.argv[3:])
fr_cfg = dec.get("framing", {})
FPS = fr_cfg.get("fps", dec.get("fps", 30))
CROP_X = tuple(fr_cfg.get("crop_x", (705, 1215)))
CROP_Y = fr_cfg.get("crop_y", {})
SCALES = tuple(fr_cfg.get("scales", (1.50, 1.65)))
BG_DARK = fr_cfg.get("bg_dark", 0.55)
HANDLE = fr_cfg.get("handle", 0.5)
W, H = 1080, 1920
os.makedirs(out_dir, exist_ok=True)
man_path = os.path.join(out_dir, "clips_manifest.json")
manifest = json.load(open(man_path, encoding="utf-8-sig")) if os.path.exists(man_path) else {}


def compose(img, key, scale):
    sw, sh = img.size
    bw = round(sh * W / H)                       # 9:16 slice of the full frame, blurred cheaply at 1/8 size
    x0 = (sw - bw) // 2
    bg = img.crop((x0, 0, x0 + bw, sh)).resize((W // 8, H // 8), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BICUBIC)
    bg = ImageEnhance.Brightness(bg).enhance(BG_DARK)
    cy = CROP_Y.get(key, 0)
    fg = img.crop((CROP_X[0], cy, CROP_X[1], sh - cy))
    fw, fh = round(fg.width * scale), round(fg.height * scale)
    fg = fg.resize((fw, fh), Image.LANCZOS)
    bg.paste(fg, ((W - fw) // 2, (H - fh) // 2))
    return bg


for scene, segs in dec["scenes"].items():
    if only and scene not in only:
        continue
    manifest[scene] = []
    for i, (key, a, b) in enumerate(segs):
        t0 = time.time()
        ha = min(HANDLE, a)
        start, end = a - ha, b + HANDLE
        n_frames = round((end - start) * FPS)
        out = os.path.join(out_dir, f"{scene}_s{i+1:02d}.mp4")
        src = av.open(dec["sources"][key])
        vs = src.streams.video[0]
        vs.thread_type = "AUTO"
        src.seek(int(max(start - 1.0, 0) / vs.time_base), stream=vs)
        dst = av.open(out, "w")
        ost = dst.add_stream("libx264", rate=FPS)
        ost.width, ost.height, ost.pix_fmt = W, H, "yuv420p"
        ost.options = {"crf": "14", "preset": "medium", "g": "15", "bf": "0"}
        for attr in ("colorspace", "color_primaries", "color_trc", "color_range"):
            try:
                setattr(ost.codec_context, attr, 1)   # BT.709, limited range
            except Exception:
                pass
        k, scale = 0, SCALES[i % len(SCALES)]
        for fr in src.decode(vs):
            if fr.time is None or fr.time + 1e-3 < start + k / FPS - 0.5 / 60:
                continue
            comp = compose(fr.to_image(src_colorspace="ITU709"), key, scale)
            vf = av.VideoFrame.from_image(comp).reformat(format="yuv420p", dst_colorspace="ITU709")
            vf.pts, vf.time_base = k, Fraction(1, FPS)
            for p in ost.encode(vf):
                dst.mux(p)
            k += 1
            if k >= n_frames:
                break
        for p in ost.encode():
            dst.mux(p)
        dst.close(); src.close()
        h_in, cut = round(ha * FPS), round(b * FPS) - round(a * FPS)
        if k - h_in < cut:   # the cut runs past the end of the recording: keep what exists and say so
            print(f"  AVISO: {scene} s{i+1:02d} solo tiene {max(k - h_in, 0)} de {cut} fotogramas; acorta este corte "
                  f"en edit_decisions.json y regenera la voz", flush=True)
            cut = max(k - h_in, 1)
        manifest[scene].append({"file": out, "frames": k, "handle_in": h_in, "handle_out": max(k - h_in - cut, 0),
                                "cut_frames": cut, "scale": scale})
        print(scene, f"s{i+1:02d}", k, "frames", round(time.time() - t0, 1), "s", flush=True)
        json.dump(manifest, open(man_path, "w", encoding="utf-8"), indent=2)
