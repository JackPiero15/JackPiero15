import json, sys, os, subprocess
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import letras, traduccion, tiktok_tramos as T
from build_es import remap
E="/home/user/JackPiero15/export"
PROJ={"holdstill":"proyecto_hold_still","weakest":"proyecto_weakest_feeling","quityou":"proyecto_quit_you","nights":"proyecto_nights_like_this"}
EXTRA_BASE={"nights":[(3.62,66),(8.2,129)]}
for song in sys.argv[1:]:
    d=f"{E}/{PROJ[song]}"; t=T.TT[song]; off=t["off"]
    wav=f"{d}/medios/audio_tiktok.wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"{os.path.dirname(D)}/tt/{song}.mp3","-c:a","pcm_s16le",wav],check=True)
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",wav],capture_output=True,text=True).stdout)
    dur=round(int(dur*30)/30,3)
    old=json.load(open(f"{d}/config.json")); oini=old["audio"]["inicio"]
    ab=sorted([(b["desde"]+oini+t["base_shift"],b["archivo"]) for b in old["base"]]+
              [(a,"medios/%03d.mp4"%c) for a,c in EXTRA_BASE.get(song,[])])
    rel=[(round(a-off,3),f) for a,f in ab]
    keep=[]
    for i,(a,f) in enumerate(rel):
        nxt=rel[i+1][0] if i+1<len(rel) else 1e9
        if nxt<=0 or a>=dur: continue
        keep.append({"archivo":f,"desde":max(0.0,a)})
    if t["frases"] is None:
        fr=[(f["lineas"],f["tiempos"],es,f.get("fin")) for f,es in zip(letras.SONGS[song]["letra"],traduccion.ES[song])]
    else:
        fr=[(x[0],x[1],x[2],x[3] if len(x)>3 else None) for x in t["frases"]]
    en=[];es=[]
    for lin,ts,est,fin in fr:
        if ts[0]<off-0.05 or ts[0]>=off+dur: continue
        r=[round(max(0.0,x-off),3) for x in ts]
        g={"lineas":lin,"tiempos":r}; h={"lineas":est,"tiempos":remap(lin,r,est)}
        if fin is not None: g["fin"]=h["fin"]=round(fin-off,3)
        en.append(g); es.append(h)
    base=dict(old); base.update({"duracion":dur,"base":keep,
        "audio":{"archivo":"medios/audio_tiktok.wav","inicio":0.0,"lufs":-14,"fade_in":0.02,"fade_out":[dur-0.3,0.3]},
        "fundido_negro":[dur-0.5,dur],"texto_fin":round(dur-0.35,3)})
    for name,L in (("config_tiktok.json",en),("config_tiktok_es.json",es)):
        c=dict(base); c["letra"]=L
        json.dump(c,open(f"{d}/{name}","w"),ensure_ascii=False,indent=1)
    print(song,"dur",dur,"frases",len(en),"clips base",len(keep))
