# Podcast „Uwierz we własny rozum – teksty Leszka Klimka”

Teksty ze strony uleszka.net (2004–2007) czytane bez zmian przez lektora AI (ElevenLabs). Każdy odcinek to jeden artykuł albo kilka krótszych.

## Opis podcastu (do Spotify for Creators)

**Nazwa:** Uwierz we własny rozum – teksty Leszka Klimka

**Opis:**
Strona uleszka.net Leszka Klimka otworzyła oczy wielu ludziom. Pytała, kto naprawdę zbudował piramidy, czy potop był tylko jeden, gdzie leżała Atlantyda i dlaczego historia ma tyle luk. Pytała o rzeczy, o które wcześniej mało kto pytał, i stała się prekursorem wielu blogów.

W tym podcaście jej teksty wracają w niezmienionej formie. Czyta je lektor wygenerowany przez sztuczną inteligencję. Podcast powstał w hołdzie śp. Leszkowi Wiktorowi Klimkowi. Przygotował go jokerwader.

Pełne teksty ze zdjęciami, źródłami i możliwością rozmowy z archiwum przez AI: https://uleszka.net

Teksty wyrażają poglądy autora sprzed ok. 20 lat. W sprawach zdrowia nie zastępują porady lekarza.

**Kategoria:** Historia (albo: Społeczeństwo i kultura)
**Język:** polski
**Okładka:** [okladka.jpg](okladka.jpg) (3000 × 3000 px)
**Treści dla dorosłych:** nie
**Monetyzacja:** wyłączona (archiwum ma charakter niekomercyjny). Dobrowolne wsparcie (Patronite) pomaga w utrzymaniu serwerów, opłaceniu lektora AI i pracy nad archiwami; odcinki są bezpłatne dla wszystkich.

## Jak przygotować odcinek

1. Teksty do wklejenia w ElevenLabs:
   ```
   npx tsx scripts/podcast.ts teksty <nr> "<tytuł odcinka>" <id artykułu> [<id> …] --tagi
   ```
   Powstaje folder `podcast/<nr>-<tytuł>/` z plikami po maks. 9 500 znaków i opisem `ODCINEK.md`.
   Opcja `--tagi` dodaje znaczniki dla ElevenLabs v3/v4 (`[calm, storytelling]`, `[long pause] [serious]` przed śródtytułami,
   `[solemn, reading an ancient text]` przy cytatach z dawnych źródeł, `[thoughtful]` przy pytaniach). Lektor ich nie czyta;
   słowa autora zostają bez zmian. Nawiasy kwadratowe autora (np. „[Henoch]”) są zamieniane na okrągłe, żeby lektor je przeczytał.
   Oczywiste literówki z oryginału (np. „moga” → „mogą”) są poprawiane według erraty `dane/poprawki/errata.json`.
   Ich lista trafia do `ODCINEK.md`. Interpunkcja zostaje bez zmian.
   Powstaje też `calosc-do-studio.txt` (cały odcinek w jednym pliku) i folder `rozdzialy-studio/` – ten sam tekst
   podzielony według śródtytułów autora, po jednym pliku na rozdział ElevenLabs Studio (bardzo krótkie fragmenty są
   dołączane do sąsiednich). W Studio rozdział, który wyjdzie źle, generuje się od nowa osobno.
2. W ElevenLabs nagraj każdy plik osobno i zapisz MP3 z tym samym numerem na początku nazwy (np. `00-zapowiedz.mp3`, `01-wstep.mp3`).
3. Połącz części w jeden odcinek (krótka cisza między częściami, głośność −16 LUFS, okładka i opis w pliku):
   ```
   npx tsx scripts/podcast.ts polacz podcast/<folder odcinka>
   ```
4. Wgraj `odcinek.mp3` do Spotify for Creators, z tytułem i opisem z `ODCINEK.md`.
5. Dopisz odcinek do `podcast/odcinki.json` (numer, tytuł, identyfikator z linku `open.spotify.com/episode/<id>`, id artykułów;
   gdy film jest na YouTube – także `"youtube": "<id>"` z linku `youtu.be/<id>`)
   i uruchom `npx tsx scripts/czytelnia.ts`. Przy tych artykułach w czytelni pojawi się odtwarzacz Spotify
   (zamiast czytania głosem przeglądarki). Na stronie głównej sekcję „Posłuchaj” (`docs/index.html`, `#podcast`) zmień ręcznie.
   Odtwarzacz Spotify wczytuje się dopiero po kliknięciu, więc bez kliknięcia strona nie łączy się ze Spotify.
   Film zaplanowany na YouTube przed linkiem ze Spotify: dopisz odcinek bez pola `spotify`, tylko z `youtube`.
   Licznik premiery zostaje, a obok pojawia się przycisk „Premiera na YouTube” (w czytelni i na stronie głównej).
   Gdy dojdzie link Spotify, dopisz `spotify` – licznik zamieni się w odtwarzacz.

## Wideo na YouTube

```
npx tsx scripts/wideo.ts podcast/<folder odcinka> "<nagranie.mp3>"
```

W `podcast/<folder>/youtube/` powstają:
- `wideo.mp4` (1920×1080): plansza tytułowa z okładką na zapowiedź, plansze z tytułami rozdziałów, zdjęcia Leszka z artykułu
  (pokazywane mniej więcej wtedy, gdy lektor czyta fragment obok zdjęcia) i plansza końcowa,
  a także zdjęcia wysokiej jakości miejsc z [Atlasu Leszka](https://uleszka.net/atlas/) (Wikimedia Commons, wolne licencje):
  pokazywane, gdy lektor wspomina miejsce, i w długich przerwach, z nazwą miejsca, autorem i licencją w kadrze.
  Pobierają się raz do `podcast/.zdjecia/` (poza repozytorium). Bez nich: opcja `--bez-commons`,
- `miniatura.jpg` (1280×720) do YouTube,
- `opis.txt`: tytuł, opis i rozdziały ze znacznikami czasu (YouTube zrobi z nich rozdziały w odtwarzaczu), linki do miejsc w atlasie;
  mieści się w limicie 5000 znaków YouTube,
- `autorzy-zdjec.txt`: pełna lista autorów i licencji zdjęć z Commons (do wglądu albo do komentarza pod filmem),
- `napisy.txt`: dokładny tekst czytany przez lektora, bez znaczników tonu. W YouTube Studio: Napisy → Dodaj język
  (polski) → Dodaj napisy → „Automatyczna synchronizacja” → wklej tekst; YouTube sam dopasuje czasy.
  Same napisy, bez wideo: `npx tsx scripts/wideo.ts <folder> <nagranie.mp3> --tylko-napisy`.

Ruch i klipy:
- zdjęcia mają powolny ruch kamery (przybliżenie albo oddalenie z lekkim przesunięciem), plansze stoją,
- animacje 3D z `grafiki/3d/wideo/*/` (zasady: `grafiki/3d/wideo/ZASADY.md`) wchodzą same, gdy w tekście odcinka jest fraza
  z ich `klip.json`; w rogu kadru znaczek według rodzaju („Według rysunku Leszka Klimka”, „Hipoteza z tekstu, nie fakt”, „Rekonstrukcja 3D”),
- nagrania wideo z Wikimedia Commons (wolne licencje) z `podcast/<folder>/nagrania-cc.json`, z autorem i licencją w kadrze
  i w `autorzy-zdjec.txt`; pliki w `podcast/.nagrania-cc/` (poza repozytorium). Bez klipów: `--bez-klipow`,
- licencje cudzych materiałów w klipach 3D (np. katalog gwiazd HYG, plan Tikal, zdjęcie korony) są w `atrybucja.txt` obok klipu
  i trafiają do opisu i `autorzy-zdjec.txt`; sam opis i miniaturę bez składania wideo odświeża `--tylko-opis`,
- szybki podgląd fragmentu: `--zakres 600-900` (sekundy) daje `youtube/wideo-probka-600-900.mp4`,
- własne tło miniatury: `--miniatura grafiki/3d/wideo/<klip>/kadr.jpg`,
- wstęp: zamiast nieruchomej planszy z okładką zapowiedź idzie na animacji 3D `grafiki/3d/wideo/wstep/wersja-b/klip.mp4`, wspólnej dla
  wszystkich odcinków (pod muzykę zapowiedzi, cięcia na akcentach muzyki). Tytuł odcinka pojawia się na niej w górnej części kadru,
  gdy lektor mówi „Odcinek …” (czas z `mowa.jsonl`). Licencje wstępu (`wersja-b/atrybucja.txt`) trafiają do opisu i `autorzy-zdjec.txt`.
  Poprzednia wersja (A) leży w `grafiki/3d/wideo/wstep/klip.mp4`. Bez animacji: `--bez-wstepu`.

Cały film z ruchem składa się dłużej (dla 90 minut ok. pół godziny) i waży więcej (ok. 1,5–2 GB).

**Czasy (kiedy pokazać zdjęcie, klip, planszę rozdziału).** Najpierw raz na odcinek rozpoznaj mowę w nagraniu:
```
npx tsx scripts/wideo.ts podcast/<folder odcinka> "<nagranie.mp3>" --rozpoznaj
```
Rozpoznawanie robi whisper.cpp wbudowany w ffmpeg (od wersji 8), lokalnie i za darmo; trwa mniej więcej połowę długości nagrania.
Potrzebny jest model `ggml-large-v3-turbo-q5_0.bin` (574 MB, https://huggingface.co/ggerganov/whisper.cpp) w folderze
`../modele/` obok repozytorium albo w ścieżce ze zmiennej `WHISPER_MODEL` (na tym samym dysku co repozytorium).
Wynik `podcast/<folder>/mowa.jsonl` (zdania z czasami) zostaje w repozytorium i jest używany przy każdym kolejnym składaniu:
słowa nagrania są dopasowywane do słów artykułu, więc zdjęcie miejsca pojawia się 1–3 s po tym, jak lektor je wymieni,
a rozdziały w opisie YouTube trafiają w tytuły. Bez `mowa.jsonl` (albo z `--bez-mowy`) czasy są szacowane z długości tekstu
i potrafią się rozjechać o minutę i więcej. Zdjęcie, które nie zmieści się najwyżej 20 s po swoim miejscu
(np. przez klip), jest pomijane, a nie pokazywane za późno. Folder `youtube/` nie trafia do repozytorium.
Przy wgrywaniu zaznacz w YouTube, że głos jest wygenerowany przez AI.

## Harmonogram odcinków

`podcast/harmonogram.json` to plan kolejnych odcinków z „Cywilizacji Bogów”: lista artykułów w kolejności,
data pierwszego terminu (`od`), dni tygodnia (`dni_tygodnia`: 1 = poniedziałek … 7 = niedziela) i godzina (czas polski).
Każdy artykuł dostaje kolejny termin. Na stronie widać licznik do premiery: przy artykule w czytelni, na jego karcie
w spisie i jako „Następny odcinek” na stronie głównej. Gdy odcinek wyjdzie, dopisz go do `odcinki.json` – licznik
zamieni się w odtwarzacz. Po każdej zmianie: `npx tsx scripts/czytelnia.ts`.

- Dwa odcinki w tygodniu: `"dni_tygodnia": [2, 5]` (wtorek i piątek).
- Opóźnienie: przesuń `od` na nowy termin – wszystkie dalsze terminy przesuną się razem z nim.
- Inna kolejność: przestaw artykuły na liście.

## Odcinki

| Nr | Odcinek | Artykuły | Znaki |
|---|---|---|---|
| zwiastun | [Wstęp](00-wstep/ODCINEK.md) | Wstęp (Cywilizacja Bogów) | 9 448 |
| 1 | [Potop – czy tylko jeden?](01-potop-czy-tylko-jeden/ODCINEK.md) | Potop | 41 100 |
| 2 | [Wielki uskok…](02-wielki-uskok/ODCINEK.md) | Wielki uskok... | 76 187 |
| zapas | [Poznaj autora](zapas-poznaj-autora/ODCINEK.md) | Prywatnie (odcinek specjalny; przed nagraniem wygenerować z właściwym numerem) | 34 412 |

Kolejne odcinki i daty premier: `harmonogram.json` (co niedzielę o 10:00).

Numer `0` w poleceniu `teksty` oznacza zwiastun: zapowiedź mówi „Na początek: …” zamiast numeru odcinka,
a w Spotify for Creators wybiera się typ odcinka „Zwiastun” (Spotify pokazuje go na górze strony podcastu).

Pliki MP3 nie trafiają do repozytorium (są w `.gitignore`), żeby go nie powiększać.
