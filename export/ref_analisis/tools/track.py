import sys,subprocess,numpy as np
f=sys.argv[1];W,H=576,712;y0,y1,x0,x1=[int(v) for v in sys.argv[2].split(',')];thr=int(sys.argv[3]); fps=10
p=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'fps={fps}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W)
for i in range(0,len(a),3):
    m=a[i,y0:y1,x0:x1]>thr
    if m.sum()<50: print(f"{i/fps:5.1f} -"); continue
    ys,xs=np.nonzero(m)
    print(f"{i/fps:5.1f} top={ys.min()+y0:4d} left={xs.min()+x0:4d} cy={ys.mean()+y0:6.1f} cx={xs.mean()+x0:6.1f}")
