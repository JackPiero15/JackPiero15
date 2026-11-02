import json, urllib.parse, subprocess, sys, os, concurrent.futures as cf
def search(q, n=25):
    data={"options":{"query":q,"scope":"videos","page_size":n},"context":{}}
    url="https://www.pinterest.com/resource/BaseSearchResource/get/?source_url="+urllib.parse.quote("/search/videos/?q="+q)+"&data="+urllib.parse.quote(json.dumps(data))
    r=subprocess.run(["curl","-sS","--max-time","40","-H","X-Requested-With: XMLHttpRequest","-H","Accept: application/json","-H","X-Pinterest-PWS-Handler: www/search/[scope].js","-A","Mozilla/5.0",url],capture_output=True,text=True)
    try: res=json.loads(r.stdout)['resource_response']['data']['results']
    except Exception as e: print('ERR',q,e,r.stdout[:200]); return []
    out=[]
    for p in res:
        v=(p.get('videos') or {}).get('video_list') or {}
        best=None
        for k,x in v.items():
            if x.get('url','').endswith('.m3u8') and 'MOBILE' not in k: best=x
        if not best:
            for k,x in v.items():
                if x.get('url'): best=x
        if best: out.append({"id":p.get('id'),"q":q,"title":(p.get('title') or p.get('grid_title') or '')[:80],"w":best.get('width'),"h":best.get('height'),"dur":(best.get('duration') or 0)/1000,"url":best['url'],"link":"https://www.pinterest.com/pin/%s/"%p.get('id')})
    return out
def dl(item, dest, maxdur=20):
    import hashlib; fn=os.path.join(dest, hashlib.md5(item['url'].encode()).hexdigest()[:12]+'.mp4')
    if os.path.exists(fn): return fn
    r=subprocess.run(["ffmpeg","-v","error","-y","-i",item['url'],"-t",str(maxdur),"-map","0:v:0","-an","-c","copy",fn],capture_output=True,text=True)
    if r.returncode!=0 or not os.path.exists(fn) or os.path.getsize(fn)<20000:
        return None
    return fn
if __name__=="__main__":
    song=sys.argv[1]; qs=sys.argv[2:]
    dest=f"/tmp/claude-0/-home-user-JackPiero15/9bffa62e-5019-5d29-a4f4-888a3e773a89/scratchpad/pin/{song}"; os.makedirs(dest,exist_ok=True)
    items=[]; seen=set()
    for q in qs:
        for it in search(q):
            if it['id'] in seen: continue
            if it['dur']<3: continue
            seen.add(it['id']); items.append(it)
    print(song,'candidatos',len(items))
    with cf.ThreadPoolExecutor(6) as ex:
        res=list(ex.map(lambda it: (it, dl(it,dest)), items))
    ok=[]
    for it,fn in res:
        if fn: it['file']=fn; ok.append(it)
    json.dump(ok,open(f"{dest}/index.json","w"),ensure_ascii=False,indent=1)
    print(song,'descargados',len(ok))
