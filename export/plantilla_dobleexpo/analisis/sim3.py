import numpy as np
X=np.load('/tmp/r3/X.npy')
Z=(X-X.mean(1,keepdims=True)); Z/= (np.linalg.norm(Z,axis=1,keepdims=True)+1e-6)
C=Z@Z.T
N=len(X)
for L in (241,242,243):
    v=np.array([C[i,i+L] for i in range(N-L)])
    print(L,'min',v.min().round(3),'mean',v.mean().round(3),'n<0.85:',int((v<0.85).sum()))
v=np.array([C[i,i+242] for i in range(N-242)])
low=[ (i,round(float(v[i]),2)) for i in range(len(v)) if v[i]<0.85]
print(low[:80])
# also mean abs pixel diff i vs i+242
d=np.array([np.abs(X[i]-X[i+242]).mean() for i in range(N-242)])
print('absdiff median',np.median(d).round(2),'p90',np.percentile(d,90).round(2))
