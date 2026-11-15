/**
 * Menu górne wspólne dla czytelni i atlasu (strona główna ma je wpisane w docs/index.html).
 * Na szerokich ekranach linki są w pasku, na wąskich chowają się pod „hamburgerem” (docs/menu.js).
 */
export type Sekcja = "czytelnia" | "atlas";

const LINKI: { klucz: Sekcja | ""; tekst: string; href: string }[] = [
  { klucz: "czytelnia", tekst: "Czytelnia", href: "../czytelnia/" },
  { klucz: "atlas", tekst: "Atlas", href: "../atlas/" },
  { klucz: "", tekst: "Podcast", href: "../#podcast" },
  { klucz: "", tekst: "Rozmowa z AI", href: "../#jak-zaczac" },
  { klucz: "", tekst: "O stronie", href: "../#o-stronie" },
];

/** linki menu (panel chowany na telefonie); aktywna sekcja oznaczona aria-current */
export const menuLinki = (aktywna: Sekcja) =>
  `<div class="menu-linki" id="menu-linki">${LINKI.map((l) => `<a href="${l.href}"${l.klucz === aktywna ? ' aria-current="page"' : ""}>${l.tekst}</a>`).join("")}</div>`;

/** przycisk otwierający menu na wąskich ekranach */
export const hamburger = `<button class="hamburger" type="button" aria-expanded="false" aria-controls="menu-linki" aria-label="Otwórz menu"><span></span><span></span><span></span></button>`;
