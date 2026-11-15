/**
 * Buduje „Atlas Leszka” na stronie: docs/atlas/index.html (mapa wszystkich miejsc z filtrami i listą)
 * oraz docs/atlas/<miejsce>.html (karta miejsca: co pisał Leszek, co mówią dziś badania, zdjęcia z jego artykułów,
 * współczesne zdjęcia z Wikimedia Commons, mini mapa, miejsca w pobliżu). Zapisuje też atlas/atlas.json dla serwera MCP.
 *
 * Dane: atlas/miejsca.json (ręczna lista) + atlas/dane.json (npx tsx scripts/atlas-pobierz.ts) + opracowania artykułów.
 * Uruchomienie: npx tsx scripts/atlas.ts   (po czytelni – korzysta z docs/czytelnia/harmonogram.json)
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { Archiwum, type Dokument } from "../src/archiwum.js";
import { wczytajAtlas, slug, type MiejsceAtlasu } from "./lib/atlas.js";
import { hamburger, menuLinki } from "./lib/menu.js";

const archiwum = new Archiwum(".");
const { miejsca, rodzaje } = wczytajAtlas(archiwum);
const WYJSCIE = "docs/atlas";
const REPO = "https://github.com/jokerwader/uleszka-archiwum";
const RAW = "https://raw.githubusercontent.com/jokerwader/uleszka-archiwum/main/";
const DOMENA = existsSync("docs/CNAME") ? readFileSync("docs/CNAME", "utf8").trim() : "";
const BAZA = DOMENA ? `https://${DOMENA}/` : "https://jokerwader.github.io/uleszka-archiwum/";
const LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist/";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const rawUrl = (sciezka: string) => RAW + sciezka.split("/").map(encodeURIComponent).join("/");
const art = (id: string) => archiwum.znajdz(id, "artykul") as Dokument;
const urlArt = (id: string) => `../czytelnia/${slug(id)}.html`;
const skroc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1).replace(/\s+\S*$/, "") + "…" : s);

// podcast: odcinki (podcast/odcinki.json) i zaplanowane premiery (docs/czytelnia/harmonogram.json z czytelni)
type Odcinek = { nr: number; tytul: string; spotify?: string; youtube?: string; artykuly: string[] };
const odcinki: Odcinek[] = existsSync("podcast/odcinki.json") ? JSON.parse(readFileSync("podcast/odcinki.json", "utf8")) : [];
type Premiera = { nr: number; tytul: string; url: string; kiedy: string; iso: string };
const premiery: Premiera[] = existsSync("docs/czytelnia/harmonogram.json") ? JSON.parse(readFileSync("docs/czytelnia/harmonogram.json", "utf8")) : [];
const podcastMiejsca = (m: MiejsceAtlasu) => {
  for (const id of m.artykuly) {
    const o = odcinki.find((x) => x.artykuly.includes(id) && (x.spotify || x.youtube));
    if (o) return { o, id };
  }
  for (const id of m.artykuly) {
    const p = premiery.find((x) => x.url === `czytelnia/${slug(id)}.html`);
    if (p) return { p, id };
  }
  return null;
};

// data powstania z Wikidata („+1200-00-00T…”, „-2560-…”) po polsku
const kiedyPowstalo = (t: string) => {
  const r = t.match(/^([+-])0*(\d+)-/);
  if (!r) return "";
  const rok = Number(r[2]);
  return r[1] === "-" ? `ok. ${rok.toLocaleString("pl-PL")} p.n.e.` : rok < 1000 ? `${rok} n.e.` : `${rok}`;
};
const odleglosc = (a: MiejsceAtlasu, b: MiejsceAtlasu) => {
  const r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLon = (b.lon - a.lon) * r;
  const x = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLon / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(x));
};
const miniatura = (m: MiejsceAtlasu) => m.zdjeciaCommons[0]?.miniatura ?? (m.zdjeciaLeszka[0] ? rawUrl(m.zdjeciaLeszka[0].sciezka) : "");
const zgloszenie = (m?: MiejsceAtlasu) =>
  `${REPO}/issues/new?template=atlas.yml&title=${encodeURIComponent(m ? `[Atlas] ${m.nazwa}` : "[Atlas] Nowe miejsce: ")}`;

const glowa = (o: { tytul: string; opis: string; url: string; obraz?: string; mapa?: boolean }) => `<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(o.tytul)}</title>
<meta name="description" content="${esc(o.opis)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pl_PL">
<meta property="og:title" content="${esc(o.tytul)}">
<meta property="og:description" content="${esc(o.opis)}">
<meta property="og:url" content="${o.url}">
<meta property="og:image" content="${o.obraz ?? BAZA + "og.png"}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="../favicon.png">
<script>
  try { document.documentElement.dataset.motyw = localStorage.getItem("uleszka-motyw") || "sepia"; } catch { document.documentElement.dataset.motyw = "sepia"; }
</script>
<link rel="stylesheet" href="../czytelnia/czytelnia.css">
${o.mapa ? `<link rel="stylesheet" href="${LEAFLET}leaflet.css" crossorigin="">\n` : ""}<link rel="stylesheet" href="atlas.css">
</head>
<body>
<header class="gora"><div class="wrap-sz">
  <a class="logo" href="../">uleszka<span>.net</span><span class="tylko-szeroki" style="color:inherit"> · atlas</span></a>
  <nav aria-label="Menu główne">
    ${menuLinki("atlas")}
    ${hamburger}
  </nav>
</div></header>
`;
const stopka = (skrypty: string) => `<footer><div class="wrap-sz">
  <p>Teksty i zdjęcia z artykułów: Leszek Klimek, uleszka.net (ok. 2004–2007). Współczesne zdjęcia: Wikimedia Commons (autor i licencja przy każdym zdjęciu).
  Wstępy w części „Co mówią dziś badania”: Wikipedia (CC BY-SA 4.0). Położenie i opisy miejsc: Wikidata. Mapa: © autorzy OpenStreetMap.
  Opracowania i opisy zdjęć przygotowała AI. <a href="${REPO}">Archiwum na GitHubie</a> · <a href="${zgloszenie()}">zgłoś miejsce lub poprawkę</a></p>
</div></footer>
<dialog class="podglad" id="podglad"><form method="dialog"><button class="zamknij" aria-label="Zamknij">✕</button></form><img alt=""><p></p></dialog>
${skrypty}<script src="../menu.js" defer></script>
<script src="atlas.js" defer></script>
</body>
</html>
`;

const chip = (r: string) => `<span class="chip r-${r}">${esc(rodzaje[r] ?? r)}</span>`;
const fotoLeszka = (m: MiejsceAtlasu) =>
  m.zdjeciaLeszka.map((z) => `<figure><button type="button" class="powieksz" data-duze="${esc(rawUrl(z.sciezka))}" data-podpis="${esc(`${z.opis} · ${z.pochodzenie}`)}"><img src="${esc(rawUrl(z.sciezka))}" alt="${esc(z.opis)}" loading="lazy"></button>
      <figcaption>${esc(skroc(z.opis, 140))} <a href="${urlArt(z.artykul)}">${esc(art(z.artykul).tytul)}</a></figcaption></figure>`).join("\n    ");
const fotoCommons = (m: MiejsceAtlasu) =>
  m.zdjeciaCommons.map((z) => {
    const podpis = `fot. ${z.autor}${z.data ? `, ${z.data.slice(0, 4)}` : ""}, ${z.licencja}`;
    return `<figure><button type="button" class="powieksz" data-duze="${esc(z.duze)}" data-podpis="${esc(`${podpis} · Wikimedia Commons`)}"><img src="${esc(z.miniatura)}" alt="${esc(`${m.nazwa} – ${z.plik.replace(/\.[a-z]+$/i, "")}`)}" loading="lazy"></button>
      <figcaption>${esc(skroc(podpis, 120))} · <a href="${esc(z.strona)}" rel="noopener">źródło</a>${z.licencja_url ? ` · <a href="${esc(z.licencja_url)}" rel="noopener">licencja</a>` : ""}</figcaption></figure>`;
  }).join("\n    ");

rmSync(WYJSCIE, { recursive: true, force: true });
mkdirSync(WYJSCIE, { recursive: true });

// ---------- karty miejsc ----------
for (const m of miejsca) {
  const glowne = m.zdjeciaCommons[0];
  const pod = podcastMiejsca(m);
  const blisko = miejsca.filter((x) => x !== m).map((x) => ({ x, km: odleglosc(m, x) })).sort((a, b) => a.km - b.km).slice(0, 4);
  const opis = `${m.nazwa} w tekstach Leszka Klimka (uleszka.net): ${m.artykuly.length} ${m.artykuly.length === 1 ? "artykuł" : "artykuły"}, zdjęcia, mapa i to, co mówią dziś badania.`;
  const powstanie = kiedyPowstalo(m.powstanie);
  const leszek = m.artykuly.map((id) => {
    const a = art(id), o = archiwum.opracowania.get(id);
    const cyt = m.cytaty.filter((c) => c.artykul === id);
    return `<li><a class="tytul-art" href="${urlArt(id)}">${esc(a.tytul)}</a> <span class="dzial">${esc(a.dzial)}</span>
        ${o?.streszczenie ? `<p>${esc(skroc(o.streszczenie, 320))}</p>` : ""}
        ${cyt.map((c) => `<blockquote>„${esc(c.cytat)}”</blockquote>`).join("\n        ")}</li>`;
  }).join("\n      ");
  const html = glowa({ tytul: `${m.nazwa} – Atlas Leszka, uleszka.net`, opis, url: `${BAZA}atlas/${m.slug}.html`, obraz: glowne?.duze, mapa: true }) +
    `<main class="wrap-atlas">
  <p class="okruszki"><a href="./">Atlas</a> › ${m.rodzaje.map((r) => `<a href="./#${r}">${esc(rodzaje[r])}</a>`).join(" · ")}</p>
  <section class="naglowek-miejsca">
    ${glowne ? `<figure class="foto-glowne"><button type="button" class="powieksz" data-duze="${esc(glowne.duze)}" data-podpis="${esc(`fot. ${glowne.autor}, ${glowne.licencja} · Wikimedia Commons`)}"><img src="${esc(glowne.duze)}" alt="${esc(m.nazwa)}" fetchpriority="high"></button><figcaption>fot. ${esc(skroc(glowne.autor, 60))}, ${esc(glowne.licencja)} · <a href="${esc(glowne.strona)}" rel="noopener">Wikimedia Commons</a></figcaption></figure>` : ""}
    <div class="naglowek-tekst">
      <h1>${esc(m.nazwa)}</h1>
      <p class="chipy">${m.rodzaje.map(chip).join(" ")}</p>
      <p class="fakty">${m.opisWikidata ? `${esc(m.opisWikidata[0].toUpperCase() + m.opisWikidata.slice(1))}` : ""}${powstanie ? ` · powstanie: ${powstanie}` : ""}<br>${m.lat.toFixed(4)}, ${m.lon.toFixed(4)} · <a href="https://www.openstreetmap.org/?mlat=${m.lat}&amp;mlon=${m.lon}#map=14/${m.lat}/${m.lon}" rel="noopener">OpenStreetMap</a></p>
      ${pod ? `<p class="podcast-miejsca">🎧 ${"o" in pod && pod.o ? `W podcaście: <a href="${urlArt(pod.id)}">odcinek ${pod.o.nr} „${esc(pod.o.tytul)}”</a>${pod.o.youtube ? ` · <a href="https://www.youtube.com/watch?v=${esc(pod.o.youtube)}" rel="noopener">YouTube</a>` : ""}${pod.o.spotify ? ` · <a href="https://open.spotify.com/episode/${esc(pod.o.spotify)}" rel="noopener">Spotify</a>` : ""}` : `Premiera w podcaście: <a href="${urlArt(pod.id)}">odcinek ${pod.p!.nr} „${esc(pod.p!.tytul)}”</a>, ${esc(pod.p!.kiedy)}`}</p>` : ""}
    </div>
  </section>

  <div class="dwie-strony">
    <section class="co-pisal">
      <h2>Co pisał Leszek</h2>
      <p class="uwaga">Streszczenia przygotowała AI; cytaty są dosłowne, z artykułów Leszka.</p>
      <ul class="lista-art">
      ${leszek}
      </ul>
    </section>
    <section class="co-dzis">
      <h2>Co mówią dziś badania</h2>
      ${m.wiki ? `<p>${esc(skroc(m.wiki.wstep, 900))}</p>
      <p class="zrodlo">Źródło: <a href="${esc(m.wiki.url)}" rel="noopener">Wikipedia${m.wiki.jezyk === "en" ? " (angielska)" : ""}: „${esc(m.wiki.tytul)}”</a>, licencja <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.pl" rel="noopener">CC BY-SA 4.0</a> · <a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Wikidata</a></p>` : `<p>Brak opracowania w Wikipedii. <a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Dane w Wikidata</a>.</p>`}
      <p class="zrodlo">To krótki wstęp, nie pełny przegląd badań. Masz lepsze źródło? <a href="${zgloszenie(m)}">Zgłoś je</a>.</p>
    </section>
  </div>

  ${m.zdjeciaLeszka.length ? `<section class="galeria-sekcja">
    <h2>Zdjęcia z artykułów Leszka <span class="ile">${m.zdjeciaLeszka.length}</span></h2>
    <p class="uwaga">Zdjęcia z lat 2004–2007, w jakości z ówczesnej strony. Opisy przygotowała AI.</p>
    <div class="galeria">
    ${fotoLeszka(m)}
    </div>
  </section>` : ""}

  ${m.zdjeciaCommons.length ? `<section class="galeria-sekcja">
    <h2>Współczesne zdjęcia <span class="ile">${m.zdjeciaCommons.length}</span></h2>
    <p class="uwaga">Z Wikimedia Commons, na wolnych licencjach. Kliknij, żeby powiększyć.</p>
    <div class="galeria">
    ${fotoCommons(m)}
    </div>
  </section>` : ""}

  <section class="gdzie">
    <h2>Gdzie to jest</h2>
    <div class="mini-mapa" id="mini-mapa" data-lat="${m.lat}" data-lon="${m.lon}" data-nazwa="${esc(m.nazwa)}"></div>
    <p class="blisko">W pobliżu: ${blisko.map(({ x, km }) => `<a href="${x.slug}.html">${esc(x.nazwa)}</a> <span>(${km < 10 ? km.toFixed(1) : Math.round(km).toLocaleString("pl-PL")} km)</span>`).join(" · ")}</p>
    <p><a class="przycisk" href="./#${m.slug}">Zobacz na mapie atlasu</a> <a class="przycisk drugi" href="${zgloszenie(m)}">Zgłoś poprawkę albo zdjęcie</a></p>
  </section>
</main>
` + stopka(`<script src="${LEAFLET}leaflet.js" crossorigin=""></script>\n`);
  writeFileSync(`${WYJSCIE}/${m.slug}.html`, html, "utf8");
}

// ---------- mapa (strona główna atlasu) ----------
const liczba = (r: string) => miejsca.filter((m) => m.rodzaje.includes(r)).length;
const daneMapy = miejsca.map((m) => ({ s: m.slug, n: m.nazwa, la: +m.lat.toFixed(4), lo: +m.lon.toFixed(4), r: m.rodzaje, a: m.artykuly.length, z: m.zdjeciaLeszka.length + m.zdjeciaCommons.length, f: miniatura(m) }));
const ileZdjec = miejsca.reduce((s, m) => s + m.zdjeciaLeszka.length + m.zdjeciaCommons.length, 0);
const index = glowa({ tytul: "Atlas Leszka – miejsca z tekstów uleszka.net na mapie", opis: `${miejsca.length} miejsc, o których pisał Leszek Klimek: piramidy, megality, dawne miasta, zamki i ślady kataklizmów – z jego tekstami, zdjęciami i współczesnymi fotografiami.`, url: `${BAZA}atlas/`, mapa: true }) +
  `<main class="wrap-atlas">
  <section class="wstep-atlasu">
    <p class="etykieta">Atlas Leszka</p>
    <h1>Miejsca, o których pisał Leszek Klimek</h1>
    <p>${miejsca.length} miejsc z jego tekstów: piramidy, megality, dawne miasta, zamki i ślady kataklizmów. Przy każdym są jego artykuły, zdjęcia z dawnej strony,
    współczesne fotografie i krótki wstęp o tym, co mówią dziś badania. Razem ${ileZdjec.toLocaleString("pl-PL")} zdjęć.</p>
  </section>
  <div class="filtry" role="group" aria-label="Rodzaj zagadki">
    <button type="button" class="filtr" data-r="" aria-pressed="true">Wszystkie <span>${miejsca.length}</span></button>
    ${Object.keys(rodzaje).filter(liczba).map((r) => `<button type="button" id="${r}" class="filtr r-${r}" data-r="${r}" aria-pressed="false">${esc(rodzaje[r])} <span>${liczba(r)}</span></button>`).join("\n    ")}
    <input type="search" id="szukaj-miejsca" placeholder="Szukaj miejsca…" aria-label="Szukaj miejsca">
  </div>
  <div class="mapa" id="mapa" aria-label="Mapa miejsc"></div>
  <p class="pod-mapa"><span id="ile-widac">${miejsca.length}</span> miejsc · kliknij punkt na mapie albo kartę poniżej · <a href="${zgloszenie()}">zaproponuj miejsce</a></p>
  <ul class="karty karty-miejsc" id="karty">
  ${daneMapy.map((d) => `<li id="${d.s}" data-s="${d.s}" data-r="${d.r.join(" ")}" data-n="${esc(d.n.toLowerCase())}"><a href="${d.s}.html">${d.f ? `<img src="${esc(d.f)}" alt="" loading="lazy">` : `<span class="bez-foto"></span>`}<b>${esc(d.n)}</b><small>${d.a} ${d.a === 1 ? "artykuł" : "artykuły"} · ${d.z} zdj.</small></a></li>`).join("\n  ")}
  </ul>
</main>
<script type="application/json" id="dane-mapy">${JSON.stringify(daneMapy).replace(/</g, "\\u003c")}</script>
` + stopka(`<script src="${LEAFLET}leaflet.js" crossorigin=""></script>\n`);
writeFileSync(`${WYJSCIE}/index.html`, index, "utf8");
for (const plik of ["atlas.css", "atlas.js"]) copyFileSync(`scripts/atlas/${plik}`, `${WYJSCIE}/${plik}`);

// ---------- dane dla serwera MCP ----------
writeFileSync(
  "atlas/atlas.json",
  JSON.stringify(miejsca.map((m) => ({
    id: m.slug, nazwa: m.nazwa, inne_nazwy: m.aliasy, rodzaje: m.rodzaje.map((r) => rodzaje[r]), lat: +m.lat.toFixed(4), lon: +m.lon.toFixed(4),
    opis: m.opisWikidata, powstanie: kiedyPowstalo(m.powstanie), artykuly: m.artykuly,
    strona: `${BAZA}atlas/${m.slug}.html`, wikipedia: m.wiki?.url ?? "", wikidata: m.wikidata,
    zdjecia_leszka: m.zdjeciaLeszka.length, zdjecia_wspolczesne: m.zdjeciaCommons.map((z) => ({ url: z.duze, autor: z.autor, licencja: z.licencja, zrodlo: z.strona })),
  })), null, 1) + "\n",
);
console.log(`Atlas: ${miejsca.length} miejsc, ${ileZdjec} zdjęć → ${WYJSCIE}/ i atlas/atlas.json`);
