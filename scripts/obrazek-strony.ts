/**
 * Tworzy docs/og.png – obrazek podglądu (1200×630), który pokazuje się przy udostępnianiu linku do strony
 * (Facebook, Messenger, WhatsApp, X…). Tłem jest kadr ze sceny 3D strony (docs/img/scena.jpg),
 * na który nakładany jest napis.
 * Uruchomienie: npx tsx scripts/obrazek-strony.ts
 */
import sharp from "sharp";

const napisy = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="lewo" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#05070c" stop-opacity="0.94"/>
      <stop offset="0.42" stop-color="#05070c" stop-opacity="0.7"/>
      <stop offset="0.62" stop-color="#05070c" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="dol" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0.7" stop-color="#05070c" stop-opacity="0"/>
      <stop offset="1" stop-color="#05070c" stop-opacity="0.75"/>
    </linearGradient>
    <linearGradient id="zloto" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#fff6e0"/>
      <stop offset="0.55" stop-color="#f0c46f"/>
      <stop offset="1" stop-color="#b47a22"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#lewo)"/>
  <rect width="1200" height="630" fill="url(#dol)"/>
  <text x="64" y="120" font-family="Segoe UI, Arial, sans-serif" font-size="21" font-weight="600" letter-spacing="4" fill="#e8b04b">„UWIERZ WE WŁASNY ROZUM” · 2004–2007</text>
  <text x="60" y="240" font-family="Georgia, serif" font-size="112" font-weight="700" fill="url(#zloto)">Nadchodzi</text>
  <text x="60" y="352" font-family="Georgia, serif" font-size="112" font-weight="700" fill="url(#zloto)">przeszłość</text>
  <text x="64" y="398" font-family="Segoe UI, Arial, sans-serif" font-size="22" fill="#9aa3b5">— Leszek Klimek, uleszka.net</text>
  <text x="64" y="480" font-family="Georgia, serif" font-size="38" fill="#ffffff">Porozmawiaj z archiwum strony</text>
  <text x="64" y="530" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#c9cfdb">przez Claude albo ChatGPT · 148 artykułów · dawne źródła</text>
</svg>`;

const tlo = await sharp("docs/img/scena.jpg")
  .resize(1200, 630, { fit: "cover", position: "centre" })
  .toBuffer();
await sharp(tlo).composite([{ input: Buffer.from(napisy) }]).png().toFile("docs/og.png");
console.log("Zapisano docs/og.png");

// ikona konektora / strony (512×512): złote „U” na granatowym tle
const ikona = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <radialGradient id="p" cx="0.85" cy="0.1" r="0.9">
      <stop offset="0" stop-color="#e8b04b" stop-opacity="0.38"/>
      <stop offset="1" stop-color="#e8b04b" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="512" height="512" rx="112" fill="#14213d"/>
  <rect width="512" height="512" rx="112" fill="url(#p)"/>
  <circle cx="256" cy="244" r="176" fill="none" stroke="#e8b04b" stroke-opacity="0.35" stroke-width="6"/>
  <text x="256" y="350" font-family="Georgia, serif" font-size="300" font-weight="700" text-anchor="middle" fill="#e8b04b">U</text>
</svg>`;
await sharp(Buffer.from(ikona)).png().toFile("docs/ikona.png");
await sharp(Buffer.from(ikona)).resize(64, 64).png().toFile("docs/favicon.png");
console.log("Zapisano docs/ikona.png i docs/favicon.png");
