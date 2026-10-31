"""Event timeline for Dinero (TikTok audio, 60 s). No outfit/clothing photos (sheet idx 67-110 excluded)."""
import json, math
WORDS = [w["s"] for s in json.load(open("work/tr.json"))["segments"] for w in s["words"]]
idx = {int(l.split()[0]): l.split()[1] for l in open("work/sheet_index.txt")}
L = [  # (start, end, en, es, mode, sheet_img)
 (0.00, 4.95, "Ya si quieres dinero, lo siento, no tengo", "Ya, si quieres dinero, lo siento, no tengo", "hold", 41),
 (5.02, 8.92, "She take my dinero, take my dinero", "Ella se lleva mi dinero, se lleva mi dinero", "flash", None),
 (8.98, 12.92, "She take my dinero, take my dinero", "Ella se lleva mi dinero, se lleva mi dinero", "flash", None),
 (12.98, 16.88, "She playin' hella hard, playin' for pesos", "Juega bien duro, juega por pesos", "hold", 9),
 (16.92, 21.15, "She playin' hella hard, playin' for pesos", "Juega bien duro, juega por pesos", "hold", 49),
 (21.24, 23.66, "I whip, whip, I'm rollin'", "Arranco el carro, voy rodando", "hold", 22),
 (23.70, 25.40, "I got my money open", "Traigo el dinero a la vista", "hold", 40),
 (25.46, 30.12, "She text me, 'Good mornin'', then I'm ready to go out and buy", "Me escribe 'buenos días' y ya estoy listo para salir a comprar", "flash", None),
 (30.20, 34.06, "Anything that she likes, get whatever's on her mind", "Todo lo que le guste, lo que se le antoje", "flash", None),
 (34.12, 37.24, "Spendin' money overtime, I'm on", "Gastando dinero sin parar", "flash", None),
 (37.30, 39.16, "Wake myself with the sun of the mornin'", "Me despierto con el sol de la mañana", "hold", 0),
 (39.22, 41.26, "I played myself with a stunner performance", "Me engañé solo por una belleza", "hold", 64),
 (41.30, 43.28, "She take all my money, and now she gone", "Se llevó todo mi dinero y ahora se fue", "flash", None),
 (43.32, 45.72, "I'm broke as a bitch and I'm all alone, yeah", "Estoy jodidamente quebrado y estoy solo", "flash", None),
 (45.78, 47.66, "Tryin' to ball fourty", "Tratando de darme la gran vida", "hold", 6),
 (47.70, 49.78, "Wearin' the same clothes, yeah", "Con la misma ropa, yeah", "hold", 7),
 (49.82, 51.78, "Tryin' to stay low, yeah", "Tratando de pasar desapercibido", "hold", 15),
 (51.82, 53.26, "Lookin' for pesos, yeah", "Buscando pesos, yeah", "hold", 23),
 (53.32, 56.82, "She take my dinero, take my dinero", "Ella se lleva mi dinero, se lleva mi dinero", "flash", None),
 (56.86, 60.00, "She take my dinero, take my-", "Ella se lleva mi dinero, se lleva mi…", "flash", None),
]
assert all(r[5] is None or not (67 <= r[5] <= 110) for r in L)
images, img_of = [], {}
for r in L:
    if r[5] is not None and r[5] not in img_of:
        img_of[r[5]] = len(images); images.append({"file": idx[r[5]], "color": True, "dim": 0.55})
events, bg, last_swap, table = [], 0, -9, []
for i, (a, e, en, es, mode, im) in enumerate(L):
    on = [t for t in WORDS if a - 0.06 <= t < e]
    m = []
    for t in on:
        if not m or t - m[-1] >= 0.16: m.append(t)
    on = m or [a]
    chunks = [[w] for w in es.split()]
    while len(chunks) > len(on):
        j = min(range(len(chunks) - 1), key=lambda j: len(" ".join(chunks[j] + chunks[j + 1])))
        chunks[j] = chunks[j] + chunks[j + 1]; del chunks[j + 1]
    steps, done = [], []
    for c in chunks: done = done + c; steps.append(" ".join(done))
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
    for k, (t, txt) in enumerate(zip(on, steps)):
        to = round(max(0.0, t - 0.03), 3)
        ev = {"t": to, "text": txt, "line": es}
        if mode == "flash":
            sw = (to - last_swap) >= 0.28 or k == 0
            if sw: bg ^= 1; last_swap = to
            ev.update({"mode": "flash", "bg": "w" if bg else "b", "swap": sw})
        else:
            ev.update({"mode": "hold", "img": img_of[im], "img_t0": round(max(0.0, a - 0.03), 3), "swap": k == 0})
            last_swap = to
        events.append(ev)
    table.append({"t0": a, "en": en, "es": es, "mode": mode})
events[0]["t"] = 0.0
piece = {"id": "dinero", "rgb": True, "duration": 60.0, "font": "fonts/RobotoCondensed[wght].ttf", "font_size": 84,
         "font_weight": 400, "text_y": 960, "max_text_w": 860, "images": images, "events": events, "fade_out": 0.4}
json.dump(piece, open("pieces/dinero.json", "w"), ensure_ascii=False, indent=1)
json.dump(table, open("pieces/dinero_table.json", "w"), ensure_ascii=False, indent=1)
print(len(events), "events")
