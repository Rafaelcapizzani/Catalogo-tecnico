import pymupdf as fitz, subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
f=sys.argv[1]; d=fitz.open(f+'.pdf'); od='ocr2_'+f; os.makedirs(od,exist_ok=True)
def run(i):
    out=f'{od}/p{i+1}.tsv'
    if os.path.exists(out): return
    png=f'{od}/p{i+1}.png'
    d[i].get_pixmap(dpi=300).save(png)
    r=subprocess.run(['tesseract',png,'-','--psm','11','-c','tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/,. Kgm','tsv'],capture_output=True,text=True)
    open(out,'w').write(r.stdout); os.remove(png)
with ThreadPoolExecutor(8) as ex: list(ex.map(run, range(len(d))))
print('done',f, len(os.listdir(od)))
