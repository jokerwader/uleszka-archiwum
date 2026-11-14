/**
 * Grafiki kanału YouTube w wymiarach YouTube, z tej samej sceny 3D co okładka podcastu (podcast/scena-kwadrat.jpg):
 *   baner.jpg        2560×1440 – napisy w strefie widocznej na każdym urządzeniu (1546×423 na środku)
 *   profil.jpg       800×800   – świecąca piramida (YouTube wyświetla ją w kółku, nawet 98×98 px)
 *   znak-wodny.png   150×150   – piramida z okiem na przezroczystym tle (pokazywana w rogu filmów)
 * Wynik: podcast/youtube-kanal/. Uruchomienie: npx tsx scripts/grafika-youtube.ts
 */
import { mkdirSync } from "node:fs";
import sharp from "sharp";

const WYJ = "podcast/youtube-kanal";
mkdirSync(WYJ, { recursive: true });
const SCENA = "podcast/scena-kwadrat.jpg"; // 1585×1600, piramida na środku, światło nad wierzchołkiem
const ZLOTO = `<linearGradient id="z" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6e0"/><stop offset=".55" stop-color="#f0c46f"/><stop offset="1" stop-color="#b47a22"/></linearGradient>`;

// ---------- baner 2560×1440 ----------
{
  const W = 2560, H = 1440;
  // scena po prawej, wtopiona w nocne tło; piramida i światło trafiają w pas widoczny na komputerze (wysokość 423 px na środku)
  // scena 1500×1514 od x = X0 – przycięta do banera, z lewą krawędzią wygaszoną miękko (bez widocznej linii)
  const X0 = 1400, SZ = W - X0;
  const maska = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${SZ}" height="${H}"><defs>
    <linearGradient id="m" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".45" stop-color="#fff" stop-opacity="1"/></linearGradient></defs>
    <rect width="${SZ}" height="${H}" fill="url(#m)"/></svg>`);
  const scena = await sharp(SCENA).resize(1500, 1514).extract({ left: 0, top: 40, width: SZ, height: H }).ensureAlpha()
    .composite([{ input: maska, blend: "dest-in" }]).png().toBuffer();
  const tlo = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs>
    <radialGradient id="n" cx="65%" cy="35%" r="80%"><stop offset="0" stop-color="#16244a"/><stop offset=".55" stop-color="#090d18"/><stop offset="1" stop-color="#05070c"/></radialGradient></defs>
    <rect width="${W}" height="${H}" fill="url(#n)"/></svg>`);
  const napisy = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs>${ZLOTO}
    <linearGradient id="l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#05070c" stop-opacity=".97"/><stop offset=".42" stop-color="#05070c" stop-opacity=".9"/><stop offset=".62" stop-color="#05070c" stop-opacity=".2"/><stop offset=".8" stop-color="#05070c" stop-opacity="0"/><stop offset="1" stop-color="#05070c" stop-opacity=".55"/></linearGradient>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070c" stop-opacity=".9"/><stop offset=".3" stop-color="#05070c" stop-opacity="0"/><stop offset=".7" stop-color="#05070c" stop-opacity="0"/><stop offset="1" stop-color="#05070c" stop-opacity=".9"/></linearGradient>
    <linearGradient id="k" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e2a93f" stop-opacity=".9"/><stop offset="1" stop-color="#e2a93f" stop-opacity="0"/></linearGradient></defs>
    <rect width="${W}" height="${H}" fill="url(#l)"/><rect width="${W}" height="${H}" fill="url(#g)"/>
    <text x="560" y="600" font-family="Arial, sans-serif" font-weight="700" font-size="30" letter-spacing="9" fill="#e2a93f">PODCAST · TEKSTY LESZKA KLIMKA</text>
    <text x="552" y="730" font-family="Georgia, serif" font-weight="700" font-size="104" fill="url(#z)">Uwierz we własny rozum</text>
    <rect x="560" y="770" width="560" height="2" fill="url(#k)"/>
    <text x="560" y="830" font-family="Georgia, serif" font-size="38" fill="#d7dbe4">Strona uleszka.net (2004–2007) czytana słowo w słowo</text>
    <text x="560" y="885" font-family="Georgia, serif" font-size="32" fill="#9aa3b5">Dawne cywilizacje · potop · Atlantyda · nowe odcinki co tydzień</text></svg>`);
  await sharp(tlo).composite([{ input: scena, left: X0, top: 0 }, { input: napisy, left: 0, top: 0 }]).jpeg({ quality: 90 }).toFile(`${WYJ}/baner.jpg`);
}

// ---------- zdjęcie profilowe 800×800: kadr na świecącą piramidę ----------
await sharp(SCENA).extract({ left: 243, top: 280, width: 1100, height: 1100 }).resize(800, 800).modulate({ brightness: 1.05 }).jpeg({ quality: 92 }).toFile(`${WYJ}/profil.jpg`);

// ---------- znak wodny 150×150: piramida z okiem (jak medalion na stronie), przezroczyste tło ----------
await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 64 64"><defs>${ZLOTO}</defs>
  <circle cx="32" cy="32" r="30" fill="#05070c" fill-opacity=".55" stroke="#e2a93f" stroke-width="1.6"/>
  <path d="M32 12 L52 46 H12 Z" fill="none" stroke="url(#z)" stroke-width="3" stroke-linejoin="round"/>
  <path d="M22 35 q10 -8 20 0 q-10 8 -20 0z" fill="none" stroke="#f0c46f" stroke-width="2"/>
  <circle cx="32" cy="35" r="3" fill="#f0c46f"/></svg>`)).resize(150, 150).png().toFile(`${WYJ}/znak-wodny.png`);

console.log(`Gotowe: ${WYJ}/baner.jpg, profil.jpg, znak-wodny.png`);
