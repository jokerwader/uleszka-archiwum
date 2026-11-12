/**
 * Wyszukiwanie po znaczeniu (semantyczne).
 * Teksty są podzielone na fragmenty, a każdy fragment ma „wektor znaczenia” policzony wielojęzycznym modelem
 * (multilingual-e5-small, działa lokalnie, bez internetu po pierwszym pobraniu). Zapytanie zamieniamy na wektor
 * tym samym modelem i szukamy fragmentów o najbliższym znaczeniu.
 *
 * Wektory liczy skrypt `npm run wektory` i zapisuje w `dane/wektory/` (archiwum.json/.bin, biblioteka.json/.bin).
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { Archiwum, Dokument } from "./archiwum.js";

export const MODEL = "Xenova/multilingual-e5-small";
export type Zbior = "archiwum" | "biblioteka";
export type Fragment = { d: string; od: number; do: number; r: "tekst" | "streszczenie" | "obraz"; s?: string };
type Plik = { model: string; wymiar: number; fragmenty: Fragment[] };

/** Dzieli tekst na fragmenty ok. `rozmiar` znaków, na granicach akapitów (zwraca pozycje w tekście). */
export function fragmentuj(tekst: string, rozmiar: number): { od: number; do: number }[] {
  const wynik: { od: number; do: number }[] = [];
  const re = /\n\s*\n/g;
  const granice = [0];
  for (const m of tekst.matchAll(re)) granice.push(m.index! + m[0].length);
  granice.push(tekst.length);
  let od = 0;
  for (let i = 1; i < granice.length; i++) {
    const g = granice[i];
    if (g - od >= rozmiar || i === granice.length - 1) {
      // akapit dłuższy niż 2× rozmiar – tniemy na spacjach
      let start = od;
      while (g - start > rozmiar * 2) {
        let k = tekst.lastIndexOf(" ", start + rozmiar);
        if (k <= start) k = start + rozmiar;
        wynik.push({ od: start, do: k });
        start = k + 1;
      }
      if (tekst.slice(start, g).trim().length > 20) wynik.push({ od: start, do: g });
      od = g;
    }
  }
  return wynik;
}

type Ekstraktor = (teksty: string[], opcje: { pooling: "mean"; normalize: boolean }) => Promise<{ data: Float32Array; dims: number[] }>;
let ekstraktor: Promise<Ekstraktor> | undefined;

/** Ładuje model (przy pierwszym użyciu pobiera go z internetu, ok. 120 MB, potem działa z pamięci podręcznej). */
export function zaladujModel(): Promise<Ekstraktor> {
  ekstraktor ??= import("@huggingface/transformers").then(
    async ({ pipeline }) => (await pipeline("feature-extraction", MODEL, { dtype: "q8" })) as unknown as Ekstraktor,
  );
  return ekstraktor;
}

export async function wektory(teksty: string[], rodzaj: "query" | "passage"): Promise<Float32Array[]> {
  const ext = await zaladujModel();
  const v = await ext(teksty.map((t) => `${rodzaj}: ${t}`), { pooling: "mean", normalize: true });
  const d = v.dims[1];
  return teksty.map((_, i) => v.data.slice(i * d, (i + 1) * d));
}

export class Semantyka {
  private zbiory = new Map<Zbior, { fragmenty: Fragment[]; wymiar: number; dane: Int8Array }>();
  private srednie = new Map<string, Float32Array>(); // średni wektor artykułu – do „powiązanych artykułów”

  constructor(private archiwum: Archiwum) {
    for (const z of ["archiwum", "biblioteka"] as Zbior[]) {
      const pj = join(archiwum.katalogGlowny, "dane", "wektory", `${z}.json`);
      const pb = join(archiwum.katalogGlowny, "dane", "wektory", `${z}.bin`);
      if (!existsSync(pj) || !existsSync(pb)) continue;
      const meta = JSON.parse(readFileSync(pj, "utf8")) as Plik;
      const buf = readFileSync(pb);
      const dane = new Int8Array(buf.buffer, buf.byteOffset, buf.byteLength);
      if (dane.length !== meta.fragmenty.length * meta.wymiar) continue;
      this.zbiory.set(z, { fragmenty: meta.fragmenty, wymiar: meta.wymiar, dane });
    }
    const a = this.zbiory.get("archiwum");
    if (a) {
      const sumy = new Map<string, Float32Array>();
      a.fragmenty.forEach((f, i) => {
        if (f.r === "obraz") return;
        const s = sumy.get(f.d) ?? new Float32Array(a.wymiar);
        for (let k = 0; k < a.wymiar; k++) s[k] += a.dane[i * a.wymiar + k];
        sumy.set(f.d, s);
      });
      for (const [id, s] of sumy) {
        const n = Math.hypot(...s) || 1;
        this.srednie.set(id, s.map((x) => x / n));
      }
    }
  }

  dostepne(z: Zbior) {
    return this.zbiory.has(z);
  }

  async szukaj(zapytanie: string, zbiory: Zbior[], limit: number) {
    const [q] = await wektory([zapytanie], "query");
    const trafienia: { fragment: Fragment; wynik: number; zbior: Zbior }[] = [];
    for (const z of zbiory) {
      const zb = this.zbiory.get(z);
      if (!zb) continue;
      const { fragmenty, wymiar, dane } = zb;
      for (let i = 0; i < fragmenty.length; i++) {
        let s = 0;
        const o = i * wymiar;
        for (let k = 0; k < wymiar; k++) s += dane[o + k] * q[k];
        trafienia.push({ fragment: fragmenty[i], wynik: s / 127, zbior: z });
      }
    }
    trafienia.sort((a, b) => b.wynik - a.wynik);
    // najwyżej 2 fragmenty z jednego dokumentu, żeby wyniki były różnorodne
    const naDok = new Map<string, number>();
    const wynik: typeof trafienia = [];
    for (const t of trafienia) {
      const n = naDok.get(t.fragment.d) ?? 0;
      if (n >= 2) continue;
      naDok.set(t.fragment.d, n + 1);
      wynik.push(t);
      if (wynik.length >= limit) break;
    }
    return wynik;
  }

  /** Artykuły najbardziej podobne znaczeniowo do danego artykułu. */
  podobne(id: string, limit: number) {
    const v = this.srednie.get(id);
    if (!v) return [];
    return [...this.srednie.entries()]
      .filter(([x]) => x !== id)
      .map(([x, w]) => ({ id: x, wynik: w.reduce((s, val, k) => s + val * v[k], 0) }))
      .sort((a, b) => b.wynik - a.wynik)
      .slice(0, limit);
  }

  /** Tekst fragmentu do pokazania w wynikach. */
  tekstFragmentu(f: Fragment, dok: Dokument | undefined): string {
    if (f.r === "obraz") return `[zdjęcie ${f.s}] ${this.archiwum.opisObrazu(f.s ?? "")}`;
    if (f.r === "streszczenie") return `[opracowanie] ${this.archiwum.opracowania.get(f.d)?.streszczenie ?? ""}`;
    return dok ? dok.czysty.slice(f.od, f.do).replace(/\s+/g, " ").trim() : "";
  }
}
