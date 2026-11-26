"""Mede o tamanho real (mm) de cada desenho padronizado.

Renderiza cada SVG (desenhos/pacotes/*-vetor.zip e, como reserva, a base do
protótipo) e mede a área efetivamente desenhada (perfil + cotas), sem a margem
em branco que alguns SVGs têm. Os desenhos estão na escala do catálogo do
fabricante (1:1 na grande maioria — ver scripts/validar_escala.py).

Grava dados/medidas-desenhos.json: código Alplan → pacote, arquivo, largura e
altura do desenho (mm) e o recorte (viewBox, em unidades do SVG) que o gerador
do PDF usa para enquadrar só o desenho.

Uso: python3 scripts/medir_desenhos.py
"""
import io
import json
import os
import re
import subprocess
import zipfile

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PT_MM = 25.4 / 72
ZOOM = 4  # px por unidade declarada (pt)

# Quando o mesmo código aparece em mais de um pacote, vence o mais recente.
PRIORIDADE = [
    "pendentes-padronizados",
    "perfis-cliente-25-11",
    "folhas-cliente",
    "lotes-avulsos",
    "belmetal-atlanta",
    "geral-stelman",
    "geral-asa",
    "gold",
    "suprema",
    "geral-alcoa",
]


def medir(svg_bytes):
    cab = svg_bytes[:800].decode("utf-8", "ignore")
    m = re.search(r'width="([\d.]+)(?:pt)?" height="([\d.]+)(?:pt)?"', cab)
    if not m:
        return None
    w, h = float(m[1]), float(m[2])
    vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', cab)
    vx, vy, vw, vh = (float(x) for x in vb.groups()) if vb else (0, 0, w, h)
    r = subprocess.run(["rsvg-convert", "-z", str(ZOOM), "-b", "white"], input=svg_bytes,
                       capture_output=True, check=True)
    img = np.array(Image.open(io.BytesIO(r.stdout)).convert("L")) < 235
    ys, xs = np.where(img)
    if not len(xs):
        return None
    folga = 1  # px
    x0, x1 = max(xs.min() - folga, 0), min(xs.max() + 1 + folga, img.shape[1])
    y0, y1 = max(ys.min() - folga, 0), min(ys.max() + 1 + folga, img.shape[0])
    # px → unidades declaradas (pt) → unidades do viewBox
    sx, sy = vw / w, vh / h
    recorte = [vx + x0 / ZOOM * sx, vy + y0 / ZOOM * sy, (x1 - x0) / ZOOM * sx, (y1 - y0) / ZOOM * sy]
    return {
        "largura_mm": round((x1 - x0) / ZOOM * PT_MM, 1),
        "altura_mm": round((y1 - y0) / ZOOM * PT_MM, 1),
        "svg_mm": [round(w * PT_MM, 1), round(h * PT_MM, 1)],
        "recorte": [round(v, 2) for v in recorte],
    }


def main():
    medidas = {}
    for pacote in reversed(PRIORIDADE):  # os prioritários sobrescrevem
        caminho = os.path.join(RAIZ, "desenhos", "pacotes", f"{pacote}-vetor.zip")
        if not os.path.exists(caminho):
            continue
        with zipfile.ZipFile(caminho) as z:
            for n in z.namelist():
                if not n.endswith(".svg"):
                    continue
                med = medir(z.read(n))
                if med:
                    codigo = os.path.basename(n)[:-4].split("_")[0]
                    medidas[codigo] = {"pacote": pacote, "arquivo": n, **med}
    base = os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip")
    if os.path.exists(base):
        with zipfile.ZipFile(base) as z:
            for n in z.namelist():
                codigo = os.path.basename(n)[:-4]
                if n.startswith("desenhos/") and n.endswith(".svg") and codigo not in medidas:
                    med = medir(z.read(n))
                    if med:
                        medidas[codigo] = {"pacote": "base-prototipo", "arquivo": n, **med}
    destino = os.path.join(RAIZ, "dados", "medidas-desenhos.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(medidas.items())), f, ensure_ascii=False, indent=1)
    print(f"{len(medidas)} desenhos medidos → {os.path.relpath(destino, RAIZ)}")


if __name__ == "__main__":
    main()
