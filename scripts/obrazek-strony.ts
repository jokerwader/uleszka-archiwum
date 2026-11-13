/**
 * Tworzy docs/og.png – obrazek podglądu (1200×630), który pokazuje się przy udostępnianiu linku do strony
 * (Facebook, Messenger, WhatsApp, X…).
 * Uruchomienie: npx tsx scripts/obrazek-strony.ts
 */
import sharp from "sharp";

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <radialGradient id="poswiata" cx="1" cy="0" r="0.8">
      <stop offset="0" stop-color="#e8b04b" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#e8b04b" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="#14213d"/>
  <rect width="1200" height="630" fill="url(#poswiata)"/>
  <rect x="70" y="70" width="6" height="150" fill="#e8b04b"/>
  <text x="100" y="105" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="600" letter-spacing="3" fill="#e8b04b">ARCHIWUM STRONY Z LAT 2004–2007</text>
  <text x="100" y="170" font-family="Georgia, serif" font-size="44" fill="#d7dbe4">„Uwierz we własny rozum”</text>
  <text x="100" y="215" font-family="Segoe UI, Arial, sans-serif" font-size="26" fill="#9aa3b5">Leszek Klimek · uleszka.net</text>
  <text x="70" y="345" font-family="Georgia, serif" font-size="78" font-weight="700" fill="#ffffff">Porozmawiaj z archiwum</text>
  <text x="70" y="435" font-family="Georgia, serif" font-size="78" font-weight="700" fill="#ffffff">uleszka.net</text>
  <text x="70" y="520" font-family="Segoe UI, Arial, sans-serif" font-size="30" fill="#d7dbe4">148 artykułów · 1714 zdjęć · biblioteka dawnych źródeł</text>
  <text x="70" y="568" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="600" fill="#e8b04b">Przez Claude albo ChatGPT – bez instalowania</text>
</svg>`;

await sharp(Buffer.from(svg)).png().toFile("docs/og.png");
console.log("Zapisano docs/og.png");
