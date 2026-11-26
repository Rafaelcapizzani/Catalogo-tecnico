import assert from "node:assert/strict";
import { paginar, sugerirTipologia, areaDesenho, CELULAS, CONFIG, type Item, type Tipologia } from "./paginacao.ts";

const perfil = (codigo: string, t: Tipologia, linha = "SUPREMA"): Item => ({
  codigo, categoria: "ESQUADRIAS", subcategoria: "LINHA", linha, classificador: 0,
  larguraMm: 1, alturaMm: 1, tipologiaManual: t,
});
const tab = (codigo: string, sub: string): Item => ({
  codigo, categoria: "STANDART", subcategoria: sub, linha: "", classificador: 0,
  larguraMm: 0, alturaMm: 0, tabelado: true,
});
const resumo = (p: any) => p.tipo === "perfis" ? `${p.tipologiaBase}:${p.espacos.map((e: any) => e.codigo + "/" + e.tipologia).join(",")}` : "tab";

// 1. Mesma tipologia enche a página e abre outra
let pg = paginar(["a", "b", "c", "d"].map((c) => perfil(c, "1-3 H")));
assert.equal(pg.length, 2);
assert.deepEqual(pg.map((p) => p.codigos.length), [3, 1]);

// 2. 1-2 V à esquerda + três 1-6 à direita (decisão 2)
pg = paginar([perfil("v", "1-2 V"), perfil("s1", "1-6"), perfil("s2", "1-6"), perfil("s3", "1-6"), perfil("s4", "1-6")]);
assert.equal(resumo(pg[0]), "1-2 V:v/1-2 V,s1/1-6,s2/1-6,s3/1-6");
assert.equal(pg.length, 2);

// 3. 1-2 H em cima + dois 1-4 embaixo
pg = paginar([perfil("h", "1-2 H"), perfil("q1", "1-4"), perfil("q2", "1-4")]);
assert.equal(pg.length, 1);
assert.equal(pg[0].codigos.length, 3);

// 4. Incompatível → página nova (1-3 V não cabe em sobra de 1-2 H)
pg = paginar([perfil("h", "1-2 H"), perfil("x", "1-3 V")]);
assert.equal(pg.length, 2);

// 5. Linha diferente nunca divide página
pg = paginar([perfil("a", "1-6", "GOLD"), perfil("b", "1-6", "SUPREMA")]);
assert.equal(pg.length, 2);

// 6. Compatibilidade pela geometria = tabela antiga
const antiga: Record<string, string[]> = {
  "1-2 H": ["1-3 H", "1-4", "1-6"], "1-2 V": ["1-3 V", "1-4", "1-6"], "1-3 H": ["1-6"], "1-4": ["1-6"],
  "1-3 V": [], "1-6": [],
};
for (const [base, ok] of Object.entries(antiga)) {
  const b = CELULAS[base as Tipologia];
  const geo = (Object.keys(CELULAS) as Tipologia[]).filter((t) => t !== base && CELULAS[t].w <= b.w && CELULAS[t].h <= b.h);
  assert.deepEqual(geo.sort(), ok.slice().sort(), base);
}

// 7. Tabelado longo quebra e repete cabeçalho; tabelas pequenas se juntam (mais de duas)
const longa = Array.from({ length: 60 }, (_, k) => tab("T" + k, "TUBOS REDONDOS"));
pg = paginar(longa);
assert.ok(pg.length >= 2);
assert.equal((pg[1] as any).blocos[0].continuacao, true);
assert.equal(pg.flatMap((p) => p.codigos).length, 60);
const pequenas = ["BARRAS CHATAS", "PERFIS T", "VERGALHÃO REDONDO"].flatMap((s) => [1, 2, 3, 4].map((k) => tab(s + k, s)));
pg = paginar(pequenas);
assert.equal(CONFIG.tabCabecalho, 50);
assert.equal(pg.length, 1);
assert.equal((pg[0] as any).blocos.length, 3);

// 8. Tipologia automática
assert.equal(sugerirTipologia(40, 30).tipologia, "1-6");
assert.equal(sugerirTipologia(150, 40).tipologia, "1-3 H");
assert.equal(sugerirTipologia(40, 200).tipologia, "1-3 V");
assert.equal(sugerirTipologia(150, 100).tipologia, "1-2 H");
assert.equal(sugerirTipologia(170, 220).tipologia, "1-1");

console.log("Todos os testes passaram.");
for (const t of Object.keys(CELULAS) as Tipologia[]) {
  const a = areaDesenho(t);
  console.log(t.padEnd(6), `${a.largura.toFixed(0)} × ${a.altura.toFixed(0)} mm para o desenho`);
}
