# Odcinek 1: Potop – czy tylko jeden?

## Do wklejenia w ElevenLabs

Wklejaj pliki po kolei; każdy mieści się w limicie 10 000 znaków. Teksty mają znaczniki dla modeli v3/v4 w nawiasach kwadratowych (np. [calm, storytelling], [long pause]) – lektor ich nie czyta, tylko zmienia sposób mówienia; liczą się jednak do znaków. Nawiasy kwadratowe autora zamieniono na okrągłe, żeby lektor je przeczytał. Nagrania zapisz jako MP3 z tymi samymi numerami
(np. `00-zapowiedz.mp3`, `01-…mp3`) w tym folderze – potem: `npx tsx scripts/podcast.ts polacz podcast/01-potop-czy-tylko-jeden`.

| Plik | Co zawiera | Znaki (≈ kredyty) |
|---|---|---|
| 00-zapowiedz.txt | zapowiedź (nie jest tekstem autora) | 293 |
| 01-potop-cz1.txt | Potop, część 1 z 5 | 8926 |
| 02-potop-cz2.txt | Potop, część 2 z 5 | 9255 |
| 03-potop-cz3.txt | Potop, część 3 z 5 | 9496 |
| 04-potop-cz4.txt | Potop, część 4 z 5 | 8901 |
| 05-potop-cz5.txt | Potop, część 5 z 5 | 3959 |
| 99-zakonczenie.txt | zakończenie (nie jest tekstem autora) | 246 |

**Razem: 41076 znaków** (≈ 43 min nagrania).

## ElevenLabs Studio (rozdziały)

W folderze `rozdzialy-studio/` ten sam tekst jest podzielony według śródtytułów autora: jeden plik = jeden rozdział.
W Studio: nowy projekt → dla każdego pliku „Add chapter”, wklej tekst, nadaj tytuł z tabeli. Rozdział, który wyjdzie źle,
generujesz od nowa osobno; na końcu „Export” całego projektu do jednego MP3. Cały odcinek w jednym pliku: `calosc-do-studio.txt`.

| Plik | Rozdział | Znaki |
|---|---|---|
| 00-zapowiedz.txt | Zapowiedź | 293 |
| 01-zrodla-pisane-starozytni.txt | Źródła pisane - Starożytni | 11288 |
| 02-co-wiemy-na-temat-potopu.txt | Co wiemy na temat potopu | 11147 |
| 03-co-moglo-byc-przyczyna-potopu.txt | Co mogło być przyczyną Potopu? | 5250 |
| 04-teoria-potopu.txt | Teoria potopu | 6189 |
| 05-byl-taki-czlowiek.txt | Był taki człowiek | 1670 |
| 06-cos-w-rodzaju-podsumowania.txt | Coś w rodzaju podsumowania | 4960 |
| 07-zakonczenie.txt | Zakończenie | 246 |

### Poprawione literówki (errata)

W tekście dla lektora poprawiono oczywiste literówki z oryginału (lista: `dane/poprawki/errata.json`):

| Artykuł | Było | Jest | Razy |
|---|---|---|---|
| Potop | cos | coś | 1 |
| Potop | obraca-jącej | obracającej | 1 |
| Potop | odziaływuje | oddziaływuje | 1 |
| Potop | ten w gąszcz | ten gąszcz | 1 |
| Potop | Zusiudra | Ziusudra | 2 |

## Opis odcinka (Spotify)

**Tytuł:** Potop – czy tylko jeden? – Leszek Klimek

Autor zestawia starożytne przekazy o potopie (biblijny, sumeryjski, grecki, mezoamerykańskie, Oera Linda Boek, Kronika Akakor, Indian Hopi) i dochodzi do wniosku, że potopy były co najmniej kilka, a ostatni nastąpił ok. 12,5 tys. lat temu. Odrzuca jako przyczynę zbliżenie wielkiego ciała niebieskiego i uderzenie meteorytu, a opowiada się za hipotezą Hapgooda o nagłym przesunięciu skorupy ziemskiej. Za Caseyem Wadowskim przyjmuje, że kataklizm przewidziała wysoko rozwinięta cywilizacja Bogów-Nauczycieli, która zabezpieczyła wiedzę i pomagała odbudowie. Twierdzi, że skorupa Ziemi nadal się nie ustabilizowała i kolejny kataklizm jest możliwy, a nauka tej hipotezy ignoruje.

Tekst Leszka Klimka ze strony uleszka.net („Uwierz we własny rozum”, 2004–2007), przeczytany bez zmian (poprawiono tylko oczywiste literówki). Czyta lektor AI (ElevenLabs). Archiwum powstało w hołdzie śp. Leszkowi Wiktorowi Klimkowi.

Teksty wyrażają poglądy autora sprzed ok. 20 lat. W sprawach zdrowia nie zastępują porady lekarza.

Pełny tekst ze zdjęciami: https://uleszka.net/czytelnia/01potop-potop.html
Rozmowa z archiwum przez AI: https://uleszka.net
