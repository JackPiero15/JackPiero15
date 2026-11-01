import numpy as np
from PIL import Image
# state boundaries (first frame where new word visible clean) - visual estimate, refine later
states=[('touch',62,77),('touch my',79,93),('tough my neck',96,119),('and',122,127),("and I'll",130,138),("and I'll touch",141,152),("and I'll touch yours",155,189),
('you',193,199),('you in',201,208),('you in those',211,223),('you in those little',228,239),('you in those little high',242,255),('was',258,270),('wasted',273,285),('wasted shorts',289,315),('wasted shorts oh',319,359),
('she',362,368),('she knows',371,378),('she knows what',381,387),('she knows what i',391,391),('she knows what i think',391,397),('she knows what i think about',400,437),
('and',440,445),('and what',447,449),('and what i think',455,461),('and what i think about',466,487),('one',491,497),('one love',500,520),('one love two',523,530),('one love two mouths',533,555),
('one',558,565),('one love',568,585),('one love one',588,591),('one love one house',595,620)]
L=lambda i: np.asarray(Image.open('/tmp/r3/f/%04d.png'%(i+1)).convert('L'),dtype=np.float32)
out=[]
for name,a,b in states:
    st=np.stack([L(i) for i in range(a,b+1)])
    mn=np.percentile(st,10,axis=0)
    m=mn>150
    ys,xs=np.nonzero(m)
    if len(xs)==0: print(name,'none'); continue
    # restrict to central region to avoid bright bg
    rows=np.nonzero(m.sum(1)>2)[0]; cols=np.nonzero(m.sum(0)>2)[0]
    print('%-30s fr %3d-%3d  x %3d-%3d  y %3d-%3d  (w %3d h %3d) ctr %.0f,%.0f  textlum %.0f'%(name,a,b,cols.min(),cols.max(),rows.min(),rows.max(),cols.max()-cols.min(),rows.max()-rows.min(),(cols.min()+cols.max())/2,(rows.min()+rows.max())/2, np.median(st.mean(0)[m])))
    Image.fromarray(np.uint8(np.clip(mn,0,255))).save('/tmp/r3/mn_%03d.png'%a)
