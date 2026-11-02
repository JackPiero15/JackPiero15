import json, os, sys, shutil, subprocess
sys.path.insert(0, os.path.dirname(__file__)); import letras
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E="/home/user/JackPiero15/export"
PLAN={
"holdstill":{"proj":"proyecto_hold_still","look":{"color":True,"saturacion":0.9,"tono_ref":0.6},
 "base":[(55.6,155),(59.0,228),(62.3,166),(65.8,204),(70.6,174),(73.6,57),(76.7,212),(78.1,161),(83.0,149),(86.0,127),(89.0,97),
         (91.5,181),(95.0,240),(98.5,183),(101.8,146),(106.0,110),(110.0,207),(112.3,235),(114.2,260)],
 "fl":[35,105,171,192,222,32,18,202,62,115,105,171]},
"weakest":{"proj":"proyecto_weakest_feeling","look":{"color":True,"saturacion":0.85,"tono_ref":0.6},
 "base":[(10.6,50),(14.3,172),(17.4,42),(20.2,246),(22.7,142),(25.3,219),(28.2,52),(31.1,182),(34.6,67),(37.5,2),(39.8,156),
         (41.5,190),(43.0,154),(45.5,46),(49.4,141),(51.3,224),(53.7,191),(57.5,181),(60.3,169),(62.9,206),(65.6,62)],
 "fl":[10,45,74,84,96,123,136,165,177,179,212,267]},
"quityou":{"proj":"proyecto_quit_you","look":{"color":True,"saturacion":1.0,"tinte":[1.04,0.98,0.9],"tono_ref":0.6},
 "base":[(34.9,25),(40.8,26),(42.0,98),(46.0,252),(49.8,147),(52.8,211),(55.6,188),(59.5,64),(62.9,256),(66.6,40),(68.6,189),
         (71.4,124),(72.9,262),(74.9,161),(76.6,164),(78.1,185),(81.5,175),(85.3,197),(88.5,101),(92.3,237)],
 "fl":[5,42,91,27,46,35,209,137,191,154,236,40]},
"nights":{"proj":"proyecto_nights_like_this","look":{"color":True,"saturacion":1.0,"tono_ref":0.55},
 "base":[(12.8,131),(13.8,108),(17.4,146),(21.2,61),(24.3,151),(26.8,284),(29.9,275),(34.4,87),(37.0,282),(38.6,197),(40.0,181),
         (43.6,267),(46.8,148),(49.5,243),(55.0,129),(58.7,279)],
 "fl":[4,66,108,267,129,279,284,197,151,61,131,282]},
}
def build(song):
    p=PLAN[song]; s=letras.SONGS[song]; ini=s["inicio"]; dur=s["dur"]
    d=f"{E}/{p['proj']}"; os.makedirs(f"{d}/medios",exist_ok=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"{S}/kid/{song}.mp3","-c:a","pcm_s16le",f"{d}/medios/cancion.wav"],check=True)
    used=sorted({c for _,c in p["base"]}|set(p["fl"]))
    for c in used: shutil.copy(f"{S}/pin/{song}_hq/{c:03d}.mp4",f"{d}/medios/{c:03d}.mp4")
    base=[{"archivo":f"medios/{c:03d}.mp4","desde":round(t-ini,3)} for t,c in p["base"]]
    fl=[{"archivo":f"medios/{c:03d}.mp4","duracion":3.0} for c in p["fl"]]
    letra=[]
    for f in s["letra"]:
        g={"lineas":f["lineas"],"tiempos":[round(x-ini,3) for x in f["tiempos"]]}
        if "fin" in f: g["fin"]=round(f["fin"]-ini,3)
        letra.append(g)
    cfg={"duracion":dur,"salida":{"ancho":1440,"alto":1080,"fps":30,"lienzo":"4:3","crf":18},"bucle":None,
         "audio":{"archivo":"medios/cancion.wav","inicio":ini,"lufs":-14,"fade_in":0.4,"fade_out":[dur-0.8,0.8]},
         "fundido_negro":[dur-0.6,dur],"base":base,"destellos":fl,"look":p["look"],"letra":letra,
         "texto_fin":round(dur-0.5,3)}
    json.dump(cfg,open(f"{d}/config.json","w"),ensure_ascii=False,indent=1)
    sel=json.load(open(f"{S}/pin/{song}_hq/sel.json"))
    src=[{"archivo":f"medios/{c:03d}.mp4","pinterest":sel[str(c)]["pin"],"busqueda":sel[str(c)]["busqueda"],
          "resolucion":sel[str(c)]["probe"][0]} for c in used]
    json.dump({"nota":"Videos de terceros obtenidos de Pinterest; no incluidos en el repositorio. Filtrados: sin texto/marcas (OCR) y revisados a mano (sin IA).","clips":src},
              open(f"{d}/fuentes.json","w"),ensure_ascii=False,indent=1)
    print(song,"ok",d)
for s in sys.argv[1:]: build(s)
