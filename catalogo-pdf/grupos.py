"""Grupo de cada perfil dentro da linha, pela descrição (decisão do cliente, 26/11/2026).

Ordem: 2 planos, 3 planos, 4 planos, 5 planos, montante, mão de amigo, demais.
"Correr N folhas" conta como N planos. "Mão de amigo" vence "montante"
(ex.: "Montante mão de amigo" fica em mão de amigo).
"""
import re
import unicodedata

ROTULOS = ["2 planos", "3 planos", "4 planos", "5 planos", "montante", "mão de amigo", "demais"]


def _simples(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t)


def grupo(descricao):
    d = _simples(descricao)
    m = re.search(r"(\d)\s*(folhas|planos)", d)
    if m and m.group(1) in "2345":
        return int(m.group(1)) - 2  # 0..3
    if "mao de amigo" in d:
        return 5
    if d.startswith("montante"):
        return 4
    return 6
