# Gerador de Catálogo (catalogo.ciazzani.com.br) — panorama

Analisado em 23/11/2026 a partir dos arquivos em "Gerador Catalogo/". Atualizado em 26/11/2026 (rev. 50).

## Decisões (23/11/2026)
- O MySQL do catálogo (mesma hospedagem do ASP) continua como base separada, alimentada pelo ERP. Os dados mudam raramente → o site publica o catálogo a partir dele só quando há mudança.
- Etapa 1 (correções de segurança no ASP atual): o Danilo já está fazendo.
- Etapa 2: reescrever dentro do site novo (Next.js/Vercel) como "Catálogo técnico".
- Aprovados: pedir orçamento → carrinho com cor + quantidade de barras por perfil (sempre barras de 6 m); catálogos salvos na Área do Cliente; dados publicados quando mudam.
- Modelo de página do PDF APROVADO (A4, tipologia 1-3 H, desenho vetorial, marca do manual). 1 QR code por página, levando à página daqueles perfis no site (cor + quantidade + orçamento).
- Rodapé do PDF igual ao site: WhatsApp (número a informar), (12) 3901-4255, alplanaluminio.com.br e ciazzani.com.br, Rua Dinamarca, 201.
- Desenhos: usar os vetores dos catálogos técnicos (PDF) em vez de JPG. Quando só existir imagem, preferir um equivalente vetorial de outro catálogo; senão, vetorizar (potrace).
- Perfil sempre PREENCHIDO (cheio em preto). Perfis de referência e guarnições em cinza ficam como estão (exceção pedida pelo cliente: a baguete cinza do BX-099 sai).
- Cotas padronizadas: fonte Bahnschrift, preto, vírgula decimal, valor como no catálogo; tamanho = corpo do texto × 0,716. Rótulos de código/peso, quadros e marcadores são removidos. Valores, posições e direção ficam em _cotas.json.
  - Setas e linhas de cota (APROVADO em 25/11): seta triangular cheia preta, linhas finas pretas.
  - Leitura normal (25/11): números sempre de baixo para cima ou horizontais; ângulos mantidos.
- Catálogo LAF (Nals) cancelado pelo cliente (24/11).

## Decisões de 25/11 (noite)
- Equivalências NÃO aparecem para o cliente, mas ficam gravadas para a busca (podem ser várias por perfil).
- Perfis inativos aparecem como "sob consulta".
- Pesos: o ideal é vir online do ERP; enquanto isso, planilha pesos-a-validar.xlsx (123 linhas) para o cliente conferir.
- Cores: mostrar as de pronta entrega, mas aceitar orçamento em qualquer cor.
- Cotas enxutas (só as principais) apenas em Belmetal e Euroshow; tolerâncias (±) retiradas de todos os desenhos; linhas de cota não cortam os números.
- AP-057 = mesmo desenho do AP-056; CM-067 = MAC-0693 (Hera); STL-221 = AP-221.
- Organização do catálogo: sugestão em organizacao-catalogo.xlsx (atual × sugerido; 28 "A revisar").
- Feitos: base de dados (schema SQL, carga, API, publicador), protótipo do Catálogo técnico (busca, filtros, ficha, carrinho de orçamento, Área do Cliente simulada), publicação automática (revalidação a cada 5 min) e redirecionamentos do site antigo.

## Decisões de 26/11 (tarde) — paginação / tipologia da página
- Tipologia da página passa a ser AUTOMÁTICA, calculada pelo tamanho real do desenho vetorial (a que põe mais perfis por página onde o desenho cabe sem reduzir). Ajuste manual continua possível no site. O cadastro de tipologia sai do ERP (ver pendência).
- Motor único de paginação (motor-paginacao/paginacao.ts) gera o modelo de página usado pelo site e pelo PDF vetorial (com QR por página); o catálogo personalizado usa as mesmas regras.
- Página = grade 6×6 células. Compatibilidade sai da geometria (reproduz exatamente a tabela antiga: 1-2 H→1-3 H/1-4/1-6; 1-2 V→1-3 V/1-4/1-6; 1-3 H→1-6; 1-4→1-6).
- Mistura H com V APROVADA: o espaço livre é dividido no tamanho do perfil que entra (ex.: 1-2 V à esquerda + três 1-6 à direita; 1-2 H em cima + dois 1-4 embaixo).
- Tabelado: a tabela quebra de página com cabeçalho repetido ("continuação"); quantas tabelas couberem dividem a página (limite pela altura, não mais 2 tabelas / 12 linhas).
- Título das páginas de tabelado: MANTER "PERFIS STANDART".
- Cabeçalho do tabelado (desenho de referência + títulos) = 50 mm (definido pelo cliente em 26/11).
- Um único perfil na sobra ocupa o espaço inteiro, com o desenho centralizado na horizontal e na vertical (APROVADO 26/11, a partir das págs. 10 e 19 da amostra Linha 25: 25-514 em 1/2 página; Y-181 e Z-248 no quadrante igual ao do lado). Com 2 ou mais perfis, a sobra continua dividida.
- Desenho sempre na escala em que foi preparado (nunca ampliado para preencher o espaço).
- ORDEM dentro de cada linha (APROVADO 26/11, noite): 1º tipologia (mesma tipologia junta, da maior para a menor), 2º tamanho do desenho (área, maior primeiro), 3º código. Substitui a ordem do classificador. Gold: 43 → 28 páginas em escala real; catálogo inteiro (793 perfis sem tabelados) ≈ 247 páginas em escala real e ≈ 202 com redução até 80%.
- GRUPOS por descrição (APROVADO 26/11, noite) vêm ANTES da tipologia: 2 planos, 3 planos, 4 planos, 5 planos, montante, mão de amigo, demais ("correr N folhas" = N planos; "mão de amigo" vence "montante"). Ordem final: grupo → tipologia → tamanho → código (catalogo-pdf/grupos.py). Gold: 32 páginas em escala real.
- Descrições padronizadas (folhas → planos, acentuação, maiúsculas): planilha dados/descricoes-atual-x-sugerida.xlsx para o cliente aprovar (337 de 931 mudam; 84 sem descrição). O catálogo usa as descrições atuais até a aprovação.
- ALINHAMENTO (APROVADO 26/11): na mesma coluna da página, os desenhos começam na mesma margem esquerda (a do mais largo) e o conjunto fica centralizado (catalogo-pdf/gerar.py).
- LG-050 girado 90° horário a pedido do cliente (scripts/girar_desenho.py; números das cotas mantidos na orientação original; registro em dados/rotacoes.json).
- GRUPO "SEM BAGUETE" (cliente 27/11): perfis com "sem baguete" na descrição ficam juntos num grupo próprio, depois de mão de amigo e antes de demais. Peças novas na ordem: montante lateral (após montante central), marco de giro e marco Max (antes de marco).
- LG-144, LG-145, LG-158 e LG-234 girados 90° horário (cliente 27/11): passam a 1-3 H (190×84 mm) em escala real. scripts/girar_desenho.py corrigido: o número é desgirado no lugar, sem sair do recorte (antes, números escondidos de vizinhos apareciam).
- DESCRIÇÕES CORRIGIDAS pelo cliente (27/11) em dados/descricoes-corrigidas.json: LG-017, 051, 133, 042, 050, 043, 127, 085, 128, 056, 056R, 068, 083, 129, 130, 132, 134, 126 ("Tarvessa" lido como Travessa; "Marcos de giro" do LG-056R lido como Marco de giro).
- ORDEM POR PEÇA (pedido do cliente 27/11; ordem das peças proposta, a confirmar): dentro de cada grupo (2…5 planos, montante, mão de amigo, demais) os perfis seguem a peça — marco superior → marco inferior → marco lateral → marco bandeira/peitoril → trilho superior → trilho inferior → lateral do trilho → travessa bandeira → travessa peitoril → montante central → montante da folha → montante travessa → montante → coluna → marco → travessa superior/central/inferior da folha → travessa → complemento → mata junta → inversor → baguete → porta palheta → tampa → pingadeira → clic → sem descrição. Depois tipologia, tamanho e código (catalogo-pdf/grupos.py: PECAS). Gold foi de 32 para 35 páginas.
- LG-133, LG-144 e LG-145 (relato do cliente 26/11): linhas e cotas de desenhos vizinhos removidas (dados/correcoes-desenhos.json; no LG-133 saíram também os números 8,1 e 33 que eram de outro perfil — scripts/limpar_desenhos.py ganhou "remover_textos").
- LG-234 é de 3 folhas: descrição corrigida em dados/descricoes-corrigidas.json (vale até o ERP ser corrigido).
- Em avaliação (26/11): ordem das tipologias encadeando as compatíveis (1-1, 1-3 V, 1-2 V, 1-2 H, 1-3 H, 1-4, 1-6) ganha ~2 páginas; nova tipologia 1-9 (3×3, desenho até 57×61 mm) ganharia ~12 páginas em escala real (243 perfis cabem nela); encaixe livre de várias tipologias na mesma sobra.
- Segundo momento: encaixe livre em qualquer área; misturar linhas diferentes numa página do catálogo personalizado.
- Áreas para o desenho (configuráveis, reserva de 16 mm p/ código+peso e 6 mm p/ descrição): 1-1 183×228; 1-2 H 183×103; 1-2 V 89×228; 1-3 H 183×61; 1-3 V 57×228; 1-4 89×103; 1-6 89×61 mm.
- Repositório GitHub privado criado (26/11): rafaelcapizzani/catalogo-tecnico. Guardar ali código, desenhos padronizados e scripts — os arquivos entregues nas conversas não ficam no Projeto.

## Tipologia atual × sugerida (26/11, fim da tarde)
- Pacotes de desenhos, scripts e dados recuperados e versionados no repositório (10 pacotes, 758 SVGs + 617 da base do protótipo; 780 códigos medidos).
- Tipologia atual lida direto do catalogo.ciazzani.com.br (atributo tipologia de dados.asp): 727 perfis → dados/tipologia-atual.json. Não foi preciso export do MySQL.
- Desenhos padronizados estão em escala real (SVG em pt, 1:1 com o catálogo do fabricante).
- Planilha dados/tipologia-atual-x-sugerida.xlsx (scripts: medir_desenhos.py → tipologia_sugerida.ts → planilha_tipologia.py).
- Resultado (835 perfis comparáveis, medição corrigida pela área desenhada): hoje 235 páginas; sugerida em ESCALA REAL 298 páginas (+27%); PERMITINDO REDUZIR ATÉ 80% → 226 páginas (−4%).
- Validação da escala (scripts/validar_escala.py, 26/11): em 476 de 744 desenhos a linha de cota bate com o valor em ±3% (1:1 confirmado, ex.: LG-002 102,2 → 102,7 mm). Os demais são, na maioria, perfis grandes que o próprio fabricante desenhou reduzidos. 72 SVGs tinham margem em branco → medição passou a usar a área desenhada (perfil + cotas) e o PDF enquadra só o desenho.
- Ponto levantado pelo cliente (26/11): "os desenhos vieram dos catálogos em tamanho real e couberam". Confirmado que são 1:1; porém o espaço inclui as cotas (LG-002: perfil 102,2 mm, desenho com cotas 124 × 38 mm) e o catálogo antigo usava JPG ajustado ao espaço (max-width/max-height), sem escala fixa — ex.: LG-002 está como 1-4 (espaço de ~89 mm de largura), o que só é possível reduzido (~70%).
- Amostras para decisão (catalogo-pdf/gerar.py): Gold e Linha 25 em 3 versões — escala real (Gold 43 págs., L25 18), redução até 80% (30 / 14) e tipologia de hoje (31 / 15).
- O catálogo antigo reduzia os desenhos sem limite (max-width/max-height da imagem).
- 12 desenhos maiores que a página inteira (AP-056, AP-057, AP-0601, AP-0603, AP-063, AP-1439, CM-093, LB-038, LB-050, LB074, LG-571, MN-039): precisam de redução de qualquer forma.
- DECISÃO PENDENTE DO CLIENTE: manter escala real ou permitir redução (sugestão: até 80%). O motor já aceita o parâmetro (sugerirTipologia(..., reducaoMaxima)).

## Revisão dos desenhos da Gold (26/11, relatos do cliente)
- Corrigidos: LG-176 (traços soltos + vão no 28,8; faixa grossa do topo conferida pelo peso e mantida); LG-071 e AP-0603 (moldura da página do fabricante, scripts/remover_molduras.py); LG-076, LG-124, LG-129 (traços e cotas de desenhos vizinhos, scripts/limpar_desenhos.py + dados/correcoes-desenhos.json).
- Pendentes: LG-133, LG-158, LG-159 (seta aberta "V" em vez da seta cheia; LG-133 também com cotas/traços de vizinhos), LG-162 e LG-164 (corte da cota).
- Correção automática de setas em massa NÃO aplicada: a detecção confunde hachuras e cotas de vizinhos (scripts/fechar_setas.py fica como apoio, uso por desenho).

## Pendências do cliente
- Decidir escala dos desenhos no catálogo: escala real (+35% de páginas) ou redução permitida até X% (80% mantém o tamanho atual do catálogo).
- Número do WhatsApp; PDF do catálogo (aguardando liberação); destino dos pedidos de orçamento (a discutir); validar os 123 pesos; revisar a organização (28 itens); export MySQL ItensEstoque atualizado (Danilo).

## Pendências para o time do ERP
- Atualizar no ERP as descrições corrigidas pelo cliente em 27/11 (lista em dados/descricoes-corrigidas.json).
- LG-234: descrição está "correr 2 folhas", o correto é 3 folhas (informado pelo cliente 26/11).
- LG-129E: cadastro duplicado (sem descrição), é o mesmo perfil do LG-129 — avaliar inativar no ERP. Já fora do catálogo (dados/fora-do-catalogo.json).
- CANCELAR o cadastro de "tipologia da página" no ERP (campo tipologia_da_pagina): a tipologia passa a ser calculada e ajustada no site. Não remover antes de o site novo assumir a paginação (o ASP atual ainda lê esse campo).

## Pendentes padronizados (25–26/11, rev. 44)
- 163 perfis que faltavam foram recortados e padronizados (pacote pendentes-padronizados, com PDF de conferência). Coluna "Desenho recortado e cotas padronizadas": 777 "Sim".
- 26/11 (revisão do cliente): BX-006/102/105/108/109/111 trocados para o ASA (Y-107, U-1002, I-154, Y-308, U-655, 44-018 = I-155) — o equivalente do cadastro é ASA e o peso do ERP bate com o ASA; o BX-xxx da Tera era só coincidência de código. Linhas tracejadas da Suprema Integrada (MN) retiradas. Setas que a linha de cota atravessava ficavam com um risco branco (setas maiores ou quase equiláteras não eram reconhecidas) → corrigido em cotas.py.
- 26/11 (tarde, revisão do cliente): BX-003 → ASA U-1056; AP-025 recorte com as cotas (desenho = BX-250 Decamp = ASA 39-956; peso do ERP não bate); FC-258 e FC-087 limpos; SU-231 (tiras finas confundidas com setas) e LG-129E (= LG-129; frestas das tiras, revetorizado) corrigidos. Desenhos enviados pelo cliente: AP-002 = PR-003E (trilho cogumelo), AP-004 (lambri 200 mm), BX-029 (travessa).
- 26/11 (planilha de pesos do cliente, dados/pesos-validados-cliente-26-11.xlsx → dados/pesos-validados.json, 37 perfis): coluna "Peso validado pelo cliente" na planilha de cruzamento (rev. 50). Fornecedor informado → desenho trocado: CG-080 = Stelman STL-424; CX-085 = Stelman STL-421; CL-006 = Império CL-006; CL-009 = Império L-468 (cliente escreveu l-498). CL-006 e CL-009: o "Peso a usar" já era por metro (gravado 1,003 e 1,645 kg/m) — confirmar com o cliente. Sem catálogo do fornecedor: Alumiso (AP-026, BX-108, BX-109) e Nals (CX-071). Desenho que não bate com o peso validado (>25%): CX-071, 42-004, CG-087, CL-010, CA-001, DS-023, DS-017, LB-069, AP-068, AP-025, CM-065, BX-105.
- Aprendido: na Tera e na Específica 3.2 o rótulo fica EMBAIXO do desenho, e o código também aparece em chamadas de peças vizinhas → usar o rótulo principal (com Kg/m logo abaixo); índice OCR da Tera em alcoa/pend/tera_idx.json. Decamp: marca d'água num bloco de conteúdo opcional, tirada do conteúdo. Números em curva/imagem lidos em 3 resoluções; correções conferidas uma a uma (pend_seg.py: fix/add).
- Sem desenho processável: 30-053, AL-089/090/091 (Perfil Master, PDF não localizado), DC-004/006 (detalhes construtivos), CM-066 (MN-014), PV-003, SU-224 (NSU325), SU-270, 25-008 e 25-531 (inativos); TG-084/TG-280 são linhas de tabela (tabelado).

## Pacotes entregues
geral-alcoa, suprema, geral-asa, gold, geral-stelman, belmetal-atlanta, lotes-avulsos, folhas-cliente, perfis-cliente-25-11 e pendentes-padronizados — cada um com PDF de conferência original × padronizado. No repositório em desenhos/pacotes/. Todos regerados em 26/11 (17h) com o cotas.py atual (setas atravessadas pela linha, setas quase equiláteras, tiras finas que não são setas, trecho de linha refeito quando a seta original é mais comprida que a padrão). CG-080 e CL-006 saíram dos pacotes geral-alcoa e gold — a versão certa (Stelman STL-424 / Império CL-006) está em pendentes-padronizados. Os lotes Stelman AP-1234…/LB/MM (lotes 9–11, no pacote lotes-avulsos) também foram regerados no padrão novo de setas. Os vetorizados por potrace (Mega 32 Lite) não mudam.

## Cruzamento perfis × desenhos
Fontes: export ItensEstoque do site + lista "Itens do Estoque" do ERP. Busca pelo código Alplan, pelo equivalente e pelos códigos informados pelo cliente.
- Prioridade: o catálogo do fabricante original vence; Stelman e Decamp só preenchem lacunas.
- Validação pelo peso: ERP guarda peso por barra de 6 m; alerta acima de 15%.
- A planilha não inclui preço, custo nem margem do ERP.

## Próximo passo
Subir os pacotes para o repositório; gerar a planilha de tipologia atual × sugerida; conferência visual dos pendentes corrigidos pelo cliente; levar os desenhos novos e o motor de paginação para a base/protótipo e montar o PDF do catálogo quando o cliente liberar.

## O que faz (sistema atual)
1. index.html: filtros em cascata Tipo > Linha > Tipologia + busca por texto.
2. retorno.asp: grade de produtos com código, descrição, equivalência, peso e imagem.
3. "Gerar seu catálogo": dados.asp monta HTML paginado A4 e o navegador converte em PDF (jsPDF + html2canvas).

## Regras de layout do sistema antigo (referência)
- Tipologia da página por item: 1-1, 1-2 H, 1-2 V, 1-3 H, 1-3 V, 1-4, 1-6 e TABELADO; itens da mesma categoria/linha compartilham página; tipologias compatíveis podem dividir a página.
- Compatível (quadranteCompativel): só o PRÓXIMO item da lista ocupa a sobra, e ocupa o espaço inteiro da tipologia da página (sem dividir).
- TABELADO: tabela com código, equivalência, peso kg/m, dimensões A/B/C/E em mm e polegadas; tabelas com até 12 linhas juntadas na mesma página (no máximo 2); tabela longa não quebrava.

## Dados
- MySQL via ODBC, tabela ItensEstoque (disp_web='Sim').
- ERP (Itens do Estoque): códigos, fornecedor, situação, tipo (pronta entrega/encomenda), cor, peso teórico por barra de 6 m.

## Problemas do sistema atual
- SQL injection (sendo corrigido), páginas de debug expostas, upload sem autenticação; PDF como imagem.
