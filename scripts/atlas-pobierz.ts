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
export type ZdjecieCommons = {
  plik: string; url: string; miniatura: string; duze: string; szer: number; wys: number; autor: string; licencja: string; licencja_url: string; data: string; strona: string;
  detal?: boolean; // zbliżenie konstrukcji (mur, blok, relief, napis, wnętrze…)
  opis?: string; // opis zdjęcia z Commons (co widać)
  ocena?: string; // wyróżnione / jakościowe / wartościowe – ocena społeczności Commons
};
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
const ENCJE: Record<string, string> = { "&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#39;": "'", "&#039;": "'", "&lt;": "<", "&gt;": ">" };
const bezHtml = (s = "") => s.replace(/<[^>]+>/g, "").replace(/&(nbsp|amp|quot|#0?39|lt|gt);/g, (e) => ENCJE[e] ?? e).replace(/\s+/g, " ").trim();

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

import { DETAL, KONSTRUKCJA, LUDZIE_KAT, LUDZIE_TXT, PRZYRODA, RZEZBA, ZBEDNE } from "./lib/filtry-zdjec.js";
const OCENY: [RegExp, string, number][] = [[/featured|poty|potd/i, "wyróżnione", 30], [/quality/i, "jakościowe", 20], [/valued/i, "wartościowe", 15]];

// zdjęcia odrzucone przy przeglądzie (ludzie pozujący, logo, reklamy…) albo zgłoszone – nie wracają przy kolejnym pobieraniu
const ODRZUCONE: Record<string, string> = existsSync("atlas/odrzucone.json") ? JSON.parse(readFileSync("atlas/odrzucone.json", "utf8")) : {};

async function zdjeciaCommons(obraz: string | undefined, kategoria: string, ile = 20): Promise<ZdjecieCommons[]> {
  const zrodlo = new Map<string, boolean>(); // plik → z podkategorii o detalach
  const dodaj = (t: string, detal: boolean) => { if (/\.jpe?g$/i.test(t) && !ZBEDNE.test(t.replace(/_/g, " "))) zrodlo.set(t, zrodlo.get(t) || detal); };
  if (obraz) dodaj(`File:${obraz}`, false);
  if (kategoria) {
    const r = await commons({ action: "query", list: "categorymembers", cmtitle: `Category:${kategoria}`, cmtype: "file", cmlimit: "100" });
    for (const c of r.query?.categorymembers ?? []) dodaj(c.title, false);
    const pod = ((await commons({ action: "query", list: "categorymembers", cmtitle: `Category:${kategoria}`, cmtype: "subcat", cmlimit: "60" })).query?.categorymembers ?? [])
      .map((k: any) => k.title as string).filter((t: string) => !ZBEDNE.test(t));
    const detale = pod.filter((t: string) => DETAL.test(t)).slice(0, 6);
    const inne = pod.filter((t: string) => !DETAL.test(t)).slice(0, zrodlo.size < 20 ? 4 : 1);
    for (const k of [...detale, ...inne]) {
      const r2 = await commons({ action: "query", list: "categorymembers", cmtitle: k, cmtype: "file", cmlimit: "40" });
      for (const c of r2.query?.categorymembers ?? []) dodaj(c.title, detale.includes(k));
    }
    // celowane szukanie w całym drzewie kategorii: rzeźby, mury, wykopaliska, tunele i wnętrza – to są zbliżenia konstrukcji
    for (const fraza of [
      "sculpture OR statue OR relief OR carving OR petroglyph OR stela",
      "wall OR masonry OR blocks OR megalith OR stones OR rampart",
      "excavation OR archaeological OR ruins OR remains",
      "tunnel OR chamber OR interior OR cave OR crypt OR inscription",
    ]) {
      const r4 = await commons({ action: "query", list: "search", srnamespace: "6", srlimit: "15", srsearch: `deepcat:"${kategoria}" ${fraza}` }).catch(() => null);
      for (const c of r4?.query?.search ?? []) dodaj(c.title, true);
    }
    // zwykłe szukanie po nazwie bez polskich znaków („Sleza sculpture”) – znajduje rzeźby i detale opisane poza drzewem kategorii
    const nazwaAscii = kategoria.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l").replace(/Ł/g, "L").replace(/\s*\(.*?\)/g, "");
    for (const slowo of ["sculpture", "statue", "relief", "wall", "ruins", "excavation", "tunnel", "inscription"]) {
      const r5 = await commons({ action: "query", list: "search", srnamespace: "6", srlimit: "8", srsearch: `${nazwaAscii} ${slowo}` }).catch(() => null);
      for (const c of r5?.query?.search ?? []) dodaj(c.title, true);
    }
    // najlepsze zdjęcia z całego drzewa kategorii: ocenione przez społeczność (Quality / Featured / Valued images)
    for (const ocena of ["Quality images", "Featured pictures on Wikimedia Commons", "Valued images sorted by promotion date"]) {
      const r3 = await commons({ action: "query", list: "search", srnamespace: "6", srlimit: "30", srsearch: `deepcat:"${kategoria}" incategory:"${ocena}"` }).catch(() => null);
      for (const c of r3?.query?.search ?? []) dodaj(c.title, false);
    }
  }
  if (!zrodlo.size) return [];
  const wyniki: (ZdjecieCommons & { punkty: number })[] = [];
  const tytuly = [...zrodlo.keys()].slice(0, 150);
  for (let i = 0; i < tytuly.length; i += 50) {
    const r = await commons({ action: "query", titles: tytuly.slice(i, i + 50).join("|"), prop: "imageinfo", iiprop: "url|size|extmetadata", iiurlwidth: "640",
      iiextmetadatafilter: "Artist|LicenseShortName|LicenseUrl|DateTimeOriginal|DateTime|ImageDescription|Assessments|Categories" });
    for (const s of Object.values<any>(r.query?.pages ?? {})) {
      const ii = s.imageinfo?.[0];
      if (!ii) continue;
      const md = ii.extmetadata ?? {};
      const licencja = bezHtml(md.LicenseShortName?.value);
      if (!WOLNA.test(licencja)) continue;
      if (ii.width < 1200 || ii.height < 700) continue; // tylko zdjęcia nadające się do wideo 1080p
      const plik = s.title.replace(/^File:/, "");
      if (ODRZUCONE[plik]) continue;
      const opis = bezHtml(md.ImageDescription?.value).replace(/^(english|polski|deutsch|español|français):\s*/i, "");
      const kategorie = String(md.Categories?.value ?? "");
      const calosc = `${plik.replace(/[_-]/g, " ")} ${opis} ${kategorie.replace(/\|/g, " ")}`;
      const rzezba = RZEZBA.test(calosc); // „Girl with fish” to rzeźba, a nie zdjęcie ludzi
      if (!rzezba && (LUDZIE_KAT.test(kategorie.replace(/\|/g, " ")) || LUDZIE_TXT.test(`${plik.replace(/[_-]/g, " ")} ${opis}`))) continue;
      if (/\b(huts?|hostels?|schronisk\w*|przystan\w*|bus stops?|parking|signposts?|tablice?)\b/i.test(calosc)) continue;
      if (PRZYRODA.test(`${plik.replace(/[_-]/g, " ")} ${opis} ${kategorie.replace(/\|/g, " ")}`)) continue;
      const ocena = OCENY.find(([w]) => w.test(`${md.Assessments?.value ?? ""} ${/Quality images|Featured pictures|Valued images/i.test(kategorie) ? kategorie : ""}`));
      const detal = zrodlo.get(s.title) || DETAL.test(`${plik.replace(/_/g, " ")} ${opis}`);
      if (ZBEDNE.test(opis.slice(0, 120))) continue;
      // konstrukcja i rzeźba w opisie/kategoriach: wyraźny dodatek (to jest to, co ma pokazać atlas)
      const punkty = (ocena?.[2] ?? 0) + (detal ? 8 : 0) + (rzezba ? 12 : 0) + (KONSTRUKCJA.test(calosc) ? 6 : 0) + Math.log2((ii.width * ii.height) / 1e6 + 1) * 3 + (ii.width > ii.height ? 3 : 0) + (opis.length > 30 ? 2 : 0);
      wyniki.push({
        plik, url: ii.url.split("?")[0], ...rozmiary(ii.thumburl, ii.url, ii.width), szer: ii.width, wys: ii.height,
        // „No machine-readable author provided. Xauxa assumed (based on copyright claims)” → „Xauxa”
        autor: (bezHtml(md.Artist?.value).replace(/^No machine-readable author provided\.\s*(.+?)\s+assumed.*$/i, "$1") || "nieznany").slice(0, 120),
        licencja, licencja_url: md.LicenseUrl?.value ?? "",
        data: bezHtml(md.DateTimeOriginal?.value ?? md.DateTime?.value).slice(0, 10), strona: ii.descriptionurl,
        detal, opis: opis.length > 220 ? `${opis.slice(0, 219).replace(/\s+\S*$/, "")}…` : opis, ...(ocena ? { ocena: ocena[1] } : {}), punkty,
      });
    }
  }
  // seria zdjęć z jednego aparatu („Tiwanaku10”, „Tiwanaku11”…) – najwyżej dwa z serii
  // „…07a”, „…07b” to ta sama seria
  const seria = (p: string) => p.replace(/\.[a-z]+$/i, "").replace(/\d+[a-z]?\b/gi, "").replace(/[\d\s_().,-]+/g, "").toLowerCase();
  const glowne = obraz ? obraz.replace(/_/g, " ") : "";
  wyniki.sort((a, b) => Number(b.plik.replace(/_/g, " ") === glowne) - Number(a.plik.replace(/_/g, " ") === glowne) || b.punkty - a.punkty);
  const ileSerii = new Map<string, number>();
  const wybrane = { detal: [] as typeof wyniki, widok: [] as typeof wyniki };
  for (const z of wyniki) {
    const s = seria(z.plik);
    if ((ileSerii.get(s) ?? 0) >= 2) continue;
    const lista = z.detal ? wybrane.detal : wybrane.widok;
    if (lista.length >= ile / 2) continue;
    lista.push(z);
    ileSerii.set(s, (ileSerii.get(s) ?? 0) + 1);
  }
  // za mało zbliżeń albo widoków: dopełnij drugą grupą do łącznej liczby
  const reszta: typeof wyniki = [];
  for (const z of wyniki) {
    if (wybrane.detal.includes(z) || wybrane.widok.includes(z)) continue;
    const s = seria(z.plik);
    if ((ileSerii.get(s) ?? 0) >= 2) continue;
    reszta.push(z);
    ileSerii.set(s, (ileSerii.get(s) ?? 0) + 1);
  }
  const razem = [...wybrane.widok, ...wybrane.detal, ...reszta].slice(0, ile);
  return razem.map(({ punkty, ...z }) => z);
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

// zapis z ponowieniem: na Windows plik bywa chwilowo zablokowany, gdy czyta go inny program
const zapisz = () => {
  for (let i = 0; ; i++) {
    try { writeFileSync(PLIK, JSON.stringify(dane, null, 1) + "\n"); return; } catch (e) {
      if (i >= 5) throw e;
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500);
    }
  }
};

// --zdjecia: tylko nowe zdjęcia dla wszystkich pobranych już miejsc (bez ponownego szukania w Wikidata i Wikipedii)
if (process.argv.includes("--zdjecia")) {
  const wszystkie = process.argv.includes("--wszystkie"); // pobierz od nowa zdjęcia wszystkich miejsc (np. po zmianie filtrów)
  const tylko = process.argv.find((a) => a.startsWith("--tylko="))?.slice(8); // np. --tylko=Stonehenge (próba na jednym miejscu)
  // --ile=40: ile zdjęć na miejsce (domyślnie 20); więcej zdjęć to mniej powtórek w filmach z podcastu
  const ILE = Number(process.argv.find((a) => a.startsWith("--ile="))?.slice(6) ?? 20);
  // bez --od-nowa pomija miejsca już zrobione (gdy poprzednie pobieranie się przerwało)
  const lista = zrodlo.miejsca.filter((m) => dane[m.nazwa] && !m.bez_zdjec && (!tylko || m.nazwa === tylko) && (odNowa || wszystkie || !!tylko || !dane[m.nazwa].zdjecia.some((z) => "detal" in z)));
  const p18 = new Map<string, string>();
  for (let i = 0; i < lista.length; i += 50) {
    const ids = lista.slice(i, i + 50).map((m) => dane[m.nazwa].wikidata);
    const e = (await wd({ action: "wbgetentities", ids: ids.join("|"), props: "claims" })).entities;
    for (const id of ids) { const v = e[id]?.claims?.P18?.[0]?.mainsnak?.datavalue?.value; if (v) p18.set(id, v); }
  }
  for (const m of lista) {
    const d = dane[m.nazwa];
    const zdj = await zdjeciaCommons(p18.get(d.wikidata), d.kategoria, ILE).catch((e) => { console.log(`✗ ${m.nazwa}: ${e.message}`); return null; });
    if (!zdj) continue;
    const przed = d.zdjecia.length;
    if (wszystkie || tylko || zdj.length >= przed || zdj.length >= 6) d.zdjecia = zdj; // nie zastępuj bogatszej listy uboższą
    console.log(`✓ ${m.nazwa}: ${przed} → ${d.zdjecia.length} zdj. (zbliżeń: ${d.zdjecia.filter((z) => z.detal).length}, ocenionych: ${d.zdjecia.filter((z) => z.ocena).length})`);
    zapisz();
    await czekaj(100);
  }
  process.exit(0);
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
