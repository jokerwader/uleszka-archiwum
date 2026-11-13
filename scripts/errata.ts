/**
 * Sprawdza erratę (dane/poprawki/errata.json): każda poprawka musi wskazywać istniejące miejsce w artykule
 * i być minimalna (kilka liter, bez zmian interpunkcji). Artykułów nie zmienia.
 *
 *   npx tsx scripts/errata.ts                       – sprawdzenie
 *   npx tsx scripts/errata.ts --scal <plik.json> …  – dołącza nowe poprawki (np. z przeglądu AI), odrzucając błędne
 */
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import nspell from "nspell";
import { Archiwum } from "../src/archiwum.js";
import { popraw, tekstBazowy, wczytajErrate, type Poprawka } from "./lib/errata.js";

const require = createRequire(import.meta.url);
const kat = require.resolve("dictionary-pl").replace(/index\.js$/, "");
const spell = nspell({ aff: readFileSync(kat + "index.aff"), dic: readFileSync(kat + "index.dic") });
const archiwum = new Archiwum(".");
const baza = new Map(archiwum.artykuly.map((a) => [a.id, tekstBazowy(a.czysty)]));
const PLIK = "dane/poprawki/errata.json";

function odleglosc(a: string, b: string): number {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++) {
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
    }
  return d[a.length][b.length];
}
const interpunkcja = (s: string) => s.replace(/[\p{L}\p{N}\s]/gu, "");
const norm = (s: string) => s.replace(/\s+/g, " ");

/** Zwraca listę problemów z poprawką (pusta = poprawka w porządku). */
function bledy(p: Poprawka): string[] {
  const b: string[] = [];
  for (const k of ["id", "zle", "dobrze", "kontekst"] as const) if (typeof p[k] !== "string" || !p[k].trim()) b.push(`brak pola ${k}`);
  if (b.length) return b;
  if (p.zle === p.dobrze) b.push("brak zmiany");
  // wyjątek: pozostałość dzielenia wyrazu na końcu linii („obraca-jącej” → „obracającej”) to nie interpunkcja
  const dzielenie = /^\p{L}+-\p{Ll}+$/u.test(p.zle) && p.zle.replace("-", "") === p.dobrze && spell.correct(p.dobrze);
  if (!dzielenie && interpunkcja(p.zle) !== interpunkcja(p.dobrze)) b.push("zmienia interpunkcję");
  const dl = Math.max(p.zle.length, p.dobrze.length);
  const d = odleglosc(p.zle, p.dobrze);
  const podwojenie = p.zle.split(/\s+/).length === 2 && p.zle.split(/\s+/)[0] === p.zle.split(/\s+/)[1] && p.dobrze === p.zle.split(/\s+/)[0];
  if (!podwojenie && d > Math.max(2, Math.ceil(dl * 0.34))) b.push(`za duża zmiana (${d} znaków)`);
  if (!norm(p.kontekst).includes(norm(p.zle))) b.push("kontekst nie zawiera błędnego fragmentu");
  if (p.id === "*" && !p.wszedzie) b.push("id „*” tylko z wszedzie: true");
  if (p.wszedzie && !/\s/.test(p.zle) && (spell.correct(p.zle) || spell.correct(p.zle.toLowerCase())))
    b.push(`„${p.zle}” jest poprawnym słowem – wszedzie musi być false`);
  const arty = p.id === "*" ? archiwum.artykuly : [archiwum.znajdz(p.id, "artykul")].filter((a) => a !== undefined);
  if (!arty.length) b.push(`nie ma artykułu ${p.id}`);
  else if (p.id !== "*" && !norm(baza.get(arty[0]!.id)!).includes(norm(p.kontekst))) b.push("kontekstu nie ma w artykule");
  else {
    const ile = arty.reduce((s, a) => s + [...popraw(baza.get(a.id)!, a.id, [p]).uzyte.values()].reduce((x, y) => x + y, 0), 0);
    if (!ile) b.push("poprawka nie trafia w tekst");
  }
  return b;
}

const klucz = (p: Poprawka) => [p.id, p.zle, p.dobrze, p.wszedzie ? "" : norm(p.kontekst)].join("\u0001");
let errata = wczytajErrate(".");
const i = process.argv.indexOf("--scal");
if (i >= 0) {
  const nowe = process.argv.slice(i + 1).flatMap((f) => JSON.parse(readFileSync(f, "utf8")) as Poprawka[]);
  const znane = new Set(errata.map(klucz));
  // słowo poprawiane „wszędzie” (id „*”) nie potrzebuje osobnych wpisów dla pojedynczych artykułów
  const globalne = new Set([...errata, ...nowe].filter((p) => p.id === "*" && p.wszedzie).map((p) => p.zle + "\u0001" + p.dobrze));
  let dodane = 0;
  const odrzucone: string[] = [];
  for (const p0 of nowe) {
    const p: Poprawka = { id: p0.id, zle: p0.zle, dobrze: p0.dobrze, kontekst: norm(p0.kontekst ?? "").trim(), wszedzie: !!p0.wszedzie, powod: p0.powod ?? "" };
    if (p.id !== "*" && p.wszedzie && globalne.has(p.zle + "\u0001" + p.dobrze)) continue;
    if (znane.has(klucz(p))) continue;
    const b = bledy(p);
    if (b.length) { odrzucone.push(`  ${p.id}: „${p.zle}” → „${p.dobrze}”: ${b.join("; ")}`); continue; }
    errata.push(p);
    znane.add(klucz(p));
    dodane++;
  }
  errata.sort((a, b) => a.id.localeCompare(b.id) || a.zle.localeCompare(b.zle, "pl"));
  writeFileSync(PLIK, JSON.stringify(errata, null, 1) + "\n", "utf8");
  console.log(`Dodano ${dodane} poprawek, odrzucono ${odrzucone.length}:`);
  console.log(odrzucone.join("\n"));
}

// sprawdzenie całej erraty
const problemy = errata.map((p) => ({ p, b: bledy(p) })).filter((x) => x.b.length);
const miejsc = archiwum.artykuly.reduce((s, a) => s + [...popraw(baza.get(a.id)!, a.id, errata).uzyte.values()].reduce((x, y) => x + y, 0), 0);
console.log(`Errata: ${errata.length} poprawek, ${miejsc} poprawionych miejsc w ${archiwum.artykuly.filter((a) => popraw(baza.get(a.id)!, a.id, errata).uzyte.size).length} artykułach.`);
if (problemy.length) {
  console.log(`Błędne poprawki (${problemy.length}):\n` + problemy.map((x) => `  ${x.p.id}: „${x.p.zle}” → „${x.p.dobrze}”: ${x.b.join("; ")}`).join("\n"));
  process.exit(1);
}
console.log("OK – każda poprawka wskazuje istniejące miejsce i jest minimalna.");
