"""Spanish lyrics (Markdown) per song from the master table: complete song by section + vertical selection.

Usage: python gen_letras.py <piece> [<piece> ...]   -> letras/<id>_letra_es.md
Sections come from piece["horizontal"]["markers"]; the title from piece["title"].
Lines whose "conf" starts with BAJA are marked with a dagger and listed in the notes.
"""
import json
import os
import sys

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()


def clean(s):
    return s["es"].replace("*", "").replace("\n", " ")


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main():
    os.makedirs(os.path.join(ROOT, "letras"), exist_ok=True)
    for name in sys.argv[1:]:
        p = json.load(open(os.path.join(ROOT, "pieces", name + ".json"), encoding="utf-8"))
        marks = sorted(p.get("horizontal", {}).get("markers", []))
        v = p["vertical"]
        lines = [f"# {p.get('title', p['id'])}", "",
                 "Adaptación al español latino, alineada con el audio original. Las líneas con † tienen palabras "
                 "que no se distinguen con seguridad (ver notas); se tradujo solo lo que se oye con certeza.", "",
                 "## Canción completa (versión YouTube)", ""]
        sec, notes = None, []
        for s in p["subs"]:
            cur = None
            for t, label in marks:
                if s["src_in"] >= t - 0.3:
                    cur = label
            if cur != sec:
                sec = cur
                lines += ["", f"### {sec} ({mmss(s['src_in'])})" if sec else "", ""]
            low = s["conf"].upper().startswith("BAJA")
            lines.append(clean(s) + (" †" if low else "") + "  ")
            if low or s["conf"].lower().startswith("media"):
                notes.append(f"- {mmss(s['src_in'])} — «{clean(s)}»: {s['conf']}")
        lines += ["", f"## Selección vertical: {mmss(v['in'])} – {mmss(v['out'])} ({v['out'] - v['in']:.1f} s)", ""]
        lines += [clean(s) + "  " for s in p["subs"] if s["src_out"] > v["in"] + 0.3 and s["src_in"] < v["out"] - 0.3]
        lines += ["", "## Notas de confianza", ""] + (notes or ["- Sin dudas pendientes."])
        out = os.path.join(ROOT, "letras", f"{p['id']}_letra_es.md")
        open(out, "w", encoding="utf-8").write("\n".join(lines).replace("\n\n\n", "\n\n") + "\n")
        print(out)


if __name__ == "__main__":
    main()
