import numpy as np, wave, sys
sr=16000; hop=320; win=2048
def load(p):
    w=wave.open(p); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
def chroma(a):
    n=(len(a)-win)//hop
    idx=np.arange(win)[None,:]+hop*np.arange(n)[:,None]
    S=np.abs(np.fft.rfft(a[idx]*np.hanning(win),axis=1))
    f=np.fft.rfftfreq(win,1/sr); m=(f>80)&(f<4000); S=S[:,m]; f=f[m]
    pc=(np.round(12*np.log2(f/440))%12).astype(int)
    C=np.stack([S[:,pc==k].sum(1) for k in range(12)],1)
    C=np.log1p(C); C-=C.mean(1,keepdims=True); C/=np.linalg.norm(C,axis=1,keepdims=True)+1e-9
    return C
def best_off(CA,CB):
    L=len(CA)
    # vectorized sliding dot via FFT per pitch class
    n=len(CB)+L; N=1<<int(np.ceil(np.log2(n)))
    acc=np.zeros(N)
    for k in range(12):
        acc+=np.fft.irfft(np.fft.rfft(CB[:,k],N)*np.conj(np.fft.rfft(CA[:,k],N)),N)
    acc=acc[:len(CB)-L]/L
    j=int(np.argmax(acc)); return acc[j],j
k=sys.argv[1]
A=load(f'{k}.wav'); B=load(f'../kid/{k}.wav'); CB=chroma(B)
res=[]
for rate in [1.0,1.03,1.05,1.07,1.1,1.12,1.15,1.18,1.2,1.25,1.3,0.95,0.9,0.85,0.8]:
    n=int(len(A)*rate); x=np.interp(np.arange(n)/rate,np.arange(len(A)),A)
    seg=x[int(2*sr):int(18*sr)]
    CA=chroma(seg)
    for sh in sorted({0,int(round(12*np.log2(rate)))}):
        c,j=best_off(np.roll(CA,sh,axis=1),CB)
        res.append((round(float(c),3),rate,sh,round(j*hop/sr-2*1.0,2)))
res.sort(reverse=True); print(k,res[:4])
