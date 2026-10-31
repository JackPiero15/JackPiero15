import sys, subprocess, numpy as np, json
f=sys.argv[1]; W,H=72,89
p=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W).astype(np.float32)
pt=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','frame=pts_time','-of','csv=p=0',f],capture_output=True,text=True).stdout.split()
pt=[float(x) for x in pt]
d=np.abs(np.diff(a,axis=0)).mean(axis=(1,2)); luma=a.mean(axis=(1,2))
out=[]
for i in range(1,len(a)):
    out.append((i,pt[i] if i<len(pt) else None,float(d[i-1]),float(luma[i])))
json.dump(out,open(sys.argv[2],'w'))
med=np.median(d)
print(len(a),'frames; median diff',round(float(med),2))
cuts=[o for o in out if o[2]>max(12,6*med)]
print('candidatos de corte:',len(cuts))
for c in cuts: print(f"f{c[0]:5d} t={c[1]:.3f} diff={c[2]:.1f} luma={c[3]:.0f}")
