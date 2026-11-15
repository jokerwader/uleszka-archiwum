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
import { zWersja } from "./lib/wersja.js";

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
// odmiana liczebników: 1 artykuł, 2–4 artykuły, 5 artykułów (ale 22 artykuły, 12 artykułów)
const odm = (n: number, [jeden, kilka, wiele]: [string, string, string]) => (n === 1 ? jeden : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? kilka : wiele);
const ART: [string, string, string] = ["artykuł", "artykuły", "artykułów"];
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
const miniatura = (m: MiejsceAtlasu) => (m.zdjeciaCommons.find((z) => !z.detal) ?? m.zdjeciaCommons[0])?.miniatura ?? (m.zdjeciaLeszka[0] ? rawUrl(m.zdjeciaLeszka[0].sciezka) : "");
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
  // motyw i wielkość tekstu wybrane w czytelni lub atlasie (przycisk „Aa”), ustawiane przed wyświetleniem strony
  try {
    document.documentElement.dataset.motyw = localStorage.getItem("uleszka-motyw") || "sepia";
    const r = localStorage.getItem("uleszka-rozmiar");
    if (r) document.documentElement.style.setProperty("--rozmiar", r + "px");
  } catch { document.documentElement.dataset.motyw = "sepia"; }
</script>
<link rel="stylesheet" href="${zWersja("../czytelnia/czytelnia.css", "scripts/czytelnia/czytelnia.css")}">
${o.mapa ? `<link rel="stylesheet" href="${LEAFLET}leaflet.css" crossorigin="">\n` : ""}<link rel="stylesheet" href="${zWersja("atlas.css", "scripts/atlas/atlas.css")}">
</head>
<body>
<header class="gora"><div class="wrap-sz">
  <a class="logo" href="../">uleszka<span>.net</span><span class="tylko-szeroki" style="color:inherit"> · atlas</span></a>
  <nav aria-label="Menu główne">
    ${menuLinki("atlas")}
    <button class="przycisk-gora" id="przycisk-wygladu" type="button" aria-expanded="false" aria-controls="panel-wygladu" title="Kolory i wielkość tekstu"><b>Aa</b></button>
    ${hamburger}
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
`;
const stopka = (skrypty: string) => `<footer><div class="wrap-sz">
  <p>Teksty i zdjęcia z artykułów: Leszek Klimek, uleszka.net (ok. 2004–2007). Współczesne zdjęcia: Wikimedia Commons i Openverse (m.in. Flickr), tylko na wolnych licencjach – autor i licencja przy każdym zdjęciu. Zdjęcie do usunięcia? Zgłoś je.
  Wstępy w części „W skrócie”: Wikipedia (CC BY-SA 4.0). Położenie i opisy miejsc: Wikidata. Mapa: © autorzy OpenStreetMap.
  Opracowania i opisy zdjęć przygotowała AI. <a href="${REPO}">Archiwum na GitHubie</a> · <a href="${zgloszenie()}">zgłoś miejsce lub poprawkę</a></p>
</div></footer>
<dialog class="podglad" id="podglad"><form method="dialog"><button class="zamknij" aria-label="Zamknij">✕</button></form><img alt=""><p></p></dialog>
${skrypty}<script src="${zWersja("../menu.js", "docs/menu.js")}" defer></script>
<script src="${zWersja("atlas.js", "scripts/atlas/atlas.js")}" defer></script>
</body>
</html>
`;

const chip = (r: string) => `<span class="chip r-${r}">${esc(rodzaje[r] ?? r)}</span>`;

// ---------- „Najnowsze badania” (atlas/odkrycia.json; instrukcja: atlas/ODKRYCIA.md) ----------
const POKAZ = Number(process.env.ATLAS_POKAZ ?? 8); // ile badań widać od razu; resztę rozwija przycisk „Pokaż wszystkie”
type Odkrycie = { rok: string; tytul: string; opis: string; pewnosc?: string; zrodla: { nazwa: string; url: string }[]; artykul?: string; cytat_leszka?: string };
const odkrycia: Record<string, Odkrycie[]> = existsSync("atlas/odkrycia.json") ? JSON.parse(readFileSync("atlas/odkrycia.json", "utf8")) : {};
const zlozone = (s: string) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l").replace(/[^a-z0-9]+/g, " ").trim();
let odrzuconeCytaty = 0;
// cytat Leszka musi być dosłowny: jeśli nie ma go w artykule, nie pokazujemy go (i ostrzegamy przy budowaniu)
const cytatPrawdziwy = (o: Odkrycie) => {
  if (!o.cytat_leszka) return "";
  const a = o.artykul ? archiwum.znajdz(o.artykul, "artykul") : undefined;
  const teksty = a ? [a.czysty] : archiwum.artykuly.map((x) => x.czysty);
  if (teksty.some((t) => zlozone(t).includes(zlozone(o.cytat_leszka!)))) return o.cytat_leszka;
  odrzuconeCytaty++;
  console.warn(`⚠ odkrycia.json: cytat nie występuje dosłownie w artykule – pominięty: „${o.cytat_leszka.slice(0, 60)}…”`);
  return "";
};
const PEWNOSC: Record<string, string> = { "potwierdzone": "potwierdzone", "publikacja naukowa": "publikacja naukowa", "doniesienie": "doniesienie", "hipoteza": "hipoteza" };

// ---------- galeria: jedna siatka z przełącznikami; opis, autor i licencja w powiększeniu ----------
type Kafelek = { mini: string; duze: string; alt: string; podpis: string; grupa: "zblizenia" | "widoki" | "leszek"; ocena?: string };
const kafelki = (m: MiejsceAtlasu, glowne?: MiejsceAtlasu["zdjeciaCommons"][number]): Kafelek[] => [
  ...m.zdjeciaCommons.filter((z) => z !== glowne).map((z): Kafelek => {
    const opisZdj = z.opis && z.opis.length > 12 ? z.opis : "";
    return {
      mini: z.miniatura, duze: z.duze, alt: opisZdj || m.nazwa, grupa: z.detal ? "zblizenia" : "widoki", ocena: z.ocena,
      podpis: `${opisZdj ? `${opisZdj} · ` : ""}fot. ${z.autor}${z.data ? `, ${z.data.slice(0, 4)}` : ""}, ${z.licencja} · ${z.serwis ?? "Wikimedia Commons"}|${z.strona}`,
    };
  }),
  ...m.zdjeciaLeszka.map((z): Kafelek => ({
    mini: rawUrl(z.sciezka), duze: rawUrl(z.sciezka), alt: z.opis, grupa: "leszek",
    podpis: `${z.opis} · ${z.pochodzenie} · artykuł „${art(z.artykul).tytul}”|${urlArt(z.artykul)}`,
  })),
];
const NAZWY_GRUP = { zblizenia: "Zbliżenia konstrukcji", widoki: "Widoki", leszek: "Archiwum Leszka" } as const;

rmSync(WYJSCIE, { recursive: true, force: true });
mkdirSync(WYJSCIE, { recursive: true });

// ---------- karty miejsc ----------
// ile widać od razu; resztę rozwija przycisk „Pokaż wszystkie”
const POKAZ_ART = 5, POKAZ_ZDJ = 9;
const km = (n: number) => `${n < 10 ? n.toLocaleString("pl-PL", { maximumFractionDigits: 1 }) : Math.round(n).toLocaleString("pl-PL")} km`;
const kafelHtml = (k: Kafelek) =>
  `<button type="button" class="powieksz" data-duze="${esc(k.duze)}" data-podpis="${esc(k.podpis)}"><img src="${esc(k.mini)}" alt="${esc(skroc(k.alt, 140))}" loading="lazy">${k.ocena ? `<span class="ocena" title="Wyróżnione przez społeczność Commons">★</span>` : ""}</button>`;

for (const m of miejsca) {
  // na górze zdjęcie całego miejsca (nie zbliżenie)
  const glowne = m.zdjeciaCommons.find((z) => !z.detal) ?? m.zdjeciaCommons[0];
  const tlo = glowne?.duze ?? (m.zdjeciaLeszka[0] ? rawUrl(m.zdjeciaLeszka[0].sciezka) : "");
  const pod = podcastMiejsca(m);
  const blisko = miejsca.filter((x) => x !== m).map((x) => ({ x, km: odleglosc(m, x) })).sort((a, b) => a.km - b.km).slice(0, 5);
  const opis = `${m.nazwa} w tekstach Leszka Klimka (uleszka.net): ${m.artykuly.length} ${odm(m.artykuly.length, ART)}, zdjęcia, najnowsze badania, mapa i to, co wiadomo dziś.`;
  const powstanie = kiedyPowstalo(m.powstanie);
  const lista = odkrycia[m.slug] ?? [];
  // jeden rok na badanie; przy zakresie („2017–2024”) liczy się rok końcowy. Od najnowszych.
  const badania = lista.map((o) => { const r = o.rok.match(/\d{4}/g) ?? []; return { o, rok: Number(r[r.length - 1] ?? 0) }; }).sort((a, b) => b.rok - a.rok);
  const lataBadan = [...new Set(badania.map((b) => b.rok))];
  const kaf = kafelki(m, glowne);
  // współczesne: najpierw zbliżenia konstrukcji, potem widoki; archiwum Leszka osobno
  const wspolczesne = kaf.filter((k) => k.grupa !== "leszek").sort((a, b) => Number(a.grupa !== "zblizenia") - Number(b.grupa !== "zblizenia"));
  const archiwalne = kaf.filter((k) => k.grupa === "leszek");
  const grupy = (["zblizenia", "widoki"] as const).filter((g) => wspolczesne.some((k) => k.grupa === g));
  // najmocniejszy cytat Leszka o tym miejscu jako motto karty
  const motto = m.cytaty.find((c) => c.cytat.length >= 60 && c.cytat.length <= 320) ?? m.cytaty[0];
  const najblizej = blisko[0];

  const leszek = m.artykuly.map((id, i) => {
    const a = art(id), o = archiwum.opracowania.get(id);
    const cyt = m.cytaty.find((c) => c.artykul === id && c !== motto);
    // zajawka: dosłowny cytat Leszka, a gdy go nie ma – początek streszczenia
    const zajawka = cyt ? `<span class="cyt">„${esc(skroc(cyt.cytat, 170))}”</span>` : o?.streszczenie ? esc(skroc(o.streszczenie, 170)) : "";
    return `<li${i >= POKAZ_ART ? ' class="dalsze"' : ""}><a href="${urlArt(id)}">
          <span class="art-glowa"><span class="tytul-art">${esc(a.tytul)}</span><span class="dzial">${esc(a.dzial)}</span></span>
          ${zajawka ? `<span class="zajawka">${zajawka}</span>` : ""}
          <span class="czytaj" aria-hidden="true">Czytaj →</span>
        </a></li>`;
  }).join("\n        ");

  const badanieHtml = ({ o, rok }: (typeof badania)[number], i: number) => {
    const c = cytatPrawdziwy(o);
    const tytulArt = o.artykul ? archiwum.znajdz(o.artykul, "artykul")?.tytul : undefined;
    return `<li data-rok="${rok}"${i >= POKAZ ? ' class="dalsze"' : ""}>
          <span class="rok">${rok || esc(o.rok)}</span>
          <details class="badanie"${i === 0 ? " open" : ""}>
            <summary><span class="tytul-badania">${esc(o.tytul)}</span>${o.pewnosc && PEWNOSC[o.pewnosc] ? ` <span class="pewnosc p-${slug(o.pewnosc)}">${esc(PEWNOSC[o.pewnosc])}</span>` : ""}</summary>
            <div class="badanie-tresc${c ? " z-cytatem" : ""}">
              ${c ? `<div class="leszek-pisal"><small>Leszek pisał</small><p>„${esc(c)}”</p>${tytulArt ? `<a href="${urlArt(o.artykul!)}">„${esc(tytulArt)}” →</a>` : ""}</div>` : ""}
              <div class="ustalenia"><small>${c ? `Badania, ${rok}` : "Co ustalono"}</small><p>${esc(o.opis)}</p></div>
            </div>
            <p class="zrodla-odkrycia"><span>Źródła:</span> ${o.zrodla.map((z) => `<a href="${esc(z.url)}" rel="noopener">${esc(z.nazwa)} ↗</a>`).join("")}</p>
          </details>
        </li>`;
  };

  const html = glowa({ tytul: `${m.nazwa} – Atlas Leszka, uleszka.net`, opis, url: `${BAZA}atlas/${m.slug}.html`, obraz: glowne?.duze, mapa: true }) +
    `<main class="karta-miejsca">
  <header class="hero-miejsca"${tlo ? ` style="--tlo: url('${esc(tlo)}')"` : ""}>
    <div class="hero-tresc wrap-atlas">
      <p class="okruszki"><a href="./">Atlas Leszka</a> › ${m.rodzaje.map((r) => `<a href="./#${r}">${esc(rodzaje[r])}</a>`).join(" · ")}</p>
      <h1>${esc(m.nazwa)}</h1>
      ${m.opisWikidata ? `<p class="podtytul">${esc(m.opisWikidata[0].toUpperCase() + m.opisWikidata.slice(1))}</p>` : ""}
      <p class="chipy">${m.rodzaje.map(chip).join(" ")}</p>
    </div>
    ${glowne ? `<button type="button" class="powieksz hero-powieksz" data-duze="${esc(glowne.duze)}" data-podpis="${esc(`${glowne.opis && glowne.opis.length > 12 ? `${glowne.opis} · ` : ""}fot. ${glowne.autor}, ${glowne.licencja} · ${glowne.serwis ?? "Wikimedia Commons"}|${glowne.strona}`)}">⤢ Powiększ zdjęcie</button>` : ""}
    ${glowne ? `<p class="hero-autor">fot. ${esc(skroc(glowne.autor, 50))}, ${esc(glowne.licencja)} · <a href="${esc(glowne.strona)}" rel="noopener">${esc(glowne.serwis ?? "Commons")}</a></p>` : ""}
  </header>

  <div class="fakty-pasek"><div class="wrap-atlas">
    <span><b>${m.artykuly.length}</b> ${odm(m.artykuly.length, ART)} Leszka</span>
    ${lista.length ? `<span><b>${lista.length}</b> ${odm(lista.length, ["najnowsze badanie", "najnowsze badania", "najnowszych badań"])}</span>` : ""}
    <span><b>${kaf.length}</b> ${odm(kaf.length, ["zdjęcie", "zdjęcia", "zdjęć"])}</span>
    ${powstanie ? `<span>powstanie: <b>${powstanie}</b></span>` : ""}
    <span><a href="https://www.openstreetmap.org/?mlat=${m.lat}&amp;mlon=${m.lon}#map=14/${m.lat}/${m.lon}" rel="noopener">${m.lat.toFixed(3)}, ${m.lon.toFixed(3)}</a></span>
    ${pod ? `<span class="pod-podcast">🎧 ${"o" in pod && pod.o ? `<a href="${urlArt(pod.id)}">odcinek ${pod.o.nr} podcastu</a>` : `premiera ${esc(pod.p!.kiedy.replace(/ \d{4},.*$/, ""))}`}</span>` : ""}
  </div></div>

  <nav class="sekcje" aria-label="Części karty"><div class="wrap-atlas">
    <a href="#skrot">W skrócie</a><a href="#leszek">Co pisał Leszek</a>${badania.length ? `<a href="#badania">Najnowsze badania</a>` : ""}${kaf.length ? `<a href="#zdjecia">Zdjęcia</a>` : ""}<a href="#mapa">Mapa</a>
  </div></nav>

  <section id="skrot" class="pas w-skrocie"><div class="wrap-atlas skrot-siatka">
    <div>
      <h2 class="etykieta">W skrócie</h2>
      ${m.wiki ? `<p class="wstep-wiki">${esc(skroc(m.wiki.wstep, 560))}</p>
      <p class="zrodlo">Wstęp z <a href="${esc(m.wiki.url)}" rel="noopener">Wikipedii${m.wiki.jezyk === "en" ? " (angielskiej)" : ""}: „${esc(m.wiki.tytul)}”</a> (CC BY-SA 4.0) · <a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Wikidata</a></p>`
        : `<p class="wstep-wiki">${esc(m.opisWikidata ? m.opisWikidata[0].toUpperCase() + m.opisWikidata.slice(1) + "." : m.nazwa)}</p><p class="zrodlo"><a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Dane w Wikidata</a></p>`}
    </div>
    <div class="skrot-boczny">
      ${badania[0] ? `<a class="skrot-kafel" href="#badania"><small>Najnowsze badanie · ${badania[0].rok}</small><b>${esc(badania[0].o.tytul)}</b></a>` : ""}
      ${najblizej ? `<a class="skrot-kafel" href="${najblizej.x.slug}.html"><small>Najbliżej w atlasie · ${km(najblizej.km)}</small><b>${esc(najblizej.x.nazwa)}</b></a>` : ""}
    </div>
  </div></section>

  <section id="leszek" class="pas jasny-pas"><div class="wrap-atlas">
    <h2 class="etykieta">Co pisał Leszek · ${m.artykuly.length}</h2>
    ${motto ? `<figure class="motto"><blockquote>„${esc(motto.cytat)}”</blockquote><figcaption>Leszek Klimek, <a href="${urlArt(motto.artykul)}">„${esc(art(motto.artykul).tytul)}”</a></figcaption></figure>` : ""}
    <ul class="lista-artykulow zwijane${m.artykuly.length > POKAZ_ART ? "" : " rozwiniete"}">
        ${leszek}
    </ul>
    ${m.artykuly.length > POKAZ_ART ? `<button type="button" class="pokaz-wszystkie">Pokaż wszystkie artykuły (${m.artykuly.length})</button>` : ""}
    <p class="uwaga">Cytaty są dosłowne, z artykułów Leszka; krótkie streszczenia przygotowała AI.</p>
  </div></section>

  ${badania.length ? `<section id="badania" class="pas"><div class="wrap-atlas">
    <h2 class="etykieta">Najnowsze badania · ${badania.length}</h2>
    ${badania.length > POKAZ && lataBadan.length > 1 ? `<div class="lata-filtr" role="group" aria-label="Pokaż badania z roku">
      <button type="button" data-rok="" aria-pressed="true">Wszystkie <span>${badania.length}</span></button>${lataBadan.map((r) => `<button type="button" data-rok="${r}" aria-pressed="false">${r}${((n) => (n > 1 ? ` <span>${n}</span>` : ""))(badania.filter((b) => b.rok === r).length)}</button>`).join("")}
    </div>` : ""}
    <ol class="os-badan zwijane${badania.length > POKAZ ? "" : " rozwiniete"}">
        ${badania.map(badanieHtml).join("\n        ")}
    </ol>
    ${badania.length > POKAZ ? `<button type="button" class="pokaz-wszystkie">Pokaż wszystkie badania (${badania.length})</button>` : ""}
    <p class="uwaga">Kliknij tytuł, żeby rozwinąć opis i źródła.</p>
  </div></section>` : ""}

  ${kaf.length ? `<section id="zdjecia" class="pas jasny-pas"><div class="wrap-atlas">
    <div class="naglowek-zdjec">
      <h2 class="etykieta">Zdjęcia · ${kaf.length}</h2>
      ${grupy.length > 1 ? `<div class="przelacznik-zdjec" role="group" aria-label="Rodzaj zdjęć">
        <button type="button" data-grupa="" aria-pressed="true">Wszystkie <span>${wspolczesne.length}</span></button>${grupy.map((g) => `<button type="button" data-grupa="${g}" aria-pressed="false">${NAZWY_GRUP[g]} <span>${wspolczesne.filter((k) => k.grupa === g).length}</span></button>`).join("")}
      </div>` : ""}
    </div>
    ${wspolczesne.length ? `<ul class="mozaika zwijane${wspolczesne.length > POKAZ_ZDJ ? "" : " rozwiniete"}">
        ${wspolczesne.map((k, i) => `<li data-grupa="${k.grupa}"${i >= POKAZ_ZDJ ? ' class="dalsze"' : ""}>${kafelHtml(k)}</li>`).join("\n        ")}
    </ul>
    ${wspolczesne.length > POKAZ_ZDJ ? `<button type="button" class="pokaz-wszystkie">Pokaż wszystkie zdjęcia (${wspolczesne.length})</button>` : ""}` : ""}
    ${archiwalne.length ? `<div class="archiwum-leszka">
      <h3>Archiwum Leszka <small>zdjęcia z jego artykułów, 2004–2007</small></h3>
      <ul class="pasek-archiwum">${archiwalne.map((k) => `<li>${kafelHtml(k)}</li>`).join("")}</ul>
    </div>` : ""}
    <p class="uwaga">Współczesne zdjęcia: Wikimedia Commons i Openverse (m.in. Flickr), na wolnych licencjach${wspolczesne.some((k) => k.ocena) ? " (★ – wyróżnione przez społeczność Commons)" : ""}. Kliknij zdjęcie, żeby zobaczyć opis, autora i licencję.</p>
  </div></section>` : ""}

  <section id="mapa" class="pas gdzie"><div class="wrap-atlas">
    <h2 class="etykieta">Gdzie to jest</h2>
    <div class="gdzie-siatka">
      <div class="mini-mapa" id="mini-mapa" data-lat="${m.lat}" data-lon="${m.lon}" data-nazwa="${esc(m.nazwa)}" data-blisko="${esc(JSON.stringify(blisko.map(({ x, km: d }) => [+x.lat.toFixed(4), +x.lon.toFixed(4), x.nazwa, x.slug, Math.round(d)])))}"></div>
      <div class="blisko">
        <p class="blisko-tytul">W pobliżu w atlasie</p>
        ${blisko.map(({ x, km: d }) => { const f = miniatura(x); return `<a href="${x.slug}.html">${f ? `<img src="${esc(f)}" alt="" loading="lazy">` : `<span class="bez-foto"></span>`}<span><b>${esc(x.nazwa)}</b><small>${km(d)}</small></span></a>`; }).join("\n        ")}
        <a class="przycisk drugi" href="./#${m.slug}">Zobacz na mapie atlasu</a>
      </div>
    </div>
  </div></section>

  <section class="pas zglos"><div class="wrap-atlas zglos-pasek">
    <p><b>Znasz nowe odkrycie, lepsze źródło albo zdjęcie tego miejsca?</b> Zgłoś je, a dopiszemy je do karty.</p>
    <a class="przycisk" href="${zgloszenie(m)}">Zgłoś</a>
  </div></section>
</main>
` + stopka(`<script src="${LEAFLET}leaflet.js" crossorigin=""></script>\n`);
  writeFileSync(`${WYJSCIE}/${m.slug}.html`, html, "utf8");
}
if (odrzuconeCytaty) console.warn(`⚠ Pominięto ${odrzuconeCytaty} cytatów z odkrycia.json, których nie ma dosłownie w artykułach.`);

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
  ${daneMapy.map((d) => `<li id="${d.s}" data-s="${d.s}" data-r="${d.r.join(" ")}" data-n="${esc(d.n.toLowerCase())}"><a href="${d.s}.html">${d.f ? `<img src="${esc(d.f)}" alt="" loading="lazy">` : `<span class="bez-foto"></span>`}<b>${esc(d.n)}</b><small>${d.a} ${odm(d.a, ART)} · ${d.z} zdj.</small></a></li>`).join("\n  ")}
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
