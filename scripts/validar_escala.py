"""Valida a escala de todos os desenhos padronizados pelas próprias cotas.

Para cada desenho com cota horizontal, renderiza o SVG e procura uma linha
horizontal de cota cujo comprimento bata com o valor da maior cota:
  razão ≈ 1,00 → desenho em tamanho real (1:1)
Também mede o espaço real ocupado (perfil + cotas) e compara com o tamanho
declarado no SVG (para detectar margem em branco).

Saída: dados/validacao-escala.json e um resumo na tela.
Uso: python3 scripts/validar_escala.py
"""
import io
import json
import os
import subprocess
import zipfile

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZOOM = 4  # px por pt
MM_PX = 25.4 / 72 / ZOOM


def render(svg_bytes):
    r = subprocess.run(["rsvg-convert", "-z", str(ZOOM), "-b", "white"], input=svg_bytes,
                       capture_output=True, check=True)
    return np.array(Image.open(io.BytesIO(r.stdout)).convert("L")) < 160


def vãos(linha, tolerancia_px):
    """Agrupa pixels de tinta de uma linha em trechos, aceitando falhas (número no meio da cota)."""
    xs = np.where(linha)[0]
    if len(xs) == 0:
        return []
    cortes = np.where(np.diff(xs) > tolerancia_px)[0]
    ini = np.concatenate([[xs[0]], xs[cortes + 1]])
    fim = np.concatenate([xs[cortes], [xs[-1]]])
    return list(zip(ini, fim))


def razao_cota(img, valor_mm):
    melhor = None
    tol = int(12 / MM_PX)  # até 12 mm de falha (número no meio da linha de cota)
    for y in range(img.shape[0]):
        for a, b in vãos(img[y], tol):
            s = (b - a) * MM_PX
            r = s / valor_mm
            if melhor is None or abs(r - 1) < abs(melhor - 1):
                melhor = r
    return melhor


def main():
    medidas = json.load(open(os.path.join(RAIZ, "dados", "medidas-desenhos.json"), encoding="utf-8"))
    zips = {}
    resultado = {}
    for cod, m in medidas.items():
        zp = (os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip") if m["pacote"] == "base-prototipo"
              else os.path.join(RAIZ, "desenhos", "pacotes", f"{m['pacote']}-vetor.zip"))
        z = zips.setdefault(zp, zipfile.ZipFile(zp))
        svg = z.read(m["arquivo"])
        img = render(svg)
        ys, xs = np.where(img)
        tinta = ((xs.max() - xs.min()) * MM_PX, (ys.max() - ys.min()) * MM_PX) if len(xs) else (0, 0)
        # maior cota horizontal (do _cotas.json do pacote)
        valor = None
        pasta = os.path.dirname(m["arquivo"])
        cj = os.path.join(pasta, "_cotas.json")
        if cj in z.namelist():
            info = json.loads(z.read(cj)).get(os.path.basename(m["arquivo"])[:-4], {})
            vs = []
            for c in info.get("cotas", []):
                if c.get("direcao") == "horizontal":
                    try:
                        vs.append(float(str(c["valor"]).replace(",", ".")))
                    except ValueError:
                        pass
            valor = max(vs) if vs else None
        razao = razao_cota(img, valor) if valor and valor >= 10 else None
        resultado[cod] = {
            "svg_mm": m.get("svg_mm", [m["largura_mm"], m["altura_mm"]]),
            "tinta_mm": [round(tinta[0], 1), round(tinta[1], 1)],
            "maior_cota_h": valor,
            "razao_linha_cota": round(razao, 3) if razao else None,
        }
    json.dump(resultado, open(os.path.join(RAIZ, "dados", "validacao-escala.json"), "w"), indent=1)

    rs = [v["razao_linha_cota"] for v in resultado.values() if v["razao_linha_cota"]]
    rs = np.array(rs)
    print(f"desenhos: {len(resultado)}; com cota horizontal ≥ 10 mm verificável: {len(rs)}")
    for a, b, rot in [(0.97, 1.03, "1:1 (±3%)"), (0.9, 0.97, "90–97%"), (1.03, 1.1, "103–110%"),
                      (0.0, 0.9, "< 90%"), (1.1, 9, "> 110%")]:
        print(f"  {rot:12s} {((rs >= a) & (rs < b)).sum()}")
    margem = [max(v["svg_mm"][0] - v["tinta_mm"][0], v["svg_mm"][1] - v["tinta_mm"][1]) for v in resultado.values()]
    print(f"margem em branco no SVG: mediana {np.median(margem):.1f} mm, máx {max(margem):.1f} mm")


if __name__ == "__main__":
    main()
