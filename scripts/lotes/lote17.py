# desenhos enviados pelo cliente em 25/11 17h (Perfis_BX_1-1.pdf, CB-266_AP-056.pdf)
import sys,json; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
U='/mnt/user-data/uploads/'; OUT='lote17'
J=json.load(open(f'{OUT}/_jobs.json')); J['AP-023_BX-203'][1]=(60,100,264,330); J['AP-027_BX-223'][1]=(315,404,456,505)
dados={}
for nome,(f,clip) in J.items():
    R=fitz.Rect(clip); p=fitz.open(U+f)[0]
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    cs,fs=C.padronizar(U+f,1,R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=[],remover_texto=True,setas=True,normalizar=True)
    dados[nome]={'origem':f'{f[9:]} (PDF do cliente, 25/11)','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}
    print(nome,sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(f'{OUT}/_cotas.json','w'),ensure_ascii=False,indent=1)
# AP-057 usa o mesmo desenho do AP-056 (cliente, 25/11 18h20)
import shutil
for pre in ('','o_'):
    shutil.copy(f'{OUT}/{pre}AP-056.png',f'{OUT}/{pre}AP-057.png')
shutil.copy(f'{OUT}/AP-056.svg',f'{OUT}/AP-057.svg')
dados['AP-057']=dict(dados['AP-056'],origem=dados['AP-056']['origem']+' — mesmo desenho do AP-056')
json.dump(dados,open(f'{OUT}/_cotas.json','w'),ensure_ascii=False,indent=1)
