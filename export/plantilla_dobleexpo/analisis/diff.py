import numpy as np, glob
from PIL import Image
fs=sorted(glob.glob('/tmp/r3/f/*.png'))
prev=None; out=[]
for i,f in enumerate(fs):
    a=np.asarray(Image.open(f).convert('RGB'),dtype=np.float32)
    lum=a.mean()
    d=0 if prev is None else np.abs(a-prev).mean()
    out.append((i,i/30,lum,d,a[...,0].mean(),a[...,1].mean(),a[...,2].mean()))
    prev=a
import csv
with open('/tmp/r3/frames.csv','w') as fh:
    w=csv.writer(fh); w.writerow(['idx','t','lum','diff','r','g','b']); w.writerows(out)
ds=np.array([o[3] for o in out])
med=np.median(ds)
print('median diff',med)
for o in out:
    if o[3]>max(4*med,8): print('%4d %6.3f lum=%6.1f diff=%6.1f'%o[:4])
