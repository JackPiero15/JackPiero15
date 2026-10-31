"""Event timeline for Down For Real (source 31.02 -> 90.55)."""
import json, math
IN, OUT = 31.02, 90.55
WORDS = [w["s"] for s in json.load(open("work/tr.json"))["segments"] for w in s["words"] if IN - 0.1 <= w["s"] < OUT]
idx = {int(l.split()[0]): l.split()[1] for l in open("work/sheet_index.txt")}
V, P, B = [125, 70, 205], [205, 90, 175], [70, 95, 210]
L = [  # (src_start, src_end, en, es, mode, sheet_img, tint)
 (31.10, 32.40, "Uh, I want confirmation, baby", "Quiero una confirmación, bebé", "flash", None, None),
 (32.40, 33.54, "I'm insecure and I'm crazy", "Soy inseguro y estoy loco", "flash", None, None),
 (33.54, 36.20, "When we together in person, it's picture perfect", "Cuando estamos juntos, todo es perfecto", "hold", 2, P),
 (36.20, 38.15, "But lately, I find it harder to feel you", "Pero últimamente me cuesta más sentirte", "flash", None, None),
 (38.18, 40.45, "Find it harder to get near you through my phone screen", "Me cuesta acercarme a ti a través de la pantalla", "hold", 69, V),
 (40.50, 42.25, "The disconnect is making me fear you", "La distancia me está haciendo temerte", "flash", None, None),
 (42.30, 44.10, "Can you tell that it's different?", "¿Notas que es diferente?", "flash", None, None),
 (44.14, 45.22, "Think there's something missing", "Creo que algo falta", "flash", None, None),
 (45.26, 47.98, "Even when we're kissing it feels like you're distant", "Incluso cuando nos besamos, te siento distante", "hold", 72, B),
 (48.02, 50.44, "I'm sick and tired of asking you to listen", "Estoy harto de pedirte que me escuches", "flash", None, None),
 (50.48, 51.68, "It takes two to tango", "Esto es cosa de dos", "flash", None, None),
 (51.72, 53.80, "Are you willing to fix this?", "¿Estás dispuesta a arreglarlo?", "flash", None, None),
 (53.88, 56.40, "'Cause I'm down if you're down", "Porque yo voy si tú vas", "hold", 80, P),
 (56.44, 59.22, "'Cause I'm down if you're down", "Porque yo voy si tú vas", "hold", 76, V),
 (59.26, 61.96, "'Cause I'm down if you're down", "Porque yo voy si tú vas", "hold", 1, P),
 (62.00, 63.32, "'Cause I'm down if you're down", "Porque yo voy si tú vas", "hold", 83, V),
 (63.36, 66.10, "Baby, are you down, for real?", "Bebé, ¿de verdad vas en serio?", "hold", 0, B),
 (66.14, 68.54, "I get worried when I'm not with you", "Me preocupo cuando no estoy contigo", "hold", 60, V),
 (68.58, 70.98, "Go and tell me how you feel", "Anda, dime lo que sientes", "hold", 64, V),
 (71.02, 74.18, "Is it reciprocated when I miss you?", "¿Es mutuo cuando te extraño?", "hold", 75, B),
 (74.22, 76.56, "Baby, are you down, for real?", "Bebé, ¿de verdad vas en serio?", "hold", 81, V),
 (76.60, 79.52, "Or is it just talk, I can't tell", "¿O son solo palabras? No lo sé", "hold", 104, B),
 (79.56, 81.70, "Say you love me, but you shut me out", "Dices que me amas, pero me cierras la puerta", "hold", 61, V),
 (81.74, 84.58, "Can't help but wonder if there's someone else", "No puedo evitar preguntarme si hay alguien más", "hold", 62, B),
 (84.62, 87.88, "I been waitin' on you, banking on you, baby", "Te he estado esperando, apostando por ti, bebé", "flash", None, None),
 (87.92, 90.55, "Hating that you thinking that I'm changing", "Odio que pienses que estoy cambiando", "flash", None, None),
]
images, img_of = [], {}
for r in L:
    if r[5] is not None and r[5] not in img_of:
        img_of[r[5]] = len(images); images.append({"file": idx[r[5]], "k": 3.6, "dim": 0.5, "tint": r[6]})
events, bg, last_swap, table = [], 0, -9, []
for i, (a, e, en, es, mode, im, tint) in enumerate(L):
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
    steps = [st.split("? ")[-1] if "? " in st else st for st in steps]
    for k, (t, txt) in enumerate(zip(on, steps)):
        to = round(max(0.0, t - IN - 0.03), 3)
        ev = {"t": to, "text": txt, "line": es}
        if mode == "flash":
            sw = (to - last_swap) >= 0.28 or k == 0
            if sw: bg ^= 1; last_swap = to
            ev.update({"mode": "flash", "bg": "w" if bg else "b", "swap": sw})
        else:
            ev.update({"mode": "hold", "img": img_of[im], "img_t0": round(max(0.0, a - IN - 0.03), 3), "swap": k == 0})
            last_swap = to
        events.append(ev)
    table.append({"t0": round(a - IN, 2), "en": en, "es": es, "mode": mode})
events[0]["t"] = 0.0
piece = {"id": "downforreal", "duration": round(OUT - IN, 3), "font": "fonts/RobotoCondensed[wght].ttf", "font_size": 84,
         "font_weight": 400, "text_y": 960, "max_text_w": 860, "images": images, "events": events, "fade_out": 0.6}
json.dump(piece, open("pieces/dfr.json", "w"), ensure_ascii=False, indent=1)
json.dump(table, open("pieces/dfr_table.json", "w"), ensure_ascii=False, indent=1)
print(len(events), "events", piece["duration"], "s")
