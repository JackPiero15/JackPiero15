"""Build the event timeline (typing chunks, flash/hold modes) for TOO MUCH from the Whisper word times."""
import json, math
tr = json.load(open("work/tr_medium.json"))
WORDS = [(w["s"], w["w"].strip()) for s in tr["segments"] for w in s["words"]]
idx = {int(l.split()[0]): l.split()[1] for l in open("work/sheet_index.txt")}
# source segments -> output: (src_in, src_out, out_offset)
SEGS = [(35.30, 55.56, 0.0), (75.76, 116.20, 20.26)]
def to_out(t):
    for a, b, o in SEGS:
        if a - 0.3 <= t < b + 0.01: return t - a + o
    return None
TINT_BLUE, TINT_CYAN, TINT_VIOLET = [40, 110, 210], [60, 170, 200], [120, 70, 200]
# (src_t0, src_end, en, es, mode, image_sheet_idx|None, tint, conf)
L = [
 (35.58, 37.86, "So tell me what got in the way", "Entonces dime qué se interpuso", "hold", 103, TINT_BLUE, "alta"),
 (37.86, 40.32, "And how I thought it was good that it changed", "y cómo pensé que era bueno que cambiara", "hold", 96, TINT_BLUE, "alta"),
 (40.32, 42.84, "And I'm sayin' I'm sorry again", "Y te pido perdón otra vez", "hold", 3, TINT_CYAN, "alta"),
 (42.84, 45.54, "Oh, I could never get out of my way", "Ay, nunca supe quitarme de mi camino", "hold", 108, TINT_BLUE, "alta: Whisper 'can never', letra 'could never'"),
 (45.54, 48.04, "Hit the store and your wardrobe's replaced", "Vamos de compras y renuevo tu clóset", "hold", 109, TINT_VIOLET, "media: Whisper no lo entiende; letra del usuario"),
 (48.04, 50.32, "And still all that you do is complain", "Y aun así solo sabes quejarte", "hold", 2, TINT_CYAN, "media: Whisper 'the lie that you do'; letra del usuario"),
 (50.32, 52.92, "You keep on throwin' it back in my face", "Me lo sigues echando en cara", "hold", 104, TINT_BLUE, "alta"),
 (52.92, 55.56, "And now you're tellin' me I need some space", "Y ahora me dices que necesito espacio", "hold", 95, TINT_BLUE, "alta"),
 (75.78, 78.42, "If we had the chance and the time to spend", "Si tuviéramos la oportunidad y el tiempo", "hold", 72, TINT_CYAN, "alta"),
 (78.42, 80.80, "Would you do it again? Would you do it again?", "¿Lo harías otra vez? ¿Lo harías otra vez?", "hold", 46, TINT_BLUE, "alta"),
 (81.10, 84.84, "Was it too much? Was it too much?", "¿Fue demasiado? ¿Fue demasiado?", "flash", None, None, "alta"),
 (85.80, 88.52, "Now you're callin' your friends 'cause I'm gone again", "Ahora llamas a tus amigas porque me fui otra vez", "hold", 110, TINT_BLUE, "alta"),
 (88.52, 91.08, "When I'm back around, would you do it again?", "Cuando vuelva, ¿lo harías otra vez?", "hold", 22, TINT_CYAN, "alta"),
 (91.26, 97.40, "Was it too much? Was it too much? Was it too much?", "¿Fue demasiado? ¿Fue demasiado? ¿Fue demasiado?", "flash", None, None, "alta"),
 (97.62, 98.66, "Am I doin' too much?", "¿Me estoy pasando?", "flash", None, None, "alta"),
 (98.86, 100.96, "Do you understand my slang and get my sense of humor?", "¿Entiendes mi jerga y mi sentido del humor?", "flash", None, None, "alta"),
 (101.30, 103.06, "When your girlfriends tell you I been fuckin' 'round", "Cuando tus amigas te digan que ando cogiendo por ahí", "flash", None, None, "alta"),
 (103.06, 106.00, "Would you believe me if I told you that they lyin' and that's just a rumor?", "¿Me creerías si te digo que mienten, que es puro chisme?", "flash", None, None, "alta"),
 (106.34, 108.56, "Send you my personal driver, man, this ain't just a Uber", "Te mando a mi chofer personal, no es cualquier Uber", "hold", 122, TINT_VIOLET, "alta"),
 (108.56, 111.18, "You know it's serious when you stay at mine and bring your toothbrush", "Es en serio si te quedas en mi casa y traes tu cepillo de dientes", "flash", None, None, "alta"),
 (111.18, 113.60, "Extra panties in your bag and some makeup removers", "Calzones extra en tu bolsa y desmaquillante", "flash", None, None, "alta"),
 (113.60, 116.20, "You know I'm hardly on my own 'cause I stay with a shooter", "Casi nunca ando solo, siempre ando con alguien armado", "hold", 115, TINT_BLUE, "alta: Whisper 'shooters'"),
]
images, img_of = [], {}
for (_, _, _, _, mode, ii, tint, _) in L:
    if ii is not None and ii not in img_of:
        img_of[ii] = len(images); images.append({"file": idx[ii], "k": 5.0, "dim": 0.46, "tint": tint, "xerox": True})
events, table, bg, last_swap = [], [], 0, -9
for i, (a, e, en, es, mode, ii, tint, conf) in enumerate(L):
    nxt = L[i + 1][0] if i + 1 < len(L) else 116.20
    on = [t for t, w in WORDS if a - 0.06 <= t < min(nxt, e + 0.3) - 0.05 and to_out(t) is not None]
    m = []
    for t in on:
        if not m or t - m[-1] >= 0.16: m.append(t)
    on = m or [a]
    words = es.split()
    chunks = [[w] for w in words]
    while len(chunks) > len(on):
        j = min(range(len(chunks) - 1), key=lambda j: len(" ".join(chunks[j] + chunks[j + 1])))
        chunks[j] = chunks[j] + chunks[j + 1]; del chunks[j + 1]
    steps, done = [], []
    for c in chunks: done = done + c; steps.append(" ".join(done))
    full, split, mark = list(steps), set(), 0
    while len(steps) < len(on):
        best = None
        for j, st in enumerate(full):
            if j in split: continue
            prev = full[j - 1] if j > 0 else ""
            add = st[len(prev):].strip()
            if best is None or len(add) > best[1]: best = (j, len(add), prev, add)
        if best is None or best[1] < 5:
            on = on[:len(steps)]; break
        j, Ln, prev, add = best; split.add(j)
        cut = max(2, int(math.ceil(Ln * 0.55)))
        steps.insert(steps.index(full[j]), (prev + " " + add[:cut]).strip() + ("_" if mark % 2 == 0 else "-")); mark += 1
    steps = [st.split("? ")[-1] if "? " in st else st for st in steps]   # repeated questions reset like the reference
    for k, (t, txt) in enumerate(zip(on, steps)):
        to = round(max(0.0, to_out(t) - 0.03), 3)
        ev = {"t": to, "text": txt, "line": es, "src": round(t, 2)}
        if mode == "flash":
            sw = (to - last_swap) >= 0.28
            if sw: bg ^= 1; last_swap = to
            ev.update({"mode": "flash", "bg": "w" if bg else "b", "swap": sw or k == 0})
            if k == 0 and not sw: bg ^= 1; ev["bg"] = "w" if bg else "b"; last_swap = to
        else:
            ev.update({"mode": "hold", "img": img_of[ii], "img_t0": round(max(0.0, to_out(a) - 0.03), 3), "swap": k == 0})
            last_swap = to
        events.append(ev)
    table.append({"src_t0": a, "t0": round(to_out(a), 2), "en": en, "es": es, "mode": mode, "conf": conf, "steps": steps})
events[0]["t"] = 0.0
piece = {"id": "toomuch", "duration": 60.7, "font": "fonts/RobotoCondensed[wght].ttf", "font_size": 84, "font_weight": 400,
         "text_y": 960, "max_text_w": 860, "images": images, "events": events, "fade_out": 0.5}
json.dump(piece, open("pieces/toomuch.json", "w"), ensure_ascii=False, indent=1)
json.dump(table, open("pieces/toomuch_table.json", "w"), ensure_ascii=False, indent=1)
for r in table: print(r["t0"], r["mode"], len(r["steps"]), r["steps"][-1] if r["steps"] else "")
print(len(events), "events;", sum(1 for e in events if e["mode"] == "flash" and e["swap"]), "flash swaps")
