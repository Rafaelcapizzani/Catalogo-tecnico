# LG-129E (= LG-129, Alumil): perfil em tiras de triângulos deixa frestas -> rasteriza o desenho já padronizado, fecha as frestas e vetoriza (potrace)
import sys,json,subprocess; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C, cv2, numpy as np
D='/home/claude/alcoa/pend/v1'; J=json.load(open('/home/claude/alcoa/pend/jobs.json')); j=J['LG-129E']; R=fitz.Rect(j['clip'])
dados=json.load(open(f'{D}/_cotas.json')); cs=dados['LG-129E']['cotas']
subprocess.run(['rsvg-convert','-d','600','-p','600','-z',str(600/72),'-b','white',f'{D}/LG-129E.svg','-o','/tmp/lg/r.png'],check=True)
g=cv2.imread('/tmp/lg/r.png',0)
bw=(g<140).astype(np.uint8)
bw=cv2.morphologyEx(bw,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
bw=cv2.morphologyEx(bw,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(2,2)))
cv2.imwrite('/tmp/lg/p.png',np.where(bw>0,0,255).astype(np.uint8))
# cotas como já padronizadas (posição relativa ao recorte)
fs=dados['LG-129E']['tamanho_pt']
lid=C.ler_cotas(fitz.open(j['pdf'])[j['pg']-1],R)
cot=[]
for c in cs:
    t=c['valor']; w=C._font.text_length(t,fs); h=C.CAP*fs; x,y=c['x'],c['y']
    v={'horizontal':False,'vertical (baixo→cima)':'up','vertical (cima→baixo)':'down'}.get(c['direcao'],False)
    r=fitz.Rect(x-w/2,y-h/2,x+w/2,y+h/2) if not v else fitz.Rect(x-h/2,y-w/2,x+h/2,y+w/2)
    cot.append((t,r,v))
C.padronizar_raster('/tmp/lg/p.png',f'{D}/LG-129E.svg',f'{D}/LG-129E.png',dpi_img=600,cotas=cot,fs=fs)
print('ok',[c[0] for c in cot])
