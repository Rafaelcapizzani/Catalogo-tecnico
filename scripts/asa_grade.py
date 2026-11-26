import sys,json
from PIL import Image,ImageDraw,ImageFont
D='/home/claude/alcoa/asa/v1'
J=json.load(open('/home/claude/alcoa/asa/jobs.json'));ks=list(J)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
def grade(lst,out):
  cw,ch=300,300;cols=4;rows=(len(lst)+cols-1)//cols
  c=Image.new('RGB',(cw*cols,ch*rows),'white');d=ImageDraw.Draw(c)
  for i,k in enumerate(lst):
    im=Image.open(f'{D}/{k}.png').convert('RGB');im.thumbnail((cw-10,ch-28))
    x,y=(i%cols)*cw,(i//cols)*ch;c.paste(im,(x+5,y+24));d.text((x+4,y+2),k,fill='firebrick',font=f);d.rectangle([x,y,x+cw-1,y+ch-1],outline='gray')
  c.save(out)
for i in range(0,len(ks),24): grade(ks[i:i+24],f'/tmp/a{i//24}.png')
