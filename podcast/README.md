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
**Monetyzacja:** wyłączona (archiwum ma charakter niekomercyjny)

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
5. Dopisz odcinek do `podcast/odcinki.json` (numer, tytuł, identyfikator z linku `open.spotify.com/episode/<id>`, id artykułów)
   i uruchom `npx tsx scripts/czytelnia.ts`. Przy tych artykułach w czytelni pojawi się odtwarzacz Spotify
   (zamiast czytania głosem przeglądarki). Na stronie głównej sekcję „Posłuchaj” (`docs/index.html`, `#podcast`) zmień ręcznie.
   Odtwarzacz Spotify wczytuje się dopiero po kliknięciu, więc bez kliknięcia strona nie łączy się ze Spotify.

## Odcinki

| Nr | Odcinek | Artykuły | Znaki |
|---|---|---|---|
| zwiastun | [Wstęp](00-wstep/ODCINEK.md) | Wstęp (Cywilizacja Bogów) | 9 448 |
| 1 | [Potop – czy tylko jeden?](01-potop-czy-tylko-jeden/ODCINEK.md) | Potop | 41 100 |
| 2 | [Poznaj autora](02-poznaj-autora/ODCINEK.md) | Prywatnie | 34 412 |

Numer `0` w poleceniu `teksty` oznacza zwiastun: zapowiedź mówi „Na początek: …” zamiast numeru odcinka,
a w Spotify for Creators wybiera się typ odcinka „Zwiastun” (Spotify pokazuje go na górze strony podcastu).

Pliki MP3 nie trafiają do repozytorium (są w `.gitignore`), żeby go nie powiększać.
