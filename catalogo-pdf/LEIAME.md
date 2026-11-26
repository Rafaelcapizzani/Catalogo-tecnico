# catalogo-pdf/

Gera o catálogo técnico em PDF (A4) a partir do motor de paginação.

```bash
python3 catalogo-pdf/gerar.py --linhas Gold --reducao 1   --saida catalogo-pdf/saida/gold-escala-real.pdf
python3 catalogo-pdf/gerar.py --linhas Gold --reducao 0.8 --saida catalogo-pdf/saida/gold-reducao-80.pdf
python3 catalogo-pdf/gerar.py --linhas Gold --atual       --saida catalogo-pdf/saida/gold-tipologia-de-hoje.pdf
```

Requisitos: Node 22+, Python 3 com `qrcode`, `numpy`, `Pillow`, Google Chrome (impressão em PDF) e as fontes
`noir-pro.ttf` e `bahnschrift.ttf` em `catalogo-pdf/fontes/` (não versionadas — licença). A saída vai para
`catalogo-pdf/saida/` (não versionada). O endereço do QR code é provisório (`URL_BASE` em gerar.py).
