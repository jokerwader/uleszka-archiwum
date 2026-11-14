/**
 * Wideo odcinka na YouTube: nagranie MP3 + zdjęcia Leszka z artykułu, pokazywane mniej więcej wtedy,
 * gdy lektor czyta fragment obok zdjęcia; plansze z tytułami rozdziałów, plansza na zapowiedź i na zakończenie.
 * Powstają też miniatura (1280×720) i opis do YouTube z orientacyjnymi rozdziałami (znacznikami czasu).
 *
 *   npx tsx scripts/wideo.ts <folder odcinka> <nagranie.mp3>
 *   np. npx tsx scripts/wideo.ts podcast/01-potop-czy-tylko-jeden "C:/Users/…/ElevenLabs_uLeszka_-_Potop.mp3"
 *
 * Wynik w <folder>/youtube/: wideo.mp4, miniatura.jpg, opis.txt (folder jest w .gitignore – pliki są duże).
 * Czasy są szacowane z długości tekstu (lektor czyta w stałym tempie), więc zdjęcie może się pojawić
 * kilkanaście sekund wcześniej albo później niż jego fragment. Wymaga ffmpeg i ffprobe.
 */
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import sharp from "sharp";
import { Archiwum, type Dokument } from "../src/archiwum.js";

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

// ---------- czasy: długość nagrania dzielona proporcjonalnie do liczby znaków rozdziałów ----------
const dlugosc = Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], { encoding: "utf8" }).trim());
if (!(dlugosc > 0)) throw new Error("Nie udało się odczytać długości nagrania");
const razem = rozdzialy.reduce((s, r) => s + r.znaki, 0);
let t0 = 0;
for (const r of rozdzialy) { r.start = t0; t0 += (r.znaki / razem) * dlugosc; }
const zapowiedzKoniec = rozdzialy[1]?.start ?? 0;
const zakonczenieStart = rozdzialy[rozdzialy.length - 1].start;

// zdjęcia: pozycja w tekście artykułu przeliczona na czas – kotwicami są początki rozdziałów (ich tytuły w tekście)
const tresc = dokumenty.map((d) => d.tresc).join("\n\n");
const kotwice: [number, number][] = [[0, zapowiedzKoniec]];
for (const r of rozdzialy.slice(1, -1)) {
  const poz = tresc.indexOf(r.tytul, kotwice[kotwice.length - 1][0]);
  if (poz > kotwice[kotwice.length - 1][0]) kotwice.push([poz, r.start]);
}
kotwice.push([tresc.length, zakonczenieStart]);
const czasPozycji = (poz: number) => {
  for (let i = 1; i < kotwice.length; i++)
    if (poz <= kotwice[i][0]) { const [p0, c0] = kotwice[i - 1], [p1, c1] = kotwice[i]; return c0 + ((poz - p0) / Math.max(1, p1 - p0)) * (c1 - c0); }
  return zakonczenieStart;
};
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

// ---------- plansze (SVG → PNG 1920×1080) ----------
const tlo = `<defs><radialGradient id="g" cx="70%" cy="0%" r="90%"><stop offset="0" stop-color="#1b2a4d"/><stop offset=".6" stop-color="#0a0d16"/><stop offset="1" stop-color="#05070c"/></radialGradient>
  <linearGradient id="z" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6e0"/><stop offset=".6" stop-color="#f0c46f"/><stop offset="1" stop-color="#b47a22"/></linearGradient></defs>
  <rect width="${W}" height="${H}" fill="url(#g)"/>`;
const tekstSvg = (wiersze: string[], x: number, y: number, rozmiar: number, styl: string) =>
  wiersze.map((w, i) => `<text x="${x}" y="${y + i * rozmiar * 1.18}" font-size="${rozmiar}" ${styl}>${xml(w)}</text>`).join("");
const stopkaSvg = `<text x="120" y="${H - 70}" font-family="Georgia, serif" font-size="30" fill="#9aa3b5">${xml(PODCAST)} · Leszek Klimek · uleszka.net</text>`;
const zSvg = (svg: string) => sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${svg}</svg>`));

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
async function klatkaZdjecia(sciezka: string, podpis: string, plik: string) {
  const tloZdj = await sharp(sciezka).flatten({ background: "#0b0d12" }).resize(W, H, { fit: "cover" }).blur(40).modulate({ brightness: 0.35 }).toBuffer();
  // małe zdjęcia z 2004 r. (często 150 px wysokości) powiększamy najwyżej 4 razy, żeby nie były rozmyte
  const org = await sharp(sciezka).metadata();
  const skala = Math.min((W - 200) / (org.width ?? 1), (H - 240) / (org.height ?? 1), 4);
  const zdj = await sharp(sciezka).resize(Math.round((org.width ?? 1) * skala), Math.round((org.height ?? 1) * skala), { kernel: "lanczos3" }).png().toBuffer();
  const m = await sharp(zdj).metadata();
  const pasek = await zSvg(`<defs><linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070c" stop-opacity="0"/><stop offset="1" stop-color="#05070c" stop-opacity=".9"/></linearGradient></defs>
    <rect y="${H - 170}" width="${W}" height="170" fill="url(#p)"/>
    <text x="60" y="${H - 50}" font-family="Georgia, serif" font-size="32" fill="#f0c46f">${xml(podpis)}</text>
    <text x="${W - 60}" y="${H - 50}" text-anchor="end" font-family="Georgia, serif" font-size="28" fill="#9aa3b5">uleszka.net</text>`).png().toBuffer();
  await sharp(tloZdj)
    .composite([{ input: zdj, left: Math.round((W - (m.width ?? 0)) / 2), top: Math.round((H - 100 - (m.height ?? 0)) / 2) }, { input: pasek, left: 0, top: 0 }])
    .png().toFile(plik);
}

// ---------- oś czasu: plansze i zdjęcia; każda klatka trwa do następnej (najkrócej 6 s) ----------
const wyj = join(folder, "youtube");
const klatki = join(wyj, "klatki");
rmSync(klatki, { recursive: true, force: true });
mkdirSync(klatki, { recursive: true });
type Zdarzenie = { t: number; plik: string; zrob: () => Promise<void> };
const zdarzenia: Zdarzenie[] = [];
const podtytul = artykuly.length === 1 && artykuly[0].tytul !== tytul ? `artykuł „${artykuly[0].tytul}”` : "";
const nr = (n: number) => join(klatki, `${String(n).padStart(4, "0")}.png`);
let n = 0;
{ const p = nr(n++); zdarzenia.push({ t: 0, plik: p, zrob: () => planszaOkladki(etykieta, tytul, ["Leszek Klimek, uleszka.net (2004–2007)", podtytul || "Tekst bez zmian, czyta lektor AI"].filter(Boolean), p) }); }
const rozdzialAt = (t: number) => [...rozdzialy].reverse().find((r) => r.start <= t + 0.5)?.tytul ?? tytul;
for (const r of rozdzialy.slice(1, -1)) {
  if (rozdzialy.length <= 3) break; // jeden rozdział (np. zwiastun) – bez planszy rozdziału
  const p = nr(n++);
  zdarzenia.push({ t: r.start, plik: p, zrob: () => planszaRozdzialu(r.tytul, p) });
}
for (const z of zdjecia) {
  const p = nr(n++);
  zdarzenia.push({ t: z.t + 8, plik: p, zrob: () => klatkaZdjecia(z.sciezka, (rozdzialAt(z.t) === tytul ? tytul : `${tytul} · ${rozdzialAt(z.t)}`).slice(0, 95), p) }); // +8 s: po planszy rozdziału
}
{ const p = nr(n++); zdarzenia.push({ t: zakonczenieStart, plik: p, zrob: () => planszaOkladki("Dziękuję za wysłuchanie", "Pełny tekst ze zdjęciami: uleszka.net", ["Rozmowa z archiwum przez AI: uleszka.net", "Kolejne odcinki: obserwuj kanał i podcast w Spotify"], p) }); }
zdarzenia.sort((a, b) => a.t - b.t);
const MIN = 6;
const os: Zdarzenie[] = [];
for (const z of zdarzenia) {
  const ost = os[os.length - 1];
  const koncowa = z.t === zakonczenieStart;
  if (ost && z.t - ost.t < MIN && !koncowa) { if (ost.t + MIN < zakonczenieStart - MIN) { z.t = ost.t + MIN; os.push(z); } continue; }
  os.push(z);
}
os.sort((a, b) => a.t - b.t);
console.log(`Nagranie ${czas(dlugosc)}, ${rozdzialy.length} rozdziałów, ${zdjecia.length} zdjęć, ${os.length} klatek – rysuję…`);
for (const z of os) await z.zrob();

// lista dla ffmpeg (concat): każda klatka z czasem trwania do następnej; ostatnią trzeba powtórzyć
const lista = os.map((z, i) => `file '${resolve(z.plik).replace(/\\/g, "/")}'\nduration ${(((os[i + 1]?.t ?? dlugosc) - z.t) || 1).toFixed(2)}`).join("\n");
writeFileSync(join(klatki, "lista.txt"), `${lista}\nfile '${resolve(os[os.length - 1].plik).replace(/\\/g, "/")}'\n`, "utf8");
console.log("Składam wideo (ffmpeg)…");
execFileSync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", join(klatki, "lista.txt"), "-i", mp3,
  "-map", "0:v", "-map", "1:a", "-vf", "fps=2,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "22",
  "-c:a", "aac", "-b:a", "192k", "-t", dlugosc.toFixed(2), "-movflags", "+faststart", join(wyj, "wideo.mp4")], { stdio: "inherit" });

// ---------- miniatura 1280×720: największe zdjęcie z artykułu w tle, tytuł złotymi literami ----------
const wybrane = zdjecia.length ? (await Promise.all(zdjecia.map(async (z) => ({ z, m: await sharp(z.sciezka).metadata() })))).sort((a, b) => (b.m.width ?? 0) * (b.m.height ?? 0) - (a.m.width ?? 0) * (a.m.height ?? 0))[0].z.sciezka : "podcast/okladka.jpg";
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
writeFileSync(join(wyj, "opis.txt"), `TYTUŁ:\n${tytul}${rodzaj === "Zwiastun" ? "" : ` | ${PODCAST} – ${rodzaj.toLowerCase()}`}\n\nOPIS:\n${opisSpotify}\n\nPodcast w Spotify: ${SPOTIFY}\n\nRozdziały:\n${znaczniki}\n`, "utf8");
rmSync(klatki, { recursive: true, force: true });
console.log(`Gotowe: ${join(wyj, "wideo.mp4")}, miniatura.jpg, opis.txt`);
console.log("Rozdziały w opisie są orientacyjne (liczone z długości tekstu) – przed publikacją sprawdź je w odtwarzaczu.");
