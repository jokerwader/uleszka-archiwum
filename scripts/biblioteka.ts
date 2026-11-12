/**
 * Buduje folder `biblioteka/`: pełne teksty dzieł, na które powołuje się autor strony,
 * a które są w domenie publicznej i legalnie dostępne do kopiowania.
 * Źródła: Project Gutenberg (z oryginalną licencją PG w pliku), Wolne Lektury, Wikiźródła.
 *
 * Uruchomienie: npm run biblioteka   (pobiera tylko brakujące pliki; --od-nowa pobiera wszystko)
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import * as cheerio from "cheerio";

type Zrodlo =
  | { typ: "gutenberg"; numer: number }
  | { typ: "wolnelektury"; slug: string }
  | { typ: "wikiźródła"; strony: string[] };

type Pozycja = {
  id: string;
  tytul: string;
  autor: string;
  tlumacz?: string;
  jezyk: "pl" | "en";
  zrodlo: Zrodlo;
  licencja: string;
  cytowane_w: string[]; // id artykułów archiwum
  uwagi?: string;
};

const PG = "Domena publiczna (USA i UE). Plik zawiera oryginalną licencję Project Gutenberg.";
const WL = "Domena publiczna. Wydanie Wolnych Lektur; materiały redakcyjne na licencji CC BY-SA 3.0.";
const WS = "Tekst przekładu w domenie publicznej. Transkrypcja z Wikiźródeł na licencji CC BY-SA 4.0.";

export const POZYCJE: Pozycja[] = [
  // ---------- po polsku ----------
  { id: "platon-timajos", tytul: "Timajos", autor: "Platon", tlumacz: "Władysław Witwicki", jezyk: "pl", zrodlo: { typ: "wolnelektury", slug: "platon-timajos" }, licencja: WL, cytowane_w: ["11atlantyda/atlant", "atomwoj/bogatom01"], uwagi: "Początek opowieści o Atlantydzie." },
  { id: "platon-kritias", tytul: "Kritias", autor: "Platon", tlumacz: "Władysław Witwicki", jezyk: "pl", zrodlo: { typ: "wolnelektury", slug: "platon-kritias" }, licencja: WL, cytowane_w: ["11atlantyda/atlant", "01potop/potop", "04chrono/chronos", "05bogowie/bogowie", "survival", "warownie/kazimierz", "ameryka/folklor", "wrozby/rok2012", "upadek/katrina1"], uwagi: "Opis Atlantydy i jej upadku." },
  { id: "ksiega-rodzaju", tytul: "Genesis. Księga Rodzaju", autor: "Biblia", jezyk: "pl", zrodlo: { typ: "wolnelektury", slug: "genesis-ksiega-rodzaju-bereszit" }, licencja: WL, cytowane_w: ["01potop/potop", "04chrono/chronos", "05bogowie/bogowie", "10woda/bogwody", "atomwoj/bogatom01", "szypow"], uwagi: "Potop, Nefilim, Sodoma i Gomora." },
  { id: "herodot-dzieje", tytul: "Dzieje", autor: "Herodot", tlumacz: "Seweryn Bronikowski (1862)", jezyk: "pl", zrodlo: { typ: "wikiźródła", strony: ["Dzieje (Herodot)/całość"] }, licencja: WS, cytowane_w: ["04chrono/chronos", "07piramidy/piramidy", "08egipt/egipt", "13celtowie/celt", "atomwoj/bogatom01", "wrozby/rok2012", "wrozby/nostradamus"], uwagi: "Egipt, labirynt i jezioro Mojrisa – księga II (Euterpe). Pisownia XIX-wieczna." },
  { id: "owidiusz-przemiany", tytul: "Przemiany (Metamorfozy)", autor: "Owidiusz", tlumacz: "Bruno Kiciński", jezyk: "pl", zrodlo: { typ: "wikiźródła", strony: ["Przemiany (Owidiusz)"] }, licencja: WS, cytowane_w: ["01potop/potop", "atomwoj/bogatom01"], uwagi: "Wieki świata, giganci, potop Deukaliona." },
  { id: "homer-iliada", tytul: "Iliada", autor: "Homer", tlumacz: "Franciszek Ksawery Dmochowski", jezyk: "pl", zrodlo: { typ: "wolnelektury", slug: "homer-iliada" }, licencja: WL, cytowane_w: ["04chrono/chronos"] },
  // ---------- po angielsku ----------
  { id: "ksiega-henocha", tytul: "The Book of Enoch", autor: "Księga Henocha (apokryf)", tlumacz: "R. H. Charles (1917)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 77935 }, licencja: PG, cytowane_w: ["henoch/henoch", "01potop/potop", "05bogowie/bogowie", "zagadki/zagadki", "hipoteza/hipowusz2", "oszusci", "medalt/orme/gwog"], uwagi: "Upadli aniołowie, olbrzymi, księga astronomiczna." },
  { id: "popol-vuh", tytul: "The Popol Vuh", autor: "Popol Vuh (księga Majów Kicze)", tlumacz: "Lewis Spence (1908)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 56550 }, licencja: PG, cytowane_w: ["05bogowie/bogowie", "ameryka/folklor"], uwagi: "Swobodne opracowanie, nie przekład naukowy." },
  { id: "chilam-balam", tytul: "The Books of Chilan Balam", autor: "Daniel G. Brinton (o księgach Chilam Balam)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 31610 }, licencja: PG, cytowane_w: ["01potop/potop", "11atlantyda/atlant"], uwagi: "Omówienie z fragmentami (1882), nie pełny przekład." },
  { id: "le-plongeon-sacred-mysteries", tytul: "Sacred Mysteries Among the Mayas and the Quiches", autor: "Augustus Le Plongeon", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 57458 }, licencja: PG, cytowane_w: ["01potop/potop", "11atlantyda/atlant", "wrozby/rok2012"], uwagi: "Autor „przekładu” Kodeksu Troano o Mu; jego odczytania są dziś uznawane za błędne." },
  { id: "gilgamesz", tytul: "An Old Babylonian Version of the Gilgamesh Epic", autor: "Epos o Gilgameszu", tlumacz: "M. Jastrow, A. T. Clay (1920)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 11000 }, licencja: PG, cytowane_w: ["05bogowie/bogowie", "01potop/potop"], uwagi: "Wersja starobabilońska (fragment eposu)." },
  { id: "kodeks-hammurabiego", tytul: "The Oldest Code of Laws in the World", autor: "Hammurabi", tlumacz: "C. H. W. Johns (1903)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 17150 }, licencja: PG, cytowane_w: ["05bogowie/bogowie", "medalt/sitwa"] },
  { id: "ksiega-umarlych", tytul: "The Egyptian Book of the Dead", autor: "Księga Umarłych", tlumacz: "P. Le Page Renouf, É. Naville", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 69566 }, licencja: PG, cytowane_w: ["medalt/orme/orme1"] },
  { id: "apokryfy-nt", tytul: "The Suppressed Gospels and Epistles of the Original New Testament", autor: "Apokryfy Nowego Testamentu", tlumacz: "William Wake (XVIII w.)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 6516 }, licencja: PG, cytowane_w: ["medalt/orme/gwog"] },
  { id: "talmud-midrasz-kabala", tytul: "Hebraic Literature; Translations from the Talmud, Midrashim and Kabbala", autor: "Talmud, Midrasz, Kabała (wybór)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 14368 }, licencja: PG, cytowane_w: ["insygnia/korony", "medalt/orme/orme1", "medalt/orme/gwog"] },
  { id: "strabon-geografia-3", tytul: "The Geography of Strabo, Volume 3", autor: "Strabon", tlumacz: "H. C. Hamilton, W. Falconer", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 44886 }, licencja: PG, cytowane_w: ["07piramidy/piramidy", "08egipt/egipt"], uwagi: "Tom 3 zawiera księgę XVII o Egipcie (piramidy, labirynt, jezioro Mojrisa)." },
  { id: "pliniusz-historia-naturalna-6", tytul: "The Natural History of Pliny, Volume 6", autor: "Pliniusz Starszy", tlumacz: "J. Bostock, H. T. Riley", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 62704 }, licencja: PG, cytowane_w: ["07piramidy/piramidy", "08egipt/egipt"], uwagi: "Tom 6 zawiera księgę XXXVI (piramidy, labirynty)." },
  { id: "apulejusz-zloty-osiol", tytul: "The Golden Asse", autor: "Apulejusz", tlumacz: "William Adlington", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 1666 }, licencja: PG, cytowane_w: ["08egipt/egipt"] },
  { id: "argonautyka", tytul: "The Argonautica", autor: "Apolloniusz z Rodos", tlumacz: "E. P. Coleridge", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 830 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "cezar-wojna-galijska", tytul: "\"De Bello Gallico\" and Other Commentaries", autor: "Juliusz Cezar", tlumacz: "W. A. McDevitte, W. S. Bohn", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 10657 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "augustyn-panstwo-boze-2", tytul: "The City of God, Volume II", autor: "św. Augustyn", tlumacz: "Marcus Dods", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 45305 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"], uwagi: "Tom 2 zawiera księgę XV (o olbrzymach, XV,23)." },
  { id: "calmet-zjawy", tytul: "The Phantom World", autor: "Augustin Calmet", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 29412 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "nostradamus-proroctwa", tytul: "The True Prophecies or Prognostications of Michael Nostradamus", autor: "Nostradamus", tlumacz: "Theophilus de Garencières (1672)", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 68907 }, licencja: PG, cytowane_w: ["wrozby/nostradamus", "wrozby/rok2012", "atomwoj/bogatom01", "quake/quake", "blogier3"] },
  { id: "ramajana", tytul: "The Rámáyan of Válmíki", autor: "Walmiki", tlumacz: "Ralph T. H. Griffith", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 24869 }, licencja: PG, cytowane_w: ["04chrono/chronos", "atomwoj/bogatom01"] },
  { id: "mahabharata-1", tytul: "The Mahabharata, Volume 1", autor: "Wjasa", tlumacz: "Kisari Mohan Ganguli", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 15474 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"], uwagi: "Wydanie Gutenberga obejmuje tylko część eposu." },
  { id: "mahabharata-2", tytul: "The Mahabharata, Volume 2", autor: "Wjasa", tlumacz: "Kisari Mohan Ganguli", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 15475 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "mahabharata-3", tytul: "The Mahabharata, Volume 3", autor: "Wjasa", tlumacz: "Kisari Mohan Ganguli", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 15476 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "mahabharata-4", tytul: "The Mahabharata, Volume 4", autor: "Wjasa", tlumacz: "Kisari Mohan Ganguli", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 15477 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "fort-book-of-the-damned", tytul: "The Book of the Damned", autor: "Charles Fort", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 22472 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"] },
  { id: "fort-new-lands", tytul: "New Lands", autor: "Charles Fort", jezyk: "en", zrodlo: { typ: "gutenberg", numer: 78289 }, licencja: PG, cytowane_w: ["atomwoj/bogatom01"], uwagi: "Fort pisze tu m.in. o obiektach widzianych na Księżycu." },
];

const UA = { "User-Agent": "uleszka-archiwum/1.2 (archiwum dokumentacyjne; https://github.com/jokerwader/uleszka-archiwum)" };

async function pobierz(url: string): Promise<string> {
  for (let proba = 1; proba <= 3; proba++) {
    const r = await fetch(url, { headers: UA });
    if (r.ok) return await r.text();
    if (proba === 3) throw new Error(`${r.status} ${url}`);
    await new Promise((ok) => setTimeout(ok, 3000 * proba));
  }
  throw new Error("nieosiągalne");
}

const RZYMSKIE: Record<string, number> = { I: 1, V: 5, X: 10, L: 50, C: 100 };
const zRzymskiej = (s: string) =>
  [...s].reduce((acc, ch, i, a) => (RZYMSKIE[ch] < (RZYMSKIE[a[i + 1]] ?? 0) ? acc - RZYMSKIE[ch] : acc + RZYMSKIE[ch]), 0);

async function wikiStrona(tytul: string): Promise<string> {
  const url = `https://pl.wikisource.org/w/api.php?action=parse&format=json&formatversion=2&prop=text&page=${encodeURIComponent(tytul)}`;
  const j = JSON.parse(await pobierz(url));
  if (!j.parse) throw new Error(`Brak strony ${tytul}`);
  const $ = cheerio.load(j.parse.text);
  $(".mw-editsection, .reference, .references, style, script, table.toccolours, .noprint, .ws-noexport, #ws-data").remove();
  $("br").replaceWith("\n");
  $("p, div, h1, h2, h3, h4, li, dd").each((_, el) => {
    $(el).append("\n\n");
  });
  return $.root().text().replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

async function wikiSeria(prefiks: string): Promise<string> {
  // wszystkie podstrony (np. „Przemiany (Owidiusz)/XII”), posortowane: wstęp, potem numery rzymskie
  const url = `https://pl.wikisource.org/w/api.php?action=query&list=allpages&apnamespace=0&aplimit=500&format=json&apprefix=${encodeURIComponent(prefiks + "/")}`;
  const j = JSON.parse(await pobierz(url));
  const tytuly: string[] = j.query.allpages.map((p: { title: string }) => p.title);
  const numer = (t: string) => {
    const k = t.slice(prefiks.length + 1);
    return /^[IVXLC]+$/.test(k) ? zRzymskiej(k) : k.startsWith("Od wydawcy") ? 0 : 10000;
  };
  tytuly.sort((a, b) => numer(a) - numer(b));
  const czesci: string[] = [];
  for (const t of tytuly) {
    czesci.push(`## ${t.slice(prefiks.length + 1)}\n\n${await wikiStrona(t)}`);
    await new Promise((ok) => setTimeout(ok, 300));
  }
  return czesci.join("\n\n");
}

async function tekst(p: Pozycja): Promise<string> {
  const z = p.zrodlo;
  if (z.typ === "gutenberg") return (await pobierz(`https://www.gutenberg.org/cache/epub/${z.numer}/pg${z.numer}.txt`)).replace(/\r\n/g, "\n").replace(/^﻿/, "");
  if (z.typ === "wolnelektury") return (await pobierz(`https://wolnelektury.pl/media/book/txt/${z.slug}.txt`)).replace(/\r\n/g, "\n");
  const czesci: string[] = [];
  for (const s of z.strony) czesci.push(s.endsWith("/całość") ? await wikiStrona(s) : await wikiSeria(s));
  return czesci.join("\n\n");
}

export function adresZrodla(z: Zrodlo): string {
  if (z.typ === "gutenberg") return `https://www.gutenberg.org/ebooks/${z.numer}`;
  if (z.typ === "wolnelektury") return `https://wolnelektury.pl/katalog/lektura/${z.slug}/`;
  return `https://pl.wikisource.org/wiki/${encodeURIComponent(z.strony[0].replace(/\/całość$/, "")).replace(/%2F/g, "/")}`;
}

async function main() {
  const odNowa = process.argv.includes("--od-nowa");
  mkdirSync("biblioteka", { recursive: true });
  for (const p of POZYCJE) {
    const plik = `biblioteka/${p.id}.md`;
    if (existsSync(plik) && !odNowa) {
      console.log(`= ${p.id} (już jest)`);
      continue;
    }
    const t = await tekst(p);
    const fm = [
      "---",
      `id: ${JSON.stringify(p.id)}`,
      `tytul: ${JSON.stringify(p.tytul)}`,
      `autor: ${JSON.stringify(p.autor)}`,
      p.tlumacz ? `tlumacz: ${JSON.stringify(p.tlumacz)}` : null,
      `jezyk: ${p.jezyk}`,
      `zrodlo: ${JSON.stringify(adresZrodla(p.zrodlo))}`,
      `licencja: ${JSON.stringify(p.licencja)}`,
      `cytowane_w: ${JSON.stringify(p.cytowane_w)}`,
      p.uwagi ? `uwagi: ${JSON.stringify(p.uwagi)}` : null,
      "---",
    ].filter(Boolean).join("\n");
    writeFileSync(plik, `${fm}\n\n${t.trim()}\n`, "utf8");
    console.log(`+ ${p.id}: ${Math.round(t.length / 1000)} tys. znaków`);
    await new Promise((ok) => setTimeout(ok, 1000));
  }
  // spis biblioteki
  const linie = [
    "# Biblioteka – dzieła, na które powołuje się autor",
    "",
    "Pełne teksty dawnych dzieł cytowanych na stronie uleszka.net, które są w **domenie publicznej** i można je legalnie kopiować.",
    "Dzięki nim asystent AI może sprawdzić, co naprawdę jest w źródle, na które powołuje się autor.",
    "Pełne zestawienie wszystkich cytowanych książek (także tych, których nie ma za darmo): [docs/ksiazki.md](../docs/ksiazki.md).",
    "",
    "| Dzieło | Autor | Przekład | Język | Wielkość | Źródło |",
    "|---|---|---|---|---|---|",
  ];
  for (const p of POZYCJE) {
    const plik = `biblioteka/${p.id}.md`;
    const n = existsSync(plik) ? readFileSync(plik, "utf8").length : 0;
    linie.push(`| [${p.tytul}](${p.id}.md) | ${p.autor} | ${p.tlumacz ?? "—"} | ${p.jezyk === "pl" ? "polski" : "angielski"} | ${Math.round(n / 1000)} tys. znaków | [${p.zrodlo.typ}](${adresZrodla(p.zrodlo)}) |`);
  }
  linie.push("", "Licencje: teksty w domenie publicznej. Pliki z Project Gutenberg zawierają oryginalną licencję PG; wydania Wolnych Lektur i transkrypcje Wikiźródeł – licencje CC BY-SA (podane w nagłówku każdego pliku).", "");
  writeFileSync("biblioteka/README.md", linie.join("\n"), "utf8");
}

if (process.argv[1]?.endsWith("biblioteka.ts")) await main();
