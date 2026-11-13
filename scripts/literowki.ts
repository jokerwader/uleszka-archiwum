/**
 * Szuka podejrzanych słów (literówek) w artykułach – do przejrzenia przez człowieka lub AI.
 * Nie zmienia artykułów. Wynik: dane/poprawki/kandydaci.json
 *
 * Trzy sposoby:
 *  1. „znaki” – słowo bez polskich znaków (lub z innymi), gdy w archiwum jest poprawna forma, np. „moga” → „mogą”;
 *  2. „wariant” – rzadkie słowo bardzo podobne do słowa, które w archiwum pojawia się wielokrotnie (np. „Zusiudra” → „Ziusudra”);
 *  3. „słownik” – słowa spoza polskiego słownika (hunspell), dla których słownik ma bliską podpowiedź.
 *
 * Uruchomienie: npx tsx scripts/literowki.ts
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import nspell from "nspell";
import { Archiwum, zloz } from "../src/archiwum.js";
import { tekstBazowy } from "./lib/errata.js";

const require = createRequire(import.meta.url);
const katalogSlownika = require.resolve("dictionary-pl").replace(/index\.js$/, "");
const spell = nspell({ aff: readFileSync(katalogSlownika + "index.aff"), dic: readFileSync(katalogSlownika + "index.dic") });

const archiwum = new Archiwum(".");
type Wystapienie = { id: string; kontekst: string };
const slowa = new Map<string, { ile: number; wyst: Wystapienie[] }>(); // klucz: słowo w oryginalnej pisowni

for (const a of archiwum.artykuly) {
  const t = tekstBazowy(a.czysty);
  for (const m of t.matchAll(/\p{L}+/gu)) {
    const s = m[0];
    if (s.length < 2 || (s.length === 2 && s !== s.toLowerCase())) continue; // dwuliterowe tylko małymi literami (np. „ne” zamiast „nie”)
    const w = slowa.get(s) ?? { ile: 0, wyst: [] };
    w.ile++;
    if (w.wyst.length < 4) {
      const od = Math.max(0, m.index! - 70);
      w.wyst.push({ id: a.id, kontekst: t.slice(od, m.index! + s.length + 70).replace(/\s+/g, " ").trim() });
    }
    slowa.set(s, w);
  }
}

const poprawne = (s: string) => spell.correct(s) || spell.correct(s.toLowerCase());
const male = (s: string) => s.toLowerCase();
// częstość form w małych literach (Potop/potop razem)
const czestosc = new Map<string, number>();
for (const [s, w] of slowa) czestosc.set(male(s), (czestosc.get(male(s)) ?? 0) + w.ile);
// formy poprawne pogrupowane po „złożeniu” (bez polskich znaków) – do wykrywania brakujących znaków
const poZlozeniu = new Map<string, string[]>();
for (const s of czestosc.keys()) {
  if (!poprawne(s)) continue;
  const z = zloz(s);
  poZlozeniu.set(z, [...(poZlozeniu.get(z) ?? []), s]);
}

/** Odległość Damerau-Levenshtein (z przestawieniem sąsiednich liter). */
function odleglosc(a: string, b: string): number {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++) {
      const k = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + k);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
    }
  return d[a.length][b.length];
}

// indeks częstych słów (≥ 3 wystąpienia) po długości – do wyszukiwania wariantów
const czeste = [...czestosc].filter(([, n]) => n >= 3).map(([s]) => s);

type Kandydat = { slowo: string; sposob: string; propozycje: string[]; ile: number; wystapienia: Wystapienie[] };
const kandydaci: Kandydat[] = [];
let sprawdzone = 0;
for (const [s, w] of slowa) {
  if (poprawne(s)) continue;
  const m = male(s);
  if ((czestosc.get(m) ?? 0) > 6) continue; // słowo używane często i konsekwentnie – raczej celowe (nazwa, termin)
  sprawdzone++;
  // 1. polskie znaki
  const znaki = (poZlozeniu.get(zloz(m)) ?? []).filter((x) => x !== m);
  if (znaki.length) {
    kandydaci.push({ slowo: s, sposob: "znaki", propozycje: znaki.slice(0, 3), ile: w.ile, wystapienia: w.wyst });
    continue;
  }
  // 2. wariant słowa częstego w archiwum (także nazw własnych)
  if (m.length >= 5 && (czestosc.get(m) ?? 0) <= 2) {
    const blisko = czeste.filter((c) => Math.abs(c.length - m.length) <= 1 && c[0] === m[0] && c !== m && odleglosc(c, m) === 1);
    if (blisko.length) {
      kandydaci.push({ slowo: s, sposob: "wariant", propozycje: blisko.slice(0, 3), ile: w.ile, wystapienia: w.wyst });
      continue;
    }
  }
  // 3. słownik (tylko słowa pisane małą literą – wielką literą to najczęściej nazwy własne)
  if (s === m && m.length === 2) {
    kandydaci.push({ slowo: s, sposob: "słownik", propozycje: spell.suggest(m).slice(0, 3), ile: w.ile, wystapienia: w.wyst });
    continue;
  }
  if (s === m && m.length >= 4) {
    const sug = spell.suggest(m).filter((x) => odleglosc(x, m) <= 2).slice(0, 3);
    if (sug.length) kandydaci.push({ slowo: s, sposob: "słownik", propozycje: sug, ile: w.ile, wystapienia: w.wyst });
  }
}

mkdirSync("dane/poprawki", { recursive: true });
kandydaci.sort((a, b) => a.sposob.localeCompare(b.sposob) || a.slowo.localeCompare(b.slowo, "pl"));
writeFileSync("dane/poprawki/kandydaci.json", JSON.stringify(kandydaci, null, 1) + "\n", "utf8");
const ile = (s: string) => kandydaci.filter((k) => k.sposob === s).length;
console.log(`Słów różnych: ${slowa.size}, spoza słownika (sprawdzonych): ${sprawdzone}`);
console.log(`Kandydaci: ${kandydaci.length} (znaki: ${ile("znaki")}, wariant: ${ile("wariant")}, słownik: ${ile("słownik")}) → dane/poprawki/kandydaci.json`);
