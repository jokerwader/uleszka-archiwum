/**
 * Tworzy folder `dla-ai/`: całe archiwum w kilku dużych plikach tekstowych (jeden na dział),
 * gotowych do wgrania jako „wiedza” do własnego GPT w ChatGPT albo do projektu w Claude.
 * Tekst artykułów jest ten sam co w `artykuly/` – usuwane są tylko odnośniki do plików zdjęć.
 *
 * Uruchomienie: npm run pakiety
 */
import { mkdirSync, rmSync, writeFileSync, copyFileSync } from "node:fs";
import { Archiwum } from "../src/archiwum.js";

const archiwum = new Archiwum(".");
const WYJSCIE = "dla-ai";
rmSync(WYJSCIE, { recursive: true, force: true });
mkdirSync(WYJSCIE);

const slug = (s: string) =>
  s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

const NAGLOWEK = (dzial: string, n: number) => `# Archiwum uleszka.net – dział „${dzial}”

Archiwum polskiego serwisu www.uleszka.net (autor: Leszek Klimek, lata ok. 2004–2007), dział „${dzial}”: ${n} stron.
Teksty są przeniesione bez zmian względem oryginału. Każdy artykuł zaczyna się od nagłówka „## ARTYKUŁ:”.
Zdjęcia są pominięte (w ich miejscu jest znacznik [obraz]); pełne archiwum ze zdjęciami: https://github.com/jokerwader/uleszka-archiwum
`;

const pliki: { plik: string; dzial: string; n: number; znaki: number }[] = [];
archiwum.dzialy.forEach((dzial, i) => {
  const lista = archiwum.artykuly.filter((a) => a.dzial === dzial);
  const czesci = lista.map((a) => {
    const tresc = a.tresc
      .replace(/\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)/g, "[obraz]") // obraz będący linkiem
      .replace(/!\[([^\]]*)\]\([^)]*\)/g, (_m, alt: string) => (alt ? `[obraz: ${alt}]` : "[obraz]"))
      .replace(/\[([^\]]*)\]\(artykul:([^)]+)\)/g, "$1 (→ artykuł $2)");
    return [
      `## ARTYKUŁ: ${a.tytul}`,
      `id: ${a.id} | dział: ${a.dzial}${a.rodzic ? ` | podstrona artykułu: ${a.rodzic}` : ""} | oryginał: ${a.adresOryginalny}`,
      "",
      tresc,
    ].join("\n");
  });
  const plik = `${WYJSCIE}/${String(i + 1).padStart(2, "0")}-${slug(dzial)}.md`;
  const tekst = `${NAGLOWEK(dzial, lista.length)}\n${czesci.join("\n\n---\n\n")}\n`;
  writeFileSync(plik, tekst, "utf8");
  pliki.push({ plik, dzial, n: lista.length, znaki: tekst.length });
});
copyFileSync("KATALOG.md", `${WYJSCIE}/00-katalog.md`);

for (const p of pliki) console.log(`${p.plik}: ${p.n} stron, ${Math.round(p.znaki / 1000)} tys. znaków`);
