import fitz,re,json,sys
sys.path.insert(0,'/home/claude'); import cotas as C
d=fitz.open('euroshow.pdf'); cl=json.load(open('euro/_clips.json')); es=json.load(open('euroshow_idx.json'))
want=['ES-001','ES-002','ES-004','ES-006','ES-010','ES-016','ES-018','ES-019','ES-022','ES-024','ES-028','ES-030','ES-031','ES-033','ES-034','ES-040','ES-042R','ES-046','ES-047']
dados={}
for c in want:
    pg,bb=cl[c]; R=fitz.Rect(bb)
    t=fitz.open(); t.insert_pdf(d,from_page=pg-1,to_page=pg-1); q=t[0]
    # remove texto não numérico e o peso do cabeçalho (cabeçalho = palavras acima do 1º traço do desenho com Kg/m)
    hdr=[fitz.Rect(w[:4]) for w in q.get_text('words') if re.search(r'Kg/m|KG/M',w[4],re.I)]
    for w in q.get_text('words'):
        r=fitz.Rect(w[:4])
        if not re.fullmatch(r'[\d.,]+',w[4]) or any(abs(r.y0-h.y0)<3 and abs(r.x1-h.x0)<15 for h in hdr):
            q.add_redact_annot(r)
    q.apply_redactions(images=0,graphics=0,text=0)
    # perfil: preenchimentos cinza (0,81) -> preto
    sh=q.new_shape()
    for x in q.get_drawings():
        f=x.get('fill')
        if f and min(f)>0.6 and max(f)<0.95 and R.intersects(x['rect']):
            for it in x['items']:
                if it[0]=='l': sh.draw_line(it[1],it[2])
                elif it[0]=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
                elif it[0]=='re': sh.draw_rect(it[1])
                elif it[0]=='qu': sh.draw_quad(it[1])
            sh.finish(fill=(0,0,0),color=None,even_odd=x.get('even_odd',False),closePath=x.get('closePath',True))
    sh.commit()
    tmp=f'euro/tmp_{c}.pdf'; t.save(tmp)
    cs,fs=C.padronizar(tmp,1,R,f'euro/{c}.svg',f'euro/{c}.png')
    dados[c]={'origem':f'Euroshow pág. {pg}','fonte':'Bahnschrift','tamanho_pt':round(fs,2),
      'cotas':[{'valor':v.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[o]} for v,r,o in cs]}
    print(c,len(cs),sorted(v for v,r,o in cs))
json.dump(dados,open('euro/_cotas.json','w'),ensure_ascii=False,indent=1)
