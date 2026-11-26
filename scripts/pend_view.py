import json,sys
import pymupdf as fitz
from PIL import Image,ImageDraw
J=json.load(open('/home/claude/alcoa/pend/jobs.json'))
ks=sys.argv[1:] or list(J)
ims=[]
for k in ks:
    j=J[k]; p=fitz.open(j['pdf'])[j['pg']-1]; R=fitz.Rect(j['clip'])
    pm=p.get_pixmap(dpi=55,clip=R); pm.save('/tmp/_c.png')
    im=Image.open('/tmp/_c.png').convert('RGB'); im.thumbnail((230,200))
    c=Image.new('RGB',(240,220),'white'); c.paste(im,(5,18)); ImageDraw.Draw(c).text((3,2),f"{k} {j['cc'][:14]}",fill='red'); ims.append(c)
for g in range(0,len(ims),35):
    G=Image.new('RGB',(240*5,220*7),'gray')
    for i,c in enumerate(ims[g:g+35]): G.paste(c,((i%5)*240,(i//5)*220))
    G.save(f'/tmp/r8/pv{g//35}.png')
print(len(ims))
