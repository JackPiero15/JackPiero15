"""Índice + hoja de contacto numerada de las imágenes del proyecto (para elegir qué imagen va en cada línea "hold").

Ejecutar desde la raíz del proyecto:
    python tools/make_sheet.py media/rel [media/otra ...]
Salida: work/sheet_index.txt ("<idx> <ruta>") y work/sheet_XX.jpg (60 miniaturas por hoja).
El idx es el número que se pone en "img" de cada línea de lineas.json.
"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageOps

EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
files = sorted(p for d in sys.argv[1:] for p in pathlib.Path(d).rglob("*") if p.suffix.lower() in EXT)
pathlib.Path("work").mkdir(exist_ok=True)
with open("work/sheet_index.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(files): f.write(f"{i} {p.as_posix()}\n")
TW, TH, COLS, PER = 180, 320, 10, 60
for s in range(0, len(files), PER):
    part = files[s:s + PER]
    sheet = Image.new("RGB", (COLS * TW, ((len(part) + COLS - 1) // COLS) * TH), "black")
    d = ImageDraw.Draw(sheet)
    for k, p in enumerate(part):
        try:
            im = ImageOps.fit(Image.open(p).convert("RGB"), (TW, TH))
        except Exception:
            continue
        x, y = (k % COLS) * TW, (k // COLS) * TH
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 44, y + 22], fill="black"); d.text((x + 4, y + 4), str(s + k), fill="yellow")
    sheet.save(f"work/sheet_{s // PER:02d}.jpg", quality=85)
print(len(files), "imágenes indexadas")
