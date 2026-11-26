import zipfile,os,sys,glob,json
sys.path.insert(0,'/home/claude')
from folha import folha
from PIL import Image
B='/home/claude/alcoa'
DIRS={'geral-alcoa':'ga/v1','geral-tera':'lote12','suprema':'su/v1','centenario-tms':'lote13','geral-asa':'asa/v1','decamp':'lote14','avulsos-cliente':'lote15','gold':'gold/v1','geral-stelman':'stl/v1'}
def membros(z):
    return [n for n in zipfile.ZipFile(f'{B}/{z}-vetor.zip').namelist() if n.endswith('.svg')]
PAC={z:membros(z) for z in ['geral-alcoa','suprema','geral-asa','gold','geral-stelman']}
# lotes avulsos
lot=[]
for d,pasta in [('lote9','lote9'),('lote10','lote10'),('lote11','lote11'),('euro','euroshow')]:
    for s in sorted(glob.glob(f'{B}/{d}/*.svg')):
        if os.path.exists(s[:-4].rsplit('/',1)[0]+'/o_'+os.path.basename(s)[:-4]+'.png'): lot.append(f'{pasta}/'+os.path.basename(s))
DIRS.update({'lote9':'lote9','lote10':'lote10','lote11':'lote11','euroshow':'euro'})
PAC['lotes-avulsos']=lot
PAC['belmetal-atlanta']=['belmetal-atlanta/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/atl/v1/*.svg'))]
DIRS['belmetal-atlanta']='atl/v1'
PAC['perfis-cliente-25-11']=['perfis-cliente-25-11/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/lote16/*.svg'))]
DIRS['perfis-cliente-25-11']='lote16'
PAC['perfis-cliente-25-11']+=['perfis-cliente-25-11-b/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/lote17/*.svg'))]
DIRS['perfis-cliente-25-11-b']='lote17'
PAC['perfis-cliente-25-11']+=['geral-hera/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/lote18/*.svg'))]
DIRS['geral-hera']='lote18'
PAC['perfis-cliente-25-11']+=['stelman-avulso/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/lote19/*.svg'))]
DIRS['stelman-avulso']='lote19'
PAC['perfis-cliente-25-11']+=['muxarabi/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/lote20/*.svg'))]
DIRS['muxarabi']='lote20'
PAC['pendentes-padronizados']=['pendentes/'+os.path.basename(x) for x in sorted(glob.glob(f'{B}/pend/v1/*.svg'))]
DIRS['pendentes']='pend/v1'
import sys as _s
if len(_s.argv)>1: PAC={k:v for k,v in PAC.items() if k in _s.argv[1:]}
for z,ms in PAC.items():
    out=f'/home/claude/out/{z}-vetor.zip'; pares=[]; pastas=set()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as Z:
        for m in ms:
            pasta,f=m.split('/'); d=f'{B}/{DIRS[pasta]}'; k=f[:-4]
            Z.write(f'{d}/{f}',m); pastas.add(pasta)
            pares.append((k,f'{d}/o_{k}.png',f'{d}/{k}.png'))
        for pasta in pastas:
            d=f'{B}/{DIRS[pasta]}'; J=json.load(open(f'{d}/_cotas.json'))
            ks={m.split('/')[1][:-4] for m in ms if m.startswith(pasta+'/')}
            Z.writestr(f'{pasta}/_cotas.json',json.dumps({k:v for k,v in J.items() if k in ks},ensure_ascii=False,indent=1))
    pages=[]
    for i in range(0,len(pares),6):
        folha(pares[i:i+6],'/tmp/_pg.png',larg=620); pages.append(Image.open('/tmp/_pg.png').convert('RGB'))
    pages[0].save(f'/home/claude/out/{z}-conferencia.pdf',save_all=True,append_images=pages[1:],resolution=110)
    print(z,len(ms),len(pages))
