"""Troca setas abertas ("V" só de contorno) pela seta triangular cheia aprovada.

Defeito (relatado pelo cliente em 26/11/2026 no LG-133, LG-158 e LG-159): na
padronização, algumas pontas de cota ficaram só com o "V" de contorno, sem o
triângulo preenchido. Este script procura, em todos os desenhos, os "V" de
contorno com cara de ponta de seta (duas pernas iguais de 7 a 10 unidades,
abertura estreita) que ficam na ponta de uma linha de cota alinhada e cuja
ponta não tem triângulo preenchido, e acrescenta o
triângulo cheio no mesmo tamanho dos já padronizados (6,1 de comprimento e
3,3 de base, em unidades do SVG).

Uso:
  python3 scripts/fechar_setas.py            → só conta
  python3 scripts/fechar_setas.py --aplicar  → regrava os zips em desenhos/pacotes/
  python3 scripts/fechar_setas.py --aplicar --so LG-158,LG-159  → só esses códigos
"""
import math
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from limpar_desenhos import PATH, matriz, subcaminhos  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP, MEIA_BASE = 6.1, 1.65


def pontas(svg):
    defs_fim = svg.find("</defs>")
    abertas, cheias, cor, linhas = [], [], None, []
    for m in PATH.finditer(svg):
        if m.start() < defs_fim:
            continue
        e = m.group(0)
        d = re.search(r'\sd="([^"]*)"', e)
        if not d or ' id="' in e:
            continue
        contorno = 'fill="none"' in e
        a, b, c, dd, ex, fy = matriz(e)
        for _, pts in subcaminhos(d.group(1)):
            P = [(a * x + c * y + ex, b * x + dd * y + fy) for x, y in pts]
            if contorno and len(P) == 2 and math.dist(P[0], P[1]) > 8:
                linhas.append(P)
            if contorno and len(P) == 3:
                l1, l2, base = math.dist(P[0], P[1]), math.dist(P[1], P[2]), math.dist(P[0], P[2])
                if 7 <= l1 <= 10 and abs(l1 - l2) < 0.5 and base < 0.6 * l1:
                    abertas.append((P[1], ((P[0][0] + P[2][0]) / 2, (P[0][1] + P[2][1]) / 2)))
            elif not contorno and 3 <= len(P) <= 5:
                if max(math.dist(P[0], q) for q in P) < 8:
                    cheias.extend(P)
                    f = re.search(r'\sfill="([^"]*)"', e)
                    cor = cor or (f.group(1) if f else "#000000")
    faltando = []
    vistos = set()
    for ponta, meio in abertas:
        chave = (round(ponta[0], 1), round(ponta[1], 1))
        if chave in vistos or any(math.dist(ponta, q) < 1.0 for q in cheias):
            continue
        # tem de ser a ponta de uma linha de cota alinhada com a seta
        ux, uy = meio[0] - ponta[0], meio[1] - ponta[1]
        n = math.hypot(ux, uy) or 1
        alinhada = False
        for a_, b_ in linhas:
            for p0, p1 in ((a_, b_), (b_, a_)):
                if math.dist(p0, ponta) < 0.8:
                    lx, ly = p1[0] - p0[0], p1[1] - p0[1]
                    ln = math.hypot(lx, ly) or 1
                    if (lx * ux + ly * uy) / (ln * n) > 0.98:
                        alinhada = True
        if not alinhada:
            continue
        vistos.add(chave)
        faltando.append((ponta, meio))
    return faltando, cor or "#000000"


def triangulo(ponta, meio):
    ux, uy = meio[0] - ponta[0], meio[1] - ponta[1]
    n = math.hypot(ux, uy) or 1
    ux, uy = ux / n, uy / n
    cx, cy = ponta[0] + ux * COMP, ponta[1] + uy * COMP
    vx, vy = -uy * MEIA_BASE, ux * MEIA_BASE
    return f"M{ponta[0]:.3f} {ponta[1]:.3f}L{cx + vx:.3f} {cy + vy:.3f}L{cx - vx:.3f} {cy - vy:.3f}Z"


def main():
    aplicar = "--aplicar" in sys.argv
    so = set(sys.argv[sys.argv.index("--so") + 1].split(",")) if "--so" in sys.argv else None
    pasta = os.path.join(RAIZ, "desenhos", "pacotes")
    total = 0
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith("-vetor.zip"):
            continue
        caminho = os.path.join(pasta, nome)
        with zipfile.ZipFile(caminho) as z:
            itens = [(i, z.read(i.filename)) for i in z.infolist()]
        novos, mudou = [], False
        for info, dados in itens:
            cod = os.path.basename(info.filename)[:-4].split("_")[0]
            if info.filename.endswith(".svg") and (so is None or cod in so):
                svg = dados.decode("utf-8")
                falt, cor = pontas(svg)
                if falt:
                    total += len(falt)
                    print(f"{os.path.basename(info.filename)[:-4]:16s} {len(falt)} seta(s) aberta(s)")
                    d = "".join(triangulo(p, m) for p, m in falt)
                    # desenho girado/espelhado: o triângulo entra no grupo de fora, no mesmo
                    # referencial das linhas de cota
                    i = svg.rfind("</g>") if re.search(r'</defs>\s*<g transform="(translate|matrix)', svg) else svg.rfind("</svg>")
                    svg = svg[:i] + f'<path d="{d}" fill="{cor}"/>\n' + svg[i:]
                    dados = svg.encode("utf-8")
                    mudou = True
            novos.append((info, dados))
        if aplicar and mudou:
            tmp = caminho + ".tmp"
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
                for info, dados in novos:
                    z.writestr(info, dados)
            os.replace(tmp, caminho)
    print(f"{total} setas abertas{' corrigidas' if aplicar else ''}")


if __name__ == "__main__":
    main()
