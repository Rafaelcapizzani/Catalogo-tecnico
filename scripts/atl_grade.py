import sys,glob,os
sys.path.insert(0,'/home/claude')
from PIL import Image,ImageDraw
fs=sorted(glob.glob('/home/claude/alcoa/atl/v1/*.png')); fs=[f for f in fs if not os.path.basename(f).startswith('o_')]
ims=[]
for f in fs:
    im=Image.open(f).convert('RGB'); im.thumbnail((290,270)); c=Image.new('RGB',(300,300),'white'); c.paste(im,(5,22)); ImageDraw.Draw(c).text((4,4),os.path.basename(f)[:-4],fill='red'); ims.append(c)
for g in range(0,len(ims),20):
    G=Image.new('RGB',(1200,1500),'gray')
    for i,c in enumerate(ims[g:g+20]): G.paste(c,((i%4)*300,(i//4)*300))
    G.save(f'/tmp/r3/atp{g//20}.png')
