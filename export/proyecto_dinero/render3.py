"""Typing-lyrics edit: black/white word flashes with horizontal blur swaps + dark swag image holds.

Usage: python render3.py piece.json out.mp4
       python render3.py piece.json out.jpg t1 t2 ...
"""
import json, math, os, random, subprocess, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = pathlib.Path(__file__).resolve().parent.parent
P = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
FONT = ImageFont.truetype(str(ROOT / P.get("font", "fonts/RobotoCondensed[wght].ttf")), P.get("font_size", 82))
try:
    FONT.set_variation_by_axes([P.get("font_weight", 400)])
except Exception:
    pass
MAXW = P.get("max_text_w", 860)
TRANS = 4 / FPS          # swap transition length

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)

# ---------------- events ----------------
EV = sorted(P["events"], key=lambda e: e["t"])     # {"t", "text", "mode": "flash"|"hold", "bg": "w"|"b", "img": idx}
def event_at(t):
    cur, nxt, prev = None, None, None
    for i, e in enumerate(EV):
        if e["t"] <= t:
            prev, cur = cur, e
            nxt = EV[i + 1] if i + 1 < len(EV) else None
    return prev, cur, nxt

# ---------------- text ----------------
_tc = {}
def wrap(text):
    words = text.split(" ")
    lines, cur = [], ""
    d = ImageDraw.Draw(Image.new("L", (10, 10)))
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=FONT) > MAXW and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur: lines.append(cur)
    return lines

def text_mask(text, layout_text=None):
    """L mask (W x H) with centered text. layout_text = the full line, so partial text keeps its final position."""
    k = (text, layout_text)
    if k in _tc: return _tc[k]
    lines = wrap(text)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    asc, desc = FONT.getmetrics()
    lh = int((asc + desc) * 1.08)
    y0 = P.get("text_y", 960) - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        d.text((W / 2 - d.textlength(ln, font=FONT) / 2, y0 + i * lh), ln, font=FONT, fill=255)
    if len(_tc) > 200: _tc.clear()
    _tc[k] = m
    return m

def hblur(img, amount):
    """Horizontal motion blur by down/up-scaling on x only."""
    if amount < 1.5: return img
    w, h = img.size
    f = max(2, int(amount))
    return img.resize((max(1, w // f), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)

# ---------------- images (hold mode) ----------------
def xerox(img, k=7.0, mid=0.5):
    g = np.asarray(ImageOps.autocontrast(img.convert("L"), cutoff=1), np.float32) / 255.0
    v = 1 / (1 + np.exp(-k * (g - mid)))
    return Image.fromarray((v * 255).astype(np.uint8))

IMGS = []
for spec in P["images"]:
    im = Image.open(ROOT / spec["file"]).convert("RGB")
    if spec.get("crop"):
        w0, h0 = im.size; c = spec["crop"]
        im = im.crop((int(c[0] * w0), int(c[1] * h0), int(c[2] * w0), int(c[3] * h0)))
    base = 1300 if spec.get("spin") else 1
    tw, th = (2300, 2300) if spec.get("spin") else (int(W * 1.12), int(H * 1.12))
    s = max(tw / im.size[0], th / im.size[1])
    im = im.resize((int(im.size[0] * s + .5), int(im.size[1] * s + .5)), Image.LANCZOS)
    l = int((im.size[0] - tw) * spec.get("fx", .5)); t = int((im.size[1] - th) * spec.get("fy", .5))
    im = im.crop((l, t, l + tw, t + th))
    if spec.get("color"):
        g = im
    else:
        g = xerox(im, k=spec.get("k", 6.0), mid=spec.get("mid", 0.5)) if spec.get("xerox", True) else im.convert("L")
    if spec.get("invert"): g = ImageOps.invert(g)
    IMGS.append((spec, g))

GRAIN = [Image.fromarray(np.clip(128 + np.random.default_rng(s).normal(0, 1, (H // 2, W // 2)) * 14, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR) for s in range(6)]
VIG = None
def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return Image.fromarray((np.clip(1.15 - 0.55 * r ** 2, 0, 1) * 255).astype(np.uint8))
VIG = vignette()

def hold_bg(e, t):
    spec, g = IMGS[e["img"]]
    lt = t - e.get("img_t0", e["t"])
    if spec.get("spin"):
        r = g.rotate(-lt * spec.get("spin"), resample=Image.BILINEAR)
        sc = 1.0 + 0.015 * lt
        cw, ch = int(W / sc), int(H / sc)
        r = r.crop((1150 - cw // 2, 1150 - ch // 2, 1150 - cw // 2 + cw, 1150 - ch // 2 + ch)).resize((W, H), Image.BILINEAR)
    else:
        sc = 1.0 + 0.012 * lt                     # slow push-in, like moving footage
        cw, ch = int(W * 1.12 / sc), int(H * 1.12 / sc)
        cx, cy = g.size[0] / 2 + 6 * math.sin(lt * 0.9), g.size[1] / 2 + 5 * math.cos(lt * 0.7)
        r = g.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx - cw / 2) + cw, int(cy - ch / 2) + ch)).resize((W, H), Image.BILINEAR)
    a = np.asarray(r, np.float32) / 255.0
    vig = np.asarray(VIG, np.float32) / 255.0
    gr = (np.asarray(GRAIN[int(t * 24) % 6], np.float32) - 128) / 255.0 * 0.06
    if a.ndim == 3:
        lum = a.mean(2, keepdims=True)
        a = lum + (a - lum) * 0.85                       # slight desaturation
        a = a * np.array(spec.get("grade", [1.06, 1.0, 0.9]), np.float32)
        a = a * spec.get("dim", 0.5) * vig[..., None] + gr[..., None] + 0.015
    else:
        a = a * spec.get("dim", 0.42) * vig + gr
    a *= 1 + 0.03 * math.sin(t * 37)
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    if P.get("rgb") and out.mode != "RGB": out = out.convert("RGB")
    return out

# ---------------- compose ----------------
def solid(v):
    return Image.new("RGB", (W, H), (v, v, v)) if P.get("rgb") else Image.new("L", (W, H), v)

def layer(e, t):
    """(background L, text value, text mask) for an event at time t (no transition)."""
    if e["mode"] == "hold":
        return hold_bg(e, t), 245
    return (solid(252) if e["bg"] == "w" else solid(2)), (8 if e["bg"] == "w" else 250)

def draw_frame(t):
    prev, cur, nxt = event_at(t)
    if cur is None:
        return Image.new("RGB", (W, H), (0, 0, 0))
    bg, tv = layer(cur, t)
    m = text_mask(cur["text"], cur.get("line"))
    lt = t - cur["t"]
    # incoming transition: first TRANS seconds after an event (blur from previous look into this one)
    swap = cur.get("swap", True) and prev is not None
    if swap and lt < TRANS:
        k = smooth(lt / TRANS)
        pbg, ptv = layer(prev, t)
        pm = text_mask(prev["text"], prev.get("line"))
        mix_bg = Image.blend(pbg, bg, k)
        blur = 55 * math.sin(math.pi * clamp(lt / TRANS))
        # ghost of previous text fading out + new text fading in, both smeared horizontally
        a_prev = hblur(pm, blur).point(lambda v: int(v * clamp(1.6 - 2.2 * k)))
        a_new = hblur(m, blur).point(lambda v: int(v * clamp(2.2 * k - 0.4)))
        tcol_prev = solid(int(ptv + (tv - ptv) * 0.25)); tcol_new = solid(tv)
        out = Image.composite(tcol_prev, mix_bg, a_prev)
        out = Image.composite(tcol_new, out, a_new)
        if blur > 20:
            ghost = hblur(m, blur * 1.4).transform((W, H), Image.AFFINE, (1, 0, -26, 0, 1, 0)).point(lambda v: int(v * 0.4))
            out = Image.composite(solid(int(128 + (tv - 128) * 0.6)), out, ghost)
        frame = out
    else:
        frame = Image.composite(solid(tv), bg, m)
    # hold-mode: soft 2-frame blur when text changes without a bg swap
    if not swap and cur["mode"] == "hold" and prev is not None and lt < 2 / FPS:
        frame = Image.composite(solid(tv), bg, hblur(m, 25))
    tint_e = cur if cur["mode"] == "hold" else (prev if (prev and prev["mode"] == "hold" and lt < TRANS) else None)
    if tint_e is not None and IMGS[tint_e["img"]][0].get("tint"):
        frame = ImageOps.colorize(frame, (0, 0, 0), (242, 248, 255), mid=tuple(IMGS[tint_e["img"]][0]["tint"]))
    end = P["duration"] - t
    if end < P.get("fade_out", 0.6):
        frame = Image.blend(frame.convert("RGB"), Image.new("RGB", (W, H)), clamp(1 - end / P.get("fade_out", 0.6)))
    return frame.convert("RGB") if frame.mode != "RGB" else frame

if __name__ == "__main__":
    if OUT.endswith((".jpg", ".png")):
        stem, ext = OUT.rsplit(".", 1)
        for k, tt in enumerate(sys.argv[3:]):
            draw_frame(float(tt)).save(f"{stem}_{k:02d}.{ext}", quality=92)
        sys.exit()
    n1 = int(round(P["duration"] * FPS))
    tmp = OUT + ".part.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "16"), "-tune", "film", "-x264-params", "aq-mode=3:aq-strength=1.0", "-g", "60", "-pix_fmt", "yuv420p",
                           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", tmp], stdin=subprocess.PIPE)
    for n in range(n1):
        ff.stdin.write(draw_frame(n / FPS).tobytes())
        if n % 150 == 0: print(f"frame {n}/{n1}", flush=True)
    ff.stdin.close(); ff.wait()
    if ff.returncode == 0: pathlib.Path(tmp).rename(OUT)
    print("done", ff.returncode, flush=True)
