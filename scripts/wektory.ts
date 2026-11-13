/**
 * Liczy „wektory znaczenia” dla wyszukiwania semantycznego i zapisuje je w `dane/wektory/`.
 *   npm run wektory              – archiwum (artykuły + opracowania + opisy zdjęć), kilka minut
 *   npm run wektory -- biblioteka – dzieła z biblioteki (32 MB tekstu), kilkadziesiąt minut
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { Archiwum } from "../src/archiwum.js";
import { MODEL, fragmentuj, wektory, type Fragment, type Zbior } from "../src/semantyka.js";

const zbior: Zbior = process.argv.includes("biblioteka") ? "biblioteka" : "archiwum";
const archiwum = new Archiwum(".");
const fragmenty: Fragment[] = [];
const teksty: string[] = [];

if (zbior === "archiwum") {
  for (const a of archiwum.artykuly) {
    for (const f of fragmentuj(a.czysty, 900)) {
      fragmenty.push({ d: a.id, od: f.od, do: f.do, r: "tekst" });
      teksty.push(`${a.tytul}. ${a.czysty.slice(f.od, f.do)}`);
    }
    const o = archiwum.opracowania.get(a.id);
    if (o?.streszczenie) {
      fragmenty.push({ d: a.id, od: 0, do: 0, r: "streszczenie" });
      teksty.push(`${a.tytul}. ${o.streszczenie} ${o.tezy.map((t) => t.teza).join(" ")} Tematy: ${o.tematy.join(", ")}`);
    }
    for (const ob of a.obrazy) {
      const opis = archiwum.opisObrazu(ob.sciezka);
      if (!opis || fragmenty.some((f) => f.r === "obraz" && f.s === ob.sciezka)) continue;
      fragmenty.push({ d: a.id, od: 0, do: 0, r: "obraz", s: ob.sciezka });
      teksty.push(`Zdjęcie w artykule „${a.tytul}”: ${opis}`);
    }
  }
} else {
  // teksty w językach oryginału (greka, sanskryt…) bez wektorów – szuka się po przekładach i numeracji cytowań
  for (const k of archiwum.ksiazki.filter((k) => !k.meta.rodzaj_tekstu))
    for (const f of fragmentuj(k.czysty, 1200)) {
      fragmenty.push({ d: k.id, od: f.od, do: f.do, r: "tekst" });
      teksty.push(`${k.tytul}. ${k.czysty.slice(f.od, f.do)}`);
    }
}

console.log(`${zbior}: ${fragmenty.length} fragmentów, liczę wektory modelem ${MODEL}…`);
const PACZKA = 32;
let wymiar = 0;
const czesci: Int8Array[] = [];
const start = Date.now();
for (let i = 0; i < teksty.length; i += PACZKA) {
  const v = await wektory(teksty.slice(i, i + PACZKA).map((t) => t.slice(0, 2000)), "passage");
  wymiar = v[0].length;
  for (const w of v) czesci.push(Int8Array.from(w, (x) => Math.max(-127, Math.min(127, Math.round(x * 127)))));
  if ((i / PACZKA) % 25 === 0) {
    const t = (Date.now() - start) / 1000;
    console.log(`  ${i + PACZKA}/${teksty.length} (${Math.round(t)} s, zostało ok. ${Math.round((t / (i + PACZKA)) * (teksty.length - i - PACZKA))} s)`);
  }
}
const dane = new Int8Array(czesci.length * wymiar);
czesci.forEach((c, i) => dane.set(c, i * wymiar));
mkdirSync("dane/wektory", { recursive: true });
writeFileSync(`dane/wektory/${zbior}.bin`, dane);
writeFileSync(`dane/wektory/${zbior}.json`, JSON.stringify({ model: MODEL, wymiar, fragmenty }));
console.log(`Zapisano dane/wektory/${zbior}.bin (${Math.round(dane.length / 1024)} KB) i ${zbior}.json, ${Math.round((Date.now() - start) / 1000)} s.`);
