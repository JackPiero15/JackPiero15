"""Build typing/flash events from a line table + word onsets (clip time). Usage: python build_lines.py justin|laroi"""
import json, math, sys
which = sys.argv[1]
if which == "justin":
    WORDS = [w["s"] for s in json.load(open("justin_tr.json"))["segments"] for w in s["words"]]
    base = json.load(open("/home/user/confident/pieces/confident_v3.json"))
    END = 60.0
    L = [  # (start, end, es, mode, img)
     (0.00, 1.15, "ella es segura", "hold", 0),
     (1.20, 5.10, "Oh, no, no, oh, no, no, y yo me apunto", "hold", 5),
     (5.18, 8.50, "Oh, no, no, oh, no, no, ella es segura", "hold", 6),
     (8.56, 11.45, "Se nota por cómo entra al lugar", "hold", 7),
     (11.50, 12.95, "Dijo que era su primera vez", "flash", None),
     (13.02, 15.20, "Creo que mintió", "flash", None),
     (15.26, 17.05, "Se siente tan bien, carajo", "flash", None),
     (17.10, 18.80, "Y no sé por qué", "flash", None),
     (18.86, 20.20, "Estoy enganchado", "flash", None),
     (20.26, 22.35, "Como un adicto", "flash", None),
     (22.40, 24.50, "Me tiene loco", "flash", None),
     (24.58, 26.15, "Pero aun así, tengo que tenerla", "flash", None),
     (26.22, 29.75, "Explosiva, explosiva", "hold", 1),
     (29.82, 32.85, "Todavía huelo su perfume", "hold", 2),
     (32.92, 37.45, "No cuesta notar que estoy clavado", "hold", 3),
     (37.56, 40.55, "Hipnotizado por cómo se mueve", "hold", 4),
     (40.62, 44.20, "Y empezó a bailar, romance sexual", "flash", None),
     (44.26, 46.05, "Atrevida, pero elegante", "flash", None),
     (46.10, 47.85, "Obra maestra, tipo Mona Lisa", "flash", None),
     (47.88, 49.60, "¿De qué país eres?", "flash", None),
     (49.66, 51.50, "¿Habrá más como tú?", "flash", None),
     (51.54, 54.90, "Tiene mi atención porque es segura", "flash", None),
     (54.96, 58.90, "Oh, no, no, oh, no, no, ella es segura", "hold", 8),
     (58.98, 60.00, "Oh, no, no", "hold", 5),
    ]
else:
    full = json.load(open("/home/user/toomuch/work/tr_medium.json"))
    clip = json.load(open("laroi_tr.json"))
    W1 = [w["s"] - 10.93 for s in full["segments"] for w in s["words"] if 12 < w["s"] - 10.93 + 10.93 and w["s"] - 10.93 < 24.5 and w["s"] - 10.93 > 0]
    W2 = [w["s"] for s in clip["segments"] for w in s["words"] if w["s"] >= 24.5]
    WORDS = sorted(W1 + W2)
    base = json.load(open("/home/user/toomuch/pieces/toomuch.json"))
    END = 60.0
    L = [
     (0.00, 3.60, "", "hold", 8),
     (3.67, 6.80, "Si tuviéramos la oportunidad y el tiempo", "hold", 8),
     (6.87, 9.50, "¿Lo harías otra vez? ¿Lo harías otra vez?", "hold", 9),
     (9.57, 14.50, "¿Fue demasiado? ¿Fue demasiado?", "flash", None),
     (14.59, 16.95, "Ahora llamas a tus amigas porque me fui otra vez", "hold", 10),
     (16.99, 19.60, "Cuando vuelva, ¿lo harías otra vez?", "hold", 11),
     (19.67, 24.55, "¿Fue demasiado? ¿Fue demasiado?", "flash", None),
     (24.65, 29.30, "Entonces dime qué se interpuso y cómo pensé que era bueno que cambiara", "hold", 0),
     (29.38, 31.95, "Y te pido perdón otra vez", "hold", 2),
     (32.00, 34.50, "Ay, nunca supe quitarme de mi camino", "hold", 3),
     (34.56, 37.05, "Vamos de compras y renuevo tu clóset", "hold", 4),
     (37.10, 39.35, "Y aun así solo sabes quejarte", "hold", 5),
     (39.40, 41.95, "Me lo sigues echando en cara", "hold", 6),
     (42.00, 44.80, "Y ahora me dices que necesito espacio", "hold", 7),
     (44.88, 48.30, "Así que estoy tirado en mi cama, alucinando con hongos", "flash", None),
     (48.38, 50.85, "Estaré muerto antes de estar sin ti", "flash", None),
     (50.90, 53.55, "Dándome cuenta de que soy adicto a ti", "hold", 13),
     (53.62, 55.85, "Ven aquí, bebé, relájate y cálmate", "flash", None),
     (55.90, 58.30, "¿Qué dices? Contéstame con tu jugada", "flash", None),
     (58.36, 60.00, "En mi mente no hay nadie más", "hold", 1),
    ]
events, bg, last_swap = [], 0, -9
for i, (a, e, es, mode, img) in enumerate(L):
    on = [t for t in WORDS if a - 0.06 <= t < e]
    m = []
    for t in on:
        if not m or t - m[-1] >= 0.16: m.append(t)
    on = m or [a]
    if not es:
        steps, on = [""], [a]
    else:
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
        to = round(max(0.0, t - 0.03), 3)
        ev = {"t": to, "text": txt, "line": es}
        if mode == "flash":
            sw = (to - last_swap) >= 0.28 or k == 0
            if sw: bg ^= 1; last_swap = to
            ev.update({"mode": "flash", "bg": "w" if bg else "b", "swap": sw})
        else:
            ev.update({"mode": "hold", "img": img, "img_t0": round(max(0.0, a - 0.03), 3), "swap": k == 0})
            last_swap = to
        events.append(ev)
events[0]["t"] = 0.0
base["events"] = events; base["duration"] = END; base["fade_out"] = 0.4
json.dump(base, open(f"pieces/{which}.json", "w"), ensure_ascii=False, indent=1)
print(which, len(events), "events")
