import pymupdf as fitz, subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
f=sys.argv[1]; d=fitz.open(f+'.pdf'); os.makedirs('ocr_'+f,exist_ok=True)
def run(i):
    out=f'ocr_{f}/p{i+1}.tsv'
    if os.path.exists(out): return
    png=f'ocr_{f}/p{i+1}.png'
    d[i].get_pixmap(dpi=200).save(png)
    r=subprocess.run(['tesseract',png,'-','--psm','11','tsv'],capture_output=True,text=True)
    open(out,'w').write(r.stdout); os.remove(png)
with ThreadPoolExecutor(8) as ex: list(ex.map(run, range(len(d))))
print('done',f)
