import sys,fitz
from PIL import Image,ImageDraw,ImageFont
def folha(pares, out, larg=620):
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',20)
    rows=[]
    for nome,a,b in pares:
        A=Image.open(a).convert('RGB'); B=Image.open(b).convert('RGB')
        sa=larg/A.width; sb=larg/B.width
        A=A.resize((larg,int(A.height*sa))); B=B.resize((larg,int(B.height*sb)))
        h=max(A.height,B.height)+34
        c=Image.new('RGB',(2*larg+30,h),'white'); c.paste(A,(0,30)); c.paste(B,(larg+30,30))
        d=ImageDraw.Draw(c); d.text((4,4),nome+'  — original',fill='firebrick',font=f); d.text((larg+34,4),'cotas padronizadas (Bahnschrift)',fill='darkgreen',font=f)
        d.line([(0,h-1),(c.width,h-1)],fill='gray',width=2); rows.append(c)
    H=sum(r.height for r in rows); s=Image.new('RGB',(rows[0].width,H),'white'); y=0
    for r in rows: s.paste(r,(0,y)); y+=r.height
    s.save(out); return s.size
