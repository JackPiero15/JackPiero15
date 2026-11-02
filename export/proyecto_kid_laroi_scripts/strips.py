import sys,os,glob,subprocess
from PIL import Image, ImageDraw
S=os.path.dirname(os.path.abspath(__file__)); song=sys.argv[1]
fs=sorted(glob.glob(f"{S}/{song}_hq/*.mp4")); T=200; C=3
rows=[]
for f in fs:
    du=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout or 1)
    ims=[]
    for t in (0.5,du*0.5,max(0,du-0.6)):
        r=subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",f,"-frames:v","1","-vf",f"scale={T}:{T}:force_original_aspect_ratio=decrease,pad={T}:{T}:(ow-iw)/2:(oh-ih)/2","-f","image2pipe","-vcodec","png","-"],capture_output=True)
        import io; ims.append(Image.open(io.BytesIO(r.stdout)) if r.stdout else Image.new("RGB",(T,T)))
    rows.append((os.path.basename(f),ims))
per=4; n=(len(rows)+per-1)//per
for p in range(0,len(rows),20):
    chunk=rows[p:p+20]; R=(len(chunk)+per-1)//per
    sh=Image.new("RGB",(per*(3*T+8),R*(T+16)),"black"); d=ImageDraw.Draw(sh)
    for i,(name,ims) in enumerate(chunk):
        x=(i%per)*(3*T+8); y=(i//per)*(T+16); d.text((x+2,y+2),name,fill="yellow")
        for j,im in enumerate(ims): sh.paste(im,(x+j*T,y+16))
    sh.save(f"{S}/strip_{song}_{p//20}.png")
print(len(rows))
