/**
 * Kontrola wierności: dla każdego artykułu porównuje ciąg liter i cyfr z oryginalnego HTML
 * z ciągiem liter i cyfr w pliku Markdown. Jeśli się różnią – tekst został zmieniony.
 *
 * Uruchomienie: npm run sprawdz
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import * as cheerio from "cheerio";
import { dekoduj } from "./dekoduj.js";

const litery = (s: string) => (s.match(/[\p{L}\p{N}]/gu) ?? []).join("");

function tekstHtml(plik: string) {
  const $ = cheerio.load(dekoduj(readFileSync(plik)));
  $("script, style, noscript, head, map, title").remove();
  // listy numerowane: przeglądarka sama wyświetla numery 1., 2., … – Markdown zapisuje je jawnie
  $("ol").each((_, ol) => {
    const start = Number($(ol).attr("start") ?? 1);
    $(ol)
      .children("li")
      .each((i, li) => {
        $(li).prepend(`${start + i}. `);
      });
  });
  return litery($("body").length ? $("body").text() : $.root().text());
}
function tekstMd(md: string) {
  const bez = md
    .replace(/^---\n[\s\S]*?\n---\n/, "") // nagłówek z opisem
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "") // obrazki (alt nie jest tekstem strony)
    .replace(/\]\([^)]*\)/g, "]") // adresy linków
    .replace(/<br>/g, " "); // łamanie linii w komórkach tabel (znacznik, nie tekst)
  return litery(bez);
}

let bledy = 0;
let sprawdzone = 0;
let znaki = 0;
for (const dzial of readdirSync("artykuly")) {
  for (const f of readdirSync(join("artykuly", dzial))) {
    const md = readFileSync(join("artykuly", dzial, f), "utf8");
    const zrodlo = md.match(/^plik_zrodlowy: "(.+)"$/m)![1];
    const a = tekstHtml(zrodlo);
    const b = tekstMd(md);
    sprawdzone++;
    znaki += a.length;
    if (a !== b) {
      bledy++;
      let i = 0;
      while (a[i] === b[i]) i++;
      console.log(`RÓŻNICA ${dzial}/${f} (pozycja ${i}):\n  oryginał: …${a.slice(i - 30, i + 50)}\n  markdown: …${b.slice(i - 30, i + 50)}`);
    }
  }
}
console.log(`Sprawdzono ${sprawdzone} artykułów (${znaki} liter i cyfr). Różnic: ${bledy}.`);
process.exit(bledy ? 1 : 0);
