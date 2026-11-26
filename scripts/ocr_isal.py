import fitz,subprocess,sys,os
from concurrent.futures import ProcessPoolExecutor
def run(i):
    out=f'ocr_isal/p{i:03d}'
    if os.path.exists(out+'.tsv'): return
    d=fitz.open('isal.pdf'); d[i].get_pixmap(dpi=300,colorspace=fitz.csGRAY).save(out+'.png')
    subprocess.run(['tesseract',out+'.png',out,'--psm','11','-c','tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-,./kgm','tsv'],capture_output=True)
    os.remove(out+'.png')
if __name__=='__main__':
    with ProcessPoolExecutor(os.cpu_count()) as ex: list(ex.map(run,range(260)))
