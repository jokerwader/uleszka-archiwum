/**
 * Buduje folder `biblioteka/`: pełne teksty dzieł, na które powołuje się autor strony,
 * a które są w domenie publicznej i legalnie dostępne do kopiowania.
 * Źródła: Project Gutenberg (z oryginalną licencją PG w pliku), Wolne Lektury, Wikiźródła.
 *
 * Uruchomienie: npm run biblioteka   (pobiera tylko brakujące pliki; --od-nowa pobiera wszystko)
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import * as cheerio from "cheerio";
import { JEZYKI } from "../src/archiwum.js";

type Zrodlo =
  | { typ: "gutenberg"; numer: number }
  | { typ: "wolnelektury"; slug: string }
  | { typ: "wikiźródła"; strony: string[] }
  // ---- źródła tekstów w językach oryginału ----
  | { typ: "perseus"; plik: string } // np. "canonical-greekLit/data/tlg0059/tlg031/tlg0059.tlg031.perseus-grc2"
  | { typ: "wlc"; ksiega: string } // Kodeks Leningradzki (Westminster Leningrad Codex) z Open Scriptures
  | { typ: "wikisource"; jezyk: string; strony: string[]; seria?: boolean } // strony HTML; seria = wszystkie podstrony
  | { typ: "sa-ramajana" }
  | { typ: "sa-mahabharata" };

type Pozycja = {
  id: string;
  tytul: string;
  autor: string;
  tlumacz?: string;
  jezyk: "pl" | "en" | "grc" | "la" | "he" | "fr" | "sa";
  zrodlo: Zrodlo;
  licencja: string;
  cytowane_w: string[]; // id artykułów archiwum
  uwagi?: string;
  rodzaj_tekstu?: "oryginał"; // tekst w języku oryginału (nie przekład)
  przeklady?: string[]; // id przekładów tego dzieła w bibliotece
  wydanie?: string; // wydanie krytyczne, z którego pochodzi tekst
};


const PG = "Domena publiczna (USA i UE). Plik zawiera oryginalną licencję Project Gutenberg.";
const WL = "Domena publiczna. Wydanie Wolnych Lektur; materiały redakcyjne na licencji CC BY-SA 3.0.";
const WS = "Tekst przekładu w domenie publicznej. Transkrypcja z Wikiźródeł na licencji CC BY-SA 4.0.";
const PERSEUS = "Tekst wydania w domenie publicznej. Cyfrowe opracowanie (TEI): Perseus Digital Library, licencja CC BY-SA 4.0.";
const WSO = (j: string) => `Tekst w domenie publicznej. Transkrypcja z Wikiźródeł (${j}.wikisource.org) na licencji CC BY-SA 4.0.`;

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

// ---------- teksty w językach oryginału ----------
// cytowane_w uzupełniane automatycznie z przekładów (pole przeklady)
const P = (plik: string): Zrodlo => ({ typ: "perseus", plik });
const ORYGINALY: Omit<Pozycja, "cytowane_w" | "rodzaj_tekstu">[] = [
  { id: "platon-timajos-grc", tytul: "Τίμαιος (Timajos)", autor: "Platon", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0059/tlg031/tlg0059.tlg031.perseus-grc2"), licencja: PERSEUS, przeklady: ["platon-timajos"], uwagi: "Numeracja Stephanusa, np. [24e]." },
  { id: "platon-kritias-grc", tytul: "Κριτίας (Kritias)", autor: "Platon", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0059/tlg032/tlg0059.tlg032.perseus-grc2"), licencja: PERSEUS, przeklady: ["platon-kritias"], uwagi: "Numeracja Stephanusa, np. [113c]." },
  { id: "herodot-dzieje-grc", tytul: "Ἱστορίαι (Dzieje)", autor: "Herodot", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0016/tlg001/tlg0016.tlg001.perseus-grc2"), licencja: PERSEUS, przeklady: ["herodot-dzieje"], uwagi: "Numeracja księga.rozdział.paragraf, np. [2.148.1]." },
  { id: "homer-iliada-grc", tytul: "Ἰλιάς (Iliada)", autor: "Homer", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2"), licencja: PERSEUS, przeklady: ["homer-iliada"], uwagi: "Numeracja pieśń.wers, np. [1.37]." },
  { id: "strabon-geografia-grc", tytul: "Γεωγραφικά (Geografia)", autor: "Strabon", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0099/tlg001/tlg0099.tlg001.perseus-grc2"), licencja: PERSEUS, przeklady: ["strabon-geografia-3"], uwagi: "Całe dzieło (17 ksiąg); Egipt w księdze 17. Numeracja księga.rozdział.paragraf." },
  { id: "argonautyka-grc", tytul: "Ἀργοναυτικά (Argonautyki)", autor: "Apolloniusz z Rodos", jezyk: "grc", zrodlo: P("canonical-greekLit/data/tlg0001/tlg001/tlg0001.tlg001.perseus-grc2"), licencja: PERSEUS, przeklady: ["argonautyka"], uwagi: "Numeracja księga.wers." },
  { id: "owidiusz-przemiany-la", tytul: "Metamorphoses (Przemiany)", autor: "Owidiusz", jezyk: "la", zrodlo: P("canonical-latinLit/data/phi0959/phi006/phi0959.phi006.perseus-lat2"), licencja: PERSEUS, przeklady: ["owidiusz-przemiany"], uwagi: "Numeracja księga.wers, np. [1.262]." },
  { id: "pliniusz-historia-naturalna-la", tytul: "Naturalis Historia (Historia naturalna)", autor: "Pliniusz Starszy", jezyk: "la", zrodlo: P("canonical-latinLit/data/phi0978/phi001/phi0978.phi001.perseus-lat2"), licencja: PERSEUS, przeklady: ["pliniusz-historia-naturalna-6"], uwagi: "Całe dzieło (37 ksiąg); piramidy i labirynty w księdze 36. Numeracja księga.paragraf, np. [36.75]." },
  { id: "cezar-wojna-galijska-la", tytul: "De bello Gallico (Wojna galijska)", autor: "Juliusz Cezar", jezyk: "la", zrodlo: P("canonical-latinLit/data/phi0448/phi001/phi0448.phi001.perseus-lat2"), licencja: PERSEUS, przeklady: ["cezar-wojna-galijska"], uwagi: "Numeracja księga.rozdział.paragraf." },
  { id: "apulejusz-metamorfozy-la", tytul: "Metamorphoses (Złoty osioł)", autor: "Apulejusz", jezyk: "la", zrodlo: P("canonical-latinLit/data/phi1212/phi002/phi1212.phi002.perseus-lat1"), licencja: PERSEUS, przeklady: ["apulejusz-zloty-osiol"], uwagi: "Numeracja księga.rozdział." },
  { id: "augustyn-panstwo-boze-la", tytul: "De civitate Dei (Państwo Boże)", autor: "św. Augustyn", jezyk: "la", zrodlo: { typ: "wikisource", jezyk: "la", strony: ["De civitate Dei"], seria: true }, licencja: WSO("la"), przeklady: ["augustyn-panstwo-boze-2"], wydanie: "tekst za The Latin Library (wydanie nieokreślone w źródle)", uwagi: "Całe dzieło (22 księgi); o olbrzymach księga XV, rozdz. 23." },
  { id: "ksiega-rodzaju-he", tytul: "בְּרֵאשִׁית (Księga Rodzaju)", autor: "Biblia hebrajska", jezyk: "he", zrodlo: { typ: "wlc", ksiega: "Gen" }, licencja: "Westminster Leningrad Codex – domena publiczna. Plik XML z projektu Open Scriptures Hebrew Bible (github.com/openscriptures/morphhb).", przeklady: ["ksiega-rodzaju"], wydanie: "Westminster Leningrad Codex (Kodeks Leningradzki, 1008 r.)", uwagi: "Z samogłoskami i znakami kantylacji. Numeracja rozdział:werset, np. [6:4] (Nefilim)." },
  { id: "nostradamus-proroctwa-fr", tytul: "Les Prophéties (Proroctwa)", autor: "Nostradamus", jezyk: "fr", zrodlo: { typ: "wikisource", jezyk: "fr", strony: ["Les oracles de Michel de Nostredame/Tome 2/Partie 2/Section I/Épître à Cesar de Nostredame mon fils", ...["I", "II", "III", "IV", "V", "VI", "VII"].map((c) => `Les oracles de Michel de Nostredame/Tome 2/Partie 2/Section I/Centurie ${c}`), "Les oracles de Michel de Nostredame/Tome 2/Partie 2/Section II/Épître à Henry Roy de France Second", ...["VIII", "IX", "X"].map((c) => `Les oracles de Michel de Nostredame/Tome 2/Partie 2/Section II/Centurie ${c}`), ...["Presages", "Sixains"].map((c) => `Les oracles de Michel de Nostredame/Tome 2/Partie 2/Section III/${c}`)] }, licencja: WSO("fr"), przeklady: ["nostradamus-proroctwa"], wydanie: "A. Le Pelletier, Les oracles de Michel de Nostredame, t. 2 (Paryż 1867): tekst wydań Pierre'a Rigauda (Lyon 1558/1566) z wariantami", uwagi: "Oryginalny francuski XVI w. – listy, centurie I–X, presages, sixains." },
  { id: "calmet-zjawy-fr", tytul: "Traité sur les apparitions des esprits et sur les vampires", autor: "Augustin Calmet", jezyk: "fr", zrodlo: { typ: "wikisource", jezyk: "fr", strony: ["Traité sur les apparitions des esprits/I/Texte entier", "Traité sur les apparitions des esprits/II/Texte entier"] }, licencja: WSO("fr"), przeklady: ["calmet-zjawy"], wydanie: "Paryż 1751, 2 tomy", uwagi: "Oryginał francuski z 1751 r. (pisownia z „ſ”)." },
  { id: "ramajana-sa", tytul: "वाल्मीकिरामायणम् (Ramajana)", autor: "Walmiki", jezyk: "sa", zrodlo: { typ: "sa-ramajana" }, licencja: WSO("sa"), przeklady: ["ramajana"], uwagi: "Siedem ksiąg (kanda), podział na pieśni (sarga). Pisane dewanagari." },
  { id: "mahabharata-sa", tytul: "महाभारतम् (Mahabharata)", autor: "Wjasa", jezyk: "sa", zrodlo: { typ: "sa-mahabharata" }, licencja: WSO("sa"), przeklady: ["mahabharata-1", "mahabharata-2", "mahabharata-3", "mahabharata-4"], uwagi: "Całość: 18 ksiąg (parwa), podział na rozdziały (adhjaja). Pisane dewanagari. Bitwy i broń bogów m.in. w Drona- i Mausala-parwie." },
];
for (const o of ORYGINALY) {
  const cytowane = [...new Set(o.przeklady!.flatMap((id) => POZYCJE.find((p) => p.id === id)?.cytowane_w ?? []))];
  POZYCJE.push({ ...o, rodzaj_tekstu: "oryginał", cytowane_w: cytowane });
}

const UA = { "User-Agent": "uleszka-archiwum/1.2 (archiwum dokumentacyjne; https://github.com/jokerwader/uleszka-archiwum)" };

async function pobierz(url: string, formularz?: Record<string, string>): Promise<string> {
  for (let proba = 1; proba <= 3; proba++) {
    const r = await fetch(url, formularz ? { method: "POST", headers: UA, body: new URLSearchParams(formularz) } : { headers: UA });
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

// ---------------- teksty w językach oryginału ----------------

/** Strona Wikiźródeł w dowolnym języku (HTML → tekst). */
async function wikiStronaJ(jezyk: string, tytul: string): Promise<string> {
  const url = `https://${jezyk}.wikisource.org/w/api.php?action=parse&format=json&formatversion=2&prop=text&page=${encodeURIComponent(tytul)}&redirects=1`;
  const j = JSON.parse(await pobierz(url));
  if (!j.parse) throw new Error(`Brak strony ${jezyk}:${tytul}`);
  const $ = cheerio.load(j.parse.text);
  $(".mw-editsection, .reference, .references, style, script, table.toccolours, .noprint, .ws-noexport, #ws-data, #headertemplate, .ws-header, #footertemplate, .pagenum, .ws-pagenum, link").remove();
  $("br").replaceWith("\n");
  $("p, div, h1, h2, h3, h4, li, dd, tr").each((_, el) => {
    $(el).append("\n\n");
  });
  return $.root().text().replace(/ /g, " ").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Wszystkie podstrony danej strony Wikiźródeł („Tytuł/…”), z obsługą kontynuacji. */
async function wikiPodstrony(jezyk: string, prefiks: string): Promise<string[]> {
  const out: string[] = [];
  let dalej = "";
  do {
    const j = JSON.parse(await pobierz(`https://${jezyk}.wikisource.org/w/api.php?action=query&list=allpages&apnamespace=0&aplimit=500&format=json&apprefix=${encodeURIComponent(prefiks)}${dalej}`));
    out.push(...j.query.allpages.map((p: { title: string }) => p.title));
    dalej = j.continue ? `&apcontinue=${encodeURIComponent(j.continue.apcontinue)}` : "";
  } while (dalej);
  return out;
}

/** Surowy wikitekst wielu stron naraz (po 50 w jednym zapytaniu). */
async function wikiZrodla(jezyk: string, tytuly: string[]): Promise<Map<string, string>> {
  const wynik = new Map<string, string>();
  for (let i = 0; i < tytuly.length; i += 50) {
    const paczka = tytuly.slice(i, i + 50);
    // POST – lista 50 tytułów w dewanagari nie mieści się w adresie URL
    const j = JSON.parse(await pobierz(`https://${jezyk}.wikisource.org/w/api.php`, { action: "query", prop: "revisions", rvprop: "content", rvslots: "main", redirects: "1", format: "json", formatversion: "2", titles: paczka.join("|") }));
    // przekierowania (np. rozdział 1.1 Mahabharaty) – treść strony docelowej pod tytułem z listy
    const alias = new Map<string, string>((j.query.redirects ?? []).map((r: { from: string; to: string }) => [r.to, r.from]));
    for (const s of j.query.pages) if (s.revisions) wynik.set(alias.get(s.title) ?? s.title, s.revisions[0].slots.main.content);
    process.stdout.write(`  ${Math.min(i + 50, tytuly.length)}/${tytuly.length}\r`);
    await new Promise((ok) => setTimeout(ok, 500));
  }
  return wynik;
}

/** Wikitekst sanskryckich stron → czysty tekst wersów. */
function czyscWikitekst(w: string): string {
  let t = w;
  for (let i = 0; i < 10 && /\{\{[^{}]*\}\}/.test(t); i++) t = t.replace(/\{\{[^{}]*\}\}/g, ""); // szablony (zagnieżdżone)
  t = t
    .replace(/<ref[^>]*\/>|<ref[^>]*>[\s\S]*?<\/ref>/gi, "")
    .replace(/\[\[(?:File|Image|Category|चित्रम्|वर्गः):[^\]]*\]\]/gi, "")
    .replace(/<td>([\s\S]*?)<td>[\s\S]*?(?=<\/tr>|<tr>|$)/gi, "$1") // Mahabharata: druga kolumna to numeracja innego wydania
    .replace(/\[\[[^\]|]*\|([^\]]*)\]\]/g, "$1")
    .replace(/\[\[([^\]]*)\]\]/g, "$1")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/'''|''/g, "")
    .replace(/__[A-Z]+__/g, "")
    .replace(/&nbsp;/g, " ");
  return t
    .split("\n")
    .map((l) => l.replace(/[ \t]+/g, " ").trim())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const CYFRY_DEWANAGARI = "०१२३४५६७८९";
const zDewanagari = (s: string) => Number([...s].map((c) => (CYFRY_DEWANAGARI.includes(c) ? CYFRY_DEWANAGARI.indexOf(c) : c)).join(""));

async function ramajana(): Promise<string> {
  const KANDY = ["बालकाण्डम्", "अयोध्याकाण्डम्", "अरण्यकाण्डम्", "किष्किन्धाकाण्डम्", "सुन्दरकाण्डम्", "युद्धकाण्डम्", "उत्तरकाण्डम्"];
  const wszystkie = await wikiPodstrony("sa", "रामायणम्/");
  const czesci: string[] = [];
  for (const [i, k] of KANDY.entries()) {
    const sargi = wszystkie
      .map((t) => ({ t, m: t.match(new RegExp(`^रामायणम्/${k}/सर्गः ([०-९]+)$`)) }))
      .filter((x) => x.m)
      .map((x) => ({ t: x.t, n: zDewanagari(x.m![1]) }))
      .sort((a, b) => a.n - b.n);
    const zrodla = await wikiZrodla("sa", sargi.map((s) => s.t));
    czesci.push(`## ${i + 1}. ${k}`);
    for (const s of sargi) czesci.push(`### [${i + 1}.${s.n}] ${k} – सर्गः ${s.n}\n\n${czyscWikitekst(zrodla.get(s.t) ?? "")}`);
    console.log(`  ${k}: ${sargi.length} sarg`);
  }
  return czesci.join("\n\n");
}

async function mahabharata(): Promise<string> {
  const strony = (await wikiPodstrony("sa", "महाभारतम्-"))
    .map((t) => ({ t, m: t.match(/^महाभारतम्-(\d\d)-([^-]+)-(\d+)$/) }))
    .filter((x) => x.m)
    .map((x) => ({ t: x.t, parwa: Number(x.m![1]), nazwa: x.m![2], n: Number(x.m![3]) }))
    .sort((a, b) => a.parwa - b.parwa || a.n - b.n);
  const zrodla = await wikiZrodla("sa", strony.map((s) => s.t));
  const czesci: string[] = [];
  let parwa = 0;
  for (const s of strony) {
    if (s.parwa !== parwa) {
      parwa = s.parwa;
      czesci.push(`## ${s.parwa}. ${s.nazwa}`);
    }
    czesci.push(`### [${s.parwa}.${s.n}] ${s.nazwa} – अध्यायः ${s.n}\n\n${czyscWikitekst(zrodla.get(s.t) ?? "")}`);
  }
  console.log(`  ${strony.length} rozdziałów (adhjaja)`);
  return czesci.join("\n\n");
}

/** Księga Biblii hebrajskiej z pliku OSIS Kodeksu Leningradzkiego. */
async function wlc(ksiega: string): Promise<string> {
  const $ = cheerio.load(await pobierz(`https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/${ksiega}.xml`), { xml: true });
  $("note").remove();
  const czesci: string[] = [];
  $("chapter").each((_, ch) => {
    const r = $(ch).attr("osisID")!.split(".")[1];
    czesci.push(`## פרק ${r} (rozdział ${r})`);
    const wersy: string[] = [];
    $(ch)
      .find("verse")
      .each((_, v) => {
        const w = $(v).attr("osisID")!.split(".")[2];
        const t = $(v).text().replace(/\//g, "").replace(/\s+/g, " ").replace(/־ /g, "־").trim();
        wersy.push(`[${r}:${w}] ${t}`);
      });
    czesci.push(wersy.join("\n"));
  });
  return czesci.join("\n\n");
}

/**
 * Tekst TEI z Perseus Digital Library → czytelny tekst z numeracją cytowań w nawiasach kwadratowych:
 * [księga.rozdział.paragraf] dla prozy, [księga.wers] dla poezji, [24e] (Stephanus) dla Platona.
 */
async function perseus(plik: string): Promise<{ tekst: string; wydanie: string }> {
  const [repo, ...reszta] = plik.split("/");
  const xml = await pobierz(`https://raw.githubusercontent.com/PerseusDL/${repo}/master/${reszta.join("/")}.xml`);
  const $ = cheerio.load(xml, { xml: true });
  // wydanie źródłowe z nagłówka TEI
  const zr = $("sourceDesc").first();
  const wydanie = [zr.find("editor").first().text(), zr.find("title").first().text(), zr.find("pubPlace").first().text(), zr.find("publisher").first().text(), zr.find("date").first().text()]
    .map((s) => s.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join(", ");
  $("teiHeader, note, bibl, sic, orig, pb, figure").remove();

  type Wezel = { type: string; name?: string; data?: string; attribs?: Record<string, string>; children?: Wezel[] };
  const out: string[] = [];
  const sciezka: string[] = []; // numery z zagnieżdżonych <div type="textpart">
  const jestDivem = (w: Wezel) => w.type === "tag" && w.name === "div" && w.attribs?.type === "textpart";
  const maMilestoneSekcji = (w: Wezel): boolean => (w.children ?? []).some((c) => (c.name === "milestone" && c.attribs?.unit === "section") || maMilestoneSekcji(c));
  const ksiega = () => sciezka[0];

  const idz = (w: Wezel, wSekcjiDiv: boolean) => {
    if (w.type === "text") {
      out.push((w.data ?? "").replace(/\s+/g, " "));
      return;
    }
    if (w.type !== "tag") return;
    const a = w.attribs ?? {};
    const dzieci = () => (w.children ?? []).forEach((c) => idz(c, wSekcjiDiv));
    switch (w.name) {
      case "div": {
        if (a.type !== "textpart") return dzieci();
        sciezka.push(a.n ?? "?");
        const lisc = !(w.children ?? []).some((c) => jestDivem(c) || (c.children ?? []).some(jestDivem));
        const sub = (a.subtype ?? "").toLowerCase();
        if (!lisc && sciezka.length === 1) out.push(`\n\n## ${sub === "book" ? "Księga" : sub} ${a.n}\n\n`);
        else if (lisc && maMilestoneSekcji(w)) out.push(`\n\n### (${sciezka.join(".")})\n\n`);
        else if (lisc && !(w.children ?? []).some((c) => c.name === "l" || c.name === "lg")) out.push(`\n\n[${sciezka.join(".")}] `);
        else if (lisc && sciezka.length === 1) out.push(`\n\n## ${sub === "book" ? "Księga" : sub} ${a.n}\n\n`);
        (w.children ?? []).forEach((c) => idz(c, wSekcjiDiv || sub === "section"));
        sciezka.pop();
        return;
      }
      case "milestone":
        if (a.unit === "section") out.push(` [${ksiega() && !/[a-e]$/.test(a.n ?? "") ? `${ksiega()}.` : ""}${a.n}] `);
        return;
      case "l":
        out.push(`\n[${[...sciezka, a.n ?? ""].join(".")}] `);
        dzieci();
        return;
      case "lg":
      case "p":
      case "sp":
        out.push("\n\n");
        dzieci();
        out.push("\n\n");
        return;
      case "head":
        out.push("\n\n### ");
        dzieci();
        out.push("\n\n");
        return;
      case "label":
      case "speaker":
        dzieci();
        out.push(" ");
        return;
      case "del":
        out.push("⟦");
        dzieci();
        out.push("⟧");
        return;
      case "add":
        out.push("⟨");
        dzieci();
        out.push("⟩");
        return;
      case "gap":
        out.push(" … ");
        return;
      case "lb":
        out.push(" ");
        return;
      default:
        dzieci();
    }
  };
  const korzen = ($("text body").get(0) ?? $("text").get(0)) as unknown as Wezel;
  idz(korzen, false);
  const tekst = out
    .join("")
    .replace(/[ \t]+/g, " ")
    .replace(/ *\n */g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .replace(/^(\[[^\]\s]+\])\n+(?=\S)/gm, "$1 "); // numer akapitu w tej samej linii co tekst
  return { tekst, wydanie };
}

async function tekst(p: Pozycja): Promise<{ tekst: string; wydanie?: string }> {
  const z = p.zrodlo;
  if (z.typ === "gutenberg") return { tekst: (await pobierz(`https://www.gutenberg.org/cache/epub/${z.numer}/pg${z.numer}.txt`)).replace(/\r\n/g, "\n").replace(/^﻿/, "") };
  if (z.typ === "wolnelektury") return { tekst: (await pobierz(`https://wolnelektury.pl/media/book/txt/${z.slug}.txt`)).replace(/\r\n/g, "\n") };
  if (z.typ === "perseus") return perseus(z.plik);
  if (z.typ === "wlc") return { tekst: await wlc(z.ksiega) };
  if (z.typ === "sa-ramajana") return { tekst: await ramajana() };
  if (z.typ === "sa-mahabharata") return { tekst: await mahabharata() };
  if (z.typ === "wikisource") {
    const czesci: string[] = [];
    for (const s of z.strony) {
      if (!z.seria) {
        const czlony = s.split("/");
        const nazwa = czlony.at(-1) === "Texte entier" ? `Tome ${czlony.at(-2)}` : czlony.at(-1)!;
        let t = await wikiStronaJ(z.jezyk, s);
        const centuria = nazwa.match(/^Centurie ([IVXLC]+)$/);
        if (centuria) {
          // czterowiersze: zwarte wersy i numeracja [centuria.czterowiersz], np. [2.51]
          const c = zRzymskiej(centuria[1]);
          t = t.replace(/\n{2,}/g, "\n").replace(/^\s*([IVXLC]+)\.\s*$/gm, (_m, r: string) => `\n[${c}.${zRzymskiej(r)}]`);
        } else if (z.jezyk === "fr") t = t.replace(/([^\n])\n(?=[^\n])/g, "$1 "); // wiersze druku łączone w akapity
        czesci.push(`## ${nazwa}\n\n${t}`);
        continue;
      }
      // seria: strona główna to spis; bierzemy podstrony w kolejności (Prologus, Liber I, II, …)
      const pod = (await wikiPodstrony(z.jezyk, s + "/")).filter((t) => t.split("/").length === 2);
      const numer = (t: string) => {
        const k = t.split("/")[1].replace(/^(Liber|Livre|Księga)\s+/i, "");
        return /^[IVXLC]+$/.test(k) ? zRzymskiej(k) : /^(Prologus|Praefatio|Préface)/i.test(k) ? 0 : 10000;
      };
      pod.sort((a, b) => numer(a) - numer(b));
      for (const t of pod) {
        const nazwa = t.split("/")[1];
        let tresc = await wikiStronaJ(z.jezyk, t);
        const liber = nazwa.match(/^Liber ([IVXLC]+)$/);
        // rozdziały [XXIII] → [15.23] (księga.rozdział), jak w cytowaniach naukowych
        if (liber) tresc = tresc.replace(/^\[([IVXLC]+)\]/gm, (_m, r: string) => `[${zRzymskiej(liber[1])}.${zRzymskiej(r)}]`);
        czesci.push(`## ${nazwa}\n\n${tresc}`);
        await new Promise((ok) => setTimeout(ok, 300));
      }
    }
    return { tekst: czesci.join("\n\n") };
  }
  const czesci: string[] = [];
  for (const s of z.strony) czesci.push(s.endsWith("/całość") ? await wikiStrona(s) : await wikiSeria(s));
  return { tekst: czesci.join("\n\n") };
}

export function adresZrodla(z: Zrodlo): string {
  if (z.typ === "gutenberg") return `https://www.gutenberg.org/ebooks/${z.numer}`;
  if (z.typ === "wolnelektury") return `https://wolnelektury.pl/katalog/lektura/${z.slug}/`;
  if (z.typ === "perseus") {
    const [repo, ...reszta] = z.plik.split("/");
    return `https://github.com/PerseusDL/${repo}/blob/master/${reszta.join("/")}.xml`;
  }
  if (z.typ === "wlc") return `https://github.com/openscriptures/morphhb/blob/master/wlc/${z.ksiega}.xml`;
  if (z.typ === "sa-ramajana") return "https://sa.wikisource.org/wiki/वाल्मीकिरामायणम्";
  if (z.typ === "sa-mahabharata") return "https://sa.wikisource.org/wiki/महाभारतम्";
  if (z.typ === "wikisource") return `https://${z.jezyk}.wikisource.org/wiki/${encodeURIComponent(z.strony[0].split("/")[0]).replace(/%2F/g, "/")}`;
  return `https://pl.wikisource.org/wiki/${encodeURIComponent(z.strony[0].replace(/\/całość$/, "")).replace(/%2F/g, "/")}`;
}

async function main() {
  const odNowa = process.argv.includes("--od-nowa");
  const tylko = process.argv.find((a) => a.startsWith("--tylko="))?.slice(8).split(",");
  mkdirSync("biblioteka", { recursive: true });
  for (const p of POZYCJE) {
    const plik = `biblioteka/${p.id}.md`;
    if (tylko && !tylko.includes(p.id)) continue;
    if (existsSync(plik) && !odNowa && !tylko) {
      console.log(`= ${p.id} (już jest)`);
      continue;
    }
    console.log(`… ${p.id}`);
    const { tekst: t, wydanie } = await tekst(p);
    const fm = [
      "---",
      `id: ${JSON.stringify(p.id)}`,
      `tytul: ${JSON.stringify(p.tytul)}`,
      `autor: ${JSON.stringify(p.autor)}`,
      p.tlumacz ? `tlumacz: ${JSON.stringify(p.tlumacz)}` : null,
      `jezyk: ${p.jezyk}`,
      p.rodzaj_tekstu ? `rodzaj_tekstu: ${JSON.stringify(p.rodzaj_tekstu)}` : null,
      p.wydanie || wydanie ? `wydanie: ${JSON.stringify(p.wydanie ?? wydanie)}` : null,
      p.przeklady ? `przeklady: ${JSON.stringify(p.przeklady)}` : null,
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
    "## Przekłady",
    "",
    "| Dzieło | Autor | Przekład | Język | Wielkość | Źródło |",
    "|---|---|---|---|---|---|",
  ];
  const rozmiar = (id: string) => (existsSync(`biblioteka/${id}.md`) ? Math.round(readFileSync(`biblioteka/${id}.md`, "utf8").length / 1000) : 0);
  for (const p of POZYCJE.filter((x) => !x.rodzaj_tekstu)) {
    linie.push(`| [${p.tytul}](${p.id}.md) | ${p.autor} | ${p.tlumacz ?? "—"} | ${JEZYKI[p.jezyk]} | ${rozmiar(p.id)} tys. znaków | [${p.zrodlo.typ}](${adresZrodla(p.zrodlo)}) |`);
  }
  linie.push(
    "",
    "## Teksty w językach oryginału",
    "",
    "Oryginalne brzmienie dzieł, których przekłady są wyżej – do sprawdzania, co naprawdę mówi źródło (asystent AI może je przetłumaczyć i porównać z przekładem).",
    "Fragmenty są oznaczone standardową numeracją w nawiasach kwadratowych, np. Platon [24e], Herodot [2.148.1], Iliada [1.37], Księga Rodzaju [6:4] – tak samo cytuje je literatura naukowa.",
    "",
    "| Dzieło | Autor | Język | Przekład w bibliotece | Wielkość | Źródło |",
    "|---|---|---|---|---|---|",
  );
  for (const p of POZYCJE.filter((x) => x.rodzaj_tekstu)) {
    linie.push(`| [${p.tytul}](${p.id}.md) | ${p.autor} | ${JEZYKI[p.jezyk]} | ${(p.przeklady ?? []).map((id) => `[${id}](${id}.md)`).join(", ")} | ${rozmiar(p.id)} tys. znaków | [${p.zrodlo.typ}](${adresZrodla(p.zrodlo)}) |`);
  }
  linie.push(
    "",
    "Brak oryginałów w formie tekstowej na wolnej licencji: Księga Henocha (gyyz), Epos o Gilgameszu i Kodeks Hammurabiego (akadyjski, pismo klinowe), Księga Umarłych (egipski, hieroglify), Popol Vuh (kicze), Księgi Chilam Balam (maja jukatański); jedyny dostępny hiszpański przekład Popol Vuh (Asturias, 1927) jest w UE chroniony prawem autorskim.",
    "",
    "Licencje: teksty w domenie publicznej. Pliki z Project Gutenberg zawierają oryginalną licencję PG; wydania Wolnych Lektur, transkrypcje Wikiźródeł i opracowania Perseus Digital Library – licencje CC BY-SA (podane w nagłówku każdego pliku).",
    "",
  );
  writeFileSync("biblioteka/README.md", linie.join("\n"), "utf8");
}

if (process.argv[1]?.endsWith("biblioteka.ts")) await main();
