"""Gira um desenho padronizado em 90° (horário) mantendo os números das cotas legíveis.

O desenho inteiro é girado; cada número de cota (grupo de glifos <use>) é
girado de volta em torno do próprio centro, então os números continuam na
mesma orientação do original (horizontais ou de baixo para cima).
O SVG é regravado no zip do pacote e o giro fica registrado em dados/rotacoes.json.

Uso: python3 scripts/girar_desenho.py LG-050 [90|180|270|espelhar]  (90 = horário)
Depois: python3 scripts/medir_desenhos.py (novas medidas)
"""
import json
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE = re.compile(r'<use\b[^>]*?/>')


def glifos(svg):
    out = []
    for m in USE.finditer(svg):
        t = re.search(r'matrix\(([^)]*)\)', m.group(0))
        if not t:
            continue
        a, b, c, d, e, f = (float(v) for v in re.split(r'[ ,]+', t.group(1).strip()))
        # caixa nominal do glifo (0..0,55 × 0..0,7 em unidades da fonte) levada pela matriz
        cantos = [(a * u + c * v + e, b * u + d * v + f) for u, v in ((0, 0), (0.55, 0), (0, 0.7), (0.55, 0.7))]
        out.append({"ini": m.start(), "fim": m.end(), "txt": m.group(0), "mat": (a, b, c, d, e, f),
                    "x": e, "y": f, "esc": (a * a + b * b) ** 0.5, "cantos": cantos})
    return out


def agrupar(gs):
    grupos = []
    for g in sorted(gs, key=lambda g: (round(g["y"]), g["x"])):
        for gr in grupos:
            if any(abs(g["x"] - h["x"]) < 0.9 * g["esc"] and abs(g["y"] - h["y"]) < 0.9 * g["esc"] for h in gr):
                gr.append(g)
                break
        else:
            grupos.append([g])
    return grupos


# Operações (matriz linear 2×2 em coordenadas do SVG, y para baixo)
OPERACOES = {
    "90": (0, 1, -1, 0),      # 90° horário:  (x, y) → (−y, x)   [a, b, c, d] como no SVG
    "180": (-1, 0, 0, -1),
    "270": (0, -1, 1, 0),
    "espelhar": (-1, 0, 0, 1),  # espelho esquerda ↔ direita
}


def transformar(svg, op="90"):
    """Gira/espelha o desenho inteiro; cada número de cota volta à orientação original
    no próprio lugar (sem sair do grupo/recorte em que está)."""
    la, lb, lc, ld = OPERACOES[op]
    cab = re.search(r'<svg\b[^>]*>', svg)
    w = float(re.search(r'\swidth="([\d.]+)', cab.group(0)).group(1))
    h = float(re.search(r'\sheight="([\d.]+)', cab.group(0)).group(1))
    vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', cab.group(0))
    vx, vy, vw, vh = (float(v) for v in vb.groups()) if vb else (0, 0, w, h)
    L = lambda x, y: (la * x + lc * y, lb * x + ld * y)
    cs = [L(x, y) for x, y in ((vx, vy), (vx + vw, vy), (vx, vy + vh), (vx + vw, vy + vh))]
    nx, ny = min(c[0] for c in cs), min(c[1] for c in cs)
    nw, nh = max(c[0] for c in cs) - nx, max(c[1] for c in cs) - ny
    troca = abs(lb) == 1  # 90°/270°: largura e altura trocam
    det = la * ld - lb * lc
    ia, ib, ic, id_ = ld / det, -lb / det, -lc / det, la / det  # inversa
    corpo_ini = svg.index("</defs>") + len("</defs>") if "</defs>" in svg else cab.end()
    corpo_fim = svg.rindex("</svg>")
    novos = {}
    for gr in agrupar(glifos(svg)):
        pts = [p for g in gr for p in g["cantos"]]
        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
        tx = cx - (ia * cx + ic * cy)
        ty = cy - (ib * cx + id_ * cy)
        for g in gr:
            a, b, c, d, e, f = g["mat"]
            m = (ia * a + ic * b, ib * a + id_ * b, ia * c + ic * d, ib * c + id_ * d,
                 ia * e + ic * f + tx, ib * e + id_ * f + ty)
            t = re.search(r'matrix\(([^)]*)\)', g["txt"])
            novos[g["ini"]] = (g["fim"], g["txt"][:t.start()] + "matrix(" + ",".join(f"{v:.6f}" for v in m) + ")" + g["txt"][t.end():])
    partes, pos = [], corpo_ini
    for i in sorted(k for k in novos if k >= corpo_ini):
        partes += [svg[pos:i], novos[i][1]]
        pos = novos[i][0]
    partes.append(svg[pos:corpo_fim])
    corpo = "".join(partes)
    grupo = f'<g transform="matrix({la},{lb},{lc},{ld},0,0)">'
    novo_cab = re.sub(r'\swidth="[^"]*"', f' width="{h if troca else w}"', cab.group(0))
    novo_cab = re.sub(r'\sheight="[^"]*"', f' height="{w if troca else h}"', novo_cab)
    vb_txt = f'viewBox="{nx:.3f} {ny:.3f} {nw:.3f} {nh:.3f}"'
    novo_cab = re.sub(r'viewBox="[^"]*"', vb_txt, novo_cab) if vb else novo_cab.replace("<svg", "<svg " + vb_txt, 1)
    return svg[:cab.start()] + novo_cab + svg[cab.end():corpo_ini] + grupo + corpo + "</g>\n" + svg[corpo_fim:]


def main():
    cod = sys.argv[1]
    op = sys.argv[2] if len(sys.argv) > 2 else "90"
    m = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))[cod]
    zp = os.path.join(RAIZ, "desenhos", "pacotes", f"{m['pacote']}-vetor.zip")
    with zipfile.ZipFile(zp) as z:
        itens = [(i, z.read(i.filename)) for i in z.infolist()]
    tmp = zp + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, dados in itens:
            if info.filename == m["arquivo"]:
                dados = transformar(dados.decode("utf-8"), op).encode("utf-8")
            z.writestr(info, dados)
    os.replace(tmp, zp)
    reg = os.path.join(RAIZ, "dados", "rotacoes.json")
    r = json.load(open(reg)) if os.path.exists(reg) else {}
    r.setdefault(cod, [])
    if isinstance(r[cod], int):
        r[cod] = [str(r[cod])]
    r[cod].append(op)
    json.dump(r, open(reg, "w"), indent=1)
    print(f"{cod}: {op} (histórico {r[cod]})")


if __name__ == "__main__":
    main()
