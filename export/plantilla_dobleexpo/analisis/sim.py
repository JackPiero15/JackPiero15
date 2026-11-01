import numpy as np, glob
from PIL import Image
fs=sorted(glob.glob('/tmp/r3/f/*.png'))
X=np.stack([np.asarray(Image.open(f).convert('L').resize((48,36)),dtype=np.float32).ravel() for f in fs])
np.save('/tmp/r3/X.npy',X)
Z=(X-X.mean(1,keepdims=True)); Z/= (np.linalg.norm(Z,axis=1,keepdims=True)+1e-6)
C=Z@Z.T
N=len(X)
# lag profile: mean correlation at lag L over frames 0..620
for L in range(20,45):
    v=[C[i,i+L] for i in range(0,600)]
    print(L, round(float(np.mean(v)),3))
