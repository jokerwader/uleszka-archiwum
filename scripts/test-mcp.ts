/**
 * Test serwera MCP: uruchamia dist/server.js tak, jak robi to klient AI, i wywołuje wszystkie narzędzia.
 * Uruchomienie: npm test  (po npm run build)
 */
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";

const HTTP = process.argv.includes("--http");
// --url <adres>: testuje działający już serwer w internecie, np. --url https://uleszka-mcp-production.up.railway.app
const URL_ZDALNY = process.argv.includes("--url") ? process.argv[process.argv.indexOf("--url") + 1] : undefined;
const client = new Client({ name: "test", version: "1.0.0" });
let proces: ChildProcess | undefined;
if (URL_ZDALNY) {
  const baza = URL_ZDALNY.replace(/\/(mcp)?$/, "");
  assert.match(await fetch(`${baza}/health`).then((r) => r.text()), /Serwer MCP archiwum uleszka\.net/);
  await client.connect(new StreamableHTTPClientTransport(new URL(`${baza}/mcp`)));
} else if (HTTP) {
  // tryb internetowy: uruchamiamy serwer na porcie i łączymy się przez adres URL, jak ChatGPT / Claude.ai
  const PORT = 3917;
  proces = spawn(process.execPath, ["dist/server.js"], { env: { ...process.env, PORT: String(PORT) }, stdio: ["ignore", "ignore", "pipe"] });
  await new Promise<void>((ok, blad) => {
    proces!.stderr!.on("data", (d) => String(d).includes("nasłuchuje") && ok());
    proces!.on("exit", (c) => blad(new Error(`serwer zakończył się kodem ${c}`)));
  });
  const strona = await fetch(`http://localhost:${PORT}/`).then((r) => r.text());
  assert.match(strona, /Serwer MCP archiwum uleszka\.net/);
  await client.connect(new StreamableHTTPClientTransport(new URL(`http://localhost:${PORT}/mcp`)));
} else {
  await client.connect(new StdioClientTransport({ command: process.execPath, args: ["dist/server.js"] }));
}
console.log(`Tryb: ${URL_ZDALNY ? `serwer zdalny ${URL_ZDALNY}` : HTTP ? "HTTP (adres URL)" : "lokalny (stdio)"}`);

type Wynik = { content: { type: string; text?: string; data?: string; mimeType?: string }[]; isError?: boolean };
const wywolaj = async (name: string, args: Record<string, unknown>) => (await client.callTool({ name, arguments: args })) as Wynik;
const txt = (w: Wynik) => w.content.map((c) => c.text ?? "").join("\n");
let ok = 0;
const sprawdz = async (opis: string, fn: () => Promise<void>) => {
  await fn();
  ok++;
  console.log(`✔ ${opis}`);
};

await sprawdz("serwer podaje instrukcje i 11 narzędzi", async () => {
  assert.match(client.getInstructions() ?? "", /uleszka\.net/);
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name).sort(), [
    "find_in_article",
    "get_article_notes",
    "get_image",
    "list_articles",
    "list_books",
    "list_library",
    "read_article",
    "read_book",
    "related_articles",
    "search",
    "search_by_meaning",
  ]);
});

await sprawdz("search_by_meaning: „katastrofy z kosmosu” znajduje teksty o kometach/Tiamat bez tych słów w pytaniu", async () => {
  const t = txt(await wywolaj("search_by_meaning", { query: "katastrofy z kosmosu", limit: 10 }));
  assert.match(t, /podobieństwo/);
  assert.match(t, /komet|Tiamat|meteor|planetoid|asteroid/i);
});

if (!existsSync("dane/wektory/biblioteka.bin")) console.log("– pominięto test wyszukiwania po znaczeniu w bibliotece (brak dane/wektory/biblioteka.bin)");
else await sprawdz("search_by_meaning działa w bibliotece („zagłada wyspy w jeden dzień i jedną noc” → Platon)", async () => {
  const t = txt(await wywolaj("search_by_meaning", { query: "zagłada wyspy na oceanie w ciągu jednego dnia i nocy", scope: "biblioteka", limit: 5 }));
  assert.match(t, /platon-(timajos|kritias)/);
});

await sprawdz("get_article_notes zwraca streszczenie i tezy z cytatami", async () => {
  const t = txt(await wywolaj("get_article_notes", { id: "01potop/potop" }));
  assert.match(t, /Streszczenie/);
  assert.match(t, /Tezy autora/);
  assert.match(t, /> „/);
});

await sprawdz("related_articles podaje artykuły powiązane", async () => {
  const t = txt(await wywolaj("related_articles", { id: "11atlantyda/atlant" }));
  assert.match(t, /Najbliższe znaczeniowo/);
  assert.match(t, /id: /);
});

await sprawdz("list_books i biblioteka: Platon dostępny, Däniken chroniony", async () => {
  const t = txt(await wywolaj("list_books", { query: "Platon" }));
  assert.match(t, /Timajos/);
  assert.match(t, /platon-kritias/);
  const d = txt(await wywolaj("list_books", { query: "Däniken" }));
  assert.match(d, /Rydwany bogów/);
  const lib = txt(await wywolaj("list_library", {}));
  assert.match(lib, /id: ksiega-henocha/);
});

await sprawdz("read_book, search w bibliotece i find_in_article na książce", async () => {
  const k = txt(await wywolaj("read_book", { id: "platon-kritias" }));
  assert.match(k, /część 1 z/);
  assert.match(k, /Witwicki/);
  const s = txt(await wywolaj("search", { query: "Atlantyda", scope: "biblioteka", limit: 5 }));
  assert.match(s, /platon-(timajos|kritias)/);
  const f = txt(await wywolaj("find_in_article", { id: "ksiega-henocha", phrase: "giants" }));
  assert.match(f, /wystąpień/);
});

await sprawdz("oryginały: read_book z numeracją (Herodot 2.148, Księga Rodzaju 6:4), powiązanie z przekładem, szukanie po grecku bez akcentów", async () => {
  const lib = txt(await wywolaj("list_library", {}));
  assert.match(lib, /Teksty w językach oryginału/);
  assert.match(lib, /id: mahabharata-sa/);
  const h = txt(await wywolaj("read_book", { id: "herodot-dzieje-grc", ref: "2.148" }));
  assert.match(h, /\[2\.148\.1\]/);
  assert.match(h, /λαβύριν/);
  const g = txt(await wywolaj("read_book", { id: "ksiega-rodzaju-he", ref: "6:4" }));
  assert.match(g, /^\[6:4\] [א-ת]/m); // werset o Nefilim, tekst hebrajski
  const n = txt(await wywolaj("search", { query: "נפלים", scope: "biblioteka", limit: 5 })); // bez samogłosek
  assert.match(n, /ksiega-rodzaju-he/);
  const p = txt(await wywolaj("read_book", { id: "platon-kritias" }));
  assert.match(p, /tekst w języku oryginału: platon-kritias-grc/);
  const s = txt(await wywolaj("search", { query: "Ατλαντις", scope: "biblioteka", limit: 5 }));
  assert.match(s, /platon-(timajos|kritias)-grc/);
  const zly = await wywolaj("read_book", { id: "herodot-dzieje-grc", ref: "99.99" });
  assert.equal(zly.isError, true);
});

await sprawdz("list_articles zwraca 148 stron i wszystkie działy", async () => {
  const t = txt(await wywolaj("list_articles", {}));
  assert.match(t, /148 stron/);
  for (const d of ["Cywilizacja Bogów", "Zapomniana medycyna", "Różności", "Pamiętam"]) assert.ok(t.includes(`## ${d}`), d);
  const m = txt(await wywolaj("list_articles", { section: "Zapomniana medycyna" }));
  assert.match(m, /47 stron/);
});

await sprawdz("search znajduje Atlantydę po słowach „Atlantyda Platon”", async () => {
  const t = txt(await wywolaj("search", { query: "Atlantyda Platon", limit: 5 }));
  assert.match(t, /id: 11atlantyda\/atlant/);
});

await sprawdz("search działa bez polskich znaków („zrodla pisane starozytni”)", async () => {
  const t = txt(await wywolaj("search", { query: "zrodla pisane starozytni", limit: 5 }));
  assert.match(t, /id: 01potop\/potop/);
  assert.match(t, /Źródła pisane/);
});

await sprawdz("read_article dzieli długi artykuł na części i podaje następną", async () => {
  const t1 = txt(await wywolaj("read_article", { id: "Bogowie atomowych wojen" }));
  assert.match(t1, /część 1 z \d+/);
  assert.match(t1, /part: 2/);
  const t2 = txt(await wywolaj("read_article", { id: "atomwoj/bogatom01", part: 2 }));
  assert.match(t2, /część 2 z/);
});

await sprawdz("read_article zwraca tekst słowo w słowo", async () => {
  const t = txt(await wywolaj("read_article", { id: "01potop/potop" }));
  assert.ok(t.includes("Z wieścią o Potopie mamy do czynienia już od najmłodszych lat."));
  assert.ok(t.includes("zrodlo/webacja/01potop/gilgam.gif"));
  assert.ok(t.includes("[opis AI:"), "opisy zdjęć przy obrazach");
});

await sprawdz("find_in_article pokazuje fragmenty z kontekstem", async () => {
  const t = txt(await wywolaj("find_in_article", { id: "01potop/potop", phrase: "Deukalion" }));
  assert.match(t, /wystąpień/);
  assert.match(t, /Pyrra/);
});

await sprawdz("get_image zwraca listę obrazów i sam obraz", async () => {
  const lista = txt(await wywolaj("get_image", { article_id: "01potop/potop" }));
  assert.match(lista, /gilgam\.gif/);
  const obraz = await wywolaj("get_image", { path: "zrodlo/webacja/01potop/gilgam.gif" });
  assert.equal(obraz.content[0].type, "image");
  assert.equal(obraz.content[0].mimeType, "image/gif");
  assert.match(String(obraz.content[1]?.text), /Opis AI/);
  const zly = await wywolaj("get_image", { path: "../package.json" });
  assert.equal(zly.isError, true);
});

await sprawdz("nieznany artykuł daje czytelny błąd", async () => {
  const w = await wywolaj("read_article", { id: "nie-ma-takiego-xyz" });
  assert.equal(w.isError, true);
});

await sprawdz("prompty i zasób katalogu są dostępne", async () => {
  const { prompts } = await client.listPrompts();
  assert.deepEqual(prompts.map((p) => p.name).sort(), ["omow_artykul", "sprawdz_zrodlo", "szukaj_odzwierciedlen"]);
  const p = await client.getPrompt({ name: "omow_artykul", arguments: { artykul: "Potop" } });
  assert.match(JSON.stringify(p.messages), /read_article/);
  const r = await client.readResource({ uri: "uleszka://katalog" });
  assert.match(String(r.contents[0].text), /Katalog archiwum/);
});

await client.close();
proces?.kill();
console.log(`\nWszystkie testy przeszły (${ok}).`);
