import numpy as np
from PIL import Image
import glob,re
for f in sorted(glob.glob('/tmp/r3/mn_*.png')):
    a=int(re.findall(r'(\d+)',f)[-1])
    m=np.asarray(Image.open(f),dtype=np.float32)>150
    # restrict to central area x 150-620
    m[:, :150]=0; m[:,620:]=0
    rows=m.sum(1)>1
    bands=[];s=None
    for y,v in enumerate(rows):
        if v and s is None: s=y
        if not v and s is not None:
            if y-s>8: bands.append((s,y-1))
            s=None
    info=[]
    for s,e in bands:
        cols=np.nonzero(m[s:e+1].sum(0))[0]
        # words: gaps > 12px
        segs=[];st=cols[0];pv=cols[0]
        for c in cols[1:]:
            if c-pv>12: segs.append((st,pv)); st=c
            pv=c
        segs.append((st,pv))
        info.append(((s,e),segs))
    print(a, [(b, [(x0,x1) for x0,x1 in sg]) for b,sg in info])
