/**
 * Buduje „Czytelnię” na stronie GitHub Pages: docs/czytelnia/ – osobna, czytelna strona HTML dla każdego artykułu
 * (tekst bez zmian, z Markdownu w artykuly/) oraz spis wszystkich artykułów z wyszukiwarką.
 * Zdjęcia nie są kopiowane – ładują się z oryginalnych plików w repozytorium (zrodlo/).
 *
 * Uruchomienie: npx tsx scripts/czytelnia.ts   (po każdej zmianie artykułów, opracowań albo domeny)
 */
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { marked } from "marked";
import { Archiwum, type Dokument } from "../src/archiwum.js";

const archiwum = new Archiwum(".");
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

function trescHtml(a: Dokument): string {
  // inicjały: w oryginale duża litera w pływającej tabelce, a tekst akapitu zaczyna się tuż obok, bez spacji
  // (np. „**P**” i osobny akapit „ora kończyć…”) – łączymy je z powrotem w jeden akapit
  const md = a.tresc.replace(/\*\*([A-ZĄĆĘŁŃÓŚŹŻ])\*\*[ \t]*\n[ \t]*\n(?=[^\s#*![>|-])/g, '<span class="inicjal">$1</span>');
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
  html = html.replace(/<a href="(https?:\/\/[^"]+)"/g, '<a href="$1" rel="noopener" target="_blank"');
  return html;
}

const glowa = (o: { tytul: string; opis: string; url: string; obraz?: string; css: string }) => `<!doctype html>
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
<link rel="stylesheet" href="${o.css}">
</head>
<body>
<header class="gora"><div class="wrap-sz">
  <a class="logo" href="../">uleszka<span>.net</span> · archiwum</a>
  <nav><a href="./">Czytelnia</a><a href="../#jak-zaczac">Porozmawiaj z AI</a></nav>
</div></header>
`;

const stopka = `<footer><div class="wrap-sz">
  <p>Teksty: Leszek Klimek, uleszka.net (ok. 2004–2007), przeniesione bez zmian. Treści należą do autora i jego spadkobierców; archiwum ma charakter dokumentacyjny i niekomercyjny.
  Opracowania i opisy zdjęć przygotowała AI. <a href="${REPO}">Archiwum na GitHubie</a> · <a href="${REPO}/issues">zgłoś uwagę</a></p>
</div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
  document.querySelectorAll("[data-kopiuj]").forEach((el) => el.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(el.dataset.kopiuj); } catch {}
    const t = document.getElementById("toast"); t.textContent = "Skopiowano ✓"; t.classList.add("widoczny");
    setTimeout(() => t.classList.remove("widoczny"), 1800);
  }));
</script>
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
  const prosba = `Omów artykuł „${a.tytul}” (id: ${a.id}) z archiwum uleszka.net: przedstaw wiernie tezy autora z cytatami, a potem porównaj je z tym, co wiadomo dziś.`;

  const html =
    glowa({ tytul: `${a.tytul} – Leszek Klimek, uleszka.net`, opis, url: `${BAZA}czytelnia/${plikArt(a)}`, obraz: pierwszyObraz ? rawUrl(pierwszyObraz.sciezka) : undefined, css: "czytelnia.css" }) +
    `<main class="wrap-czyt">
  <p class="okruszki"><a href="./">Czytelnia</a> › <a href="./#${slug(a.dzial)}">${esc(a.dzial)}</a>${rodzic ? ` › <a href="${plikArt(rodzic)}">${esc(rodzic.tytul)}</a>` : ""}</p>
  <h1>${esc(a.tytul)}</h1>
  <p class="meta">Leszek Klimek · uleszka.net · tekst bez zmian względem oryginału</p>
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
${trescHtml(a)}
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
  <p class="zrodla-art">Oryginał: <a href="${esc(a.adresOryginalny)}" rel="noopener" target="_blank">${esc(a.adresOryginalny)}</a> (strona już nie istnieje) · <a href="${REPO}/blob/main/${a.plik.split("/").map(encodeURIComponent).join("/")}">tekst w repozytorium</a></p>
  <nav class="poprz-nast">
    ${poprz ? `<a class="poprz" href="${plikArt(poprz)}"><span>← poprzedni</span>${esc(poprz.tytul)}</a>` : "<span></span>"}
    ${nast ? `<a class="nast" href="${plikArt(nast)}"><span>następny →</span>${esc(nast.tytul)}</a>` : "<span></span>"}
  </nav>
</main>
` +
    stopka;
  writeFileSync(`${WYJSCIE}/${plikArt(a)}`, html, "utf8");
});

// ---------- spis treści ----------
const wpis = (a: Dokument) => {
  const o = archiwum.opracowania.get(a.id);
  const krotko = (o?.streszczenie ?? "").replace(/\s+/g, " ").trim();
  const zdanie = krotko.length > 170 ? krotko.slice(0, krotko.lastIndexOf(" ", 165)) + "…" : krotko;
  return `<li class="${a.rodzic ? "pod" : ""}" data-szukaj="${esc((a.tytul + " " + krotko + " " + (o?.tematy ?? []).join(" ")).toLowerCase())}"><a href="${plikArt(a)}"><b>${esc(a.tytul)}</b>${zdanie ? `<span>${esc(zdanie)}</span>` : ""}</a></li>`;
};
const spis =
  glowa({ tytul: "Czytelnia – wszystkie artykuły uleszka.net", opis: `Wszystkie ${lista.length} artykuły strony uleszka.net Leszka Klimka, słowo w słowo, w wygodnej formie do czytania.`, url: `${BAZA}czytelnia/`, css: "czytelnia.css" }) +
  `<main class="wrap-czyt spis">
  <p class="okruszki"><a href="../">Strona główna</a> › Czytelnia</p>
  <h1>Czytelnia</h1>
  <p class="meta">Wszystkie ${lista.length} strony uleszka.net, słowo w słowo. Krótkie opisy pod tytułami przygotowała AI.</p>
  <input id="szukaj" type="search" placeholder="Szukaj w tytułach i tematach, np. potop, Atlantyda, witamina…" aria-label="Szukaj artykułu">
${archiwum.dzialy
  .map((d) => {
    const art = lista.filter((a) => a.dzial === d);
    return `  <section class="dzial" id="${slug(d)}">
    <h2>${esc(d)} <small>${art.length}</small></h2>
    <ul>${art.map(wpis).join("")}</ul>
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
    document.querySelectorAll(".dzial li").forEach((li) => {
      const ok = !q || zloz(li.dataset.szukaj).includes(q);
      li.hidden = !ok;
      if (ok) ile++;
    });
    document.querySelectorAll(".dzial").forEach((s) => (s.hidden = ![...s.querySelectorAll("li")].some((li) => !li.hidden)));
    document.getElementById("brak").hidden = ile > 0;
  });
</script>
` +
  stopka;
writeFileSync(`${WYJSCIE}/index.html`, spis, "utf8");

// ---------- styl ----------
writeFileSync(
  `${WYJSCIE}/czytelnia.css`,
  `:root { color-scheme: dark; --tlo: #07090f; --karta: #10151f; --tekst: #ece6d8; --tekst-2: #a6adbb; --linia: #222b3b; --akcent: #e2a93f; --akcent-mocny: #f0c46f; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: radial-gradient(ellipse 80% 40% at 50% 0%, rgba(30, 48, 90, .25), transparent 70%), var(--tlo); color: var(--tekst);
  font: 17px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; -webkit-text-size-adjust: 100%; }
a { color: var(--akcent-mocny); }
.wrap-sz { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
.wrap-czyt { max-width: 760px; margin: 0 auto; padding: 0 20px 40px; }
.gora { position: sticky; top: 0; z-index: 5; background: rgba(7, 9, 15, .82); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255, 255, 255, .06); }
.gora .wrap-sz { display: flex; justify-content: space-between; align-items: center; gap: 12px; height: 56px; }
.logo { font-family: Georgia, serif; font-weight: 700; color: #f4efe4; text-decoration: none; }
.logo span { color: #e8b04b; }
.gora nav { display: flex; gap: 18px; font-size: 15px; }
.gora nav a { color: #cfd6e4; text-decoration: none; }
.gora nav a:hover { color: #fff; }
.okruszki { margin: 34px 0 8px; font-size: 14px; color: var(--tekst-2); }
.okruszki a { color: var(--tekst-2); }
h1 { font-family: Georgia, serif; font-size: clamp(32px, 6vw, 50px); line-height: 1.1; margin: 0 0 10px;
  background: linear-gradient(180deg, #fff6e0, #f0c46f 60%, #b47a22); -webkit-background-clip: text; background-clip: text; color: transparent; }
.meta { color: var(--tekst-2); font-size: 14px; margin: 0 0 26px; }
.skrot { background: var(--karta); border: 1px solid var(--linia); border-radius: 14px; padding: 14px 18px; margin: 0 0 30px; }
.skrot summary { cursor: pointer; font-weight: 600; }
.skrot summary span { font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--akcent); margin-left: 8px; font-weight: 700; }
.skrot p, .skrot li { color: var(--tekst-2); font-size: 15px; }
.skrot .uwaga { font-size: 13px; font-style: italic; }
.tresc { font-family: Georgia, "Times New Roman", serif; font-size: 19px; line-height: 1.75; color: #e4ddcd; overflow-wrap: break-word; }
.tresc p { margin: 0 0 1.05em; }
.tresc strong { color: #fbf3e0; }
.tresc h1, .tresc h2, .tresc h3 { font-family: Georgia, serif; color: #f4efe4; line-height: 1.25; }
.tresc img { display: block; max-width: 100%; height: auto; margin: 1.4em auto; border-radius: 6px; box-shadow: 0 10px 30px rgba(0, 0, 0, .45); background: #fff; }
.tresc a img { display: inline-block; margin: .3em; box-shadow: none; background: none; }
.tresc hr { border: 0; height: 1px; margin: 2.2em auto; width: 40%; background: linear-gradient(90deg, transparent, rgba(232, 176, 75, .6), transparent); }
.tresc blockquote { margin: 1.2em 0; padding: .2em 0 .2em 1em; border-left: 3px solid var(--akcent); color: #d6cfbf; }
.tresc ul, .tresc ol { padding-left: 1.3em; }
.tresc table { border-collapse: collapse; width: 100%; font-size: 16px; }
.tresc td, .tresc th { border: 1px solid var(--linia); padding: 6px 8px; }
.inicjal { float: left; font-size: 3.1em; line-height: .85; margin: .06em .1em 0 0; color: #f0c46f; font-weight: 700; }
.podstrony, .zapytaj { background: var(--karta); border: 1px solid var(--linia); border-radius: 14px; padding: 16px 20px; margin: 30px 0 16px; }
.podstrony h2 { font-family: Georgia, serif; font-size: 20px; margin: 0 0 8px; }
.zapytaj p { margin: 6px 0 12px; color: var(--tekst-2); font-size: 15px; }
.pytanie { width: 100%; text-align: left; background: #0b0f17; border: 1px solid var(--linia); border-radius: 12px; padding: 12px 14px; color: var(--tekst);
  font: 15px/1.5 system-ui, sans-serif; cursor: pointer; display: flex; justify-content: space-between; gap: 12px; }
.pytanie:hover { border-color: var(--akcent); }
.kop { font-size: 13px; color: var(--akcent-mocny); font-weight: 600; white-space: nowrap; }
.zrodla-art { font-size: 14px; color: var(--tekst-2); overflow-wrap: anywhere; }
.poprz-nast { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 28px; }
.poprz-nast a { display: block; background: var(--karta); border: 1px solid var(--linia); border-radius: 12px; padding: 12px 14px; text-decoration: none; color: var(--tekst); }
.poprz-nast a:hover { border-color: var(--akcent); }
.poprz-nast span { display: block; font-size: 12px; color: var(--akcent); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 2px; }
.poprz-nast .nast { text-align: right; }
.spis input { width: 100%; padding: 14px 16px; border-radius: 12px; border: 1px solid var(--linia); background: var(--karta); color: var(--tekst); font-size: 16px; margin: 0 0 22px; }
.spis input:focus { outline: 2px solid rgba(232, 176, 75, .5); }
.dzial h2 { font-family: Georgia, serif; font-size: 26px; margin: 30px 0 10px; }
.dzial h2 small { font-size: 14px; color: var(--tekst-2); font-family: system-ui, sans-serif; }
.dzial ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
.dzial li a { display: block; padding: 12px 14px; border-radius: 12px; background: var(--karta); border: 1px solid var(--linia); text-decoration: none; color: var(--tekst); }
.dzial li a:hover { border-color: var(--akcent); }
.dzial li.pod { margin-left: 22px; }
.dzial li b { display: block; font-family: Georgia, serif; font-size: 18px; color: #f4efe4; }
.dzial li span { display: block; font-size: 14px; color: var(--tekst-2); margin-top: 2px; }
.brak { color: var(--tekst-2); }
footer { margin-top: 50px; padding: 26px 0 40px; border-top: 1px solid var(--linia); color: var(--tekst-2); font-size: 14px; }
.toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%) translateY(20px); opacity: 0; transition: .2s; background: #e8b04b; color: #14110a;
  font-weight: 600; padding: 10px 18px; border-radius: 999px; pointer-events: none; }
.toast.widoczny { opacity: 1; transform: translateX(-50%); }
@media (max-width: 640px) {
  .tresc { font-size: 18px; }
  .poprz-nast { grid-template-columns: 1fr; }
  .poprz-nast .nast { text-align: left; }
  .gora nav { gap: 12px; font-size: 14px; }
  .gora nav a { white-space: nowrap; }
  .logo { font-size: 15px; white-space: nowrap; }
  .dzial li.pod { margin-left: 12px; }
}
`,
  "utf8",
);

console.log(`Czytelnia: ${lista.length} artykułów + spis w ${WYJSCIE}/ (adres bazowy ${BAZA})`);
