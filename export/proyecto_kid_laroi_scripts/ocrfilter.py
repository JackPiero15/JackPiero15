import sys, json, subprocess, os, numpy as np
from multiprocessing import Pool
from PIL import Image
import io
S=os.path.dirname(os.path.abspath(__file__))
def frames(f, du):
    ts=[0.3, du*0.25, du*0.5, du*0.75, max(0,du-1.2), max(0,du-0.4)]
    out=[]
    for t in ts:
        r=subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f,"-frames:v","1","-vf","scale=480:-2","-f","image2pipe","-vcodec","png","-"],capture_output=True)
        if r.stdout: out.append(np.asarray(Image.open(io.BytesIO(r.stdout)).convert("RGB")))
    return out
eng=None
def work(item):
    global eng
    if eng is None:
        from rapidocr_onnxruntime import RapidOCR; eng=RapidOCR()
    k,(f,w,h,du)=item
    if not os.path.exists(f): return k,None
    texts=[]
    for im in frames(f,du):
        res,_=eng(im)
        for box,txt,conf in (res or []):
            if float(conf)>0.6 and len(txt.strip())>=2: texts.append(txt.strip())
    return k,texts
if __name__=="__main__":
    song=sys.argv[1]
    info=json.load(open(f"{S}/{song}/probe.json"))
    with Pool(4) as p: res=dict(p.map(work, list(enumerate(info))))
    json.dump(res,open(f"{S}/{song}/ocr.json","w"),ensure_ascii=False,indent=0)
    clean=[k for k,v in res.items() if v==[]]
    print(song,"limpios",len(clean),"de",len(info))
