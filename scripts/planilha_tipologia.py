"""Gera dados/tipologia-atual-x-sugerida.xlsx a partir de dados/tipologia-sugerida.json.

Uso: python3 scripts/planilha_tipologia.py
"""
import collections
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(RAIZ, "dados", "tipologia-sugerida.json"), encoding="utf-8"))
linhas, resumo, red = d["linhas"], d["resumo"], d["reducaoAlternativa"]
red_pct = f"{int(red * 100)}%"

LARANJA = "F88C22"
CAB = Font(bold=True, color="FFFFFF")
CAB_FUNDO = PatternFill("solid", fgColor="3D3D3D")
CORES = {
    "Igual": "E2F0D9",
    "Precisa de espaço maior": "FCE4D6",
    "Economiza espaço": "DDEBF7",
    "Muda orientação": "FFF2CC",
}
ORDEM = ["1-6", "1-4", "1-3 H", "1-3 V", "1-2 H", "1-2 V", "1-1"]

wb = Workbook()

# --- Como ler -------------------------------------------------------------
ws = wb.active
ws.title = "Como ler"
texto = [
    ("Tipologia da página: atual × sugerida", True),
    ("Alplan & Ciazzani · Catálogo técnico · 26/11/2026", False),
    ("", False),
    ("Tipologia atual: lida do catalogo.ciazzani.com.br em 26/11/2026 (727 perfis). Os tabelados aparecem como TABELADO.", False),
    ("Tipologia sugerida: calculada pelo motor de paginação a partir do tamanho real de cada desenho padronizado.", False),
    ("Regra: a tipologia que coloca mais perfis por página onde o desenho cabe, descontando 16 mm para código e peso e 6 mm para a descrição.", False),
    ("", False),
    ("Duas colunas de sugestão:", True),
    ("• Sugerida (escala real): o desenho sai no tamanho do catálogo do fabricante, sem reduzir (regra combinada até agora).", False),
    (f"• Sugerida (reduzindo até {red_pct}): o desenho pode ser reduzido até {red_pct} do tamanho real para caber num espaço menor.", False),
    ("  O catálogo antigo reduzia os desenhos sem limite para caberem no espaço escolhido.", False),
    ("", False),
    ("Comparação (coluna \"Comparação\", sobre a sugestão em escala real):", True),
    ("• Igual: a tipologia atual já serve.", False),
    ("• Precisa de espaço maior: em escala real o desenho não cabe na tipologia atual. A coluna \"Redução para manter a atual\" mostra quanto seria preciso reduzir.", False),
    ("• Economiza espaço: o desenho cabe numa tipologia com mais perfis por página.", False),
    ("• Muda orientação: mesma quantidade por página, outra orientação (ex.: 1-3 H → 1-3 V).", False),
    ("• Sem tipologia atual: perfil que não aparece no catálogo antigo.", False),
    ("• Sem desenho: perfil sem desenho processável (ver panorama).", False),
    ("", False),
    ("Alertas: \"desenho maior que a página inteira\" = precisa reduzir de qualquer forma; \"escala reduzida no catálogo de origem\" = o fabricante já desenhou menor que o real.", False),
]
for i, (t, negrito) in enumerate(texto, 1):
    c = ws.cell(row=i, column=1, value=t)
    c.font = Font(bold=negrito, size=14 if i == 1 else 11, color=LARANJA if i == 1 else None)
ws.column_dimensions["A"].width = 140

# --- Resumo ---------------------------------------------------------------
ws = wb.create_sheet("Resumo")
pc = resumo["paginasComparaveis"]
ws.append(["Páginas do catálogo (mesmos perfis, só os que têm tipologia atual e desenho)"])
ws["A1"].font = Font(bold=True, size=12)
ws.append(["Cenário", "Páginas", "Diferença × hoje"])
for nome, n in [
    ("Hoje (tipologia atual)", pc["atual"]),
    ("Sugerida em escala real", pc["sugerida"]),
    (f"Sugerida reduzindo até {red_pct}", pc["sugeridaReduzida"]),
]:
    ws.append([nome, n, f"{(n - pc['atual']) / pc['atual']:+.0%}" if nome.startswith("Sug") else ""])
ws.append([f"Perfis considerados: {pc['perfis']}. Estimativa agrupando por aplicação + linha, na ordem do cadastro."])
ws.append([])

ws.append(["Comparação (escala real)", "Perfis"])
inicio = ws.max_row
for k, v in collections.Counter(l["comparacao"] for l in linhas).most_common():
    ws.append([k, v])
ws.append([])

comp = [l for l in linhas if l["atual"] in ORDEM and l["sugerida"] in ORDEM]
iguais_red = sum(1 for l in comp if l["sugeridaReduzida"] == l["atual"])
ws.append([f"Reduzindo até {red_pct}: {iguais_red} de {len(comp)} perfis mantêm a tipologia atual."])
ws.append([])

ws.append(["Atual ↓ / Sugerida em escala real →"] + ORDEM + ["Total"])
cab_matriz = ws.max_row
mat = collections.Counter((l["atual"], l["sugerida"]) for l in comp)
for a in ORDEM:
    linha = [mat[(a, s)] or None for s in ORDEM]
    ws.append([a] + linha + [sum(x or 0 for x in linha)])
for r in (2, inicio, cab_matriz):
    for c in ws[r]:
        if c.value is not None:
            c.font, c.fill = CAB, CAB_FUNDO
for i, a in enumerate(ORDEM):
    c = ws.cell(row=cab_matriz + 1 + i, column=2 + i)
    c.fill = PatternFill("solid", fgColor=CORES["Igual"])
ws.column_dimensions["A"].width = 44
for col in range(2, 10):
    ws.column_dimensions[get_column_letter(col)].width = 11

# --- Comparação -----------------------------------------------------------
ws = wb.create_sheet("Comparação")
cab = [
    "Código", "Descrição", "Aplicação", "Linha", "Situação", "Pacote do desenho",
    "Largura do desenho (mm)", "Altura do desenho (mm)",
    "Tipologia atual", "Sugerida (escala real)", "Comparação",
    "Redução para manter a atual", f"Sugerida (reduzindo até {red_pct})", "Alerta",
]
ws.append(cab)
for c in ws[1]:
    c.font, c.fill = CAB, CAB_FUNDO
    c.alignment = Alignment(wrap_text=True, vertical="center")
ordem_comp = {"Precisa de espaço maior": 0, "Economiza espaço": 1, "Muda orientação": 2, "Igual": 3,
              "Sem tipologia atual": 4, "Sem desenho": 5, "Tabelado": 6}
for l in sorted(linhas, key=lambda l: (ordem_comp.get(l["comparacao"], 9), l["aplicacao"], l["linha"], l["codigo"])):
    ws.append([
        l["codigo"], l["descricao"], l["aplicacao"], l["linha"], l["situacao"].replace("_", " "), l["pacote"],
        l["largura_mm"], l["altura_mm"], l["atual"], l["sugerida"], l["comparacao"],
        (l["reducaoParaManter"] / 100) if l["reducaoParaManter"] else None,
        l["sugeridaReduzida"], l["alerta"],
    ])
    cor = CORES.get(l["comparacao"])
    if cor:
        ws.cell(row=ws.max_row, column=11).fill = PatternFill("solid", fgColor=cor)
    ws.cell(row=ws.max_row, column=12).number_format = "0%"
larguras = [12, 34, 20, 26, 12, 22, 12, 12, 11, 13, 24, 13, 15, 40]
for i, w in enumerate(larguras, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[1].height = 45
ws.freeze_panes = "B2"
ws.auto_filter.ref = ws.dimensions

wb.active = 1
destino = os.path.join(RAIZ, "dados", "tipologia-atual-x-sugerida.xlsx")
wb.save(destino)
print("→", os.path.relpath(destino, RAIZ))
