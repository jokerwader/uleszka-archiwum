/**
 * Podcast „Uwierz we własny rozum” – teksty Leszka Klimka czytane przez lektora AI (ElevenLabs).
 *
 *   npx tsx scripts/podcast.ts teksty <nr> <tytul-odcinka> <id artykułu> [<id> …]
 *       przygotowuje podcast/<nr>-<slug>/: części tekstu do wklejenia w ElevenLabs (do 9 500 znaków każda,
 *       podział na granicach akapitów), zapowiedź i zakończenie odcinka oraz opis do Spotify.
 *       Tekst autora jest wierny – usuwane są tylko obrazy, tabele, podpisy zdjęć i resztki strony,
 *       a oczywiste literówki są poprawiane według erraty (dane/poprawki/errata.json).
 *
 *   npx tsx scripts/podcast.ts polacz <folder odcinka>
 *       łączy pliki MP3 z folderu (w kolejności nazw) w jeden odcinek: krótka cisza między częściami,
 *       głośność wyrównana do standardu podcastów (-16 LUFS), opis i okładka zapisane w pliku. Wymaga ffmpeg.
 */
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { Archiwum, type Dokument } from "../src/archiwum.js";
import { popraw, wczytajErrate } from "./lib/errata.js";
import { polaczInicjaly } from "./lib/inicjaly.js";

const NAZWA = "Uwierz we własny rozum – teksty Leszka Klimka";
/** Zdanie o tym, kto przygotował podcast (czytane na końcu odcinka); puste = bez podpisu. */
const PRZYGOTOWAL = "Podcast przygotował Mateusz Małek.";
const LIMIT = 9500; // ElevenLabs przyjmuje do 10 000 znaków naraz – zostawiamy zapas
const slug = (s: string) =>
  s.toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

/** Tekst artykułu do czytania na głos – słowa autora bez zmian, bez elementów, których nie da się przeczytać. */
export function tekstDoCzytania(a: Dokument): string {
  return (
    // inicjał w osobnym akapicie („**P**” + „ora …”) – jedno słowo, chyba że to osobne słowo („**W**” + „Polsce”)
    polaczInicjaly(a.tresc, /\*\*([A-ZĄĆĘŁŃÓŚŹŻ])\*\*[ \t]*\n[ \t]*\n(?=\S)/g, (l, osobne) => (osobne ? l + " " : l))
      .replace(/\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)/g, "") // zdjęcia z odnośnikiem
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "") // zdjęcia
      .replace(/^\|.*\|$/gm, "") // tabele (dane czyta się lepiej w artykule)
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1") // odnośniki: zostaje sam tekst
      .replace(/<br>/g, " ")
      .replace(/\\([\\`*_{}[\]()#+\-.!|])/g, "$1") // znaki ucieczki Markdownu
      .replace(/\*\*|__/g, "")
      .replace(/(^|\s)\*([^*\n]+)\*(?=\s|$|[.,;:!?])/g, "$1$2")
      .replace(/^-{3,}$/gm, "")
      .replace(/^[-•]\s+/gm, "") // znaczniki list – zostaje treść punktu
      .replace(/[ \t]+/g, " ")
      .split("\n")
      .map((l) => l.trim())
      // resztki strony: liczniki, plakietki, pojedyncze znaki
      .filter((l) => !/^(JS|\d{1,6}|[<>|]|NETYKIETA.*)$/i.test(l))
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
  );
}

/**
 * Znaczniki dla ElevenLabs v3/v4 (w nawiasach kwadratowych; lektor ich nie czyta, tylko zmienia sposób mówienia).
 * Dodawane oszczędnie, tylko tam, gdzie zmienia się charakter tekstu – słowa autora pozostają bez zmian.
 * Nawiasy kwadratowe autora („[Henoch]”) zamieniamy na okrągłe – inaczej ElevenLabs wziąłby je za polecenia i pominął.
 */
export function zTagami(tekst: string): string {
  const akapity = tekst
    .replace(/\[(?:\.\.\.|…)\]/g, "…")
    .replace(/\[([^\]\n]+)\]/g, "($1)")
    .split(/\n\n+/);
  let wCytacie = false;
  return akapity
    .map((ak, i) => {
      const linie = ak.split("\n");
      const naglowek = linie.length === 1 && ak.length <= 70 && !/[.!?…:"”»]$/.test(ak);
      const zrodlo = /^[^.!?\n]{2,45} - \S/.test(ak) && !naglowek; // „Stary Testament - A potop trwał…” – cytat ze źródła
      const wiersz = linie.length >= 3; // fragment wiersza / eposu
      const krzyk = ak.length > 15 && ak === ak.toUpperCase() && /\p{L}/u.test(ak);
      const pytania = (ak.match(/\?/g) ?? []).length >= 2;
      let tag = "";
      if (i === 0) tag = "[calm, storytelling]";
      else if (naglowek) tag = "[long pause] [serious]";
      else if (krzyk) tag = "[emphatic]";
      else if (zrodlo || wiersz) tag = "[short pause] [solemn, reading an ancient text]";
      else if (wCytacie) tag = "[short pause] [calm, storytelling]";
      else if (pytania) tag = "[thoughtful]";
      wCytacie = zrodlo || wiersz;
      return tag ? `${tag} ${ak}` : ak;
    })
    .join("\n\n");
}

/** Dzieli tekst na części do LIMIT znaków, na granicach akapitów (a gdy akapit jest za długi – zdań). */
function czesci(tekst: string): string[] {
  const akapity = tekst.split(/\n\n+/);
  const wynik: string[] = [];
  let biezaca = "";
  const dodaj = (k: string) => {
    if (biezaca && (biezaca + "\n\n" + k).length > LIMIT) {
      wynik.push(biezaca);
      biezaca = "";
    }
    biezaca = biezaca ? `${biezaca}\n\n${k}` : k;
  };
  for (const ak of akapity) {
    if (ak.length <= LIMIT) dodaj(ak);
    else for (const z of ak.match(/[^.!?…]+[.!?…]+["”»)]*\s*|[^.!?…]+$/g) ?? [ak]) dodaj(z.trim());
  }
  if (biezaca) wynik.push(biezaca);
  return wynik;
}

const [, , polecenie, ...arg] = process.argv;

if (polecenie === "teksty") {
  const tagi = arg.includes("--tagi");
  const [nr, tytul, ...idy] = arg.filter((x) => x !== "--tagi");
  if (!nr || !tytul || !idy.length) throw new Error("Użycie: teksty <nr> <tytuł odcinka> <id artykułu> [<id> …]");
  const archiwum = new Archiwum(".");
  const artykuly = idy.map((id) => archiwum.znajdz(id, "artykul") ?? (() => { throw new Error(`Brak artykułu ${id}`); })());
  const folder = join("podcast", `${nr.padStart(2, "0")}-${slug(tytul)}`);
  mkdirSync(folder, { recursive: true });

  let n = 0;
  const spis: string[] = [];
  let razem = 0;
  const errata = wczytajErrate(".");
  const poprawki: string[] = [];
  const calosc: string[] = [];
  const rozdzialy: { artykul: string; tytul: string; srodtytul: boolean; akapity: string[] }[] = [];
  // zapowiedź i zakończenie nie są tekstem autora; adres strony zapisany tak, jak ma go wymówić lektor
  const zapowiedz = `Uwierz we własny rozum. Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi. Jego teksty ze strony uleszka kropka net, z lat dwa tysiące cztery – dwa tysiące siedem, czytane bez zmian. Odcinek ${Number(nr)}: ${tytul}${/[.?!…]$/.test(tytul) ? "" : "."} Czyta lektor wygenerowany przez sztuczną inteligencję.`;
  const zakonczenie = `To był tekst Leszka Klimka ze strony uleszka kropka net. Pełny tekst, ze zdjęciami i źródłami, znajdziesz w czytelni na stronie uleszka kropka net. Tam możesz też porozmawiać z archiwum strony przez sztuczną inteligencję.${PRZYGOTOWAL ? ` ${PRZYGOTOWAL}` : ""} Dziękuję za wysłuchanie.`;
  writeFileSync(join(folder, "00-zapowiedz.txt"), zapowiedz + "\n", "utf8");
  spis.push(`| 00-zapowiedz.txt | zapowiedź (nie jest tekstem autora) | ${zapowiedz.length} |`);
  razem += zapowiedz.length;
  for (const a of artykuly) {
    // oczywiste literówki poprawione według erraty (dane/poprawki/errata.json) – lektor czyta poprawną formę
    const { tekst: poprawiony, uzyte } = popraw(tekstDoCzytania(a), a.id, errata);
    for (const [k, ile] of uzyte) poprawki.push(`| ${a.tytul} | ${errata[k].zle} | ${errata[k].dobrze} | ${ile} |`);
    const tekstArt = tagi ? zTagami(poprawiony) : poprawiony;
    calosc.push(tagi && !tekstArt.startsWith("[") ? `[calm, storytelling] ${tekstArt}` : tekstArt);
    // rozdziały do Studio: podział na śródtytułach autora (te same, co w spisie treści czytelni)
    const srodtytuly = new Set(
      [...a.tresc.matchAll(/^(?:#{1,4}[ \t]+(.+)|\*\*([^*\n]{3,140})\*\*)[ \t]*$/gm)]
        .map((m) => (m[1] ?? m[2]).replace(/\*\*|__|\\/g, "").trim())
        .filter((t) => /\p{L}/u.test(t)),
    );
    const bezTagow = (ak: string) => ak.replace(/^(?:\[[^\]\n]*\]\s*)+/, "").trim();
    for (const ak of tekstArt.split(/\n\n+/)) {
      const t = bezTagow(ak);
      if (srodtytuly.has(t) || !rozdzialy.length || rozdzialy[rozdzialy.length - 1].artykul !== a.tytul)
        rozdzialy.push({ artykul: a.tytul, tytul: srodtytuly.has(t) ? t : a.tytul, srodtytul: srodtytuly.has(t), akapity: [] });
      rozdzialy[rozdzialy.length - 1].akapity.push(ak);
    }
    const czesciArt = czesci(tekstArt);
    czesciArt.forEach((c0, i) => {
      // każda część nagrywana jest osobno – zaczyna się od wskazówki tonu, jeśli nie ma własnej
      const c = tagi && !c0.startsWith("[") ? `[calm, storytelling] ${c0}` : c0;
      const plik = `${String(++n).padStart(2, "0")}-${slug(a.tytul)}${czesciArt.length > 1 ? `-cz${i + 1}` : ""}.txt`;
      writeFileSync(join(folder, plik), c + "\n", "utf8");
      spis.push(`| ${plik} | ${a.tytul}${czesciArt.length > 1 ? `, część ${i + 1} z ${czesciArt.length}` : ""} | ${c.length} |`);
      razem += c.length;
    });
  }
  writeFileSync(join(folder, "99-zakonczenie.txt"), zakonczenie + "\n", "utf8");
  spis.push(`| 99-zakonczenie.txt | zakończenie (nie jest tekstem autora) | ${zakonczenie.length} |`);
  razem += zakonczenie.length;
  // cały odcinek w jednym pliku – do ElevenLabs Studio, które samo dzieli długie teksty
  const pauza = tagi ? "[long pause]\n\n" : "";
  writeFileSync(join(folder, "calosc-do-studio.txt"), [zapowiedz, ...calosc, zakonczenie].join(`\n\n${pauza}`) + "\n", "utf8");
  // ten sam tekst podzielony na rozdziały Studio (jeden plik = jeden rozdział; nagrywany i poprawiany osobno)
  const folderRozdzialow = join(folder, "rozdzialy-studio");
  rmSync(folderRozdzialow, { recursive: true, force: true });
  mkdirSync(folderRozdzialow, { recursive: true });
  // bardzo krótki rozdział (sam tytuł z mottem, jedno zdanie) łączymy z następnym z tego samego artykułu
  for (let i = rozdzialy.length - 2; i >= 0; i--) {
    const r = rozdzialy[i], nast = rozdzialy[i + 1];
    if (r.akapity.join("\n\n").length >= 800 || r.artykul !== nast.artykul) continue;
    rozdzialy.splice(i, 2, { ...nast, tytul: r.srodtytul ? r.tytul : nast.tytul, srodtytul: r.srodtytul || nast.srodtytul, akapity: [...r.akapity, ...nast.akapity] });
  }
  // … a krótki ostatni rozdział artykułu – z poprzednim
  for (let i = rozdzialy.length - 1; i >= 1; i--) {
    const r = rozdzialy[i], poprz = rozdzialy[i - 1];
    if (r.akapity.join("\n\n").length >= 800 || r.artykul !== poprz.artykul) continue;
    rozdzialy.splice(i - 1, 2, { ...poprz, akapity: [...poprz.akapity, ...r.akapity] });
  }
  const plikiRozdzialow = [
    { tytul: "Zapowiedź", tekst: zapowiedz },
    ...rozdzialy.map((r) => {
      let t = r.akapity.join("\n\n").replace(/^\[long pause\]\s*/, ""); // pauza na początku rozdziału jest zbędna
      if (tagi && !t.startsWith("[")) t = `[calm, storytelling] ${t}`;
      return { tytul: r.tytul, tekst: t };
    }),
    { tytul: "Zakończenie", tekst: zakonczenie },
  ];
  const spisRozdzialow = plikiRozdzialow.map((r, i) => {
    const plik = `${String(i).padStart(2, "0")}-${slug(r.tytul).slice(0, 50)}.txt`;
    writeFileSync(join(folderRozdzialow, plik), r.tekst + "\n", "utf8");
    return `| ${plik} | ${r.tytul} | ${r.tekst.length} |`;
  });

  const linki = artykuly.map((a) => `https://uleszka.net/czytelnia/${slug(a.id)}.html`);
  const streszczenia = artykuly.map((a) => archiwum.opracowania.get(a.id)?.streszczenie ?? "").filter(Boolean);
  const opis = `# Odcinek ${Number(nr)}: ${tytul}

## Do wklejenia w ElevenLabs

Wklejaj pliki po kolei; każdy mieści się w limicie 10 000 znaków.${tagi ? " Teksty mają znaczniki dla modeli v3/v4 w nawiasach kwadratowych (np. [calm, storytelling], [long pause]) – lektor ich nie czyta, tylko zmienia sposób mówienia; liczą się jednak do znaków. Nawiasy kwadratowe autora zamieniono na okrągłe, żeby lektor je przeczytał." : ""} Nagrania zapisz jako MP3 z tymi samymi numerami
(np. \`00-zapowiedz.mp3\`, \`01-…mp3\`) w tym folderze – potem: \`npx tsx scripts/podcast.ts polacz ${folder.replace(/\\/g, "/")}\`.

| Plik | Co zawiera | Znaki (≈ kredyty) |
|---|---|---|
${spis.join("\n")}

**Razem: ${razem} znaków** (≈ ${Math.round(razem / 950)} min nagrania).

## ElevenLabs Studio (rozdziały)

W folderze \`rozdzialy-studio/\` ten sam tekst jest podzielony według śródtytułów autora: jeden plik = jeden rozdział.
W Studio: nowy projekt → dla każdego pliku „Add chapter”, wklej tekst, nadaj tytuł z tabeli. Rozdział, który wyjdzie źle,
generujesz od nowa osobno; na końcu „Export” całego projektu do jednego MP3. Cały odcinek w jednym pliku: \`calosc-do-studio.txt\`.

| Plik | Rozdział | Znaki |
|---|---|---|
${spisRozdzialow.join("\n")}
${poprawki.length ? `
### Poprawione literówki (errata)

W tekście dla lektora poprawiono oczywiste literówki z oryginału (lista: \`dane/poprawki/errata.json\`):

| Artykuł | Było | Jest | Razy |
|---|---|---|---|
${poprawki.join("\n")}
` : ""}
## Opis odcinka (Spotify)

**Tytuł:** ${tytul} – Leszek Klimek

${streszczenia.join("\n\n")}

Tekst Leszka Klimka ze strony uleszka.net („Uwierz we własny rozum”, 2004–2007), przeczytany bez zmian (poprawiono tylko oczywiste literówki). Czyta lektor AI (ElevenLabs). Archiwum i podcast powstały w hołdzie śp. Leszkowi Wiktorowi Klimkowi. Podcast przygotował Mateusz Małek (jokerwader).

Teksty wyrażają poglądy autora sprzed ok. 20 lat. W sprawach zdrowia nie zastępują porady lekarza.

Pełny tekst ze zdjęciami: ${linki.join(" · ")}
Rozmowa z archiwum przez AI: https://uleszka.net
`;
  writeFileSync(join(folder, "ODCINEK.md"), opis, "utf8");
  console.log(`${folder}: ${spis.length} plików, razem ${razem} znaków`);
  for (const s of spis) console.log("  " + s);
} else if (polecenie === "polacz") {
  const [folder] = arg;
  if (!folder || !existsSync(folder)) throw new Error("Użycie: polacz <folder odcinka>");
  const mp3 = readdirSync(folder).filter((f) => /\.mp3$/i.test(f) && f !== "odcinek.mp3").sort();
  if (!mp3.length) throw new Error(`Brak plików MP3 w ${folder}`);
  const opis = existsSync(join(folder, "ODCINEK.md")) ? readFileSync(join(folder, "ODCINEK.md"), "utf8") : "";
  const tytul = opis.match(/^\*\*Tytuł:\*\* (.+)$/m)?.[1] ?? folder;
  const okladka = "podcast/okladka.jpg";
  // lista wejść: każda część + 0,8 s ciszy między częściami
  const wejscia: string[] = [];
  const filtr: string[] = [];
  mp3.forEach((f, i) => {
    wejscia.push("-i", join(folder, f));
    filtr.push(`[${i}:a]aresample=44100,aformat=channel_layouts=mono[a${i}]`);
  });
  const cisza = mp3.length;
  wejscia.push("-f", "lavfi", "-t", "0.8", "-i", "anullsrc=r=44100:cl=mono");
  const kolejnosc = mp3.flatMap((_, i) => (i < mp3.length - 1 ? [`[a${i}]`, `[${cisza}:a]`] : [`[a${i}]`]));
  // ciszy używamy wiele razy – rozdzielamy ją
  const ileCiszy = Math.max(0, mp3.length - 1);
  if (ileCiszy > 1) {
    filtr.push(`[${cisza}:a]asplit=${ileCiszy}${[...Array(ileCiszy).keys()].map((k) => `[c${k}]`).join("")}`);
    let k = 0;
    for (let j = 0; j < kolejnosc.length; j++) if (kolejnosc[j] === `[${cisza}:a]`) kolejnosc[j] = `[c${k++}]`;
  }
  filtr.push(`${kolejnosc.join("")}concat=n=${kolejnosc.length}:v=0:a=1[razem]`);
  filtr.push(`[razem]loudnorm=I=-16:TP=-1.5:LRA=11[wyj]`);
  const okl = existsSync(okladka) ? ["-i", okladka] : [];
  const nrOkl = mp3.length + 1;
  const wyjscie = join(folder, "odcinek.mp3");
  execFileSync(
    "ffmpeg",
    [
      "-y", ...wejscia, ...okl,
      "-filter_complex", filtr.join(";"),
      "-map", "[wyj]",
      ...(okl.length ? ["-map", `${nrOkl}:v`, "-c:v", "mjpeg", "-disposition:v", "attached_pic"] : []),
      "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "1",
      "-id3v2_version", "3",
      "-metadata", `title=${tytul}`,
      "-metadata", "artist=Leszek Klimek (czyta lektor AI)",
      "-metadata", `album=${NAZWA}`,
      "-metadata", "comment=https://uleszka.net",
      wyjscie,
    ],
    { stdio: "inherit" },
  );
  const czas = Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wyjscie]).toString().trim());
  console.log(`Gotowe: ${wyjscie} (${Math.floor(czas / 60)} min ${Math.round(czas % 60)} s, ${mp3.length} części)`);
} else {
  console.log("Użycie: npx tsx scripts/podcast.ts teksty <nr> <tytuł> <id…>  |  polacz <folder>");
}
