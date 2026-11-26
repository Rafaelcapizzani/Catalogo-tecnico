import pymupdf as fitz, subprocess, sys, os, csv, io
from concurrent.futures import ThreadPoolExecutor
d=fitz.open('asa.pdf')
def run(i):
    out=f'ocr/p{i+1}.tsv'
    if os.path.exists(out): return
    png=f'ocr/p{i+1}.png'
    d[i].get_pixmap(dpi=200).save(png)
    r=subprocess.run(['tesseract',png,'-','--psm','11','tsv'],capture_output=True,text=True)
    open(out,'w').write(r.stdout); os.remove(png)
with ThreadPoolExecutor(8) as ex: list(ex.map(run, range(14,len(d))))
print('ok')
