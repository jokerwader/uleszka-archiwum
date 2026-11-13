/**
 * Konwerter: zamienia oryginalne strony HTML z folderu `zrodlo/` na pliki Markdown
 * w folderze `artykuly/` oraz generuje spis treści `KATALOG.md`.
 *
 * Zasada: tekst artykułów przenosimy bez zmian. Zmienia się tylko zapis
 * (HTML -> Markdown) i kodowanie znaków (ISO-8859-2 -> UTF-8).
 *
 * Uruchomienie: npm run konwertuj
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join, posix } from "node:path";
import * as cheerio from "cheerio";
import type { Element } from "domhandler";
import TurndownService from "turndown";
import { dekoduj } from "./dekoduj.js";

const ZRODLO = "zrodlo";
const WYJSCIE = "artykuly";
const ADRES = "http://www.uleszka.net/";

// ---------- struktura serwisu (z menu strony) ----------
type Dzial = { id: string; nazwa: string; opis: string; menu?: string; strony?: { p: string; t: string }[] };
const DZIALY: Dzial[] = [
  {
    id: "00-strona-glowna",
    nazwa: "Strona główna",
    opis: "Strona tytułowa i menu główne serwisu.",
    strony: [
      { p: "webacja/doindeksu/tytx1.htm", t: "Strona tytułowa" },
      { p: "webacja/doindeksu/spis1b.htm", t: "Menu główne" },
    ],
  },
  { id: "01-cywilizacja-bogow", nazwa: "Cywilizacja Bogów", opis: "Dawne cywilizacje, budowle, mity i katastrofy.", menu: "webacja/cybog/spis1a.htm" },
  { id: "02-zapomniana-medycyna", nazwa: "Zapomniana medycyna", opis: "Medycyna naturalna, zdrowie i żywność.", menu: "webacja/medalt/spis1.htm" },
  { id: "03-roznosci", nazwa: "Różności", opis: "Teksty prywatne, publicystyka i fotografie.", menu: "webacja/inne/spis1c.htm" },
  { id: "04-pamietam", nazwa: "Pamiętam", opis: "Strona wspomnieniowa.", strony: [{ p: "webacja/papa.htm", t: "Pamiętam" }] },
];
/** Strony techniczne (ramki, menu, paski tytułowe) – nie są artykułami. */
/** Strony z ramkami (wejścia do działów) – linki do nich prowadzą do odpowiedniego miejsca w KATALOG.md. */
const RAMKI: Record<string, string> = {
  "index.html": "",
  "webacja/doindeksu/index.htm": "",
  "webacja/cybog/cybog.htm": "#cywilizacja-bogów",
  "webacja/medalt/medalt.htm": "#zapomniana-medycyna",
  "webacja/inne/inne.htm": "#różności",
};
const NAWIGACJA = new Set([
  "index.html",
  "webacja/doindeksu/index.htm",
  "webacja/cybog/cybog.htm",
  "webacja/cybog/linki.htm",
  "webacja/cybog/odstep.htm",
  "webacja/cybog/spis1a.htm",
  "webacja/cybog/tytcb.htm",
  "webacja/inne/inne.htm",
  "webacja/inne/odstepi.htm",
  "webacja/inne/spis1c.htm",
  "webacja/medalt/medalt.htm",
  "webacja/medalt/linki.htm",
  "webacja/medalt/spis1.htm",
  "webacja/medalt/tytul.htm",
]);

// ---------- pomocnicze ----------
function walk(d: string): string[] {
  return readdirSync(d).flatMap((n) => {
    const p = join(d, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}
const wszystkieStrony = walk(ZRODLO)
  .map((p) => p.slice(ZRODLO.length + 1).replace(/\\/g, "/"))
  .filter((p) => /\.html?$/i.test(p))
  .sort();

const cache = new Map<string, cheerio.CheerioAPI>();
function wczytaj(p: string) {
  if (!cache.has(p)) cache.set(p, cheerio.load(dekoduj(readFileSync(join(ZRODLO, p)))));
  return cache.get(p)!;
}
/** Rozwiązuje względny adres z kodu strony na ścieżkę w `zrodlo/` (lub null dla adresów zewnętrznych). */
function rozwiaz(zStrony: string, href: string): string | null {
  const h = href.trim().replace(/\\/g, "/");
  if (!h || /^(https?:|mailto:|javascript:|ftp:|#)/i.test(h)) return null;
  return posix.normalize(posix.join(posix.dirname(zStrony), decodeURI(h.split("#")[0].split("?")[0])));
}
function tekst(s: string) {
  return s.replace(/\s+/g, " ").trim();
}
function slug(s: string) {
  return (
    s
      .toLowerCase()
      .replace(/ł/g, "l")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 50) || "strona"
  );
}
function idStrony(p: string) {
  return p.replace(/^webacja\//, "").replace(/\.html?$/i, "");
}
function linkiStron(p: string): { cel: string; tekst: string }[] {
  const $ = wczytaj(p);
  const wynik: { cel: string; tekst: string }[] = [];
  $("a[href], area[href]").each((_, el) => {
    const cel = rozwiaz(p, $(el).attr("href")!);
    if (cel && /\.html?$/i.test(cel) && existsSync(join(ZRODLO, cel))) wynik.push({ cel, tekst: tekst($(el).text()) });
  });
  return wynik;
}
/** Tytuł podstrony, której nie ma w menu: pierwszy wyróżniony napis na stronie. */
function zgadnijTytul(p: string): string {
  const $ = wczytaj(p);
  for (const sel of ['font[size="6"]', 'font[size="5"]', "font[size=6]", "font[size=5]", "h1", "h2", "b", "strong"]) {
    const el = $(sel).first();
    if (el.length) {
      const t = tekst(el.clone().children("font").remove().end().text()) || tekst(el.text());
      if (t.length > 2) return t.length > 90 ? t.slice(0, 87) + "…" : t;
    }
  }
  return idStrony(p);
}

/** Podstrony bez własnego napisu (galerie zdjęć, obrazki) – tytuł z nazwy folderu i numeru. */
const NAZWY_FOLDEROW: Record<string, string> = {
  bobolice: "Bobolice",
  mirow: "Mirów",
  olsztyn: "Olsztyn",
  ostreznik: "Ostrężnik",
  proboszczowice: "Proboszczowice",
};
function tytulPodstrony(p: string): string {
  const m = p.match(/kolasia\/(\w+)\/[a-z]+(\d+)\.htm$/);
  if (m) return `Fotografie – ${NAZWY_FOLDEROW[m[1]] ?? m[1]} ${m[2]}`;
  const t = zgadnijTytul(p);
  return t === idStrony(p) ? `${t.split("/").pop()} (obraz)` : t;
}

// ---------- układ: przypisanie stron do działów ----------
type Wpis = { p: string; tytul: string; dzial: Dzial; rodzic?: string; poziom: number };
const przypisane = new Map<string, Wpis>();
const kolejnosc: Wpis[] = [];
function dodaj(p: string, tytul: string, dzial: Dzial, rodzic?: string, poziom = 0) {
  if (przypisane.has(p) || NAWIGACJA.has(p) || zarezerwowane.has(p)) return;
  const w: Wpis = { p, tytul, dzial, rodzic, poziom };
  przypisane.set(p, w);
  kolejnosc.push(w);
  // podstrony, do których prowadzą linki z tej strony (najpierw wszystkie bezpośrednie, potem głębiej)
  const dzieci = [...new Set(linkiStron(p).map((l) => l.cel))].filter(
    (c) => !przypisane.has(c) && !NAWIGACJA.has(c) && !menuWszystkie.has(c) && !zarezerwowane.has(c),
  );
  for (const c of dzieci) zarezerwowane.add(c);
  for (const c of dzieci) {
    zarezerwowane.delete(c);
    dodaj(c, tytulPodstrony(c), dzial, p, poziom + 1);
  }
}
const zarezerwowane = new Set<string>();
const menuWszystkie = new Set<string>();
for (const d of DZIALY) {
  if (d.menu) for (const l of linkiStron(d.menu)) if (!NAWIGACJA.has(l.cel)) menuWszystkie.add(l.cel);
  for (const s of d.strony ?? []) menuWszystkie.add(s.p);
}
for (const d of DZIALY) {
  const pozycje = d.menu
    ? linkiStron(d.menu)
        .filter((l) => !NAWIGACJA.has(l.cel))
        .map((l) => ({ p: l.cel, t: l.tekst }))
    : d.strony!;
  for (const s of pozycje) if (!przypisane.has(s.p)) dodaj(s.p, s.t, d);
}
const pozostale: Dzial = { id: "05-pozostale", nazwa: "Pozostałe", opis: "Strony, do których nie prowadzi żadne menu.", strony: [] };
for (const p of wszystkieStrony) if (!przypisane.has(p) && !NAWIGACJA.has(p)) dodaj(p, tytulPodstrony(p), pozostale);
if (kolejnosc.some((w) => w.dzial === pozostale)) DZIALY.push(pozostale);

// ścieżki plików wynikowych
const plikMd = new Map<string, string>();
for (const d of DZIALY) {
  let n = 0;
  for (const w of kolejnosc.filter((w) => w.dzial === d)) {
    n++;
    plikMd.set(w.p, `${WYJSCIE}/${d.id}/${String(n).padStart(3, "0")}-${slug(w.tytul)}.md`);
  }
}

// ---------- konwersja HTML -> Markdown ----------
function wzgledna(zPliku: string, doPliku: string) {
  return encodeURI(posix.relative(posix.dirname(zPliku), doPliku));
}
function konwertuj(w: Wpis): { md: string; obrazy: { src: string; alt: string }[] } {
  const $ = cheerio.load(dekoduj(readFileSync(join(ZRODLO, w.p))));
  const cel = plikMd.get(w.p)!;
  const obrazy: { src: string; alt: string }[] = [];
  $("script, style, noscript, head, map").remove();
  $("img").each((_, el) => {
    const $el = $(el);
    const src = $el.attr("src") ?? "";
    const r = rozwiaz(w.p, src);
    let nowy = src;
    if (r && existsSync(join(ZRODLO, r))) {
      nowy = wzgledna(cel, `${ZRODLO}/${r}`);
      obrazy.push({ src: `${ZRODLO}/${r}`, alt: tekst($el.attr("alt") ?? "") });
    } else if (r?.startsWith("..")) {
      // licznik odwiedzin z zewnętrznego serwisu (poza serwisem uleszka.net) – nie jest treścią
      $el.remove();
      return;
    } else if (r) nowy = ADRES + r;
    $el.attr("src", nowy);
  });
  $("a[href]").each((_, el) => {
    const $el = $(el);
    const href = $el.attr("href")!;
    if (href.startsWith("#")) {
      $el.replaceWith($el.contents());
      return;
    }
    // autor często linkował do własnych tekstów pełnym adresem (http://www.uleszka.net/webacja/…) – traktujemy go
    // jak odnośnik wewnętrzny; dziś domena znów należy do archiwum, więc stare adresy prowadziłyby donikąd
    const wlasny = href.trim().match(/^https?:\/\/(?:www\.)?uleszka\.net\/?(.*)$/i);
    if (wlasny && /(^|\/)www\.[^/]+/i.test(wlasny[1])) {
      // błąd w oryginale: adres zewnętrzny wpisany jako ścieżka strony (…/webacja/medalt/www.iamthewitness.com)
      $el.attr("href", "http://" + wlasny[1].slice(wlasny[1].search(/www\./i)));
      return;
    }
    const r = wlasny ? posix.normalize(decodeURI(wlasny[1].split("#")[0].split("?")[0]) || "index.html") : rozwiaz(w.p, href);
    if (r && plikMd.has(r)) $el.attr("href", wzgledna(cel, plikMd.get(r)!));
    else if (r && r in RAMKI) $el.attr("href", wzgledna(cel, "KATALOG.md") + RAMKI[r]);
    // program kopiujący stronę (HTTrack) zapisał część adresów zewnętrznych jako ścieżki lokalne – przywracamy je
    else if (r?.startsWith("..")) $el.attr("href", "http://" + r.replace(/^(\.\.\/)+/, ""));
    else if (r && existsSync(join(ZRODLO, r))) $el.attr("href", wzgledna(cel, `${ZRODLO}/${r}`));
    // strony, których nie ma w kopii – kopia z 2007 r. w Internet Archive (Wayback Machine)
    else if (r) $el.attr("href", `https://web.archive.org/web/2007/${ADRES}${r}`);
    else if (wlasny) $el.attr("href", `https://web.archive.org/web/2007/${href.trim()}`);
  });
  $("a:not([href])").each((_, el) => {
    $(el).replaceWith($(el).contents());
  });

  const td = new TurndownService({ headingStyle: "atx", hr: "---", bulletListMarker: "-", emDelimiter: "*" });
  td.remove(["script", "style", "title"]);
  // tabele były na tej stronie tylko układem graficznym – zamieniamy je na zwykłe akapity
  td.addRule("tabele", {
    filter: ["table", "tbody", "thead", "tfoot", "tr", "td", "th", "center", "div", "form", "frameset", "frame"],
    replacement: (content) => `\n\n${content}\n\n`,
  });
  // …ale część tabel to prawdziwe zestawienia danych (planety, normy, tabele żywieniowe) albo listy punktowane
  // zbudowane z tabeli („•” w pierwszej kolumnie). Te odtwarzamy jako tabele Markdown lub listy.
  // Reguły dodane później mają w Turndown pierwszeństwo, więc ta wygrywa z regułą „tabele” dla pasujących tabel.
  type Wezel = { nodeName: string; textContent: string | null; innerHTML: string; querySelectorAll(s: string): ArrayLike<Wezel>; childNodes: ArrayLike<Wezel> };
  const tekstKomorki = (k: Wezel) => (k.textContent ?? "").replace(/\s+/g, " ").trim();
  const wierszeTabeli = (t: Wezel) =>
    Array.from(t.querySelectorAll("tr")).map((w) => Array.from(w.childNodes).filter((k) => k.nodeName === "TD" || k.nodeName === "TH"));
  const tylkoObraz = (k: Wezel) => k.querySelectorAll("img").length > 0 && !tekstKomorki(k);
  const tekstowa = (k: Wezel) => !!tekstKomorki(k) && !k.querySelectorAll("img").length;
  const pustaKomorka = (k: Wezel) => !tekstKomorki(k) && !k.querySelectorAll("img").length;
  const czyTabelaDanych = (t: Wezel) => {
    if (t.querySelectorAll("table").length) return false;
    const wiersze = wierszeTabeli(t);
    if (wiersze.length < 2 || Math.max(...wiersze.map((w) => w.length)) < 2) return false;
    // tabela z obrazkami jest zestawieniem tylko wtedy, gdy ma kilka wierszy z tekstem w kilku kolumnach
    // (np. kalendarz Henocha: miesiące, dni, rysunki, proporcje) – inaczej to galeria albo układ strony
    if (t.querySelectorAll("img").length && wiersze.filter((r) => r.filter(tekstowa).length >= 2).length < 2) return false;
    return wiersze.every((w) => w.every((k) => tekstKomorki(k).length <= 2000));
  };
  // galerie: wiersz zdjęć, a pod nim (albo nad nim) wiersz podpisów – odtwarzamy pary „zdjęcie + jego podpis”.
  // Uwzględniamy scalone komórki (colspan: jeden podpis pod dwoma zdjęciami), puste kolumny-odstępy i puste wiersze.
  // Zdjęcia nie mają liter, więc kolejność tekstu (i kontrola wierności) się nie zmienia.
  type Pole = { k: Wezel; od: number; do: number };
  const siatka = (t: Wezel): Pole[][] =>
    wierszeTabeli(t)
      .map((r) => {
        let c = 0;
        return r.map((k) => {
          const n = Math.max(1, Number((k as unknown as { getAttribute(n: string): string | null }).getAttribute("colspan")) || 1);
          const p = { k, od: c, do: c + n - 1 };
          c += n;
          return p;
        });
      })
      .map((r) => r.filter((p) => !pustaKomorka(p.k)))
      .filter((r) => r.length);
  const rzadObrazow = (r?: Pole[]) => !!r && r.length > 1 && r.every((p) => tylkoObraz(p.k));
  const rzadPodpisow = (r?: Pole[]) => !!r && r.length > 0 && r.every((p) => tekstowa(p.k) && tekstKomorki(p.k).length <= 200);
  const czyGaleria = (t: Wezel) => {
    if (t.querySelectorAll("table").length || !t.querySelectorAll("img").length || czyTabelaDanych(t)) return false;
    const w = siatka(t);
    return w.some((r, i) => rzadObrazow(r) && (rzadPodpisow(w[i + 1]) || rzadPodpisow(w[i - 1])));
  };
  td.addRule("galerie", {
    filter: (node) => node.nodeName === "TABLE" && czyGaleria(node as unknown as Wezel),
    replacement: (_c, node) => {
      const w = siatka(node as unknown as Wezel);
      const md = (k: Wezel) => td.turndown(k.innerHTML).trim();
      // zdjęcia trafiają do podpisu, którego kolumny się z nimi pokrywają; reszta zostaje osobno, w kolejności
      const paruj = (zdjecia: Pole[], podpisy: Pole[], podpisPod: boolean) => {
        const out: string[] = [];
        const uzyte = new Set<Pole>();
        for (const c of podpisy) {
          for (const z of zdjecia) if (!uzyte.has(z) && z.do < c.od) (out.push(md(z.k)), uzyte.add(z));
          const pasujace = zdjecia.filter((z) => !uzyte.has(z) && z.od <= c.do && z.do >= c.od);
          pasujace.forEach((z) => uzyte.add(z));
          const obrazy = pasujace.map((z) => md(z.k)).join(" ");
          out.push((podpisPod ? [obrazy, md(c.k)] : [md(c.k), obrazy]).filter(Boolean).join("  \n"));
        }
        for (const z of zdjecia) if (!uzyte.has(z)) out.push(md(z.k));
        return out;
      };
      const wyjscie: string[] = [];
      for (let i = 0; i < w.length; i++) {
        if (rzadObrazow(w[i]) && rzadPodpisow(w[i + 1])) (wyjscie.push(...paruj(w[i], w[i + 1], true)), i++);
        else if (rzadPodpisow(w[i]) && rzadObrazow(w[i + 1])) (wyjscie.push(...paruj(w[i + 1], w[i], false)), i++);
        else w[i].forEach((p) => wyjscie.push(md(p.k)));
      }
      return `\n\n${wyjscie.filter(Boolean).join("\n\n")}\n\n`;
    },
  });
  // kolor tła komórki niósł w kilku tabelach znaczenie (np. czerwone = „najgorsze połączenie”, zielone = „najlepsze”);
  // Markdown nie ma kolorów, więc zamieniamy go na kolorowy znak (nie jest literą ani cyfrą – tekst autora się nie zmienia)
  const NAZWY: Record<string, string> = { red: "#ff0000", green: "#008000", lime: "#00ff00", orange: "#ffa500", yellow: "#ffff00", gray: "#808080", grey: "#808080", silver: "#c0c0c0", blue: "#0000ff", navy: "#000080", white: "#ffffff", black: "#000000" };
  const znakKoloru = (kolor: string | null | undefined) => {
    const k = (kolor ?? "").trim().toLowerCase();
    const hex = NAZWY[k] ?? (/^#?[0-9a-f]{6}$/.test(k) ? (k.startsWith("#") ? k : "#" + k) : "");
    if (!hex) return "";
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    if (Math.max(r, g, b) - Math.min(r, g, b) < 40) return Math.max(r, g, b) > 230 ? "" : "⬜";
    if (r > g + 60 && r > b + 60) return g > 110 ? "🟧" : "🟥";
    if (r > 180 && g > 180 && b < 120) return "🟨";
    if (g > r && g > b) return "🟩";
    if (b > r && b > g) return "🟦";
    return "";
  };
  td.addRule("tabele-danych", {
    filter: (node) => node.nodeName === "TABLE" && czyTabelaDanych(node as unknown as Wezel),
    replacement: (_c, node) => {
      const wiersze = wierszeTabeli(node as unknown as Wezel).map((w) =>
        w.map((k) => {
          const tresc = td
            .turndown(k.innerHTML)
            .replace(/^(?:---|\* \* \*)$/gm, "") // ozdobne linie poziome w komórkach – w tabeli wyglądałyby jak tekst
            .trim()
            .replace(/\n{2,}/g, "<br>")
            .replace(/ {2}\n|\n/g, "<br>")
            .replace(/\|/g, "\\|")
            .trim();
          let znak = znakKoloru((k as unknown as { getAttribute(n: string): string | null }).getAttribute("bgcolor"));
          if (znak === "⬜" && tresc) znak = ""; // szare tło pod tekstem to ozdoba nagłówka, nie informacja
          return znak ? `${znak}${tresc ? " " + tresc : ""}` : tresc;
        }),
      );
      const kolumn = Math.max(...wiersze.map((w) => w.length));
      const ZNAKI = /^(?:🟥|🟩|🟧|🟨|🟦|⬜)$/u;
      // pomijamy kolumny puste w każdym wierszu (odstępy) oraz pasy jednego koloru przez wiele wierszy (ozdobne rozdzielacze)
      const pelne = [...Array(kolumn).keys()].filter((i) => {
        const komorki = wiersze.map((w) => (w[i] ?? "").replace(/<br>/g, "").trim()).filter(Boolean);
        if (!komorki.length) return false;
        const pas = komorki.every((k) => ZNAKI.test(k)) && new Set(komorki).size === 1 && (komorki.length >= 4 || komorki[0] === "⬜");
        return !pas;
      });
      const tabela = wiersze.map((w) => pelne.map((i) => w[i] ?? "")).filter((w) => w.some((k) => k.trim()));
      if (!tabela.length) return "\n\n";
      if (pelne.length === 1) return `\n\n${tabela.map((w) => w[0]).join("\n\n")}\n\n`;
      // lista zbudowana z tabeli: pierwsza kolumna to same znaczniki („•”, „-”, „1.”)
      const znacznik = /^(?:[•·\-–]|\d+\.)$/;
      if (pelne.length === 2 && tabela.every((w) => znacznik.test(w[0].trim()))) {
        return `\n\n${tabela.map((w) => (/^\d+\.$/.test(w[0].trim()) ? `${w[0].trim()} ${w[1]}` : `- ${w[1]}`)).join("\n")}\n\n`;
      }
      const linia = (w: string[]) => `| ${w.map((k) => k || " ").join(" | ")} |`;
      return `\n\n${linia(tabela[0])}\n|${pelne.map(() => " --- ").join("|")}|\n${tabela.slice(1).map(linia).join("\n")}\n\n`;
    },
  });
  td.addRule("obrazy", {
    filter: "img",
    replacement: (_c, node) => {
      const el = node as unknown as HTMLImageElement;
      const src = el.getAttribute("src") ?? "";
      const alt = (el.getAttribute("alt") ?? "").replace(/\s+/g, " ").trim();
      return src ? `![${alt}](${src.replace(/ /g, "%20")})` : "";
    },
  });
  const body = $("body").length ? $("body").html() ?? "" : $.html();
  let md = td.turndown(body);
  md = md
    .replace(/[ \t]+\n/g, (m) => (m.endsWith("  \n") ? "  \n" : "\n"))
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return { md, obrazy };
}

function yaml(s: string) {
  return JSON.stringify(s);
}

// ---------- zapis ----------
rmSync(WYJSCIE, { recursive: true, force: true });
const indeks: Record<string, unknown>[] = [];
for (const w of kolejnosc) {
  const cel = plikMd.get(w.p)!;
  const { md, obrazy } = konwertuj(w);
  const fm = [
    "---",
    `id: ${yaml(idStrony(w.p))}`,
    `tytul: ${yaml(w.tytul)}`,
    `dzial: ${yaml(w.dzial.nazwa)}`,
    w.rodzic ? `rodzic: ${yaml(idStrony(w.rodzic))}` : null,
    `adres_oryginalny: ${yaml(ADRES + w.p)}`,
    `plik_zrodlowy: ${yaml(`${ZRODLO}/${w.p}`)}`,
    `liczba_obrazow: ${obrazy.length}`,
    "---",
  ]
    .filter(Boolean)
    .join("\n");
  mkdirSync(posix.dirname(cel), { recursive: true });
  writeFileSync(cel, `${fm}\n\n${md}\n`, "utf8");
  indeks.push({ id: idStrony(w.p), tytul: w.tytul, dzial: w.dzial.nazwa, plik: cel, znaki: md.length, obrazy: obrazy.length });
}

// ---------- KATALOG.md ----------
const linie: string[] = [
  "# Katalog archiwum uleszka.net",
  "",
  `Wszystkie artykuły serwisu w kolejności z menu strony. Razem: **${kolejnosc.length}** stron.`,
  "Podstrony (do których prowadzą linki z artykułu) są wcięte pod artykułem nadrzędnym.",
  "",
];
for (const d of DZIALY) {
  const wpisy = kolejnosc.filter((w) => w.dzial === d);
  if (!wpisy.length) continue;
  linie.push(`## ${d.nazwa}`, "", `_${d.opis}_`, "");
  for (const w of wpisy) {
    const i = indeks.find((x) => x.id === idStrony(w.p))!;
    const opis = [`${Math.round((i.znaki as number) / 1000)} tys. znaków`, i.obrazy ? `${i.obrazy} obr.` : null].filter(Boolean).join(", ");
    linie.push(`${"  ".repeat(w.poziom)}- [${w.tytul}](${encodeURI(plikMd.get(w.p)!)}) — ${opis}`);
  }
  linie.push("");
}
writeFileSync("KATALOG.md", linie.join("\n"), "utf8");
console.log(`Zapisano ${kolejnosc.length} artykułów w ${DZIALY.length} działach.`);
for (const d of DZIALY) console.log(`  ${d.nazwa}: ${kolejnosc.filter((w) => w.dzial === d).length}`);
