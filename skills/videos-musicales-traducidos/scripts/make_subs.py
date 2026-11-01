"""Subtitle layers (PNG), plates/gradients, SRTs and alignment tables from a piece JSON.

Usage: python make_subs.py pieces/<piece>.json [vertical|horizontal]

The piece's "subs" list is the MASTER table of the complete song (source seconds). Each format
("vertical" fragment, "horizontal" complete song) derives its own montage times by subtracting
its "in" point, so both versions share one translation.

Text conventions in "es": '\n' = line break (vertical), *word* = accent colour.
Horizontal joins the two lines when they fit in 42 chars, unless "es_h" is given.
Writes subs/<id>/<fmt>/: sub_XXX.png, gradient.png, timing.json, <id>_<SUFFIX>.srt
and subs/<id>/<id>_alineacion_maestra.csv (+ .json).
"""
import csv
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()   # project folder: pieces/, media/, subs/, ...
FONT = os.path.join(ROOT, "fonts", "Inter.woff2")
if not os.path.exists(FONT):        # fall back to the copy bundled with the skill (Inter, SIL OFL)
    FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "Inter.woff2")
TEXT_RGB = (255, 246, 234)        # warm white
OUTLINE = (18, 8, 10)
LINE_GAP = 1.18
MIN_GAP = 0.085                   # ~2 frames between consecutive subtitles
DEFAULT_HOLD = 0.25
SUFFIX = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_COMPLETO_16x9"}

# per-format layout; a piece can override any key in piece[fmt]["layout"]
LAYOUT = {
    "vertical": {"W": 1080, "H": 1920, "size": 64, "min_size": 56, "max_w": 790, "cx": 500,
                 "cy": 1290, "cy_top": 360, "stroke": 3, "shadow": 7, "max_chars": 34,
                 "band": [1040, 1210, 1380, 1560, 0.42]},
    "horizontal": {"W": 1920, "H": 1080, "size": 54, "min_size": 46, "max_w": 1560, "cx": 960,
                   "cy": 878, "cy_top": 200, "stroke": 3, "shadow": 6, "max_chars": 42,
                   "band": [700, 800, 960, 1080, 0.40]},
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def parse_line(line):
    """'pero tu amor es tan *agridulce*' -> [(text, accent?)]"""
    return [(c, i % 2 == 1) for i, c in enumerate(line.split("*")) if c]


def fit_font(lines, L):
    """Largest size <= L['size'] (min L['min_size']) whose widest line fits L['max_w']."""
    for size in range(L["size"], L["min_size"] - 1, -2):
        font = ImageFont.truetype(FONT, size)
        font.set_variation_by_name("SemiBold")
        if max(font.getlength("".join(p for p, _ in parts)) for parts in lines) <= L["max_w"]:
            return font, size
    return font, size


def band(L, top, peak0, peak1, bot, strength, x0=0, x1=None, feather_x=0):
    """Localized dark band (smoothstep edges); optional horizontal limits for a plate."""
    W, H = L["W"], L["H"]
    x1 = W if x1 is None else x1
    img = Image.new("L", (W, H), 0)
    px = img.load()
    for y in range(max(0, top), min(H, bot)):
        if y < peak0:
            a = (y - top) / max(1, peak0 - top)
        elif y <= peak1:
            a = 1.0
        else:
            a = 1 - (y - peak1) / max(1, bot - peak1)
        a = a * a * (3 - 2 * a) * strength
        for x in range(max(0, x0 - feather_x), min(W, x1 + feather_x)):
            ax = 1.0
            if x < x0:
                ax = (x - (x0 - feather_x)) / feather_x
            elif x >= x1:
                ax = 1 - (x - x1) / feather_x
            ax = ax * ax * (3 - 2 * ax)
            px[x, y] = int(255 * a * ax)
    out = Image.new("RGBA", (W, H), (8, 3, 4, 0))
    out.putalpha(img)
    return out


def plate_img(L, p):
    """Opaque-core plate that hides burned-in text (IMPULSIVE)."""
    f = p.get("feather", 14)
    img = band(L, p["y0"] - f, p["y0"], p["y1"], p["y1"] + f, p.get("alpha", 0.93), p["x0"], p["x1"],
               f if p["x1"] - p["x0"] < L["W"] else 0)
    col = hex_rgb(p.get("color", "#07080C"))
    r, g, b, a = img.split()
    return Image.merge("RGBA", (Image.new("L", img.size, col[0]), Image.new("L", img.size, col[1]),
                                Image.new("L", img.size, col[2]), a))


def render(text, accent_rgb, path, L, pos="low"):
    W, H = L["W"], L["H"]
    lines = [parse_line(l) for l in text.split("\n")]
    font, size = fit_font(lines, L)
    asc, desc = font.getmetrics()
    lh = int(size * LINE_GAP)
    block_h = lh * (len(lines) - 1) + asc + desc
    y0 = (L["cy_top"] if pos == "top" else L["cy"]) - block_h // 2
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    d, dm = ImageDraw.Draw(text_layer), ImageDraw.Draw(mask)
    max_w = 0
    for i, parts in enumerate(lines):
        lw = font.getlength("".join(p for p, _ in parts))
        max_w = max(max_w, lw)
        x, y = L["cx"] - lw / 2, y0 + i * lh
        for chunk, acc in parts:
            d.text((x, y), chunk, font=font, fill=(accent_rgb if acc else TEXT_RGB) + (255,))
            dm.text((x, y), chunk, font=font, fill=255, stroke_width=L["stroke"])
            x += font.getlength(chunk)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh_mask = mask.filter(ImageFilter.GaussianBlur(L["shadow"])).point(lambda v: int(v * 0.55))
    shadow.paste((0, 0, 0, 255), (0, 4), sh_mask)
    outline = Image.new("RGBA", (W, H), OUTLINE + (0,))
    outline.putalpha(mask.point(lambda v: int(v * 0.85)))
    out = Image.alpha_composite(Image.alpha_composite(shadow, outline), text_layer)
    if pos == "top":
        c = L["cy_top"]
        out = Image.alpha_composite(band(L, c - 250, c - 80, c + 80, c + 250, 0.42), out)
    out.save(path, optimize=True)
    return {"lines": len(lines), "size": size, "max_line_px": round(max_w),
            "x0": round(L["cx"] - max_w / 2), "x1": round(L["cx"] + max_w / 2), "y0": y0, "y1": y0 + block_h}


def text_for(s, fmt, L):
    if fmt == "horizontal":
        if "es_h" in s:
            return s["es_h"]
        lines = s["es"].split("\n")
        joined = " ".join(lines)
        return joined if len(joined.replace("*", "")) <= L["max_chars"] else s["es"]
    return s["es"]


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_format(piece, fmt):
    cfg = piece[fmt]
    L = dict(LAYOUT[fmt], **cfg.get("layout", {}))
    out_dir = os.path.join(ROOT, "subs", piece["id"], fmt)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.startswith("sub_") and old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    a_in, a_out = cfg["in"], cfg["out"]
    dur = a_out - a_in
    accent = hex_rgb(piece["accent"])
    subs = piece["subs"]
    timing = []
    for i, s in enumerate(subs):
        m_in = s["src_in"] - a_in
        m_out = s["src_out"] - a_in + s.get("hold", DEFAULT_HOLD)
        if i + 1 < len(subs):
            m_out = min(m_out, subs[i + 1]["src_in"] - a_in - MIN_GAP)
        if m_out <= 0.3 or m_in >= dur - 0.3:
            continue                      # outside this format's interval
        m_in, m_out = max(m_in, 0.0), min(m_out, dur - 0.05)
        text = text_for(s, fmt, L)
        png = f"sub_{i + 1:03d}.png"
        pos = s.get("pos" if fmt == "vertical" else "pos_h", "low")
        geo = render(text, accent, os.path.join(out_dir, png), L, pos)
        plain = text.replace("*", "")
        timing.append({"n": i + 1, "png": png, "in": round(m_in, 3), "out": round(m_out, 3), "es": plain,
                       "cps": round(len(plain.replace("\n", " ")) / (m_out - m_in), 1),
                       "max_line_chars": max(len(l) for l in plain.split("\n")), **geo})
    if cfg.get("plate"):
        plate_img(L, cfg["plate"]).save(os.path.join(out_dir, "gradient.png"), optimize=True)
    else:
        b = L["band"]
        band(L, *b).save(os.path.join(out_dir, "gradient.png"), optimize=True)
    srt = os.path.join(out_dir, f"{piece['id']}_{SUFFIX[fmt]}.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for k, t in enumerate(timing):
            f.write(f"{k + 1}\n{srt_time(t['in'])} --> {srt_time(t['out'])}\n{t['es']}\n\n")
    json.dump(timing, open(os.path.join(out_dir, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    flags = 0
    for t in timing:
        bad = (t["cps"] > 20 or t["max_line_chars"] > L["max_chars"] or t["x0"] < L.get("safe_x0", 100)
               or t["x1"] > L.get("safe_x1", L["W"] - 100))
        if bad:
            flags += 1
            print(f"  revisar {fmt} #{t['n']}: cps={t['cps']} chars={t['max_line_chars']} x={t['x0']}-{t['x1']} {t['es']!r}")
    print(f"{fmt}: {len(timing)} subtitulos, {flags} a revisar -> {srt}")
    return timing


def master_table(piece, timings):
    rows = []
    for i, s in enumerate(piece["subs"]):
        row = {"n": i + 1, "archivo_fuente": os.path.basename(piece["audio_file"]), "fuente_in_s": s["src_in"],
               "fuente_out_s": s["src_out"], "ingles_transcrito": s["en"],
               "espanol": s["es"].replace("*", "").replace("\n", " / "), "confianza_observaciones": s["conf"]}
        for fmt, tl in timings.items():
            t = next((t for t in tl if t["n"] == i + 1), None)
            row[f"{fmt}_in_s"] = t["in"] if t else ""
            row[f"{fmt}_out_s"] = t["out"] if t else ""
        rows.append(row)
    base = os.path.join(ROOT, "subs", piece["id"], f"{piece['id']}_alineacion_maestra")
    with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json.dump({"id": piece["id"], "vertical_interval_src_s": [piece["vertical"]["in"], piece["vertical"]["out"]],
               "horizontal_interval_src_s": [piece["horizontal"]["in"], piece["horizontal"]["out"]], "rows": rows},
              open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    piece = json.load(open(sys.argv[1], encoding="utf-8"))
    fmts = sys.argv[2:] or [f for f in ("vertical", "horizontal") if f in piece]
    timings = {}
    for fmt in ("vertical", "horizontal"):
        if fmt in piece:
            if fmt in fmts:
                timings[fmt] = build_format(piece, fmt)
            else:
                p = os.path.join(ROOT, "subs", piece["id"], fmt, "timing.json")
                timings[fmt] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    master_table(piece, timings)


if __name__ == "__main__":
    main()
