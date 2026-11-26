"""Remove traços que não pertencem ao perfil (sobras de desenhos vizinhos do catálogo de origem).

Trabalha no nível de subcaminho: cada <path> só de contorno (fill="none") é
quebrado nos seus subcaminhos (cada "M ...") e só os subcaminhos listados em
dados/correcoes-desenhos.json são apagados. Pontas de seta preenchidas (pequenas)
também podem sair; o perfil e os números das cotas nunca são tocados.

dados/correcoes-desenhos.json:
  { "LG-124": {"remover": [[x0, y0, x1, y1], ...], "motivo": "..."} }
  Cada retângulo está em unidades do SVG (as do viewBox). Um subcaminho é
  removido quando a caixa dele cabe inteira num dos retângulos.
  "vaos": [{"x": X, "de": Y0, "ate": Y1}] abre vão na linha de cota que corta o número.

Uso:
  python3 scripts/limpar_desenhos.py listar LG-124   → imagem numerada em /tmp/limpeza/LG-124.png + lista
  python3 scripts/limpar_desenhos.py aplicar         → regrava os zips em desenhos/pacotes/
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = re.compile(r'<path\b[^>]*?/>', re.S)
NUM = re.compile(r'-?\d*\.?\d+(?:e-?\d+)?')


def matriz(e):
    t = re.search(r'matrix\(([^)]*)\)', e)
    return [float(v) for v in re.split(r'[ ,]+', t.group(1).strip())] if t else [1, 0, 0, 1, 0, 0]


def subcaminhos(d):
    """Quebra um d (só comandos absolutos M L H V C Z) em subcaminhos com a lista de pontos."""
    partes = re.split(r'(?=M)', d.strip())
    out = []
    for p in partes:
        if not p.strip():
            continue
        pts = []
        x = y = 0.0
        for cmd, args in re.findall(r'([MLHVCZ])([^MLHVCZ]*)', p):
            n = [float(v) for v in NUM.findall(args)]
            if cmd in "ML":
                for i in range(0, len(n) - 1, 2):
                    x, y = n[i], n[i + 1]
                    pts.append((x, y))
            elif cmd == "H":
                for v in n:
                    x = v
                    pts.append((x, y))
            elif cmd == "V":
                for v in n:
                    y = v
                    pts.append((x, y))
            elif cmd == "C":
                for i in range(0, len(n) - 5, 6):
                    pts += [(n[i], n[i + 1]), (n[i + 2], n[i + 3])]
                    x, y = n[i + 4], n[i + 5]
                    pts.append((x, y))
        out.append((p, pts))
    return out


def tracos(svg):
    """Lista (início, fim, índice do subcaminho, caixa em unidades do SVG) dos traços removíveis."""
    defs_fim = svg.find("</defs>")
    res = []
    for m in PATH.finditer(svg):
        if m.start() < defs_fim:
            continue
        e = m.group(0)
        contorno = 'fill="none"' in e and "stroke=" in e
        d = re.search(r'\sd="([^"]*)"', e)
        if not d or ' id="' in e:
            continue
        a, b, c, dd, ex, fy = matriz(e)
        for k, (_, pts) in enumerate(subcaminhos(d.group(1))):
            if not pts:
                continue
            xs = [a * x + c * y + ex for x, y in pts]
            ys = [b * x + dd * y + fy for x, y in pts]
            caixa = (min(xs), min(ys), max(xs), max(ys))
            # preenchidos: só pontas de seta (pequenas); o perfil nunca entra
            if not contorno and max(caixa[2] - caixa[0], caixa[3] - caixa[1]) > 6:
                continue
            res.append((m.start(), m.end(), k, caixa))
    return res


def dentro(caixa, ret, folga=0.6):
    return (caixa[0] >= ret[0] - folga and caixa[1] >= ret[1] - folga and
            caixa[2] <= ret[2] + folga and caixa[3] <= ret[3] + folga)


def limpar(svg, retangulos):
    alvo = {}
    for ini, fim, k, caixa in tracos(svg):
        if any(dentro(caixa, r) for r in retangulos):
            alvo.setdefault((ini, fim), set()).add(k)
    for (ini, fim), ks in sorted(alvo.items(), reverse=True):
        e = svg[ini:fim]
        d = re.search(r'\sd="([^"]*)"', e)
        resto = [p for k, (p, _) in enumerate(subcaminhos(d.group(1))) if k not in ks]
        novo = "" if not resto else e[:d.start(1)] + "".join(resto) + e[d.end(1):]
        svg = svg[:ini] + novo + svg[fim:]
    return svg, sum(len(v) for v in alvo.values())


def abrir_vaos(svg, vaos):
    """Abre vão na linha de cota onde ela atravessa o número.

    vaos: [{"x": X, "de": Y0, "ate": Y1}] para linha vertical em X,
          [{"y": Y, "de": X0, "ate": X1}] para linha horizontal em Y
    (unidades do SVG). A linha que cruza o intervalo é partida em duas.
    """
    n = 0
    for vao in vaos:
        for _ in range(50):  # a mesma linha pode estar repetida no arquivo
            antes = n
            svg, n = _um_vao(svg, vao, n)
            if n == antes:
                break
    return svg, n


def _um_vao(svg, vao, n):
    if True:
        for m in list(PATH.finditer(svg)):
            e = m.group(0)
            if 'fill="none"' not in e:
                continue
            d = re.search(r'\sd="([^"]*)"', e)
            if not d:
                continue
            a, b, c, dd, ex, fy = matriz(e)
            det = a * dd - b * c
            if not det:
                continue

            def local(X, Y):
                X, Y = X - ex, Y - fy
                return ((dd * X - c * Y) / det, (-b * X + a * Y) / det)

            novas, mudou = [], False
            for parte, pts in subcaminhos(d.group(1)):
                P = [(a * x + c * y + ex, b * x + dd * y + fy) for x, y in pts]
                if len(P) == 2:
                    if "x" in vao and abs(P[0][0] - vao["x"]) < 0.4 and abs(P[1][0] - vao["x"]) < 0.4:
                        lo, hi = sorted((P[0][1], P[1][1]))
                        if lo < vao["de"] and hi > vao["ate"]:
                            p1, p2, p3, p4 = local(vao["x"], lo), local(vao["x"], vao["de"]), local(vao["x"], vao["ate"]), local(vao["x"], hi)
                            parte = f"M{p1[0]:.3f} {p1[1]:.3f}L{p2[0]:.3f} {p2[1]:.3f}M{p3[0]:.3f} {p3[1]:.3f}L{p4[0]:.3f} {p4[1]:.3f}"
                            mudou = True
                    if "y" in vao and abs(P[0][1] - vao["y"]) < 0.4 and abs(P[1][1] - vao["y"]) < 0.4:
                        lo, hi = sorted((P[0][0], P[1][0]))
                        if lo < vao["de"] and hi > vao["ate"]:
                            p1, p2, p3, p4 = local(lo, vao["y"]), local(vao["de"], vao["y"]), local(vao["ate"], vao["y"]), local(hi, vao["y"])
                            parte = f"M{p1[0]:.3f} {p1[1]:.3f}L{p2[0]:.3f} {p2[1]:.3f}M{p3[0]:.3f} {p3[1]:.3f}L{p4[0]:.3f} {p4[1]:.3f}"
                            mudou = True
                novas.append(parte)
            if mudou:
                n += 1
                novo = e[:d.start(1)] + "".join(novas) + e[d.end(1):]
                svg = svg[:m.start()] + novo + svg[m.end():]
                return svg, n
    return svg, n


def localizar(codigo):
    m = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))[codigo]
    return os.path.join(RAIZ, "desenhos", "pacotes", f"{m['pacote']}-vetor.zip"), m["arquivo"]


def listar(codigo):
    from PIL import Image, ImageDraw
    zp, arq = localizar(codigo)
    svg = zipfile.ZipFile(zp).read(arq).decode("utf-8")
    z = 5
    png = subprocess.run(["rsvg-convert", "-z", str(z), "-b", "white"], input=svg.encode(),
                         capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB")
    vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)"', svg[:800])
    vx, vy = (float(vb.group(1)), float(vb.group(2))) if vb else (0, 0)
    dr = ImageDraw.Draw(im)
    lista = tracos(svg)
    for n, (_, _, _, cx) in enumerate(lista):
        x0, y0, x1, y1 = [(v - o) * z for v, o in zip(cx, (vx, vy, vx, vy))]
        dr.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=(230, 0, 0))
        dr.text((x0 + 2, y0 + 1), str(n), fill=(0, 0, 230))
    os.makedirs("/tmp/limpeza", exist_ok=True)
    im.save(f"/tmp/limpeza/{codigo}.png")
    for n, (_, _, _, cx) in enumerate(lista):
        print(n, [round(v, 1) for v in cx])


def aplicar():
    corr = json.load(open(os.path.join(RAIZ, "dados", "correcoes-desenhos.json"), encoding="utf-8"))
    por_zip = {}
    for cod, c in corr.items():
        zp, arq = localizar(cod)
        por_zip.setdefault(zp, {})[arq] = (cod, c)
    for zp, arqs in por_zip.items():
        with zipfile.ZipFile(zp) as z:
            itens = [(i, z.read(i.filename)) for i in z.infolist()]
        novos = []
        for info, dados in itens:
            if info.filename in arqs:
                cod, c = arqs[info.filename]
                svg, n = limpar(dados.decode("utf-8"), c.get("remover", []))
                svg, v = abrir_vaos(svg, c.get("vaos", []))
                print(f"{cod}: {n} traço(s) removido(s), {v} vão(s) aberto(s)")
                dados = svg.encode("utf-8")
            novos.append((info, dados))
        tmp = zp + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for info, dados in novos:
                z.writestr(info, dados)
        os.replace(tmp, zp)


if __name__ == "__main__":
    if sys.argv[1] == "listar":
        for c in sys.argv[2:]:
            listar(c)
    else:
        aplicar()
