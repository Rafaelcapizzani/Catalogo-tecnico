"""Gera um catálogo técnico em PDF (A4) para uma ou mais linhas.

Usa o motor de paginação (motor-paginacao/paginacao.ts, via layout.ts) e os
desenhos padronizados (desenhos/pacotes/*-vetor.zip ou a base do protótipo).

Uso:
  python3 catalogo-pdf/gerar.py --linhas "Gold" --reducao 1 --saida catalogo-pdf/saida/gold-escala-real.pdf
  python3 catalogo-pdf/gerar.py --linhas "Linha 25" "Linha 25 (ASA)" --reducao 0.8 --titulo "Linha 25" ...

--reducao 1   → escala real (o desenho só é reduzido se não couber nem na página inteira)
--reducao 0.8 → o desenho pode ser reduzido até 80% para caber num espaço menor
--atual       → usa a tipologia do catálogo antigo e reduz o desenho o quanto for preciso (referência)

As fontes (Noir Pro e Bahnschrift) não são versionadas: coloque os .ttf em catalogo-pdf/fontes/.
"""
import argparse
import base64
import html
import io
import json
import os
import re
import subprocess
import tempfile
import zipfile

import qrcode
import qrcode.image.svg

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AQUI = os.path.join(RAIZ, "catalogo-pdf")

# Área útil do motor (mm) e posição dela na folha A4
AREA_L, AREA_A = 189, 250
MARGEM_X, TOPO = (210 - AREA_L) / 2, 24
RES_TOPO, RES_BASE, RES_LAT = 16, 6, 3  # iguais ao CONFIG do motor

URL_BASE = "https://www.alplanaluminio.com.br/catalogo/p/"  # provisório até o domínio final
RODAPE_CONTATO = "WhatsApp (número a informar)  ·  (12) 3901-4255  ·  Rua Dinamarca, 201"
RODAPE_SITES = "alplanaluminio.com.br  ·  ciazzani.com.br"


def carregar_perfis(caminho_base_zip):
    with zipfile.ZipFile(caminho_base_zip) as z:
        return {p["codigo"]: p for p in json.loads(z.read("perfis.json"))["perfis"]}


def enquadrar(svg, recorte):
    """Troca o viewBox/tamanho do SVG para mostrar só o desenho (sem margem em branco)."""
    txt = svg.decode("utf-8")
    x, y, w, h = recorte
    cab_fim = txt.index(">", txt.index("<svg"))
    cab = txt[:cab_fim]
    cab = re.sub(r'\s(width|height|viewBox)="[^"]*"', "", cab)
    cab += f' width="{w}" height="{h}" viewBox="{x} {y} {w} {h}" preserveAspectRatio="xMidYMid meet"'
    return (cab + txt[cab_fim:]).encode("utf-8")


def svg_do_desenho(medida):
    if medida["pacote"] == "base-prototipo":
        zp = os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip")
    else:
        zp = os.path.join(RAIZ, "desenhos", "pacotes", f"{medida['pacote']}-vetor.zip")
    with zipfile.ZipFile(zp) as z:
        return enquadrar(z.read(medida["arquivo"]), medida["recorte"])


def qr_svg(texto):
    img = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=0)
    buf = io.BytesIO()
    img.save(buf)
    return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()


def peso_br(v):
    return f"{v:.3f}".replace(".", ",") if v else ""


def montar(args):
    perfis = carregar_perfis(os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip"))
    medidas = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))
    atual = json.load(open(os.path.join(RAIZ, "dados", "tipologia-atual.json"), encoding="utf-8"))
    fora = json.load(open(os.path.join(RAIZ, "dados", "fora-do-catalogo.json"), encoding="utf-8"))

    itens = []
    for linha in args.linhas:
        # ordem final (tipologia, tamanho, código) é aplicada pelo motor (ordenarItens)
        sel = [p for p in perfis.values() if p["linha"] == linha and not p["tabelado"] and p["codigo"] not in fora]
        for p in sel:
            m = medidas.get(p["codigo"])
            itens.append({
                "codigo": p["codigo"],
                "familia": linha,
                "larguraMm": m["largura_mm"] if m else 0,
                "alturaMm": m["altura_mm"] if m else 0,
                "tipologia": atual.get(p["codigo"]) if args.atual and atual.get(p["codigo"], "TABELADO") != "TABELADO" else None,
            })

    with tempfile.TemporaryDirectory() as tmp:
        ent, sai = os.path.join(tmp, "e.json"), os.path.join(tmp, "s.json")
        json.dump({"reducaoMaxima": args.reducao, "itens": itens}, open(ent, "w"))
        subprocess.run(["node", "--experimental-strip-types", "--no-warnings",
                        os.path.join(AQUI, "layout.ts"), ent, sai], check=True)
        paginas = json.load(open(sai))

    logo = "data:image/svg+xml;base64," + base64.b64encode(
        open(os.path.join(AQUI, "marca", "logo.svg"), "rb").read()).decode()
    fontes = os.path.join(AQUI, "fontes")
    if args.atual:
        rotulo_escala = "Tipologia de hoje (desenho reduzido para caber)"
    else:
        rotulo_escala = "Escala real" if args.reducao >= 1 else f"Redução permitida até {int(args.reducao * 100)}%"

    partes = [f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><style>
@font-face {{ font-family: 'Noir Pro'; src: url('file://{fontes}/noir-pro.ttf'); }}
@font-face {{ font-family: 'Bahnschrift'; src: url('file://{fontes}/bahnschrift.ttf'); font-weight: 300 700; }}
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Bahnschrift', sans-serif; color: #3d3d3d; }}
.pag {{ width: 210mm; height: 297mm; position: relative; page-break-after: always; overflow: hidden; }}
.cab {{ position: absolute; left: {MARGEM_X}mm; right: {MARGEM_X}mm; top: 8mm; height: 13mm;
        display: flex; align-items: center; justify-content: space-between; border-bottom: 0.3mm solid #2F4396; }}
.cab img {{ height: 10mm; }}
.cab .tit {{ font-family: 'Noir Pro'; font-size: 17pt; color: #2F4396; text-align: right; line-height: 1; }}
.cab .tit small {{ display: block; font-family: 'Bahnschrift'; font-size: 7.5pt; color: #F88C22; letter-spacing: .3pt; margin-top: 1.2mm; }}
.area {{ position: absolute; left: {MARGEM_X}mm; top: {TOPO}mm; width: {AREA_L}mm; height: {AREA_A}mm; }}
.esp {{ position: absolute; border: 0.15mm solid #c9c9c9; margin: -0.075mm; }}
.esp .cod {{ position: absolute; left: 2.5mm; top: 2mm; font-family: 'Noir Pro'; font-size: 13pt; color: #2F4396; }}
.esp .peso {{ position: absolute; left: 2.5mm; top: 8.6mm; font-size: 8pt; }}
.esp .sit {{ position: absolute; right: 2.5mm; top: 2.6mm; font-size: 7pt; color: #fff; background: #F88C22; padding: .4mm 1.5mm; border-radius: .8mm; }}
.esp .esc {{ position: absolute; right: 2.5mm; bottom: 1.6mm; font-size: 6.5pt; color: #9a9a9a; }}
.esp .desc {{ position: absolute; left: 2.5mm; right: 14mm; bottom: 1.6mm; font-size: 7.5pt; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.esp img.des {{ position: absolute; }}
.esp .vazio {{ position: absolute; left: 0; right: 0; top: 45%; text-align: center; font-size: 8pt; color: #9a9a9a; }}
.rod {{ position: absolute; left: {MARGEM_X}mm; right: {MARGEM_X}mm; bottom: 7mm; height: 15mm; border-top: 0.3mm solid #2F4396;
        display: flex; align-items: center; justify-content: space-between; font-size: 7.5pt; }}
.rod .txt div + div {{ margin-top: 1mm; }}
.rod .sites {{ color: #2F4396; font-weight: 600; }}
.rod .dir {{ display: flex; align-items: center; gap: 3mm; text-align: right; }}
.rod .dir img {{ width: 12mm; height: 12mm; }}
.rod .num {{ font-family: 'Noir Pro'; font-size: 11pt; color: #F88C22; }}
.capa {{ display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }}
.capa img {{ width: 120mm; }}
.capa h1 {{ font-family: 'Noir Pro'; font-weight: normal; font-size: 30pt; color: #2F4396; margin-top: 18mm; }}
.capa h2 {{ font-weight: 400; font-size: 13pt; color: #F88C22; margin-top: 4mm; }}
.capa p {{ font-size: 9pt; color: #777; margin-top: 30mm; max-width: 140mm; line-height: 1.5; }}
.capa .barra {{ position: absolute; left: 0; right: 0; bottom: 0; height: 9mm; background: linear-gradient(90deg, #0779B3, #2F4396); }}
</style></head><body>"""]

    n_perfis = len(itens)
    partes.append(f"""<div class="pag capa"><img src="{logo}">
<h1>Catálogo técnico · {html.escape(args.titulo)}</h1>
<h2>{rotulo_escala}</h2>
<p>Amostra para avaliação ({n_perfis} perfis, {len(paginas)} páginas). Dimensões em milímetros.
Desenhos padronizados a partir dos catálogos dos fabricantes. Barras de 6 m.</p>
<div class="barra"></div></div>""")

    for np_, pag in enumerate(paginas, 1):
        espacos = []
        for e in pag["espacos"]:
            p = perfis[e["codigo"]]
            m = medidas.get(e["codigo"])
            corpo = ""
            esc_txt = ""
            if m:
                aw = e["largura"] - 2 * RES_LAT
                ah = e["altura"] - RES_TOPO - RES_BASE
                escala = min(1.0, aw / m["largura_mm"], ah / m["altura_mm"])
                w, h = m["largura_mm"] * escala, m["altura_mm"] * escala
                x = RES_LAT + (aw - w) / 2
                y = RES_TOPO + (ah - h) / 2
                src = "data:image/svg+xml;base64," + base64.b64encode(svg_do_desenho(m)).decode()
                corpo = (f'<img class="des" src="{src}" style="left:{x:.2f}mm;top:{y:.2f}mm;'
                         f'width:{w:.2f}mm;height:{h:.2f}mm">')
                esc_txt = "escala real" if escala >= 0.995 else f"reduzido a {round(escala * 100)}%"
            else:
                corpo = '<div class="vazio">Desenho sob consulta</div>'
            sit = '<div class="sit">Sob consulta</div>' if p["situacao"] != "ativo" else ""
            peso = peso_br(p.get("peso_kg_m"))
            espacos.append(
                f'<div class="esp" style="left:{e["x"]:.2f}mm;top:{e["y"]:.2f}mm;width:{e["largura"]:.2f}mm;height:{e["altura"]:.2f}mm">'
                f'{corpo}<div class="cod">{html.escape(p["codigo"])}</div>'
                f'<div class="peso">{peso + " kg/m" if peso else ""}</div>{sit}'
                f'<div class="desc">{html.escape(p.get("descricao") or "")}</div>'
                f'<div class="esc">{esc_txt}</div></div>')
        qr = qr_svg(URL_BASE + "+".join(pag["codigos"]))
        partes.append(f"""<div class="pag">
<div class="cab"><img src="{logo}"><div class="tit">{html.escape(pag["titulo"])}<small>CATÁLOGO TÉCNICO · {rotulo_escala.upper()}</small></div></div>
<div class="area">{''.join(espacos)}</div>
<div class="rod"><div class="txt"><div>{RODAPE_CONTATO}</div><div class="sites">{RODAPE_SITES}</div>
<div>Dimensões em milímetros · pesos teóricos · barras de 6 m</div></div>
<div class="dir"><div>Cor, quantidade e<br>orçamento no site</div><img src="{qr}"><div class="num">{np_ + 1}</div></div></div>
</div>""")

    partes.append("</body></html>")
    return "".join(partes), len(paginas), n_perfis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--linhas", nargs="+", required=True)
    ap.add_argument("--titulo")
    ap.add_argument("--reducao", type=float, default=1.0)
    ap.add_argument("--atual", action="store_true", help="usa a tipologia do catálogo antigo (referência)")
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()
    args.titulo = args.titulo or args.linhas[0]

    doc, npag, nperf = montar(args)
    os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
    html_path = os.path.abspath(args.saida)[:-4] + ".html"
    open(html_path, "w", encoding="utf-8").write(doc)
    subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", f"--print-to-pdf={os.path.abspath(args.saida)}",
                    "file://" + html_path], check=True, capture_output=True)
    print(f"{args.saida}: {nperf} perfis, {npag} páginas + capa")


if __name__ == "__main__":
    main()
