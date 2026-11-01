"""Copy the video stream untouched and re-encode only the audio through a peak limiter (-1.5 dBFS).

limit_audio.py <in.mp4> <out.mp4>
Use after Blender's render when the mix peaks above -1 dB: TikTok re-encodes and would distort it.
Loudness stays the same (~-14 LUFS); AAC 320 kbps 48 kHz. latency=1 keeps audio in sync with the video.
"""
import av, sys
from fractions import Fraction

src, dst = sys.argv[1], sys.argv[2]
inp = av.open(src)
vin, ain = inp.streams.video[0], inp.streams.audio[0]
out = av.open(dst, "w")
vout = out.add_stream_from_template(vin)
aout = out.add_stream("aac", rate=48000, layout="stereo")
aout.bit_rate = 320000

g = av.filter.Graph()
srcf = g.add_abuffer(format="fltp", sample_rate=48000, layout="stereo", time_base=Fraction(1, 48000))
lim = g.add("alimiter", "limit=0.84:attack=5:release=50:level=disabled:latency=1")
fmt = g.add("aformat", "sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo")
sink = g.add("abuffersink")
srcf.link_to(lim); lim.link_to(fmt); fmt.link_to(sink)
g.configure()
rs = av.AudioResampler(format="fltp", layout="stereo", rate=48000)
pts = 0


def drain():
    while True:
        try:
            f = g.pull()
        except (av.BlockingIOError, av.EOFError):
            return
        f.pts = None
        for p in aout.encode(f):
            out.mux(p)


for pkt in inp.demux(vin, ain):
    if pkt.dts is None:
        continue
    if pkt.stream is vin:
        pkt.stream = vout
        out.mux(pkt)
    else:
        for fr in pkt.decode():
            for r in rs.resample(fr):
                r.pts, r.time_base = pts, Fraction(1, 48000)
                pts += r.samples
                g.push(r)
                drain()
g.push(None)
drain()
for p in aout.encode(None):
    out.mux(p)
out.close(); inp.close()
print("ok", dst)
