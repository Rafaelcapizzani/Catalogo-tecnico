"""Grupo de cada perfil dentro da linha, pela descrição (decisão do cliente, 26/11/2026).

Ordem: 2 planos, 3 planos, 4 planos, 5 planos, montante, mão de amigo, sem baguete (27/11), demais.
"Correr N folhas" conta como N planos. "Mão de amigo" vence "montante"
(ex.: "Montante mão de amigo" fica em mão de amigo).
"""
import re
import unicodedata

# Ordem da peça dentro de cada grupo (proposta 27/11/2026, a confirmar com o cliente).
# A primeira expressão que casar com a descrição decide; o que não casar vai para o fim.
PECAS = [
    ("marco superior", r"marco superior"),
    ("marco inferior", r"marco inferior"),
    ("marco lateral", r"marco lateral"),
    ("marco bandeira / peitoril", r"marco (bandeira|peitoril)"),
    ("trilho superior", r"trilho superior"),
    ("trilho inferior", r"trilho inferior"),
    ("lateral do trilho", r"later\w* p\.?\s*t\w*lho|lateral (do |p/? ?)?trilho"),
    ("travessa bandeira", r"travessa bandeira"),
    ("travessa peitoril", r"travessa peitoril"),
    ("montante central", r"montante central"),
    ("montante lateral", r"montante lateral"),
    ("montante da folha", r"montante (da )?folha"),
    ("montante travessa", r"montante (max )?travessa"),
    ("montante", r"^montante"),
    ("coluna", r"^coluna"),
    ("marco de giro", r"^marco de giro"),
    ("marco max", r"^marco max"),
    ("marco", r"^marco"),
    ("travessa superior da folha", r"travessa superior"),
    ("travessa central da folha", r"travessa central"),
    ("travessa inferior da folha", r"travessa inferior"),
    ("travessa", r"^travessa"),
    ("complemento", r"^complemento"),
    ("mata junta", r"mata ?junta"),
    ("inversor", r"^inversor"),
    ("baguete", r"^baguete"),
    ("porta palheta", r"porta palheta"),
    ("tampa", r"^tampa"),
    ("pingadeira", r"^pingadeira"),
    ("clic", r"^clic"),
]


def peca(descricao):
    d = _simples(descricao)
    for i, (_, rx) in enumerate(PECAS):
        if re.search(rx, d):
            return i
    return len(PECAS)


def chave(descricao):
    """Chave numérica de ordenação: grupo, depois peça (vai no campo "grupo" do motor)."""
    return grupo(descricao) * 100 + peca(descricao)


ROTULOS = ["2 planos", "3 planos", "4 planos", "5 planos", "montante", "mão de amigo", "sem baguete", "demais"]


def _simples(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t)


def grupo(descricao):
    d = _simples(descricao)
    if "sem baguete" in d:  # pedido do cliente 27/11: os "sem baguete" ficam juntos
        return 6
    m = re.search(r"(\d)\s*(folhas|planos)", d)
    if m and m.group(1) in "2345":
        return int(m.group(1)) - 2  # 0..3
    if "mao de amigo" in d:
        return 5
    if d.startswith("montante"):
        return 4
    return 7
