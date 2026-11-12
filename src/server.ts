#!/usr/bin/env node
/**
 * Serwer MCP archiwum uleszka.net.
 * Pozwala asystentowi AI przeglądać, przeszukiwać i czytać artykuły serwisu w oryginalnym brzmieniu.
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { Archiwum, type Artykul } from "./archiwum.js";

const KATALOG_GLOWNY = process.env.ULESZKA_KATALOG ?? resolve(dirname(fileURLToPath(import.meta.url)), "..");
const ROZMIAR_CZESCI = 15000;
const archiwum = new Archiwum(KATALOG_GLOWNY);

const INSTRUKCJE = `To jest archiwum serwisu uleszka.net – prywatnej polskiej strony internetowej (ok. 2004–2007) autorstwa „Uleszki”.
Zawiera ${archiwum.artykuly.length} stron w działach: ${archiwum.dzialy.join(", ")}.
Tematy: dawne cywilizacje, Atlantyda, piramidy, potop, kalendarze, katastrofy kosmiczne, medycyna naturalna, zdrowie i żywność, publicystyka.
Teksty są przeniesione bez żadnych zmian względem oryginału.

Jak pracować:
- Zacznij od list_articles (spis treści) albo search (wyszukiwanie pełnotekstowe, odporne na brak polskich znaków).
- Czytaj artykuły przez read_article; długie artykuły mają kilka części (parametr part).
- W długim artykule szukaj konkretnych miejsc przez find_in_article.
- Cytując archiwum, przytaczaj tekst dosłownie i podawaj tytuł artykułu.
- Wyraźnie oddzielaj to, co twierdzi autor strony, od aktualnej wiedzy i własnej oceny. Teksty pochodzą sprzed ok. 20 lat
  i zawierają wiele hipotez niezgodnych z dzisiejszą nauką (szczególnie w dziale medycznym) – omawiaj je rzetelnie,
  a przy porównaniu z obecną wiedzą korzystaj z wyszukiwarki, jeśli jest dostępna, i podawaj źródła.`;

const server = new McpServer({ name: "uleszka-archiwum", version: "1.0.0" }, { instructions: INSTRUKCJE });

const tekst = (t: string) => ({ content: [{ type: "text" as const, text: t }] });
const blad = (t: string) => ({ content: [{ type: "text" as const, text: t }], isError: true });
const naglowek = (a: Artykul) =>
  [
    `# ${a.tytul}`,
    `id: ${a.id} | dział: ${a.dzial}${a.rodzic ? ` | podstrona artykułu: ${a.rodzic}` : ""}`,
    `oryginał: ${a.adresOryginalny} | plik w repozytorium: ${a.plik}`,
  ].join("\n");
const nieZnaleziono = (klucz: string) =>
  blad(`Nie znaleziono artykułu „${klucz}”. Użyj list_articles albo search, żeby znaleźć właściwe id.`);

// ---------------- narzędzia ----------------

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
    const lista = section
      ? archiwum.artykuly.filter((a) => a.dzial.toLowerCase() === section.toLowerCase())
      : archiwum.artykuly;
    if (!lista.length) return blad(`Brak działu „${section}”. Dostępne: ${archiwum.dzialy.join(", ")}`);
    const linie: string[] = [];
    let dzial = "";
    for (const a of lista) {
      if (a.dzial !== dzial) {
        dzial = a.dzial;
        linie.push(`\n## ${dzial}`);
      }
      const czesci = archiwum.czesci(a, ROZMIAR_CZESCI).length;
      const wciecie = a.rodzic ? "  " : "";
      linie.push(
        `${wciecie}- ${a.tytul} — id: ${a.id} (${Math.round(a.czysty.length / 1000)} tys. znaków${czesci > 1 ? `, ${czesci} części` : ""}${a.obrazy.length ? `, ${a.obrazy.length} obr.` : ""})`,
      );
    }
    return tekst(`Archiwum uleszka.net – ${lista.length} stron${linie.join("\n")}`);
  },
);

server.registerTool(
  "search",
  {
    title: "Szukaj w archiwum",
    description:
      "Full-text search across all articles (content is Polish – query in Polish for best results; diacritics optional, prefix and fuzzy matching). Returns matching articles ranked by relevance with quoted passages.",
    inputSchema: {
      query: z.string().min(1).describe("Słowa do wyszukania, np. „Atlantyda Platon” albo „wapn kosci”"),
      section: z.string().optional().describe("Ogranicz do działu"),
      limit: z.number().int().min(1).max(50).default(10).describe("Maksymalna liczba artykułów"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ query, section, limit }) => {
    const { tryb, lacznie, wyniki } = archiwum.szukaj(query, { dzial: section, limit });
    if (!wyniki.length) return tekst(`Brak wyników dla „${query}”.`);
    const bloki = wyniki.map(({ artykul: a, terminy }) => {
      const fr = archiwum.fragmenty(a, terminy, 160, 3);
      return [
        `## ${a.tytul}  (id: ${a.id}, dział: ${a.dzial})`,
        `trafień w tekście: ${fr.lacznie}`,
        ...fr.fragmenty.map((f) => `> ${f.tekst}`),
      ].join("\n");
    });
    return tekst(`Znaleziono ${lacznie} artykułów (dopasowanie: ${tryb}). Pokazuję ${wyniki.length}.\n\n${bloki.join("\n\n")}`);
  },
);

server.registerTool(
  "read_article",
  {
    title: "Czytaj artykuł",
    description: `Returns the full original text of an article as Markdown (verbatim). Long articles are split into parts of ~${ROZMIAR_CZESCI} characters – read all parts to see the whole text. Images appear as Markdown image links with repository paths (use get_image to view one); links to other articles appear as artykul:<id>.`,
    inputSchema: {
      id: z.string().describe("id artykułu (z list_articles/search) albo jego tytuł"),
      part: z.number().int().min(1).default(1).describe("Numer części (od 1)"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ id, part }) => {
    const a = archiwum.znajdz(id);
    if (!a) return nieZnaleziono(id);
    const czesci = archiwum.czesci(a, ROZMIAR_CZESCI);
    if (part > czesci.length) return blad(`Artykuł ma tylko ${czesci.length} części.`);
    const pod = archiwum.podstrony(a);
    const stopka = [
      czesci.length > 1
        ? part < czesci.length
          ? `[Część ${part} z ${czesci.length}. Dalej: read_article(id: "${a.id}", part: ${part + 1})]`
          : `[Koniec artykułu – część ${part} z ${czesci.length}.]`
        : "[Koniec artykułu.]",
      pod.length && part === czesci.length ? `Podstrony: ${pod.map((p) => `${p.tytul} (id: ${p.id})`).join("; ")}` : "",
    ]
      .filter(Boolean)
      .join("\n");
    return tekst(`${naglowek(a)}${czesci.length > 1 ? ` | część ${part} z ${czesci.length}` : ""}\n\n---\n\n${czesci[part - 1]}\n\n---\n${stopka}`);
  },
);

server.registerTool(
  "find_in_article",
  {
    title: "Szukaj w artykule",
    description:
      "Finds all places in one article where the given words occur and returns verbatim passages with context. Useful for long articles. Matching ignores case and Polish diacritics.",
    inputSchema: {
      id: z.string().describe("id albo tytuł artykułu"),
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
    if (!fr.lacznie) return tekst(`W artykule „${a.tytul}” nie ma frazy „${phrase}”.`);
    return tekst(
      `„${phrase}” w artykule „${a.tytul}” (id: ${a.id}): ${fr.lacznie} wystąpień, ${fr.wszystkichFragmentow} fragmentów, pokazuję ${fr.fragmenty.length}.\n\n` +
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
      "Returns an image from the archive. Pass a path shown in read_article (e.g. zrodlo/webacja/01potop/gilgam.gif), or an article id to list that article's images with their captions.",
    inputSchema: {
      path: z.string().optional().describe("Ścieżka obrazu z treści artykułu"),
      article_id: z.string().optional().describe("Zamiast ścieżki: id artykułu – zwraca listę jego obrazów"),
    },
    annotations: { readOnlyHint: true },
  },
  async ({ path, article_id }) => {
    if (article_id) {
      const a = archiwum.znajdz(article_id);
      if (!a) return nieZnaleziono(article_id);
      if (!a.obrazy.length) return tekst(`Artykuł „${a.tytul}” nie ma obrazów.`);
      return tekst(`Obrazy w artykule „${a.tytul}” (${a.obrazy.length}):\n` + a.obrazy.map((o, i) => `${i + 1}. ${o.sciezka}${o.opis ? ` — ${o.opis}` : ""}`).join("\n"));
    }
    if (!path) return blad("Podaj path albo article_id.");
    const pelna = resolve(KATALOG_GLOWNY, path);
    if (!pelna.startsWith(ZRODLO + sep) || !existsSync(pelna)) return blad(`Nie ma takiego obrazu w archiwum: ${path}`);
    const typ = TYPY[extname(pelna).toLowerCase()];
    if (!typ) return blad("To nie jest obsługiwany plik graficzny.");
    return { content: [{ type: "image" as const, data: readFileSync(pelna).toString("base64"), mimeType: typ }] };
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
    description: "Wierne streszczenie tez artykułu, a potem zestawienie każdej tezy z aktualną wiedzą.",
    argsSchema: { artykul: z.string().describe("id albo tytuł artykułu") },
  },
  ({ artykul }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Przeczytaj w całości artykuł „${artykul}” z archiwum uleszka.net (narzędzie read_article – wszystkie części).
1. Streść wiernie główne tezy autora, każdą z krótkim dosłownym cytatem.
2. Dla każdej tezy oceń ją w świetle dzisiejszej wiedzy (użyj wyszukiwarki internetowej, jeśli jest dostępna) i oznacz: potwierdzone / częściowo trafne / sporne / obalone / niesprawdzalne. Podaj źródła.
3. Wskaż, co od czasu napisania tekstu się zmieniło: nowe odkrycia, badania, wydarzenia.
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
1. Przeszukaj archiwum uleszka.net (search, potem find_in_article w trafionych artykułach) i zbierz wszystko, co autor pisał na ten temat – z dosłownymi cytatami i tytułami artykułów.
2. Poszukaj odzwierciedleń w obecnej wiedzy: aktualne badania, odkrycia, wydarzenia i publikacje (użyj wyszukiwarki internetowej, jeśli jest dostępna). Podaj źródła i daty.
3. Zestaw to w tabeli: teza autora | co wiemy dziś | ocena (potwierdzone / sporne / obalone / niesprawdzalne).
Wyraźnie oddzielaj zdanie autora od swojej oceny.`,
        },
      },
    ],
  }),
);

await server.connect(new StdioServerTransport());
