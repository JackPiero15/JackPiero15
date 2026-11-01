import sys, os
from rembg import remove, new_session
from PIL import Image
s = new_session(sys.argv[1])
for f in sys.argv[3:]:
    im = Image.open(f).convert("RGB")
    out = remove(im, session=s, post_process_mask=True)
    dst = os.path.join(sys.argv[2], os.path.splitext(os.path.basename(f))[0] + f"_{sys.argv[1]}.png")
    out.save(dst); print("ok", dst, flush=True)
