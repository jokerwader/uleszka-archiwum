/**
 * Odrzuca zdjęcia atlasu wskazane przy przeglądzie arkuszy (scripts/atlas-arkusze.ts):
 * dopisuje je do atlas/odrzucone.json (nie wrócą przy kolejnym pobieraniu) i usuwa z atlas/dane.json.
 * Wszystkie pozostałe zdjęcia zostają (przeszły przegląd).
 *
 * Uruchomienie: npx tsx scripts/atlas-odrzuc.ts <spis.json z arkuszy> <odrzuty.json>
 *   odrzuty.json: { "<id miejsca>": { "numery": [3, 8], "powod": "ludzie pozujący do zdjęcia" } }
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { slug } from "./lib/atlas.js";

const [plikSpisu, plikOdrzutow] = process.argv.slice(2);
if (!plikSpisu || !plikOdrzutow) throw new Error("Użycie: npx tsx scripts/atlas-odrzuc.ts <spis.json> <odrzuty.json>");
const spis: Record<string, string[]> = JSON.parse(readFileSync(plikSpisu, "utf8"));
const odrzuty: Record<string, { numery: number[]; powod?: string }> = JSON.parse(readFileSync(plikOdrzutow, "utf8"));
const odrzucone: Record<string, string> = JSON.parse(readFileSync("atlas/odrzucone.json", "utf8"));
const dane: Record<string, { zdjecia: { plik: string }[] }> = JSON.parse(readFileSync("atlas/dane.json", "utf8"));


let ile = 0;
for (const [id, { numery, powod }] of Object.entries(odrzuty)) {
  for (const n of numery) {
    const plik = spis[id]?.[n - 1];
    if (!plik) { console.warn(`⚠ ${id}: nie ma zdjęcia nr ${n}`); continue; }
    odrzucone[plik] = powod ?? "przegląd: zdjęcie nie pokazuje budowli";
    ile++;
  }
}
let usuniete = 0;
for (const [nazwa, d] of Object.entries(dane)) {
  const przed = d.zdjecia.length;
  d.zdjecia = d.zdjecia.filter((z) => !odrzucone[z.plik]);
  usuniete += przed - d.zdjecia.length;
  void slug(nazwa);
}
// zdjęcia z Openverse leżą w osobnym pliku
if (existsSync("atlas/openverse.json")) {
  const ov: Record<string, { plik: string }[]> = JSON.parse(readFileSync("atlas/openverse.json", "utf8"));
  for (const n of Object.keys(ov)) { const przed = ov[n].length; ov[n] = ov[n].filter((z) => !odrzucone[z.plik]); usuniete += przed - ov[n].length; }
  writeFileSync("atlas/openverse.json", JSON.stringify(ov, null, 1) + "\n");
}
writeFileSync("atlas/odrzucone.json", JSON.stringify(Object.fromEntries(Object.entries(odrzucone).sort()), null, 1) + "\n");
writeFileSync("atlas/dane.json", JSON.stringify(dane, null, 1) + "\n");
console.log(`Odrzucono ${ile} zdjęć (razem na liście: ${Object.keys(odrzucone).length}); z atlasu ubyło ${usuniete}.`);
