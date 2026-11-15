/**
 * Atlas Leszka – pobieranie danych o miejscach z otwartych źródeł:
 *  - Wikidata: identyfikator, współrzędne, opis, kategoria Commons, data powstania, artykuły w Wikipedii,
 *  - Wikipedia (pl, a gdy brak – en): krótki wstęp do sekcji „Co mówią dziś badania” (licencja CC BY-SA, z linkiem),
 *  - Wikimedia Commons: współczesne zdjęcia tylko na wolnych licencjach (CC0, domena publiczna, CC BY, CC BY-SA),
 *    z autorem, licencją i datą – obrazy nie są kopiowane do repozytorium, strona wczytuje je z serwerów Wikimedia.
 *
 * Wejście: atlas/miejsca.json (ręczna lista). Wyjście: atlas/dane.json (do przejrzenia i poprawienia ręcznie;
 * wpis z "wikidata" w miejsca.json ma pierwszeństwo przed wyszukiwaniem).
 *
 * Uruchomienie: npx tsx scripts/atlas-pobierz.ts [--od-nowa]
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";

type Miejsce = { nazwa: string; szukaj?: string; wikidata?: string; wsp?: [number, number]; rodzaje: string[]; aliasy: string[]; bez_zdjec?: boolean };
export type ZdjecieCommons = { plik: string; url: string; miniatura: string; duze: string; szer: number; wys: number; autor: string; licencja: string; licencja_url: string; data: string; strona: string };
export type DaneMiejsca = {
  wikidata: string; etykieta: string; opis: string; lat: number | null; lon: number | null;
  kategoria: string; powstanie: string; wiki: { jezyk: string; tytul: string; url: string; wstep: string } | null;
  zdjecia: ZdjecieCommons[];
  ponowione?: boolean; // pobierane ponownie z powodu małej liczby zdjęć
};

const UA = { "User-Agent": "uleszka-archiwum-atlas/1.0 (https://github.com/jokerwader/uleszka-archiwum)" };
const zrodlo: { miejsca: Miejsce[] } = JSON.parse(readFileSync("atlas/miejsca.json", "utf8"));
const PLIK = "atlas/dane.json";
const odNowa = process.argv.includes("--od-nowa");
const dane: Record<string, DaneMiejsca> = existsSync(PLIK) && !odNowa ? JSON.parse(readFileSync(PLIK, "utf8")) : {};

const czekaj = (ms: number) => new Promise((r) => setTimeout(r, ms));
async function json(url: string): Promise<any> {
  for (let proba = 0; proba < 4; proba++) {
    const r = await fetch(url, { headers: UA });
    if (r.status === 429 || r.status >= 500) { await czekaj(2000 * (proba + 1)); continue; }
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r.json();
  }
  throw new Error(`nie udało się: ${url}`);
}
const wd = (p: Record<string, string>) => json(`https://www.wikidata.org/w/api.php?${new URLSearchParams({ format: "json", ...p })}`);
const commons = (p: Record<string, string>) => json(`https://commons.wikimedia.org/w/api.php?${new URLSearchParams({ format: "json", ...p })}`);
const bezHtml = (s = "") => s.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();

// Commons podaje miniatury tylko w stałych szerokościach (m.in. 330, 500, 960, 1280, 1920 px):
// 500 px na karty i galerie, 1920 px (albo oryginał, gdy mniejszy) do powiększenia i do wideo
export const rozmiary = (thumburl: string, url: string, szer: number) => {
  const baza = thumburl.split("?")[0].replace(/^https:\/\/thumb\.wikimedia\.org\//, "https://upload.wikimedia.org/");
  return { miniatura: baza.replace(/\/\d+px-/, "/500px-"), duze: szer > 1920 ? baza.replace(/\/\d+px-/, "/1920px-") : url.split("?")[0] };
};

// licencje, które pozwalają pokazać zdjęcie z podaniem autora
const WOLNA = /^(cc0|public domain|pd|cc by(-sa)? \d(\.\d)?( [a-z]+)?|cc by(-sa)?)$/i;

async function znajdzQid(m: Miejsce): Promise<string | null> {
  if (m.wikidata) return m.wikidata;
  for (const jezyk of ["en", "pl"]) {
    const r = await wd({ action: "wbsearchentities", search: m.szukaj ?? m.nazwa, language: jezyk, uselang: "pl", limit: "1", type: "item" });
    if (r.search?.[0]) return r.search[0].id;
  }
  return null;
}

async function zdjeciaCommons(obraz: string | undefined, kategoria: string, ile = 8): Promise<ZdjecieCommons[]> {
  const tytuly = new Set<string>();
  if (obraz) tytuly.add(`File:${obraz}`);
  if (kategoria) {
    const r = await commons({ action: "query", list: "categorymembers", cmtitle: `Category:${kategoria}`, cmtype: "file", cmlimit: "60" });
    for (const c of r.query?.categorymembers ?? []) if (/\.jpe?g$/i.test(c.title)) tytuly.add(c.title);
    // mało plików w samej kategorii (zdjęcia bywają w podkategoriach): zajrzyj do kilku podkategorii
    if (tytuly.size < 12) {
      const pod = await commons({ action: "query", list: "categorymembers", cmtitle: `Category:${kategoria}`, cmtype: "subcat", cmlimit: "8" });
      for (const k of pod.query?.categorymembers ?? []) {
        const r2 = await commons({ action: "query", list: "categorymembers", cmtitle: k.title, cmtype: "file", cmlimit: "15" });
        for (const c of r2.query?.categorymembers ?? []) if (/\.jpe?g$/i.test(c.title)) tytuly.add(c.title);
        if (tytuly.size >= 40) break;
      }
    }
  }
  if (!tytuly.size) return [];
  const lista = [...tytuly].slice(0, 50);
  const r = await commons({ action: "query", titles: lista.join("|"), prop: "imageinfo", iiprop: "url|size|extmetadata", iiurlwidth: "640", iiextmetadatafilter: "Artist|LicenseShortName|LicenseUrl|DateTimeOriginal|DateTime" });
  const wyniki: ZdjecieCommons[] = [];
  for (const s of Object.values<any>(r.query?.pages ?? {})) {
    const ii = s.imageinfo?.[0];
    if (!ii) continue;
    const md = ii.extmetadata ?? {};
    const licencja = bezHtml(md.LicenseShortName?.value);
    if (!WOLNA.test(licencja)) continue;
    if (ii.width < 1200 || ii.height < 700) continue; // tylko zdjęcia nadające się do wideo 1080p
    const plik = s.title.replace(/^File:/, "");
    wyniki.push({
      plik, url: ii.url.split("?")[0], ...rozmiary(ii.thumburl, ii.url, ii.width), szer: ii.width, wys: ii.height,
      autor: bezHtml(md.Artist?.value) || "nieznany", licencja, licencja_url: md.LicenseUrl?.value ?? "",
      data: bezHtml(md.DateTimeOriginal?.value ?? md.DateTime?.value).slice(0, 10), strona: ii.descriptionurl,
    });
  }
  // najpierw zdjęcie główne z Wikidata, potem poziome i duże
  const glowne = obraz ? `${obraz}`.replace(/_/g, " ") : "";
  wyniki.sort((a, b) => Number(b.plik.replace(/_/g, " ") === glowne) - Number(a.plik.replace(/_/g, " ") === glowne) || Number(b.szer > b.wys) - Number(a.szer > a.wys) || b.szer * b.wys - a.szer * a.wys);
  return wyniki.slice(0, ile);
}

async function wstepWiki(sitelinks: any): Promise<DaneMiejsca["wiki"]> {
  for (const jezyk of ["pl", "en"]) {
    const tytul = sitelinks?.[`${jezyk}wiki`]?.title;
    if (!tytul) continue;
    const r = await json(`https://${jezyk}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(tytul.replace(/ /g, "_"))}`).catch(() => null);
    if (r?.extract) return { jezyk, tytul, url: r.content_urls?.desktop?.page ?? `https://${jezyk}.wikipedia.org/wiki/${encodeURIComponent(tytul)}`, wstep: r.extract };
  }
  return null;
}

let nowe = 0;
for (const m of zrodlo.miejsca) {
  const juz = dane[m.nazwa];
  // pobrane wcześniej i bez zmian: pomijamy (raz ponawiamy, gdy było mniej niż 4 zdjęcia)
  if (juz && !odNowa && (!m.wikidata || juz.wikidata === m.wikidata) && (juz.zdjecia.length >= 4 || m.bez_zdjec || juz.ponowione)) continue;
  const qid = await znajdzQid(m);
  if (!qid) { console.log(`✗ ${m.nazwa}: nie znaleziono w Wikidata`); continue; }
  const e = (await wd({ action: "wbgetentities", ids: qid, props: "labels|descriptions|claims|sitelinks", languages: "pl|en" })).entities[qid];
  const c = e.claims ?? {};
  const wartosc = (p: string) => c[p]?.[0]?.mainsnak?.datavalue?.value;
  const wsp = wartosc("P625");
  const kategoria = wartosc("P373") ?? "";
  const powstanie = wartosc("P571")?.time ?? "";
  const d: DaneMiejsca = {
    wikidata: qid,
    etykieta: e.labels?.pl?.value ?? e.labels?.en?.value ?? "",
    opis: e.descriptions?.pl?.value ?? e.descriptions?.en?.value ?? "",
    lat: m.wsp?.[0] ?? wsp?.latitude ?? null, lon: m.wsp?.[1] ?? wsp?.longitude ?? null,
    kategoria, powstanie,
    wiki: await wstepWiki(e.sitelinks),
    zdjecia: m.bez_zdjec ? [] : await zdjeciaCommons(wartosc("P18"), kategoria),
  };
  dane[m.nazwa] = juz && juz.wikidata === qid ? { ...d, ponowione: true } : d;
  nowe++;
  console.log(`${d.lat === null ? "⚠" : "✓"} ${m.nazwa} → ${qid} „${d.etykieta}” (${d.opis}) · ${d.zdjecia.length} zdj.${d.wiki ? ` · wiki ${d.wiki.jezyk}` : ""}`);
  writeFileSync(PLIK, JSON.stringify(dane, null, 1) + "\n");
  await czekaj(150);
}
console.log(`Gotowe: ${nowe} pobranych, razem ${Object.keys(dane).length} miejsc w ${PLIK}.`);
