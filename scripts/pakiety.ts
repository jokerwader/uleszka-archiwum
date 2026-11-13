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

// opracowania AI wszystkich artykułów w jednym pliku – szybki przegląd całego archiwum
const opr: string[] = [
  "# Archiwum uleszka.net – opracowania artykułów",
  "",
  "Streszczenia, główne tezy autora (z dosłownymi cytatami), tematy, osoby, miejsca i daty dla każdego artykułu.",
  "UWAGA: opracowania przygotowała AI (Claude); nie są częścią oryginalnej strony. Każdy cytat sprawdzono automatycznie – występuje w artykule dosłownie.",
  "",
];
for (const a of archiwum.artykuly) {
  const o = archiwum.opracowania.get(a.id);
  if (!o || (!o.tezy.length && o.streszczenie.length < 140)) continue;
  opr.push(`## OPRACOWANIE: ${a.tytul}`, `id: ${a.id} | dział: ${a.dzial}`, "", `Streszczenie: ${o.streszczenie}`);
  if (o.tezy.length) opr.push("", "Tezy:", ...o.tezy.map((t, i) => `${i + 1}. ${t.teza} (${t.dziedzina}) – cytat: „${t.cytat}”`));
  if (o.tematy.length) opr.push("", `Tematy: ${o.tematy.join(", ")}`);
  if (o.osoby.length) opr.push(`Osoby: ${o.osoby.join(", ")}`);
  if (o.miejsca.length) opr.push(`Miejsca: ${o.miejsca.join(", ")}`);
  if (o.okresy.length) opr.push(`Daty: ${o.okresy.map((x) => `${x.kiedy} – ${x.co}`).join("; ")}`);
  if (o.zrodla_cytowane.length) opr.push(`Źródła cytowane: ${o.zrodla_cytowane.join("; ")}`);
  opr.push("", "---", "");
}
writeFileSync(`${WYJSCIE}/06-opracowania.md`, opr.join("\n"), "utf8");
console.log(`${WYJSCIE}/06-opracowania.md: ${Math.round(opr.join("\n").length / 1000)} tys. znaków`);

for (const p of pliki) console.log(`${p.plik}: ${p.n} stron, ${Math.round(p.znaki / 1000)} tys. znaków`);

// ---- biblioteka: dawne źródła cytowane przez autora (domena publiczna), pogrupowane tematycznie ----
// Limit ok. 4,5 mln znaków na plik: ChatGPT przyjmuje do 2 mln tokenów na plik i do 20 plików na GPT.
const GRUPY: { nazwa: string; opis: string; ids: string[] }[] = [
  { nazwa: "polskie-przeklady", opis: "dzieła w polskich przekładach", ids: ["platon-timajos", "platon-kritias", "ksiega-rodzaju", "herodot-dzieje", "owidiusz-przemiany", "homer-iliada"] },
  { nazwa: "bliski-wschod-egipt", opis: "Mezopotamia, Egipt, apokryfy i tradycja żydowska", ids: ["ksiega-henocha", "gilgamesz", "kodeks-hammurabiego", "ksiega-umarlych", "apokryfy-nt", "talmud-midrasz-kabala"] },
  { nazwa: "ameryki", opis: "Majowie i Ameryka przedkolumbijska", ids: ["popol-vuh", "chilam-balam", "le-plongeon-sacred-mysteries"] },
  { nazwa: "antyk", opis: "autorzy greccy i rzymscy", ids: ["strabon-geografia-3", "pliniusz-historia-naturalna-6", "apulejusz-zloty-osiol", "argonautyka", "cezar-wojna-galijska", "augustyn-panstwo-boze-2"] },
  { nazwa: "nowozytne", opis: "Calmet, Nostradamus, Charles Fort", ids: ["calmet-zjawy", "nostradamus-proroctwa", "fort-book-of-the-damned", "fort-new-lands"] },
  { nazwa: "indie", opis: "Ramajana i Mahabharata", ids: ["ramajana", "mahabharata-1", "mahabharata-2", "mahabharata-3", "mahabharata-4"] },
];
const LIMIT = 4_500_000;
const wGrupach = new Set(GRUPY.flatMap((g) => g.ids));
const pozostale = archiwum.ksiazki.filter((k) => !wGrupach.has(k.id)).map((k) => k.id);
if (pozostale.length) GRUPY.push({ nazwa: "inne", opis: "pozostałe dzieła", ids: pozostale });

const naglowekKsiazki = (k: (typeof archiwum.ksiazki)[number]) => {
  const m = k.meta as Record<string, string | string[] | undefined>;
  const cyt = (m.cytowane_w as string[] | undefined) ?? [];
  return [
    `## KSIĄŻKA: ${k.tytul}`,
    [`id: ${k.id}`, m.autor && `autor: ${m.autor}`, m.tlumacz && `przekład: ${m.tlumacz}`, m.jezyk && `język: ${m.jezyk}`].filter(Boolean).join(" | "),
    `źródło: ${m.zrodlo} | licencja: ${m.licencja}`,
    cyt.length ? `cytowana w artykułach uleszka.net: ${cyt.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n");
};

let nr = 7;
for (const g of GRUPY) {
  const ksiazki = g.ids.map((id) => archiwum.ksiazki.find((k) => k.id === id)).filter((k) => k !== undefined);
  // dzielimy na pliki po kolei, nie przekraczając limitu (bardzo długie tomy idą do osobnych plików)
  const paczki: (typeof ksiazki)[] = [];
  let biezaca: typeof ksiazki = [];
  let rozmiar = 0;
  for (const k of ksiazki) {
    if (biezaca.length && rozmiar + k.tresc.length > LIMIT) {
      paczki.push(biezaca);
      biezaca = [];
      rozmiar = 0;
    }
    biezaca.push(k);
    rozmiar += k.tresc.length;
  }
  if (biezaca.length) paczki.push(biezaca);

  paczki.forEach((p, i) => {
    const plik = `${WYJSCIE}/${String(nr++).padStart(2, "0")}-biblioteka-${g.nazwa}${paczki.length > 1 ? `-${i + 1}` : ""}.md`;
    const tekst = [
      `# Biblioteka archiwum uleszka.net – ${g.opis}${paczki.length > 1 ? ` (część ${i + 1} z ${paczki.length})` : ""}`,
      "",
      "Pełne teksty dawnych dzieł, na które powołuje się autor uleszka.net. Wszystkie są w domenie publicznej; tekst jest taki, jak w podanym źródle.",
      "To NIE są teksty autora strony – służą do sprawdzania, co naprawdę mówi źródło. Każda książka zaczyna się od nagłówka „## KSIĄŻKA:”.",
      "",
      p.map((k) => `${naglowekKsiazki(k)}\n\n${k.tresc.trim()}`).join("\n\n---\n\n"),
      "",
    ].join("\n");
    writeFileSync(plik, tekst, "utf8");
    console.log(`${plik}: ${p.length} ksiąg, ${Math.round(tekst.length / 1000)} tys. znaków`);
  });
}
