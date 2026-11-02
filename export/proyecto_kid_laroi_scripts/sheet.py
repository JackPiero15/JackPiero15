import sys, os, glob, json, subprocess
from PIL import Image, ImageDraw
MODE="_c" if len(sys.argv)>2 else ""
song=sys.argv[1]; d=f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/{song}"
fs=sorted(glob.glob(f"{d}/*.mp4"))
info=[]
for f in fs:
    p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height:format=duration","-of","json",f],capture_output=True,text=True)
    try:
        j=json.loads(p.stdout); w=j['streams'][0]['width']; h=j['streams'][0]['height']; du=float(j['format']['duration'])
    except Exception: continue
    info.append((f,w,h,du))
json.dump(info,open(f"{d}/probe.json","w"))
T=150; C=12
ims=[]
for k,(f,w,h,du) in enumerate(info):
    out=f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/thumbs_{song}_{k:03d}{MODE}.jpg"
    if not os.path.exists(out):
        subprocess.run(["ffmpeg","-v","error","-y","-ss",str(du*0.4),"-i",f,"-frames:v","1","-vf",f"scale={T}:{T}:force_original_aspect_ratio=decrease,pad={T}:{T}:(ow-iw)/2:(oh-ih)/2"+("" if MODE else ",format=gray"),out])
    ims.append((k,out,w,h,du))
for s in range(0,len(ims),84):
    sh=Image.new("RGB",(C*T,7*(T+14)),"black"); dr=ImageDraw.Draw(sh)
    for i,(k,out,w,h,du) in enumerate(ims[s:s+84]):
        x=(i%C)*T; y=(i//C)*(T+14)
        try: sh.paste(Image.open(out),(x,y+14))
        except Exception: pass
        dr.text((x+2,y+1),f"{k} {min(w,h)}p {du:.0f}s",fill="yellow")
    sh.save(f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/sheet_{song}_{s//84}.png")
print(len(ims))
