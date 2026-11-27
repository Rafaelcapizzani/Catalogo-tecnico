"""Classifica o sistema (Correr, Maxim-ar, Giro, Complementos) de todos os perfis.

Regra do cliente (27/11/2026): o sistema vem antes de tudo e os sistemas não se
misturam na página; por último os complementos. Vale para todas as linhas.

Fontes, em ordem de prioridade:
  1. dados/sistemas-manuais.json  → decisão do cliente ou catálogo do fabricante
     (a Gold veio do catálogo Alcoa Gold IV / Gold III).
  2. regra pela descrição (já com as correções de dados/descricoes-corrigidas.json):
       baguete, porta palheta, complemento, clic, tampa, pingadeira, arremate → Complementos
       giro                                → Giro
       max / maxim-ar / "folha 45"         → Maxim-ar (corte a 45° é da folha de maxim-ar)
       correr, N folhas/planos, trilho,
       mão de amigo                        → Correr
  3. sem pista → "Outros" (entra antes dos Complementos) e vai para a planilha
     para o cliente definir.

Só as linhas de esquadria (LINHAS_ESQUADRIA) são divididas por sistema; box,
divisórias, pele de vidro, guarda-corpo, portão etc. seguem só grupo e peça.

Saídas: dados/sistemas.json (usado por catalogo-pdf/gerar.py) e
        dados/sistemas-por-perfil.xlsx (para o cliente conferir).
Uso: python3 scripts/classificar_sistemas.py /tmp/cat/perfis.json
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDEM = ["Correr", "Maxim-ar", "Giro", "Outros", "Complementos"]
# Linhas de esquadria (janelas e portas): só estas são divididas por sistema.
# Box, divisórias, pele de vidro, guarda-corpo, portão etc. seguem só por grupo/peça.
LINHAS_ESQUADRIA = {
    "Gold", "Suprema", "Suprema Integrada (persiana)", "Linha 25", "Linha 25 (ASA)", "Linha 30",
    "Linha 30 (ASA)", "Linha 42", "SP20", "Sistema Modular", "Euroshow Giro-Oscilo", "Linha MB (correr)",
    "Luxxor 2.5", "MG32", "Linha SI", "Mega 32 Lite (ASA)", "Persiana integrada",
}


def simples(t):
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower().strip()


def pela_descricao(desc):
    d = simples(desc)
    if not d:
        return None
    if re.search(r"baguete|porta palheta|^complemento|^clic|^tampa|pingadeira|arremate|acabamento", d) and "sem baguete" not in d:
        return "Complementos"
    if "giro" in d:
        return "Giro"
    if re.search(r"maxim|\bmax\b|folha 45\b|\b45$", d):
        return "Maxim-ar"
    if re.search(r"correr|\d\s*(folhas|planos)|trilho|mao de amigo", d):
        return "Correr"
    return None


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cat/perfis.json"
    P = json.load(open(base, encoding="utf-8"))
    P = P if isinstance(P, list) else P.get("perfis", list(P.values()))
    P = [p for p in P if isinstance(p, dict) and not p.get("tabelado")]
    corr = json.load(open(os.path.join(RAIZ, "dados", "descricoes-corrigidas.json"), encoding="utf-8"))
    manual = {k: v for k, v in json.load(open(os.path.join(RAIZ, "dados", "sistemas-manuais.json"), encoding="utf-8")).items() if not k.startswith("_")}

    por_linha = defaultdict(list)
    for p in P:
        desc = corr.get(p["codigo"], p.get("descricao"))
        if p["codigo"] in manual:
            sis, fonte = manual[p["codigo"]], "catálogo do fabricante / cliente"
        else:
            sis = pela_descricao(desc)
            fonte = "regra pela descrição" if sis else "a definir"
        por_linha[p.get("linha")].append((p["codigo"], desc, sis, fonte))

    saida = {"_ordem": ORDEM,
             "_fonte": "Gerado por scripts/classificar_sistemas.py (manuais em dados/sistemas-manuais.json + regra pela descrição)."}
    linhas_planilha = []
    resumo = {}
    for linha, itens in por_linha.items():
        esquadria = linha in LINHAS_ESQUADRIA
        cont = Counter()
        for cod, desc, sis, fonte in itens:
            if not esquadria:
                linhas_planilha.append((linha, cod, desc or "", "(linha sem divisão por sistema)", ""))
                continue
            sis = sis or "Outros"
            saida[cod] = sis
            cont[sis] += 1
            linhas_planilha.append((linha, cod, desc or "", sis, fonte))
        if esquadria:
            resumo[linha] = dict(cont)
    json.dump(saida, open(os.path.join(RAIZ, "dados", "sistemas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Sistema por perfil"
    ws.append(["Linha", "Código", "Descrição", "Sistema", "De onde veio"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F4396")
    amarelo = PatternFill("solid", fgColor="FFF2CC")
    for r in sorted(linhas_planilha, key=lambda r: (r[0] or "", ORDEM.index(r[3]) if r[3] in ORDEM else 9, r[1])):
        ws.append(list(r))
        if r[4] in ("a definir", "regra pela descrição"):
            for c in ws[ws.max_row]:
                c.fill = amarelo if r[4] == "a definir" else PatternFill()
    for col, w in zip("ABCDE", (28, 12, 52, 22, 30)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(os.path.join(RAIZ, "dados", "sistemas-por-perfil.xlsx"))
    for l, c in sorted(resumo.items(), key=lambda x: -sum(x[1].values())):
        print(f"{l:32s} {c}")


if __name__ == "__main__":
    main()
