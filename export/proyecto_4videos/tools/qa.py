import json, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
F="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for cfgp in sorted(os.listdir("configs")):
    if not cfgp.endswith(".json"): continue
    n=cfgp[:-5]; c=json.load(open("configs/"+cfgp,encoding="utf-8")); mp4=f"render/{n}.mp4"
    pr=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate","-of","compact",mp4],capture_output=True,text=True).stdout.strip().replace("\n"," | ")
    lo=subprocess.run(["ffmpeg","-hide_banner","-i",mp4,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    I=[l for l in lo.split("\n") if l.strip().startswith(("I:","Peak:"))]
    bd=subprocess.run(["ffmpeg","-hide_banner","-i",mp4,"-vf","blackdetect=d=0.3:pix_th=0.08","-an","-f","null","-"],capture_output=True,text=True).stderr
    blacks=[l.split("]")[1].strip() for l in bd.split("\n") if "black_start" in l]
    print(f"== {n}\n  {pr}\n  loudness: {' '.join(x.strip() for x in I)}\n  negros: {blacks}")
    ts=[e["start"]+0.6 for e in c["lyrics"]]+[c["duration"]-1.2]
    tiles=[]
    for t in ts:
        png=subprocess.run(["ffmpeg","-v","error","-ss",f"{t:.2f}","-i",mp4,"-frames:v","1","-vf","scale=216:384","-f","image2pipe","-vcodec","png","-"],capture_output=True).stdout
        im=Image.open(__import__("io").BytesIO(png)).convert("RGB"); d=ImageDraw.Draw(im)
        d.rectangle((0,364,70,384),fill=(0,0,0)); d.text((3,366),f"{t:.1f}s",font=ImageFont.truetype(F,14),fill=(255,255,0))
        tiles.append(im)
    cols=8; rows=(len(tiles)+cols-1)//cols
    sh=Image.new("RGB",(cols*220,rows*388))
    for i,im in enumerate(tiles): sh.paste(im,((i%cols)*220,(i//cols)*388))
    sh.save(f"work/qa_{n}.png")
