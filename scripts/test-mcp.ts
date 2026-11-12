/**
 * Test serwera MCP: uruchamia dist/server.js tak, jak robi to klient AI, i wywołuje wszystkie narzędzia.
 * Uruchomienie: npm test  (po npm run build)
 */
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { spawn, type ChildProcess } from "node:child_process";

const HTTP = process.argv.includes("--http");
const client = new Client({ name: "test", version: "1.0.0" });
let proces: ChildProcess | undefined;
if (HTTP) {
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
console.log(`Tryb: ${HTTP ? "HTTP (adres URL)" : "lokalny (stdio)"}`);

type Wynik = { content: { type: string; text?: string; data?: string; mimeType?: string }[]; isError?: boolean };
const wywolaj = async (name: string, args: Record<string, unknown>) => (await client.callTool({ name, arguments: args })) as Wynik;
const txt = (w: Wynik) => w.content.map((c) => c.text ?? "").join("\n");
let ok = 0;
const sprawdz = async (opis: string, fn: () => Promise<void>) => {
  await fn();
  ok++;
  console.log(`✔ ${opis}`);
};

await sprawdz("serwer podaje instrukcje i 5 narzędzi", async () => {
  assert.match(client.getInstructions() ?? "", /uleszka\.net/);
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name).sort(), ["find_in_article", "get_image", "list_articles", "read_article", "search"]);
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
  const zly = await wywolaj("get_image", { path: "../package.json" });
  assert.equal(zly.isError, true);
});

await sprawdz("nieznany artykuł daje czytelny błąd", async () => {
  const w = await wywolaj("read_article", { id: "nie-ma-takiego-xyz" });
  assert.equal(w.isError, true);
});

await sprawdz("prompty i zasób katalogu są dostępne", async () => {
  const { prompts } = await client.listPrompts();
  assert.deepEqual(prompts.map((p) => p.name).sort(), ["omow_artykul", "szukaj_odzwierciedlen"]);
  const p = await client.getPrompt({ name: "omow_artykul", arguments: { artykul: "Potop" } });
  assert.match(JSON.stringify(p.messages), /read_article/);
  const r = await client.readResource({ uri: "uleszka://katalog" });
  assert.match(String(r.contents[0].text), /Katalog archiwum/);
});

await client.close();
proces?.kill();
console.log(`\nWszystkie testy przeszły (${ok}).`);
