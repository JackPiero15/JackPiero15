import numpy as np
X=np.load('/tmp/r3/X.npy')
Z=(X-X.mean(1,keepdims=True)); Z/= (np.linalg.norm(Z,axis=1,keepdims=True)+1e-6)
C=Z@Z.T
res=[]
for L in range(1,400):
    n=min(620-L,600)
    if n<50: break
    res.append((L,float(np.mean([C[i,i+L] for i in range(0,n)]))))
res.sort(key=lambda r:-r[1])
print([ (l,round(v,3)) for l,v in res[:30]])
# period estimate: fit peaks near multiples
for k in range(1,12):
    best=max([r for r in res if abs(r[0]-32.5*k)<=3],key=lambda r:r[1],default=None)
    print(k,best)
