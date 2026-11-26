"""Sugere descrições padronizadas para todos os perfis e gera a planilha para o cliente aprovar.

Regras (pedido do cliente em 26/11/2026):
  - "correr N folhas" / "N folhas" / "N Planos" → "N planos"
  - acentuação (mao → mão, reforco → reforço, vergalhao → vergalhão ...)
  - erros de digitação conhecidos (Laterial pTirlho → Lateral p/ trilho)
  - só a primeira letra maiúscula; espaços duplos removidos
  - descrição vazia é sinalizada

Saída: dados/descricoes-atual-x-sugerida.xlsx e dados/descricoes-sugeridas.json
Uso: python3 scripts/descricoes_padronizadas.py
"""
import json
import os
import re
import sys
import zipfile

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "catalogo-pdf"))
from grupos import ROTULOS, grupo  # noqa: E402

ACENTOS = {
    "mao": "mão", "reforco": "reforço", "vergalhao": "vergalhão", "corrimao": "corrimão",
    "conexao": "conexão", "movel": "móvel", "chapeu": "chapéu", "sanitario": "sanitário",
    "vedacao": "vedação", "femea": "fêmea", "rodape": "rodapé", "uniao": "união",
    "juncao": "junção", "intermediario": "intermediário", "intermediaria": "intermediária",
    "maximar": "maxim-ar", "laterial": "lateral", "ptirlho": "p/ trilho",
}


def sugerir(desc):
    if not (desc or "").strip():
        return "", ["sem descrição — completar no cadastro"]
    regras = []
    s = re.sub(r"\s+", " ", desc.strip())
    novo = re.sub(r"\b(?:de\s+)?correr\s+(\d)\s+folhas\b", r"\1 planos", s, flags=re.I)
    novo = re.sub(r"\b(\d)\s+(folhas|planos)\b", r"\1 planos", novo, flags=re.I)
    if novo != s:
        regras.append("folhas → planos")
        s = novo

    def troca(m):
        w = m.group(0)
        r = ACENTOS.get(w.lower())
        return r if r else w

    novo = re.sub(r"[A-Za-z]+", troca, s)
    if novo != s:
        regras.append("acentuação/digitação")
        s = novo
    novo = s[:1].upper() + s[1:].lower() if s else s
    # mantém siglas curtas em maiúsculas (ex.: U, T, H, AP, BX)
    novo = re.sub(r"\b([a-z]{1,2})\b", lambda m: m.group(1).upper() if m.group(1) in {"u", "t", "h", "ap", "bx", "cg", "fa", "ts", "al"} else m.group(1), novo)
    for nome in ("Stanley", "Transpace", "Infinity", "Fancoy", "Muxarabi"):
        novo = re.sub(rf"\b{nome.lower()}\b", nome, novo)
    novo = novo.replace("Mm", "mm")
    if novo != s:
        regras.append("maiúsculas")
        s = novo
    return s, regras


def main():
    perfis = json.loads(zipfile.ZipFile(os.path.join(RAIZ, "dados", "catalogo-base-de-dados.zip")).read("perfis.json"))["perfis"]
    linhas = []
    for p in sorted(perfis, key=lambda p: (p["aplicacao"], p["linha"], p["codigo"])):
        sug, regras = sugerir(p.get("descricao"))
        linhas.append({
            "codigo": p["codigo"], "aplicacao": p["aplicacao"], "linha": p["linha"],
            "atual": p.get("descricao") or "", "sugerida": sug,
            "muda": sug != (p.get("descricao") or "") or not sug,
            "regras": ", ".join(regras), "grupo": ROTULOS[grupo(sug or p.get("descricao"))],
        })
    json.dump({l["codigo"]: l["sugerida"] for l in linhas}, open(os.path.join(RAIZ, "dados", "descricoes-sugeridas.json"), "w"),
              ensure_ascii=False, indent=1)

    wb = Workbook()
    ws = wb.active
    ws.title = "Como ler"
    for i, t in enumerate([
        "Descrições: atual × sugerida (26/11/2026)",
        "",
        "Regras: \"correr N folhas\" → \"N planos\"; acentuação (mão, reforço, vergalhão...); erros de digitação; só a 1ª letra maiúscula.",
        "Coluna \"Grupo no catálogo\": ordem dentro da linha — 2 planos, 3 planos, 4 planos, 5 planos, montante, mão de amigo, demais.",
        "Para aprovar: deixe \"Aprovar?\" em branco (aceita) ou escreva a descrição correta na coluna \"Correção do cliente\".",
        "A aba \"Mudanças\" só tem as linhas que mudam; \"Todas\" tem os 931 perfis.",
    ], 1):
        ws.cell(row=i, column=1, value=t).font = Font(bold=(i == 1), size=13 if i == 1 else 11)
    ws.column_dimensions["A"].width = 130
    cab = ["Código", "Aplicação", "Linha", "Descrição atual", "Descrição sugerida", "Regras", "Grupo no catálogo", "Correção do cliente"]
    for nome, filtro in [("Mudanças", lambda l: l["muda"]), ("Todas", lambda l: True)]:
        w = wb.create_sheet(nome)
        w.append(cab)
        for c in w[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="3D3D3D")
        for l in linhas:
            if filtro(l):
                w.append([l["codigo"], l["aplicacao"], l["linha"], l["atual"], l["sugerida"], l["regras"], l["grupo"], ""])
                if not l["sugerida"]:
                    w.cell(row=w.max_row, column=5).fill = PatternFill("solid", fgColor="FCE4D6")
        for i, larg in enumerate([12, 20, 26, 40, 40, 30, 16, 40], 1):
            w.column_dimensions[get_column_letter(i)].width = larg
        w.freeze_panes = "B2"
        w.auto_filter.ref = w.dimensions
    wb.active = 1
    wb.save(os.path.join(RAIZ, "dados", "descricoes-atual-x-sugerida.xlsx"))
    print(f"{sum(l['muda'] for l in linhas)} de {len(linhas)} descrições mudam; vazias: {sum(1 for l in linhas if not l['sugerida'])}")


if __name__ == "__main__":
    main()
