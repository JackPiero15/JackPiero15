#!/usr/bin/env python3
"""Motor «Cuaderno» — render vertical 1080x1920 a partir de un episodio JSON.

Estilo: cuaderno de laboratorio (papel, cuadrícula, tinta con «line boil»,
trama de puntos, un solo color de acento). Todo es procedural: no usa
imágenes generadas por IA, así que cada episodio es editable al detalle.

Uso:
  python3 cuaderno.py episodio.json salida.mp4 [--desde 0 --hasta 99]
                      [--voz voz.wav] [--fotograma 12.5 portada.png] [--workers 4]

Salidas junto al mp4: .srt (subtítulos) y _locucion.txt (guion con tiempos
para grabar la voz). Ver ../PLANTILLA.md para el formato del JSON.
"""
import argparse, json, math, os, subprocess, sys, wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, SS, FPS = 1080, 1920, 2, 30
FONTS = {
    "titulo": "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "titulo2": "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf",
    "cuerpo": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "cuerpo_b": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "mono": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf",
}
EP = None          # episodio cargado (por proceso)
PAL = {}           # paleta resuelta


# ───────────────────────── utilidades ─────────────────────────
def hexrgb(h):
    h = PAL.get(h, h)
    if isinstance(h, (list, tuple)):
        return tuple(h)
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


EASE = {
    "lin": lambda x: x,
    "in": lambda x: x * x * x,
    "out": lambda x: 1 - (1 - x) ** 3,
    "io": lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2,
    "back": lambda x: 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2,
}


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def kv(v, t, default=None):
    """Valor animable: escalar o [[t, valor, easing?], ...] (tiempos absolutos)."""
    if v is None:
        return default
    if not isinstance(v, list) or not v or not isinstance(v[0], list):
        return v
    if t <= v[0][0]:
        return v[0][1]
    for a, b in zip(v, v[1:]):
        if t <= b[0]:
            e = EASE[b[2] if len(b) > 2 else "io"]
            u = e(clamp((t - a[0]) / max(1e-6, b[0] - a[0])))
            if isinstance(a[1], (list, tuple)):
                return [x + (y - x) * u for x, y in zip(a[1], b[1])]
            return a[1] + (b[1] - a[1]) * u
    return v[-1][1]


def rng_noise(seed, k):
    """Ruido determinista barato en [-1, 1]."""
    x = math.sin(seed * 12.9898 + k * 78.233) * 43758.5453
    return (x - math.floor(x)) * 2 - 1


# ───────────────────────── cámara / contexto ─────────────────────────
class Ctx:
    def __init__(self, img, t, frame, cam):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.t = t
        self.frame = frame
        self.z, self.cx, self.cy, self.rot = cam
        boil = EP["estilo"].get("boil_fps", 10)
        self.seed = int(t * boil)              # cambia ~10 veces/seg → línea viva
        self.boil_amp = EP["estilo"].get("boil_px", 1.6)
        cr, sr = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        self._r = (cr, sr)

    def P(self, x, y):
        dx, dy = (x - self.cx) * self.z, (y - self.cy) * self.z
        cr, sr = self._r
        return ((dx * cr - dy * sr + W / 2) * SS, (dx * sr + dy * cr + H / 2) * SS)

    def S(self, v):
        return v * self.z * SS


def jitter_path(pts, seed, amp, closed=False):
    """Line boil: desplazamiento suave a lo largo del trazo, nueva semilla ~10 fps."""
    if amp <= 0:
        return pts
    out, s = [], 0.0
    ph = [rng_noise(seed, i) * 6.28 for i in range(4)]
    for i, (x, y) in enumerate(pts):
        if i:
            s += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        dx = amp * (math.sin(s * .021 + ph[0]) * .7 + math.sin(s * .057 + ph[1]) * .3)
        dy = amp * (math.sin(s * .019 + ph[2]) * .7 + math.sin(s * .061 + ph[3]) * .3)
        out.append((x + dx, y + dy))
    if closed and out:
        out[-1] = out[0]
    return out


def resample(pts, step=10.0):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for k in range(1, n + 1):
            u = k / n
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def catmull(pts, n=14):
    if len(pts) < 3:
        return pts
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def cut_path(pts, prog):
    if prog >= 1:
        return pts
    if prog <= 0 or len(pts) < 2:
        return pts[:1]
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    target, acc, out = sum(seg) * prog, 0.0, [pts[0]]
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if acc + L >= target:
            u = (target - acc) / max(L, 1e-6)
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            return out
        out.append(b)
        acc += L
    return out


def rrect_pts(x0, y0, x1, y1, r, n=8):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def ellipse_pts(cx, cy, rx, ry, n=64, a0=0.0, sweep=360.0, wobble=0.0, seed=0):
    pts = []
    for k in range(n + 1):
        a = math.radians(a0 + sweep * k / n)
        w = 1 + wobble * (k / n)                       # círculo a mano: no cierra perfecto
        pts.append((cx + rx * w * math.cos(a), cy + ry * w * math.sin(a)))
    return pts


def rot_pts(pts, cx, cy, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def stroke(ctx, pts, width, color, alpha=1.0, prog=1.0, closed=False, boil=True):
    if len(pts) < 2 or alpha <= 0:
        return
    pts = resample(pts, 9)
    if boil:
        pts = jitter_path(pts, ctx.seed, ctx.boil_amp, closed)
    pts = cut_path(pts, prog)
    if len(pts) < 2:
        return
    sp = [ctx.P(*p) for p in pts]
    w = max(1, int(round(ctx.S(width))))
    col = hexrgb(color) + (int(255 * alpha),)
    ctx.d.line(sp, fill=col, width=w, joint="curve")
    r = w / 2
    for (x, y) in (sp[0], sp[-1]):
        ctx.d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def fill_poly(ctx, pts, color, alpha=1.0, boil=True):
    if alpha <= 0:
        return
    pts = resample(pts, 12)
    if boil:
        pts = jitter_path(pts, ctx.seed + 7, ctx.boil_amp * .8, True)
    ctx.d.polygon([ctx.P(*p) for p in pts], fill=hexrgb(color) + (int(255 * alpha),))


@lru_cache(maxsize=8)
def halftone_tile(spacing, radius):
    """Trama de puntos 2x (máscara L)."""
    s = int(spacing * SS)
    tile = Image.new("L", (s * 2, s * 2), 0)
    d = ImageDraw.Draw(tile)
    r = radius * SS
    for cx, cy in ((s / 2, s / 2), (s * 1.5, s * 1.5), (s * 1.5, s / 2), (s / 2, s * 1.5)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    big = Image.new("L", (W * SS, H * SS))
    for y in range(0, H * SS, s * 2):
        for x in range(0, W * SS, s * 2):
            big.paste(tile, (x, y))
    return big


def halftone_fill(ctx, pts, color, alpha=1.0, spacing=14, radius=3.2):
    pts = jitter_path(resample(pts, 12), ctx.seed + 3, ctx.boil_amp * .8, True)
    m = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(m).polygon([ctx.P(*p) for p in pts], fill=int(255 * alpha))
    mask = Image.fromarray((np.asarray(m, np.uint16) * np.asarray(halftone_tile(spacing, radius), np.uint16) // 255).astype(np.uint8))
    layer = Image.new("RGBA", m.size, hexrgb(color) + (255,))
    ctx.img.paste(layer, (0, 0), mask)


def silhouette(ctx, polys, fill, ink, width, alpha=1.0, prog=1.0):
    """Unión de polígonos con contorno uniforme (sin líneas internas)."""
    if alpha <= 0:
        return
    jp = [jitter_path(resample(p, 10), ctx.seed + i, ctx.boil_amp, True) for i, p in enumerate(polys)]
    sp = [[ctx.P(*q) for q in p] for p in jp]
    xs = [q[0] for p in sp for q in p]
    ys = [q[1] for p in sp for q in p]
    pad = int(ctx.S(width)) + 4
    x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
    x1, y1 = int(max(xs)) + pad, int(max(ys)) + pad
    if x1 <= x0 or y1 <= y0:
        return
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    md = ImageDraw.Draw(m)
    for p in sp:
        md.polygon([(x - x0, y - y0) for x, y in p], fill=255)
    # contorno: trazos de 2×grosor de cada polígono, recortados por el relleno de la unión
    e = Image.new("L", m.size, 0)
    ed = ImageDraw.Draw(e)
    lw = max(2, int(ctx.S(width) * 1.6))
    for p in sp:
        q = [(x - x0, y - y0) for x, y in p]
        ed.line(q + [q[0]], fill=255, width=lw, joint="curve")
    edge = Image.fromarray((np.asarray(e, np.uint16) * (255 - np.asarray(m, np.uint16)) // 255).astype(np.uint8))
    if prog < 1:   # revela de abajo hacia arriba
        cut = int((y1 - y0) * (1 - prog))
        ImageDraw.Draw(edge).rectangle([0, 0, x1 - x0, cut], fill=0)
        ImageDraw.Draw(m).rectangle([0, 0, x1 - x0, cut], fill=0)
    a = int(255 * alpha)
    if fill:
        ctx.img.paste(Image.new("RGBA", m.size, hexrgb(fill) + (a,)), (x0, y0), m)
    ctx.img.paste(Image.new("RGBA", m.size, hexrgb(ink) + (a,)), (x0, y0), edge.point(lambda v: v * alpha))


# ───────────────────────── texto ─────────────────────────
@lru_cache(maxsize=64)
def font(name, size):
    return ImageFont.truetype(FONTS.get(name, name), max(4, int(size)))


def parse_marks(txt):
    """'hola *mundo*' → [('hola', False), ('mundo', True)] por palabra; '\n' = salto."""
    words = []
    for line_i, line in enumerate(txt.split("\n")):
        if line_i:
            words.append(("\n", False))
        acc = False
        for w in line.split(" "):
            if not w:
                continue
            st = w.startswith("*")
            acc = acc or st
            clean = w.replace("*", "")
            words.append((clean, acc))
            if w.endswith("*") and (len(w) > 1 or not st):
                acc = False
    return words


@lru_cache(maxsize=256)
def layout(txt, fname, size, maxw, lh):
    f = font(fname, size * SS)
    space = f.getlength(" ")
    lines, cur, curw = [], [], 0.0
    for w, acc in parse_marks(txt):
        if w == "\n":
            lines.append(cur); cur, curw = [], 0.0; continue
        ww = f.getlength(w)
        if cur and curw + space + ww > maxw * SS:
            lines.append(cur); cur, curw = [], 0.0
        cur.append((w, acc, ww))
        curw += (space if len(cur) > 1 else 0) + ww
    lines.append(cur)
    asc, desc = f.getmetrics()
    lineh = (asc + desc) * lh
    out = []   # (word, accent, x_center_rel, y_center_rel, w)
    total_h = lineh * len(lines)
    for li, ln in enumerate(lines):
        lw = sum(x[2] for x in ln) + space * max(0, len(ln) - 1)
        x = -lw / 2
        y = -total_h / 2 + lineh * (li + .5)
        for w, acc, ww in ln:
            out.append((w, acc, x + ww / 2, y, ww))
            x += ww + space
    return out, total_h, (asc + desc)


@lru_cache(maxsize=512)
def word_img(w, fname, size_px, color, stroke_px=0, stroke_col=None):
    f = font(fname, size_px)
    bb = f.getbbox(w, stroke_width=stroke_px)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(bb[2] - min(0, bb[0]) + 8 + stroke_px * 2), asc + desc + 8 + stroke_px * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 + stroke_px, 4 + stroke_px), w, font=f, fill=hexrgb(color),
                            stroke_width=stroke_px, stroke_fill=hexrgb(stroke_col) if stroke_col else None)
    return im


def paste_word(ctx, w, fname, size, color, cx, cy, scale=1.0, alpha=1.0, rot=0.0, screen=False):
    """Pega una palabra centrada en (cx, cy) (coords de mundo, o pantalla 2x si screen)."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    z = 1 if screen else ctx.z
    px = max(6, int(round(size * SS * z * scale)))
    im = word_img(w, fname, px, color)
    if rot or ctx.rot and not screen:
        im = im.rotate(-(rot + (0 if screen else ctx.rot)), resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    X, Y = (cx, cy) if screen else ctx.P(cx, cy)
    ctx.img.alpha_composite(im, (int(X - im.width / 2), int(Y - im.height / 2)))


def appear(el, t):
    """Factor de entrada/salida (0..1) y progreso de entrada."""
    a, b = el["t"]
    fi = el.get("fi", .22)
    fo = el.get("fo", .18)
    pin = clamp((t - a) / fi) if fi > 0 else 1.0
    pout = clamp((b - t) / fo) if fo > 0 else 1.0
    return pin, pout


# ───────────────────────── primitivas ─────────────────────────
def el_texto(ctx, el, t):
    pin, pout = appear(el, t)
    if pin <= 0 or pout <= 0:
        return
    x, y = kv(el["x"], t), kv(el["y"], t)
    size = kv(el.get("size", 80), t)
    fname = el.get("fuente", "titulo")
    col = el.get("color", "tinta")
    acc = el.get("acento", "acento")
    words, _, _ = layout(el["txt"], fname, size, el.get("ancho", 900), el.get("lh", 1.0))
    stag = el.get("stagger", .07)
    mode = el.get("entrada", "pop")
    rot = kv(el.get("rot", 0), t)
    for i, (w, isacc, rx, ry, _) in enumerate(words):
        lt = t - el["t"][0] - i * stag
        p = clamp(lt / el.get("fi", .22)) if mode != "fade" else pin
        if p <= 0:
            continue
        sc = EASE["back"](p) if mode == "pop" else 1.0
        dy = (1 - EASE["out"](p)) * 40 if mode == "sube" else 0
        rx_r, ry_r = rx / SS, ry / SS + dy
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            rx_r, ry_r = rx_r * c - ry_r * s, rx_r * s + ry_r * c
        paste_word(ctx, w, fname, size, acc if isacc else col, x + rx_r, y + ry_r,
                   scale=sc, alpha=min(1, p * 1.5) * pout, rot=rot)


def el_trazo(ctx, el, t):
    pin, pout = appear(el, t)
    if pout <= 0 or t < el["t"][0]:
        return
    pts = [tuple(p) for p in el["pts"]]
    if el.get("curva", True):
        pts = catmull(pts)
    prog = EASE["out"](clamp((t - el["t"][0]) / el.get("dibujo", .5)))
    w = el.get("grosor", 7)
    col = el.get("color", "tinta")
    stroke(ctx, pts, w, col, pout, prog)
    if el.get("flecha") and prog > .98:
        (x1, y1), (x2, y2) = pts[-3] if len(pts) > 2 else pts[0], pts[-1]
        ang = math.atan2(y2 - y1, x2 - x1)
        L = el.get("punta", 34)
        for s in (-1, 1):
            a = ang + math.pi + s * .5
            stroke(ctx, [(x2, y2), (x2 + L * math.cos(a), y2 + L * math.sin(a))], w, col, pout)


def el_marca(ctx, el, t):
    """Marcas a mano: circulo (rodear), check, cruz, subrayado."""
    pin, pout = appear(el, t)
    if pout <= 0 or t < el["t"][0]:
        return
    x, y = kv(el["x"], t), kv(el["y"], t)
    prog = EASE["out"](clamp((t - el["t"][0]) / el.get("dibujo", .45)))
    col, w, k = el.get("color", "acento"), el.get("grosor", 8), el["forma"]
    s = kv(el.get("s", 1), t)
    if k == "circulo":
        rx, ry = el.get("rx", 120) * s, el.get("ry", 80) * s
        stroke(ctx, ellipse_pts(x, y, rx, ry, 70, -200, 380, .08), w, col, pout, prog)
    elif k == "check":
        pts = [(x - 50 * s, y), (x - 12 * s, y + 42 * s), (x + 60 * s, y - 55 * s)]
        stroke(ctx, pts, w, col, pout, prog)
    elif k == "cruz":
        stroke(ctx, [(x - 45 * s, y - 45 * s), (x + 45 * s, y + 45 * s)], w, col, pout, clamp(prog * 2))
        stroke(ctx, [(x + 45 * s, y - 45 * s), (x - 45 * s, y + 45 * s)], w, col, pout, clamp(prog * 2 - 1))
    elif k == "subrayado":
        L = el.get("largo", 300) * s
        pts = [(x - L / 2, y), (x - L / 6, y + 6), (x + L / 6, y - 3), (x + L / 2, y + 4)]
        stroke(ctx, catmull(pts), w, col, pout, prog)


def el_caja(ctx, el, t):
    """Rectángulo redondeado (relleno opcional, trama opcional, contorno)."""
    pin, pout = appear(el, t)
    a = min(pin, pout)
    if a <= 0:
        return
    x, y, w, h = (kv(el[k], t) for k in ("x", "y", "w", "h"))
    s = EASE["back"](pin) if el.get("entrada") == "pop" else 1
    w, h = w * s, h * s
    pts = rrect_pts(x - w / 2, y - h / 2, x + w / 2, y + h / 2, el.get("r", 28))
    rot = kv(el.get("rot", 0), t)
    if rot:
        pts = rot_pts(pts, x, y, rot)
    if el.get("relleno"):
        fill_poly(ctx, pts, el["relleno"], a)
    if el.get("trama"):
        halftone_fill(ctx, pts, el["trama"], a)
    if el.get("grosor", 6):
        stroke(ctx, pts, el.get("grosor", 6), el.get("color", "tinta"), a, closed=True)


def el_cita(ctx, el, t):
    """Globo de diálogo con texto."""
    pin, pout = appear(el, t)
    if pin <= 0 or pout <= 0:
        return
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    s = EASE["back"](pin)
    w2, h2 = w * s / 2, h * s / 2
    tx, ty = el.get("cola", [x - w * .25, y + h * .9])
    body = rrect_pts(x - w2, y - h2, x + w2, y + h2, 40)
    tail = [(x - w * .32 * s, y + h2 - 2), (tx, ty), (x - w * .12 * s, y + h2 - 2)]
    fill_poly(ctx, body, el.get("relleno", "papel_claro"), pout)
    fill_poly(ctx, tail + [tail[0]], el.get("relleno", "papel_claro"), pout)
    stroke(ctx, body, 6, "tinta", pout, closed=True)
    stroke(ctx, tail, 6, "tinta", pout)
    if pin > .35:
        el_texto(ctx, {"t": [el["t"][0] + .1, el["t"][1]], "x": x, "y": y, "txt": el["txt"],
                       "size": el.get("size", 64), "fuente": el.get("fuente", "titulo2"),
                       "ancho": w - 80, "entrada": "pop", "stagger": .05, "fo": el.get("fo", .18)}, t)


def el_fuente(ctx, el, t):
    """Ficha de fuente: cinta adhesiva + tarjeta mono. Credibilidad visible."""
    pin, pout = appear(el, t)
    if pin <= 0 or pout <= 0:
        return
    x0, y = el["x"], el["y"]
    slide = (1 - EASE["out"](pin)) * -500
    x0 += slide
    lines = el["txt"].split("\n")
    size = el.get("size", 30)
    f = font("mono", size * SS)
    wmax = max(f.getlength(l) for l in lines) / SS + 70
    h = len(lines) * size * 1.35 + 74
    rot = el.get("rot", -2.5)
    box = rot_pts(rrect_pts(x0, y, x0 + wmax, y + h, 10), x0 + wmax / 2, y + h / 2, rot)
    fill_poly(ctx, box, "papel_claro", pout)
    stroke(ctx, box, 5, "tinta", pout, closed=True)
    tape = rot_pts(rrect_pts(x0 - 30, y - 22, x0 + 110, y + 22, 3), x0 + 40, y, rot - 14)
    fill_poly(ctx, tape, "cinta", .8 * pout)
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    cx, cy = x0 + wmax / 2, y + h / 2
    hdr = el.get("etiqueta", "FUENTE")
    rows = [(hdr, "acento", size * .8)] + [(l, "tinta", size) for l in lines]
    yy = y + 40
    for txt, col, sz in rows:
        lx = x0 + 35 + font("mono", sz * SS).getlength(txt) / SS / 2
        rx, ry = lx - cx, yy - cy
        paste_word(ctx, txt, "mono", sz, col, cx + rx * c - ry * s_, cy + rx * s_ + ry * c, alpha=pout, rot=rot)
        yy += sz * 1.35


def el_contador(ctx, el, t):
    pin, pout = appear(el, t)
    if pin <= 0 or pout <= 0:
        return
    a, b = el.get("cuenta", el["t"])
    u = EASE[el.get("ease", "out")](clamp((t - a) / max(.01, b - a)))
    v = el["desde"] + (el["hasta"] - el["desde"]) * u
    txt = f"{int(round(v)):,}".replace(",", " ")
    txt = el.get("prefijo", "") + txt + el.get("sufijo", "")
    el_texto(ctx, {"t": el["t"], "x": el["x"], "y": el["y"], "txt": txt, "size": el.get("size", 120),
                   "color": el.get("color", "acento"), "fuente": el.get("fuente", "titulo"), "entrada": "fade",
                   "fi": el.get("fi", .2), "fo": el.get("fo", .18), "ancho": 2000}, t)


# — ilustraciones compuestas —
def hand_polys(x, y, s, flip, curl=0.0):
    """Mano esquemática (dorso, dedos arriba). curl dobla el índice (0..1)."""
    m = -1 if flip else 1
    P = lambda px, py: (x + px * s * m, y + py * s)
    polys = [[P(*q) for q in rrect_pts(-120, -10, 120, 210, 60)]]
    fingers = [(-88, 150, 44), (-31, 178, 46), (27, 168, 45), (82, 128, 40)]
    for i, (fx, L, fw) in enumerate(fingers):
        pts = rrect_pts(fx - fw / 2, -L, fx + fw / 2, 30, fw / 2)
        if i == 0 and curl:
            pts = rot_pts(pts, fx, -20, -25 * curl)
        polys.append([P(*q) for q in pts])
    th = rot_pts(rrect_pts(-152, 50, -108, 185, 22), -130, 180, -22)
    polys.append([P(*q) for q in th])
    return polys, fingers


def el_mano(ctx, el, t):
    pin, pout = appear(el, t)
    if pin <= 0 or pout <= 0:
        return
    x, y, s = kv(el["x"], t), kv(el["y"], t), kv(el.get("s", 1), t)
    flip = el.get("espejo", False)
    prog = EASE["out"](clamp((t - el["t"][0]) / el.get("dibujo", .6)))
    polys, fingers = hand_polys(x, y, s, flip, kv(el.get("curl", 0), t))
    silhouette(ctx, polys, el.get("relleno", "papel_claro"), "tinta", el.get("grosor", 7), pout, prog)
    if prog >= 1:   # nudillos: arcos pequeños
        m = -1 if flip else 1
        for fx, L, fw in fingers:
            for ky in (-L * .52, -L * .05):
                cx, cy = x + fx * s * m, y + ky * s
                stroke(ctx, ellipse_pts(cx, cy, fw * .28 * s, 9 * s, 10, 200, 140), 4, "tinta", pout * .8)
    for i in el.get("marcar", []):
        fx, L, fw = fingers[i]
        m = -1 if flip else 1
        cx, cy = x + fx * s * m, y - L * .05 * s
        stroke(ctx, ellipse_pts(cx, cy, 36 * s, 36 * s, 40, -100, 380, .1), 6, "acento", pout,
               EASE["out"](clamp((t - el.get("t_marca", el["t"][0])) / .4)))


def el_articulacion(ctx, el, t):
    """Corte de una articulación de nudillo: huesos, cápsula, líquido sinovial, gas, cavidad."""
    pin, pout = appear(el, t)
    a = min(pin, pout)
    if a <= 0:
        return
    cx, cy = el["x"], el["y"]
    sep = kv(el.get("sep", 18), t)
    bub = kv(el.get("burbuja", 0), t)
    gas = kv(el.get("gas", 1), t)
    # cápsula + líquido (trama)
    cap = ellipse_pts(cx, cy, 250, 175 + sep * .6, 72)
    fill_poly(ctx, cap, "liquido_claro", a)
    halftone_fill(ctx, cap, "liquido", a, 18, 3.4)
    # gas disuelto: puntos que se mueven
    if gas > 0:
        for i in range(26):
            ang = rng_noise(i, 1) * math.pi
            rr = 60 + abs(rng_noise(i, 2)) * 150
            px = cx + math.cos(ang + t * .4 * rng_noise(i, 3)) * rr
            py = cy + math.sin(ang + t * .3) * (40 + sep * .3) * abs(rng_noise(i, 4))
            # cuando hay cavidad, el gas viaja hacia el centro
            px += (cx - px) * clamp(bub / 70) * .85
            py += (cy - py) * clamp(bub / 70) * .85
            r = 7
            P = ctx.P(px, py)
            R = ctx.S(r)
            ctx.d.ellipse([P[0] - R, P[1] - R, P[0] + R, P[1] + R], fill=hexrgb("tinta") + (int(220 * a * gas),))
    # huesos
    top = rrect_pts(cx - 105, cy - 480, cx + 105, cy - sep / 2, 100)
    bot = rrect_pts(cx - 115, cy + sep / 2, cx + 115, cy + 480, 46)
    for poly in (top, bot):
        fill_poly(ctx, poly, "hueso", a)
        stroke(ctx, poly, 7, "tinta", a, closed=True)
    # sombreado de hueso: rayado a mano
    for k in range(6):
        yy = cy - 150 - k * 40 - sep / 2
        stroke(ctx, [(cx + 50, yy), (cx + 88, yy - 22)], 4, "tinta", a * .55)
        stroke(ctx, [(cx + 55, cy + 70 + k * 40 + sep / 2), (cx + 93, cy + 48 + k * 40 + sep / 2)], 4, "tinta", a * .55)
    stroke(ctx, cap, 6, "tinta", a, closed=True)
    # cavidad de gas
    if bub > 1:
        bp = ellipse_pts(cx, cy, bub * 1.25, min(bub, sep * .48 + 4), 48)
        fill_poly(ctx, bp, "papel_claro", a)
        stroke(ctx, bp, 6, "acento", a, closed=True)
        flash = clamp(1 - (t - el.get("t_pop", -9)) / .35)
        if flash > 0:
            for i in range(10):
                ang = i / 10 * math.tau
                r0, r1 = bub * 1.5 + 10, bub * 1.5 + 10 + 90 * flash
                stroke(ctx, [(cx + math.cos(ang) * r0 * 1.2, cy + math.sin(ang) * r0 * .6),
                             (cx + math.cos(ang) * r1 * 1.2, cy + math.sin(ang) * r1 * .6)], 6, "acento", flash)


PRIM = {"texto": el_texto, "trazo": el_trazo, "marca": el_marca, "caja": el_caja, "cita": el_cita,
        "fuente": el_fuente, "contador": el_contador, "mano": el_mano, "articulacion": el_articulacion}


# ───────────────────────── papel y fondo ─────────────────────────
_PAPER = None
_GRAIN = None


def paper_base():
    global _PAPER, _GRAIN
    if _PAPER is None:
        r = np.random.default_rng(7)
        base = np.array(hexrgb("papel"), np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
        low = Image.fromarray((r.random((H // 24, W // 24)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        low = (np.asarray(low, np.float32) / 255 - .5) * 10
        fib = Image.fromarray((r.random((H // 3, W)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        fib = (np.asarray(fib, np.float32) / 255 - .5) * 6
        _PAPER = np.clip(base + (low + fib)[..., None], 0, 255)
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - .10 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2
        _PAPER *= vig[..., None]
        # grano a media resolución: textura visible sin inflar el bitrate
        _GRAIN = [(1 - np.asarray(Image.fromarray((r.random((H // 2, W // 2)) * 255).astype(np.uint8))
                                  .resize((W, H), Image.BICUBIC), np.float32) / 255 * .05)[..., None] for _ in range(3)]
    return _PAPER


def draw_grid(img, cam, t):
    """Cuadrícula del cuaderno en coordenadas de mundo (se mueve con la cámara)."""
    z, cx, cy, _ = cam
    d = ImageDraw.Draw(img)
    step = EP["estilo"].get("cuadricula", 54) * z
    col = hexrgb("cuadricula") + (255,)
    ox = (W / 2 - cx * z) % step
    oy = (H / 2 - cy * z) % step
    x = ox
    while x < W:
        d.line([(x, 0), (x, H)], fill=col, width=1)
        x += step
    y = oy
    while y < H:
        d.line([(0, y), (W, y)], fill=col, width=1)
        y += step
    mx = W / 2 + (EP["estilo"].get("margen_x", 110) - cx) * z     # línea de margen roja
    d.line([(mx, 0), (mx, H)], fill=hexrgb("margen") + (255,), width=max(1, int(2 * z)))


# ───────────────────────── subtítulos ─────────────────────────
def subtitle_chunks():
    """Divide la narración en bloques de ≤N palabras con tiempos por palabra (proporcional a letras)."""
    out = []
    maxw = EP["estilo"].get("sub_palabras", 5)
    for ln in EP["narracion"]:
        a, b = ln["t"]
        words = ln["txt"].split()
        weights = [len(w.strip(".,¿?¡!…:;«»\"")) + 2 for w in words]
        tot, acc, times = sum(weights), 0, []
        for wgt in weights:
            times.append((a + (b - a) * acc / tot, a + (b - a) * (acc + wgt) / tot))
            acc += wgt
        for i in range(0, len(words), maxw):
            ws = list(zip(words[i:i + maxw], times[i:i + maxw]))
            out.append({"t": [ws[0][1][0], ws[-1][1][1]], "words": ws, "line": ln})
    for c, n in zip(out, out[1:] + [None]):      # nunca dos bloques a la vez
        c["hasta"] = min(c["t"][1] + .35, n["t"][0] - .03) if n else c["t"][1] + .35
    return out


SUBS = None


def draw_subs(ctx, t):
    st = EP["estilo"]
    y = st.get("sub_y", 1330) * SS
    size = st.get("sub_size", 58)
    for ch in SUBS:
        a, b = ch["t"]
        if not (a - .03 <= t < ch["hasta"]):
            continue
        txt = " ".join(w for w, _ in ch["words"])
        words, total_h, lineh = layout(txt.replace("*", ""), "cuerpo_b", size, 860, 1.05)
        # placa de papel detrás: legible aunque haya dibujo debajo
        xs = [rx - ww / 2 for _, _, rx, _, ww in words] + [rx + ww / 2 for _, _, rx, _, ww in words]
        pad = 34 * SS
        plate = rrect_pts(W * SS / 2 + min(xs) - pad, y - total_h / 2 - pad * .55,
                          W * SS / 2 + max(xs) + pad, y + total_h / 2 + pad * .55, 22 * SS)
        plate = jitter_path(resample(plate, 30), ctx.seed + 5, 1.5 * SS, True)
        ctx.d.polygon(plate, fill=hexrgb("papel_claro") + (235,))
        ctx.d.line(plate, fill=hexrgb("tinta") + (255,), width=4 * SS, joint="curve")
        for (w, _, rx, ry, ww), (_, (wa, wb)) in zip(words, ch["words"]):
            if t < wa - .02:
                continue
            p = clamp((t - wa) / .12)
            X, Y = W * SS / 2 + rx, y + ry
            cur = wa <= t < wb
            if cur:   # marcador de resaltador detrás de la palabra actual
                pad = 14 * SS
                hl = rrect_pts(X - ww / 2 - pad, Y - lineh * .38, X + ww / 2 + pad, Y + lineh * .42, 12)
                hl = jitter_path(resample(hl, 20), ctx.seed + 11, 2.5 * SS, True)
                ctx.d.polygon(hl, fill=hexrgb("resaltador") + (int(255 * p),))
            paste_word(ctx, w, "cuerpo_b", size, "tinta", X, Y, scale=.85 + .15 * EASE["back"](p),
                       alpha=p, screen=True)


# ───────────────────────── transiciones ─────────────────────────
def transition_overlay(ctx, t):
    for sc in EP["escenas"]:
        tr = sc.get("transicion", "corte")
        t0 = sc["t"][0]
        if tr == "barrido" and t0 - .28 <= t <= t0 + .28:
            p = EASE["io"]((t - (t0 - .28)) / .56)
            D = (W + .5 * H) * SS          # recorrido para cruzar la pantalla en diagonal
            B = D * 1.05                   # ancho de banda: en p = 0.5 cubre todo el cuadro
            lead = p * (D + B)
            trail = lead - B
            sk = H * SS * .5
            poly = [(lead, 0), (lead - sk, H * SS), (trail - sk, H * SS), (trail, 0)]
            ctx.d.polygon(poly, fill=hexrgb("tinta") + (255,))
            edge = [(lead, 0), (lead - H * SS * .5, H * SS)]
            ctx.d.line(edge, fill=hexrgb("acento") + (255,), width=26 * SS)


def scene_at(t):
    cur = EP["escenas"][0]
    for sc in EP["escenas"]:
        if sc["t"][0] <= t:
            cur = sc
    return cur


def camera(sc, t):
    c = sc.get("camara", {})
    return (kv(c.get("z", 1), t), kv(c.get("cx", W / 2), t), kv(c.get("cy", H / 2), t), kv(c.get("rot", 0), t))


def render_scene(sc, t, frame):
    cam = camera(sc, t)
    paper = Image.fromarray(paper_base().astype(np.uint8)).convert("RGBA")
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_grid(grid, cam, t)
    paper.alpha_composite(grid)
    ink = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ctx = Ctx(ink, t, frame, cam)
    for el in sc["elementos"]:
        if el["t"][0] - .01 <= t <= el["t"][1] + .01:
            PRIM[el["tipo"]](ctx, el, t)
    return paper, ink, ctx


def render_frame(frame):
    t = frame / FPS
    sc = scene_at(t)
    paper, ink, ctx = render_scene(sc, t, frame)
    # overlays de pantalla (no siguen la cámara)
    hud = Ctx(ink, t, frame, (1, W / 2, H / 2, 0))
    tag = EP.get("serie", {})
    if tag:
        paste_word(hud, tag.get("sello", ""), "mono", 26, "tinta", 90 * SS + font("mono", 26 * SS).getlength(tag.get("sello", "")) / 2,
                   232 * SS, alpha=.85, screen=True)
    draw_subs(hud, t)
    transition_overlay(hud, t)
    inkd = ink.reduce(SS)
    paper.alpha_composite(inkd)
    arr = np.asarray(paper.convert("RGB"), np.float32)
    grain = _GRAIN[(frame // 4) % 3]
    return (arr * grain).astype(np.uint8).tobytes()


def init_worker(path):
    global EP, PAL, SUBS
    EP = json.load(open(path, encoding="utf-8"))
    PAL.update(EP["estilo"]["paleta"])
    SUBS = subtitle_chunks()
    paper_base()


# ───────────────────────── audio (SFX procedurales) ─────────────────────────
SR = 48000


def sfx(kind, seed=0):
    r = np.random.default_rng(seed)
    if kind == "pop":
        n = int(.09 * SR); tt = np.arange(n) / SR
        f = 900 * np.exp(-tt * 28) + 260
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45) * .5
    if kind == "tick":
        n = int(.03 * SR); tt = np.arange(n) / SR
        return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 260) * .18
    if kind == "lapiz":
        n = int(.45 * SR); tt = np.arange(n) / SR
        x = r.standard_normal(n)
        x = np.convolve(x, np.ones(6) / 6, "same") - np.convolve(x, np.ones(40) / 40, "same")
        env = np.minimum(1, tt * 20) * np.exp(-tt * 4) * (0.6 + .4 * np.sin(2 * np.pi * 9 * tt))
        return x * env * .35
    if kind == "barrido":
        n = int(.55 * SR); tt = np.arange(n) / SR
        x = r.standard_normal(n)
        k = int(30)
        x = np.convolve(x, np.ones(k) / k, "same")
        env = np.sin(np.pi * tt / tt[-1]) ** 2
        return x * env * 1.4
    if kind == "crack":
        n = int(.12 * SR); tt = np.arange(n) / SR
        x = r.standard_normal(n) * np.exp(-tt * 90)
        body = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 40) * .6
        return (x * .9 + body) * .8
    if kind == "golpe":
        n = int(.35 * SR); tt = np.arange(n) / SR
        return np.sin(2 * np.pi * (70 * np.exp(-tt * 6) + 40) * tt) * np.exp(-tt * 9) * .9
    raise ValueError(kind)


def build_audio(dur, voz=None):
    mix = np.zeros(int(dur * SR) + SR, np.float64)
    events = list(EP.get("sfx", []))
    for sc in EP["escenas"]:
        if sc.get("transicion") == "barrido":
            events.append({"t": sc["t"][0] - .3, "tipo": "barrido", "vol": .5})
        for el in sc["elementos"]:
            if "sfx" in el:
                events.append({"t": el["t"][0], "tipo": el["sfx"], "vol": el.get("sfx_vol", .7)})
            if el["tipo"] == "contador":
                a, b = el.get("cuenta", el["t"])
                n = int((b - a) * 14)
                for k in range(n):   # ticks que se frenan con el easing
                    u = 1 - (1 - k / n) ** (1 / 3)
                    events.append({"t": a + (b - a) * u, "tipo": "tick", "vol": .5})
    for i, ev in enumerate(events):
        s = sfx(ev["tipo"], i) * ev.get("vol", .7)
        k = int(ev["t"] * SR)
        if 0 <= k < len(mix):
            mix[k:k + len(s)] += s[:len(mix) - k]
    if voz:
        vw = read_wav(voz)
        env = np.convolve(np.abs(vw), np.ones(2400) / 2400, "same")
        duck = 1 - .55 * np.clip(env / (env.max() * .25 + 1e-9), 0, 1)
        n = min(len(mix), len(vw))
        mix[:n] = mix[:n] * duck[:n] + vw[:n]
    peak = np.abs(mix).max() + 1e-9
    mix = mix / peak * .89
    return mix[:int(dur * SR)]


def read_wav(path):
    tmp = path + ".48k.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR), tmp], check=True)
    with wave.open(tmp) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# ───────────────────────── SRT y guion de locución ─────────────────────────
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    with open(path, "w", encoding="utf-8") as f:
        for i, ch in enumerate(SUBS, 1):
            f.write(f"{i}\n{srt_time(ch['t'][0])} --> {srt_time(ch['t'][1])}\n{' '.join(w for w, _ in ch['words'])}\n\n")


def write_locucion(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{EP['titulo']}\nGrabar a ritmo natural; cada línea debe caber en su ventana.\n\n")
        for ln in EP["narracion"]:
            a, b = ln["t"]
            n = len(ln["txt"].split())
            f.write(f"[{a:5.2f}–{b:5.2f}s | {n / (b - a):.1f} pal/s] {ln['txt']}\n")
            if ln.get("nota"):
                f.write(f"    ↳ {ln['nota']}\n")


# ───────────────────────── main ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodio")
    ap.add_argument("salida")
    ap.add_argument("--desde", type=float, default=0)
    ap.add_argument("--hasta", type=float, default=None)
    ap.add_argument("--voz")
    ap.add_argument("--fotograma", nargs=2, metavar=("SEG", "PNG"))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--crf", type=int, default=int(os.environ.get("CRF", 18)))
    a = ap.parse_args()
    init_worker(a.episodio)
    if a.fotograma:
        f = int(float(a.fotograma[0]) * FPS)
        Image.frombytes("RGB", (W, H), render_frame(f)).save(a.fotograma[1])
        print("OK", a.fotograma[1]); return
    dur = EP["duracion"]
    f0, f1 = int(a.desde * FPS), int((a.hasta if a.hasta is not None else dur) * FPS)
    base = os.path.splitext(a.salida)[0]
    wav = base + "_audio.wav"
    full = build_audio(dur, a.voz)
    write_wav(wav, full[int(a.desde * SR):int(f1 / FPS * SR)])
    write_srt(base + ".srt")
    write_locucion(base + "_locucion.txt")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", a.salida],
                          stdin=subprocess.PIPE)
    with Pool(a.workers, initializer=init_worker, initargs=(a.episodio,)) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(f0, f1), chunksize=4)):
            ff.stdin.write(buf)
            if i % 60 == 0:
                print(f"\r{(f0 + i) / FPS:6.1f}s / {f1 / FPS:.1f}s", end="", flush=True)
    ff.stdin.close(); ff.wait()
    os.remove(wav)
    print("\nOK", a.salida)


if __name__ == "__main__":
    main()
