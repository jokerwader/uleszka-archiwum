/**
 * Errata – poprawki oczywistych literówek (np. „moga” → „mogą”, „ne” → „nie”).
 * Artykuły w artykuly/ zostają wierną kopią oryginału; poprawki są stosowane tylko tam, gdzie tekst się czyta
 * lub słucha: w czytelni (poprawione słowo jest oznaczone, oryginał widać po najechaniu) i w tekstach dla lektora.
 * Lista: dane/poprawki/errata.json, sprawdzana przez scripts/errata.ts.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { osobneSlowo } from "./inicjaly.js";

export type Poprawka = {
  /** identyfikator artykułu albo „*” (wszystkie artykuły – tylko gdy `wszedzie`) */
  id: string;
  /** błędny fragment dokładnie jak w tekście */
  zle: string;
  /** poprawiony fragment */
  dobrze: string;
  /** kilka słów z tekstu zawierających `zle` – wskazuje miejsce poprawki */
  kontekst: string;
  /** `zle` nigdy nie jest poprawnym słowem – poprawiamy każde wystąpienie (w artykule `id` albo wszędzie) */
  wszedzie: boolean;
  powod: string;
};

/**
 * Tekst artykułu, w którym szukamy miejsc poprawek: sam tekst, z inicjałami połączonymi ze słowem
 * (w oryginale „**Z**” stoi w osobnym akapicie przed „abawna…” – czytelnia i lektor łączą to w „Zabawna”).
 */
export const tekstBazowy = (czysty: string) =>
  czysty.replace(/(?<=^|\n)([A-ZĄĆĘŁŃÓŚŹŻ])[ \t]*\n[ \t]*\n(?=\p{Ll})/gu, (m, l: string, poz: number, s: string) =>
    osobneSlowo(l, s.slice(poz + m.length, poz + m.length + 40)) ? l + " " : l,
  );

export function wczytajErrate(katalogGlowny = "."): Poprawka[] {
  const plik = join(katalogGlowny, "dane/poprawki/errata.json");
  return existsSync(plik) ? (JSON.parse(readFileSync(plik, "utf8")) as Poprawka[]) : [];
}

const regEsc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
/** Wzorzec fragmentu tekstu odporny na różne odstępy i na encje HTML (&quot; &#39; &amp;). */
function wzorzec(s: string): string {
  return [...s]
    .map((z) => (/\s/.test(z) ? "\\s+" : z === '"' ? '(?:"|&quot;)' : z === "'" ? "(?:'|&#39;)" : z === "&" ? "&(?:amp;)?" : regEsc(z)))
    .join("")
    .replace(/(?:\\s\+)+/g, "\\s+");
}
const wyraz = (s: string) => new RegExp(`(?<![\\p{L}\\p{N}])${wzorzec(s)}(?![\\p{L}\\p{N}])`, "gu");

export const dotyczy = (p: Poprawka, id: string) => p.id === id || (p.id === "*" && p.wszedzie);

/**
 * Stosuje poprawki do tekstu artykułu `id`. `oznacz` pozwala opakować poprawione słowo (np. w HTML).
 * Zwraca poprawiony tekst i numery (indeksy w erracie) poprawek, które zadziałały.
 */
export function popraw(
  tekst: string,
  id: string,
  errata: Poprawka[],
  oznacz: (p: Poprawka, znalezione: string) => string = (p) => p.dobrze,
): { tekst: string; uzyte: Map<number, number> } {
  const uzyte = new Map<number, number>();
  const wstawki: string[] = [];
  // poprawione miejsca zastępujemy znacznikiem, żeby kolejne poprawki nie trafiły w już poprawiony tekst
  const znacznik = (s: string) => `\u0000${wstawki.push(s) - 1}\u0000`;
  const licz = (i: number) => uzyte.set(i, (uzyte.get(i) ?? 0) + 1);
  errata.forEach((p, i) => {
    if (!dotyczy(p, id)) return;
    if (p.wszedzie) {
      tekst = tekst.replace(wyraz(p.zle), (m) => (licz(i), znacznik(oznacz(p, m))));
    } else {
      tekst = tekst.replace(new RegExp(wzorzec(p.kontekst), "gu"), (fragment) => {
        let zrobione = false;
        const nowy = fragment.replace(wyraz(p.zle), (m) => (zrobione ? m : ((zrobione = true), znacznik(oznacz(p, m)))));
        if (zrobione) licz(i);
        return nowy;
      });
    }
  });
  return { tekst: tekst.replace(/\u0000(\d+)\u0000/g, (_m, n: string) => wstawki[Number(n)]), uzyte };
}

/** Poprawki w HTML – tylko w tekście (poza znacznikami i atrybutami), poprawione słowo oznaczone klasą „poprawka”. */
export function poprawHtml(html: string, id: string, errata: Poprawka[]): { html: string; uzyte: Map<number, number> } {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const uzyte = new Map<number, number>();
  // sam tekst strony (bez znaczników) z mapą: pozycja w tekście → pozycja w HTML,
  // żeby kontekst poprawki mógł przechodzić przez granice akapitów i formatowania
  const kawalki: { odTekst: number; odHtml: number; dl: number }[] = [];
  let tekst = "";
  for (const m of html.matchAll(/[^<]+|<[^>]*>/g)) {
    if (m[0].startsWith("<")) { tekst += m[0].startsWith("</") || /^<(?:p|div|li|h\d|br|tr|td|th|blockquote)\b/i.test(m[0]) ? " " : ""; continue; }
    kawalki.push({ odTekst: tekst.length, odHtml: m.index!, dl: m[0].length });
    tekst += m[0];
  }
  const doHtml = (poz: number, dl: number) => {
    const k = kawalki.find((x) => poz >= x.odTekst && poz + dl <= x.odTekst + x.dl);
    return k ? k.odHtml + (poz - k.odTekst) : -1; // -1: słowo przecina znacznik – pomijamy
  };
  const zmiany: { od: number; dl: number; na: string; i: number }[] = [];
  const zajete = (od: number, dl: number) => zmiany.some((z) => od < z.od + z.dl && z.od < od + dl);
  const dodaj = (p: Poprawka, i: number, poz: number, znalezione: string) => {
    const od = doHtml(poz, znalezione.length);
    if (od < 0 || zajete(od, znalezione.length)) return false;
    zmiany.push({ od, dl: znalezione.length, i, na: `<span class="poprawka" title="${esc(`W oryginale: „${znalezione}”`)}">${esc(p.dobrze)}</span>` });
    return true;
  };
  errata.forEach((p, i) => {
    if (!dotyczy(p, id)) return;
    if (p.wszedzie) {
      for (const m of tekst.matchAll(wyraz(p.zle))) dodaj(p, i, m.index!, m[0]);
    } else {
      for (const f of tekst.matchAll(new RegExp(wzorzec(p.kontekst), "gu"))) {
        const m = [...f[0].matchAll(wyraz(p.zle))][0];
        if (m) dodaj(p, i, f.index! + m.index!, m[0]);
      }
    }
  });
  let wynik = html;
  for (const z of zmiany.sort((a, b) => b.od - a.od)) {
    wynik = wynik.slice(0, z.od) + z.na + wynik.slice(z.od + z.dl);
    uzyte.set(z.i, (uzyte.get(z.i) ?? 0) + 1);
  }
  return { html: wynik, uzyte };
}
