import glob,sys
from PIL import Image,ImageDraw
fs=sorted(glob.glob('/tmp/r3/f/*.png'))
W,H=192,144; C=10; R=6; N=C*R
for s in range(0,len(fs),N):
    sh=Image.new('RGB',(C*W,R*(H+14)),'black'); d=ImageDraw.Draw(sh)
    for k,f in enumerate(fs[s:s+N]):
        i=s+k; im=Image.open(f).resize((W,H))
        x=(k%C)*W; y=(k//C)*(H+14)
        sh.paste(im,(x,y+14)); d.text((x+2,y+1),'%d  %.2fs'%(i,i/30),fill='yellow')
    sh.save('/tmp/r3/sheets/s%02d.png'%(s//N))
