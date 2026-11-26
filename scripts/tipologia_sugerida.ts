/**
 * Compara a tipologia atual (catálogo antigo) com a sugerida pelo motor.
 *
 * Entradas:
 *   dados/medidas-desenhos.json       (scripts/medir_desenhos.py)
 *   dados/tipologia-atual.json        (lida do catalogo.ciazzani.com.br em 26/11/2026)
 *   dados/catalogo-base-de-dados.zip → perfis.json (extraído em /tmp pelo chamador; caminho no 1º argumento)
 * Saída:
 *   dados/tipologia-sugerida.json
 *
 * Uso: node --experimental-strip-types scripts/tipologia_sugerida.ts /caminho/perfis.json
 */
import { readFileSync, writeFileSync } from "node:fs";
import { sugerirTipologia, areaDesenho, paginar, CELULAS, type Tipologia, type Item } from "../motor-paginacao/paginacao.ts";

const REDUCAO_ALTERNATIVA = 0.8;

const medidas: Record<string, { largura_mm: number; altura_mm: number; pacote: string; alerta: string }> = JSON.parse(
  readFileSync("dados/medidas-desenhos.json", "utf8"),
);
const atual: Record<string, string> = JSON.parse(readFileSync("dados/tipologia-atual.json", "utf8"));
const perfis: any[] = JSON.parse(readFileSync(process.argv[2], "utf8")).perfis;

const porPagina = (t: string) => (t in CELULAS ? 36 / (CELULAS[t as Tipologia].w * CELULAS[t as Tipologia].h) : 0);

const linhas = perfis.map((p) => {
  const m = medidas[p.codigo];
  const at = atual[p.codigo] ?? "";
  if (p.tabelado || at === "TABELADO") {
    return { ...base(p, m), atual: at || "TABELADO", sugerida: "TABELADO", sugeridaReduzida: "TABELADO", comparacao: "Tabelado", reducaoParaManter: null, alerta: "" };
  }
  if (!m) {
    return { ...base(p, m), atual: at, sugerida: "", sugeridaReduzida: "", comparacao: "Sem desenho", reducaoParaManter: null, alerta: "" };
  }
  const s = sugerirTipologia(m.largura_mm, m.altura_mm);
  const r = sugerirTipologia(m.largura_mm, m.altura_mm, REDUCAO_ALTERNATIVA);
  let comparacao = "Sem tipologia atual";
  let reducaoParaManter: number | null = null;
  if (at) {
    if (at === s.tipologia) comparacao = "Igual";
    else if (porPagina(s.tipologia) < porPagina(at)) comparacao = "Precisa de espaço maior";
    else if (porPagina(s.tipologia) > porPagina(at)) comparacao = "Economiza espaço";
    else comparacao = "Muda orientação";
    if (at in CELULAS) {
      const a = areaDesenho(at as Tipologia);
      const f = Math.min(a.largura / m.largura_mm, a.altura / m.altura_mm);
      if (f < 1) reducaoParaManter = Math.round(f * 100);
    }
  }
  return {
    ...base(p, m),
    atual: at,
    sugerida: s.tipologia,
    sugeridaReduzida: r.tipologia,
    comparacao,
    reducaoParaManter,
    alerta: [s.alerta, m.alerta].filter(Boolean).join("; "),
  };
});

function base(p: any, m: any) {
  return {
    codigo: p.codigo,
    descricao: p.descricao ?? "",
    aplicacao: p.aplicacao ?? "",
    linha: p.linha ?? "",
    situacao: p.situacao ?? "",
    pacote: m?.pacote ?? "",
    largura_mm: m?.largura_mm ?? null,
    altura_mm: m?.altura_mm ?? null,
  };
}

// Estimativa de páginas (ordem do cadastro, agrupado por aplicação + linha)
function paginas(lista: typeof linhas, campo: "atual" | "sugerida" | "sugeridaReduzida") {
  const itens: Item[] = lista
    .filter((l) => l[campo] && l.comparacao !== "Sem desenho")
    .map((l) => ({
      codigo: l.codigo,
      categoria: l.aplicacao,
      subcategoria: l.linha,
      linha: "",
      classificador: 0,
      larguraMm: 0,
      alturaMm: 0,
      tabelado: l[campo] === "TABELADO",
      tipologiaManual: l[campo] === "TABELADO" ? undefined : (l[campo] as Tipologia),
    }))
    .filter((i) => i.tabelado || (i.tipologiaManual && i.tipologiaManual in CELULAS))
    .sort((a, b) => (a.categoria + a.subcategoria).localeCompare(b.categoria + b.subcategoria));
  return paginar(itens).length;
}

const comparaveis = linhas.filter((l) => l.atual && l.sugerida);
const resumo = {
  perfis: linhas.length,
  comTipologiaAtual: linhas.filter((l) => l.atual).length,
  paginasComparaveis: {
    perfis: comparaveis.length,
    atual: paginas(comparaveis, "atual"),
    sugerida: paginas(comparaveis, "sugerida"),
    sugeridaReduzida: paginas(comparaveis, "sugeridaReduzida"),
  },
};
writeFileSync(
  "dados/tipologia-sugerida.json",
  JSON.stringify({ reducaoAlternativa: REDUCAO_ALTERNATIVA, resumo, linhas }, null, 1),
);
console.log(`${linhas.length} perfis → dados/tipologia-sugerida.json`);
console.log(resumo);
