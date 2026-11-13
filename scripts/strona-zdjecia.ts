/**
 * Kopiuje wybrane zdjęcia ze strony uleszka.net (folder zrodlo/) do docs/img/ – do sceny 3D i galerii na stronie
 * GitHub Pages. Oryginały w zrodlo/ zostają nietknięte; tu powstają tylko kopie w formacie JPG.
 * Uruchomienie: npx tsx scripts/strona-zdjecia.ts
 */
import { mkdirSync } from "node:fs";
import sharp from "sharp";

export const ZDJECIA = [
  "brama.jpg",
  "tsunami.jpg",
  "09tiahu/wejscie.jpg",
  "09tiahu/tiahuair.jpg",
  "07piramidy/satpir.jpg",
  "07piramidy/orion3.jpg",
  "07piramidy/renowacja.jpg",
  "zagadki/stopione.jpg",
  "blazenada/pacal.gif",
  "blazenada/nazca.jpg",
  "02uskok/moai1.jpg",
  "02uskok/ollinstone.jpg",
  "06budowle/tort5b.jpg",
  "25maja2006/meteo.jpg",
  "ameryka/1p_teoti.jpg",
  "05bogowie/cywilizacje.jpg",
];

mkdirSync("docs/img", { recursive: true });
for (const z of ZDJECIA) {
  const cel = `docs/img/${z.replace(/\//g, "-").replace(/\.(gif|png)$/, ".jpg")}`;
  await sharp(`zrodlo/webacja/${z}`).flatten({ background: "#0b0f19" }).jpeg({ quality: 85, mozjpeg: true }).toFile(cel);
  console.log(cel);
}
