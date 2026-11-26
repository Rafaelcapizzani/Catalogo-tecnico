"""Gira um desenho padronizado em 90° (horário) mantendo os números das cotas legíveis.

O desenho inteiro é girado; cada número de cota (grupo de glifos <use>) é
girado de volta em torno do próprio centro, então os números continuam na
mesma orientação do original (horizontais ou de baixo para cima).
O SVG é regravado no zip do pacote e o giro fica registrado em dados/rotacoes.json.

Uso: python3 scripts/girar_desenho.py LG-050 [graus=90]
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
        out.append({"ini": m.start(), "fim": m.end(), "txt": m.group(0), "x": e, "y": f, "esc": abs(a) or abs(b)})
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


def girar(svg, graus=90):
    cab = re.search(r'<svg\b[^>]*>', svg)
    w = float(re.search(r'\swidth="([\d.]+)', cab.group(0)).group(1))
    h = float(re.search(r'\sheight="([\d.]+)', cab.group(0)).group(1))
    vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', cab.group(0))
    vx, vy, vw, vh = (float(v) for v in vb.groups()) if vb else (0, 0, w, h)
    if graus != 90:
        raise SystemExit("só 90° horário por enquanto")
    gs = glifos(svg)
    grupos = agrupar(gs)
    corpo_ini = svg.index("</defs>") + len("</defs>") if "</defs>" in svg else cab.end()
    corpo_fim = svg.rindex("</svg>")
    corpo = svg[corpo_ini:corpo_fim]
    # tira os glifos do corpo e reinsere agrupados, com o "desgiro"
    for g in sorted(gs, key=lambda g: g["ini"], reverse=True):
        if g["ini"] >= corpo_ini:
            i, f = g["ini"] - corpo_ini, g["fim"] - corpo_ini
            corpo = corpo[:i] + corpo[f:]
    textos = []
    for gr in grupos:
        esc = gr[0]["esc"]
        x0 = min(g["x"] for g in gr)
        x1 = max(g["x"] for g in gr) + 0.55 * esc
        y0 = min(g["y"] for g in gr) - 0.7 * esc
        y1 = max(g["y"] for g in gr)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        textos.append(f'<g transform="rotate(-90 {cx:.3f} {cy:.3f})">' + "".join(g["txt"] for g in gr) + "</g>")
    # giro horário de 90° em torno da origem do viewBox + translação para caber
    novo_vb = f'{vy:.3f} {vx:.3f} {vh:.3f} {vw:.3f}'
    gir = f'<g transform="translate({vh + 2 * vy:.3f} 0) rotate(90)">'
    novo_cab = re.sub(r'\swidth="[^"]*"', f' width="{h}"', cab.group(0))
    novo_cab = re.sub(r'\sheight="[^"]*"', f' height="{w}"', novo_cab)
    novo_cab = re.sub(r'viewBox="[^"]*"', f'viewBox="{novo_vb}"', novo_cab) if vb else novo_cab
    return (svg[:cab.start()] + novo_cab + svg[cab.end():corpo_ini] + gir + corpo + "".join(textos) + "</g>\n" + svg[corpo_fim:])


def main():
    cod = sys.argv[1]
    graus = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    m = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))[cod]
    zp = os.path.join(RAIZ, "desenhos", "pacotes", f"{m['pacote']}-vetor.zip")
    with zipfile.ZipFile(zp) as z:
        itens = [(i, z.read(i.filename)) for i in z.infolist()]
    tmp = zp + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, dados in itens:
            if info.filename == m["arquivo"]:
                dados = girar(dados.decode("utf-8"), graus).encode("utf-8")
            z.writestr(info, dados)
    os.replace(tmp, zp)
    reg = os.path.join(RAIZ, "dados", "rotacoes.json")
    r = json.load(open(reg)) if os.path.exists(reg) else {}
    r[cod] = (r.get(cod, 0) + graus) % 360
    json.dump(r, open(reg, "w"), indent=1)
    print(f"{cod} girado {graus}° (total {r[cod]}°)")


if __name__ == "__main__":
    main()
