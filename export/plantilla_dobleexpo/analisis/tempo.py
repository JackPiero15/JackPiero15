# Requiere: ffmpeg -i REFERENCIA.mp4 -ac 1 -ar 22050 -f f32le /tmp/r3/a.raw
import numpy as np
a=np.fromfile('/tmp/r3/a.raw',dtype=np.float32); sr=22050
hop=512; win=2048
n=(len(a)-win)//hop
spec=np.abs(np.stack([np.fft.rfft(a[i*hop:i*hop+win]*np.hanning(win)) for i in range(n)]))
logs=np.log1p(1000*spec)
flux=np.maximum(0,np.diff(logs,axis=0)).sum(1)
flux=np.concatenate([[0],flux]); fr=sr/hop
o=flux-np.convolve(flux,np.ones(16)/16,'same'); o=np.maximum(o,0)
ac=np.correlate(o,o,'full')[len(o)-1:]
lags=np.arange(len(ac))/fr
bpm=60/lags[1:]
cand=[(60/lags[l],ac[l]) for l in range(1,len(ac)) if 60<=60/lags[l]<=200]
cand.sort(key=lambda c:-c[1]); print('tempo cands',[(round(b,1),round(float(v),1)) for b,v in cand[:12]])
rms=np.sqrt(np.convolve(a**2,np.ones(2205)/2205,'same'))[::2205]
print('RMS dB per 0.1s first 2s:',np.round(20*np.log10(rms[:20]+1e-9),1))
print('RMS dB last 4s:',np.round(20*np.log10(rms[-40:]+1e-9),1))
# onset peaks times
from numpy.lib.stride_tricks import sliding_window_view
pk=[i for i in range(2,len(o)-2) if o[i]==max(o[i-2:i+3]) and o[i]>np.percentile(o,93)]
print('strong onsets (s):',[round(i/fr,2) for i in pk])
np.save('/tmp/r3/onset.npy',o)
