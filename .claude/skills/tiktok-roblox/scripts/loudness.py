"""Shared audio helpers: BS.1770-4 integrated loudness, peaks and decoding with PyAV (no ffmpeg.exe needed)."""
import av
import numpy as np

SR = 48000


def decode(path, start=None, end=None, sr=SR, layout="stereo", stream=0):
    """Decode an audio stream to float32 (channels, n). Optional [start, end) window in seconds."""
    c = av.open(path)
    st = c.streams.audio[stream]
    rs = av.AudioResampler(format="fltp", layout=layout, rate=sr)
    if start:
        c.seek(int(max(start - 1.0, 0) / st.time_base), stream=st)
    out, first_t = [], None
    for fr in c.decode(st):
        if fr.time is None:
            continue
        if first_t is None:
            first_t = fr.time
        for r in rs.resample(fr):
            out.append(r.to_ndarray())
        if end is not None and fr.time > end + 0.5:
            break
    for r in rs.resample(None):
        out.append(r.to_ndarray())
    c.close()
    x = np.concatenate(out, axis=1).astype(np.float32)
    if start is None:
        return x
    i0 = int(round((start - first_t) * sr))
    n = int(round(((end if end is not None else first_t + x.shape[1] / sr) - start) * sr))
    return x[:, i0:i0 + n]


def _biquad(x, b, a):
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    b0, b1, b2 = b
    _, a1, a2 = a
    for i, v in enumerate(x.tolist()):
        o = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, o
        y[i] = o
    return y


def lufs(x):
    """Integrated loudness of float audio (channels, n) at 48 kHz, gated per BS.1770-4."""
    if x.shape[1] < 19200:
        x = np.pad(x, ((0, 0), (0, 19200 - x.shape[1])))
    pre = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
    rlb = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])
    z = []
    for ch in x:
        k = _biquad(_biquad(ch.astype(np.float64), *pre), *rlb)
        n = (len(k) - 19200) // 4800 + 1
        z.append(np.array([np.mean(k[j * 4800:j * 4800 + 19200] ** 2) for j in range(max(n, 0))]))
    blk = np.sum(z, axis=0)
    L = -0.691 + 10 * np.log10(blk + 1e-12)
    g1 = blk[L > -70]
    if not len(g1):
        return -70.0
    rel = -0.691 + 10 * np.log10(g1.mean()) - 10
    g2 = blk[(L > -70) & (L > rel)]
    return round(float(-0.691 + 10 * np.log10(g2.mean())), 1)


def peak_db(x):
    return round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 1)


def gain_for(current_lufs, target_lufs):
    """Linear volume that moves a clip from current to target loudness (use for Blender strip.volume)."""
    return round(10 ** ((target_lufs - current_lufs) / 20), 3)
