/**
 * Buduje „Czytelnię” na stronie GitHub Pages: docs/czytelnia/ – osobna, czytelna strona HTML dla każdego artykułu
 * (tekst bez zmian, z Markdownu w artykuly/) oraz spis wszystkich artykułów z wyszukiwarką.
 * Zdjęcia nie są kopiowane – ładują się z oryginalnych plików w repozytorium (zrodlo/).
 *
 * Uruchomienie: npx tsx scripts/czytelnia.ts   (po każdej zmianie artykułów, opracowań albo domeny)
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { marked } from "marked";
import { Archiwum, type Dokument } from "../src/archiwum.js";
import { poprawHtml, popraw, tekstBazowy, wczytajErrate } from "./lib/errata.js";
import { INICJAL_MD, polaczInicjaly } from "./lib/inicjaly.js";

const archiwum = new Archiwum(".");
const errata = wczytajErrate(".");
let poprawekRazem = 0, poprawekPominietych = 0;
const WYJSCIE = "docs/czytelnia";
const REPO = "https://github.com/jokerwader/uleszka-archiwum";
const RAW = "https://raw.githubusercontent.com/jokerwader/uleszka-archiwum/main/";
// adres strony: własna domena z docs/CNAME, a bez niej GitHub Pages
const DOMENA = existsSync("docs/CNAME") ? readFileSync("docs/CNAME", "utf8").trim() : "";
const BAZA = DOMENA ? `https://${DOMENA}/` : "https://jokerwader.github.io/uleszka-archiwum/";

const slug = (s: string) =>
  s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const plikArt = (a: Dokument) => `${slug(a.id)}.html`;
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const poId = new Map(archiwum.artykuly.map((a) => [a.id, a]));
const rawUrl = (sciezka: string) => RAW + sciezka.split("/").map(encodeURIComponent).join("/");

marked.setOptions({ gfm: true, breaks: false });

function trescHtml(a: Dokument): { html: string; rozdzialy: { id: string; tytul: string }[] } {
  // inicjały: w oryginale duża litera w pływającej tabelce, a tekst akapitu zaczyna się tuż obok, bez spacji
  // (np. „**P**” i osobny akapit „ora kończyć…”) – łączymy je z powrotem w jeden akapit
  // – chyba że inicjał jest osobnym słowem („W Polsce”), wtedy zostaje spacja
  const md = polaczInicjaly(a.tresc, INICJAL_MD, (l, osobne) => `<span class="inicjal">${l}</span>${osobne ? " " : ""}`);
  let html = marked.parse(md, { async: false }) as string;
  // obrazy: z repozytorium, z opisem AI jako tekstem alternatywnym
  html = html.replace(/<img src="(zrodlo\/[^"]+)" alt="([^"]*)"/g, (_m, src: string, alt: string) => {
    const opis = archiwum.opisObrazu(src);
    const tekstAlt = alt || opis || "";
    return `<img src="${rawUrl(src)}" alt="${esc(tekstAlt)}"${opis ? ` title="${esc("Opis AI: " + opis)}"` : ""} loading="lazy" decoding="async"`;
  });
  // linki do innych artykułów i do plików repozytorium
  html = html.replace(/href="artykul:([^"]+)"/g, (_m, id: string) => {
    const cel = poId.get(id);
    return cel ? `href="${plikArt(cel)}"` : `href="./"`;
  });
  html = html.replace(/href="((?:zrodlo|artykuly)\/[^"]+)"/g, (_m, p: string) => `href="${REPO}/blob/main/${p.split("/").map(encodeURIComponent).join("/")}"`);
  // odnośniki do spisu działów (KATALOG.md#dział) – w czytelni prowadzą do działu w spisie artykułów
  html = html.replace(/href="(?:\.\.\/)*KATALOG\.md(?:#([^"]*))?"/g, (_m, kotwica?: string) => `href="./${kotwica ? "#" + slug(decodeURIComponent(kotwica)) : ""}"`);
  html = html.replace(/<a href="(https?:\/\/[^"]+)"/g, '<a href="$1" rel="noopener" target="_blank"');
  // tabele w przewijanym pudełku (szerokie tabele nie rozpychają strony na telefonie)
  html = html.replace(/<table>/g, '<div class="tabela"><table>').replace(/<\/table>/g, "</table></div>");
  // galerie: co najmniej dwa kolejne akapity złożone z samego zdjęcia (lub kilku), ewentualnie z krótkim podpisem pod spodem
  // – układamy je w siatkę zamiast długiej kolumny (tylko wygląd, tekst bez zmian)
  const obraz = String.raw`(?:<a [^>]*>)?<img [^>]*>(?:<\/a>)?`;
  const akapitZdjecia = String.raw`<p>${obraz}(?:\s*${obraz})*(?:<br>\s*(?:[^<]|<\/?(?:strong|em)>){1,90})?<\/p>`;
  html = html.replace(new RegExp(String.raw`(?:${akapitZdjecia}\s*){2,}`, "g"), (m) => `<div class="galeria">${m}</div>\n`);
  const rozdzialy: { id: string; tytul: string }[] = [];
  html = html.replace(/<(h[1-4])>([^<]{2,140})<\/h[1-4]>|<p><strong>([^<]{3,140})<\/strong><\/p>/g, (m, tag: string | undefined, h: string | undefined, b: string | undefined) => {
    const tytul = (h ?? b ?? "").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
    if (!/\p{L}/u.test(tytul)) return m;
    const id = `r-${rozdzialy.length + 1}`;
    rozdzialy.push({ id, tytul });
    return tag ? `<${tag} class="rozdzial" id="${id}">${h}</${tag}>` : `<p class="rozdzial" id="${id}"><strong>${b}</strong></p>`;
  });
  return { html, rozdzialy };
}

/** Panel spisu treści: rozdziały bieżącego artykułu i wszystkie artykuły (dział bieżącego artykułu rozwinięty). */
function spisHtml(aktualny?: Dokument, rozdzialy: { id: string; tytul: string }[] = []) {
  const czesc1 = rozdzialy.length
    ? `<h3>W tym artykule</h3><ol>${rozdzialy.map((r) => `<li><a href="#${r.id}">${esc(r.tytul)}</a></li>`).join("")}</ol>`
    : "";
  const czesc2 = archiwum.dzialy
    .map((d) => {
      const art = archiwum.artykuly.filter((a) => a.dzial === d);
      const otwarty = aktualny ? aktualny.dzial === d : false;
      return `<details${otwarty ? " open" : ""}><summary>${esc(d)} <small>${art.length}</small></summary><ul>${art
        .map((a) => `<li class="${a.rodzic ? "pod" : ""}"><a href="${plikArt(a)}"${aktualny?.id === a.id ? ' class="aktualny" aria-current="page"' : ""}>${esc(a.tytul)}</a></li>`)
        .join("")}</ul></details>`;
    })
    .join("");
  return `${czesc1}<h3>Wszystkie artykuły</h3>${czesc2}`;
}

const glowa = (o: { tytul: string; opis: string; url: string; obraz?: string; css: string; spis: string }) => `<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(o.tytul)}</title>
<meta name="description" content="${esc(o.opis)}">
<meta property="og:type" content="article">
<meta property="og:locale" content="pl_PL">
<meta property="og:title" content="${esc(o.tytul)}">
<meta property="og:description" content="${esc(o.opis)}">
<meta property="og:url" content="${o.url}">
<meta property="og:image" content="${o.obraz ?? BAZA + "og.png"}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="../favicon.png">
<script>
  // motyw i wielkość tekstu ustawiane przed wyświetleniem strony (bez mignięcia); domyślnie sepia
  try {
    document.documentElement.dataset.motyw = localStorage.getItem("uleszka-motyw") || "sepia";
    const r = localStorage.getItem("uleszka-rozmiar");
    if (r) document.documentElement.style.setProperty("--rozmiar", r + "px");
  } catch { document.documentElement.dataset.motyw = "sepia"; }
</script>
<link rel="stylesheet" href="${o.css}">
</head>
<body>
<header class="gora"><div class="wrap-sz">
  <a class="logo" href="../">uleszka<span>.net</span><span class="tylko-szeroki" style="color:inherit"> · archiwum</span></a>
  <nav>
    <button class="przycisk-gora" id="przycisk-spisu" type="button" aria-expanded="false" aria-controls="spis-panel">☰ Spis treści</button>
    <button class="przycisk-gora" id="przycisk-wygladu" type="button" aria-expanded="false" aria-controls="panel-wygladu" title="Kolory i wielkość tekstu"><b>Aa</b></button>
    <a class="tylko-szeroki" href="../#jak-zaczac">Porozmawiaj z AI</a>
  </nav>
</div></header>
<div class="panel-wygladu" id="panel-wygladu" hidden>
  <p>Kolory</p>
  <div class="motywy">
    <button type="button" data-motyw="sepia"><span>Aa</span>Sepia</button>
    <button type="button" data-motyw="jasny"><span>Aa</span>Jasny</button>
    <button type="button" data-motyw="ciemny"><span>Aa</span>Ciemny</button>
    <button type="button" data-motyw="kontrast"><span>Aa</span>Kontrast</button>
  </div>
  <p>Wielkość tekstu</p>
  <div class="rozmiary"><button type="button" data-rozmiar="-1" aria-label="Mniejszy tekst">A−</button><span id="rozmiar-wart">100%</span><button type="button" data-rozmiar="1" aria-label="Większy tekst">A+</button></div>
</div>
<div class="zaslona" id="zaslona" hidden></div>
<aside class="spis-panel" id="spis-panel" hidden aria-label="Spis treści">
  <div class="spis-glowa"><b>Spis treści</b><button type="button" id="zamknij-spis" aria-label="Zamknij spis treści">✕</button></div>
  ${o.spis}
</aside>
`;

const stopka = `<footer><div class="wrap-sz">
  <p>Teksty: Leszek Klimek, uleszka.net (ok. 2004–2007), przeniesione bez zmian. Treści należą do autora i jego spadkobierców; archiwum ma charakter dokumentacyjny i niekomercyjny.
  Opracowania i opisy zdjęć przygotowała AI. <a href="${REPO}">Archiwum na GitHubie</a> · <a href="${REPO}/issues">zgłoś uwagę</a></p>
</div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="czytelnia.js" defer></script>
</body>
</html>
`;

rmSync(WYJSCIE, { recursive: true, force: true });
mkdirSync(WYJSCIE, { recursive: true });

const lista = archiwum.artykuly;
lista.forEach((a, i) => {
  const o = archiwum.opracowania.get(a.id);
  const opis = (o?.streszczenie ?? a.czysty).replace(/\s+/g, " ").trim().slice(0, 180);
  const rodzic = a.rodzic ? poId.get(a.rodzic) : undefined;
  const podstrony = archiwum.podstrony(a);
  const poprz = lista[i - 1];
  const nast = lista[i + 1];
  const pierwszyObraz = a.obrazy.find((x) => /\.(jpe?g|png)$/i.test(x.sciezka) && archiwum.opisObrazu(x.sciezka));
  const ksiazki = archiwum.ksiazkiArtykulu(a.id);
  const { html: tresc0, rozdzialy } = trescHtml(a);
  // oczywiste literówki poprawione według erraty; oryginalny zapis widać po najechaniu na podkreślone słowo
  const { html: tresc, uzyte } = poprawHtml(tresc0, a.id, errata);
  const ilePoprawek = [...uzyte.values()].reduce((x, y) => x + y, 0);
  const oczekiwane = [...popraw(tekstBazowy(a.czysty), a.id, errata).uzyte.values()].reduce((x, y) => x + y, 0);
  poprawekRazem += ilePoprawek;
  poprawekPominietych += Math.max(0, oczekiwane - ilePoprawek);
  const prosba = `Omów artykuł „${a.tytul}” (id: ${a.id}) z archiwum uleszka.net: przedstaw wiernie tezy autora z cytatami, a potem porównaj je z tym, co wiadomo dziś.`;

  const html =
    glowa({ tytul: `${a.tytul} – Leszek Klimek, uleszka.net`, opis, url: `${BAZA}czytelnia/${plikArt(a)}`, obraz: pierwszyObraz ? rawUrl(pierwszyObraz.sciezka) : undefined, css: "czytelnia.css", spis: spisHtml(a, rozdzialy) }) +
    `<main class="wrap-czyt">
  <p class="okruszki"><a href="./">Czytelnia</a> › <a href="./#${slug(a.dzial)}">${esc(a.dzial)}</a>${rodzic ? ` › <a href="${plikArt(rodzic)}">${esc(rodzic.tytul)}</a>` : ""}</p>
  <h1>${esc(a.tytul)}</h1>
  <p class="meta">Leszek Klimek · uleszka.net · tekst bez zmian względem oryginału${ilePoprawek ? ` <span class="meta-poprawki" title="Podkreślone słowa: najedź (albo dotknij), żeby zobaczyć zapis z oryginału.">· poprawiono ${ilePoprawek} ${ilePoprawek === 1 ? "oczywistą literówkę" : ilePoprawek % 10 >= 2 && ilePoprawek % 10 <= 4 && (ilePoprawek % 100 < 10 || ilePoprawek % 100 >= 20) ? "oczywiste literówki" : "oczywistych literówek"}</span>` : ""}</p>
  <div class="odtwarzacz" id="odtwarzacz" hidden>
    <button class="graj" id="graj" type="button" aria-label="Posłuchaj artykułu"><span class="ikona-graj" aria-hidden="true"></span><span id="graj-tekst">Posłuchaj</span></button>
    <button class="stop" id="stop" type="button" aria-label="Zatrzymaj i wróć na początek" hidden>■</button>
    <label class="tempo">tempo <select id="tempo"><option value="0.85">0,85×</option><option value="1" selected>1×</option><option value="1.15">1,15×</option><option value="1.3">1,3×</option><option value="1.5">1,5×</option></select></label>
    <label class="glos">głos <select id="glos"></select></label>
    <span class="postep" id="postep"></span>
    <p class="wskazowka-glos" id="wskazowka-glos" hidden></p>
  </div>
${
  o && o.streszczenie
    ? `  <details class="skrot">
    <summary>W skrócie <span>opracowanie AI</span></summary>
    <p>${esc(o.streszczenie)}</p>
${o.tezy.length ? `    <ul>${o.tezy.slice(0, 6).map((t) => `<li>${esc(t.teza)}</li>`).join("")}</ul>\n` : ""}    <p class="uwaga">Przygotowała sztuczna inteligencja; nie jest częścią oryginalnej strony. Poniżej pełny, oryginalny tekst.</p>
  </details>
`
    : ""
}  <article class="tresc">
${tresc}
  </article>
${
  podstrony.length
    ? `  <nav class="podstrony"><h2>Dalsze części i podstrony</h2><ul>${podstrony.map((p) => `<li><a href="${plikArt(p)}">${esc(p.tytul)}</a></li>`).join("")}</ul></nav>\n`
    : ""
}${
  ksiazki.length
    ? `  <p class="zrodla-art">Źródła cytowane w artykule, dostępne w bibliotece archiwum: ${ksiazki.map((k) => `<a href="${REPO}/blob/main/biblioteka/${k.id}.md">${esc(k.tytul)}</a>`).join(", ")}.</p>\n`
    : ""
}  <div class="zapytaj">
    <b>Porozmawiaj o tym artykule z AI</b>
    <p>Kliknij, żeby skopiować prośbę, i wklej ją w rozmowie z asystentem, który ma podłączone archiwum. <a href="../#jak-zaczac">Jak podłączyć →</a></p>
    <button class="pytanie" data-kopiuj="${esc(prosba)}">${esc(prosba)}<span class="kop">kopiuj</span></button>
  </div>
  <p class="zrodla-art">Pierwotny adres: <span class="stary-adres">${esc(a.adresOryginalny)}</span> · <a href="https://web.archive.org/web/2007/${esc(a.adresOryginalny)}" rel="noopener" target="_blank">kopia z 2007 r. w Internet Archive</a> · <a href="${REPO}/blob/main/${a.plik.split("/").map(encodeURIComponent).join("/")}">tekst w repozytorium</a> · <a href="${REPO}/blob/main/${(a.meta.plik_zrodlowy as string).split("/").map(encodeURIComponent).join("/")}">oryginalny plik HTML</a></p>
  <nav class="poprz-nast">
    ${poprz ? `<a class="poprz" href="${plikArt(poprz)}"><span>← poprzedni</span>${esc(poprz.tytul)}</a>` : "<span></span>"}
    ${nast ? `<a class="nast" href="${plikArt(nast)}"><span>następny →</span>${esc(nast.tytul)}</a>` : "<span></span>"}
  </nav>
</main>
` +
    stopka.replace("</body>", `<script src="czytaj.js" defer></script>\n</body>`);
  writeFileSync(`${WYJSCIE}/${plikArt(a)}`, html, "utf8");
});

// ---------- spis treści: karty artykułów (na komputerze w kilku kolumnach, na telefonie jedna pod drugą) ----------
const czasCzytania = (a: Dokument) => Math.max(1, Math.round(a.czysty.split(/\s+/).length / 200));
const miniatura = (a: Dokument) => {
  // pierwsze zdjęcie artykułu (albo jego podstron), które ma opis AI – czyli nie jest ozdobnikiem
  for (const d of [a, ...archiwum.podstrony(a)])
    for (const o of d.obrazy) if (/\.(jpe?g|png)$/i.test(o.sciezka) && archiwum.opisObrazu(o.sciezka)) return o.sciezka;
  return undefined;
};
const karta = (a: Dokument) => {
  const o = archiwum.opracowania.get(a.id);
  const krotko = (o?.streszczenie ?? "").replace(/\s+/g, " ").trim();
  const podstrony = archiwum.podstrony(a);
  const min = miniatura(a);
  const zdjec = a.obrazy.filter((x) => archiwum.opisObrazu(x.sciezka)).length;
  const szukaj = [a.tytul, krotko, ...(o?.tematy ?? []), ...podstrony.map((p) => p.tytul)].join(" ").toLowerCase();
  const meta = [`${czasCzytania(a)} min czytania`, zdjec ? `${zdjec} ${zdjec === 1 ? "zdjęcie" : zdjec < 5 ? "zdjęcia" : "zdjęć"}` : "", podstrony.length ? `+ ${podstrony.length} ${podstrony.length < 5 ? "części" : "części"}` : ""]
    .filter(Boolean)
    .join(" · ");
  return `<li class="karta-art" data-szukaj="${esc(szukaj)}">
      <a class="karta-link" href="${plikArt(a)}">
        <div class="miniatura">${min ? `<img src="${rawUrl(min)}" alt="" loading="lazy" decoding="async">` : `<span aria-hidden="true">${esc(a.tytul.trim().charAt(0))}</span>`}</div>
        <div class="karta-tresc"><b>${esc(a.tytul)}</b>${krotko ? `<span class="opis">${esc(krotko)}</span>` : ""}<span class="meta-art">${meta}</span></div>
      </a>${
        podstrony.length
          ? `\n      <div class="czesci"><span>Dalsze części:</span>${podstrony.map((p) => `<a href="${plikArt(p)}">${esc(p.tytul)}</a>`).join("")}</div>`
          : ""
      }
    </li>`;
};
const spis =
  glowa({ tytul: "Czytelnia – wszystkie artykuły uleszka.net", opis: `Wszystkie ${lista.length} strony uleszka.net Leszka Klimka, słowo w słowo, w wygodnej formie do czytania.`, url: `${BAZA}czytelnia/`, css: "czytelnia.css", spis: spisHtml() }) +
  `<main class="wrap-szeroki spis">
  <p class="okruszki"><a href="../">Strona główna</a> › Czytelnia</p>
  <h1>Czytelnia</h1>
  <p class="meta">Wszystkie ${lista.length} strony uleszka.net, słowo w słowo. Krótkie opisy na kartach przygotowała AI.</p>
  <div class="spis-narzedzia">
    <input id="szukaj" type="search" placeholder="Szukaj w tytułach i tematach, np. potop, Atlantyda, witamina…" aria-label="Szukaj artykułu">
    <nav class="dzialy-skrot" aria-label="Działy">${archiwum.dzialy.map((d) => `<a href="#${slug(d)}">${esc(d)}</a>`).join("")}</nav>
  </div>
${archiwum.dzialy
  .map((d) => {
    const glowne = lista.filter((a) => a.dzial === d && !a.rodzic);
    const wszystkich = lista.filter((a) => a.dzial === d).length;
    return `  <section class="dzial" id="${slug(d)}">
    <h2>${esc(d)} <small>${glowne.length} ${glowne.length === 1 ? "artykuł" : glowne.length < 5 ? "artykuły" : "artykułów"}${wszystkich > glowne.length ? ` · ${wszystkich} stron` : ""}</small></h2>
    <ul class="karty">${glowne.map(karta).join("")}</ul>
  </section>`;
  })
  .join("\n")}
  <p class="brak" id="brak" hidden>Nic nie znaleziono. Spróbuj innego słowa albo zapytaj AI – ono szuka także po znaczeniu.</p>
</main>
<script>
  const pole = document.getElementById("szukaj");
  const zloz = (s) => s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  pole.addEventListener("input", () => {
    const q = zloz(pole.value.trim());
    let ile = 0;
    document.querySelectorAll(".karta-art").forEach((k) => {
      const ok = !q || zloz(k.dataset.szukaj).includes(q);
      k.hidden = !ok;
      if (ok) ile++;
    });
    document.querySelectorAll(".dzial").forEach((s) => (s.hidden = ![...s.querySelectorAll(".karta-art")].some((k) => !k.hidden)));
    document.getElementById("brak").hidden = ile > 0;
  });
</script>
` +
  stopka;
writeFileSync(`${WYJSCIE}/index.html`, spis, "utf8");

// ---------- styl i skrypty (pliki źródłowe w scripts/czytelnia/) ----------
for (const plik of ["czytelnia.css", "czytelnia.js", "czytaj.js"]) copyFileSync(`scripts/czytelnia/${plik}`, `${WYJSCIE}/${plik}`);

console.log(`Czytelnia: ${lista.length} artykułów + spis w ${WYJSCIE}/ (adres bazowy ${BAZA})`);
console.log(`Errata: poprawiono ${poprawekRazem} miejsc${poprawekPominietych ? `, ${poprawekPominietych} nie dało się nanieść w HTML (fragment przecina formatowanie)` : ""}`);
