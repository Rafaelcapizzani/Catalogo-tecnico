"""Mede o tamanho real (mm) de cada desenho padronizado.

Lê os SVGs de desenhos/pacotes/*-vetor.zip (largura/altura em pt, escala do
catálogo) e grava dados/medidas-desenhos.json: código Alplan → pacote, arquivo,
largura e altura em mm, e um alerta quando o desenho parece estar em escala
reduzida no catálogo de origem (maior cota maior que o próprio desenho).

Uso: python3 scripts/medir_desenhos.py
"""
import glob
import json
import os
import re
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PT_MM = 25.4 / 72

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


def numero(v):
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def main():
    medidas = {}
    for pacote in reversed(PRIORIDADE):  # os prioritários sobrescrevem
        caminho = os.path.join(RAIZ, "desenhos", "pacotes", f"{pacote}-vetor.zip")
        if not os.path.exists(caminho):
            continue
        with zipfile.ZipFile(caminho) as z:
            cotas = {}
            for n in z.namelist():
                if n.endswith("_cotas.json"):
                    pasta = os.path.dirname(n)
                    for chave, info in json.loads(z.read(n)).items():
                        cotas[(pasta, chave)] = info
            for n in z.namelist():
                if not n.endswith(".svg"):
                    continue
                cab = z.read(n)[:600].decode("utf-8", "ignore")
                m = re.search(r'width="([\d.]+)(?:pt)?" height="([\d.]+)(?:pt)?"', cab)
                if not m:
                    continue
                largura, altura = float(m[1]) * PT_MM, float(m[2]) * PT_MM
                pasta, arq = os.path.dirname(n), os.path.basename(n)[:-4]
                codigo = arq.split("_")[0]
                info = cotas.get((pasta, arq)) or cotas.get((pasta, codigo)) or {}
                alerta = ""
                hs = [numero(c["valor"]) for c in info.get("cotas", []) if c.get("direcao") == "horizontal"]
                vs = [numero(c["valor"]) for c in info.get("cotas", []) if c.get("direcao") != "horizontal"]
                hs, vs = [x for x in hs if x], [x for x in vs if x]
                if (hs and max(hs) > largura * 1.1) or (vs and max(vs) > altura * 1.1):
                    alerta = "desenho em escala reduzida no catálogo de origem"
                medidas[codigo] = {
                    "pacote": pacote,
                    "arquivo": n,
                    "largura_mm": round(largura, 1),
                    "altura_mm": round(altura, 1),
                    "alerta": alerta,
                }
    # Reserva: desenhos que só existem na base do protótipo (catalogo-base-de-dados.zip)
    base = os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip")
    if os.path.exists(base):
        with zipfile.ZipFile(base) as z:
            for n in z.namelist():
                if not (n.startswith("desenhos/") and n.endswith(".svg")):
                    continue
                codigo = os.path.basename(n)[:-4]
                if codigo in medidas:
                    continue
                cab = z.read(n)[:600].decode("utf-8", "ignore")
                m = re.search(r'width="([\d.]+)(?:pt)?" height="([\d.]+)(?:pt)?"', cab)
                if m:
                    medidas[codigo] = {
                        "pacote": "base-prototipo",
                        "arquivo": n,
                        "largura_mm": round(float(m[1]) * PT_MM, 1),
                        "altura_mm": round(float(m[2]) * PT_MM, 1),
                        "alerta": "",
                    }
    destino = os.path.join(RAIZ, "dados", "medidas-desenhos.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(medidas.items())), f, ensure_ascii=False, indent=1)
    print(f"{len(medidas)} desenhos medidos → {os.path.relpath(destino, RAIZ)}")


if __name__ == "__main__":
    main()
