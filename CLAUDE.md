# Instruções para o Claude neste repositório

- Idioma: português do Brasil, em código (nomes, comentários) e na conversa.
- Antes de mudar regras do catálogo, leia `docs/gerador-catalogo-panorama.md` — ali estão as decisões
  aprovadas pelo cliente. Registre ali toda decisão nova (com data).
- Tudo que for produzido (desenhos, scripts, planilhas) fica neste repositório — arquivos entregues só
  na conversa se perdem entre sessões.
- Nunca versionar credenciais (ex.: `conexao.asp` do gerador antigo, strings de conexão, .env) nem
  preço/custo/margem do ERP.
- Rode `node --experimental-strip-types motor-paginacao/teste.ts` depois de mexer no motor.
- Padrões de desenho: perfil cheio em preto; cotas em Bahnschrift preta, vírgula decimal, tamanho =
  corpo do texto × 0,716; seta triangular cheia; leitura de baixo para cima ou horizontal; sem tolerâncias (±).
