/**
 * Kontrola opracowań i opisów zdjęć (warstwy tworzonej przez AI):
 *  - każdy artykuł ma opracowanie, a każde opracowanie ma poprawną strukturę,
 *  - KAŻDY cytat z opracowania występuje dosłownie w tekście artykułu (po ujednoliceniu odstępów),
 *  - każde zdjęcie z artykułów ma opis.
 * Generuje też spis `opracowania/README.md`.
 *
 * Uruchomienie: npm run sprawdz-opracowania
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { Archiwum } from "../src/archiwum.js";

const DZIEDZINY = ["historia", "archeologia", "astronomia", "geologia", "fizyka", "biologia", "medycyna", "żywienie", "religia", "mitologia", "polityka", "społeczeństwo", "inne"];
const archiwum = new Archiwum(".");
const odstepy = (s: string) => s.replace(/\s+/g, " ").trim();
const bledy: string[] = [];
let cytaty = 0;

for (const a of archiwum.artykuly) {
  const o = archiwum.opracowania.get(a.id);
  const plik = a.plik.replace(/^artykuly\//, "opracowania/").replace(/\.md$/, ".json");
  if (!o) {
    bledy.push(`${a.id}: brak opracowania (${plik}${existsSync(plik) ? " – plik jest, ale nie wczytał się" : ""})`);
    continue;
  }
  if (typeof o.streszczenie !== "string" || !o.streszczenie.trim()) bledy.push(`${a.id}: puste streszczenie`);
  for (const pole of ["tezy", "tematy", "osoby", "miejsca", "okresy", "zrodla_cytowane"] as const)
    if (!Array.isArray(o[pole])) bledy.push(`${a.id}: pole ${pole} nie jest listą`);
  const tekst = odstepy(a.czysty);
  for (const t of o.tezy ?? []) {
    cytaty++;
    if (!DZIEDZINY.includes(t.dziedzina)) bledy.push(`${a.id}: nieznana dziedzina „${t.dziedzina}”`);
    if (!tekst.includes(odstepy(t.cytat))) bledy.push(`${a.id}: cytat nie występuje w tekście: „${t.cytat.slice(0, 80)}…”`);
  }
}

let zdjecia = 0;
const sciezki = new Set(archiwum.artykuly.flatMap((a) => a.obrazy.map((o) => o.sciezka)));
for (const s of sciezki) {
  zdjecia++;
  if (!archiwum.opisyObrazow.has(s)) bledy.push(`brak opisu zdjęcia ${s}`);
}

// spis opracowań
const linie = [
  "# Opracowania artykułów",
  "",
  "Streszczenia, główne tezy autora (z dosłownymi cytatami), tematy, osoby, miejsca i daty dla każdego artykułu.",
  "",
  "> **Uwaga:** opracowania przygotowała sztuczna inteligencja (Claude). To pomoc w nawigacji, nie część oryginalnej strony.",
  "> Oryginalne teksty są w folderze [`artykuly/`](../artykuly) i nie zostały zmienione. Każdy cytat w opracowaniach jest",
  "> automatycznie sprawdzany (`npm run sprawdz-opracowania`) – musi występować w artykule dosłownie.",
  "",
];
let dzial = "";
for (const a of archiwum.artykuly) {
  const o = archiwum.opracowania.get(a.id);
  if (!o || (!o.tezy.length && o.streszczenie.length < 140)) continue; // pomijamy galerie i strony z samym zdjęciem
  if (a.dzial !== dzial) {
    dzial = a.dzial;
    linie.push(`## ${dzial}`, "");
  }
  const json = a.plik.replace(/^artykuly\//, "").replace(/\.md$/, ".json");
  linie.push(`### [${a.tytul}](../${encodeURI(a.plik)})`, "", o.streszczenie, "");
  if (o.tematy.length) linie.push(`*Tematy:* ${o.tematy.join(", ")}  `, `*Tezy:* ${o.tezy.length} · [pełne opracowanie (JSON)](${encodeURI(json)})`, "");
}
writeFileSync("opracowania/README.md", linie.join("\n"), "utf8");

console.log(`Opracowania: ${archiwum.opracowania.size}/${archiwum.artykuly.length}, cytatów sprawdzonych: ${cytaty}. Zdjęcia z opisem: ${zdjecia - bledy.filter((b) => b.startsWith("brak opisu")).length}/${zdjecia}.`);
if (bledy.length) {
  console.log(`Problemy (${bledy.length}):`);
  for (const b of bledy.slice(0, 50)) console.log(" - " + b);
  process.exit(1);
}
console.log("Wszystko w porządku.");
