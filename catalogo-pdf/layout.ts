/**
 * Ponte entre o gerador do PDF (Python) e o motor de paginação.
 * Lê uma lista de itens (JSON), escolhe a tipologia de cada um pelo motor
 * e devolve as páginas montadas.
 *
 * Uso: node --experimental-strip-types catalogo-pdf/layout.ts entrada.json saida.json
 *   entrada: { reducaoMaxima: number, itens: [{codigo, familia, larguraMm, alturaMm, tipologia?, grupo?}] }
 *   (tipologia preenchida = usa essa, ex.: a tipologia atual do catálogo antigo)
 */
import { readFileSync, writeFileSync } from "node:fs";
import { paginar, ordenarItens, sugerirTipologia, type Item } from "../motor-paginacao/paginacao.ts";

const [entrada, saida] = process.argv.slice(2);
const { reducaoMaxima, itens } = JSON.parse(readFileSync(entrada, "utf8"));

const lista: Item[] = itens.map((i: any) => ({
  codigo: i.codigo,
  categoria: "",
  subcategoria: i.familia,
  linha: "",
  classificador: 0,
  larguraMm: i.larguraMm,
  alturaMm: i.alturaMm,
  grupo: i.grupo,
  // sem desenho: ocupa um espaço 1-6 com o aviso "sob consulta"
  tipologiaManual: i.tipologia ? i.tipologia : i.larguraMm ? sugerirTipologia(i.larguraMm, i.alturaMm, reducaoMaxima).tipologia : "1-6",
}));

writeFileSync(saida, JSON.stringify(paginar(ordenarItens(lista)), null, 1));
