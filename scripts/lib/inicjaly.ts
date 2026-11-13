/**
 * Inicjały akapitów. W oryginale pierwsza litera akapitu stała w osobnej tabelce, więc w Markdownie jest zapisana
 * osobno („**W**”, pusta linia, „ładza…”). Zwykle to początek słowa („Władza”), ale czasem samodzielne słowo
 * („W Polsce”, „A oto”, „Z Kuby”) – wtedy trzeba zostawić spację. Rozstrzyga słownik języka polskiego.
 * Używane przez skrypty budujące czytelnię, teksty dla lektora i erratę (nie przez serwer MCP).
 */
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import nspell from "nspell";

let spell: ReturnType<typeof nspell> | undefined;
const poprawne = (s: string) => {
  if (!spell) {
    const kat = createRequire(import.meta.url).resolve("dictionary-pl").replace(/index\.js$/, "");
    spell = nspell({ aff: readFileSync(kat + "index.aff"), dic: readFileSync(kat + "index.dic") });
  }
  return spell.correct(s) || spell.correct(s.toLowerCase());
};

/** Czy inicjał `litera` jest osobnym słowem przed tekstem `dalej` (a nie początkiem wyrazu)? */
export function osobneSlowo(litera: string, dalej: string): boolean {
  if (!/^[AIOUWZ]$/.test(litera)) return false; // jednoliterowe słowa w polszczyźnie
  if (/^[\p{Lu}\p{N}]/u.test(dalej)) return true; // „W Polsce”, „W X wieku”, „A Albert…”
  const reszta = dalej.match(/^\p{L}+/u)?.[0] ?? "";
  return !!reszta && poprawne(reszta) && !poprawne(litera + reszta);
}

/** Wzorzec inicjału w Markdownie: „**X**”, pusta linia, dalszy tekst akapitu. */
export const INICJAL_MD = /\*\*([A-ZĄĆĘŁŃÓŚŹŻ])\*\*[ \t]*\n[ \t]*\n(?=[^\s#*![>|-])/g;

/** Łączy inicjały z akapitem: `zamien(litera, osobne)` zwraca tekst wstawiany w miejsce inicjału. */
export function polaczInicjaly(tekst: string, wzorzec: RegExp, zamien: (litera: string, osobne: boolean) => string): string {
  return tekst.replace(wzorzec, (...a) => {
    const litera = a[1] as string, poz = a[a.length - 2] as number, calosc = a[a.length - 1] as string;
    return zamien(litera, osobneSlowo(litera, calosc.slice(poz + a[0].length, poz + a[0].length + 40)));
  });
}
