/**
 * Sprawdza odnośniki wewnętrzne strony (docs/): czy każdy prowadzi do istniejącego pliku i istniejącej kotwicy (#…).
 * Uruchomienie: npx tsx scripts/sprawdz-linki.ts   (kod wyjścia 1, gdy są martwe odnośniki)
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, normalize } from "node:path";

const KORZEN = "docs";
const pliki = (readdirSync(KORZEN, { recursive: true }) as string[])
  .map((p) => p.split(String.fromCharCode(92)).join("/"))
  .filter((p) => p.endsWith(".html"));
const kotwice = new Map<string, Set<string>>();
const html = (p: string) => readFileSync(join(KORZEN, p), "utf8");
const idWPliku = (p: string) => {
  if (!kotwice.has(p)) kotwice.set(p, new Set([...html(p).matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  return kotwice.get(p)!;
};

const martwe = new Map<string, { cel: string; skad: Set<string> }>();
for (const p of pliki) {
  for (const m of html(p).matchAll(/\shref="([^"]+)"/g)) {
    let href = m[1].replace(/&amp;/g, "&");
    // adresy własnej domeny traktujemy jak wewnętrzne – muszą istnieć na stronie (docs/)
    const wlasny = href.match(/^https?:\/\/(?:www\.)?uleszka\.net(\/.*)?$/i);
    if (wlasny) href = (wlasny[1] ?? "/").replace(/^\//, "/");
    if (/^(https?:|mailto:|microsoft-edge:|data:|javascript:)/.test(href)) continue;
    if (href.startsWith("/")) href = "../".repeat(p.split("/").length - 1) + href.slice(1);
    const [sciezka, kotwica] = href.split("#");
    let cel = sciezka ? normalize(join(dirname(p), sciezka.split("?")[0])).split(String.fromCharCode(92)).join("/") : p;
    if (cel.endsWith("/") || cel === "." || !/\.[a-z0-9]+$/i.test(cel)) cel = (cel === "." ? "" : cel.replace(/\/?$/, "/")) + "index.html";
    cel = cel.replace(/^\/+/, "");
    const istnieje = existsSync(join(KORZEN, cel));
    const kotwicaOk = !kotwica || !istnieje || !cel.endsWith(".html") || idWPliku(cel).has(decodeURIComponent(kotwica));
    if (!istnieje || !kotwicaOk) {
      const klucz = istnieje ? `${cel}#${kotwica}` : cel;
      if (!martwe.has(klucz)) martwe.set(klucz, { cel: klucz, skad: new Set() });
      martwe.get(klucz)!.skad.add(p);
    }
  }
}
for (const { cel, skad } of martwe.values()) console.log(`MARTWY ${cel}  ← ${[...skad].slice(0, 3).join(", ")}${skad.size > 3 ? ` (+${skad.size - 3})` : ""}`);
console.log(`Sprawdzono ${pliki.length} stron. Martwych odnośników: ${martwe.size}.`);
if (martwe.size) process.exitCode = 1;
