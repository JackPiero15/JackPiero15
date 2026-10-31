"""Descarga las imágenes (736x) que aparecen en la página pública de un tablero de Pinterest."""
import re, subprocess, sys, pathlib
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
limit = int(sys.argv[2])
for url in sys.argv[3:]:
    html = subprocess.run(["curl", "-sL", "-m", "40", url], capture_output=True).stdout.decode("utf-8", "ignore").replace("\\/", "/")
    hs = []
    for h in re.findall(r'i\.pinimg\.com/(?:236x|474x|736x)/([0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{32})\.(jpg|png|gif)', html):
        if h not in hs: hs.append(h)
    name = url.rstrip("/").split("/")[-1]
    print(url, len(hs), flush=True)
    for k, (h, ext) in enumerate(hs[:limit]):
        dst = out / f"{name}_{k:02d}.{ext}"
        subprocess.run(["curl", "-sL", "-m", "40", "-o", str(dst), f"https://i.pinimg.com/736x/{h}.{ext}"])
