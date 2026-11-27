"""Tira o ",0" do fim das cotas (ex.: 236,0 → 236) e recentraliza o número.

Padrão do catálogo: cota sem casa decimal quando ela é zero.
Uso: python3 scripts/tirar_decimal_zero.py LG-570 LG-571 LG-572
"""
import json
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE = re.compile(r'<use\b[^>]*?/>')


def mat(u):
    return [float(v) for v in re.split(r'[ ,]+', re.search(r'matrix\(([^)]*)\)', u).group(1).strip())]


def corrigir(svg):
    us = list(USE.finditer(svg))
    remover, mover = set(), {}
    for i in range(len(us) - 1):
        t1 = re.search(r'data-text="([^"]*)"', us[i].group(0))
        t2 = re.search(r'data-text="([^"]*)"', us[i + 1].group(0))
        if not (t1 and t2 and t1.group(1) == "," and t2.group(1) == "0"):
            continue
        nxt = re.search(r'data-text="([^"]*)"', us[i + 2].group(0)).group(1) if i + 2 < len(us) else ""
        a, b, c, d, e, f = mat(us[i].group(0))
        e2, f2 = mat(us[i + 1].group(0))[4:6]
        if nxt.isdigit() and abs(mat(us[i + 2].group(0))[4] - e2) + abs(mat(us[i + 2].group(0))[5] - f2) < 1.2 * (a * a + b * b) ** 0.5:
            continue  # o 0 não é o último algarismo (ex.: 2,05)
        remover |= {i, i + 1}
        # largura retirada ≈ do início da vírgula ao fim do zero; os algarismos andam metade
        esc = (a * a + b * b) ** 0.5
        larg = ((e2 - e) ** 2 + (f2 - f) ** 2) ** 0.5 + 0.55 * esc
        ux, uy = a / esc, b / esc
        j = i - 1
        while j >= 0 and re.search(r'data-text="(\d)"', us[j].group(0)):
            ej, fj = mat(us[j].group(0))[4:6]
            if ((ej - e) ** 2 + (fj - f) ** 2) ** 0.5 > 4 * esc:
                break
            mover[j] = (ux * larg / 2, uy * larg / 2)
            j -= 1
    out, pos = [], 0
    for k, m in enumerate(us):
        out.append(svg[pos:m.start()])
        u = m.group(0)
        if k in remover:
            u = ""
        elif k in mover:
            v = mat(u)
            v[4] += mover[k][0]
            v[5] += mover[k][1]
            u = re.sub(r'matrix\([^)]*\)', "matrix(" + ",".join(f"{x:.6f}" for x in v) + ")", u)
        out.append(u)
        pos = m.end()
    out.append(svg[pos:])
    return "".join(out), len(remover) // 2


def main():
    M = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))
    for cod in sys.argv[1:]:
        m = M[cod]
        zp = os.path.join(RAIZ, "desenhos", "pacotes", f"{m['pacote']}-vetor.zip")
        with zipfile.ZipFile(zp) as z:
            itens = [(i, z.read(i.filename)) for i in z.infolist()]
        tmp = zp + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for info, dados in itens:
                if info.filename == m["arquivo"]:
                    novo, n = corrigir(dados.decode("utf-8"))
                    dados = novo.encode("utf-8")
                    print(f"{cod}: {n} cota(s) sem ,0")
                z.writestr(info, dados)
        os.replace(tmp, zp)


if __name__ == "__main__":
    main()
