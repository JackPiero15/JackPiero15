import json, sys, os, hashlib, subprocess, re, urllib.parse
sys.path.insert(0,'/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin'); import pin
song=sys.argv[1]; sel=[int(x) for x in sys.argv[2].split(',')]; qs=sys.argv[3:]
d=f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/{song}"; info=json.load(open(f"{d}/probe.json"))
mp={}
idxf=f"{d}/index.json"
if os.path.exists(idxf):
    for it in json.load(open(idxf)): mp[hashlib.md5(it['url'].encode()).hexdigest()[:12]]=it
for q in qs:
    for it in pin.search(q): mp.setdefault(hashlib.md5(it['url'].encode()).hexdigest()[:12],it)
out=f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/{song}_hq"; os.makedirs(out,exist_ok=True)
res=json.load(open(f"{out}/sel.json")) if os.path.exists(f"{out}/sel.json") else {}
res={int(k):v for k,v in res.items()}
for k in sel:
    f=info[k][0]; h=os.path.basename(f)[:12]; it=mp.get(h)
    if not it: print(k,'sin URL'); continue
    m=subprocess.run(["curl","-s","--max-time","20",it['url']],capture_output=True,text=True).stdout
    best=None;bb=-1
    lines=m.splitlines()
    for i,l in enumerate(lines):
        if l.startswith('#EXT-X-STREAM-INF'):
            bw=int(re.search(r'BANDWIDTH=(\d+)',l).group(1))
            if bw>bb: bb=bw; best=urllib.parse.urljoin(it['url'],lines[i+1].strip())
    src=best or it['url']
    fn=f"{out}/{k:03d}.mp4"
    if not os.path.exists(fn): r=subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-t","25","-map","0:v:0","-an","-c","copy",fn],capture_output=True,text=True)
    p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height:format=duration","-of","csv=p=0",fn],capture_output=True,text=True).stdout.split()
    res[k]={"file":fn,"pin":it['link'],"titulo":it['title'],"busqueda":it['q'],"probe":p}
    print(k,p,it['link'])
json.dump(res,open(f"{out}/sel.json","w"),ensure_ascii=False,indent=1)
