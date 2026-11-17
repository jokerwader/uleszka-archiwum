/**
 * Wideo odcinka na YouTube: nagranie MP3 + zdjęcia Leszka z artykułu, pokazywane mniej więcej wtedy,
 * gdy lektor czyta fragment obok zdjęcia; plansze z tytułami rozdziałów, plansza na zapowiedź i na zakończenie.
 * Powstają też miniatura (1280×720) i opis do YouTube z orientacyjnymi rozdziałami (znacznikami czasu).
 *
 *   npx tsx scripts/wideo.ts <folder odcinka> <nagranie.mp3>
 *   np. npx tsx scripts/wideo.ts podcast/01-potop-czy-tylko-jeden "C:/Users/…/ElevenLabs_uLeszka_-_Potop.mp3"
 *
 * Zdjęcia wysokiej jakości: miejsca z Atlasu Leszka (Wikimedia Commons, z autorem i licencją w kadrze i w opisie) – pokazywane,
 * gdy lektor wspomina miejsce, i w długich przerwach. Pobierane do podcast/.zdjecia/. Bez nich: --bez-commons.
 *
 * Wynik w <folder>/youtube/: wideo.mp4, miniatura.jpg, opis.txt (folder jest w .gitignore – pliki są duże).
 * Czasy są szacowane z długości tekstu (lektor czyta w stałym tempie), więc zdjęcie może się pojawić
 * kilkanaście sekund wcześniej albo później niż jego fragment. Wymaga ffmpeg i ffprobe.
 */
import { execFile, execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import sharp from "sharp";
import { Archiwum, zloz, type Dokument } from "../src/archiwum.js";
import { rdzenie, wczytajAtlas, type MiejsceAtlasu, type ZdjecieCommons } from "./lib/atlas.js";
import { pobierzZdjecie, podpisAutora } from "./lib/zdjecia-hq.js";

const [folder, mp3] = process.argv.slice(2);
if (!folder || !mp3 || !existsSync(join(folder, "ODCINEK.md")) || !existsSync(mp3))
  throw new Error("Użycie: npx tsx scripts/wideo.ts <folder odcinka z ODCINEK.md> <nagranie.mp3>");

const W = 1920, H = 1080;
const PODCAST = "Uwierz we własny rozum";
const SPOTIFY = "https://open.spotify.com/show/2xo2dGbYUOWBLWeDI1QKpu";
const slug = (s: string) =>
  s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const xml = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const czas = (s: number) => {
  const t = Math.max(0, Math.round(s)), h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), sek = t % 60;
  return `${h ? `${h}:${String(m).padStart(2, "0")}` : String(m).padStart(2, "0")}:${String(sek).padStart(2, "0")}`;
};
/** łamie tekst na linie o długości do `max` znaków (do napisów w SVG) */
const linie = (tekst: string, max: number) => {
  const wynik: string[] = [];
  let l = "";
  for (const s of tekst.split(/\s+/)) {
    if (l && (l + " " + s).length > max) { wynik.push(l); l = s; } else l = l ? `${l} ${s}` : s;
  }
  if (l) wynik.push(l);
  return wynik;
};

// ---------- odcinek: tytuł, artykuły, rozdziały (z ODCINEK.md i folderu rozdzialy-studio/) ----------
const opisMd = readFileSync(join(folder, "ODCINEK.md"), "utf8");
const [, rodzaj, tytul] = opisMd.match(/^# (Odcinek \d+|Zwiastun): (.+)$/m) ?? ["", "", folder];
const etykieta = rodzaj === "Zwiastun" ? "Na początek" : rodzaj;
const archiwum = new Archiwum(".");
const linkiArt = new Set([...opisMd.matchAll(/uleszka\.net\/czytelnia\/([a-z0-9-]+)\.html/g)].map((m) => m[1]));
const artykuly = archiwum.artykuly.filter((a) => linkiArt.has(slug(a.id)));
if (!artykuly.length) throw new Error("W ODCINEK.md nie ma linków do artykułów w czytelni");
const dokumenty: Dokument[] = artykuly.flatMap((a) => [a, ...archiwum.podstrony(a)]);
const tytulyRozdzialow = new Map([...opisMd.matchAll(/^\| (\d\d-[^|]+\.txt) \| ([^|]+) \| \d+ \|$/gm)].map((m) => [m[1].trim(), m[2].trim()]));
const folderRozdzialow = join(folder, "rozdzialy-studio");
const rozdzialy = readdirSync(folderRozdzialow).filter((f) => f.endsWith(".txt")).sort().map((f) => {
  const tekst = readFileSync(join(folderRozdzialow, f), "utf8").replace(/\[[^\]\n]*\]/g, "").replace(/\s+/g, " ").trim(); // znaczniki tonu nie są czytane
  return { plik: f, tytul: tytulyRozdzialow.get(f) ?? f, znaki: tekst.length, start: 0 };
});

// ---------- napisy: dokładny tekst czytany przez lektora, bez znaczników tonu (YouTube: „Automatyczna synchronizacja”) ----------
const wyjNapisy = join(folder, "youtube");
mkdirSync(wyjNapisy, { recursive: true });
writeFileSync(
  join(wyjNapisy, "napisy.txt"),
  readdirSync(folderRozdzialow).filter((f) => f.endsWith(".txt")).sort()
    .map((f) => readFileSync(join(folderRozdzialow, f), "utf8").replace(/\[[^\]\n]*\]/g, "").replace(/[ \t]+/g, " ").replace(/ *\n */g, "\n").replace(/\n{3,}/g, "\n\n").trim())
    .join("\n\n") + "\n",
  "utf8",
);
if (process.argv.includes("--tylko-napisy")) { console.log(`Gotowe: ${join(wyjNapisy, "napisy.txt")}`); process.exit(0); }

// ---------- czasy ----------
// Najlepiej: rozpoznana mowa (<folder>/mowa.jsonl, tworzy ją opcja --rozpoznaj) – zdania nagrania dopasowane do słów artykułu,
// zdjęcia i klipy trafiają w swoje zdanie z dokładnością do 1–2 s, rozdziały w opisie YouTube też.
// Bez niej: długość nagrania dzielona proporcjonalnie do liczby znaków rozdziałów (zdjęcie potrafi się spóźnić o minutę i więcej).
const dlugosc = Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], { encoding: "utf8" }).trim());
if (!(dlugosc > 0)) throw new Error("Nie udało się odczytać długości nagrania");
const plikMowy = join(folder, "mowa.jsonl");
if (process.argv.includes("--rozpoznaj")) {
  // whisper.cpp wbudowany w ffmpeg (od wersji 8); model np. ggml-large-v3-turbo-q5_0.bin z huggingface.co/ggerganov/whisper.cpp
  const model = process.env.WHISPER_MODEL ?? "../modele/ggml-large-v3-turbo-q5_0.bin";
  if (!existsSync(model)) throw new Error(`Brak modelu rozpoznawania mowy: ${model} (podaj ścieżkę w zmiennej WHISPER_MODEL)`);
  // ścieżki względne z ukośnikami: w opcjach filtra ffmpeg dwukropek (np. „C:”) jest separatorem
  const wzgl = (p: string) => relative(process.cwd(), resolve(p)).replace(/\\/g, "/");
  if ([model, plikMowy].some((p) => wzgl(p).includes(":"))) throw new Error("Model musi leżeć na tym samym dysku co repozytorium");
  console.log("Rozpoznaję mowę (whisper.cpp w ffmpeg) – trwa mniej więcej połowę długości nagrania…");
  execFileSync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-i", mp3, "-af",
    `whisper=model=${wzgl(model)}:language=pl:queue=20:destination=${wzgl(plikMowy)}:format=json`, "-f", "null", "-"], { stdio: "inherit" });
}
const tresc = dokumenty.map((d) => d.tresc).join("\n\n");
let kotwice: [number, number][] = [];
let zapowiedzKoniec = 0, zakonczenieStart = 0;
const mowa = existsSync(plikMowy) && !process.argv.includes("--bez-mowy");
if (mowa) {
  // słowa nagrania z czasem (wewnątrz zdania czas rozłożony według długości słów)
  const slowaM: { w: string; t: number }[] = [];
  for (const l of readFileSync(plikMowy, "utf8").split("\n").filter((x) => x.trim())) {
    // ffmpeg nie zabezpiecza cudzysłowów w tekście zdania, więc nie zawsze jest to poprawny JSON
    const m = l.match(/^\{"start":(\d+),"end":(\d+),"text":"(.*)"\}\s*$/);
    if (!m) continue;
    const o = { start: Number(m[1]), end: Number(m[2]), text: m[3] };
    const ws = zloz(o.text).match(/[a-z0-9]+/g) ?? [];
    const suma = ws.reduce((s, w) => s + w.length + 1, 0);
    let acc = 0;
    for (const w of ws) { slowaM.push({ w, t: (o.start + ((o.end - o.start) * acc) / suma) / 1000 }); acc += w.length + 1; }
  }
  const slowaT = [...zloz(tresc).matchAll(/[a-z0-9]+/g)].map((m) => ({ w: m[0], poz: m.index! }));
  // kotwice: te same 4 słowa pod rząd w tekście i w nagraniu, po kolei i blisko miejsca poprzedniej kotwicy
  const N = 4;
  const klucz = (a: { w: string }[], i: number) => a.slice(i, i + N).map((x) => x.w).join(" ");
  const indeks = new Map<string, number[]>();
  for (let j = 0; j + N <= slowaM.length; j++) { const k = klucz(slowaM, j); const l = indeks.get(k); if (l) l.push(j); else indeks.set(k, [j]); }
  let ostJ = -1, ostI = 0;
  for (let i = 0; i + N <= slowaT.length; i++) {
    const k = klucz(slowaT, i);
    if (k.length < 16) continue; // krótkie zbitki („i w tym”) powtarzają się w całym tekście
    const okno = kotwice.length ? 40 + 2 * (i - ostI) : 2000;
    const j = indeks.get(k)?.find((x) => x > ostJ && x - ostJ <= okno);
    if (j === undefined) continue;
    kotwice.push([slowaT[i].poz, slowaM[j].t]);
    ostJ = j; ostI = i;
  }
  if (kotwice.length < 20) throw new Error(`Rozpoznana mowa nie pasuje do tekstu odcinka (${kotwice.length} kotwic) – sprawdź ${plikMowy} albo użyj --bez-mowy`);
  // zakończenie (nie jest tekstem autora): pierwsze słowa pliku zakończenia w nagraniu po ostatniej kotwicy
  const ostatni = rozdzialy[rozdzialy.length - 1];
  const slowaZak = (zloz(readFileSync(join(folder, "rozdzialy-studio", ostatni.plik), "utf8").replace(/\[[^\]\n]*\]/g, "")).match(/[a-z0-9]+/g) ?? []).map((w) => ({ w }));
  const jZak = indeks.get(klucz(slowaZak, 0))?.find((x) => x > ostJ);
  zakonczenieStart = jZak !== undefined ? slowaM[jZak].t - 0.5 : kotwice[kotwice.length - 1][1] + 3;
  kotwice = [[0, Math.max(0, kotwice[0][1] - 1)], ...kotwice, [tresc.length, zakonczenieStart]];
  const luki = kotwice.slice(1).map((k, i) => k[1] - kotwice[i][1]);
  console.log(`Dopasowanie mowy: ${kotwice.length} kotwic, najdłuższa luka bez kotwicy ${Math.round(Math.max(...luki))} s.`);
}
const czasPozycji = (poz: number) => {
  for (let i = 1; i < kotwice.length; i++)
    if (poz <= kotwice[i][0]) { const [p0, c0] = kotwice[i - 1], [p1, c1] = kotwice[i]; return c0 + ((poz - p0) / Math.max(1, p1 - p0)) * (c1 - c0); }
  return zakonczenieStart;
};
if (mowa) {
  // rozdziały: chwila, w której lektor czyta tytuł rozdziału
  let od = 0;
  for (const r of rozdzialy.slice(1, -1)) {
    const poz = tresc.indexOf(r.tytul, od);
    if (poz >= od) { r.start = Math.max(0, czasPozycji(poz) - 0.5); od = poz + 1; } else r.start = -1;
  }
  rozdzialy[0].start = 0;
  rozdzialy[rozdzialy.length - 1].start = zakonczenieStart;
  // rozdział, którego tytułu nie ma dosłownie w tekście: w połowie między sąsiadami
  rozdzialy.forEach((r, i) => { if (r.start < 0) r.start = (rozdzialy[i - 1].start + (rozdzialy.slice(i + 1).find((x) => x.start >= 0)?.start ?? zakonczenieStart)) / 2; });
  zapowiedzKoniec = rozdzialy[1]?.start ?? 0;
} else {
  // zdjęcia: pozycja w tekście artykułu przeliczona na czas – kotwicami są początki rozdziałów (ich tytuły w tekście)
  const razem = rozdzialy.reduce((s, r) => s + r.znaki, 0);
  let t0 = 0;
  for (const r of rozdzialy) { r.start = t0; t0 += (r.znaki / razem) * dlugosc; }
  zapowiedzKoniec = rozdzialy[1]?.start ?? 0;
  zakonczenieStart = rozdzialy[rozdzialy.length - 1].start;
  kotwice = [[0, zapowiedzKoniec]];
  for (const r of rozdzialy.slice(1, -1)) {
    const poz = tresc.indexOf(r.tytul, kotwice[kotwice.length - 1][0]);
    if (poz > kotwice[kotwice.length - 1][0]) kotwice.push([poz, r.start]);
  }
  kotwice.push([tresc.length, zakonczenieStart]);
  console.log("Czasy szacowane z długości tekstu, bez rozpoznanej mowy (dokładniej: opcja --rozpoznaj).");
}
const widziane = new Set<string>();
const zdjecia: { sciezka: string; t: number }[] = [];
let przesuniecie = 0;
for (const d of dokumenty) {
  for (const o of d.obrazy) {
    if (!/\.(jpe?g|png|gif)$/i.test(o.sciezka) || !archiwum.opisObrazu(o.sciezka) || widziane.has(o.sciezka) || !existsSync(o.sciezka)) continue;
    const meta = await sharp(o.sciezka).metadata();
    if ((meta.width ?? 0) < 100 || (meta.height ?? 0) < 90) continue; // ikonki i ozdobniki
    widziane.add(o.sciezka);
    zdjecia.push({ sciezka: o.sciezka, t: czasPozycji(przesuniecie + Math.max(0, d.tresc.indexOf(`](${o.sciezka})`))) });
  }
  przesuniecie += d.tresc.length + 2;
}

// ---------- zdjęcia wysokiej jakości z Atlasu Leszka (Wikimedia Commons) ----------
// miejsca z artykułów odcinka; zdjęcie miejsca pojawia się, gdy lektor o nim mówi, a pozostałe wypełniają długie przerwy
const atlas = wczytajAtlas(archiwum);
const miejscaOdc = [...new Set(dokumenty.flatMap((d) => atlas.poArtykule.get(d.id) ?? []))];
const zt = zloz(tresc);
const LITERA = /[a-z0-9]/;
const wzmianki = (m: MiejsceAtlasu) => {
  const poz: number[] = [];
  for (const w of rdzenie([m.nazwa, ...m.aliasy])) {
    for (let i = zt.indexOf(w[0]); i >= 0; i = zt.indexOf(w[0], i + 1)) {
      if (i > 0 && LITERA.test(zt[i - 1])) continue; // tylko początek słowa
      if (w.slice(1).every((x) => zt.slice(i, i + 90).includes(x))) poz.push(i);
    }
  }
  return poz.sort((a, b) => a - b).filter((p, i, t) => i === 0 || p - t[i - 1] > 3000); // jedna wzmianka na ok. 3 min czytania
};
type ZdjecieHQ = { z: ZdjecieCommons; m: MiejsceAtlasu; plik: string };
const hq: { m: MiejsceAtlasu; poz: number[]; zdjecia: ZdjecieHQ[] }[] = [];
const bezHq = process.argv.includes("--bez-commons");
for (const m of bezHq ? [] : miejscaOdc) {
  const poz = wzmianki(m);
  if (!poz.length) continue;
  // najpierw zdjęcia poziome (lepiej wypełniają kadr 16:9)
  const kandydaci = [...m.zdjeciaCommons].sort((a, b) => Number(b.szer / b.wys >= 1.3) - Number(a.szer / a.wys >= 1.3)).slice(0, 20); // wszystkie zdjęcia miejsca z atlasu (do 20): im więcej, tym mniej powtórek
  const zdjecia: ZdjecieHQ[] = [];
  for (const z of kandydaci) {
    const plik = await pobierzZdjecie(z);
    if (plik && (await sharp(plik).metadata().then((x) => (x.width ?? 0) >= 1200).catch(() => false))) zdjecia.push({ z, m, plik });
  }
  if (zdjecia.length) hq.push({ m, poz, zdjecia });
}
console.log(`Atlas: ${miejscaOdc.length} miejsc w artykułach, ${hq.length} wspomnianych w tekście, ${hq.reduce((s, x) => s + x.zdjecia.length, 0)} zdjęć wysokiej jakości.`);
const hqPoKlatce = new Map<string, ZdjecieHQ>(); // klatka → zdjęcie (do podpisów autorów w opisie)

// ---------- plansze (SVG → PNG 1920×1080) ----------
const tlo = `<defs><radialGradient id="g" cx="70%" cy="0%" r="90%"><stop offset="0" stop-color="#1b2a4d"/><stop offset=".6" stop-color="#0a0d16"/><stop offset="1" stop-color="#05070c"/></radialGradient>
  <linearGradient id="z" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6e0"/><stop offset=".6" stop-color="#f0c46f"/><stop offset="1" stop-color="#b47a22"/></linearGradient></defs>
  <rect width="${W}" height="${H}" fill="url(#g)"/>`;
const tekstSvg = (wiersze: string[], x: number, y: number, rozmiar: number, styl: string) =>
  wiersze.map((w, i) => `<text x="${x}" y="${y + i * rozmiar * 1.18}" font-size="${rozmiar}" ${styl}>${xml(w)}</text>`).join("");
const stopkaSvg = `<text x="120" y="${H - 70}" font-family="Georgia, serif" font-size="30" fill="#9aa3b5">${xml(PODCAST)} · Leszek Klimek · uleszka.net</text>`;
const zSvg = (svg: string) => sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${svg}</svg>`));
/** nakładka (przezroczysta, nieruchoma nad ruchomym obrazem): pasek z podpisem na dole, opcjonalnie znaczek w lewym górnym rogu */
const nakladka = (podpis: string, prawy: string, znaczek = "", rozmiar = 40) => {
  const zn = znaczek ? `<rect x="40" y="40" width="${Math.round(znaczek.length * 12.6 + 48)}" height="52" rx="26" fill="#05070c" fill-opacity=".72" stroke="#f0c46f" stroke-opacity=".55"/>
    <text x="64" y="75" font-family="Arial, sans-serif" font-weight="700" font-size="24" fill="#f0c46f">${xml(znaczek)}</text>` : "";
  return zSvg(`<defs><linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070c" stop-opacity="0"/><stop offset="1" stop-color="#05070c" stop-opacity=".88"/></linearGradient></defs>
    <rect y="${H - 200}" width="${W}" height="200" fill="url(#p)"/>
    <text x="60" y="${H - 58}" font-family="Georgia, serif" font-weight="700" font-size="${rozmiar}" fill="#f0c46f">${xml(podpis)}</text>
    <text x="${W - 60}" y="${H - 60}" text-anchor="end" font-family="Arial, sans-serif" font-size="22" fill="#c9cfdb">${xml(prawy)}</text>${zn}`).png();
};
const naklPlik = (plik: string) => plik.replace(/\.png$/, "-n.png");

async function planszaRozdzialu(nazwa: string, plik: string) {
  const w = linie(nazwa, 30);
  const y0 = H / 2 - ((w.length - 1) * 96 * 1.18) / 2;
  await zSvg(`${tlo}<text x="120" y="${y0 - 110}" font-family="Arial, sans-serif" font-weight="700" font-size="30" letter-spacing="8" fill="#e2a93f">ROZDZIAŁ</text>
    ${tekstSvg(w, 120, y0, 96, 'font-family="Georgia, serif" font-weight="700" fill="url(#z)"')}${stopkaSvg}`).png().toFile(plik);
}
async function planszaOkladki(gora: string, glowny: string, dol: string[], plik: string) {
  const okladka = await sharp("podcast/okladka.jpg").resize(720, 720).toBuffer();
  const w = linie(glowny, 17); // 88 px Georgia bold: ok. 17 znaków mieści się w 860 px od x=1000
  const y0 = 470 - ((w.length - 1) * 88 * 1.18) / 2;
  const svg = await zSvg(`${tlo}<text x="1000" y="${y0 - 120}" font-family="Arial, sans-serif" font-weight="700" font-size="30" letter-spacing="8" fill="#e2a93f">${xml(gora.toUpperCase())}</text>
    ${tekstSvg(w, 1000, y0, 88, 'font-family="Georgia, serif" font-weight="700" fill="url(#z)"')}
    ${tekstSvg(dol, 1000, y0 + w.length * 88 * 1.18 + 40, 36, 'font-family="Georgia, serif" fill="#d7dbe4"')}`).png().toBuffer();
  await sharp(svg).composite([{ input: okladka, left: 160, top: 180 }]).png().toFile(plik);
}
/** zdjęcie wysokiej jakości: poziome wypełnia cały kadr, pionowe stoi na rozmytym tle; podpis (miejsce, autor) w osobnej nakładce */
async function klatkaHQ(sciezka: string, podpis: string, autor: string, plik: string) {
  const org = await sharp(sciezka).metadata();
  const poziome = (org.width ?? 1) / (org.height ?? 1) >= 1.3;
  const tloZdj = await sharp(sciezka).flatten({ background: "#0b0d12" }).resize(W, H, { fit: "cover" })
    .modulate(poziome ? { brightness: 1 } : { brightness: 0.35 }).blur(poziome ? 0.3 : 40).toBuffer();
  const warstwy: sharp.OverlayOptions[] = [];
  if (!poziome) {
    const zdj = await sharp(sciezka).resize(W - 200, H - 200, { fit: "inside" }).toBuffer();
    const m = await sharp(zdj).metadata();
    warstwy.push({ input: zdj, left: Math.round((W - (m.width ?? 0)) / 2), top: Math.round((H - 100 - (m.height ?? 0)) / 2) });
  }
  await sharp(tloZdj).composite(warstwy).png().toFile(plik);
  await nakladka(podpis, autor).toFile(naklPlik(plik));
}
async function klatkaZdjecia(sciezka: string, podpis: string, plik: string) {
  const tloZdj = await sharp(sciezka).flatten({ background: "#0b0d12" }).resize(W, H, { fit: "cover" }).blur(40).modulate({ brightness: 0.35 }).toBuffer();
  // małe zdjęcia z 2004 r. (często 150 px wysokości) powiększamy najwyżej 4 razy, żeby nie były rozmyte
  const org = await sharp(sciezka).metadata();
  const skala = Math.min((W - 200) / (org.width ?? 1), (H - 240) / (org.height ?? 1), 4);
  const zdj = await sharp(sciezka).resize(Math.round((org.width ?? 1) * skala), Math.round((org.height ?? 1) * skala), { kernel: "lanczos3" }).png().toBuffer();
  const m = await sharp(zdj).metadata();
  await sharp(tloZdj).composite([{ input: zdj, left: Math.round((W - (m.width ?? 0)) / 2), top: Math.round((H - 100 - (m.height ?? 0)) / 2) }]).png().toFile(plik);
  await nakladka(podpis, "uleszka.net", "", 32).toFile(naklPlik(plik));
}

// ---------- klipy: animacje 3D (grafiki/3d/wideo/*/klip.json) i nagrania na wolnej licencji (<folder>/nagrania-cc.json) ----------
// fraza z tekstu lektora szukana w treści artykułu po samych literach i cyfrach (bez wielkości liter, polskich znaków,
// odstępów, cudzysłowów i znaków markdown); gdy całej nie ma (np. poprawiona literówka), szukany jest jej początek
const plaski = (() => {
  let s = "";
  const poz: number[] = [];
  for (let i = 0; i < zt.length; i++) if (/[a-z0-9]/.test(zt[i])) { s += zt[i]; poz.push(i); }
  return { s, poz };
})();
const znajdzFraze = (fraza: string) => {
  const g = zloz(fraza).replace(/[^a-z0-9]/g, "");
  if (g.length < 30) return -1;
  for (const dl of [g.length, 80, 50]) {
    const i = plaski.s.indexOf(g.slice(0, dl));
    if (dl <= g.length && i >= 0) return plaski.poz[i];
  }
  return -1;
};
const dlugoscPliku = (p: string) => Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], { encoding: "utf8" }).trim());
const ZNACZKI: Record<string, string> = {
  "rysunek-leszka": "Według rysunku Leszka Klimka · animacja 3D",
  hipoteza: "Hipoteza z tekstu, nie fakt · animacja 3D",
  rekonstrukcja: "Rekonstrukcja 3D",
  ilustracja: "Animacja 3D",
};
type NagranieCC = { nazwa: string; miejsce: string; plik: string; strona: string; autor: string; licencja: string; licencja_url?: string; serwis?: string; fraza?: string; frazy?: string[] };
type Klip = { mp4: string; dl: number; t: number; nakl: () => ReturnType<typeof sharp>; cc?: NagranieCC; nazwa: string; naklCzas?: [number, number]; atrybucja?: string }; // naklCzas: nakładka tylko w tym czasie (s od początku klipu), z płynnym wejściem i zejściem
const klipy: Klip[] = [];
if (!process.argv.includes("--bez-klipow")) {
  const KLIPY3D = "grafiki/3d/wideo";
  for (const k of existsSync(KLIPY3D) ? readdirSync(KLIPY3D) : []) {
    const pj = join(KLIPY3D, k, "klip.json"), mp4 = join(KLIPY3D, k, "klip.mp4");
    if (!existsSync(pj) || !existsSync(mp4)) continue;
    const o = JSON.parse(readFileSync(pj, "utf8"));
    const dl = dlugoscPliku(mp4);
    // atrybucja.txt obok klipu: autorzy i licencje cudzych materiałów (CC BY, CC BY-SA), po jednym źródle w wierszu – idą do opisu
    const pa = join(KLIPY3D, k, "atrybucja.txt");
    const atrybucja = existsSync(pa) ? readFileSync(pa, "utf8").trim() : undefined;
    for (const f of (o.frazy ?? [o.fraza]).filter(Boolean) as string[]) {
      const poz = znajdzFraze(f);
      if (poz >= 0) klipy.push({ mp4, dl, t: czasPozycji(poz) + 2, nazwa: k, atrybucja, nakl: () => nakladka(String(o.podpis ?? o.tytul).slice(0, 80), "uleszka.net", ZNACZKI[o.rodzaj] ?? "Animacja 3D") });
      else console.log(`Klip 3D „${k}”: nie znalazłem frazy w tekście odcinka – pomijam to miejsce.`);
    }
  }
  const plikCC = join(folder, "nagrania-cc.json");
  for (const o of (existsSync(plikCC) ? JSON.parse(readFileSync(plikCC, "utf8")) : []) as NagranieCC[]) {
    if (!existsSync(o.plik)) { console.log(`Nagranie CC „${o.nazwa}”: brak pliku ${o.plik}`); continue; }
    const dl = dlugoscPliku(o.plik);
    const autor = o.autor.replace(/\s+/g, " ").trim();
    for (const f of (o.frazy ?? [o.fraza]).filter(Boolean) as string[]) {
      const poz = znajdzFraze(f);
      if (poz >= 0) klipy.push({ mp4: o.plik, dl, t: czasPozycji(poz) + 2, nazwa: o.nazwa, cc: o, nakl: () => nakladka(o.miejsce.slice(0, 60), `nagranie: ${autor.length > 40 ? `${autor.slice(0, 39)}…` : autor}, ${o.licencja} · ${o.serwis ?? "Wikimedia Commons"}`) });
      else console.log(`Nagranie CC „${o.nazwa}”: nie znalazłem frazy w tekście odcinka – pomijam.`);
    }
  }
}

// ---------- oś czasu: plansze, zdjęcia i klipy ----------
// plansze (tytułowa, rozdziałów, końcowa) mają stałe czasy; klipy i zdjęcia układane są w wolne miejsca:
// najpierw klipy (każdy dostaje tyle czasu, ile trwa), potem zdjęcia (najkrócej 6 s)
const wyj = join(folder, "youtube");
const klatki = join(wyj, "klatki");
rmSync(klatki, { recursive: true, force: true });
mkdirSync(klatki, { recursive: true });
type Zdarzenie = { t: number; plik: string; zrob: () => Promise<void>; twarde?: boolean; ruch?: number; klip?: Klip };
const zdarzenia: Zdarzenie[] = [];
const podtytul = artykuly.length === 1 && artykuly[0].tytul !== tytul ? `artykuł „${artykuly[0].tytul}”` : "";
const nr = (n: number) => join(klatki, `${String(n).padStart(4, "0")}.png`);
let n = 0;
// wstęp: animacja 3D pod zapowiedź (grafiki/3d/wideo/wstep/wersja-b/klip.mp4, wspólna dla odcinków); tytuł odcinka wchodzi na nią,
// gdy lektor mówi „Odcinek …” (z mowa.jsonl), i schodzi przed końcem zapowiedzi. Bez animacji albo z --bez-wstepu: plansza z okładką.
// Wersja A (przelot wśród rysunków Leszka) leży w grafiki/3d/wideo/wstep/klip.mp4. Licencje wstępu: atrybucja.txt obok klipu (idzie do opisu).
const WSTEP = "grafiki/3d/wideo/wstep/wersja-b/klip.mp4";
const WSTEP_ATRYBUCJA = join(dirname(WSTEP), "atrybucja.txt");
let wstepAtrybucja = "";
if (existsSync(WSTEP) && !process.argv.includes("--bez-wstepu")) {
  if (existsSync(WSTEP_ATRYBUCJA)) wstepAtrybucja = readFileSync(WSTEP_ATRYBUCJA, "utf8").trim();
  const linia = mowa ? readFileSync(plikMowy, "utf8").split("\n").map((l) => l.match(/^\{"start":(\d+),"end":\d+,"text":"\s*(.*)"\}\s*$/)).find((m) => m && Number(m[1]) < 40000 && /^odcinek\b/i.test(m[2])) : undefined;
  const od = linia ? Number(linia[1]) / 1000 : 14.3;
  const doT = Math.max(od + 6, Math.min(25, zapowiedzKoniec - 1));
  const w = linie(tytul, 24);
  // tytuł w górnej części kadru: w wersji B wolne niebo sięga do ok. y = 680 px (niżej kamienie Stonehenge)
  const y0 = H / 2 - ((w.length - 1) * 104 * 1.18) / 2 - 120;
  const tytulWstepu = () => zSvg(`${tlo.replace(/<rect[^>]*\/>\s*$/, "")}
    <text x="${W / 2}" y="${y0 - 120}" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="34" letter-spacing="10" fill="#e2a93f">${xml(etykieta.toUpperCase())}</text>
    ${w.map((x, i) => `<text x="${W / 2}" y="${y0 + i * 104 * 1.18}" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="104" fill="url(#z)" stroke="#05070c" stroke-opacity=".35" stroke-width="2">${xml(x)}</text>`).join("")}
    ${podtytul ? `<text x="${W / 2}" y="${y0 + w.length * 104 * 1.18 + 10}" text-anchor="middle" font-family="Georgia, serif" font-size="38" fill="#d7dbe4">${xml(podtytul)}</text>` : ""}`).png();
  zdarzenia.push({ t: 0, plik: nr(n++), twarde: true, zrob: async () => {}, klip: { mp4: WSTEP, dl: dlugoscPliku(WSTEP), t: 0, nazwa: "wstep", nakl: tytulWstepu, naklCzas: [od, doT] } });
} else { const p = nr(n++); zdarzenia.push({ t: 0, plik: p, twarde: true, zrob: () => planszaOkladki(etykieta, tytul, ["Leszek Klimek, uleszka.net (2004–2007)", podtytul || "Tekst bez zmian, czyta lektor AI"].filter(Boolean), p) }); }
const rozdzialAt = (t: number) => [...rozdzialy].reverse().find((r) => r.start <= t + 0.5)?.tytul ?? tytul;
for (const r of rozdzialy.slice(1, -1)) {
  if (rozdzialy.length <= 3) break; // jeden rozdział (np. zwiastun) – bez planszy rozdziału
  const p = nr(n++);
  zdarzenia.push({ t: r.start, plik: p, twarde: true, zrob: () => planszaRozdzialu(r.tytul, p) });
}
for (const k of klipy) zdarzenia.push({ t: k.t, plik: nr(n++), klip: k, zrob: async () => {} });
for (const z of zdjecia) {
  const p = nr(n++);
  zdarzenia.push({ t: z.t + (mowa ? 1 : 8), plik: p, ruch: 0.05, zrob: () => klatkaZdjecia(z.sciezka, (rozdzialAt(z.t) === tytul ? tytul : `${tytul} · ${rozdzialAt(z.t)}`).slice(0, 95), p) }); // +8 s: po planszy rozdziału
}
// zdjęcia miejsc: przy kolejnych wzmiankach kolejne zdjęcie (+14 s, żeby nie zderzać się ze zdjęciem z artykułu)
const dodajHq = (x: ZdjecieHQ, t: number) => {
  const p = nr(n++);
  hqPoKlatce.set(p, x);
  return { t, plik: p, ruch: 0.1, zrob: () => klatkaHQ(x.plik, x.m.nazwa.slice(0, 60), podpisAutora(x.z), p) } as Zdarzenie;
};
const wolne = new Map(hq.map((x) => [x.m, [...x.zdjecia]]));
for (const x of hq) x.poz.forEach((poz) => { const z = wolne.get(x.m)!.shift(); if (z) zdarzenia.push(dodajHq(z, czasPozycji(poz) + (mowa ? 3 : 14))); });
{ const p = nr(n++); zdarzenia.push({ t: zakonczenieStart, plik: p, twarde: true, zrob: () => planszaOkladki("Dziękuję za wysłuchanie", "Pełny tekst ze zdjęciami: uleszka.net", ["Rozmowa z archiwum przez AI: uleszka.net", "Kolejne odcinki: obserwuj kanał i podcast w Spotify"], p) }); }

const MIN = 6;
const zajmuje = (z: Zdarzenie) => (z.klip ? z.klip.dl : MIN);
const os: Zdarzenie[] = zdarzenia.filter((z) => z.twarde).sort((a, b) => a.t - b.t);
/** wstawia zdarzenie w najbliższe wolne miejsce nie wcześniej niż z.t (zdjęcie najwyżej 20 s, klip 30 s później); false, gdy się nie mieści */
const wstaw = (z: Zdarzenie) => {
  let t = z.t;
  for (let krok = 0; krok < 50; krok++) {
    const prev = [...os].reverse().find((x) => x.t <= t), next = os.find((x) => x.t > t);
    if (prev && t < prev.t + zajmuje(prev)) { t = prev.t + zajmuje(prev); continue; }
    if (next && next.t - t < Math.min(zajmuje(z), MIN)) { t = next.t + zajmuje(next); continue; }
    if (t - z.t > (z.klip ? 30 : 20) || t > zakonczenieStart - MIN) return false; // lepiej pominąć niż pokazać za późno
    z.t = t;
    os.push(z);
    os.sort((a, b) => a.t - b.t);
    return true;
  }
  return false;
};
const miekkie = zdarzenia.filter((z) => !z.twarde).sort((a, b) => Number(!!b.klip) - Number(!!a.klip) || a.t - b.t);
const pominiete = miekkie.filter((z) => !wstaw(z));
if (pominiete.some((z) => z.klip)) console.log(`Nie zmieściły się klipy: ${pominiete.filter((z) => z.klip).map((z) => z.klip!.nazwa).join(", ")}`);
// wypełnianie: obraz nie stoi w miejscu dłużej niż ok. 25–30 s (plansza rozdziału 8 s, po klipie najwyżej 6 s jego ostatniej klatki);
// wolne miejsca dostają zdjęcia miejsc z odcinka: najpierw nieużyte; gdy zabraknie – zdjęcie pokazane dotąd tylko raz
// i nie w ostatnich 10 minutach (każde zdjęcie najwyżej dwa razy w filmie); bez takiego przerwa zostaje dłuższym ujęciem
const DLUGO = { zdjecie: 25, plansza: 8, poKlipie: 6 };
const wzmiankiCzas = hq.flatMap((x) => x.poz.map((p) => ({ t: czasPozycji(p), m: x.m }))).sort((a, b) => a.t - b.t);
const ostatnio = new Map<string, number>(); // plik zdjęcia → kiedy ostatnio pokazane
const ileRazy = new Map<string, number>(); // plik zdjęcia → ile razy w filmie
const pokazane = (x: ZdjecieHQ, t: number) => { ostatnio.set(x.plik, t); ileRazy.set(x.plik, (ileRazy.get(x.plik) ?? 0) + 1); };
for (const z of os) { const x = hqPoKlatce.get(z.plik); if (x) pokazane(x, z.t); }
const wybierzZdjecie = (t: number): ZdjecieHQ | undefined => {
  const ost = [...wzmiankiCzas].reverse().find((w) => w.t <= t && wolne.get(w.m)?.length);
  if (ost) return wolne.get(ost.m)!.shift();
  const dowolne = [...wolne.values()].find((l) => l.length);
  if (dowolne) return dowolne.shift();
  const raz = (l: ZdjecieHQ[]) => l.filter((x) => (ileRazy.get(x.plik) ?? 0) < 2 && t - (ostatnio.get(x.plik) ?? -1e9) > 600)
    .sort((a, b) => (ostatnio.get(a.plik) ?? -1e9) - (ostatnio.get(b.plik) ?? -1e9))[0];
  const m = [...wzmiankiCzas].reverse().find((w) => w.t <= t)?.m;
  return (m && raz(hq.find((x) => x.m === m)?.zdjecia ?? [])) || raz(hq.flatMap((x) => x.zdjecia));
};
const bezZdjecia = new Set<string>(); // ujęcia, po których nie było już czym wypełnić przerwy
for (let proba = 0; proba < 3000; proba++) {
  let dodano = false;
  for (let i = 1; i < os.length - 1 && !dodano; i++) { // i = 0: plansza tytułowa (albo wstęp) stoi przez całą zapowiedź
    const a = os[i];
    if (a.t >= zakonczenieStart || bezZdjecia.has(a.plik)) continue;
    const limit = a.klip ? a.klip.dl + DLUGO.poKlipie : a.twarde ? DLUGO.plansza : DLUGO.zdjecie;
    const dl = os[i + 1].t - a.t;
    if (dl <= limit + MIN) continue;
    const t = a.t + (a.klip ? a.klip.dl : a.twarde ? DLUGO.plansza : Math.min(DLUGO.zdjecie, dl / 2));
    const x = wybierzZdjecie(t);
    if (!x) { bezZdjecia.add(a.plik); continue; }
    pokazane(x, t);
    os.push(dodajHq(x, t));
    os.sort((p, q) => p.t - q.t);
    dodano = true;
  }
  if (!dodano) break;
}
// zamiast powtórek: lista miejsc, gdzie zabrakło materiału – tam trzeba dobrać zdjęcia albo nagrania (nagrania-cc.json) lub klip 3D
if (bezZdjecia.size) console.log(`Zabrakło zdjęć bez powtórek w ${bezZdjecia.size} miejscach: ${os.filter((z) => bezZdjecia.has(z.plik)).map((z) => czas(z.t)).join(", ")} – dobierz zdjęcia lub nagrania.`);
{
  const dlugosci = os.map((z, i) => ({ z, d: (os[i + 1]?.t ?? dlugosc) - z.t - (z.klip ? z.klip.dl : 0) })).filter((x) => x.z.t < zakonczenieStart && x.z !== os[0]);
  const najdl = dlugosci.reduce((m, x) => (x.d > m.d ? x : m), dlugosci[0]);
  // podsumowanie po rozdziałach: ile ujęć, klipów i powtórzonych zdjęć (gdzie przydałyby się nowe klipy)
  const widzianeHq = new Set<string>();
  const statyRozdz = rozdzialy.slice(1, -1).map((r) => ({ r, ujec: 0, klipow: 0, powtorek: 0, minut: 0 }));
  statyRozdz.forEach((x, i) => { x.minut = ((statyRozdz[i + 1]?.r.start ?? zakonczenieStart) - x.r.start) / 60; });
  for (const z of os) {
    const st = [...statyRozdz].reverse().find((x) => x.r.start <= z.t + 0.5);
    if (!st) continue;
    st.ujec++;
    if (z.klip) st.klipow++;
    const x = hqPoKlatce.get(z.plik);
    if (x) { if (widzianeHq.has(x.plik)) st.powtorek++; widzianeHq.add(x.plik); }
  }
  for (const x of statyRozdz) console.log(`  ${x.r.tytul.slice(0, 45).padEnd(45)} ${x.minut.toFixed(1).padStart(5)} min, ${String(x.ujec).padStart(3)} ujęć (co ${Math.round((x.minut * 60) / Math.max(1, x.ujec))} s), klipów ${x.klipow}, powtórzonych zdjęć ${x.powtorek}`);
  console.log(`Najdłużej stojący obraz: ${Math.round(najdl.d)} s (${czas(najdl.z.t)}); ujęć dłuższych niż 30 s: ${dlugosci.filter((x) => x.d > 30).length}.`);
}
const uzyteHq = os.map((z) => hqPoKlatce.get(z.plik)).filter((x): x is ZdjecieHQ => !!x);
const uzyteKlipy = os.filter((z) => z.klip).map((z) => z.klip!);
for (const z of os.filter((x) => x.klip)) console.log(`  ${czas(z.t)}  ${z.klip!.cc ? "nagranie" : "3D"}: ${z.klip!.nazwa} (${z.klip!.dl.toFixed(1)} s)`);
console.log(`Nagranie ${czas(dlugosc)}, ${rozdzialy.length} rozdziałów, ${zdjecia.length} zdjęć z artykułu, ${uzyteHq.length} zdjęć wysokiej jakości, ${uzyteKlipy.length} klipów (${uzyteKlipy.filter((k) => k.cc).length} nagrań CC), ${os.length} ujęć.`);

// --zakres 600-900: tylko ujęcia z tego przedziału (w sekundach) – szybki podgląd do sprawdzenia
const zakres = (() => { const i = process.argv.indexOf("--zakres"); if (i < 0) return null; const [a, b] = process.argv[i + 1].split("-").map(Number); return { a, b }; })();
// --tylko-opis: bez rysowania i składania wideo, tylko miniatura, opis.txt i autorzy-zdjec.txt (np. po zmianie licencji klipu)
if (!process.argv.includes("--tylko-opis")) {
const FPS = 25;
const klatkaNr = (t: number) => Math.round(t * FPS);
const doZrobienia = os.map((z, i) => ({ z, i, f0: klatkaNr(z.t), f1: klatkaNr(os[i + 1]?.t ?? dlugosc) }))
  .filter((x) => x.f1 > x.f0 && (!zakres || (x.f1 / FPS > zakres.a && x.f0 / FPS < zakres.b)));
console.log(`Rysuję ${doZrobienia.length} ujęć…`);
for (const { z } of doZrobienia) await z.zrob();

// ---------- ujęcia wideo: zdjęcia z powolnym ruchem kamery (przybliżenie, przesunięcie), klipy z nakładką, plansze bez ruchu ----------
const ffmpegAsync = (args: string[]) => new Promise<void>((ok, blad) => execFile("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", ...args], (e) => (e ? blad(e) : ok())));
const KODEK = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-r", String(FPS), "-g", String(FPS * 2), "-an"];
const RUCHY: [number, number][] = [[0.5, 0.5], [0.3, 0.7], [0.7, 0.3], [0.5, 0.5]];
/** wejścia ffmpeg i graf filtrów jednego ujęcia; wynik grafu: [o] */
async function grafUjecia(z: Zdarzenie, i: number, klatek: number): Promise<{ wejscia: string[]; graf: string }> {
  if (z.klip) {
    const nakl = join(klatki, `klip-${i}-n.png`);
    if (!existsSync(nakl)) await z.klip.nakl().toFile(nakl);
    const zapas = Math.max(0, klatek / FPS - z.klip.dl + 1); // gdy lektor mówi dłużej, ostatnia klatka klipu zostaje
    const nc = z.klip.naklCzas;
    const n = nc ? `[1:v]format=rgba,fade=in:st=${nc[0].toFixed(2)}:d=0.8:alpha=1,fade=out:st=${(nc[1] - 0.8).toFixed(2)}:d=0.8:alpha=1[n]` : "[1:v]null[n]";
    return { wejscia: ["-i", z.klip.mp4, "-loop", "1", "-framerate", String(FPS), "-i", nakl],
      graf: `[0:v]fps=${FPS},scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,tpad=stop_mode=clone:stop_duration=${zapas.toFixed(2)}[v];${n};[v][n]overlay=0:0[o]` };
  }
  const nakl = naklPlik(z.plik), maNakl = existsSync(nakl);
  const A = z.ruch ?? 0;
  let obraz = "[0:v]setsar=1[v]";
  if (A) {
    const zoom = i % 2 ? `1+${A}*on/${klatek}` : `1+${A}-${A}*on/${klatek}`; // na przemian przybliżenie i oddalenie
    const [p0, p1] = RUCHY[i % RUCHY.length];
    // obraz powiększony do 4K przed zoompan: ruch bez drgań (zoompan zaokrągla położenie do pełnych pikseli)
    obraz = `[0:v]scale=${W * 2}:${H * 2}:flags=lanczos,zoompan=z='${zoom}':x='(iw-iw/zoom)*(${p0}+${(p1 - p0).toFixed(2)}*on/${klatek})':y='(ih-ih/zoom)*0.5':d=1:s=${W}x${H}:fps=${FPS},setsar=1[v]`;
  }
  return { wejscia: ["-loop", "1", "-framerate", String(FPS), "-i", z.plik, ...(maNakl ? ["-loop", "1", "-i", nakl] : [])],
    graf: `${obraz};${maNakl ? "[v][1:v]overlay=0:0[o]" : "[v]null[o]"}` };
}
// przejścia: ostatnie klatki ujęcia płynnie przenikają w pierwszą klatkę następnego (dokumentalny „cross dissolve”);
// dłużej przy wstępie i planszach rozdziałów. Ujęcia liczą się równolegle, bo pierwszą klatkę następnego ujęcia
// rysujemy osobno, zanim powstanie samo ujęcie.
const PRZEJSCIE = { zwykle: 0.6, plansza: 1.0 };
const ujecia: string[] = [];
let gotowe = 0;
const kolejka = doZrobienia.map((x, k) => ({ ...x, plik: join(klatki, `ujecie-${String(x.i).padStart(4, "0")}.mp4`), pierwsza: join(klatki, `pierwsza-${String(x.i).padStart(4, "0")}.png`), nast: doZrobienia[k + 1] }));
const pierwsze = [...kolejka.slice(1)];
async function pierwszaKlatka() {
  for (let x = pierwsze.shift(); x; x = pierwsze.shift()) {
    const g = await grafUjecia(x.z, x.i, x.f1 - x.f0);
    await ffmpegAsync([...g.wejscia, "-filter_complex", `${g.graf};[o]format=rgb24[f]`, "-map", "[f]", "-frames:v", "1", x.pierwsza]);
  }
}
await Promise.all([pierwszaKlatka(), pierwszaKlatka(), pierwszaKlatka(), pierwszaKlatka()]);
async function pracownik() {
  for (let x = kolejka.shift(); x; x = kolejka.shift()) {
    const klatek = x.f1 - x.f0;
    const g = await grafUjecia(x.z, x.i, klatek);
    const n = g.wejscia.filter((a) => a === "-i").length; // numer wejścia z klatką następnego ujęcia
    const dl = x.nast ? (x.z.twarde || x.nast.z.twarde || x.i === 0 ? PRZEJSCIE.plansza : PRZEJSCIE.zwykle) : 0;
    const dlK = Math.min(Math.round(dl * FPS), Math.floor(klatek / 3));
    const przejscie = dlK > 0 && x.nast ? `;[${n}:v]format=rgba,fade=in:st=${((klatek - dlK) / FPS).toFixed(3)}:d=${(dlK / FPS).toFixed(3)}:alpha=1[x];[o][x]overlay=0:0,format=yuv420p[f]` : ";[o]format=yuv420p[f]";
    await ffmpegAsync([...g.wejscia, ...(dlK > 0 && x.nast ? ["-loop", "1", "-framerate", String(FPS), "-i", join(klatki, `pierwsza-${String(x.nast.i).padStart(4, "0")}.png`)] : []),
      "-filter_complex", g.graf + przejscie, "-map", "[f]", ...KODEK, "-frames:v", String(klatek), x.plik]);
    if (++gotowe % 20 === 0) console.log(`  ujęcia: ${gotowe}/${doZrobienia.length}`);
  }
}
for (const x of kolejka) ujecia.push(x.plik);
await Promise.all([pracownik(), pracownik(), pracownik()]);
writeFileSync(join(klatki, "lista.txt"), ujecia.map((p) => `file '${resolve(p).replace(/\\/g, "/")}'`).join("\n") + "\n", "utf8");
console.log("Składam wideo z dźwiękiem (ffmpeg)…");
const start = zakres ? doZrobienia[0].f0 / FPS : 0;
const koniecWideo = zakres ? Math.min(dlugosc, doZrobienia[doZrobienia.length - 1].f1 / FPS) : dlugosc;
const plikWideo = join(wyj, zakres ? `wideo-probka-${zakres.a}-${zakres.b}.mp4` : "wideo.mp4");
execFileSync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", join(klatki, "lista.txt"), "-ss", start.toFixed(2), "-i", mp3,
  "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", (koniecWideo - start).toFixed(2), "-movflags", "+faststart", plikWideo], { stdio: "inherit" });
if (zakres) { rmSync(klatki, { recursive: true, force: true }); console.log(`Gotowe: ${plikWideo}`); process.exit(0); }
} // koniec części bez --tylko-opis

// ---------- miniatura 1280×720: największe zdjęcie z artykułu w tle, tytuł złotymi literami ----------
// miniatura: zdjęcie wysokiej jakości najczęściej wspominanego miejsca (poziome), a bez niego największe zdjęcie z artykułu
const najwazniejsze = [...hq].sort((a, b) => b.poz.length - a.poz.length)[0]?.zdjecia.find((x) => x.z.szer / x.z.wys >= 1.3);
// --miniatura <obraz>: własne tło miniatury (np. kadr.jpg animacji 3D)
const wlasnaMiniatura = process.argv[process.argv.indexOf("--miniatura") + 1];
const wybrane = process.argv.includes("--miniatura") && existsSync(wlasnaMiniatura) ? wlasnaMiniatura : najwazniejsze ? najwazniejsze.plik : zdjecia.length ? (await Promise.all(zdjecia.map(async (z) => ({ z, m: await sharp(z.sciezka).metadata() })))).sort((a, b) => (b.m.width ?? 0) * (b.m.height ?? 0) - (a.m.width ?? 0) * (a.m.height ?? 0))[0].z.sciezka : "podcast/okladka.jpg";
const mt = linie(tytul, 18);
const napisy = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs>
  <linearGradient id="c" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#05070c" stop-opacity=".95"/><stop offset=".6" stop-color="#05070c" stop-opacity=".6"/><stop offset="1" stop-color="#05070c" stop-opacity=".1"/></linearGradient>
  <linearGradient id="z" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6e0"/><stop offset=".6" stop-color="#f0c46f"/><stop offset="1" stop-color="#b47a22"/></linearGradient></defs>
  <rect width="1280" height="720" fill="url(#c)"/>
  <text x="70" y="130" font-family="Arial, sans-serif" font-weight="700" font-size="34" letter-spacing="6" fill="#e2a93f">${xml(etykieta.toUpperCase())}</text>
  ${mt.map((w, i) => `<text x="70" y="${250 + i * 104}" font-family="Georgia, serif" font-weight="700" font-size="96" fill="url(#z)">${xml(w)}</text>`).join("")}
  <text x="70" y="660" font-family="Georgia, serif" font-size="34" fill="#d7dbe4">${xml(PODCAST)} · Leszek Klimek</text></svg>`);
await sharp(wybrane).resize(1280, 720, { fit: "cover" }).modulate({ brightness: 0.8 }).composite([{ input: napisy, left: 0, top: 0 }]).jpeg({ quality: 88 }).toFile(join(wyj, "miniatura.jpg"));

// ---------- opis do YouTube: opis odcinka + orientacyjne rozdziały ----------
const opisSpotify = (opisMd.split("## Opis odcinka (Spotify)")[1] ?? "").replace(/^\s*\*\*Tytuł:\*\*.*$/m, "").replace(/^\s*\*\*Typ odcinka:\*\*.*$/m, "").trim();
const znaczniki = rozdzialy.map((r) => `${czas(r.start)} ${r.tytul}`).join("\n");
// atlas i autorzy zdjęć (licencje CC BY i CC BY-SA wymagają podania autora i licencji)
const miejscaWOpisie = hq.map((x) => `${x.m.nazwa}: https://uleszka.net/atlas/${x.m.slug}.html`);
const autorzy = [...new Map(uzyteHq.map((x) => [x.z.plik, x])).values()].map(
  (x) => `${x.m.nazwa} – fot. ${x.z.autor.replace(/\s+/g, " ").trim()}, ${x.z.licencja}${x.z.licencja_url ? ` (${x.z.licencja_url})` : ""}, ${x.z.strona}`,
);
// YouTube przyjmuje opis do 5000 znaków: pełna lista autorów idzie do osobnego pliku (np. na przypięty komentarz),
// a w opisie zostaje krótka informacja i linki do kart miejsc (tam każde zdjęcie ma autora i licencję)
const nagraniaCC = [...new Map(uzyteKlipy.filter((k) => k.cc).map((k) => [k.cc!.strona, k.cc!])).values()].map(
  (o) => `${o.miejsce} (${o.serwis ?? "Wikimedia Commons"}) – nagranie: ${o.autor.replace(/\s+/g, " ").trim()}, ${o.licencja}${o.licencja_url ? ` (${o.licencja_url})` : ""}, ${o.strona} – użyto fragmentu, kadr przycięty i przeskalowany`,
);
const ma3d = uzyteKlipy.some((k) => !k.cc);
const zrodla3d = [...new Set(uzyteKlipy.filter((k) => !k.cc && k.atrybucja).flatMap((k) => k.atrybucja!.split("\n").map((s) => s.trim()).filter(Boolean)))];
const INFO_3D = "Animacje 3D (Blender) na podstawie rysunków Leszka Klimka i publicznych danych; skrypty i źródła: https://github.com/jokerwader/uleszka-archiwum/tree/main/grafiki/3d/wideo";
if (autorzy.length || nagraniaCC.length) writeFileSync(join(wyj, "autorzy-zdjec.txt"), [
  autorzy.length ? `Zdjęcia współczesne w filmie (Wikimedia Commons i Openverse):\n${autorzy.join("\n")}\n` : "",
  nagraniaCC.length ? `Nagrania wideo w filmie:\n${nagraniaCC.join("\n")}\n` : "",
  ma3d ? `${INFO_3D}\n` : "",
  zrodla3d.length ? `Cudze materiały w animacjach 3D:\n${zrodla3d.join("\n")}\n` : "",
  wstepAtrybucja ? `${wstepAtrybucja}\n` : "",
  "Zdjęcia archiwalne: artykuły Leszka Klimka na uleszka.net (2004–2007).\n",
].filter(Boolean).join("\n"), "utf8");
const glowna = `TYTUŁ:\n${tytul}${rodzaj === "Zwiastun" ? "" : ` | ${PODCAST} – ${rodzaj.toLowerCase()}`}\n\nOPIS:\n${opisSpotify}\n\nPodcast w Spotify: ${SPOTIFY}\n\nRozdziały:\n${znaczniki}\n`;
const zdjeciaInfo = autorzy.length ? `\nZdjęcia współczesne: Wikimedia Commons i Openverse (${autorzy.length}, wolne licencje) – autor i licencja w kadrze i na kartach miejsc w atlasie. Zdjęcia archiwalne: artykuły Leszka Klimka (2004–2007).\n` : "";
const klipyInfo = `${nagraniaCC.length ? `\nNagrania wideo: ${[...new Set(uzyteKlipy.filter((k) => k.cc).map((k) => k.cc!.serwis ?? "Wikimedia Commons"))].join(", ")} (${nagraniaCC.length}) – autor i licencja w kadrze; pełna lista w komentarzu.\n` : ""}${ma3d ? `\n${INFO_3D}\n` : ""}${zrodla3d.length ? `${ma3d ? "" : "\n"}W animacjach: ${zrodla3d.map((s) => s.replace(/\.$/, "")).join("; ")}.\n` : ""}${wstepAtrybucja ? `${ma3d ? "" : "\n"}${wstepAtrybucja}\n` : ""}`;
let miejscaTxt = miejscaWOpisie.length ? `\nMiejsca z odcinka na mapie (Atlas Leszka):\n${miejscaWOpisie.join("\n")}\n` : "";
const LIMIT = 4900 + "TYTUŁ:\n".length + tytul.length + 60; // ok. 4900 znaków samego opisu
for (let ile = miejscaWOpisie.length; ile > 0 && (glowna + miejscaTxt + zdjeciaInfo + klipyInfo).length > LIMIT; ile--)
  miejscaTxt = `\nMiejsca z odcinka na mapie (Atlas Leszka):\n${miejscaWOpisie.slice(0, ile - 1).join("\n")}\n…i więcej: https://uleszka.net/atlas/\n`;
writeFileSync(join(wyj, "opis.txt"), glowna + miejscaTxt + zdjeciaInfo + klipyInfo, "utf8");
rmSync(klatki, { recursive: true, force: true });
console.log(`Gotowe: ${process.argv.includes("--tylko-opis") ? "" : `${join(wyj, "wideo.mp4")}, `}miniatura.jpg, opis.txt, autorzy-zdjec.txt`);
console.log("Rozdziały w opisie są orientacyjne (liczone z długości tekstu) – przed publikacją sprawdź je w odtwarzaczu.");
