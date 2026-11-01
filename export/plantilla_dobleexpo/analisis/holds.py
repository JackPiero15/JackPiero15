import numpy as np
X=np.load('/tmp/r3/X.npy')
# mask out central text region to reduce text influence: use 48x36 grid; text approx x 13-35, y 8-28 -> keep border ring only? use whole but text minor
Z=(X-X.mean(1,keepdims=True)); Z/= (np.linalg.norm(Z,axis=1,keepdims=True)+1e-6)
c=np.array([1.0]+[float(Z[i]@Z[i-1]) for i in range(1,len(X))])
b=[i for i in range(1,242) if c[i]<0.93]
print('cortes en bucle (cuadro inicial de cada retención):',b)
print('duraciones:',np.diff(b+[242]).tolist())
