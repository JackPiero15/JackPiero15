import numpy as np, glob
from PIL import Image
fs=sorted(glob.glob('/tmp/r3/f/*.png'))[:615]
P=[];S=[];acc=np.zeros((576,768));sat=[]
for f in fs[::3]:
    a=np.asarray(Image.open(f).convert('RGB'),dtype=np.float32)
    L=a.mean(2); acc+=L
    P.append(np.percentile(L,[1,5,25,50,75,95,99]))
    sat.append(np.abs(a-L[...,None]).mean())
P=np.array(P); print('percentiles luminancia (media sobre cuadros) p1,5,25,50,75,95,99:',P.mean(0).round(1))
print('mediana por cuadro: min %.0f max %.0f'%(P[:,3].min(),P[:,3].max()))
print('saturacion media |RGB-L|:',np.mean(sat).round(2))
acc/=len(fs[::3])
yy,xx=np.mgrid[0:576,0:768]; r=np.hypot((xx-384)/384,(yy-288)/288)
for r0 in (0.0,0.3,0.6,0.9,1.1,1.3):
    m=(r>=r0)&(r<r0+0.15); print('radio %.1f lum media %.1f'%(r0,acc[m].mean()))
print('bordes: col0 %.1f col767 %.1f fila0 %.1f fila575 %.1f'%(acc[:,0].mean(),acc[:,767].mean(),acc[0].mean(),acc[575].mean()))
print('cols 760-767:',acc[:,760:768].mean(0).round(1))
# full histogram average (64 bins) to store
H=np.zeros(256)
for f in fs[::3]:
    L=np.asarray(Image.open(f).convert('L')); H+=np.bincount(L.ravel(),minlength=256)
H/=H.sum(); np.save('/tmp/r3/ref_hist.npy',H)
cdf=np.cumsum(H); print('cdf quantiles of ref (value at 10..90%):',[int(np.searchsorted(cdf,q)) for q in np.linspace(0.1,0.9,9)])
