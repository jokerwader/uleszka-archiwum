/**
 * Okładka podcastu (3000 × 3000 px, wymagania Spotify i Apple Podcasts): kadr sceny 3D ze strony
 * (podcast/scena-kwadrat.jpg) z napisem. Wynik: podcast/okladka.jpg
 * Uruchomienie: npx tsx scripts/okladka-podcastu.ts
 */
import sharp from "sharp";

const B = 3000;
const napisy = `<svg xmlns="http://www.w3.org/2000/svg" width="${B}" height="${B}" viewBox="0 0 ${B} ${B}">
  <defs>
    <linearGradient id="gora" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#05070c" stop-opacity="0.85"/>
      <stop offset="0.16" stop-color="#05070c" stop-opacity="0.35"/>
      <stop offset="0.3" stop-color="#05070c" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="dol" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0.55" stop-color="#05070c" stop-opacity="0"/>
      <stop offset="0.72" stop-color="#05070c" stop-opacity="0.78"/>
      <stop offset="1" stop-color="#05070c" stop-opacity="0.96"/>
    </linearGradient>
    <linearGradient id="zloto" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#fff6e0"/>
      <stop offset="0.55" stop-color="#f0c46f"/>
      <stop offset="1" stop-color="#b47a22"/>
    </linearGradient>
    <linearGradient id="linia" x1="0" x2="1">
      <stop offset="0" stop-color="#e2a93f" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#e2a93f" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#e2a93f" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="${B}" height="${B}" fill="url(#gora)"/>
  <rect width="${B}" height="${B}" fill="url(#dol)"/>
  <text x="${B / 2}" y="250" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="88" font-weight="600" letter-spacing="26" fill="#e8b04b">PODCAST · ULESZKA.NET</text>
  <text x="${B / 2}" y="2290" text-anchor="middle" font-family="Georgia, serif" font-size="300" font-weight="700" fill="url(#zloto)">Uwierz we</text>
  <text x="${B / 2}" y="2600" text-anchor="middle" font-family="Georgia, serif" font-size="300" font-weight="700" fill="url(#zloto)">własny rozum</text>
  <rect x="900" y="2700" width="1200" height="4" fill="url(#linia)"/>
  <text x="${B / 2}" y="2840" text-anchor="middle" font-family="Georgia, serif" font-size="110" fill="#ece6d8">teksty Leszka Klimka</text>
</svg>`;

const tlo = await sharp("podcast/scena-kwadrat.jpg")
  .resize(B, B, { fit: "cover", position: "centre", kernel: "lanczos3" })
  .sharpen({ sigma: 1.1 })
  .toBuffer();
const info = await sharp(tlo)
  .composite([{ input: Buffer.from(napisy) }])
  .jpeg({ quality: 88, mozjpeg: true })
  .toFile("podcast/okladka.jpg");
console.log(`Zapisano podcast/okladka.jpg (${info.width}×${info.height}, ${Math.round(info.size / 1024)} KB)`);
