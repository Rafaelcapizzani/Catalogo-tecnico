import pymupdf as fitz, subprocess, os, sys, json
from concurrent.futures import ThreadPoolExecutor
d=fitz.open('/home/claude/alcoa/geral.pdf'); od='/home/claude/alcoa/ga/ocr'; os.makedirs(od,exist_ok=True)
def run(i):
    out=f'{od}/p{i+1}.tsv'
    if os.path.exists(out): return
    png=f'{od}/p{i+1}.png'
    d[i].get_pixmap(dpi=300,colorspace=fitz.csGRAY).save(png)
    r=subprocess.run(['tesseract',png,'-','--psm','11','tsv'],capture_output=True,text=True)
    open(out,'w').write(r.stdout); os.remove(png)
pages=sorted(set(int(x) for x in sys.argv[1:]))
with ThreadPoolExecutor(8) as ex: list(ex.map(run,[p-1 for p in pages if 0<p<=len(d)]))
