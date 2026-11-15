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
  <p>Teksty i zdjęcia z artykułów: Leszek Klimek, uleszka.net (ok. 2004–2007). Współczesne zdjęcia: Wikimedia Commons i Openverse (m.in. Flickr), tylko na wolnych licencjach – autor i licencja przy każdym zdjęciu. Zdjęcie do usunięcia? Zgłoś je.
  Wstępy w części „Co wiadomo dziś”: Wikipedia (CC BY-SA 4.0). Położenie i opisy miejsc: Wikidata. Mapa: © autorzy OpenStreetMap.
  Opracowania i opisy zdjęć przygotowała AI. <a href="${REPO}">Archiwum na GitHubie</a> · <a href="${zgloszenie()}">zgłoś miejsce lub poprawkę</a></p>
</div></footer>
<dialog class="podglad" id="podglad"><form method="dialog"><button class="zamknij" aria-label="Zamknij">✕</button></form><img alt=""><p></p></dialog>
${skrypty}<script src="../menu.js" defer></script>
<script src="atlas.js" defer></script>
</body>
</html>
`;

const chip = (r: string) => `<span class="chip r-${r}">${esc(rodzaje[r] ?? r)}</span>`;

// ---------- „Najnowsze badania” (atlas/odkrycia.json; instrukcja: atlas/ODKRYCIA.md) ----------
const POKAZ = Number(process.env.ATLAS_POKAZ ?? 6); // ile badań i artykułów widać od razu; resztę rozwija przycisk „Pokaż wszystkie”
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
for (const m of miejsca) {
  // na górze zdjęcie całego miejsca (nie zbliżenie)
  const glowne = m.zdjeciaCommons.find((z) => !z.detal) ?? m.zdjeciaCommons[0];
  const tlo = glowne?.duze ?? (m.zdjeciaLeszka[0] ? rawUrl(m.zdjeciaLeszka[0].sciezka) : "");
  const pod = podcastMiejsca(m);
  const blisko = miejsca.filter((x) => x !== m).map((x) => ({ x, km: odleglosc(m, x) })).sort((a, b) => a.km - b.km).slice(0, 4);
  const opis = `${m.nazwa} w tekstach Leszka Klimka (uleszka.net): ${m.artykuly.length} ${odm(m.artykuly.length, ART)}, zdjęcia, najnowsze badania, mapa i to, co wiadomo dziś.`;
  const powstanie = kiedyPowstalo(m.powstanie);
  const lista = odkrycia[m.slug] ?? [];
  // najnowsze badania od najnowszych; „2014–2016” obejmuje każdy z tych lat w kalendarzu
  const badania = lista.map((o) => {
    const r = (o.rok.match(/\d{4}/g) ?? []).map(Number);
    const lata = r.length >= 2 ? Array.from({ length: Math.max(1, r[r.length - 1] - r[0] + 1) }, (_, i) => r[0] + i) : r;
    return { o, lata, od: r[0] ?? 0, do: r[r.length - 1] ?? 0 };
  }).sort((a, b) => b.do - a.do || b.od - a.od);
  const ileWRoku = new Map<number, number>();
  for (const b of badania) for (const r of b.lata) ileWRoku.set(r, (ileWRoku.get(r) ?? 0) + 1);
  const wszystkieLata = [...ileWRoku.keys()];
  const lataBadan: [number, number][] = wszystkieLata.length
    ? Array.from({ length: Math.max(...wszystkieLata) - Math.min(...wszystkieLata) + 1 }, (_, i) => Math.min(...wszystkieLata) + i).map((r) => [r, ileWRoku.get(r) ?? 0])
    : [];
  const maxRok = Math.max(1, ...lataBadan.map(([, n]) => n));
  const kaf = kafelki(m, glowne);
  const grupy = (["zblizenia", "widoki", "leszek"] as const).filter((g) => kaf.some((k) => k.grupa === g));
  // najmocniejszy cytat Leszka o tym miejscu jako motto karty
  const motto = m.cytaty.find((c) => c.cytat.length >= 60 && c.cytat.length <= 320) ?? m.cytaty[0];

  const leszek = m.artykuly.map((id, i) => {
    const a = art(id), o = archiwum.opracowania.get(id);
    const cyt = m.cytaty.filter((c) => c.artykul === id && c !== motto).slice(0, 1);
    return `<li class="art-karta${i >= POKAZ ? " dalsze" : ""}">
          <a class="tytul-art" href="${urlArt(id)}">${esc(a.tytul)}</a><span class="dzial">${esc(a.dzial)}</span>
          ${o?.streszczenie ? `<p>${esc(skroc(o.streszczenie, 260))}</p>` : ""}
          ${cyt.map((c) => `<blockquote>„${esc(c.cytat)}”</blockquote>`).join("")}
        </li>`;
  }).join("\n        ");

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
    <a href="#leszek">Co pisał Leszek</a>${lista.length ? `<a href="#badania">Najnowsze badania</a>` : ""}<a href="#dzis">Co wiadomo dziś</a>${kaf.length ? `<a href="#zdjecia">Zdjęcia</a>` : ""}<a href="#mapa">Mapa</a>
  </div></nav>

  <div class="wrap-atlas">
    <section id="leszek" class="sekcja">
      <p class="etykieta">Co pisał Leszek</p>
      ${motto ? `<figure class="motto"><blockquote>„${esc(motto.cytat)}”</blockquote><figcaption>Leszek Klimek, <a href="${urlArt(motto.artykul)}">„${esc(art(motto.artykul).tytul)}”</a></figcaption></figure>` : ""}
      <ul class="artykuly-miejsca zwijane${m.artykuly.length > POKAZ ? "" : " rozwiniete"}">
        ${leszek}
      </ul>
      ${m.artykuly.length > POKAZ ? `<button type="button" class="pokaz-wszystkie" data-tekst="Pokaż wszystkie artykuły (${m.artykuly.length})">Pokaż wszystkie artykuły (${m.artykuly.length})</button>` : ""}
      <p class="uwaga">Streszczenia przygotowała AI; cytaty są dosłowne, z artykułów Leszka.</p>
    </section>

    ${badania.length ? `<section id="badania" class="sekcja">
      <p class="etykieta">Najnowsze badania · ${badania.length}</p>
      ${lataBadan.length > 1 ? `<div class="kalendarz" role="group" aria-label="Kalendarz: lata badań">
        <button type="button" class="kal-wszystkie" data-rok="" aria-pressed="true">Wszystkie</button>
        <div class="kal-lata">${lataBadan.map(([rok, ile]) => `<button type="button" data-rok="${rok}" aria-pressed="false"${ile ? "" : " disabled"} title="${rok}: ${ile} ${odm(ile, ["badanie", "badania", "badań"])}"><span class="slupek" style="--n:${(ile / maxRok).toFixed(2)}"></span><b>${String(rok).slice(2)}</b></button>`).join("")}</div>
      </div>` : ""}
      <ol class="lista-badan zwijane${badania.length > POKAZ ? "" : " rozwiniete"}">
        ${badania.map(({ o, lata }, i) => { const c = cytatPrawdziwy(o); return `<li data-lata="${lata.join(" ")}"${i >= POKAZ ? ' class="dalsze"' : ""}>
          <span class="rok">${esc(o.rok)}</span>
          <div class="badanie">
            <h3>${esc(o.tytul)}${o.pewnosc && PEWNOSC[o.pewnosc] ? ` <span class="pewnosc p-${slug(o.pewnosc)}">${esc(PEWNOSC[o.pewnosc])}</span>` : ""}</h3>
            <p class="opis-badania${o.opis.length > 300 ? " dlugi" : ""}">${esc(o.opis)}</p>
            ${o.opis.length > 300 ? `<button type="button" class="wiecej">więcej</button>` : ""}
            ${c ? `<p class="nawiazanie">Leszek pytał: „${esc(c)}”${o.artykul ? ` <a href="${urlArt(o.artykul)}">(„${esc(art(o.artykul)?.tytul ?? o.artykul)}”)</a>` : ""}</p>` : ""}
            <p class="zrodla-odkrycia">${o.zrodla.map((z) => `<a href="${esc(z.url)}" rel="noopener">${esc(z.nazwa)} ↗</a>`).join("")}</p>
          </div>
        </li>`; }).join("\n        ")}
      </ol>
      ${badania.length > POKAZ ? `<button type="button" class="pokaz-wszystkie" data-tekst="Pokaż wszystkie badania (${badania.length})">Pokaż wszystkie badania (${badania.length})</button>` : ""}
    </section>` : ""}

    <section id="dzis" class="sekcja dzis">
      <p class="etykieta">Co wiadomo dziś</p>
      ${m.wiki ? `<p class="wstep-wiki">${esc(skroc(m.wiki.wstep, 700))}</p>
      <p class="zrodlo">Wstęp z <a href="${esc(m.wiki.url)}" rel="noopener">Wikipedii${m.wiki.jezyk === "en" ? " (angielskiej)" : ""}: „${esc(m.wiki.tytul)}”</a> (CC BY-SA 4.0) · <a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Wikidata</a> · Znasz nowe odkrycie albo lepsze źródło? <a href="${zgloszenie(m)}">Zgłoś je</a>.</p>` : `<p>Brak opracowania w Wikipedii. <a href="https://www.wikidata.org/wiki/${m.wikidata}" rel="noopener">Dane w Wikidata</a>.</p>`}
    </section>

    ${kaf.length ? `<section id="zdjecia" class="sekcja">
      <p class="etykieta">Zdjęcia</p>
      <div class="przelacznik-zdjec" role="group" aria-label="Rodzaj zdjęć">
        ${grupy.length > 1 ? `<button type="button" data-grupa="" aria-pressed="true">Wszystkie <span>${kaf.length}</span></button>` : ""}
        ${grupy.map((g) => `<button type="button" data-grupa="${g}" aria-pressed="${grupy.length === 1}">${NAZWY_GRUP[g]} <span>${kaf.filter((k) => k.grupa === g).length}</span></button>`).join("")}
      </div>
      <ul class="siatka-zdjec">
        ${kaf.map((k, i) => `<li data-grupa="${k.grupa}"><button type="button" class="powieksz" data-i="${i}" data-duze="${esc(k.duze)}" data-podpis="${esc(k.podpis)}"><img src="${esc(k.mini)}" alt="${esc(skroc(k.alt, 140))}" loading="lazy">${k.ocena ? `<span class="ocena">★</span>` : ""}${k.grupa === "leszek" ? `<span class="znak-archiwum">2004–07</span>` : ""}</button></li>`).join("\n        ")}
      </ul>
      <p class="uwaga">Współczesne zdjęcia: Wikimedia Commons i Openverse (m.in. Flickr), na wolnych licencjach (★ – wyróżnione przez społeczność Commons). Archiwum Leszka: zdjęcia z jego artykułów z lat 2004–2007. Kliknij zdjęcie, żeby zobaczyć opis, autora i licencję.</p>
    </section>` : ""}

    <section id="mapa" class="sekcja gdzie">
      <p class="etykieta">Gdzie to jest</p>
      <div class="mini-mapa" id="mini-mapa" data-lat="${m.lat}" data-lon="${m.lon}" data-nazwa="${esc(m.nazwa)}"></div>
      <div class="blisko">${blisko.map(({ x, km }) => `<a href="${x.slug}.html"><b>${esc(x.nazwa)}</b><span>${km < 10 ? km.toFixed(1) : Math.round(km).toLocaleString("pl-PL")} km</span></a>`).join("")}</div>
      <p><a class="przycisk" href="./#${m.slug}">Zobacz na mapie atlasu</a> <a class="przycisk drugi" href="${zgloszenie(m)}">Zgłoś odkrycie, poprawkę albo zdjęcie</a></p>
    </section>
  </div>
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
