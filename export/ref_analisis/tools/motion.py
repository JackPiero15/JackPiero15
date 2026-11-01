import sys,subprocess,numpy as np
f=sys.argv[1];W,H=576,712
regs={k:[int(v) for v in s.split(',')] for k,s in (r.split('=') for r in sys.argv[2:])}
p=subprocess.run(['ffmpeg','-v','error','-ss','4','-i',f,'-t','20','-vf','fps=30','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W).astype(np.float32)
for k,(y0,y1,x0,x1) in regs.items():
    r=a[:,y0:y1,x0:x1]; d=np.abs(np.diff(r,axis=0)).mean(axis=(1,2))
    drift=np.abs(r[-1]-r[0]).mean()
    print(f"{k}: diff medio/frame={d.mean():.2f} p95={np.percentile(d,95):.2f} | diferencia t4 vs t24={drift:.2f}")
