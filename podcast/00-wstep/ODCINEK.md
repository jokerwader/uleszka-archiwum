# Zwiastun: Wstęp

## Do wklejenia w ElevenLabs

Wklejaj pliki po kolei; każdy mieści się w limicie 10 000 znaków. Teksty mają znaczniki dla modeli v3/v4 w nawiasach kwadratowych (np. [calm, storytelling], [long pause]) – lektor ich nie czyta, tylko zmienia sposób mówienia; liczą się jednak do znaków. Nawiasy kwadratowe autora zamieniono na okrągłe, żeby lektor je przeczytał. Nagrania zapisz jako MP3 z tymi samymi numerami
(np. `00-zapowiedz.mp3`, `01-…mp3`) w tym folderze – potem: `npx tsx scripts/podcast.ts polacz podcast/00-wstep`.

| Plik | Co zawiera | Znaki (≈ kredyty) |
|---|---|---|
| 00-zapowiedz.txt | zapowiedź (nie jest tekstem autora) | 269 |
| 01-wstep.txt | Wstęp | 8901 |
| 99-zakonczenie.txt | zakończenie (nie jest tekstem autora) | 278 |

**Razem: 9448 znaków** (≈ 10 min nagrania).

## ElevenLabs Studio (rozdziały)

W folderze `rozdzialy-studio/` ten sam tekst jest podzielony według śródtytułów autora: jeden plik = jeden rozdział.
W Studio: nowy projekt → dla każdego pliku „Add chapter”, wklej tekst, nadaj tytuł z tabeli. Rozdział, który wyjdzie źle,
generujesz od nowa osobno; na końcu „Export” całego projektu do jednego MP3. Cały odcinek w jednym pliku: `calosc-do-studio.txt`.

| Plik | Rozdział | Znaki |
|---|---|---|
| 00-zapowiedz.txt | Zapowiedź | 269 |
| 01-wstep.txt | Wstęp | 8901 |
| 02-zakonczenie.txt | Zakończenie | 278 |

### Poprawione literówki (errata)

W tekście dla lektora poprawiono oczywiste literówki z oryginału (lista: `dane/poprawki/errata.json`):

| Artykuł | Było | Jest | Razy |
|---|---|---|---|
| Wstęp | moga | mogą | 1 |
| Wstęp | uzwględnić | uwzględnić | 1 |

## Opis odcinka (Spotify)

**Tytuł:** Wstęp

**Typ odcinka:** Zwiastun (w Spotify for Creators: typ odcinka „Zwiastun”; pokazuje się na górze strony podcastu)

Autor przedstawia założenia całego działu. Twierdzi, że oficjalna historia i teoria ewolucji są kontrolowane przez grupę naukowców broniących swojego monopolu, a początki cywilizacji opisują błędnie. Proponuje hipotezę o dawnej wysoko rozwiniętej „cywilizacji Bogów”, cyklicznych kataklizmach (wielkich uskokach skorupy ziemskiej), realnej Atlantydzie i błędnym przypisywaniu starożytnym ludom budowli, których nie mogły zbudować. Ostrzega, że kolejny globalny kataklizm jest nieuchronny, a ludzkość jest na niego nieprzygotowana.

Tekst Leszka Klimka ze strony uleszka.net („Uwierz we własny rozum”, 2004–2007), przeczytany bez zmian (poprawiono tylko oczywiste literówki). Czyta lektor AI (ElevenLabs). Archiwum i podcast powstały w hołdzie śp. Leszkowi Wiktorowi Klimkowi. Podcast przygotował jokerwader.

Teksty wyrażają poglądy autora sprzed ok. 20 lat.

Pełny tekst ze zdjęciami: https://uleszka.net/czytelnia/cybog-wstepcb.html
Rozmowa z archiwum przez AI: https://uleszka.net
