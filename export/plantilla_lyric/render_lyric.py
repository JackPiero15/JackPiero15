#!/usr/bin/env python3
"""Plantilla "lyric aesthetic" replicada de TIKTOK_reference_1 / TikTok_Reference_2.

Estructura medida en las referencias (ver ANALISIS.md):
  - Un solo plano: fondo nocturno + personaje (manga B/N) + letra a la izquierda.
  - Fundido desde negro (~0.6 s) y zoom-out de apertura (preset "luna": 1.96x -> 1.0x en 3.1 s;
    preset "ciudad": 1.17x -> 1.0x en 3.0 s). El texto forma parte del plano que se aleja.
  - Flotación global continua (traslación diagonal senoidal, periodo 4.8 s).
  - Letra: comilla " fija + 1-3 palabras por línea en Montserrat ExtraBold blanca con brillo suave,
    crédito "Canción - Artista" en Open Sans debajo. Cambios con fundido ~0.25 s.
  - Estilo opcional "neon_red" (final de la referencia 2).
  - Audio: fundido de entrada ~1 s, de salida ~2 s; fundido a negro final ~0.5 s.

Uso:  python3 render_lyric.py config.json [--preview T1,T2,...] [--out salida.mp4]
"""
import json, math, os, subprocess, sys, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REF_W, REF_H = 576, 712  # sistema de coordenadas de las referencias

PRESETS = {
    # Medido en ref1: escala por correlación contra el encuadre final (t=3.8 s)
    "luna": {
        "zoom_keys": [[0.0, 1.96], [0.4, 1.88], [1.0, 1.64], [1.6, 1.40], [2.0, 1.24],
                      [2.4, 1.12], [2.8, 1.04], [3.1, 1.0]],
        "zoom_center": [300, 368],          # en coords de referencia 576x712
        "float_amp": [7.5, 6.5], "float_period": 4.8, "float_phase_t": 6.0,  # mínimo en t=6.0
        "fade_in": 0.6, "fade_out": 0.5,
        "text": {"x": 34, "quote_top": 167, "line1_cap_top": 186, "size": 29.5,
                 "line_pitch": 34.5, "credit_gap": 51, "credit_size": 21.5,
                 "credit_lines": False},
    },
    # Medido en ref2
    "ciudad": {
        "zoom_keys": [[0.0, 1.17], [0.9, 1.16], [1.4, 1.12], [1.9, 1.08], [2.4, 1.04], [3.0, 1.0]],
        "zoom_center": [292, 362],
        "float_amp": [3.5, 3.5], "float_period": 4.8, "float_phase_t": 6.0,
        "fade_in": 0.75, "fade_out": 0.45,
        "text": {"x": 20, "quote_top": 187, "line1_cap_top": 209, "size": 32.0,
                 "line_pitch": 41.0, "credit_gap": 47, "credit_size": 21.0,
                 "credit_lines": True},
    },
}

STYLES = {
    "white":    {"core": (255, 255, 255), "glow": [(255, 255, 255, 10, 0.55), (255, 255, 255, 26, 0.22)]},
    # Muestreo ref2 t=26 s: núcleo ~ (242,86,88), halo ~ (151,58,51)
    "neon_red": {"core": (255, 92, 92),   "glow": [(255, 40, 40, 9, 0.95), (255, 30, 30, 22, 0.75),
                                                   (220, 20, 20, 48, 0.45)]},
}


# ---------------------------------------------------------------- utilidades
def pchip(keys, t):
    """Interpolación cúbica monótona (Fritsch-Carlson) sobre [[t, v], ...]."""
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    if t <= xs[0]: return ys[0]
    if t >= xs[-1]: return ys[-1]
    n = len(xs); h = [xs[i+1]-xs[i] for i in range(n-1)]; d = [(ys[i+1]-ys[i])/h[i] for i in range(n-1)]
    m = [0.0]*n
    m[0], m[-1] = d[0], 0.0  # termina con velocidad cero (ease-out)
    for i in range(1, n-1):
        m[i] = 0.0 if d[i-1]*d[i] <= 0 else 3*(h[i-1]+h[i])/((2*h[i]+h[i-1])/d[i-1]+(h[i]+2*h[i-1])/d[i])
    i = max(j for j in range(n-1) if xs[j] <= t)
    s = (t-xs[i])/h[i]
    h00, h10, h01, h11 = 2*s**3-3*s**2+1, s**3-2*s**2+s, -2*s**3+3*s**2, s**3-s**2
    return h00*ys[i]+h10*h[i]*m[i]+h01*ys[i+1]+h11*h[i]*m[i+1]


def font(path, size, weight=None):
    f = ImageFont.truetype(path, int(round(size)))
    if weight is not None:
        try: f.set_variation_by_axes([weight] if "Montserrat" in path else [weight, 100])
        except Exception: pass
    return f


def cover(img, W, H, focus=(0.5, 0.5)):
    """Escala tipo 'cover' y recorta respetando el punto focal."""
    s = max(W/img.width, H/img.height)
    img = img.resize((max(W, round(img.width*s)), max(H, round(img.height*s))), Image.LANCZOS)
    x = int((img.width-W)*focus[0]); y = int((img.height-H)*focus[1])
    return img.crop((x, y, x+W, y+H))


# ---------------------------------------------------------------- render
class Renderer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.W, self.H = cfg.get("size", [1080, 1336])
        self.fps = cfg.get("fps", 60)
        self.P = json.loads(json.dumps(PRESETS[cfg.get("preset", "luna")]))
        for k, v in cfg.get("overrides", {}).items():
            if k == "text": self.P["text"].update(v)
            else: self.P[k] = v
        self.k = self.W / REF_W                         # escala ref -> salida
        self.oy = (self.H - REF_H*self.k) / 2           # centra el cuadro 72:89 si el lienzo es 9:16
        self.WR = cfg.get("world_res", 2.0)             # supermuestreo del fondo para el zoom inicial
        self.dur = cfg["duration"]
        self._build_world()
        self._text_cache = {}
        self.fonts = {
            "lyric": os.path.join(HERE, "fonts", "Montserrat-VF.ttf"),
            "credit": os.path.join(HERE, "fonts", "OpenSans-VF.ttf"),
        }

    def R(self, x, y):  # coords de referencia -> salida
        return x*self.k, y*self.k + self.oy

    def _build_world(self):
        c = self.cfg; WR = self.WR
        Ww, Hw = round(self.W*WR), round(self.H*WR)
        bg = Image.open(c["background"]).convert("RGB")
        world = cover(bg, Ww, Hw, tuple(c.get("background_focus", [0.5, 0.5]))).convert("RGBA")
        ch = c.get("character")
        if ch:
            im = Image.open(ch["image"]).convert("RGBA")
            h = ch.get("height", 0.62) * Hw
            im = im.resize((round(im.width*h/im.height), round(h)), Image.LANCZOS)
            cx, by = ch.get("center_x", 0.5)*Ww, ch.get("bottom_y", 1.0)*Hw
            world.alpha_composite(im, (round(cx-im.width/2), round(by-im.height)))
        g = c.get("grade", {})
        if g:
            a = np.asarray(world.convert("RGB"), np.float32)/255
            a = a*g.get("exposure", 1.0)
            if "vignette" in g:
                yy, xx = np.mgrid[0:Hw, 0:Ww]; r = np.sqrt(((xx/Ww-0.5)/0.5)**2+((yy/Hw-0.5)/0.5)**2)
                a *= (1 - g["vignette"]*np.clip(r-0.35, 0, None)**1.5)[..., None]
            world = Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8)).convert("RGBA")
        self.world = world.convert("RGB")

    # --- capas de texto (a resolución de salida, coordenadas de mundo sin cámara)
    def text_layer(self, text, style, with_quote, with_credit):
        key = (text, style, with_quote, with_credit)
        if key in self._text_cache: return self._text_cache[key]
        T = self.P["text"]; k = self.k
        size = T["size"]*k; fL = font(self.fonts["lyric"], size, 800)
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        x, _ = self.R(T["x"], 0)
        cap = 0.70*size                                   # cap height Montserrat ≈ 0.70 em
        asc = fL.getmetrics()[0]
        st = STYLES[style]
        if with_quote:
            _, qy = self.R(0, T["quote_top"])
            qtop = fL.getbbox('"')[1]
            d.text((x, qy - qtop), '"', font=fL, fill=(255, 255, 255, 255))
        if text:
            _, y1 = self.R(0, T["line1_cap_top"])
            base1 = y1 + cap
            for i, line in enumerate(text.split("\n")):
                d.text((x, base1 + i*T["line_pitch"]*k - asc), line, font=fL, fill=st["core"]+(255,))
        if with_credit and self.cfg.get("credit"):
            fC = font(self.fonts["credit"], T["credit_size"]*k, 400)
            n_lines = T.get("credit_after_lines", 3)   # el crédito no se mueve aunque la letra tenga 1-2 líneas
            _, y1 = self.R(0, T["line1_cap_top"])
            last_base = y1 + cap + (n_lines-1)*T["line_pitch"]*k
            cb = last_base + T["credit_gap"]*k
            cascC = fC.getmetrics()[0]
            for j, cl in enumerate(self.cfg["credit"].split("\n")):
                d.text((x, cb + j*T["credit_size"]*k*1.25 - cascC), cl, font=fC, fill=(240, 240, 240, 255))
        # brillo
        alpha = layer.split()[3]
        out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        glows = st["glow"] if text else STYLES["white"]["glow"]
        for (r, g, b, rad, op) in glows:
            ga = alpha.filter(ImageFilter.GaussianBlur(rad*k/1.875)).point(lambda v, op=op: min(255, int(v*op)))
            gl = Image.new("RGBA", layer.size, (r, g, b, 0)); gl.putalpha(ga)
            out.alpha_composite(gl)
        out.alpha_composite(layer)
        bb = out.getbbox() or (0, 0, 1, 1)
        res = (out.crop(bb), bb)
        self._text_cache[key] = res
        return res

    # --- cámara: devuelve (escala, dx, dy) en píxeles de salida
    def camera(self, t):
        P = self.P; k = self.k
        s = pchip(P["zoom_keys"], t)
        ax, ay = P["float_amp"]
        ph = 2*math.pi*(t - P["float_phase_t"])/P["float_period"]
        f = -math.cos(ph)                  # mínimo en float_phase_t
        return s, ax*k*f, ay*k*f

    def affine(self, t, res):
        """Coeficientes de PIL.transform: salida -> fuente (fuente a resolución res*salida)."""
        s, dx, dy = self.camera(t)
        cx, cy = self.R(*self.P["zoom_center"])
        # punto de salida (u,v) -> mundo: ((u - cx - dx)/s + cx, (v - cy - dy)/s + cy)
        a = 1/s; c = (-cx-dx)/s + cx; e = (-cy-dy)/s + cy
        return (a*res, 0, c*res, 0, a*res, e*res)

    def text_alpha(self, t, ev):
        fi, fo = ev.get("fade_in", 0.25), ev.get("fade_out", 0.25)
        if t < ev["start"] or t > ev["end"]: return 0.0
        a = min(1.0, (t-ev["start"])/fi if fi > 0 else 1.0)
        if not ev.get("hold_to_end"): a = min(a, (ev["end"]-t)/fo if fo > 0 else 1.0)
        return max(0.0, min(1.0, a))

    def _paste(self, img, t, layer, alpha):
        """Transforma solo el recuadro de la capa de texto con la misma cámara que el fondo."""
        crop, (x0, y0, x1, y1) = layer
        s, dx, dy = self.camera(t)
        cx, cy = self.R(*self.P["zoom_center"])
        fw = lambda x, c, d: s*(x-c)+c+d
        u0 = max(0, int(math.floor(fw(x0, cx, dx)))-2); v0 = max(0, int(math.floor(fw(y0, cy, dy)))-2)
        u1 = min(self.W, int(math.ceil(fw(x1, cx, dx)))+2); v1 = min(self.H, int(math.ceil(fw(y1, cy, dy)))+2)
        if u1 <= u0 or v1 <= v0: return
        a, _, c, _, _, e = self.affine(t, 1.0)
        L = crop.transform((u1-u0, v1-v0), Image.AFFINE, (a, 0, a*u0+c-x0, 0, a, a*v0+e-y0), Image.BICUBIC)
        if alpha < 1: L.putalpha(L.split()[3].point(lambda v: int(v*alpha)))
        img.alpha_composite(L, (u0, v0))

    def frame(self, t):
        W, H = self.W, self.H
        img = self.world.transform((W, H), Image.AFFINE, self.affine(t, self.WR), Image.BICUBIC).convert("RGBA")
        ev_list = self.cfg["lyrics"]
        first = min(e["start"] for e in ev_list) if ev_list else 1e9
        # elementos fijos (comilla + crédito) aparecen con la primera letra y se quedan
        fixed_a = 0.0 if t < first else min(1.0, (t-first)/0.25)
        if fixed_a > 0:
            self._paste(img, t, self.text_layer("", "white", True, True), fixed_a)
        for ev in ev_list:
            a = self.text_alpha(t, ev)
            if a > 0:
                self._paste(img, t, self.text_layer(ev["text"], ev.get("style", "white"), False, False), a)
        # fundidos a negro
        P = self.P; m = 1.0
        if t < P["fade_in"]: m = (t/P["fade_in"])**1.6
        if t > self.dur-P["fade_out"]: m = min(m, max(0.0, (self.dur-t)/P["fade_out"]))
        rgb = img.convert("RGB")
        if m < 1: rgb = Image.eval(rgb, lambda v: int(v*m))
        return rgb


def audio_filter(cfg):
    a = cfg.get("audio", {})
    fi, fo, d = a.get("fade_in", 1.0), a.get("fade_out", 2.0), cfg["duration"]
    return f"afade=t=in:st=0:d={fi},afade=t=out:st={max(0, d-fo):.3f}:d={fo}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config"); ap.add_argument("--out"); ap.add_argument("--preview")
    ap.add_argument("--fps", type=int)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.config))
    for k in ("background",):
        cfg[k] = os.path.join(base, cfg[k])
    if cfg.get("character"): cfg["character"]["image"] = os.path.join(base, cfg["character"]["image"])
    if cfg.get("audio", {}).get("file"): cfg["audio"]["file"] = os.path.join(base, cfg["audio"]["file"])
    if a.fps: cfg["fps"] = a.fps
    # En las referencias el cambio es secuencial: la frase saliente se apaga (0.25 s) y la entrante
    # empieza a aparecer justo cuando la anterior termina. Se corrigen solapamientos.
    ev = sorted(cfg["lyrics"], key=lambda e: e["start"])
    for e, nxt in zip(ev, ev[1:]):
        e["end"] = min(e.get("end", nxt["start"]), nxt["start"])
    if ev and "end" not in ev[-1]: ev[-1]["end"] = cfg["duration"]; ev[-1]["hold_to_end"] = True
    cfg["lyrics"] = ev
    r = Renderer(cfg)
    if a.preview:
        os.makedirs(os.path.join(base, "preview"), exist_ok=True)
        for t in a.preview.split(","):
            r.frame(float(t)).save(os.path.join(base, "preview", f"t{float(t):06.2f}.png"))
        print("preview ok"); return
    out = a.out or os.path.join(base, cfg.get("output", "salida.mp4"))
    n = int(round(cfg["duration"]*r.fps))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{r.W}x{r.H}",
           "-r", str(r.fps), "-i", "-"]
    au = cfg.get("audio", {})
    if au.get("file"):
        cmd += ["-ss", str(au.get("start", 0)), "-t", str(cfg["duration"]), "-i", au["file"],
                "-map", "0:v", "-map", "1:a", "-af", audio_filter(cfg),
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(r.frame(i/r.fps).tobytes())
        if i % (r.fps*5) == 0: print(f"  {i/r.fps:5.1f}s / {cfg['duration']}s", flush=True)
    p.stdin.close(); p.wait()
    print("ok", out)


if __name__ == "__main__":
    main()
