import json,sys,os
from PIL import Image, ImageDraw
S=os.path.dirname(os.path.abspath(__file__)); song=sys.argv[1]
info=json.load(open(f"{S}/{song}/probe.json")); ocr=json.load(open(f"{S}/{song}/ocr.json"))
clean=[int(k) for k,v in ocr.items() if v==[] and min(info[int(k)][1],info[int(k)][2])>=320]
clean.sort(); T=150; C=12
for s in range(0,len(clean),84):
    sh=Image.new("RGB",(C*T,7*(T+14)),"black"); d=ImageDraw.Draw(sh)
    for i,k in enumerate(clean[s:s+84]):
        x=(i%C)*T; y=(i//C)*(T+14)
        try: sh.paste(Image.open(f"{S}/thumbs_{song}_{k:03d}_c.jpg"),(x,y+14))
        except Exception: pass
        d.text((x+2,y+1),f"{k} {info[k][3]:.0f}s",fill="yellow")
    sh.save(f"{S}/clean_{song}_{s//84}.png")
print(song,len(clean))
