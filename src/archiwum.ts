/**
 * Wczytywanie archiwum: artykuły (`artykuly/`), biblioteka dzieł z domeny publicznej (`biblioteka/`),
 * opracowania AI (`opracowania/`) i opisy zdjęć AI (`dane/opisy-obrazow/`). Wyszukiwanie i dzielenie na części.
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, posix } from "node:path";
import MiniSearch from "minisearch";

export type Obraz = { opis: string; sciezka: string };
export type Dokument = {
  rodzaj: "artykul" | "ksiazka";
  id: string;
  tytul: string;
  dzial: string; // dla książek: "Biblioteka"
  autor?: string;
  rodzic?: string;
  adresOryginalny: string; // dla książek: źródło (Gutenberg, Wolne Lektury, Wikiźródła)
  plik: string; // ścieżka względem katalogu głównego repozytorium
  tresc: string; // Markdown/tekst; ścieżki obrazów względem katalogu głównego, linki do innych artykułów jako artykul:<id>
  czysty: string; // sam tekst (bez składni obrazków i linków) – do wyszukiwania
  obrazy: Obraz[];
  kolejnosc: number;
  meta: Record<string, unknown>;
};
export type Artykul = Dokument;

export type Teza = { teza: string; cytat: string; dziedzina: string };
export type Opracowanie = {
  id: string;
  tytul: string;
  streszczenie: string;
  tezy: Teza[];
  tematy: string[];
  osoby: string[];
  miejsca: string[];
  okresy: { kiedy: string; co: string }[];
  zrodla_cytowane: string[];
};
export type OpisObrazu = { sciezka: string; typ: string; opis: string; tekst_na_obrazie: string };

/** Zamienia litery na małe i bez polskich znaków, zachowując długość tekstu (1 znak -> 1 znak). */
const ZLOZONE_ZNAKI = new Map<string, string>();
export function zloz(s: string): string {
  // zamiana tylko znaków spoza ASCII, jednym przebiegiem – oszczędza pamięć przy długich książkach
  return s.toLowerCase().replace(/[^\x00-\x7f]/gu, (ch) => {
    let r = ZLOZONE_ZNAKI.get(ch);
    if (r === undefined) {
      const base = ch.normalize("NFD")[0];
      r = ch === "ł" ? "l" : base.length === ch.length ? base : ch;
      ZLOZONE_ZNAKI.set(ch, r);
    }
    return r;
  });
}

function frontMatter(md: string): { meta: Record<string, unknown>; body: string } {
  const m = md.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return { meta: {}, body: md };
  const meta: Record<string, unknown> = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^(\w+): (.*)$/);
    if (kv) meta[kv[1]] = /^["[]/.test(kv[2]) ? JSON.parse(kv[2]) : kv[2];
  }
  return { meta, body: md.slice(m[0].length).trim() };
}

function wszystkiePliki(dir: string, rozszerzenie: string): string[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .sort()
    .flatMap((n) => {
      const p = join(dir, n);
      return statSync(p).isDirectory() ? wszystkiePliki(p, rozszerzenie) : n.endsWith(rozszerzenie) ? [p] : [];
    });
}

const naCzysty = (tresc: string) =>
  tresc
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\\([\\`*_{}[\]()#+\-.!])/g, "$1")
    .replace(/\*\*|__/g, "")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n");

export class Archiwum {
  readonly artykuly: Dokument[] = [];
  readonly ksiazki: Dokument[] = [];
  readonly dzialy: string[] = [];
  readonly opracowania = new Map<string, Opracowanie>();
  readonly opisyObrazow = new Map<string, OpisObrazu>();
  private poId = new Map<string, Dokument>();
  private indeks: MiniSearch;
  private indeksBiblioteki: MiniSearch;
  private zlozone = new Map<string, string>(); // tekst bez polskich znaków – do szukania fraz

  constructor(readonly katalogGlowny: string) {
    // ---- opracowania i opisy zdjęć (opcjonalne) ----
    for (const p of wszystkiePliki(join(katalogGlowny, "opracowania"), ".json")) {
      try {
        const o = JSON.parse(readFileSync(p, "utf8")) as Opracowanie;
        if (o.id) this.opracowania.set(o.id, o);
      } catch {
        /* uszkodzony plik pomijamy – wykryje go `npm run sprawdz` */
      }
    }
    for (const p of wszystkiePliki(join(katalogGlowny, "dane", "opisy-obrazow"), ".json")) {
      try {
        for (const o of JSON.parse(readFileSync(p, "utf8")) as OpisObrazu[]) if (o?.sciezka) this.opisyObrazow.set(o.sciezka, o);
      } catch {
        /* jw. */
      }
    }

    // ---- artykuły ----
    const pliki = wszystkiePliki(join(katalogGlowny, "artykuly"), ".md").map((p) => posix.join("artykuly", p.slice(join(katalogGlowny, "artykuly").length + 1).replace(/\\/g, "/")));
    const surowe = pliki.map((p) => ({ p, ...frontMatter(readFileSync(join(katalogGlowny, p), "utf8")) }));
    const idPoPliku = new Map(surowe.map((s) => [s.p, String(s.meta.id)]));
    surowe.forEach(({ p, meta, body }, i) => {
      const obrazy: Obraz[] = [];
      const tresc = body
        .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_m, alt: string, src: string) => {
          if (/^https?:/.test(src)) return `![${alt}](${src})`;
          const sciezka = posix.normalize(posix.join(posix.dirname(p), decodeURI(src)));
          obrazy.push({ opis: alt, sciezka });
          return `![${alt}](${sciezka})`;
        })
        .replace(/\]\(([^)]+\.md)\)/g, (m, href: string) => {
          const cel = posix.normalize(posix.join(posix.dirname(p), decodeURI(href)));
          return idPoPliku.has(cel) ? `](artykul:${idPoPliku.get(cel)})` : m;
        })
        .replace(/\]\((\.\.\/[^)]+)\)/g, (_m, href: string) => `](${posix.normalize(posix.join(posix.dirname(p), decodeURI(href)))})`);
      const a: Dokument = {
        rodzaj: "artykul",
        id: String(meta.id),
        tytul: String(meta.tytul),
        dzial: String(meta.dzial),
        rodzic: meta.rodzic as string | undefined,
        adresOryginalny: String(meta.adres_oryginalny),
        plik: p,
        tresc,
        czysty: naCzysty(tresc),
        obrazy,
        kolejnosc: i,
        meta,
      };
      this.artykuly.push(a);
      this.poId.set(a.id, a);
      if (!this.dzialy.includes(a.dzial)) this.dzialy.push(a.dzial);
    });

    // ---- biblioteka ----
    wszystkiePliki(join(katalogGlowny, "biblioteka"), ".md")
      .filter((p) => !p.endsWith("README.md"))
      .forEach((pelna, i) => {
        const { meta, body } = frontMatter(readFileSync(pelna, "utf8"));
        if (!meta.id) return;
        const k: Dokument = {
          rodzaj: "ksiazka",
          id: String(meta.id),
          tytul: String(meta.tytul),
          dzial: "Biblioteka",
          autor: String(meta.autor),
          adresOryginalny: String(meta.zrodlo),
          plik: posix.join("biblioteka", String(meta.id) + ".md"),
          tresc: body,
          czysty: body,
          obrazy: [],
          kolejnosc: i,
          meta,
        };
        this.ksiazki.push(k);
        this.poId.set(k.id, k);
      });

    // ---- indeksy pełnotekstowe ----
    const opcje = {
      storeFields: ["id"],
      processTerm: (t: string) => (t.length < 2 ? null : zloz(t)),
    };
    this.indeks = new MiniSearch({
      ...opcje,
      fields: ["tytul", "czysty", "opracowanie", "obrazy"],
      searchOptions: { boost: { tytul: 3, opracowanie: 1.5, obrazy: 0.7 }, prefix: true, fuzzy: 0.15 },
    });
    this.indeks.addAll(
      this.artykuly.map((a) => ({
        id: a.id,
        tytul: a.tytul,
        czysty: a.czysty,
        opracowanie: this.tekstOpracowania(a.id),
        obrazy: a.obrazy.map((o) => this.opisObrazu(o.sciezka)).filter(Boolean).join("\n"),
      })),
    );
    this.indeksBiblioteki = new MiniSearch({
      ...opcje,
      fields: ["tytul", "autor", "czysty"],
      searchOptions: { boost: { tytul: 3, autor: 2 }, prefix: true, fuzzy: 0.1 },
    });
    this.indeksBiblioteki.addAll(this.ksiazki.map((k) => ({ id: k.id, tytul: k.tytul, autor: k.autor, czysty: k.czysty })));
    // zamiana przez funkcję (a nie tekst " ") – V8 buduje wtedy zwarty napis; przy książkach to ok. 0,5 GB pamięci mniej
    for (const d of [...this.artykuly, ...this.ksiazki]) this.zlozone.set(d.id, ` ${zloz(d.czysty).replace(/[^\p{L}\p{N}]+/gu, () => " ")} `);
  }

  /** Tekst opracowania (streszczenie, tezy, tematy…) jako jeden ciąg – do wyszukiwania. */
  tekstOpracowania(id: string): string {
    const o = this.opracowania.get(id);
    if (!o) return "";
    return [o.streszczenie, ...o.tezy.map((t) => t.teza), o.tematy.join(", "), o.osoby.join(", "), o.miejsca.join(", "), o.okresy.map((x) => `${x.kiedy}: ${x.co}`).join("; ")].join("\n");
  }

  opisObrazu(sciezka: string): string {
    const o = this.opisyObrazow.get(sciezka);
    if (!o || o.typ === "dekoracja" || o.typ === "błąd") return "";
    return [o.opis, o.tekst_na_obrazie].filter(Boolean).join(" Napis: ");
  }

  /** Szuka artykułu lub książki po id, nazwie pliku lub tytule (bez względu na wielkość liter i polskie znaki). */
  znajdz(klucz: string, rodzaj?: "artykul" | "ksiazka"): Dokument | undefined {
    const k = klucz.trim().replace(/^(artykul|ksiazka):/, "");
    const lista = rodzaj === "ksiazka" ? this.ksiazki : rodzaj === "artykul" ? this.artykuly : [...this.artykuly, ...this.ksiazki];
    const d = this.poId.get(k);
    if (d && (!rodzaj || d.rodzaj === rodzaj)) return d;
    const z = zloz(k);
    return (
      lista.find((a) => a.plik === k || a.plik.endsWith("/" + k) || a.plik.endsWith("/" + k + ".md")) ??
      lista.find((a) => zloz(a.tytul) === z) ??
      lista.find((a) => zloz(a.id).endsWith("/" + z) || zloz(a.id) === z) ??
      lista.find((a) => zloz(a.tytul).includes(z))
    );
  }

  szukaj(zapytanie: string, opcje: { dzial?: string; limit: number; zakres?: "archiwum" | "biblioteka" }) {
    const biblioteka = opcje.zakres === "biblioteka";
    const indeks = biblioteka ? this.indeksBiblioteki : this.indeks;
    const filtr = opcje.dzial && !biblioteka ? (w: { id: string }) => zloz(this.poId.get(w.id)!.dzial) === zloz(opcje.dzial!) : undefined;
    let wyniki = indeks.search(zapytanie, { combineWith: "AND", filter: filtr });
    let tryb = "wszystkie słowa";
    if (!wyniki.length) {
      wyniki = indeks.search(zapytanie, { combineWith: "OR", filter: filtr });
      tryb = "dowolne ze słów";
    }
    // premia, gdy całe zapytanie występuje w tekście jako dokładna fraza
    const fraza = zloz(zapytanie).replace(/[^\p{L}\p{N}]+/gu, " ").trim();
    if (fraza.includes(" "))
      wyniki = wyniki.map((w) => (this.zlozone.get(w.id)!.includes(fraza) ? { ...w, score: w.score * 5 } : w)).sort((x, y) => y.score - x.score);
    return {
      tryb,
      lacznie: wyniki.length,
      wyniki: wyniki.slice(0, opcje.limit).map((w) => ({ artykul: this.poId.get(w.id)!, terminy: w.terms, wynik: w.score })),
    };
  }

  /** Fragmenty tekstu wokół wystąpień słów (bez względu na polskie znaki i wielkość liter). */
  fragmenty(a: Dokument, terminy: string[], kontekst: number, limit: number) {
    const tekst = a.czysty;
    const zlozony = zloz(tekst);
    const pozycje: number[] = [];
    for (const t of new Set(terminy.map(zloz).filter((t) => t.length >= 2))) {
      let i = zlozony.indexOf(t);
      while (i !== -1) {
        pozycje.push(i);
        i = zlozony.indexOf(t, i + t.length);
      }
    }
    pozycje.sort((x, y) => x - y);
    const wynik: { od: number; tekst: string }[] = [];
    let koniecPoprzedniego = -1;
    for (const p of pozycje) {
      if (p < koniecPoprzedniego) continue;
      let od = Math.max(0, p - kontekst);
      let doo = Math.min(tekst.length, p + kontekst);
      while (od > 0 && /\S/.test(tekst[od - 1])) od--;
      while (doo < tekst.length && /\S/.test(tekst[doo])) doo++;
      wynik.push({ od, tekst: (od > 0 ? "…" : "") + tekst.slice(od, doo).replace(/\s+/g, " ").trim() + (doo < tekst.length ? "…" : "") });
      koniecPoprzedniego = doo;
    }
    return { lacznie: pozycje.length, fragmenty: wynik.slice(0, limit), wszystkichFragmentow: wynik.length };
  }

  /** Dzieli treść na części po ok. `rozmiar` znaków, na granicach akapitów. */
  czesci(a: Dokument, rozmiar: number): string[] {
    const akapity = a.tresc.split(/\n\n/);
    const wynik: string[] = [];
    let biezaca = "";
    for (const ak of akapity) {
      if (biezaca && biezaca.length + ak.length + 2 > rozmiar) {
        wynik.push(biezaca);
        biezaca = "";
      }
      if (ak.length > rozmiar) {
        // bardzo długi akapit – dzielimy go na kawałki o stałej długości
        for (let i = 0; i < ak.length; i += rozmiar) wynik.push(ak.slice(i, i + rozmiar));
        continue;
      }
      biezaca = biezaca ? `${biezaca}\n\n${ak}` : ak;
    }
    if (biezaca) wynik.push(biezaca);
    return wynik.length ? wynik : [""];
  }

  podstrony(a: Dokument) {
    return this.artykuly.filter((x) => x.rodzic === a.id);
  }

  /** Książki z biblioteki cytowane w danym artykule. */
  ksiazkiArtykulu(idArtykulu: string) {
    return this.ksiazki.filter((k) => (k.meta.cytowane_w as string[] | undefined)?.includes(idArtykulu));
  }

  /** Artykuły podobne tematycznie wg wspólnych haseł z opracowań (zapas, gdy brak wektorów). */
  podobnePoTematach(id: string, limit: number) {
    const o = this.opracowania.get(id);
    if (!o) return [];
    const moje = new Set([...o.tematy, ...o.miejsca, ...o.osoby].map(zloz));
    return this.artykuly
      .filter((a) => a.id !== id)
      .map((a) => {
        const x = this.opracowania.get(a.id);
        const ich = x ? [...x.tematy, ...x.miejsca, ...x.osoby].map(zloz) : [];
        const wspolne = [...new Set(ich.filter((t) => moje.has(t)))];
        return { artykul: a, wynik: wspolne.length, wspolne };
      })
      .filter((x) => x.wynik > 0)
      .sort((a, b) => b.wynik - a.wynik)
      .slice(0, limit);
  }
}
