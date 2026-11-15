/**
 * Arkusze do przeglądu zdjęć atlasu: dla każdego miejsca jedna siatka ponumerowanych miniatur zdjęć z Commons
 * (atlas/dane.json). Na tej podstawie człowiek albo AI wskazuje zdjęcia do odrzucenia (ludzie pozujący do aparatu,
 * wycieczki, logo, reklamy, zdjęcia niezwiązane z budowlą), a scripts/atlas-odrzuc.ts dopisuje je do atlas/odrzucone.json.
 *
 * Uruchomienie: npx tsx scripts/atlas-arkusze.ts <folder wyjściowy>   (folder poza repozytorium, np. tymczasowy)
 * Wynik: <folder>/<id miejsca>.jpg i <folder>/spis.json (id → lista plików w kolejności numerów na arkuszu).
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import sharp from "sharp";
import { slug } from "./lib/atlas.js";

const wyj = process.argv[2];
if (!wyj) throw new Error("Użycie: npx tsx scripts/atlas-arkusze.ts <folder wyjściowy>");
mkdirSync(join(wyj, "mini"), { recursive: true });
const dane: Record<string, { zdjecia: { plik: string; miniatura: string }[] }> = JSON.parse(readFileSync("atlas/dane.json", "utf8"));
// razem ze zdjęciami z Openverse (scripts/atlas-openverse.ts) – w tej samej kolejności co na stronie
const openverse: Record<string, { plik: string; miniatura: string }[]> = existsSync("atlas/openverse.json") ? JSON.parse(readFileSync("atlas/openverse.json", "utf8")) : {};
for (const [n, z] of Object.entries(openverse)) if (dane[n]) dane[n].zdjecia = [...dane[n].zdjecia, ...z];
const UA = { "User-Agent": "uleszka-archiwum-atlas/1.0 (https://github.com/jokerwader/uleszka-archiwum)" };
const czekaj = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function miniatura(url: string, plik: string): Promise<Buffer | null> {
  const lok = join(wyj, "mini", plik.replace(/[^\w.-]+/g, "_").slice(-100));
  if (existsSync(lok)) return readFileSync(lok);
  for (let proba = 0; proba < 5; proba++) {
    const r = await fetch(url.replace(/\/500px-/, "/330px-"), { headers: UA }).catch(() => null);
    if (r?.ok) { const b = Buffer.from(await r.arrayBuffer()); writeFileSync(lok, b); await czekaj(120); return b; }
    if (r && r.status !== 429 && r.status < 500) return null;
    await czekaj(3000 * (proba + 1));
  }
  return null;
}

const K = 5, SZ = 300, WY = 225, PAS = 34;
const spis: Record<string, string[]> = {};
for (const [nazwa, d] of Object.entries(dane)) {
  if (!d.zdjecia.length) continue;
  const id = slug(nazwa);
  const kafle: sharp.OverlayOptions[] = [];
  const pliki: string[] = [];
  for (const [i, z] of d.zdjecia.entries()) {
    const b = await miniatura(z.miniatura, z.plik);
    const x = (i % K) * SZ, y = Math.floor(i / K) * (WY + PAS);
    pliki.push(z.plik);
    if (b) kafle.push({ input: await sharp(b).resize(SZ - 6, WY, { fit: "cover" }).toBuffer(), left: x + 3, top: y + PAS });
    kafle.push({ input: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${SZ}" height="${PAS}"><rect width="${SZ}" height="${PAS}" fill="#111"/><text x="8" y="25" font-family="Arial" font-weight="700" font-size="22" fill="#ffd84d">${i + 1}</text></svg>`), left: x, top: y });
  }
  const wiersze = Math.ceil(d.zdjecia.length / K);
  await sharp({ create: { width: K * SZ, height: wiersze * (WY + PAS), channels: 3, background: "#222" } }).composite(kafle).jpeg({ quality: 80 }).toFile(join(wyj, `${id}.jpg`));
  spis[id] = pliki;
  console.log(`${id}: ${pliki.length}`);
}
writeFileSync(join(wyj, "spis.json"), JSON.stringify(spis, null, 1));
console.log(`Gotowe: ${Object.keys(spis).length} arkuszy w ${wyj}`);
