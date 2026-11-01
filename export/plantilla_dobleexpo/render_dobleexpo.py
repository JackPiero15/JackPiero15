#!/usr/bin/env python3
"""Plantilla "doble exposición B/N + letra palabra por palabra".

Replica la referencia TikVid.io_7548994381039078712.mp4 (768x576, 30 fps, 22.47 s). Valores medidos
en ANALISIS.md. Estructura:
  - Capa base (clips "historia") + capa de destellos (planos de ~0.1 s en ciclo de 32.5 cuadros)
    mezcladas al 50 % (doble exposición permanente); capa "fantasma" opcional a baja opacidad.
  - Movimiento a cadencia reducida (~14 imágenes/s: cada imagen dura 2-3 cuadros a 30 fps).
  - Blanco y negro puro, curva tonal ajustada a la de la referencia, suavizado, viñeta, grano leve.
  - Imagen en bucle (la referencia repite un bloque de 8.067 s casi 3 veces).
  - Letra palabra por palabra, sans condensada (Arial Narrow ~ Liberation Sans al 82 % de ancho),
    gris claro 225, sin brillo ni sombra, bloque centrado, líneas justificadas. Si el bloque se
    recompone: distorsión de 3 cuadros; si solo se añade una palabra en su sitio: fundido de 3 cuadros.
  - Fundido a negro al final; audio con fundido de entrada y salida.

Uso:
  python3 render_dobleexpo.py config.json --preview 2.5,9.2,13.4      # cuadros PNG en preview/
  python3 render_dobleexpo.py config.json --out final.mp4
  python3 render_dobleexpo.py config.json --solo-texto --preview 3.0   # texto sobre negro (control)
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REF_W, REF_H = 768, 576            # coordenadas de la referencia; todo se escala por alto/576

# ------------------------------------------------------------------ valores medidos (ANALISIS.md)
REF = {
    "fps": 30,
    "fps_efectivo": 14.0,          # retenciones de 2-3 cuadros (media 2.17) -> ~13.8 img/s
    "ciclo_destellos": 32.5,       # cuadros; período medido de los destellos (=2 tiempos a ~111 BPM)
    # inicio (en cuadros, ciclo de 32.5) de cada plano de destello dentro del ciclo
    "slots": [0, 2, 4, 6, 9, 11, 13, 14, 17, 21, 24, 28, 31],
    "mezcla_destellos": 0.5,       # estimación: no hay evidencia verificable del modo/valor exacto
    "bucle": 242 / 30,             # 8.067 s
    "texto_color": 225,
    "texto_condensado": 0.82,      # ancho de Arial Narrow respecto de Arial
    "em_1": {"ancho_obj": 262, "max": 200},   # 1 línea: ajustar a ancho, tope
    "caja_apilada": [250, 255],    # palabras de una misma línea apiladas: caja ancho x alto (px ref)
    "umbral_apilar": 1.25,         # se apila solo si el tamaño apilado supera en 25 % al de 1 línea
    "em_lineas": {2: 92, 3: 70, 4: 58},
    "ancho_max": 340,              # ancho máximo del bloque (px ref; máx. medido 337)
    "interlineado": 1.13,          # em
    "centro": (384, 282),          # centro de la caja de tinta del bloque (px ref)
    "transicion": 2,               # cuadros de distorsión al recomponer (moda medida = 2)
    "fundido_palabra": [0.35, 0.75, 1.0],
    "desenfoque": 0.8,             # px ref (gaussiano)
    "grano": 4.0,                  # sigma, niveles 0-255
    "vineta": 0.30,                # oscurecimiento en esquinas
    "fundido_negro": [2.02, 0.52], # empieza 2.02 s antes del final, negro total 0.52 s antes
    "audio_fade_in": 1.1,
    "audio_fade_out": [1.47, 0.27],
}

FONT_PATHS = [
    os.path.join(HERE, "fonts", "LiberationSans-Regular.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]


def find_font():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    sys.exit("No se encontró LiberationSans-Regular.ttf (ver fonts/).")


# ------------------------------------------------------------------ medios
def cover_gray(im, W, H, focus=(0.5, 0.5), zoom=1.0):
    im = im.convert("L")
    s = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W, round(im.width * s)), max(H, round(im.height * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = int(round((nw - W) * focus[0])); y = int(round((nh - H) * focus[1]))
    return np.asarray(im.crop((x, y, x + W, y + H)), dtype=np.uint8)


def is_image(p):
    return os.path.splitext(p)[1].lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")


class Source:
    """Clip o imagen convertida a gris, a tamaño de lienzo, muestreada a fps_efectivo."""

    def __init__(self, path, W, H, fpe, inicio=0.0, dur=None, focus=(0.5, 0.5), zoom=(1.0, 1.06)):
        self.path, self.W, self.H, self.fpe = path, W, H, fpe
        self.focus, self.zoom = focus, zoom
        if is_image(path):
            self.still = Image.open(path)
            self.frames = None
        else:
            self.still = None
            cmd = ["ffmpeg", "-v", "error", "-ss", str(inicio)]
            if dur: cmd += ["-t", str(dur)]
            fx, fy = focus
            vf = (f"fps={fpe},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                  f"crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})*{fy},format=gray")
            cmd += ["-i", path, "-vf", vf, "-f", "rawvideo", "-"]
            raw = subprocess.run(cmd, capture_output=True, check=True).stdout
            n = len(raw) // (W * H)
            if n == 0: sys.exit(f"Sin cuadros: {path}")
            self.frames = np.frombuffer(raw[: n * W * H], np.uint8).reshape(n, H, W)
        self._cache = {}

    def get(self, t, span=None):
        """t: segundos dentro del clip (ya cuantizado). span: duración del tramo (para zoom lento)."""
        if self.frames is not None:
            i = int(math.floor(t * self.fpe + 1e-6)) % len(self.frames)
            return self.frames[i]
        # imagen fija: acercamiento lento cuantizado (se percibe el ritmo entrecortado)
        span = span or 4.0
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * min(max(t / span, 0), 1)
        key = round(z, 4)
        if key not in self._cache:
            if len(self._cache) > 64: self._cache.clear()
            self._cache[key] = cover_gray(self.still, self.W, self.H, self.focus, z)
        return self._cache[key]


# ------------------------------------------------------------------ texto
class TextEngine:
    def __init__(self, H, cfg_txt):
        self.s = H / REF_H
        self.font_path = find_font()
        self.cond = cfg_txt.get("condensado", REF["texto_condensado"])
        self.color = cfg_txt.get("color", REF["texto_color"])
        self._fonts = {}

    def font(self, px):
        px = max(4, int(round(px)))
        if px not in self._fonts:
            self._fonts[px] = ImageFont.truetype(self.font_path, px)
        return self._fonts[px]

    def wwidth(self, word, em):
        """ancho natural (px de salida) de una palabra condensada"""
        return self.font(em * self.s).getlength(word) * self.cond

    def line_width(self, words, em):
        sp = self.font(em * self.s).getlength(" ") * self.cond
        return sum(self.wwidth(w, em) for w in words) + sp * max(0, len(words) - 1)

    def em_for(self, lines, override=None, apilada=False):
        """tamaño (em en px ref) según número de líneas y ancho máximo"""
        n = len(lines)
        unit = [self.line_width(l, 100.0) / 100.0 / self.s for l in lines]   # ancho por em, px ref
        widest = max(unit)
        if apilada:
            bw, bh = REF["caja_apilada"]
            return min(bw / widest, bh / ((n - 1) * REF["interlineado"] + 1.0))
        if n == 1:
            em = min(REF["em_1"]["max"], REF["em_1"]["ancho_obj"] / widest)
        else:
            em = REF["em_lineas"].get(n, 58 * 4 / n)
        em = min(em, REF["ancho_max"] / widest)
        if override: em *= override
        return em

    def layout(self, lines, em, justify):
        """devuelve [(palabra, x, baseline)] en px de salida, sin centrar"""
        s = self.s
        sp = self.font(em * s).getlength(" ") * self.cond
        widths = [self.line_width(l, em) for l in lines]
        W = max(widths)
        out = []
        for i, l in enumerate(lines):
            y = i * REF["interlineado"] * em * s
            ws = [self.wwidth(w, em) for w in l]
            if justify and len(l) > 1:
                gap = (W - sum(ws)) / (len(l) - 1)
            else:
                gap = sp
            x = 0.0
            for w, ww in zip(l, ws):
                out.append((w, x, y)); x += ww + gap
        return out

    def render(self, placed, em, visible, W, H, center=None):
        """máscara float32 HxW. placed: layout completo (para centrar); visible: índices dibujados.
        Devuelve (máscara, bbox)"""
        s = self.s
        f = self.font(em * s)
        # dibujar sin condensar en lienzo ancho, luego condensar en horizontal
        asc, desc = f.getmetrics()
        maxx = max(x / self.cond + f.getlength(w) for w, x, y in placed) + 4
        maxy = max(y for _, _, y in placed) + asc + desc + 4
        tmp = Image.new("L", (int(math.ceil(maxx)) + 2, int(math.ceil(maxy)) + 2), 0)
        full = Image.new("L", tmp.size, 0)
        dt, df = ImageDraw.Draw(tmp), ImageDraw.Draw(full)
        for k, (w, x, y) in enumerate(placed):
            df.text((x / self.cond + 1, y + 1), w, font=f, fill=255)
            if k in visible:
                dt.text((x / self.cond + 1, y + 1), w, font=f, fill=255)
        nw = max(1, int(round(tmp.width * self.cond)))
        tmp = tmp.resize((nw, tmp.height), Image.LANCZOS)
        full = full.resize((nw, full.height), Image.LANCZOS)
        bb = full.getbbox() or (0, 0, 1, 1)
        cx, cy = center or REF["centro"]
        ox = int(round(cx * s - (bb[0] + bb[2]) / 2)); oy = int(round(cy * s - (bb[1] + bb[3]) / 2))
        m = np.zeros((H, W), np.float32)
        a = np.asarray(tmp, np.float32) / 255.0
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(W, ox + a.shape[1]), min(H, oy + a.shape[0])
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        return m


def build_states(letra, eng):
    """Convierte la letra en estados [(t, mascara_fn_key, layout_key)].
    Cada frase: {"lineas": "she knows\\nwhat i\\nthink about", "tiempos": [...], "escala_1": opc.}
    Un token "was|wasted" se muestra como "was" y luego cambia a "wasted" (consume 2 tiempos)."""
    states = []
    for fi, fr in enumerate(letra):
        lines_tok = [l.split() for l in fr["lineas"].split("\n") if l.strip()]
        # lista plana de (linea, idx_en_linea, variantes)
        toks = [(li, wi, tok.split("|")) for li, l in enumerate(lines_tok) for wi, tok in enumerate(l)]
        times = list(fr["tiempos"])
        need = sum(len(v) for _, _, v in toks)
        if len(times) != need:
            sys.exit(f"Frase {fi+1}: {need} tiempos necesarios, hay {len(times)} ({fr['lineas']!r})")
        ti = 0
        shown = {}   # (li,wi) -> texto actual
        for li, wi, vars_ in toks:
            for v in vars_:
                shown[(li, wi)] = v
                t = times[ti]; ti += 1
                states.append((t, fi, dict(shown), lines_tok, fr.get("escala_1")))
    return states


def state_layout(st, eng):
    """Decide composición de un estado. Devuelve dict con em, placed, visible, firma."""
    _, fi, shown, lines_tok, esc1 = st
    final_full = [[t.split("|")[-1] for t in l] for l in lines_tok]
    used_lines = sorted({li for (li, wi) in shown})
    n_lines = len(used_lines)

    def cur(li, wi):
        return shown.get((li, wi))

    if n_lines == 1:
        li = used_lines[0]
        words = [cur(li, wi) for wi in range(len(lines_tok[li])) if cur(li, wi) is not None]
        one = [words]
        em1 = eng.em_for(one, esc1 if len(words) == 1 else None)
        if len(words) > 1:
            stack = [[w] for w in words]
            em2 = eng.em_for(stack, apilada=True)
            if em2 > REF["umbral_apilar"] * em1:
                one, em1 = stack, em2
        placed = eng.layout(one, em1, justify=False)
        visible = set(range(len(placed)))
        lines_desc = one
        em = em1
    else:
        # líneas usadas con su contenido final reservado; palabras visibles = las ya cantadas
        lines = []
        vis_flags = []
        for li in used_lines:
            row = []
            for wi in range(len(lines_tok[li])):
                c = cur(li, wi)
                row.append(c if c is not None else final_full[li][wi])
                vis_flags.append(c is not None)
            lines.append(row)
        em = eng.em_for(lines)
        placed = eng.layout(lines, em, justify=True)
        visible = {k for k, f in enumerate(vis_flags) if f}
        lines_desc = lines
    sig = (fi, tuple(tuple(l) for l in lines_desc), round(em, 3))
    return {"em": em, "placed": placed, "visible": visible, "sig": sig}


def glitch(mask, strength, rng, em_px):
    """Distorsión de transición medida en la referencia: ondulación horizontal suave por filas,
    arrastre horizontal y doble imagen tenue. strength 1 = leve, 2 = fuerte."""
    ys, xs = np.nonzero(mask > 0.02)
    if len(ys) == 0: return mask
    pad = int(em_px * 0.6)
    H, W = mask.shape
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad)
    sub = mask[y0:y1, x0:x1]
    h, w = sub.shape
    p1, p2 = rng.uniform(0, 2 * math.pi, 2)
    yy = np.arange(h, dtype=np.float32)
    dx = strength * (0.045 * em_px * np.sin(2 * math.pi * yy / (0.95 * em_px) + p1)
                     + 0.008 * em_px * np.sin(2 * math.pi * yy / (0.30 * em_px) + p2))
    xx = np.arange(w, dtype=np.float32)[None, :] - dx[:, None]
    x0i = np.clip(np.floor(xx).astype(int), 0, w - 1); x1i = np.clip(x0i + 1, 0, w - 1)
    fx = np.clip(xx - np.floor(xx), 0, 1)
    rows = np.arange(h)[:, None]
    out = sub[rows, x0i] * (1 - fx) + sub[rows, x1i] * fx
    k = max(1, int(strength * 0.11 * em_px))
    if k > 1:   # arrastre horizontal (media móvil)
        c = np.cumsum(np.pad(out, ((0, 0), (k, 0))), axis=1)
        out = np.clip((c[:, k:] - c[:, :-k]) / k * (1.0 + 0.15 * strength), 0, 1)
    off = int(strength * 0.09 * em_px)
    ghost = np.roll(np.roll(out, off, axis=1), int(0.02 * em_px), axis=0)
    out = np.maximum(out, 0.5 * ghost) * 0.85
    res = mask.copy(); res[y0:y1, x0:x1] = out
    return res


class TextTrack:
    def __init__(self, cfg, W, H, fps):
        self.eng = TextEngine(H, cfg.get("texto", {}))
        self.W, self.H, self.fps = W, H, fps
        self.states = build_states(cfg.get("letra", []), self.eng)
        self.layouts = [state_layout(s, self.eng) for s in self.states]
        self.fin = cfg.get("texto_fin")
        self._mcache = {}
        self.T = REF["transicion"]
        self.frames = [int(round(s[0] * fps)) for s in self.states]

    def mask(self, k):
        if k not in self._mcache:
            L = self.layouts[k]
            self._mcache[k] = self.eng.render(L["placed"], L["em"], L["visible"], self.W, self.H)
            if len(self._mcache) > 6:
                self._mcache.pop(next(iter(self._mcache)))
        return self._mcache[k]

    def em_px(self, k):
        return self.layouts[k]["em"] * self.eng.s

    def at(self, n):
        """máscara alfa (float32) del cuadro n o None"""
        if not self.states: return None
        frames = self.frames
        fin = int(round(self.fin * self.fps)) if self.fin is not None else None
        rng = np.random.default_rng(1000 + n)
        if fin is not None and n >= fin:
            d = n - fin
            if d >= 2: return None
            k = len(self.states) - 1
            return glitch(self.mask(k), 1 + d, rng, self.em_px(k)) * (1.0 - 0.45 * d)
        k = max((i for i, f in enumerate(frames) if f <= n), default=None)
        if k is None: return None
        d = n - frames[k]
        prev = k - 1 if k > 0 else None
        if prev is None:   # primera aparición: 2 cuadros distorsionados
            if d == 0: return glitch(self.mask(k), 2, rng, self.em_px(k)) * 0.6
            if d == 1: return glitch(self.mask(k), 1, rng, self.em_px(k))
            return self.mask(k)
        same = (self.layouts[prev]["sig"][0] == self.layouts[k]["sig"][0] and
                self.layouts[prev]["placed"] == self.layouts[k]["placed"])
        if same:   # misma composición: solo aparece la palabra nueva (fundido de 3 cuadros)
            fp = REF["fundido_palabra"]
            if d >= len(fp): return self.mask(k)
            return np.maximum(self.mask(prev), self.mask(k) * fp[d])
        if d >= self.T:
            return self.mask(k)
        if d == 0:   # sale la composición anterior distorsionada, entra la nueva tenue
            return np.maximum(glitch(self.mask(prev), 2, rng, self.em_px(prev)) * 0.8,
                              glitch(self.mask(k), 2, rng, self.em_px(k)) * 0.4)
        return glitch(self.mask(k), 1, rng, self.em_px(k))


# ------------------------------------------------------------------ imagen
class Visual:
    def __init__(self, cfg, W, H, fps, base_dir):
        self.W, self.H, self.fps = W, H, fps
        self.s = H / REF_H
        look = cfg.get("look", {})
        self.fpe = look.get("fps_efectivo", REF["fps_efectivo"])
        self.mix = look.get("mezcla_destellos", REF["mezcla_destellos"])
        self.loop = cfg.get("bucle", REF["bucle"])
        bpm = cfg.get("bpm")
        self.cycle = (2 * 60.0 / bpm * fps) if bpm else REF["ciclo_destellos"] * fps / 30.0
        rp = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)
        span_max = self.loop or cfg["duracion"]
        self.base = []
        segs = sorted(cfg["base"], key=lambda b: b["desde"])
        for i, b in enumerate(segs):
            end = segs[i + 1]["desde"] if i + 1 < len(segs) else span_max
            src = Source(rp(b["archivo"]), W, H, self.fpe, b.get("inicio_clip", 0.0), end - b["desde"] + 0.5,
                         tuple(b.get("enfoque", (0.5, 0.5))))
            self.base.append((b["desde"], end, src))
        self.flash = [Source(rp(d["archivo"] if isinstance(d, dict) else d), W, H, self.fpe,
                             (d.get("inicio_clip", 0.0) if isinstance(d, dict) else 0.0),
                             (d.get("duracion", 4.0) if isinstance(d, dict) else 4.0),
                             tuple(d.get("enfoque", (0.5, 0.5))) if isinstance(d, dict) else (0.5, 0.5))
                      for d in cfg.get("destellos", [])]
        self.ghosts = [(g["desde"], g["hasta"], g.get("opacidad", 0.3),
                        Source(rp(g["archivo"]), W, H, self.fpe, g.get("inicio_clip", 0.0),
                               g["hasta"] - g["desde"] + 0.5, tuple(g.get("enfoque", (0.5, 0.5)))))
                       for g in cfg.get("fantasma", [])]
        slots = REF["slots"]
        self.slots = [o * self.cycle / 32.5 for o in slots]
        # tono / acabado
        self.lut = None
        self.tone_strength = look.get("tono_ref", 0.85)
        self.blur = look.get("desenfoque", REF["desenfoque"]) * self.s
        self.grain = look.get("grano", REF["grano"])
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((xx - W / 2) / (W / 2)) ** 2 * 0.5 + ((yy - H / 2) / (H / 2)) ** 2 * 0.5
        self.vig = (1.0 - look.get("vineta", REF["vineta"]) * r2).astype(np.float32)

    def raw(self, n):
        t = n / self.fps
        tv = (t % self.loop) if self.loop else t
        tq = math.floor(tv * self.fpe + 1e-6) / self.fpe          # cadencia reducida
        base = None
        for a, b, src in self.base:
            if a <= tq < b or (base is None and a > tq):
                base = src.get(tq - a, b - a).astype(np.float32); break
        if base is None:
            a, b, src = self.base[-1]; base = src.get(tq - a, b - a).astype(np.float32)
        img = base
        if self.flash:
            p = (tq * self.fps) % self.cycle     # en la misma rejilla de ~14 img/s
            si = max(i for i, o in enumerate(self.slots) if o <= p + 1e-6)
            fl = self.flash[si % len(self.flash)].get(tq, 4.0).astype(np.float32)
            img = (1 - self.mix) * img + self.mix * fl
        for a, b, op, src in self.ghosts:
            if a <= tq < b:
                img = (1 - op) * img + op * src.get(tq - a, b - a).astype(np.float32)
        return img

    def calibrate(self, n_frames, ref_cdf):
        """LUT global que lleva el histograma del montaje al de la referencia"""
        hist = np.zeros(256)
        for n in range(0, n_frames, max(1, n_frames // 120)):
            hist += np.bincount(np.clip(self.raw(n) * self.vig, 0, 255).astype(np.uint8).ravel(),
                                minlength=256)
        cdf = np.cumsum(hist); cdf /= cdf[-1]
        ref = np.asarray(ref_cdf)
        lut = np.searchsorted(ref, cdf).clip(0, 255).astype(np.float32)
        ident = np.arange(256, dtype=np.float32)
        self.lut = self.tone_strength * lut + (1 - self.tone_strength) * ident

    def finish(self, img, n):
        g = np.clip(img * self.vig, 0, 255).astype(np.uint8)
        if self.lut is not None:
            g = self.lut[g].astype(np.uint8)
        if self.blur > 0.3:
            g = np.asarray(Image.fromarray(g).filter(ImageFilter.GaussianBlur(self.blur)))
        out = g.astype(np.float32)
        if self.grain > 0:
            rng = np.random.default_rng(n)
            out += rng.normal(0, self.grain, out.shape).astype(np.float32)
        return out


# ------------------------------------------------------------------ principal
def load_cfg(path):
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def frame_at(n, cfg, vis, txt, W, H, fps, solo_texto=False):
    dur = cfg["duracion"]
    if solo_texto:
        img = np.zeros((H, W), np.float32)
    else:
        img = vis.finish(vis.raw(n), n)
    m = txt.at(n)
    if m is not None:
        img = img * (1 - m) + txt.eng.color * m
    t = n / fps
    f0, f1 = dur - REF["fundido_negro"][0], dur - REF["fundido_negro"][1]
    if t >= f0 and not solo_texto:
        img = img * max(0.0, 1 - (t - f0) / (f1 - f0))
    return np.clip(img, 0, 255).astype(np.uint8)


def audio_filter(cfg):
    a = cfg["audio"]; dur = cfg["duracion"]
    fo0 = dur - REF["audio_fade_out"][0]; fo1 = dur - REF["audio_fade_out"][1]
    chain = [f"atrim=start={a.get('inicio', 0.0)}:duration={dur}", "asetpts=PTS-STARTPTS",
             f"afade=t=in:st=0:d={a.get('fade_in', REF['audio_fade_in'])}",
             f"afade=t=out:st={fo0}:d={fo1 - fo0}", f"apad=whole_dur={dur}"]
    return ",".join(chain)


def loudnorm_args(cfg, base_filter):
    a = cfg["audio"]; target = a.get("lufs", -14)
    if target is None: return base_filter
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(cfg["_dir"], a["archivo"]),
                        "-af", base_filter + f",loudnorm=I={target}:TP=-1:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    txt = p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1]
    try:
        m = json.loads(txt)
        return (base_filter + f",loudnorm=I={target}:TP=-1:LRA=11:measured_I={m['input_i']}:"
                f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    except Exception:
        return base_filter + f",loudnorm=I={target}:TP=-1:LRA=11"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--preview", help="tiempos separados por coma (s)")
    ap.add_argument("--out")
    ap.add_argument("--solo-texto", action="store_true")
    ap.add_argument("--desde", type=float, default=0.0)
    ap.add_argument("--hasta", type=float)
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    sal = cfg.get("salida", {})
    W, H, fps = sal.get("ancho", 1440), sal.get("alto", 1080), sal.get("fps", REF["fps"])
    txt = TextTrack(cfg, W, H, fps)
    vis = None
    if not args.solo_texto:
        vis = Visual(cfg, W, H, fps, cfg["_dir"])
        with open(os.path.join(HERE, "ref_tono.json")) as fh:
            vis.calibrate(int(cfg["duracion"] * fps), json.load(fh)["cdf"])
    if args.preview:
        od = os.path.join(cfg["_dir"], "preview"); os.makedirs(od, exist_ok=True)
        for t in [float(x) for x in args.preview.split(",")]:
            n = int(round(t * fps))
            Image.fromarray(frame_at(n, cfg, vis, txt, W, H, fps, args.solo_texto)).save(
                os.path.join(od, f"f_{n:05d}.png"))
        print("preview ->", od)
    if args.out:
        n0 = int(round(args.desde * fps))
        n1 = int(round((args.hasta or cfg["duracion"]) * fps))
        lienzo = sal.get("lienzo", "4:3")
        vf = "format=yuv420p"
        if lienzo == "9:16":
            vw = sal.get("ancho_916", 1080)
            vh = int(round(vw * 16 / 9)); ch = int(round(vw * H / W / 2) * 2)
            vf = f"scale={vw}:{ch}:flags=lanczos,pad={vw}:{vh}:0:(oh-ih)/2:black,format=yuv420p"
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
               "-r", str(fps), "-i", "-"]
        if cfg.get("audio") and not args.solo_texto:
            af = loudnorm_args(cfg, audio_filter(cfg))
            if n0 or args.hasta:
                af += f",atrim=start={n0 / fps}:end={n1 / fps},asetpts=PTS-STARTPTS"
            cmd += ["-i", os.path.join(cfg["_dir"], cfg["audio"]["archivo"]), "-filter_complex",
                    f"[1:a]{af}[a]", "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "320k"]
        cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", str(sal.get("crf", 18)),
                "-tune", "film", "-movflags", "+faststart", "-shortest", args.out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for n in range(n0, n1):
            p.stdin.write(frame_at(n, cfg, vis, txt, W, H, fps, args.solo_texto).tobytes())
            if n % 60 == 0: print(f"  cuadro {n}/{n1}", flush=True)
        p.stdin.close(); p.wait()
        print("listo ->", args.out)


if __name__ == "__main__":
    main()
