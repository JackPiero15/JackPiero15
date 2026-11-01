"""Measurement table (Markdown) for every piece in pieces/*.json from export/*.json written by mux.py
and final_qa.py. Prints it and writes export/tabla_mediciones.md - paste it into the report.
"""
import glob
import json
import os

ROOT = os.environ.get("MT_PROJECT") or os.getcwd()
SUF = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_COMPLETO_16x9"}


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


rows = []
for path in sorted(glob.glob(os.path.join(ROOT, "pieces", "*.json"))):
    p = json.load(open(path, encoding="utf-8"))
    for fmt in ("vertical", "horizontal"):
        if fmt not in p:
            continue
        num, den = p[fmt].get("fps", p["fps"])
        e = os.path.join(ROOT, "export", f"{p['id']}_{SUF[fmt]}.json")
        q = os.path.join(ROOT, "export", f"{p['id']}_{SUF[fmt]}_qa.json")
        if not os.path.exists(e):
            rows.append(f"| {p['id']} | {fmt} | NO EXPORTADO | | | | | | |")
            continue
        d = json.load(open(e))
        qa = json.load(open(q)) if os.path.exists(q) else {}
        res = "1080×1920" if fmt == "vertical" else "1920×1080"
        b = qa.get("black_intervals")
        bl = "—" if b is None else ("ninguno" if not b else ", ".join(f"{float(x):.2f}–{float(y):.2f}" for x, y in b))
        rows.append(f"| {p['id']} | {fmt} | {mmss(d['segment_src_s'][0])}–{mmss(d['segment_src_s'][1])} | "
                    f"{d['duration_s']:.2f} s | {res} @ {num / den:.3f} | {d['source_segment']['I_LUFS']} / "
                    f"{d['source_segment']['TP_dBTP']} | {d['gain_dB']:+.2f} dB | {d['delivered']['I_LUFS']} / "
                    f"{d['delivered']['TP_dBTP']} | {bl} |")
table = "\n".join(["| Pieza | Formato | Tramo de la fuente | Duración | Resolución / FPS | Fuente LUFS / dBTP | "
                   "Ganancia | Entregado LUFS / dBTP | Negros detectados |", "|---|---|---|---|---|---|---|---|---|"] + rows)
os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
open(os.path.join(ROOT, "export", "tabla_mediciones.md"), "w", encoding="utf-8").write(table + "\n")
print(table)
