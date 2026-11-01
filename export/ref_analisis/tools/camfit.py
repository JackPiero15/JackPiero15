import sys,subprocess,numpy as np
from PIL import Image
from numpy.lib.stride_tricks import sliding_window_view as swv
f=sys.argv[1]; tref=float(sys.argv[2]); times=[float(x) for x in sys.argv[3].split(',')]
W,H=576,712; D=6; w,h=W//D,H//D
def grab(t):
    p=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',f,'-frames:v','1','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
    return Image.frombytes('L',(W,H),p.stdout)
def norm(x): x=x-x.mean(); return x/(x.std()+1e-6)
R=grab(tref)
# exclude text: blank left text zone by using only right 60%? keep full but text absent early
for t in times:
    fr=np.asarray(grab(t).resize((w,h),Image.BILINEAR),np.float32); fn=norm(fr)
    best=(-9,)
    for s in np.arange(1.0,2.3,0.04):
        Rs=np.asarray(R.resize((int(round(W*s/D)),int(round(H*s/D))),Image.BILINEAR),np.float32)
        if Rs.shape[0]<h or Rs.shape[1]<w: continue
        win=swv(Rs,(h,w))  # (ny,nx,h,w)
        m=win.mean(axis=(2,3),keepdims=True); sd=win.std(axis=(2,3),keepdims=True)+1e-6
        sc=((win-m)/sd*fn).mean(axis=(2,3))
        iy,ix=np.unravel_index(sc.argmax(),sc.shape)
        if sc[iy,ix]>best[0]: best=(sc[iy,ix],s,ix*D/s,iy*D/s)
    c,s,ox,oy=best
    # center of visible region in reference coords
    cx=ox+W/s/2; cy=oy+H/s/2
    print(f"t={t:4.2f} escala={s:.2f} centro_visible=({cx:5.1f},{cy:5.1f}) corr={c:.2f}")
