# Catálogo técnico — Alplan + Ciazzani

Repositório do Catálogo técnico de perfis de alumínio do site unificado Alplan/Ciazzani:
desenhos padronizados, scripts de padronização, motor de paginação e (depois) o código do site.

## Pastas

| Pasta | O que guarda |
|---|---|
| `motor-paginacao/` | Motor único de paginação (site + PDF vetorial). `paginacao.ts` + testes. |
| `desenhos/pacotes/` | Desenhos padronizados (vetor) por pacote: geral-alcoa, suprema, geral-asa, gold, geral-stelman, belmetal-atlanta, lotes-avulsos, folhas-cliente, perfis-cliente-25-11, pendentes-padronizados. |
| `desenhos/fontes/` | Catálogos técnicos originais dos fabricantes (PDF) usados como fonte. |
| `scripts/` | Scripts de recorte e padronização (cotas, setas, OCR). |
| `dados/` | Exports do MySQL do catálogo (ItensEstoque) e planilhas de conferência. Sem preço, custo ou margem. |
| `docs/` | Decisões e regras (panorama do gerador de catálogo). |

## Rodar os testes do motor

```bash
node --experimental-strip-types motor-paginacao/teste.ts
```

(Node 22 ou superior.)

## Regras principais da paginação

- Tipologia da página (1-1, 1-2 H, 1-2 V, 1-3 H, 1-3 V, 1-4, 1-6, TABELADO) calculada automaticamente
  pelo tamanho real do desenho; ajuste manual possível. Não vem mais do ERP.
- Só dividem página perfis da mesma categoria + subcategoria + linha, na ordem do classificador.
- Página = grade 6×6; o espaço livre é dividido no tamanho do perfil que entra (mistura H com V aprovada).
- Tabelado: quebra de página com cabeçalho repetido; várias tabelas por página; cabeçalho de 50 mm;
  título "PERFIS STANDART".
- Desenho sempre na escala em que foi preparado.

Detalhes e histórico de decisões: [`docs/gerador-catalogo-panorama.md`](docs/gerador-catalogo-panorama.md).
