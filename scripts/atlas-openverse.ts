/**
 * Atlas Leszka – dodatkowe zdjęcia z Openverse (openverse.org: otwarta wyszukiwarka zdjęć na wolnych licencjach,
 * głównie Flickr, muzea i archiwa). Tylko licencje pozwalające na każde użycie z podaniem autora: CC BY, CC BY-SA,
 * CC0 i domena publiczna (bez NC i ND). Zdjęcia z Wikimedia są pomijane – te pobiera scripts/atlas-pobierz.ts.
 * Te same filtry co dla Commons (scripts/lib/filtry-zdjec.ts) i lista odrzuconych (atlas/odrzucone.json).
 *
 * Bez klucza Openverse pozwala na 20 zapytań na minutę i 200 na dobę: jedno zapytanie na miejsce, przerwy po 3,5 s;
 * miejsca już pobrane są pomijane, więc po przekroczeniu limitu wystarczy uruchomić skrypt następnego dnia.
 * Wynik: atlas/openverse.json (nazwa miejsca → zdjęcia w tym samym formacie co w atlas/dane.json, z polem „serwis”).
 *
 * Uruchomienie: npx tsx scripts/atlas-openverse.ts [--od-nowa] [--tylko=<nazwa miejsca>]
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import type { ZdjecieCommons } from "./lib/atlas.js";
import { DETAL, PRZYRODA, odrzucZdjecie } from "./lib/filtry-zdjec.js";
const TAGI_LUDZIE = /\b(people|portrait|selfie|woman|women|girl|boy|family|friends|group|crowd|tourists?|kids?|children)\b/i;

const PLIK = "atlas/openverse.json";
const UA = { "User-Agent": "uleszka-archiwum-atlas/1.0 (https://github.com/jokerwader/uleszka-archiwum)" };
const czekaj = (ms: number) => new Promise((r) => setTimeout(r, ms));
const zrodlo: { miejsca: { nazwa: string; aliasy: string[] }[] } = JSON.parse(readFileSync("atlas/miejsca.json", "utf8"));
const dane: Record<string, { kategoria: string; etykieta: string; zdjecia: unknown[] }> = JSON.parse(readFileSync("atlas/dane.json", "utf8"));
const odNowa = process.argv.includes("--od-nowa");
const tylko = process.argv.find((a) => a.startsWith("--tylko="))?.slice(8);
const wynik: Record<string, ZdjecieCommons[]> = existsSync(PLIK) && !odNowa ? JSON.parse(readFileSync(PLIK, "utf8")) : {};
const ODRZUCONE: Record<string, string> = existsSync("atlas/odrzucone.json") ? JSON.parse(readFileSync("atlas/odrzucone.json", "utf8")) : {};
const ascii = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l").replace(/Ł/g, "L").replace(/\s*\(.*?\)/g, "").trim();
// tytuły zdjęć ludzi („Woman of Sacsayhuaman”, „me at the pyramids”)
const OSOBY = /\b(woman|women|man|men|girl|girls|boy|boys|child|children|kid|kids|lady|ladies|me|my|myself|mom|dad|wife|husband|friend|friends|portrait|selfie|smile)\b/i;
const NAZWA_SERWISU: Record<string, string> = { flickr: "Flickr", smithsonian: "Smithsonian", met: "Metropolitan Museum", europeana: "Europeana", nappy: "Nappy", rawpixel: "rawpixel", stocksnap: "StockSnap", wordpress: "WordPress Photo Directory" };
const licencja = (r: any) => (r.license === "cc0" ? "CC0" : r.license === "pdm" ? "Public domain" : `CC ${String(r.license).toUpperCase()} ${r.license_version ?? ""}`.trim());

async function szukaj(q: string): Promise<any[]> {
  const url = `https://api.openverse.org/v1/images/?${new URLSearchParams({ q, license: "by,by-sa,cc0,pdm", category: "photograph", page_size: "20", mature: "false" })}`;
  for (let proba = 0; proba < 3; proba++) {
    const r = await fetch(url, { headers: UA });
    if (r.status === 429) {
      const czas = Number(r.headers.get("retry-after") ?? 60);
      if (czas > 120) throw new Error("limit dobowy Openverse – uruchom ponownie jutro");
      await czekaj(czas * 1000);
      continue;
    }
    if (!r.ok) throw new Error(`Openverse ${r.status}`);
    return (await r.json()).results ?? [];
  }
  throw new Error("Openverse nie odpowiada");
}

const lista = zrodlo.miejsca.filter((m) => dane[m.nazwa] && (!tylko || m.nazwa === tylko) && (odNowa || tylko || !wynik[m.nazwa]));
let n = 0;
for (const m of lista) {
  const d = dane[m.nazwa];
  // nazwa do szukania: kategoria Commons (zwykle angielska nazwa miejsca) bez polskich znaków
  const q = ascii(d.kategoria || d.etykieta || m.nazwa);
  let wyniki: any[];
  // najpierw nazwa z polskimi znakami („Ślęża”), gdy pusto – bez nich („Sleza”)
  const zPolskimi = (d.kategoria || d.etykieta || m.nazwa).replace(/\s*\(.*?\)/g, "").trim();
  try {
    wyniki = await szukaj(zPolskimi);
    if (!wyniki.length && q !== zPolskimi) { await czekaj(3500); wyniki = await szukaj(q); }
  } catch (e) { console.log(`✗ ${m.nazwa}: ${(e as Error).message}`); break; }
  const zdjecia: ZdjecieCommons[] = [];
  const widziane = new Set<string>();
  for (const r of wyniki) {
    if (r.source === "wikimedia" || !r.url) continue;
    const plik = `openverse:${r.id}`;
    if (ODRZUCONE[plik] || (r.width && r.width < 900)) continue;
    const tytul = String(r.title ?? "");
    const tagi = (r.tags ?? []).map((t: any) => t.name).join(" ");
    // tytuł sprawdzamy pełnym filtrem; tagi Flickra („travel”, „vacation”) tylko pod kątem ludzi i przyrody
    if (OSOBY.test(tytul) || odrzucZdjecie(tytul) || TAGI_LUDZIE.test(tagi) || PRZYRODA.test(tagi)) continue;
    // nazwa miejsca musi być w tytule albo tagach (bez tego trafiają zdjęcia z sąsiednich miejsc)
    const rdzen = ascii(zPolskimi).toLowerCase().split(/\s+/).filter((w) => w.length >= 4).map((w) => w.slice(0, 6));
    if (rdzen.length && !rdzen.some((w) => ascii(`${tytul} ${tagi}`).toLowerCase().includes(w))) continue;
    // najwyżej 2 zdjęcia od jednego autora
    const autor = String(r.creator ?? "");
    const ileAutora = [...widziane].filter((x) => x.startsWith(`${autor}#`)).length;
    if (ileAutora >= 2 || widziane.has(`${autor}|${tytul}`) || widziane.has(r.url)) continue; // Openverse bywa zdublowany
    widziane.add(`${autor}|${tytul}`);
    widziane.add(r.url);
    widziane.add(`${autor}#${ileAutora}`);
    const duze = r.url as string;
    // Flickr: _b = 1024 px, _z = 640 px (miniatura)
    const miniatura = /staticflickr\.com/.test(duze) ? duze.replace(/(_[a-z])?\.jpg$/, "_z.jpg") : r.thumbnail ?? duze;
    zdjecia.push({
      plik, url: duze, miniatura, duze, szer: r.width ?? 0, wys: r.height ?? 0,
      autor: String(r.creator ?? "nieznany").slice(0, 120), licencja: licencja(r), licencja_url: r.license_url ?? "",
      data: "", strona: r.foreign_landing_url ?? duze, opis: tytul.length > 12 ? tytul : "",
      detal: DETAL.test(`${tytul} ${tagi}`), serwis: NAZWA_SERWISU[r.source] ?? r.source,
    } as ZdjecieCommons);
    if (zdjecia.length >= 8) break;
  }
  wynik[m.nazwa] = zdjecia;
  writeFileSync(PLIK, JSON.stringify(wynik, null, 1) + "\n");
  console.log(`✓ ${m.nazwa} („${q}”): ${zdjecia.length} zdj. z ${wyniki.length} wyników`);
  n++;
  await czekaj(3500);
}
console.log(`Gotowe: ${n} miejsc; razem ${Object.values(wynik).flat().length} zdjęć z Openverse w ${PLIK}.`);
