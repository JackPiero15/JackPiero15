import sys,subprocess,numpy as np
f=sys.argv[1];W,H=576,712
p=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf','fps=10','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W).astype(np.float32)
txt=a[:,140:360,20:200]; bg_sky=a[:,10:120,350:560]; bg_sea=a[:,250:420,380:560]
full=a.mean(axis=(1,2))
for i in range(0,len(a),5):
    d_sky=np.abs(a[i,10:120,350:560]-a[max(i-1,0),10:120,350:560]).mean()
    d_sea=np.abs(a[i,250:420,380:560]-a[max(i-1,0),250:420,380:560]).mean()
    print(f"t={i/10:5.1f} full={full[i]:5.1f} txtmax={np.percentile(txt[i],99.5):5.0f} dSky={d_sky:4.2f} dSea={d_sea:4.2f}")
