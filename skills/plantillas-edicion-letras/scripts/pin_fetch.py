"""Descarga la imagen/GIF/video principal de pins públicos de Pinterest (página normal del pin)."""
import json, re, subprocess, sys, pathlib
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ids = sys.argv[2:]
meta = []
def get(url, dst=None):
    cmd = ["curl", "-sL", "-m", "40", url] + (["-o", str(dst)] if dst else [])
    r = subprocess.run(cmd, capture_output=True); return r.stdout
for pid in ids:
    html = get(f"https://www.pinterest.com/pin/{pid}/").decode("utf-8", "ignore").replace("\\/", "/").replace("\\u002F", "/")
    og = re.search(r'property="og:image"[^>]*|content="([^"]+)"[^>]*property="og:image"', html)
    m = re.search(r'content="(https://i\.pinimg\.com/[^"]+)"[^>]*property="og:image"', html)
    title = (re.search(r'content="([^"]*)"[^>]*property="og:title"', html) or [None, ""])[1]
    rec = {"id": pid, "title": title}
    if m:
        h = re.search(r'/([0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{32})\.', m.group(1)).group(1)
        orig = sorted(set(re.findall(r'https://i\.pinimg\.com/originals/' + h + r'\.(?:gif|jpg|jpeg|png|webp)', html)))
        gif = [u for u in orig if u.endswith(".gif")]
        url = (gif or orig or [m.group(1)])[0]
        ext = url.rsplit(".", 1)[1]
        dst = out / f"{pid}.{ext}"; get(url, dst); rec["image"] = dst.name; rec["image_url"] = url
    vids = sorted(set(re.findall(r'https://v1\.pinimg\.com/videos/[^"\s]+?\.mp4', html)))
    vids = [v for v in vids if "/720p/" in v or "/expMp4/" in v] or vids
    if vids:
        dst = out / f"{pid}.mp4"; get(vids[0], dst); rec["video"] = dst.name; rec["video_url"] = vids[0]
    meta.append(rec); print(json.dumps(rec, ensure_ascii=False)[:220], flush=True)
json.dump(meta, open(out / "pins.json", "w"), ensure_ascii=False, indent=1)
