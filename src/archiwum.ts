/**
 * Wczytywanie archiwum (pliki Markdown z folderu `artykuly/`), wyszukiwanie i dzielenie na części.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join, posix } from "node:path";
import MiniSearch from "minisearch";

export type Obraz = { opis: string; sciezka: string };
export type Artykul = {
  id: string;
  tytul: string;
  dzial: string;
  rodzic?: string;
  adresOryginalny: string;
  plik: string; // ścieżka względem katalogu głównego repozytorium
  tresc: string; // Markdown, ścieżki obrazów względem katalogu głównego, linki do innych artykułów jako id
  czysty: string; // sam tekst (bez składni obrazków i linków) – do wyszukiwania
  obrazy: Obraz[];
  kolejnosc: number;
};

/** Zamienia litery na małe i bez polskich znaków, zachowując długość tekstu (1 znak -> 1 znak). */
export function zloz(s: string): string {
  let out = "";
  for (const ch of s.toLowerCase()) {
    if (ch === "ł") out += "l";
    else {
      const base = ch.normalize("NFD")[0];
      out += base.length === ch.length ? base : ch;
    }
  }
  return out;
}

function frontMatter(md: string): { meta: Record<string, string>; body: string } {
  const m = md.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return { meta: {}, body: md };
  const meta: Record<string, string> = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^(\w+): (.*)$/);
    if (kv) meta[kv[1]] = kv[2].startsWith('"') ? JSON.parse(kv[2]) : kv[2];
  }
  return { meta, body: md.slice(m[0].length).trim() };
}

export class Archiwum {
  readonly artykuly: Artykul[] = [];
  readonly dzialy: string[] = [];
  private poId = new Map<string, Artykul>();
  private indeks: MiniSearch<Artykul>;
  private zlozone = new Map<string, string>(); // tekst bez polskich znaków – do szukania fraz

  constructor(readonly katalogGlowny: string) {
    const dirArt = join(katalogGlowny, "artykuly");
    const pliki: string[] = [];
    for (const d of readdirSync(dirArt).sort())
      for (const f of readdirSync(join(dirArt, d)).sort()) if (f.endsWith(".md")) pliki.push(`artykuly/${d}/${f}`);

    // najpierw mapa plik -> id, żeby przepisać linki między artykułami
    const surowe = pliki.map((p) => ({ p, ...frontMatter(readFileSync(join(katalogGlowny, p), "utf8")) }));
    const idPoPliku = new Map(surowe.map((s) => [s.p, s.meta.id]));

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
      const czysty = tresc
        .replace(/!\[([^\]]*)\]\([^)]*\)/g, "")
        .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
        .replace(/\\([\\`*_{}[\]()#+\-.!])/g, "$1")
        .replace(/\*\*|__/g, "")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n");
      const a: Artykul = {
        id: meta.id,
        tytul: meta.tytul,
        dzial: meta.dzial,
        rodzic: meta.rodzic,
        adresOryginalny: meta.adres_oryginalny,
        plik: p,
        tresc,
        czysty,
        obrazy,
        kolejnosc: i,
      };
      this.artykuly.push(a);
      this.poId.set(a.id, a);
      if (!this.dzialy.includes(a.dzial)) this.dzialy.push(a.dzial);
    });

    this.indeks = new MiniSearch<Artykul>({
      fields: ["tytul", "czysty"],
      storeFields: ["id"],
      processTerm: (t) => (t.length < 2 ? null : zloz(t)),
      searchOptions: { boost: { tytul: 3 }, prefix: true, fuzzy: 0.15 },
    });
    this.indeks.addAll(this.artykuly);
    for (const a of this.artykuly) this.zlozone.set(a.id, ` ${zloz(a.czysty).replace(/[^\p{L}\p{N}]+/gu, " ")} `);
  }

  /** Szuka artykułu po id, nazwie pliku lub tytule (bez względu na wielkość liter i polskie znaki). */
  znajdz(klucz: string): Artykul | undefined {
    const k = klucz.trim().replace(/^artykul:/, "");
    if (this.poId.has(k)) return this.poId.get(k);
    const z = zloz(k);
    return (
      this.artykuly.find((a) => a.plik === k || a.plik.endsWith("/" + k) || a.plik.endsWith("/" + k + ".md")) ??
      this.artykuly.find((a) => zloz(a.tytul) === z) ??
      this.artykuly.find((a) => zloz(a.id).endsWith("/" + z) || zloz(a.id) === z) ??
      this.artykuly.find((a) => zloz(a.tytul).includes(z))
    );
  }

  szukaj(zapytanie: string, opcje: { dzial?: string; limit: number }) {
    const filtr = opcje.dzial ? (w: { id: string }) => zloz(this.poId.get(w.id)!.dzial) === zloz(opcje.dzial!) : undefined;
    let wyniki = this.indeks.search(zapytanie, { combineWith: "AND", filter: filtr });
    let tryb = "wszystkie słowa";
    if (!wyniki.length) {
      wyniki = this.indeks.search(zapytanie, { combineWith: "OR", filter: filtr });
      tryb = "dowolne ze słów";
    }
    // premia, gdy całe zapytanie występuje w tekście jako dokładna fraza
    const fraza = zloz(zapytanie).replace(/[^\p{L}\p{N}]+/gu, " ").trim(); // bez interpunkcji
    if (fraza.includes(" "))
      wyniki = wyniki
        .map((w) => (this.zlozone.get(w.id)!.includes(fraza) ? { ...w, score: w.score * 5 } : w))
        .sort((x, y) => y.score - x.score);
    return {
      tryb,
      lacznie: wyniki.length,
      wyniki: wyniki.slice(0, opcje.limit).map((w) => {
        const a = this.poId.get(w.id)!;
        return { artykul: a, terminy: w.terms, wynik: w.score };
      }),
    };
  }

  /** Fragmenty tekstu wokół wystąpień słów (bez względu na polskie znaki i wielkość liter). */
  fragmenty(a: Artykul, terminy: string[], kontekst: number, limit: number) {
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
      // przytnij do granic słów
      while (od > 0 && /\S/.test(tekst[od - 1])) od--;
      while (doo < tekst.length && /\S/.test(tekst[doo])) doo++;
      wynik.push({
        od,
        tekst: (od > 0 ? "…" : "") + tekst.slice(od, doo).replace(/\s+/g, " ").trim() + (doo < tekst.length ? "…" : ""),
      });
      koniecPoprzedniego = doo;
    }
    return { lacznie: pozycje.length, fragmenty: wynik.slice(0, limit), wszystkichFragmentow: wynik.length };
  }

  /** Dzieli treść na części po ok. `rozmiar` znaków, na granicach akapitów. */
  czesci(a: Artykul, rozmiar: number): string[] {
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

  podstrony(a: Artykul) {
    return this.artykuly.filter((x) => x.rodzic === a.id);
  }
}
