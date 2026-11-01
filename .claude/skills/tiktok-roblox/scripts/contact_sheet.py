"""Contact sheet of a video: one labeled thumbnail every STEP seconds.

contact_sheet.py <video> <out.jpg> <step_s> [start_s] [end_s]
Use it to see who is on stage at each candidate moment and where the character sits in the frame.
"""
import av, sys
from PIL import Image, ImageDraw

path, out, step = sys.argv[1], sys.argv[2], float(sys.argv[3])
start = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
end = float(sys.argv[5]) if len(sys.argv) > 5 else None
c = av.open(path)
st = c.streams.video[0]
end = min(end or c.duration / 1e6, c.duration / 1e6)
thumbs, t = [], start
while t < end:
    c.seek(int(t / st.time_base), stream=st, any_frame=False, backward=True)
    for fr in c.decode(st):
        if fr.time is not None and fr.time >= t - 0.05:
            thumbs.append((t, fr.to_image().resize((384, 216))))
            break
    t += step
cols = 6
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 384, rows * 216), "black")
d = ImageDraw.Draw(sheet)
for i, (t, img) in enumerate(thumbs):
    x, y = (i % cols) * 384, (i // cols) * 216
    sheet.paste(img, (x, y))
    m, s = divmod(int(t), 60)
    d.rectangle([x, y, x + 70, y + 22], fill="black")
    d.text((x + 4, y + 4), f"{m:02d}:{s:02d}", fill="yellow")
sheet.save(out, quality=80)
print(out, len(thumbs))
