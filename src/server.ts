#!/usr/bin/env node
/**
 * Serwer MCP archiwum uleszka.net.
 * Pozwala asystentowi AI przeglądać, przeszukiwać (po słowach i po znaczeniu) i czytać artykuły strony
 * w oryginalnym brzmieniu, a także opracowania AI, opisy zdjęć i bibliotekę dzieł z domeny publicznej.
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "node:http";
import { z } from "zod";
import { Archiwum, JEZYKI, zloz, type Dokument } from "./archiwum.js";
import { Semantyka, zaladujModel, type Zbior } from "./semantyka.js";

const KATALOG_GLOWNY = process.env.ULESZKA_KATALOG ?? resolve(dirname(fileURLToPath(import.meta.url)), "..");
const ROZMIAR_CZESCI = 15000;
const archiwum = new Archiwum(KATALOG_GLOWNY);
const semantyka = new Semantyka(archiwum);
// model do wyszukiwania po znaczeniu ładujemy od razu w tle, żeby pierwsze zapytanie było szybkie
if (semantyka.dostepne("archiwum") && !process.env.ULESZKA_BEZ_MODELU) zaladujModel().catch(() => {});

const INSTRUKCJE = `To jest archiwum serwisu uleszka.net („Uwierz we własny rozum”) – prywatnej polskiej strony internetowej z lat ok. 2004–2007, której autorem był Leszek Klimek.
Zawiera ${archiwum.artykuly.length} stron w działach: ${archiwum.dzialy.join(", ")}.
Tematy: dawne cywilizacje, Atlantyda, piramidy, potop, kalendarze, katastrofy kosmiczne, medycyna naturalna, zdrowie i żywność, publicystyka.
Teksty artykułów są przeniesione bez żadnych zmian względem oryginału.
Dodatkowo: opracowania AI każdego artykułu (streszczenie, tezy z dosłownymi cytatami, tematy), opisy AI ${archiwum.opisyObrazow.size} zdjęć
oraz biblioteka ${archiwum.ksiazki.length} dawnych dzieł z domeny publicznej, na które powołuje się autor (Platon, Herodot, Księga Henocha, Popol Vuh, Mahabharata i in.).

Jak pracować:
- Spis treści: list_articles. Wyszukiwanie po słowach: search. Po znaczeniu (gdy słowa mogą być inne niż w tekście): search_by_meaning.
- Szybki przegląd artykułu: get_article_notes (opracowanie). Pełny tekst: read_article (długie artykuły mają kilka części).
- Powiązane artykuły: related_articles. Konkretne miejsca w długim tekście: find_in_article.
- Książki cytowane przez autora i gdzie są dostępne: list_books. Pełne teksty dawnych źródeł: list_library, read_book.
  Gdy autor powołuje się na Platona, Herodota, Biblię itp., sprawdź w bibliotece, co źródło naprawdę mówi.
  Dla wielu dzieł jest też tekst w języku oryginału (greka, łacina, hebrajski, dawny francuski, sanskryt) z numeracją miejsc –
  read_book(id, ref) otwiera wskazane miejsce. Własne tłumaczenia z oryginału oznaczaj jako przekład roboczy AI.
- Cytując archiwum, przytaczaj tekst dosłownie i podawaj tytuł artykułu. Opracowania i opisy zdjęć są pomocą AI, nie częścią oryginału.
- Wyraźnie oddzielaj to, co twierdzi autor strony, od aktualnej wiedzy i własnej oceny. Teksty pochodzą sprzed ok. 20 lat
  i zawierają wiele hipotez niezgodnych z dzisiejszą nauką (szczególnie w dziale medycznym) – omawiaj je rzetelnie,
  a przy porównaniu z obecną wiedzą korzystaj z wyszukiwarki, jeśli jest dostępna, i podawaj źródła.`;

/** Wiersze tabel z docs/ksiazki.md (lista książek cytowanych przez autora) z nazwą sekcji. */
const WIERSZE_KSIAZEK: { sekcja: string; wiersz: string }[] = (() => {
  const p = join(KATALOG_GLOWNY, "docs", "ksiazki.md");
  if (!existsSync(p)) return [];
  let sekcja = "";
  const out: { sekcja: string; wiersz: string }[] = [];
  for (const l of readFileSync(p, "utf8").split("\n")) {
    if (/^#{2,3} /.test(l)) sekcja = l.replace(/^#+ /, "");
    else if (l.startsWith("| ") && !/^\|\s*(Dzieło|Autor)\s*\|/.test(l) && !/^\|[-| ]+\|$/.test(l)) out.push({ sekcja, wiersz: l });
  }
  return out;
})();

/** Tworzy serwer MCP z narzędziami archiwum (jeden na połączenie; archiwum jest wczytane raz, wspólne). */
function utworzSerwer(): McpServer {
const STRONA_WWW = "https://jokerwader.github.io/uleszka-archiwum/";
const server = new McpServer(
  {
    name: "uleszka-archiwum",
    title: "U Leszka – archiwum uleszka.net",
    version: "1.3.0",
    websiteUrl: STRONA_WWW,
    // ikona konektora w aplikacjach AI (Claude, ChatGPT…)
    icons: [
      { src: `${STRONA_WWW}ikona.png`, mimeType: "image/png", sizes: ["512x512"] },
      { src: `${STRONA_WWW}favicon.png`, mimeType: "image/png", sizes: ["64x64"] },
    ],
  },
  { instructions: INSTRUKCJE },
);

const tekst = (t: string) => ({ content: [{ type: "text" as const, text: t }] });
const blad = (t: string) => ({ content: [{ type: "text" as const, text: t }], isError: true });
const wersje = (k: Dokument) => {
  const { oryginaly, przeklady } = archiwum.powiazaneWersje(k);
  if (oryginaly.length) return `tekst w języku oryginału: ${oryginaly.map((o) => `${o.id} (${JEZYKI[String(o.meta.jezyk)]})`).join(", ")}`;
  if (przeklady.length) return `przekład w bibliotece: ${przeklady.map((p) => p.id).join(", ")}`;
  return "";
};
const naglowek = (a: Dokument) =>
  a.rodzaj === "ksiazka"
    ? [
        `# ${a.tytul}`,
        `id: ${a.id} | autor: ${a.autor}${a.meta.tlumacz ? ` | przekład: ${a.meta.tlumacz}` : ""} | język: ${JEZYKI[String(a.meta.jezyk)] ?? a.meta.jezyk}${a.meta.rodzaj_tekstu ? " (ORYGINAŁ)" : ""}`,
        a.meta.wydanie ? `wydanie: ${a.meta.wydanie}` : "",
        wersje(a),
        `źródło: ${a.adresOryginalny} | licencja: ${a.meta.licencja}`,
      ]
        .filter(Boolean)
        .join("\n")
    : [
        `# ${a.tytul}`,
        `id: ${a.id} | dział: ${a.dzial}${a.rodzic ? ` | podstrona artykułu: ${a.rodzic}` : ""}`,
        `oryginał: ${a.adresOryginalny} | plik w repozytorium: ${a.plik}`,
      ].join("\n");
const nieZnaleziono = (klucz: string, coTo = "artykułu") =>
  blad(`Nie znaleziono ${coTo} „${klucz}”. Użyj ${coTo === "książki" ? "list_library" : "list_articles albo search"}, żeby znaleźć właściwe id.`);
const stopkaCzesci = (a: Dokument, part: number, ile: number, narzedzie: string) =>
  ile > 1
    ? part < ile
      ? `[Część ${part} z ${ile}. Dalej: ${narzedzie}(id: "${a.id}", part: ${part + 1})]`
      : `[Koniec – część ${part} z ${ile}.]`
    : "[Koniec.]";

// ---------------- narzędzia: archiwum ----------------

server.registerTool(
  "list_articles",
  {
    title: "Spis treści archiwum",
    description:
      "Lists all articles of the uleszka.net archive (Polish) in the original site order, grouped by section (dział). Returns id, title, length and number of parts for each article. Optionally filter by section name.",
    inputSchema: {
      section: z.string().optional().describe(`Nazwa działu, np. ${archiwum.dzialy.map((d) => `„${d}”`).join(", ")}`),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ section }) => {
    const lista = section ? archiwum.artykuly.filter((a) => a.dzial.toLowerCase() === section.toLowerCase()) : archiwum.artykuly;
    if (!lista.length) return blad(`Brak działu „${section}”. Dostępne: ${archiwum.dzialy.join(", ")}`);
    const linie: string[] = [];
    let dzial = "";
    for (const a of lista) {
      if (a.dzial !== dzial) {
        dzial = a.dzial;
        linie.push(`\n## ${dzial}`);
      }
      const czesci = archiwum.czesci(a, ROZMIAR_CZESCI).length;
      const tematy = archiwum.opracowania.get(a.id)?.tematy.slice(0, 4).join(", ");
      linie.push(
        `${a.rodzic ? "  " : ""}- ${a.tytul} — id: ${a.id} (${Math.round(a.czysty.length / 1000)} tys. znaków${czesci > 1 ? `, ${czesci} części` : ""}${a.obrazy.length ? `, ${a.obrazy.length} obr.` : ""})${tematy ? ` · ${tematy}` : ""}`,
      );
    }
    return tekst(`Archiwum uleszka.net – ${lista.length} stron${linie.join("\n")}`);
  },
);

server.registerTool(
  "search",
  {
    title: "Szukaj słów",
    description:
      "Keyword full-text search (content is Polish – query in Polish; diacritics optional, prefix and fuzzy matching). scope='archiwum' (default) searches the website's articles, their AI notes and AI photo descriptions; scope='biblioteka' searches the public-domain library of ancient sources. Returns ranked documents with verbatim passages. For searching by meaning/concept use search_by_meaning.",
    inputSchema: {
      query: z.string().min(1).describe("Słowa do wyszukania, np. „Atlantyda Platon” albo „wapn kosci”"),
      scope: z.enum(["archiwum", "biblioteka"]).default("archiwum").describe("archiwum = artykuły strony; biblioteka = dawne dzieła"),
      section: z.string().optional().describe("Ogranicz do działu archiwum"),
      limit: z.number().int().min(1).max(50).default(10).describe("Maksymalna liczba wyników"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ query, scope, section, limit }) => {
    const { tryb, lacznie, wyniki } = archiwum.szukaj(query, { dzial: section, limit, zakres: scope });
    if (!wyniki.length) return tekst(`Brak wyników dla „${query}”.`);
    const bloki = wyniki.map(({ artykul: a, terminy }) => {
      const fr = archiwum.fragmenty(a, terminy, 160, 3);
      const zrodlo = a.rodzaj === "ksiazka" ? `książka, ${a.autor}` : `dział: ${a.dzial}`;
      const linie = [`## ${a.tytul}  (id: ${a.id}, ${zrodlo})`, `trafień w tekście: ${fr.lacznie}`, ...fr.fragmenty.map((f) => `> ${f.tekst}`)];
      if (!fr.lacznie && a.rodzaj === "artykul") {
        const o = archiwum.opracowania.get(a.id);
        if (o) linie.push(`(trafienie w opracowaniu lub opisach zdjęć) Streszczenie: ${o.streszczenie}`);
      }
      return linie.join("\n");
    });
    return tekst(`Znaleziono ${lacznie} (dopasowanie: ${tryb}). Pokazuję ${wyniki.length}.\n\n${bloki.join("\n\n")}`);
  },
);

server.registerTool(
  "search_by_meaning",
  {
    title: "Szukaj po znaczeniu",
    description:
      "Semantic search: finds passages whose MEANING matches the query, even if they use different words (e.g. 'katastrofy z kosmosu' finds texts about comets, Tiamat, meteorites). Works in Polish and English. scope: 'archiwum' (articles, AI notes, AI photo descriptions), 'biblioteka' (ancient public-domain sources) or 'wszystko'. Returns the best matching passages with their article/book ids.",
    inputSchema: {
      query: z.string().min(2).describe("Pytanie lub opis tematu, np. „czy dawne cywilizacje znały energię atomową”"),
      scope: z.enum(["archiwum", "biblioteka", "wszystko"]).default("archiwum"),
      limit: z.number().int().min(1).max(30).default(10),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ query, scope, limit }) => {
    const zbiory: Zbior[] = scope === "wszystko" ? ["archiwum", "biblioteka"] : [scope];
    const dostepne = zbiory.filter((z) => semantyka.dostepne(z));
    if (!dostepne.length) return blad(`Wyszukiwanie po znaczeniu nie jest dostępne dla „${scope}” (brak policzonych wektorów – uruchom npm run wektory). Użyj search.`);
    let wyniki;
    try {
      wyniki = await semantyka.szukaj(query, dostepne, limit);
    } catch (e) {
      return blad(`Nie udało się załadować modelu do wyszukiwania po znaczeniu (${(e as Error).message}). Użyj search.`);
    }
    const bloki = wyniki.map(({ fragment: f, wynik }) => {
      const d = archiwum.znajdz(f.d);
      const kto = d?.rodzaj === "ksiazka" ? `książka, ${d.autor}` : `dział: ${d?.dzial}`;
      return `## ${d?.tytul ?? f.d}  (id: ${f.d}, ${kto}, podobieństwo ${wynik.toFixed(2)})\n> ${semantyka.tekstFragmentu(f, d)}`;
    });
    return tekst(`Najbliższe znaczeniowo fragmenty dla „${query}” (${dostepne.join(" + ")}):\n\n${bloki.join("\n\n")}`);
  },
);

server.registerTool(
  "read_article",
  {
    title: "Czytaj artykuł",
    description: `Returns the full original text of an article as Markdown (verbatim). Long articles are split into parts of ~${ROZMIAR_CZESCI} characters – read all parts to see the whole text. Images appear as Markdown image links with repository paths, each followed by an AI description in [opis AI: …] (not part of the original); use get_image to view one. Links to other articles appear as artykul:<id>.`,
    inputSchema: {
      id: z.string().describe("id artykułu (z list_articles/search) albo jego tytuł"),
      part: z.number().int().min(1).default(1).describe("Numer części (od 1)"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ id, part }) => {
    const a = archiwum.znajdz(id, "artykul");
    if (!a) return nieZnaleziono(id);
    const czesci = archiwum.czesci(a, ROZMIAR_CZESCI);
    if (part > czesci.length) return blad(`Artykuł ma tylko ${czesci.length} części.`);
    const tresc = czesci[part - 1].replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (m, _alt, src: string) => {
      const opis = archiwum.opisObrazu(src);
      return opis ? `${m} [opis AI: ${opis}]` : m;
    });
    const pod = archiwum.podstrony(a);
    const ksiazki = archiwum.ksiazkiArtykulu(a.id);
    const stopka = [
      stopkaCzesci(a, part, czesci.length, "read_article"),
      pod.length && part === czesci.length ? `Podstrony: ${pod.map((p) => `${p.tytul} (id: ${p.id})`).join("; ")}` : "",
      part === czesci.length && archiwum.opracowania.has(a.id) ? `Opracowanie (streszczenie, tezy, tematy): get_article_notes(id: "${a.id}"). Podobne artykuły: related_articles.` : "",
      part === czesci.length && ksiazki.length ? `Źródła cytowane w artykule, dostępne w bibliotece (read_book): ${ksiazki.map((k) => `${k.tytul} (id: ${k.id})`).join("; ")}` : "",
    ]
      .filter(Boolean)
      .join("\n");
    return tekst(`${naglowek(a)}${czesci.length > 1 ? ` | część ${part} z ${czesci.length}` : ""}\n\n---\n\n${tresc}\n\n---\n${stopka}`);
  },
);

server.registerTool(
  "get_article_notes",
  {
    title: "Opracowanie artykułu",
    description:
      "Returns the AI-prepared notes for an article: summary, the author's main theses (each with a verbatim quote verified to occur in the article), topics, people, places, dates/periods and sources the author cites. Use it for a quick overview or to compare the author's claims with current knowledge. Notes are an AI aid, not part of the original website.",
    inputSchema: { id: z.string().describe("id albo tytuł artykułu") },
    annotations: { readOnlyHint: true },
  },
  async ({ id }) => {
    const a = archiwum.znajdz(id, "artykul");
    if (!a) return nieZnaleziono(id);
    const o = archiwum.opracowania.get(a.id);
    if (!o) return blad(`Artykuł „${a.tytul}” nie ma jeszcze opracowania.`);
    const lista = (nazwa: string, x: string[]) => (x.length ? `**${nazwa}:** ${x.join(", ")}` : "");
    const ksiazki = archiwum.ksiazkiArtykulu(a.id);
    return tekst(
      [
        `# Opracowanie: ${a.tytul}`,
        `id: ${a.id} | dział: ${a.dzial} | (opracowanie AI – nie jest częścią oryginalnej strony)`,
        "",
        `**Streszczenie:** ${o.streszczenie}`,
        "",
        o.tezy.length ? "**Tezy autora:**" : "",
        ...o.tezy.map((t, i) => `${i + 1}. ${t.teza} *(${t.dziedzina})*\n   > „${t.cytat}”`),
        "",
        lista("Tematy", o.tematy),
        lista("Osoby", o.osoby),
        lista("Miejsca", o.miejsca),
        o.okresy.length ? `**Daty i okresy:** ${o.okresy.map((x) => `${x.kiedy} – ${x.co}`).join("; ")}` : "",
        lista("Źródła cytowane przez autora", o.zrodla_cytowane),
        ksiazki.length ? `**W bibliotece (read_book):** ${ksiazki.map((k) => `${k.tytul} (id: ${k.id})`).join("; ")}` : "",
      ]
        .filter((l) => l !== "")
        .join("\n"),
    );
  },
);

server.registerTool(
  "related_articles",
  {
    title: "Powiązane artykuły",
    description: "Finds articles related to the given one – by meaning (semantic similarity of the whole text) and by shared topics, people and places from the AI notes.",
    inputSchema: {
      id: z.string().describe("id albo tytuł artykułu"),
      limit: z.number().int().min(1).max(20).default(8),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ id, limit }) => {
    const a = archiwum.znajdz(id, "artykul");
    if (!a) return nieZnaleziono(id);
    const poZnaczeniu = semantyka.podobne(a.id, limit);
    const poTematach = archiwum.podobnePoTematach(a.id, limit);
    const linie = [`# Artykuły powiązane z „${a.tytul}”`];
    if (poZnaczeniu.length) {
      linie.push("", "## Najbliższe znaczeniowo");
      for (const p of poZnaczeniu) {
        const d = archiwum.znajdz(p.id)!;
        linie.push(`- ${d.tytul} (id: ${d.id}, dział: ${d.dzial}, podobieństwo ${p.wynik.toFixed(2)})`);
      }
    }
    if (poTematach.length) {
      linie.push("", "## Wspólne tematy, osoby i miejsca");
      for (const p of poTematach) linie.push(`- ${p.artykul.tytul} (id: ${p.artykul.id}) – wspólne: ${p.wspolne.slice(0, 6).join(", ")}`);
    }
    if (linie.length === 1) linie.push("Brak danych o powiązaniach.");
    return tekst(linie.join("\n"));
  },
);

server.registerTool(
  "find_in_article",
  {
    title: "Szukaj w artykule lub książce",
    description:
      "Finds all places in ONE article or library book where the given words occur and returns verbatim passages with context. Useful for long texts. Matching ignores case and Polish diacritics.",
    inputSchema: {
      id: z.string().describe("id albo tytuł artykułu (albo id książki z biblioteki)"),
      phrase: z.string().min(2).describe("Słowo lub fraza (wyszukiwane jako ciąg znaków, także fragment słowa)"),
      context: z.number().int().min(50).max(2000).default(400).describe("Ile znaków kontekstu z każdej strony"),
      limit: z.number().int().min(1).max(50).default(15),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ id, phrase, context, limit }) => {
    const a = archiwum.znajdz(id);
    if (!a) return nieZnaleziono(id);
    const fr = archiwum.fragmenty(a, [phrase], context, limit);
    if (!fr.lacznie) return tekst(`W „${a.tytul}” nie ma frazy „${phrase}”.`);
    return tekst(
      `„${phrase}” w „${a.tytul}” (id: ${a.id}): ${fr.lacznie} wystąpień, ${fr.wszystkichFragmentow} fragmentów, pokazuję ${fr.fragmenty.length}.\n\n` +
        fr.fragmenty.map((f, i) => `### Fragment ${i + 1} (znak ${f.od})\n${f.tekst}`).join("\n\n"),
    );
  },
);

const TYPY: Record<string, string> = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".png": "image/png", ".bmp": "image/bmp" };
const ZRODLO = resolve(KATALOG_GLOWNY, "zrodlo");

server.registerTool(
  "get_image",
  {
    title: "Pokaż obraz",
    description:
      "Returns an image from the archive together with its AI description. Pass a path shown in read_article (e.g. zrodlo/webacja/01potop/gilgam.gif), or an article id to list that article's images with their AI descriptions.",
    inputSchema: {
      path: z.string().optional().describe("Ścieżka obrazu z treści artykułu"),
      article_id: z.string().optional().describe("Zamiast ścieżki: id artykułu – zwraca listę jego obrazów z opisami"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ path, article_id }) => {
    if (article_id) {
      const a = archiwum.znajdz(article_id, "artykul");
      if (!a) return nieZnaleziono(article_id);
      if (!a.obrazy.length) return tekst(`Artykuł „${a.tytul}” nie ma obrazów.`);
      return tekst(
        `Obrazy w artykule „${a.tytul}” (${a.obrazy.length}; opisy przygotowała AI):\n` +
          a.obrazy
            .map((o, i) => {
              const op = archiwum.opisyObrazow.get(o.sciezka);
              return `${i + 1}. ${o.sciezka}${op ? ` — [${op.typ}] ${op.opis}${op.tekst_na_obrazie ? ` Napis: „${op.tekst_na_obrazie}”` : ""}` : ""}`;
            })
            .join("\n"),
      );
    }
    if (!path) return blad("Podaj path albo article_id.");
    const pelna = resolve(KATALOG_GLOWNY, path);
    if (!pelna.startsWith(ZRODLO + sep) || !existsSync(pelna)) return blad(`Nie ma takiego obrazu w archiwum: ${path}`);
    const typ = TYPY[extname(pelna).toLowerCase()];
    if (!typ) return blad("To nie jest obsługiwany plik graficzny.");
    const op = archiwum.opisyObrazow.get(path.replace(/\\/g, "/"));
    return {
      content: [
        { type: "image" as const, data: readFileSync(pelna).toString("base64"), mimeType: typ },
        ...(op ? [{ type: "text" as const, text: `Opis AI [${op.typ}]: ${op.opis}${op.tekst_na_obrazie ? ` Napis na obrazie: „${op.tekst_na_obrazie}”` : ""}` }] : []),
      ],
    };
  },
);

// ---------------- narzędzia: książki i biblioteka ----------------

server.registerTool(
  "list_books",
  {
    title: "Książki cytowane przez autora",
    description:
      "Lists books and ancient sources cited in the archive's articles, with information where they can be read for free and legally (or that they are copyrighted). Filter by a search phrase (author/title) or by article id. Books available in full in the built-in library can be read with read_book.",
    inputSchema: {
      query: z.string().optional().describe("Fragment autora lub tytułu, np. „Platon”, „Däniken”"),
      article_id: z.string().optional().describe("Pokaż książki cytowane w tym artykule"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ query, article_id }) => {
    let wiersze = WIERSZE_KSIAZEK;
    if (!wiersze.length) return blad("Brak pliku docs/ksiazki.md.");
    let opis = "wszystkie";
    if (article_id) {
      const a = archiwum.znajdz(article_id, "artykul");
      if (!a) return nieZnaleziono(article_id);
      wiersze = wiersze.filter((w) => w.wiersz.includes(encodeURI(a.plik.replace(/^artykuly\//, ""))));
      opis = `cytowane w „${a.tytul}”`;
    }
    if (query) {
      wiersze = wiersze.filter((w) => zloz(w.wiersz).includes(zloz(query)));
      opis += ` pasujące do „${query}”`;
    }
    if (!wiersze.length) return tekst(`Nie znaleziono książek (${opis}).`);
    const linie = [`# Książki i źródła (${opis}) – ${wiersze.length}`];
    let sekcja = "";
    for (const w of wiersze) {
      if (w.sekcja !== sekcja) {
        sekcja = w.sekcja;
        linie.push("", `## ${sekcja}`);
      }
      // linki do artykułów skracamy do tytułów, żeby odpowiedź była zwięzła
      linie.push(w.wiersz.replace(/\]\(\.\.\/artykuly\/[^)]+\)/g, "]"));
    }
    const wBibliotece = archiwum.ksiazki.filter((k) => !query || zloz(`${k.tytul} ${k.autor}`).includes(zloz(query)));
    if (wBibliotece.length && wBibliotece.length < archiwum.ksiazki.length)
      linie.push("", `W bibliotece (pełny tekst, read_book): ${wBibliotece.map((k) => `${k.tytul} (id: ${k.id})`).join("; ")}`);
    return tekst(linie.join("\n"));
  },
);

server.registerTool(
  "list_library",
  {
    title: "Biblioteka dawnych źródeł",
    description:
      "Lists the built-in library: full texts of ancient and historical works cited by the author that are in the public domain (Plato's Timaeus and Critias, Herodotus, Genesis, Ovid, the Book of Enoch, Popol Vuh, Gilgamesh, Hammurabi, Book of the Dead, Strabo, Pliny, Mahabharata, Ramayana, Nostradamus, Charles Fort and more) – translations (Polish/English) and, for many works, the ORIGINAL-LANGUAGE text (Ancient Greek, Latin, Hebrew, old French, Sanskrit) with standard citation numbering. Use read_book (optionally with ref, e.g. '24e', '2.148', '6:4') / find_in_article / search(scope='biblioteka') on them.",
    inputSchema: {},
    annotations: { readOnlyHint: true },
  },
  async () => {
    const wiersz = (k: Dokument) => {
      const ile = archiwum.czesci(k, ROZMIAR_CZESCI).length;
      const cyt = (k.meta.cytowane_w as string[] | undefined) ?? [];
      const w = wersje(k);
      return `- ${k.tytul} — ${k.autor}${k.meta.tlumacz ? `, przekład: ${k.meta.tlumacz}` : ""} (${JEZYKI[String(k.meta.jezyk)] ?? k.meta.jezyk}) — id: ${k.id} (${ile} części)${w ? ` · ${w}` : ""}${k.meta.uwagi ? ` · ${k.meta.uwagi}` : ""}${cyt.length ? ` · cytowane w ${cyt.length} art.` : ""}`;
    };
    const przeklady = archiwum.ksiazki.filter((k) => !k.meta.rodzaj_tekstu);
    const oryginaly = archiwum.ksiazki.filter((k) => k.meta.rodzaj_tekstu);
    return tekst(
      [
        `# Biblioteka – ${archiwum.ksiazki.length} tekstów z domeny publicznej`,
        "",
        `## Przekłady (${przeklady.length})`,
        ...przeklady.map(wiersz),
        "",
        `## Teksty w językach oryginału (${oryginaly.length})`,
        "Fragmenty mają standardową numerację w nawiasach, np. [24e], [2.148.1], [1.37], [6:4] – read_book(id, ref) otwiera wskazane miejsce.",
        "Tłumacząc z oryginału, zaznacz, że to przekład roboczy AI, i porównaj go z opublikowanym przekładem z biblioteki.",
        ...oryginaly.map(wiersz),
      ].join("\n"),
    );
  },
);

server.registerTool(
  "read_book",
  {
    title: "Czytaj dzieło z biblioteki",
    description: `Returns the text of a public-domain book from the library, in parts of ~${ROZMIAR_CZESCI} characters. Books are long – use find_in_article(id, phrase) or search(scope='biblioteka') to locate the relevant part first. For original-language texts (and translations with numbering) pass ref = standard citation to open that exact place: Plato Stephanus '24e', Herodotus/Strabo/Caesar 'book.chapter' or 'book.chapter.section' ('2.148'), poems 'book.line' ('1.37'), Pliny 'book.section' ('36.75'), Genesis 'chapter:verse' ('6:4'), Ramayana/Mahabharata 'book.chapter' ('6.5').`,
    inputSchema: {
      id: z.string().describe("id książki z list_library, np. „platon-kritias” albo „platon-kritias-grc” (oryginał)"),
      part: z.number().int().min(1).default(1),
      ref: z.string().optional().describe("numeracja miejsca w dziele, np. „113c”, „2.148”, „1.37”, „6:4” – zwraca fragment od tego miejsca"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ id, part, ref }) => {
    const k = archiwum.znajdz(id, "ksiazka");
    if (!k) return nieZnaleziono(id, "książki");
    if (ref) {
      const od = archiwum.miejsce(k, ref);
      if (od === undefined) return blad(`Nie znaleziono miejsca [${ref}] w „${k.tytul}”. Numeracja w tym tekście wygląda tak: ${(k.tresc.match(/\[[^\]\s]{1,12}\]/g) ?? []).slice(0, 5).join(" ") || "(brak – użyj find_in_article)"}.`);
      let fragment = k.tresc.slice(od, od + ROZMIAR_CZESCI);
      const koniec = fragment.lastIndexOf("\n");
      if (od + ROZMIAR_CZESCI < k.tresc.length && koniec > ROZMIAR_CZESCI / 2) fragment = fragment.slice(0, koniec);
      return tekst(`${naglowek(k)} | od miejsca [${ref}]\n\n---\n\n${fragment}\n\n---\n[Dalej: read_book(id: "${k.id}", ref: …) z następnym numerem, albo find_in_article.]`);
    }
    const czesci = archiwum.czesci(k, ROZMIAR_CZESCI);
    if (part > czesci.length) return blad(`Książka ma tylko ${czesci.length} części.`);
    return tekst(`${naglowek(k)} | część ${part} z ${czesci.length}\n\n---\n\n${czesci[part - 1]}\n\n---\n${stopkaCzesci(k, part, czesci.length, "read_book")}`);
  },
);

// ---------------- zasoby ----------------

server.registerResource(
  "katalog",
  "uleszka://katalog",
  { title: "Katalog archiwum uleszka.net", description: "Spis treści wszystkich artykułów", mimeType: "text/markdown" },
  async (uri) => ({ contents: [{ uri: uri.href, mimeType: "text/markdown", text: readFileSync(join(KATALOG_GLOWNY, "KATALOG.md"), "utf8") }] }),
);

// ---------------- gotowe polecenia (prompty) ----------------

server.registerPrompt(
  "omow_artykul",
  {
    title: "Omów artykuł i porównaj z obecną wiedzą",
    description: "Wierne streszczenie tez artykułu, sprawdzenie źródeł autora, a potem zestawienie każdej tezy z aktualną wiedzą.",
    argsSchema: { artykul: z.string().describe("id albo tytuł artykułu") },
  },
  ({ artykul }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Omów artykuł „${artykul}” z archiwum uleszka.net.
1. Pobierz opracowanie (get_article_notes) i przeczytaj artykuł w całości (read_article – wszystkie części).
2. Streść wiernie główne tezy autora, każdą z krótkim dosłownym cytatem.
3. Gdy autor powołuje się na dawne źródło dostępne w bibliotece (Platon, Herodot, Biblia, Księga Henocha, Popol Vuh…), sprawdź w nim (find_in_article / read_book), czy źródło rzeczywiście to mówi.
4. Każdą tezę oceń w świetle dzisiejszej wiedzy (użyj wyszukiwarki internetowej, jeśli jest dostępna) i oznacz: potwierdzone / częściowo trafne / sporne / obalone / niesprawdzalne. Podaj źródła.
5. Wskaż, co od czasu napisania tekstu (ok. 2004–2007) się zmieniło: nowe odkrycia, badania, wydarzenia. Zaproponuj powiązane artykuły (related_articles).
Wyraźnie oddzielaj zdanie autora od swojej oceny.`,
        },
      },
    ],
  }),
);

server.registerPrompt(
  "szukaj_odzwierciedlen",
  {
    title: "Temat: co pisał autor, a co wiemy dziś",
    description: "Zbiera wszystko, co archiwum mówi na dany temat, i szuka odzwierciedleń w obecnej wiedzy i wydarzeniach.",
    argsSchema: { temat: z.string().describe("Temat, np. „potop”, „Tiahuanaco”, „fluor”") },
  },
  ({ temat }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Temat: „${temat}”.
1. Znajdź w archiwum uleszka.net wszystko na ten temat: search_by_meaning (po znaczeniu) i search (po słowach), potem get_article_notes i find_in_article w trafionych artykułach. Zbierz to, co pisał autor – z dosłownymi cytatami i tytułami artykułów.
2. Jeśli autor opiera się na dawnych źródłach, sprawdź je w bibliotece (search z scope „biblioteka”, read_book).
3. Poszukaj odzwierciedleń w obecnej wiedzy: aktualne badania, odkrycia, wydarzenia i publikacje (użyj wyszukiwarki internetowej, jeśli jest dostępna). Podaj źródła i daty.
4. Zestaw to w tabeli: teza autora | co wiemy dziś | ocena (potwierdzone / sporne / obalone / niesprawdzalne).
Wyraźnie oddzielaj zdanie autora od swojej oceny.`,
        },
      },
    ],
  }),
);

server.registerPrompt(
  "sprawdz_zrodlo",
  {
    title: "Sprawdź, co naprawdę mówi źródło",
    description: "Porównuje to, co autor strony przypisuje dawnemu źródłu (np. Platonowi, Herodotowi, Biblii), z oryginalnym tekstem w bibliotece.",
    argsSchema: { teza: z.string().describe("Twierdzenie lub temat, np. „Platon o zagładzie Atlantydy w jeden dzień i jedną noc”") },
  },
  ({ teza }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Sprawdź źródło dla: „${teza}”.
1. Znajdź w archiwum uleszka.net, co autor pisze na ten temat i na jakie źródło się powołuje (search_by_meaning, search, find_in_article). Zacytuj go dosłownie.
2. Znajdź to źródło w bibliotece (list_library, search z scope „biblioteka”, find_in_article, read_book) i zacytuj odpowiedni fragment przekładu (z podaniem tłumacza i numeracji miejsca).
3. Jeśli w bibliotece jest tekst w języku oryginału (greka, łacina, hebrajski, francuski, sanskryt), otwórz to samo miejsce (read_book z ref, np. „24e”, „2.148”, „6:4”), przytocz oryginał i przetłumacz go dosłownie – oznacz to jako przekład roboczy AI. Wskaż, czy przekład lub autor strony nie zmienił sensu.
4. Porównaj: czy autor oddał źródło wiernie, czy coś dodał, pominął lub zinterpretował po swojemu? Jeśli źródła nie ma w bibliotece, sprawdź list_books i powiedz, gdzie można je przeczytać.`,
        },
      },
    ],
  }),
);

return server;
}

// ---------------- uruchomienie ----------------
// Bez parametrów: tryb lokalny (stdio) – dla Claude Desktop / Claude Code.
// Z PORT w zmiennych środowiskowych albo z --http: tryb internetowy (Streamable HTTP pod adresem /mcp)
// – dla ChatGPT, Claude.ai i innych klientów łączących się przez adres URL.
const port = process.env.PORT ?? (process.argv.includes("--http") ? "3000" : undefined);

if (!port) {
  await utworzSerwer().connect(new StdioServerTransport());
} else {
  const STRONA = `Serwer MCP archiwum uleszka.net (${archiwum.artykuly.length} artykułów).
Adres dla asystenta AI: <ten adres>/mcp
Instrukcja dla każdego: https://jokerwader.github.io/uleszka-archiwum/
Kod: https://github.com/jokerwader/uleszka-archiwum
`;
  const IKONY: Record<string, string> = {
    "/favicon.ico": join(KATALOG_GLOWNY, "docs", "favicon.png"),
    "/favicon.png": join(KATALOG_GLOWNY, "docs", "favicon.png"),
    "/icon.png": join(KATALOG_GLOWNY, "docs", "ikona.png"),
    "/apple-touch-icon.png": join(KATALOG_GLOWNY, "docs", "ikona.png"),
  };
  // prosty limit zapytań z jednego adresu IP – chroni publiczny serwer przed zalewem zapytań (i kosztami)
  const LIMIT_NA_MINUTE = Number(process.env.ULESZKA_LIMIT_NA_MINUTE ?? 120);
  const licznik = new Map<string, { okno: number; n: number }>();
  setInterval(() => {
    const teraz = Math.floor(Date.now() / 60000);
    for (const [ip, w] of licznik) if (w.okno < teraz) licznik.delete(ip);
  }, 60000).unref();
  const zaDuzo = (ip: string) => {
    const okno = Math.floor(Date.now() / 60000);
    const w = licznik.get(ip);
    if (!w || w.okno !== okno) {
      licznik.set(ip, { okno, n: 1 });
      return false;
    }
    return ++w.n > LIMIT_NA_MINUTE;
  };

  createServer(async (req, res) => {
    const sciezka = new URL(req.url ?? "/", "http://localhost").pathname;
    // CORS – żeby z serwera mogły korzystać także klienty działające w przeglądarce (np. MCP Inspector)
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization, Mcp-Session-Id, Mcp-Protocol-Version, Last-Event-ID");
    res.setHeader("Access-Control-Expose-Headers", "Mcp-Session-Id, Mcp-Protocol-Version");
    if (req.method === "OPTIONS") {
      res.writeHead(204).end();
      return;
    }
    const ip = String(req.headers["x-forwarded-for"] ?? "").split(",")[0].trim() || req.socket.remoteAddress || "?";
    try {
      if (sciezka === "/mcp") {
        if (zaDuzo(ip)) {
          res.writeHead(429, { "Content-Type": "application/json", "Retry-After": "60" });
          res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32000, message: "Za dużo zapytań – spróbuj za minutę" }, id: null }));
          return;
        }
        if (req.method !== "POST") {
          res.writeHead(405, { Allow: "POST", "Content-Type": "application/json" });
          res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32000, message: "Method not allowed" }, id: null }));
          return;
        }
        // tryb bezstanowy: każde zapytanie dostaje własny serwer i transport
        const server = utworzSerwer();
        const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
        res.on("close", () => {
          void transport.close();
          void server.close();
        });
        await server.connect(transport);
        await transport.handleRequest(req, res);
        return;
      }
      if (sciezka === "/" || sciezka === "/health") {
        res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
        res.end(STRONA);
        return;
      }
      // ikona pod adresem serwera – część aplikacji pokazuje favicon domeny konektora
      if (IKONY[sciezka] && existsSync(IKONY[sciezka])) {
        res.writeHead(200, { "Content-Type": "image/png", "Cache-Control": "public, max-age=86400" });
        res.end(readFileSync(IKONY[sciezka]));
        return;
      }
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Nie znaleziono. Serwer MCP działa pod adresem /mcp\n");
    } catch (e) {
      console.error(e);
      if (!res.headersSent) res.writeHead(500).end();
    }
  }).listen(Number(port), "0.0.0.0", () => console.error(`Serwer MCP uleszka (HTTP) nasłuchuje na porcie ${port}, adres /mcp`));
}
