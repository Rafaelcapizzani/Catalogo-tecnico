import fitz,re,json
d=fitz.open('euroshow.pdf'); es=json.load(open('euroshow_idx.json'))
want=['ES-001','ES-002','ES-004','ES-006','ES-010','ES-016','ES-018','ES-019','ES-022','ES-024','ES-028','ES-030','ES-031','ES-033','ES-034','ES-040','ES-042R','ES-046','ES-047']
clips={}
for pg in sorted({es[c][0] for c in want}):
  p=d[pg-1]; W,H=p.rect.width,p.rect.height
  heads=[]
  kg=p.search_for('Kg/m')+p.search_for('KG/M')
  for c in es:
    if es[c][0]!=pg: continue
    rs=[x for x in p.search_for(c) if not p.get_textbox(fitz.Rect(x.x1,x.y0,x.x1+6,x.y1)).strip()[:1].isdigit()]
    if not rs: continue
    r=rs[0]
    wr=[x for x in kg if x.y0>=r.y0-2 and x.y0<r.y0+70 and abs(x.x0-r.x0)<260]
    bottom=min(wr,key=lambda x:x.y0).y1 if wr else r.y1+30
    heads.append((c,r,bottom))
  cols_used={0 if h[1].x0<200 else 1 for h in heads}
  for c,r,bottom in heads:
    if c not in es: continue
    col=0 if r.x0<200 else 1
    x0,x1=(25,W-40) if len(cols_used)==1 else ((25,286) if col==0 else (290,W-40))
    below=[h[1].y0 for h in heads if h[1].y0>r.y0+5 and ((h[1].x0<200)==(col==0) or len(cols_used)==1)]
    y1=(min(below)-4) if below else H-42
    clip=fitz.Rect(x0,r.y0-2,x1,y1)
    if c=='ES-028': clip=fitz.Rect(25,r.y0-2,W-40,655)
    bb=fitz.Rect()
    for dr in p.get_drawings():
      rr=dr['rect']
      if clip.contains(rr) and not (rr.width>0.9*clip.width or rr.height>0.9*clip.height): bb|=rr
    hdr=fitz.Rect(x0,r.y0-3,x1,bottom+1)
    for w in p.get_text('words',clip=clip):
      if re.fullmatch(r'[\d.,]+',w[4]) and not fitz.Rect(w[:4]).intersects(hdr): bb|=fitz.Rect(w[:4])
    if bb.is_empty: print('vazio',c); continue
    bb=fitz.Rect(bb)&clip; bb=bb+(-4,-4,4,4)
    clips[c]=(pg,[round(v,1) for v in bb])
    t=fitz.open(); t.insert_pdf(d,from_page=pg-1,to_page=pg-1); q=t[0]
    for w in q.get_text('words'):
      if not re.fullmatch(r'[\d.,]+',w[4]) or fitz.Rect(w[:4]).intersects(hdr): q.add_redact_annot(fitz.Rect(w[:4]))
    q.apply_redactions(images=0,graphics=0,text=0)
    q.get_pixmap(dpi=80,clip=bb).save(f'euro/v_{c}.png')
    q.get_pixmap(dpi=300,clip=bb,colorspace=fitz.csGRAY).save(f'euro/hi_{c}.png')
for c in want: print(c,clips.get(c))
json.dump(clips,open('euro/_clips.json','w'))
