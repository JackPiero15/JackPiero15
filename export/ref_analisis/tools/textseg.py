import sys,subprocess,numpy as np
f=sys.argv[1];W,H=576,712;y0,y1,x0,x1=[int(v) for v in sys.argv[2].split(',')]
p=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf','fps=20','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W)[:,y0:y1,x0:x1].astype(np.int16)
cnt=(a>200).sum(axis=(1,2))
prev=None
for i in range(len(a)):
    b=(a[i]>200)
    if prev is not None:
        ch=(b^prev).sum()
    else: ch=0
    prev=b
    if i%2==0 or ch>200: print(f"{i/20:6.2f} bright={cnt[i]:5d} change={ch:5d}")
