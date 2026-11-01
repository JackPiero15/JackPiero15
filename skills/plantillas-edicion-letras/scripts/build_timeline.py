"""Construye la pieza (eventos flash/hold con letra tecleada) desde una tabla de líneas + tiempos de palabra de Whisper.

Generaliza los builders de Dinero y Down For Real (misma lógica de troceo y alternancia blanco/negro).
Ejecutar desde la raíz del proyecto (rutas relativas a ella):
    python tools/build_timeline.py lineas.json
Salida: pieces/<id>.json (para render_letras.py) y pieces/<id>_table.json (tabla en/es para revisión).
Config: ver assets/plantilla_lineas.json.
"""
import json, math, pathlib, sys

C = json.load(open(sys.argv[1], encoding="utf-8"))
IN, OUT = C.get("in", 0.0), C["out"]
WORDS = [w["s"] for s in json.load(open(C.get("words", "work/tr.json"), encoding="utf-8"))["segments"]
         for w in s["words"] if IN - 0.1 <= w["s"] < OUT]
idx = {}
if pathlib.Path(C.get("sheet_index", "work/sheet_index.txt")).exists():
    idx = {int(l.split()[0]): l.split()[1] for l in open(C.get("sheet_index", "work/sheet_index.txt"), encoding="utf-8") if l.strip()}
IMG_DEF = C.get("image_defaults", {"k": 3.6, "dim": 0.5})
MIN_GAP = C.get("min_word_gap", 0.16)     # palabras más juntas que esto se funden en un solo paso
MIN_SWAP = C.get("min_flash_swap", 0.28)  # separación mínima entre cambios de fondo en modo flash

L = C["lines"]
images, img_of = [], {}
for r in L:
    im = r.get("img")
    if im is not None and im not in img_of:
        img_of[im] = len(images)
        spec = {"file": idx[im] if isinstance(im, int) else im, **IMG_DEF, **r.get("img_spec", {})}
        if r.get("tint") is not None: spec["tint"] = r["tint"]
        images.append(spec)

events, bg, last_swap, table = [], 0, -9, []
for r in L:
    a, e, en, es, mode = r["t0"], r["t1"], r.get("en", ""), r["es"], r["mode"]
    on = [t for t in WORDS if a - 0.06 <= t < e]
    m = []
    for t in on:
        if not m or t - m[-1] >= MIN_GAP: m.append(t)
    on = m or [a]
    # 1) agrupar palabras en español hasta tener <= tantos pasos como golpes de voz
    chunks = [[w] for w in es.split()]
    while len(chunks) > len(on):
        j = min(range(len(chunks) - 1), key=lambda j: len(" ".join(chunks[j] + chunks[j + 1])))
        chunks[j] = chunks[j] + chunks[j + 1]; del chunks[j + 1]
    steps, done = [], []
    for c in chunks: done = done + c; steps.append(" ".join(done))
    # 2) si sobran golpes, partir la palabra más larga con "_" / "-" (efecto tecleo)
    full_s, split, mark = list(steps), set(), 0
    while len(steps) < len(on):
        best = None
        for j, st in enumerate(full_s):
            if j in split: continue
            prev = full_s[j - 1] if j > 0 else ""
            add = st[len(prev):].strip()
            if best is None or len(add) > best[1]: best = (j, len(add), prev, add)
        if best is None or best[1] < 5: on = on[:len(steps)]; break
        j, Ln, prev, add = best; split.add(j)
        cut = max(2, int(math.ceil(Ln * 0.55)))
        steps.insert(steps.index(full_s[j]), (prev + " " + add[:cut]).strip() + ("_" if mark % 2 == 0 else "-")); mark += 1
    if C.get("reset_questions", True):   # preguntas repetidas: cada "?" reinicia el texto en pantalla
        steps = [st.split("? ")[-1] if "? " in st else st for st in steps]
    for k, (t, txt) in enumerate(zip(on, steps)):
        to = round(max(0.0, t - IN - 0.03), 3)
        ev = {"t": to, "text": txt, "line": es}
        if mode == "flash":
            sw = (to - last_swap) >= MIN_SWAP or k == 0
            if sw: bg ^= 1; last_swap = to
            ev.update({"mode": "flash", "bg": "w" if bg else "b", "swap": sw})
        else:
            ev.update({"mode": "hold", "img": img_of[r["img"]], "img_t0": round(max(0.0, a - IN - 0.03), 3), "swap": k == 0})
            last_swap = to
        events.append(ev)
    table.append({"t0": round(a - IN, 2), "en": en, "es": es, "mode": mode})
events[0]["t"] = 0.0

piece = {"id": C["id"]}
if C.get("rgb"): piece["rgb"] = True
piece.update({"duration": C.get("duration", round(OUT - IN, 3)), "font": C.get("font", "fonts/RobotoCondensed-Variable.ttf"),
              "font_size": C.get("font_size", 84), "font_weight": C.get("font_weight", 400), "text_y": C.get("text_y", 960),
              "max_text_w": C.get("max_text_w", 860), "images": images, "events": events, "fade_out": C.get("fade_out", 0.5)})
pathlib.Path("pieces").mkdir(exist_ok=True)
json.dump(piece, open(f"pieces/{C['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(table, open(f"pieces/{C['id']}_table.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(events), "eventos", piece["duration"], "s;", sum(1 for e in events if e["mode"] == "flash" and e["swap"]), "cambios de fondo")
