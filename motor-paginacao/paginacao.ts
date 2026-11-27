/**
 * Motor de paginação do Catálogo técnico (Alplan + Ciazzani).
 *
 * Uma única função monta o "modelo de página" (posições em mm) que é usado
 * tanto pela página do site quanto pelo PDF vetorial. O catálogo personalizado
 * do cliente passa pelas mesmas regras.
 *
 * Regras (decididas em 26/11/2026):
 *  - A tipologia de cada perfil é calculada automaticamente pelo tamanho real
 *    do desenho vetorial (sugerirTipologia). O ajuste manual continua possível
 *    (campo tipologiaManual), mas deixa de vir do ERP.
 *  - Só dividem a página os perfis da mesma categoria + subcategoria + linha.
 *    Ordem dentro da família: tipologia, tamanho e código (ordenarItens).
 *  - A página é uma grade de 6×6 células. Uma tipologia diferente só entra num
 *    espaço livre se couber nele (a compatibilidade sai da geometria e reproduz
 *    exatamente a tabela do sistema antigo). O espaço livre é dividido no
 *    tamanho do perfil que entra: ex. 1-2 V à esquerda + três 1-6 à direita.
 *  - TABELADO: a tabela quebra de página com cabeçalho repetido, e quantas
 *    tabelas couberem dividem a mesma página. Título "PERFIS STANDART" mantido.
 *  - Desenho sempre na escala em que foi preparado (nunca ampliado).
 */

export type Tipologia = "1-1" | "2-3 V" | "1-2 H" | "1-2 V" | "1-3 H" | "1-3 V" | "1-4" | "1-6";
export type TipologiaOuTabelado = Tipologia | "TABELADO";

/** Tamanho de cada tipologia em células da grade 6×6 (largura × altura). */
export const CELULAS: Record<Tipologia, { w: number; h: number }> = {
  "1-1": { w: 6, h: 6 },
  // 2/3 da página na vertical; o 1/3 que sobra recebe 1-3 V, 1-6 etc.
  // Só manual (cliente 27/11: LG-571 + LG-572 na mesma página); não é sugerida.
  "2-3 V": { w: 4, h: 6 },
  "1-2 H": { w: 6, h: 3 },
  "1-2 V": { w: 3, h: 6 },
  "1-3 H": { w: 6, h: 2 },
  "1-3 V": { w: 2, h: 6 },
  "1-4": { w: 3, h: 3 },
  "1-6": { w: 3, h: 2 },
};

/** Medidas da área útil da página A4 e reservas de texto, em mm. */
export const CONFIG = {
  areaLargura: 189, // largura útil (716 px do sistema antigo ≈ 189 mm)
  areaAltura: 250, // altura útil entre cabeçalho e rodapé
  reservaTopo: 16, // código + peso acima do desenho
  reservaBase: 6, // descrição abaixo do desenho
  reservaLateral: 3,
  // Tabelado
  tabCabecalho: 50, // desenho de referência + títulos da tabela (definido pelo cliente em 26/11)
  tabLinha: 6.5, // altura de uma linha da tabela
  tabMinLinhas: 3, // não começa uma tabela no fim da página com menos que isso
  tabEspaco: 6, // espaço entre duas tabelas na mesma página
};

const celulaL = () => CONFIG.areaLargura / 6;
const celulaA = () => CONFIG.areaAltura / 6;

/** Área disponível para o desenho dentro de um espaço da tipologia (mm). */
export function areaDesenho(t: Tipologia) {
  const c = CELULAS[t];
  return {
    largura: c.w * celulaL() - 2 * CONFIG.reservaLateral,
    altura: c.h * celulaA() - CONFIG.reservaTopo - CONFIG.reservaBase,
  };
}

/** Quantos perfis por página (quanto maior, mais econômica). */
/** Tipologias que só entram por escolha manual. */
const SO_MANUAL: Tipologia[] = ["2-3 V"];

const porPagina = (t: Tipologia) => 36 / (CELULAS[t].w * CELULAS[t].h);

/**
 * Tipologia sugerida: a que coloca mais perfis por página e onde o desenho
 * cabe sem reduzir. Empate (1-2 H × 1-2 V, 1-3 H × 1-3 V): vence a que deixa
 * menos sobra. Se nada couber, 1-1 com alerta.
 */
export function sugerirTipologia(larguraMm: number, alturaMm: number, reducaoMaxima = 1) {
  // reducaoMaxima = 1 → escala real (regra atual). Ex.: 0,8 permite reduzir o desenho até 80%.
  const candidatas = (Object.keys(CELULAS) as Tipologia[])
    .filter((t) => !SO_MANUAL.includes(t))
    .map((t) => {
      const a = areaDesenho(t);
      const cabe = larguraMm * reducaoMaxima <= a.largura && alturaMm * reducaoMaxima <= a.altura;
      const ocupacao = (larguraMm * alturaMm) / (a.largura * a.altura);
      return { t, cabe, ocupacao, porPagina: porPagina(t) };
    })
    .filter((c) => c.cabe)
    .sort((x, y) => y.porPagina - x.porPagina || y.ocupacao - x.ocupacao);
  if (!candidatas.length) return { tipologia: "1-1" as Tipologia, alerta: "desenho maior que a página inteira" };
  return { tipologia: candidatas[0].t, alerta: "" };
}

export function cabeNaTipologia(t: Tipologia, larguraMm: number, alturaMm: number) {
  const a = areaDesenho(t);
  return larguraMm <= a.largura && alturaMm <= a.altura;
}

// ---------------------------------------------------------------------------

export interface Item {
  codigo: string;
  categoria: string;
  subcategoria: string;
  linha: string;
  classificador: number;
  /** Tamanho real do desenho vetorial (mm). Para TABELADO pode ficar 0. */
  larguraMm: number;
  alturaMm: number;
  tabelado?: boolean;
  /** Ajuste manual; quando preenchido, vence o cálculo automático. */
  tipologiaManual?: Tipologia;
  /** Grupo dentro da família (ex.: 2 planos, montante, mão de amigo); menor vem antes. */
  grupo?: number;
}

export interface Espaco {
  codigo: string;
  tipologia: Tipologia;
  /** Posição e tamanho do espaço dentro da área útil (mm, origem no canto superior esquerdo). */
  x: number;
  y: number;
  largura: number;
  altura: number;
}

export interface BlocoTabela {
  subcategoria: string;
  continuacao: boolean;
  codigos: string[];
  y: number;
  altura: number;
}

export type Pagina =
  | { tipo: "perfis"; numero: number; titulo: string; familia: string; tipologiaBase: Tipologia; espacos: Espaco[]; codigos: string[] }
  | { tipo: "tabelado"; numero: number; titulo: string; blocos: BlocoTabela[]; codigos: string[] };

/**
 * Ordem dos perfis dentro de cada família (decisões do cliente, 26/11/2026):
 * 0º grupo (2, 3, 4, 5 planos, montante, mão de amigo, demais — campo grupo),
 * 1º tipologia (mesma tipologia junta; da maior para a menor, assim as sobras
 *    de uma página podem receber as tipologias menores que vêm depois),
 * 2º tamanho do desenho (área, do maior para o menor),
 * 3º código.
 * A ordem das famílias entre si é mantida.
 */
export const ORDEM_TIPOLOGIA: TipologiaOuTabelado[] = ["1-1", "2-3 V", "1-2 H", "1-2 V", "1-3 H", "1-3 V", "1-4", "1-6", "TABELADO"];

export function ordenarItens(itens: Item[]): Item[] {
  const familias: string[] = [];
  const grupos = new Map<string, Item[]>();
  for (const i of itens) {
    const f = familia(i);
    if (!grupos.has(f)) {
      grupos.set(f, []);
      familias.push(f);
    }
    grupos.get(f)!.push(i);
  }
  const chave = (i: Item) => ORDEM_TIPOLOGIA.indexOf(tipologiaDoItem(i));
  return familias.flatMap((f) =>
    grupos.get(f)!.slice().sort(
      (a, b) =>
        (a.grupo ?? 99) - (b.grupo ?? 99) ||
        chave(a) - chave(b) ||
        b.larguraMm * b.alturaMm - a.larguraMm * a.alturaMm ||
        a.codigo.localeCompare(b.codigo, "pt-BR", { numeric: true }),
    ),
  );
}

export function tipologiaDoItem(i: Item): TipologiaOuTabelado {
  if (i.tabelado) return "TABELADO";
  return i.tipologiaManual ?? sugerirTipologia(i.larguraMm, i.alturaMm).tipologia;
}

const familia = (i: Item) => `${i.categoria}|${i.subcategoria}|${i.linha}`;

/** Espaços principais de uma tipologia, em ordem de leitura (linha por linha). */
function espacosPrincipais(t: Tipologia) {
  const c = CELULAS[t];
  const r: { cx: number; cy: number; w: number; h: number }[] = [];
  for (let cy = 0; cy + c.h <= 6; cy += c.h) {
    let cx = 0;
    for (; cx + c.w <= 6; cx += c.w) r.push({ cx, cy, w: c.w, h: c.h });
    if (cx < 6) r.push({ cx, cy, w: 6 - cx, h: c.h }); // sobra na largura (ex.: 2-3 V deixa 1/3)
  }
  return r;
}

/**
 * Monta as páginas. Os itens devem chegar na ordem do catálogo
 * (categoria, subcategoria, linha, classificador) — a função não reordena.
 */
export function paginar(itens: Item[]): Pagina[] {
  const paginas: Pagina[] = [];
  let i = 0;
  while (i < itens.length) {
    if (tipologiaDoItem(itens[i]) === "TABELADO") {
      const inicio = i;
      while (i < itens.length && tipologiaDoItem(itens[i]) === "TABELADO") i++;
      paginarTabelados(itens.slice(inicio, i), paginas);
    } else {
      i = paginarPerfis(itens, i, paginas);
    }
  }
  return paginas;
}

/** Monta UMA página de perfis a partir de itens[i]; devolve o próximo índice. */
function paginarPerfis(itens: Item[], i: number, paginas: Pagina[]): number {
  const primeiro = itens[i];
  const fam = familia(primeiro);
  const base = tipologiaDoItem(primeiro) as Tipologia;
  const principais = espacosPrincipais(base);
  const espacos: Espaco[] = [];
  const cl = celulaL(), ca = celulaA();

  for (const p of principais) {
    if (i >= itens.length) break;
    const it = itens[i];
    if (familia(it) !== fam) break;
    const t = tipologiaDoItem(it);
    if (t === "TABELADO") break;
    const c = CELULAS[t];
    if (c.w > p.w || c.h > p.h) break; // não cabe no espaço livre → página nova

    // Divide o espaço livre no tamanho da tipologia que entra
    // e preenche com os próximos perfis da mesma tipologia, em ordem.
    const antes = espacos.length;
    for (let sy = 0; sy + c.h <= p.h; sy += c.h) {
      for (let sx = 0; sx + c.w <= p.w; sx += c.w) {
        if (i >= itens.length) break;
        const atual = itens[i];
        if (familia(atual) !== fam || tipologiaDoItem(atual) !== t) break;
        espacos.push({
          codigo: atual.codigo,
          tipologia: t,
          x: (p.cx + sx) * cl,
          y: (p.cy + sy) * ca,
          largura: c.w * cl,
          altura: c.h * ca,
        });
        i++;
      }
      if (i >= itens.length || familia(itens[i]) !== fam || tipologiaDoItem(itens[i]) !== t) break;
    }
    // Um único perfil no espaço livre: ocupa o espaço inteiro (o desenho fica
    // centralizado na horizontal e na vertical). Decisão do cliente em 26/11/2026.
    if (espacos.length - antes === 1) {
      const e = espacos[espacos.length - 1];
      e.x = p.cx * cl;
      e.y = p.cy * ca;
      e.largura = p.w * cl;
      e.altura = p.h * ca;
    }
  }

  paginas.push({
    tipo: "perfis",
    numero: paginas.length + 1,
    titulo: primeiro.linha ? `${primeiro.subcategoria} - ${primeiro.linha}` : primeiro.subcategoria,
    familia: fam,
    tipologiaBase: base,
    espacos,
    codigos: espacos.map((e) => e.codigo),
  });
  return i;
}

/** Tabelados: tabela quebra com cabeçalho repetido; várias tabelas por página. */
function paginarTabelados(itens: Item[], paginas: Pagina[]) {
  // agrupa por subcategoria mantendo a ordem
  const grupos: { sub: string; codigos: string[] }[] = [];
  for (const it of itens) {
    const g = grupos[grupos.length - 1];
    if (g && g.sub === it.subcategoria) g.codigos.push(it.codigo);
    else grupos.push({ sub: it.subcategoria, codigos: [it.codigo] });
  }

  let pag: Extract<Pagina, { tipo: "tabelado" }> | null = null;
  let y = 0;
  const novaPagina = () => {
    pag = { tipo: "tabelado", numero: paginas.length + 1, titulo: "PERFIS STANDART", blocos: [], codigos: [] };
    paginas.push(pag);
    y = 0;
  };

  for (const g of grupos) {
    let restantes = g.codigos.slice();
    let continuacao = false;
    while (restantes.length) {
      if (!pag) novaPagina();
      const espacoAntes = pag!.blocos.length ? CONFIG.tabEspaco : 0;
      const livre = CONFIG.areaAltura - y - espacoAntes - CONFIG.tabCabecalho;
      const cabem = Math.floor(livre / CONFIG.tabLinha);
      const minimo = Math.min(CONFIG.tabMinLinhas, restantes.length);
      if (cabem < minimo) {
        if (!pag!.blocos.length) throw new Error("Configuração de tabelado não cabe numa página vazia");
        novaPagina();
        continue;
      }
      const n = Math.min(cabem, restantes.length);
      const bloco: BlocoTabela = {
        subcategoria: g.sub,
        continuacao,
        codigos: restantes.slice(0, n),
        y: y + espacoAntes,
        altura: CONFIG.tabCabecalho + n * CONFIG.tabLinha,
      };
      pag!.blocos.push(bloco);
      pag!.codigos.push(...bloco.codigos);
      y = bloco.y + bloco.altura;
      restantes = restantes.slice(n);
      if (restantes.length) {
        continuacao = true;
        pag = null;
      }
    }
  }
}
