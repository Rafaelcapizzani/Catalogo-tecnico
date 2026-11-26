"""Remove dos desenhos as linhas de moldura herdadas da página do catálogo do fabricante.

Defeito (relatado pelo cliente em 26/11/2026 no LG-071 e no LG-076): o quadro
da página/célula do catálogo de origem é um retângulo só de contorno
(fill="none", d="M0 0H…V…H0Z") que, recortado junto com o perfil, aparece como
linhas soltas nas bordas do desenho.

Critério: path retangular, sem preenchimento, cujo retângulo passa dos limites
do viewBox do SVG (ou seja, é maior que o próprio desenho recortado).

Uso:
  python3 scripts/remover_molduras.py            → só lista
  python3 scripts/remover_molduras.py --aplicar LG-071 AP-0603  → regrava só esses desenhos
  (na varredura de 26/11, só LG-071 e AP-0603 tinham moldura visível; nos demais ela fica fora do recorte)
"""
import json
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RET = re.compile(r'^M\s*([\d.\-]+)[ ,]([\d.\-]+)\s*H\s*([\d.\-]+)\s*V\s*([\d.\-]+)\s*H\s*([\d.\-]+)\s*Z$')
PATH = re.compile(r'<path\b[^>]*?/>', re.S)


def molduras(svg):
    cab = svg[:800]
    vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', cab)
    if vb:
        vx, vy, vw, vh = (float(v) for v in vb.groups())
    else:
        m = re.search(r'width="([\d.]+)(?:pt)?" height="([\d.]+)(?:pt)?"', cab)
        vx, vy, vw, vh = 0, 0, float(m[1]), float(m[2])
    achadas = []
    for m in PATH.finditer(svg):
        e = m.group(0)
        if 'fill="none"' not in e or "stroke=" not in e:
            continue
        d = re.search(r'\sd="([^"]*)"', e)
        r = RET.match(d.group(1).strip()) if d else None
        if not r:
            continue
        x0, y0, x1, y1, _ = (float(v) for v in r.groups())
        t = re.search(r'matrix\(([^)]*)\)', e)
        a, b, c, dd, ex, fy = ([float(v) for v in re.split(r'[ ,]+', t.group(1).strip())] if t else (1, 0, 0, 1, 0, 0))
        xs = [a * x + c * y + ex for x, y in ((x0, y0), (x1, y1))]
        ys = [b * x + dd * y + fy for x, y in ((x0, y0), (x1, y1))]
        fora = min(xs) < vx - 1 or max(xs) > vx + vw + 1 or min(ys) < vy - 1 or max(ys) > vy + vh + 1
        if fora:
            achadas.append((m.start(), m.end()))
    return achadas


def main():
    aplicar = "--aplicar" in sys.argv
    somente = {a for a in sys.argv[1:] if not a.startswith("--")}
    pasta = os.path.join(RAIZ, "desenhos", "pacotes")
    relatorio = {}
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith("-vetor.zip"):
            continue
        caminho = os.path.join(pasta, nome)
        with zipfile.ZipFile(caminho) as z:
            itens = [(i, z.read(i.filename)) for i in z.infolist()]
        mudou = False
        novos = []
        for info, dados in itens:
            if info.filename.endswith(".svg"):
                svg = dados.decode("utf-8")
                ach = molduras(svg)
                cod = os.path.basename(info.filename)[:-4]
                if ach and (not somente or cod.split("_")[0] in somente):
                    relatorio[cod] = {"pacote": nome, "molduras": len(ach)}
                    for ini, fim in reversed(ach):
                        svg = svg[:ini] + svg[fim:]
                    dados = svg.encode("utf-8")
                    mudou = True
            novos.append((info, dados))
        if aplicar and mudou:
            tmp = caminho + ".tmp"
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
                for info, dados in novos:
                    z.writestr(info, dados)
            os.replace(tmp, caminho)
    for cod, r in relatorio.items():
        print(f"{cod:12s} {r['pacote']:40s} {r['molduras']} moldura(s)")
    print(f"{len(relatorio)} desenhos com moldura{' — corrigidos' if aplicar else ''}")
    if aplicar:
        json.dump(relatorio, open(os.path.join(RAIZ, "dados", "molduras-removidas.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
