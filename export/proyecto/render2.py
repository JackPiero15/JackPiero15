"""Vertical 9:16 lyric edit, B/W xerox 'swag grunge' style.

Usage: python render2.py piece.json out.mp4            -> full render (video only)
       python render2.py piece.json out.jpg t1 t2 ...  -> stills
"""
import json, math, random, subprocess, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageSequence, ImageChops, ImageOps

W, H, FPS = 1080, 1920, 30
ROOT = pathlib.Path(__file__).resolve().parent.parent
P = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
BEAT, PHASE = P["beat"], P["beat_phase"]
RED = (200, 16, 46)
INK = (12, 12, 12)
PAPER = (246, 245, 240)
ANTON = str(ROOT / "fonts/Anton-Regular.ttf")
GOTH = str(ROOT / "fonts/UnifrakturCook-Bold.ttf")
_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_out_back(x, s=2.0): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def beat_pulse(t, decay=8.0):
    if t < PHASE: return 0.0
    return math.exp(-decay * ((t - PHASE) % BEAT))
def beat_no(t): return int(math.floor((t - PHASE) / BEAT))
def in_ranges(t, rs): return any(a <= t < b for a, b in rs)

# ---------------- xerox helpers ----------------
NOISE = np.random.default_rng(1).normal(0, 1, (H, W)).astype(np.float32)
def xerox(img, k=9.0, mid=0.5, grain=0.07, seed=0, lift=0.0):
    g = np.asarray(ImageOps.autocontrast(img.convert("L"), cutoff=2), np.float32) / 255.0
    h, w = g.shape
    r = np.random.default_rng(seed)
    n = r.normal(0, grain, (h, w)).astype(np.float32)
    v = 1 / (1 + np.exp(-k * (g + n - mid)))
    v = np.clip(v + lift, 0, 1)
    return Image.fromarray((v * 255).astype(np.uint8)).convert("RGB")

def make_paper(seed):
    r = np.random.default_rng(seed)
    base = np.ones((H, W), np.float32) * 245
    n = r.normal(0, 5, (H // 2, W // 2)).astype(np.float32)
    base += np.kron(n, np.ones((2, 2), np.float32))
    # toner specks
    sp = r.random((H, W)) < 0.0009
    base[sp] = r.uniform(40, 140, sp.sum())
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGB")
    return img
PAPERS = [make_paper(s) for s in range(3)]

def collage_layer():
    """Washed-out newspaper collage blocks (like the reference), multiply layer."""
    im = Image.new("L", (W + 240, H + 240), 255)
    d = ImageDraw.Draw(im)
    r = random.Random(11)
    for _ in range(26):
        x, y = r.randint(0, W + 100), r.randint(0, H + 100)
        bw, bh = r.randint(160, 520), r.randint(140, 600)
        tone = r.choice([235, 228, 220, 200, 170, 120])
        d.rectangle([x, y, x + bw, y + bh], fill=tone)
        if tone > 190:   # text lines
            yy = y + 14
            while yy < y + bh - 10:
                ln = int(bw * r.uniform(0.5, 0.95))
                d.rectangle([x + 12, yy, x + 12 + ln, yy + 5], fill=tone - 70); yy += 13
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    arr = np.asarray(im, np.float32)
    arr = 255 - (255 - arr) * 0.42          # wash out
    return Image.fromarray(arr.astype(np.uint8)).convert("RGB")
COLLAGE = collage_layer()

def load(path):
    return Image.open(ROOT / path)

# spiral reference, made square + xerox
SPIRAL = None
if P.get("spiral"):
    s = load(P["spiral"]).convert("RGB")
    m = min(s.size); s = s.crop(((s.size[0] - m) // 2, (s.size[1] - m) // 2, (s.size[0] + m) // 2, (s.size[1] + m) // 2))
    SPIRAL = xerox(s.resize((2300, 2300), Image.LANCZOS), k=7, mid=0.5, grain=0.04)

DECOS = {}
for name, spec in P.get("decos", {}).items():
    im = load(spec["file"]).convert("RGB")
    if spec.get("crop"):
        w0, h0 = im.size; c = spec["crop"]; im = im.crop((int(c[0] * w0), int(c[1] * h0), int(c[2] * w0), int(c[3] * h0)))
    im.thumbnail((spec.get("size", 300), spec.get("size", 300)), Image.LANCZOS)
    if spec.get("xerox"): im = xerox(im, k=10, grain=0.05)
    DECOS[name] = im

# ---------------- media ----------------
class Media:
    def __init__(self, spec, idx):
        self.spec = spec; self.idx = idx
        im = load(spec["file"])
        crop = spec.get("crop")
        self.frames, self.durs = [], []
        for fr in ImageSequence.Iterator(im):
            f = fr.convert("RGB")
            if crop:
                w0, h0 = f.size
                f = f.crop((int(crop[0] * w0), int(crop[1] * h0), int(crop[2] * w0), int(crop[3] * h0)))
            self.frames.append(f)
            self.durs.append(max(fr.info.get("duration", 80), 20) / 1000.0)
        self.total = sum(self.durs)
        self.cut = spec.get("cutout", False)
        self.cache = {}
    def frame(self, lt, bw, bh):
        i = 0
        if len(self.frames) > 1:
            tt = lt % self.total; acc = 0
            for i, d in enumerate(self.durs):
                acc += d
                if acc > tt: break
        k = (i, bw, bh)
        if k not in self.cache:
            f = self.frames[i]
            s = max(bw / f.size[0], bh / f.size[1])
            g = f.resize((max(1, int(f.size[0] * s + .5)), max(1, int(f.size[1] * s + .5))), Image.LANCZOS)
            l = int((g.size[0] - bw) * self.spec.get("fx", .5)); t = int((g.size[1] - bh) * self.spec.get("fy", .5))
            g = g.crop((l, t, l + bw, t + bh))
            g = xerox(g, k=self.spec.get("k", 8.0), mid=self.spec.get("mid", 0.5), grain=0.06, seed=self.idx * 97 + i,
                      lift=0.0)
            if len(self.cache) > 300: self.cache.clear()
            self.cache[k] = g
        return self.cache[k]

MEDIA = [Media(m, i) for i, m in enumerate(P["media"])]
SHOTS = P["shots"]; SUBS = P["subs"]

# ---------------- lyrics ----------------
def rough(mask, seed):
    """Photocopy edges: blur + noise + threshold on an L mask."""
    a = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255.0
    h, w = a.shape
    n = np.random.default_rng(seed).normal(0, 0.18, (h, w)).astype(np.float32)
    v = (a + n * (a * (1 - a)) * 2.2) > 0.5
    return Image.fromarray((v * 255).astype(np.uint8))

def word_img(word, size, accent, seed):
    if accent:
        f = font(GOTH, int(size * 1.6)); col = RED; stretch = 1.0
        txt = word
    else:
        f = font(ANTON, size); col = INK; stretch = 1.22
        txt = word.upper()
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + 8, b - t + 8
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((4 - l, 4 - t), txt, font=f, fill=255)
    m = m.resize((w, int(h * stretch)), Image.LANCZOS)
    m = rough(m, seed)
    pad = 14
    big = Image.new("L", (m.size[0] + 2 * pad, m.size[1] + 2 * pad), 0); big.paste(m, (pad, pad))
    stroke = rough(big.filter(ImageFilter.MaxFilter(17)), seed + 5)
    out = Image.new("RGBA", big.size, (255, 255, 255, 0)); out.putalpha(stroke)
    txt_l = Image.new("RGBA", big.size, col + (0,)); txt_l.putalpha(big)
    out.alpha_composite(txt_l)
    return out

def layout(text, seed, max_w=800, base=150, xc=505):
    lines = [s.strip() for s in text.split("|")]
    size = base
    while True:
        rows = []
        for li, line in enumerate(lines):
            ws = []
            for wi, w in enumerate(line.split()):
                acc = w.startswith("*") and w.endswith("*")
                ws.append(word_img(w.strip("*"), size, acc, seed + li * 31 + wi))
            gap = int(size * 0.02)
            width = sum(i.size[0] for i in ws) + gap * (len(ws) - 1)
            rows.append((ws, width, gap))
        if all(r[1] <= max_w for r in rows) or size <= 70: break
        size -= 6
    items, y, order = [], 0, 0
    heights = [max(i.size[1] for i in r[0]) for r in rows]
    total = sum(heights) + int(size * 0.05) * (len(rows) - 1)
    for (ws, width, gap), rh in zip(rows, heights):
        x = xc - width / 2
        for im in ws:
            items.append((im, x, y + (rh - im.size[1]) / 2 - total / 2, order)); order += 1
            x += im.size[0] + gap
        y += rh + int(size * 0.05)
    return items, total, order
SUBC = {}
def sub_layout(i):
    if i not in SUBC:
        s = SUBS[i]; SUBC[i] = layout(s["es"], 500 + 13 * i, base=s.get("size", 150))
    return SUBC[i]

# ---------------- frame ----------------
def paste_mult(frame, img, x, y):
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + img.size[0]), min(H, y + img.size[1])
    if x1 <= x0 or y1 <= y0: return
    sub = img.crop((x0 - x, y0 - y, x1 - x, y1 - y)).convert("RGB")
    reg = frame.crop((x0, y0, x1, y1)).convert("RGB")
    frame.paste(ImageChops.multiply(reg, sub), (x0, y0))

def draw_frame(t):
    fr = ImageChops.multiply(PAPERS[int(t * 12) % 3], COLLAGE.crop((int(120 + 50 * math.sin(t * .3)), int(120 + 60 * math.cos(t * .23)),
                                                                      int(120 + 50 * math.sin(t * .3)) + W, int(120 + 60 * math.cos(t * .23)) + H)))
    pulse = beat_pulse(t)
    bn = beat_no(t)
    chorus = in_ranges(t, P.get("chorus", []))
    hyp = in_ranges(t, P.get("hypno", []))

    # spiral
    if SPIRAL is not None:
        strength = 0.8 if hyp else (0.33 if chorus else 0.14)
        sc = 1.0 + 0.05 * pulse
        sp = SPIRAL.rotate(-t * (150 if hyp else 55), resample=Image.BILINEAR)
        cw, ch = int(W / sc), int(H / sc)
        cx, cy = 1150, 1150 + (960 - 780)
        sp = sp.crop((cx - cw // 2, cy - ch // 2, cx - cw // 2 + cw, cy - ch // 2 + ch)).resize((W, H), Image.BILINEAR)
        arr = 255 - (255 - np.asarray(sp, np.float32)) * strength
        fr = ImageChops.multiply(fr, Image.fromarray(arr.astype(np.uint8)))

    # red star-skull flashes behind photo
    for a, b in P.get("star_flash", []):
        if a <= t < b and "skull" in DECOS:
            im = DECOS["skull"]; e = ease_out_back((t - a) / 0.25)
            s2 = max(.05, e) * (1 + .08 * pulse)
            im2 = im.resize((int(im.size[0] * s2), int(im.size[1] * s2)), Image.BILINEAR)
            paste_mult(fr, im2, W / 2 - im2.size[0] / 2 + 300, 330 - im2.size[1] / 2 + 60)

    # media
    cur = None
    for s in SHOTS:
        if s["t"] <= t: cur = s
    if cur:
        lt = t - cur["t"]; m = MEDIA[cur["m"]]
        bw, bh = cur.get("w", 800), cur.get("h", 800)
        img = m.frame(lt, bw, bh)
        enter = ease_out_expo(lt / 0.25)
        sc = (1.12 - 0.12 * enter) * (1 + 0.05 * pulse)
        im2 = img.resize((int(bw * sc), int(bh * sc)), Image.BILINEAR)
        # 12fps jitter
        jr = random.Random(int(t * 12))
        jx, jy = jr.randint(-4, 4), jr.randint(-4, 4)
        x = W / 2 - im2.size[0] / 2 + cur.get("x", 0) + jx
        y = cur.get("y", 770) - im2.size[1] / 2 + jy
        if m.cut:
            paste_mult(fr, im2, x, y)
        else:
            d = ImageDraw.Draw(fr)
            d.rectangle([x - 10, y - 10, x + im2.size[0] + 9, y + im2.size[1] + 9], fill=INK)
            fr.paste(im2, (int(x), int(y)))
            # torn tape label
            if cur.get("tag"):
                f = font(ANTON, 54)
                tw = f.getlength(cur["tag"])
                d.rectangle([x + 20, y + im2.size[1] - 40, x + 60 + tw, y + im2.size[1] + 40], fill=(255, 255, 255))
                d.text((x + 40, y + im2.size[1] - 38), cur["tag"], font=f, fill=RED)

    # gothic crosses
    for name, a, b, cx, cy, rot in [tuple(c) for c in P.get("crosses", [])]:
        if a <= t < b and name in DECOS:
            if random.Random(int(t * 15) + int(cx)).random() < 0.12: continue   # flicker
            im = DECOS[name]
            s2 = (1 + 0.12 * pulse)
            im2 = im.resize((int(im.size[0] * s2), int(im.size[1] * s2)), Image.BILINEAR).rotate(rot + 4 * math.sin(t * 2), fillcolor=(255, 255, 255), resample=Image.BILINEAR)
            paste_mult(fr, im2, cx - im2.size[0] / 2, cy - im2.size[1] / 2)

    # lyrics
    for i, s in enumerate(SUBS):
        if s["t0"] - 0.03 <= t < s["t1"]:
            items, total, n = sub_layout(i)
            lt = t - s["t0"]
            yc = s.get("y", 1350)
            boil = random.Random(int(t * 12) * 7 + i)
            reveal = min(0.42, (s["t1"] - s["t0"]) * 0.35)
            for im, x, y, order in items:
                ts = reveal * order / max(n - 1, 1) if n > 1 else 0
                a = (lt - ts) / 0.12
                if a <= 0: continue
                sc = 1.35 - 0.35 * ease_out_expo(a)
                sc *= 1 + 0.04 * pulse
                w2, h2 = int(im.size[0] * sc), int(im.size[1] * sc)
                im2 = im.resize((w2, h2), Image.BILINEAR)
                px = x + im.size[0] / 2 - w2 / 2 + boil.randint(-2, 2)
                py = yc + y + im.size[1] / 2 - h2 / 2 + boil.randint(-2, 2)
                fr.paste(im2, (int(px), int(py)), im2)

    # invert flash on chorus downbeats
    if chorus and bn % 4 == 0 and ((t - PHASE) % BEAT) < 2 / FPS:
        fr = ImageOps.invert(fr)
    # shake
    if chorus and pulse > 0.4:
        dx, dy = int(9 * pulse * math.sin(t * 91)), int(9 * pulse * math.cos(t * 73))
        fr = fr.transform(fr.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=PAPER)
    # global fade at very end
    end = P["duration"] - t
    if end < 0.5:
        fr = Image.blend(fr, Image.new("RGB", fr.size, (255, 255, 255)), clamp(1 - end / 0.5))
    return fr

if __name__ == "__main__":
    if OUT.endswith((".jpg", ".png")):
        for k, tt in enumerate(sys.argv[3:]):
            draw_frame(float(tt)).save(OUT.replace(".", f"_{k:02d}.", 1) if OUT.count(".") == 1 else OUT, quality=90)
        sys.exit()
    n1 = int(round(P["duration"] * FPS))
    tmp = OUT + ".part.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", tmp], stdin=subprocess.PIPE)
    for n in range(n1):
        ff.stdin.write(draw_frame(n / FPS).tobytes())
        if n % 150 == 0: print(f"frame {n}/{n1}", flush=True)
    ff.stdin.close(); ff.wait()
    if ff.returncode == 0: pathlib.Path(tmp).rename(OUT)
    print("done", ff.returncode, flush=True)
