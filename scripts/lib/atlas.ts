/**
 * Atlas Leszka – wspólne dane dla strony atlasu (scripts/atlas.ts), czytelni i serwera MCP:
 * łączy ręczną listę miejsc (atlas/miejsca.json) z danymi z Wikidata/Commons (atlas/dane.json),
 * artykułami, w których opracowaniach występuje miejsce, i zdjęciami z tych artykułów.
 */
import { existsSync, readFileSync } from "node:fs";
import type { Archiwum, Dokument } from "../../src/archiwum.js";

export type ZdjecieCommons = { plik: string; url: string; miniatura: string; duze: string; szer: number; wys: number; autor: string; licencja: string; licencja_url: string; data: string; strona: string };
type DaneMiejsca = {
  wikidata: string; etykieta: string; opis: string; lat: number | null; lon: number | null;
  kategoria: string; powstanie: string; wiki: { jezyk: string; tytul: string; url: string; wstep: string } | null; zdjecia: ZdjecieCommons[];
};
type Wpis = { nazwa: string; wikidata?: string; wsp?: [number, number]; rodzaje: string[]; aliasy: string[] };

export type ZdjecieLeszka = { sciezka: string; typ: string; opis: string; artykul: string; pochodzenie: string };
export type MiejsceAtlasu = {
  slug: string; nazwa: string; aliasy: string[]; rodzaje: string[]; lat: number; lon: number;
  wikidata: string; opisWikidata: string; powstanie: string; wiki: DaneMiejsca["wiki"];
  artykuly: string[]; zdjeciaLeszka: ZdjecieLeszka[]; zdjeciaCommons: ZdjecieCommons[];
  /** tezy z opracowań, które dotyczą miejsca – z dosłownym cytatem autora (sprawdzanym przez sprawdz-opracowania) */
  cytaty: { artykul: string; teza: string; cytat: string }[];
};

export const slug = (s: string) =>
  s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const norm = (s: string) => s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[„”"']/g, "").trim();

// rdzenie nazw do szukania w opisach zdjęć: „Gizie” ~ „Giza”, „Sacsayhuamán” ~ „Sacsayhuaman”
const ZBEDNE = new Set(["zamek", "zamku", "w", "we", "i", "na", "pod", "k", "dolina", "jezioro", "wyspa", "wielki", "wielka", "swiatynie", "swiatynia", "piramidy", "piramida", "grobowce", "megalityczne", "klasztor", "nekropolia", "jaskinia", "linie", "z", "kamienie", "most", "mur", "wal", "palac", "struktura", "naturalny", "reaktor", "meteoryt", "katastrofa", "slady", "nad", "rzeka", "odcisk", "droga", "kolegiata", "akwedukt", "cysterna", "bazyliki", "mechanizm", "dolmen", "egipskie", "egipt", "porownanie", "jeziorem", "stare", "miasto"]);
// każda nazwa daje wzorzec: rdzenie jej znaczących słów – opis zdjęcia musi zawierać wszystkie („Brama Słońca” = bram + slonc)
export const rdzenie = (nazwy: string[]) =>
  nazwy
    .map((n) => norm(n.replace(/\(.*?\)/g, "")).split(/[^a-z0-9]+/).filter((w) => w.length >= 3 && !ZBEDNE.has(w)).map((w) => w.slice(0, Math.max(4, Math.min(w.length - 1, 7)))))
    .filter((w) => w.length);
const pasuje = (tekst: string, wzorce: string[][]) => wzorce.some((w) => w.every((x) => tekst.includes(x)));

const TYPY_ZDJEC = new Set(["zdjęcie", "rzeźba/relief", "rysunek", "schemat", "mapa", "portret"]);
const pochodzenie = (sciezka: string) =>
  sciezka.includes("/kolasia/")
    ? "fot. Joanna, cykl „Kamienna Polska w obiektywie Joanny” na uleszka.net"
    : "z artykułu Leszka Klimka na uleszka.net (2004–2007), źródło oryginału nieznane";

export function wczytajAtlas(archiwum: Archiwum, katalog = "."): { miejsca: MiejsceAtlasu[]; rodzaje: Record<string, string>; poArtykule: Map<string, MiejsceAtlasu[]> } {
  const plikM = `${katalog}/atlas/miejsca.json`, plikD = `${katalog}/atlas/dane.json`;
  if (!existsSync(plikM) || !existsSync(plikD)) return { miejsca: [], rodzaje: {}, poArtykule: new Map() };
  const zrodlo: { rodzaje: Record<string, string>; miejsca: Wpis[] } = JSON.parse(readFileSync(plikM, "utf8"));
  const dane: Record<string, DaneMiejsca> = JSON.parse(readFileSync(plikD, "utf8"));

  const poAliasie = new Map<string, Wpis>();
  for (const w of zrodlo.miejsca) for (const a of [w.nazwa, ...w.aliasy]) poAliasie.set(norm(a), w);
  const artykulyMiejsca = new Map<Wpis, Set<string>>();
  for (const o of archiwum.opracowania.values())
    for (const x of o.miejsca) {
      const w = poAliasie.get(norm(x));
      if (w) artykulyMiejsca.set(w, (artykulyMiejsca.get(w) ?? new Set()).add(o.id));
    }
  // ile miejsc atlasu ma dany artykuł (artykuł o jednym miejscu: wszystkie jego zdjęcia należą do tego miejsca)
  const ileMiejsc = new Map<string, number>();
  for (const s of artykulyMiejsca.values()) for (const id of s) ileMiejsc.set(id, (ileMiejsc.get(id) ?? 0) + 1);

  const wzorce = new Map(zrodlo.miejsca.map((w) => [w, rdzenie([w.nazwa, ...w.aliasy, dane[w.nazwa]?.etykieta ?? ""])]));
  const miejsca: MiejsceAtlasu[] = [];
  for (const w of zrodlo.miejsca) {
    const d = dane[w.nazwa];
    const lat = w.wsp?.[0] ?? d?.lat, lon = w.wsp?.[1] ?? d?.lon;
    if (!d || lat == null || lon == null) continue;
    const artykuly = [...(artykulyMiejsca.get(w) ?? [])].filter((id) => archiwum.znajdz(id, "artykul"));
    artykuly.sort((a, b) => (archiwum.znajdz(a, "artykul")!.kolejnosc - archiwum.znajdz(b, "artykul")!.kolejnosc));
    const r = wzorce.get(w)!;
    const inne = [...wzorce].filter(([x]) => x !== w).map(([, p]) => p);
    const zdjeciaLeszka: ZdjecieLeszka[] = [];
    const juz = new Set<string>();
    for (const id of artykuly) {
      const a = archiwum.znajdz(id, "artykul") as Dokument;
      // artykuł naprawdę o tym jednym miejscu (np. fotografie z Bobolic): mało miejsc w opracowaniu i jedno z atlasu
      const jedno = ileMiejsc.get(id) === 1 && (archiwum.opracowania.get(id)?.miejsca.length ?? 99) <= 3;
      for (const o of a.obrazy) {
        const op = archiwum.opisyObrazow.get(o.sciezka);
        if (!op || !TYPY_ZDJEC.has(op.typ) || juz.has(o.sciezka)) continue;
        const tekst = norm(`${op.opis} ${op.tekst_na_obrazie}`);
        if (!jedno && !pasuje(tekst, r)) continue;
        if (jedno && !pasuje(tekst, r) && (!["zdjęcie", "rzeźba/relief"].includes(op.typ) || inne.some((p) => pasuje(tekst, p)))) continue;
        juz.add(o.sciezka);
        zdjeciaLeszka.push({ sciezka: o.sciezka, typ: op.typ, opis: op.opis, artykul: id, pochodzenie: pochodzenie(o.sciezka) });
      }
    }
    const cytaty: MiejsceAtlasu["cytaty"] = [];
    for (const id of artykuly) {
      const o = archiwum.opracowania.get(id);
      if (!o) continue;
      const tezy = o.tezy.filter((t) => t.cytat && pasuje(norm(`${t.teza} ${t.cytat}`), r));
      for (const t of tezy.slice(0, 2)) cytaty.push({ artykul: id, teza: t.teza, cytat: t.cytat });
    }
    miejsca.push({
      cytaty,
      slug: slug(w.nazwa), nazwa: w.nazwa, aliasy: w.aliasy.filter((a) => a !== w.nazwa), rodzaje: w.rodzaje, lat, lon,
      wikidata: d.wikidata, opisWikidata: d.opis, powstanie: d.powstanie, wiki: d.wiki,
      artykuly, zdjeciaLeszka: zdjeciaLeszka.slice(0, 40), zdjeciaCommons: d.zdjecia,
    });
  }
  const poArtykule = new Map<string, MiejsceAtlasu[]>();
  for (const m of miejsca) for (const id of m.artykuly) poArtykule.set(id, [...(poArtykule.get(id) ?? []), m]);
  return { miejsca, rodzaje: zrodlo.rodzaje, poArtykule };
}
