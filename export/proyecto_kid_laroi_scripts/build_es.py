import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import traduccion
E="/home/user/JackPiero15/export"
PROJ={"holdstill":"proyecto_hold_still","weakest":"proyecto_weakest_feeling","quityou":"proyecto_quit_you","nights":"proyecto_nights_like_this"}
def tokens(s): return [w for l in s.split("\n") for w in l.split()]
def remap(en_txt, en_t, es_txt):
    en=tokens(en_txt); es=tokens(es_txt)
    # posición de cada palabra inglesa en fracción de caracteres
    L=[len(w)+1 for w in en]; c=np.concatenate([[0],np.cumsum(L)])/sum(L)
    t=list(en_t)+[en_t[-1]+max(0.35,(en_t[-1]-en_t[0])/max(1,len(en_t)-1))]
    Ls=[len(w)+1 for w in es]; cs=np.concatenate([[0],np.cumsum(Ls)])[:-1]/sum(Ls)
    out=[float(np.interp(f,c,t)) for f in cs]
    for i in range(1,len(out)): out[i]=max(out[i],out[i-1]+0.07)
    return [round(x,3) for x in out]
for song in sys.argv[1:]:
    d=f"{E}/{PROJ[song]}"; cfg=json.load(open(f"{d}/config.json"))
    tr=traduccion.ES[song]; assert len(tr)==len(cfg["letra"])
    new=[]
    for f,es in zip(cfg["letra"],tr):
        g={"lineas":es,"tiempos":remap(f["lineas"],f["tiempos"],es)}
        if "fin" in f: g["fin"]=f["fin"]
        new.append(g)
    cfg["letra"]=new
    json.dump(cfg,open(f"{d}/config_es.json","w"),ensure_ascii=False,indent=1)
    print(song,"ok")
