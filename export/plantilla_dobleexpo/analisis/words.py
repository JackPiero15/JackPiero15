import numpy as np
from PIL import Image
N=674
L=lambda i: np.asarray(Image.open('/tmp/r3/f/%04d.png'%(i+1)).convert('L'),dtype=np.int16)[100:480,150:620]
cnt=[];masks=[]
for i in range(N-50):
    F=L(i); ds=[]
    for j in (i-242,i+242,i-484,i+484):
        if 0<=j<N-50: ds.append(F-L(j))
    d=np.max(np.stack(ds),0)
    m=(F>195)&(d>45)
    masks.append(np.packbits(m)); cnt.append(int(m.sum()))
np.save('/tmp/r3/tmask.npy',np.array(masks))
cnt=np.array(cnt)
prev=None
M=[np.unpackbits(x)[:380*470].reshape(380,470).astype(bool) for x in masks]
for i in range(1,len(M)):
    inter=(M[i]&M[i-1]).sum(); uni=(M[i]|M[i-1]).sum()+1
    iou=inter/uni
    if iou<0.6: print('%3d %.2fs  px=%5d  IoU_prev=%.2f'%(i,i/30,cnt[i],iou))
