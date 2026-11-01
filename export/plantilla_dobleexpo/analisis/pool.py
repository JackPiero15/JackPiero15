import numpy as np
X=np.load('/tmp/r3/X.npy')
Z=(X-X.mean(1,keepdims=True)); Z/= (np.linalg.norm(Z,axis=1,keepdims=True)+1e-6)
C=Z@Z.T
for ref,name in [(21,'rayas blancas'),(14,'bokeh'),(31,'teatro'),(12,'nubes'),(10,'puerta'),(25,'niebla'),(23,'remolino'),(6,'?6'),(38,'pelo'),(44,'?44'),(48,'gorra')]:
    hits=[i for i in range(242) if C[ref,i]>0.6]
    print('%-14s ref %3d: %s'%(name,ref,hits))
