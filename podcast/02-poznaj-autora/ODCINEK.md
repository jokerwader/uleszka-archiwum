# Odcinek 2: Poznaj autora

## Do wklejenia w ElevenLabs

Wklejaj pliki po kolei; każdy mieści się w limicie 10 000 znaków. Teksty mają znaczniki dla modeli v3/v4 w nawiasach kwadratowych (np. [calm, storytelling], [long pause]) – lektor ich nie czyta, tylko zmienia sposób mówienia; liczą się jednak do znaków. Nawiasy kwadratowe autora zamieniono na okrągłe, żeby lektor je przeczytał. Nagrania zapisz jako MP3 z tymi samymi numerami
(np. `00-zapowiedz.mp3`, `01-…mp3`) w tym folderze – potem: `npx tsx scripts/podcast.ts polacz podcast/02-poznaj-autora`.

| Plik | Co zawiera | Znaki (≈ kredyty) |
|---|---|---|
| 00-zapowiedz.txt | zapowiedź (nie jest tekstem autora) | 275 |
| 01-wstep.txt | Wstęp | 8901 |
| 02-prywatnie-cz1.txt | Prywatnie, część 1 z 4 | 9227 |
| 03-prywatnie-cz2.txt | Prywatnie, część 2 z 4 | 9465 |
| 04-prywatnie-cz3.txt | Prywatnie, część 3 z 4 | 9383 |
| 05-prywatnie-cz4.txt | Prywatnie, część 4 z 4 | 5784 |
| 99-zakonczenie.txt | zakończenie (nie jest tekstem autora) | 281 |

**Razem: 43316 znaków** (≈ 46 min nagrania).

## ElevenLabs Studio (rozdziały)

W folderze `rozdzialy-studio/` ten sam tekst jest podzielony według śródtytułów autora: jeden plik = jeden rozdział.
W Studio: nowy projekt → dla każdego pliku „Add chapter”, wklej tekst, nadaj tytuł z tabeli. Rozdział, który wyjdzie źle,
generujesz od nowa osobno; na końcu „Export” całego projektu do jednego MP3. Cały odcinek w jednym pliku: `calosc-do-studio.txt`.

| Plik | Rozdział | Znaki |
|---|---|---|
| 00-zapowiedz.txt | Zapowiedź | 275 |
| 01-wstep.txt | Wstęp | 8901 |
| 02-calkiem-prywatnie.txt | CAŁKIEM PRYWATNIE | 5647 |
| 03-o-historii.txt | O HISTORII | 5329 |
| 04-o-najdawniejszej-polsce.txt | O NAJDAWNIEJSZEJ POLSCE | 5424 |
| 05-o-ochronie-przyrody-i-zabytkow.txt | O OCHRONIE PRZYRODY I ZABYTKÓW | 5202 |
| 06-o-zdrowiu.txt | O ZDROWIU | 2011 |
| 07-o-przyszlosci.txt | O PRZYSZŁOŚCI | 5626 |
| 08-co-zrozumialem.txt | CO ZROZUMIAŁEM? | 2590 |
| 09-co-robic.txt | CO ROBIĆ? | 1957 |
| 10-zakonczenie.txt | Zakończenie | 281 |

### Poprawione literówki (errata)

W tekście dla lektora poprawiono oczywiste literówki z oryginału (lista: `dane/poprawki/errata.json`):

| Artykuł | Było | Jest | Razy |
|---|---|---|---|
| Wstęp | moga | mogą | 1 |
| Wstęp | uzwględnić | uwzględnić | 1 |
| Prywatnie | artukule | artykule | 1 |
| Prywatnie | dżwięku | dźwięku | 1 |
| Prywatnie | indokrynacja | indoktrynacja | 1 |
| Prywatnie | kokwisty | konkwisty | 1 |
| Prywatnie | odłożyc | odłożyć | 1 |
| Prywatnie | ogladania | oglądania | 1 |
| Prywatnie | paździeżu | paździerzu | 1 |
| Prywatnie | przęjeli | przejęli | 1 |
| Prywatnie | wiecej | więcej | 1 |
| Prywatnie | wszyskich | wszystkich | 1 |
| Prywatnie | wymalowana | wymalowaną | 1 |
| Prywatnie | wysuwaja | wysuwają | 1 |
| Prywatnie | zastanowiał | zastanawiał | 1 |
| Prywatnie | żadem | żaden | 1 |

## Opis odcinka (Spotify)

**Tytuł:** Poznaj autora – Leszek Klimek

Autor przedstawia założenia całego działu. Twierdzi, że oficjalna historia i teoria ewolucji są kontrolowane przez grupę naukowców broniących swojego monopolu, a początki cywilizacji opisują błędnie. Proponuje hipotezę o dawnej wysoko rozwiniętej „cywilizacji Bogów”, cyklicznych kataklizmach (wielkich uskokach skorupy ziemskiej), realnej Atlantydzie i błędnym przypisywaniu starożytnym ludom budowli, których nie mogły zbudować. Ostrzega, że kolejny globalny kataklizm jest nieuchronny, a ludzkość jest na niego nieprzygotowana.

Autor strony żegna się z aktywnym prowadzeniem serwisu i w osobistej refleksji (wrzesień 2006) podsumowuje swoje poglądy. Pisze, że zaczął pisać w ramach rehabilitacji po wylewie z 2001 roku, a opierał się na hipotezie cyklicznych kataklizmów (Hapgood), na kwestionowaniu sposobu budowy dawnych budowli i obróbki kamienia oraz na przekonaniu, że oficjalna historia jest fałszowana, w tym historia Rzymu i Polski (Mieszko I jako marionetka rzymska). Dodaje krytyczne uwagi o ochronie przyrody i zabytków, zdrowym żywieniu, demokracji i polskiej polityce, a także o ewolucji i medycynie. Kończy radami: dbać o zdrowie i rozwój duchowy oraz poznawać prawdziwą historię.

Tekst Leszka Klimka ze strony uleszka.net („Uwierz we własny rozum”, 2004–2007), przeczytany bez zmian (poprawiono tylko oczywiste literówki). Czyta lektor AI (ElevenLabs). Archiwum i podcast powstały w hołdzie śp. Leszkowi Wiktorowi Klimkowi. Podcast przygotował Mateusz Małek (jokerwader).

Teksty wyrażają poglądy autora sprzed ok. 20 lat. W sprawach zdrowia nie zastępują porady lekarza.

Pełny tekst ze zdjęciami: https://uleszka.net/czytelnia/cybog-wstepcb.html · https://uleszka.net/czytelnia/refleksja.html
Rozmowa z archiwum przez AI: https://uleszka.net
