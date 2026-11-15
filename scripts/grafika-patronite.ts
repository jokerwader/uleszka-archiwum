/**
 * Grafiki progów wsparcia na Patronite: patronite-*-532x240.jpg (wymiar zalecany przez Patronite) i -1064x480.jpg (ostrzejsza),
 * oraz kwadratowe prog-*.jpg 1080×1080 z listą nagród (na Facebooka i do wpisów), w stylu okładki podcastu i kanału YouTube:
 * nocne tło, złote litery, własny znak każdego progu; im wyższy próg, tym jaśniejsza scena z piramidą w tle.
 * Zdjęcie sceny jest nasze (podcast/scena-kwadrat.jpg), więc grafiki nie wymagają podpisów autorów.
 * Wynik: podcast/patronite/. Uruchomienie: npx tsx scripts/grafika-patronite.ts
 */
import { mkdirSync } from "node:fs";
import sharp from "sharp";

const WYJ = "podcast/patronite";
mkdirSync(WYJ, { recursive: true });
const S = 1080;
const xml = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// znaki progów (viewBox 0 0 100 100, złota linia)
const ZNAKI: Record<string, string> = {
  ksiazka: `<path d="M50 30 C40 22 22 22 12 26 V76 C22 72 40 72 50 80 C60 72 78 72 88 76 V26 C78 22 60 22 50 30 Z M50 30 V80"/>
    <path d="M20 38 C28 36 36 36 43 39 M20 48 C28 46 36 46 43 49 M20 58 C28 56 36 56 43 59 M57 39 C64 36 72 36 80 38 M57 49 C64 46 72 46 80 48 M57 59 C64 56 72 56 80 58" stroke-width="2.5" opacity=".7"/>`,
  kompas: `<circle cx="50" cy="50" r="36"/><circle cx="50" cy="50" r="29" stroke-width="2" opacity=".5"/>
    <path d="M50 16 V22 M50 78 V84 M16 50 H22 M78 50 H84" stroke-width="3"/>
    <path d="M50 24 L58 50 L50 76 L42 50 Z" fill="url(#z)" fill-opacity=".35"/><path d="M50 24 L58 50 H42 Z" fill="url(#z)" stroke="none"/><circle cx="50" cy="50" r="3.5" fill="#fff6e0" stroke="none"/>`,
  mapa: `<path d="M12 28 L36 20 L62 28 L88 20 V74 L62 82 L36 74 L12 82 Z M36 20 V74 M62 28 V82"/>
    <path d="M20 40 C30 36 34 50 44 46" stroke-width="2.5" stroke-dasharray="4 4" opacity=".7"/>
    <circle cx="60" cy="54" r="15" fill="#05070c" fill-opacity=".7"/><path d="M71 65 L84 78" stroke-width="8" stroke-linecap="round"/>`,
  piramida: `<path d="M50 20 L88 82 H12 Z"/><path d="M31 51 H69 M22 66 H78" stroke-width="2" opacity=".5"/>
    <path d="M37 57 C44 49 56 49 63 57 C56 65 44 65 37 57 Z" fill="#05070c" fill-opacity=".6"/><circle cx="50" cy="57" r="4.5" fill="url(#z)" stroke="none"/>
    <path d="M50 4 V12 M36 8 L41 15 M64 8 L59 15 M26 16 L33 20 M74 16 L67 20" stroke-width="3" opacity=".9"/>`,
  klucz: `<circle cx="32" cy="38" r="17"/><circle cx="32" cy="38" r="7" stroke-width="3"/>
    <path d="M44 50 L84 90 M64 70 L72 62 M72 78 L80 70 M76 82 L84 74"/>
    <path d="M14 12 L18 20 M50 12 L46 20 M10 38 H4" stroke-width="2.5" opacity=".7"/>`,
};

// kwoty jak zaleca Patronite (10, 20, 30, 50, 100 zł; kwoty progu nie da się później zmienić);
// próg 10 zł wybiera najwięcej osób, więc ma najatrakcyjniejszą nagrodę: odcinek dzień przed premierą
const PROGI = [
  { nr: 1, nazwa: "Czytelnik", kwota: "10 zł", znak: "ksiazka", jasnosc: 0.15, zalety: ["Odcinek dzień przed premierą", "Twoje imię na stronie Patronów", "Wpisy zza kulis podcastu i atlasu"] },
  { nr: 2, nazwa: "Odkrywca", kwota: "20 zł", znak: "kompas", jasnosc: 0.25, zalety: ["Imię w napisach końcowych filmów", "Głos w wyborze odcinków specjalnych", "Wszystko z progu Czytelnik"] },
  { nr: 3, nazwa: "Badacz", kwota: "30 zł", znak: "mapa", jasnosc: 0.35, zalety: ["Co miesiąc mapa z atlasu do druku", "Nowe części atlasu przed publikacją", "Wszystko z niższych progów"] },
  { nr: 4, nazwa: "Mecenas", kwota: "50 zł", znak: "piramida", jasnosc: 0.48, zalety: ["Pierwszeństwo Twoich miejsc i tematów", "Spotkanie online raz na kwartał", "Wszystko z niższych progów"] },
  { nr: 5, nazwa: "Opiekun archiwum", kwota: "100 zł", znak: "klucz", jasnosc: 0.62, zalety: ["Twoje imię jako opiekuna miejsca w atlasie", "Podziękowanie w odcinku specjalnym", "Wszystko z niższych progów"] },
];

const ZLOTO = `<linearGradient id="z" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6e0"/><stop offset=".55" stop-color="#f0c46f"/><stop offset="1" stop-color="#b47a22"/></linearGradient>`;

for (const p of PROGI) {
  // scena z piramidą, przyciemniona tym mocniej, im niższy próg
  const scena = await sharp("podcast/scena-kwadrat.jpg").resize(S, S, { fit: "cover" }).modulate({ brightness: p.jasnosc }).blur(p.nr === 4 ? 0.3 : 6).toBuffer();
  const gwiazdy = Array.from({ length: 30 + p.nr * 25 }, (_, i) => {
    const x = (i * 397 + p.nr * 131) % S, y = (i * 211 + p.nr * 59) % 560, r = ((i * 7) % 3) * 0.6 + 0.6;
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff6e0" opacity="${0.15 + ((i * 13) % 10) / 25}"/>`;
  }).join("");
  const zalety = p.zalety.map((z, i) => {
    const y = 780 + i * 62;
    const ostatnia = z.startsWith("Wszystko z");
    return `<text x="${S / 2}" y="${y}" text-anchor="middle" font-family="Georgia, serif" font-size="${ostatnia ? 30 : 36}" fill="${ostatnia ? "#9aa3b5" : "#e4e8f0"}" ${ostatnia ? 'font-style="italic"' : ""}>${ostatnia ? "+ " : "✦ "}${xml(z)}</text>`;
  }).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}"><defs>${ZLOTO}
    <radialGradient id="tlo" cx="50%" cy="28%" r="75%"><stop offset="0" stop-color="#16244a" stop-opacity=".55"/><stop offset=".6" stop-color="#05070c" stop-opacity=".75"/><stop offset="1" stop-color="#05070c" stop-opacity=".95"/></radialGradient>
    <radialGradient id="blask" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f0c46f" stop-opacity="${0.12 + p.nr * 0.06}"/><stop offset="1" stop-color="#f0c46f" stop-opacity="0"/></radialGradient>
    <linearGradient id="kreska" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e2a93f" stop-opacity="0"/><stop offset=".5" stop-color="#e2a93f"/><stop offset="1" stop-color="#e2a93f" stop-opacity="0"/></linearGradient></defs>
    <rect width="${S}" height="${S}" fill="url(#tlo)"/>${gwiazdy}
    <rect x="18" y="18" width="${S - 36}" height="${S - 36}" rx="34" fill="none" stroke="#e2a93f" stroke-opacity="${0.25 + p.nr * 0.1}" stroke-width="2"/>
    <circle cx="${S / 2}" cy="270" r="190" fill="url(#blask)"/>
    <circle cx="${S / 2}" cy="270" r="128" fill="#05070c" fill-opacity=".72" stroke="url(#z)" stroke-width="4"/>
    <circle cx="${S / 2}" cy="270" r="112" fill="none" stroke="#e2a93f" stroke-opacity=".35" stroke-width="1.5"/>
    <g transform="translate(${S / 2 - 80} 190) scale(1.6)" fill="none" stroke="url(#z)" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round">${ZNAKI[p.znak]}</g>
    <text x="${S / 2}" y="482" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="26" letter-spacing="9" fill="#e2a93f">PRÓG ${p.nr} · PATRONITE</text>
    <text x="${S / 2}" y="590" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="${p.nazwa.length > 12 ? 84 : 112}" fill="url(#z)">${xml(p.nazwa)}</text>
    <text x="${S / 2}" y="660" text-anchor="middle" font-family="Georgia, serif" font-size="46" fill="#f4efe4">${xml(p.kwota)} <tspan font-size="30" fill="#9aa3b5">miesięcznie</tspan></text>
    <rect x="${S / 2 - 220}" y="700" width="440" height="2" fill="url(#kreska)"/>
    ${zalety}
    <text x="${S / 2}" y="${S - 56}" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="#9aa3b5">Uwierz we własny rozum · uleszka.net</text></svg>`;
  const plik = `${WYJ}/prog-${p.nr}-${p.nazwa.toLowerCase().replace(/ /g, "-")}.jpg`;
  await sharp(scena).composite([{ input: Buffer.from(svg), left: 0, top: 0 }]).jpeg({ quality: 92 }).toFile(plik);
  console.log(plik);

  // ---------- grafika progu na Patronite: 532×240 (zalecany wymiar) i 1064×480 (podwójna rozdzielczość) ----------
  // tylko znak, nazwa i kwota – nagrody wpisuje się w opisie progu
  const BW = 1064, BH = 480;
  const tloB = await sharp("podcast/scena-kwadrat.jpg").resize(BW, BH, { fit: "cover", position: "top" }).modulate({ brightness: p.jasnosc * 0.9 }).blur(4).toBuffer();
  const gwiazdyB = Array.from({ length: 25 + p.nr * 15 }, (_, i) => {
    const x = (i * 389 + p.nr * 97) % BW, y = (i * 173 + p.nr * 41) % BH, r = ((i * 7) % 3) * 0.6 + 0.6;
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff6e0" opacity="${0.12 + ((i * 13) % 10) / 28}"/>`;
  }).join("");
  const dluga = p.nazwa.length > 12;
  const baner = `<svg xmlns="http://www.w3.org/2000/svg" width="${BW}" height="${BH}"><defs>${ZLOTO}
    <linearGradient id="ciemno" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#05070c" stop-opacity=".55"/><stop offset=".45" stop-color="#05070c" stop-opacity=".8"/><stop offset="1" stop-color="#05070c" stop-opacity=".55"/></linearGradient>
    <radialGradient id="blask" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f0c46f" stop-opacity="${0.12 + p.nr * 0.06}"/><stop offset="1" stop-color="#f0c46f" stop-opacity="0"/></radialGradient>
    <linearGradient id="kreska" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e2a93f"/><stop offset="1" stop-color="#e2a93f" stop-opacity="0"/></linearGradient></defs>
    <rect width="${BW}" height="${BH}" fill="url(#ciemno)"/>${gwiazdyB}
    <rect x="10" y="10" width="${BW - 20}" height="${BH - 20}" rx="28" fill="none" stroke="#e2a93f" stroke-opacity="${0.3 + p.nr * 0.1}" stroke-width="3"/>
    <circle cx="215" cy="240" r="175" fill="url(#blask)"/>
    <circle cx="215" cy="240" r="140" fill="#05070c" fill-opacity=".75" stroke="url(#z)" stroke-width="5"/>
    <circle cx="215" cy="240" r="122" fill="none" stroke="#e2a93f" stroke-opacity=".35" stroke-width="2"/>
    <g transform="translate(125 150) scale(1.8)" fill="none" stroke="url(#z)" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round">${ZNAKI[p.znak]}</g>
    <text x="410" y="${dluga ? 150 : 145}" font-family="Arial, sans-serif" font-weight="700" font-size="28" letter-spacing="8" fill="#e2a93f">PRÓG ${p.nr}</text>
    <text x="404" y="${dluga ? 245 : 262}" font-family="Georgia, serif" font-weight="700" font-size="${dluga ? 60 : 112}" fill="url(#z)">${xml(p.nazwa)}</text>
    <rect x="410" y="${dluga ? 278 : 296}" width="300" height="3" fill="url(#kreska)"/>
    <text x="410" y="${dluga ? 352 : 366}" font-family="Georgia, serif" font-size="58" fill="#f4efe4">${xml(p.kwota)} <tspan font-size="34" fill="#c9cfdb">miesięcznie</tspan></text>
    <text x="410" y="${BH - 48}" font-family="Georgia, serif" font-size="26" fill="#9aa3b5">Uwierz we własny rozum · uleszka.net</text></svg>`;
  const nazwaB = `${WYJ}/patronite-${p.nr}-${p.nazwa.toLowerCase().replace(/ /g, "-")}`;
  const duzy = await sharp(tloB).composite([{ input: Buffer.from(baner), left: 0, top: 0 }]).png().toBuffer();
  await sharp(duzy).jpeg({ quality: 92 }).toFile(`${nazwaB}-1064x480.jpg`);
  await sharp(duzy).resize(532, 240, { kernel: "lanczos3" }).jpeg({ quality: 94 }).toFile(`${nazwaB}-532x240.jpg`);
  console.log(`${nazwaB}-532x240.jpg i -1064x480.jpg`);
}
