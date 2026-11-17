# Audyt prawdziwości klipów 3D (16.11.2026)

Zasada: każdy render ma mieć oparcie w prawdzie i w prawdziwych wzorach. Położenia gwiazd i planet, daty, kąty, mapy,
wymiary budowli i czasy fal mają być policzone albo wzięte ze źródeł. Uproszczenia są w porządku, jeśli kadr i README
je nazywają. Klipy rodzaju `hipoteza` mogą pokazywać tezę z tekstu, ale dane wokół niej muszą być prawdziwe.

Poza zakresem (robią je inne sesje): `zacmienie-slonca`, `tikal-przelot`, `wschod-slonca-z-piramidy`, `fala-po-uskoku`,
oraz `wstep/` i `czolowka/`.

## Jak sprawdzano

- **Gwiazdy:** pełny katalog HYG v4.4 (z ruchem własnym i prędkościami), precesja według wzorów IAU 1976
  (J. Meeus, „Astronomical Algorithms”, rozdz. 21), ruch własny liniowo w przestrzeni.
- **Planety i Słońce:** efemeryda JPL Horizons (DE441, https://ssd.jpl.nasa.gov/horizons/) jako wzorzec; porównanie ze
  średnimi elementami orbit E. M. Standisha (JPL, „Approximate Positions of the Planets”), których używa `_wspolne/niebo.py`.
- **Granice gwiazdozbiorów:** wielokąty granic IAU (Delporte 1930) z pliku `constellations.bounds.json` projektu
  d3-celestial; policzone przecięcia z ekliptyką.
- **Tsunami:** baza NOAA NCEI (zdarzenie 2439), pobrana na nowo przez API (2177 rekordów, 213 z czasem dojścia).
- **Budowle:** W. M. F. Petrie „The Pyramids and Temples of Gizeh” (1883), R. Engelbach „The Aswân Obelisk” (1922),
  Platon „Kritias” (przekład Jowetta, Wikisource), hasła Wikipedii (tekst źródłowy pobrany 16.11.2026).
- **Mapy:** Natural Earth; granice płyt PB2002 (P. Bird 2003).

## Wynik

Oznaczenia: **zgodne** (nic do zmiany w obrazie), **README** (obraz poprawny, dopisane źródło lub sprostowanie),
**BŁĄD** (obraz do poprawy i nowego renderu).

| Klip | Co sprawdzone | Wynik | Źródło | Co poprawić |
|---|---|---|---|---|
| `giza-pas-oriona` | odległości środków piramid, boki, wysokości, gwiazdy pasa, dopasowanie | **BŁĄD**: odległość wschód–zachód Chefren–Mykerinos wzięta z Wikidata (254,6 m) zamiast z pomiaru Petriego (9450,2 cala = 240,0 m); Mykerinos stał o 14,6 m za daleko na zachód. Po poprawce: obrót −164,7° (było −165,4°), skala 342,3 m/° (było 345,5), odchyłki 9,1 / 18,0 / 8,9 m (było 6,9 / 13,6 / 6,7). Napis w kadrze „odchyłki do 14 m” był zaniżony | Petrie 1883, §92 (tabela odległości środków: I–II 13931,6 N i 13165,8 E; I–III 29102,0 i 22616,0; II–III 15170,4 i 9450,2 cala) | wszystkie trzy położenia z Petriego, napis „odchyłki do 18 m”, nowy render |
| `wenus-pozycja` | pozycje Wenus i Ziemi 22.12.2012, pozycja z 9792 p.n.e., kierunki gwiazdozbiorów | **BŁĄD**: (1) kierunki gwiazdozbiorów Zodiaku wpisane z pamięci, przesunięte o 4–10° (np. Strzelec 275° zamiast 283°, Panna 190° zamiast 196°), bez Wężownika; (2) Wenus i Ziemia ustawione według długości średniej zamiast prawdziwej (Wenus 213,7° zamiast 214,5°; Ziemia 90,8° zamiast 90,4°); (3) README: Wenus stała „w Wadze” – naprawdę w Pannie (granica Panna/Waga na 217,8°). Twierdzenie Lenga nie potwierdza się: 27.07.9792 p.n.e. Wenus miała długość heliocentryczną 98,7° (Bliźnięta), a 22.12.2012 – 214,5° | JPL Horizons DE441 (wektory heliocentryczne Wenus dla obu dat); granice IAU | granice i środki gwiazdozbiorów policzone, pozycje z równania Keplera, README, nowy render |
| `syriusz-kalendarz-egiptu` | niebo przy wschodzie Syriusza, azymut łuny świtu, budowa kalendarza, cykl 1460 lat | **BŁĄD**: niebo było dzisiejsze (J2000), nie starożytne: w 1322 r. p.n.e. Syriusz miał deklinację −17,8° (dziś −16,7°), a Orion stał inaczej względem horyzontu (Betelgeza azymut 108° zamiast 97°, Rigel wysokość 22° zamiast 26°). Łuna świtu malowana w azymucie 73°; z rachunku Słońce było w azymucie 58°. Kalendarz (12 × 30 + 5 dni, pory Achet/Peret/Szemu, nazwy miesięcy, 1460 lat) zgodny | HYG v4.4 + precesja + ruch własny; długość Słońca wg Meeusa rozdz. 25; kontrola: z tego samego rachunku wschód heliakalny w 139 r. n.e. wypada 20–21 lipca, tak jak u Cenzoryna | niebo dla Memfis (29,85°N), świt 19 lipca 1322 r. p.n.e. (początek cyklu, który skończył się w 139 r. n.e.), Słońce policzone, nowy render |
| `tsunami-2004` | czasy dojścia fali w 9 punktach, ognisko, model czoła fali | punkty: **zgodne** co do minuty z NOAA (wszystkie 9; ognisko 3,295°N 95,982°E, 00:58:53 UTC). **BŁĄD** w modelu czoła fali: głębokość oceanu była zgadywana z odległości od brzegu, przez co czoło mijało Phuket po 0:58, a mareograf zanotował 1:56 | NOAA NCEI, zdarzenie 2439; batymetria ETOPO (NOAA, domena publiczna) | czoło fali policzyć na prawdziwej batymetrii (v = √(g·h)), nowy render |
| `zwiastun-kamienne-olbrzymy` | wymiary i masy 6 kamieni | wymiary i masy **zgodne** ze źródłami (trylit 19 × 4,2 × 3,6 m i 750–800 t; Kamień Ciężarnej Kobiety 20,31–20,76 m i ok. 1000 t; sarsen 4,1 × 2,1 m i 25 t; blok piramidy śr. 2,5 t; Sacsayhuamán 128–200 t). **BŁĄD** drobny: piramidion obelisku miał 3,2 m długości, według Engelbacha 4,5 m; podstawa 4,2 m i szerokość 2,5 m pod piramidionem były dobre, ale README pisało, że „nie pochodzą ze sprawdzonego źródła” | R. Engelbach, „The Aswân Obelisk” (1922): długość 41,75 m, podstawa 4,20 m, podstawa piramidionu 2,50 m, wysokość piramidionu 4,50 m, 1168 ton ang.; Wikipedia: „Baalbek Stones”, „Stonehenge”, „Sacsayhuamán” | piramidion 4,5 m, README ze źródłami, nowy render |
| `paski-magnetyczne` | kolejność i szerokość pasów | **BŁĄD** (dane wymyślone): odwrócenia pola liczyła funkcja z sinusów; istnieje prawdziwa skala odwróceń pola | skala czasu polarności GPTS (Brunhes, Matuyama, Jaramillo, Olduvai, Gauss, Kaena, Mammoth, Gilbert) | pasy według prawdziwej skali z ostatnich ok. 5 mln lat, nowy render |
| `tiamat-zderzenie` | układ planet, tło | hipoteza Sitchina pokazana zgodnie z tekstem; kolejność planet prawdziwa, skala orbit umowna (README to mówi). **BŁĄD** drobny: gwiazdy w tle losowe | katalog HYG | tło z prawdziwych gwiazd (widok na płaszczyznę ekliptyki), nowy render |
| `ziemia-z-kosmosu` | odległość i rozmiar Księżyca, Mars, czasy lotu | liczby **zgodne**: 384 400 km = 60,27 promienia Ziemi; promień Księżyca 0,2727; Mars 55,76 mln km (27.08.2003) = 145 × dalej; Apollo ok. 3 dni; Mars ok. 7 miesięcy. Umowne (README to mówi): kierunek Słońca, obrót tła gwiazd, powierzchnia Księżyca z szumu | NASA (fakty ogólne) | do rozważenia: ustawić Słońce, Księżyc i gwiazdy na konkretną datę |
| `stonehenge-swit-2012` | położenia Wegi, Spiki, Alamaka, Jowisza, Wenus, Saturna 6:00–6:23 UT; plan kręgu | **zgodne**: planety różnią się od JPL Horizons o 0,1–0,2° (Wenus 6:00: klip 120,8°/−2,2°, Horizons 120,7°/−2,3°; Jowisz 300,2°/3,2° i 300,0°/3,4°); gwiazdy bez precesji z 13 lat: błąd do 0,17°. Wenus wschodzi (bez refrakcji) 6:17, Jowisz zachodzi 6:25. Układ kamieni (17 stojących sarsenów o właściwych numerach, nadproża, trylity, Heel Stone 77 m, jamy Aubreya 43,3 m) zgodny z planem zabytku | JPL Horizons; HYG | README: dopisane porównanie |
| `niebo-gwiazdozbiory` | gwiazdy, biegun, ekliptyka, wymiary El Caracol i El Castillo | **zgodne**: niebo dzisiejsze (J2000) nad dzisiejszą ruiną; biegun 20,7° nad horyzontem; ekliptyka 23,44°. El Caracol: platforma 67 × 52 m, wieża 16 m, razem ok. 23 m; El Castillo 55,3 m i 24 + 6 m | HYG; opisy INAH | README: dopisać, że to niebo dzisiejsze (w X w. biegun leżał ok. 6° od Gwiazdy Polarnej) |
| `grzbiet-atlantycki` | oś grzbietu (38 punktów „z map”) | **zgodne**: średnia odległość od granic płyt PB2002 0,31° (34 km), największa 1,2° (131 km, koniec przy Wyspie Bouveta); README obiecuje „ok. 1°” | P. Bird 2003, PB2002 (granice NA–EU, NA–AF, AF–SA) | README: dopisane porównanie |
| `obliczenia-biegun` | współrzędne 7 miejsc, azymuty na Akpatok | **zgodne**: azymuty z README przeliczone (19,9°; 17,9°; 15,3°; 13,7°; 1,3°; −0,7°; −31,6°) | wzór na azymut koła wielkiego | nic |
| `odchylenie-17-globus` | azymuty z Jukatanu i Egiptu na Akpatok | **zgodne**: 14,2° na wschód i 31,1° na zachód | jw. | nic |
| `kalendarz-majow-2012` | rachunek dat | **zgodne**: 13.0.0.0.0 = 4 Ajaw 3 K'ank'in; 60 dni wcześniej 12.19.19.15.0 = 9 Ajaw 3 Sak'; 21 lub 23.12.2012 zależnie od stałej (584283 / 584285) | rachunek | nic |
| `epoki-lodowcowe` | dane wykresu | **zgodne**: wykres wprost z pliku EPICA Dome C (5800 próbek) | Jouzel i in. 2007, PANGAEA | nic |
| `kamien-slonca-4-ollin` | średnica, układ czterech Słońc | **zgodne**: średnica 3,58 m; prawy górny 4 Jaguar, lewy górny 4 Wiatr, lewy dolny 4 Deszcz, prawy dolny 4 Woda | Wikipedia „Aztec sun stone” | nic |
| `zwiastun-atlantyda-platona` | liczby z „Kritiasa” | **zgodne**: wyspa 5 stadiów, pierścienie wody 1, 2, 3 i lądu 2, 3 stadia, kanał 50 stadiów × 300 stóp × 100 stóp, most 1/6 stadionu, świątynia 1 × 0,5 stadionu, tor 1 stadion, mur 50 stadiów od portu, mury: mosiądz, cyna, orichalk | Platon, „Kritias” (Jowett) | nic |
| `zwiastun-nadchodzi-przeszlosc` | wysokość Statuy Wolności | **zgodne**: 46 m posąg, 93 m z cokołem | Wikipedia | nic |
| `poslizg-skorupy` | promienie warstw Ziemi | **zgodne**: 6371, 3480, 1220 km (PREM: 1221,5); strefa 400–600 km jest z tekstu Leszka i tak podpisana | model PREM | nic |
| `grenlandia-odwiert` | głębokość odwiertu, krzywa | **zgodne**: krzywa z pikseli rysunku Leszka; GRIP 3029 m, GISP2 3053 m | rysunek; GRIP/GISP2 | nic |
| `lod-przy-biegunie` | zasięg lodu, biegun, kierunek siły | **zgodne** z rysunkami Leszka; zasięg lodu z jego mapy przeliczony na kulę; siła odśrodkowa skierowana od osi (poprawnie); grubość lodu umowna i tak opisana | rysunki Leszka; Natural Earth | nic |
| `teotihuacan-aleja` | kąt alei | **zgodne** ze szkicem (19,4° na szkicu, „ok. 18°” z tekstu); README podaje pomiar dzisiejszy 15,5° | szkic Leszka | nic |
| `tikal-kompas` | położenia świątyń, kąty | **zgodne** z planem S. Burchella (CC BY-SA) i ze szkicem; README podaje, że na planie wychodzi 12–13°, nie 17° | plan z Commons | nic |
| `uskok-globus`, `tektonika-globus`, `slone-jeziora`, `stonehenge-szkic` | wierność rysunkom Leszka, mapy | **zgodne**: treść odczytana z pikseli rysunków, lądy z Natural Earth lub Blue Marble | rysunki Leszka | nic |
| `osiem-slupow-nieba` | treść mitu | **zgodne** z cytatem (mit, stylizacja nazwana w README) | „Tianwen” w cytacie Leszka | nic |
| `titicaca-linia-brzegowa`, `obieg-wody`, `zwiastun-linia-brzegowa`, `zwiastun-domek-z-kart` | schematy bez danych liczbowych | **zgodne**: schemat zasady, krajobraz umowny i tak opisany w README (w `titicaca` także w kadrze) | tekst Leszka | nic |

## Podsumowanie

- Rzeczywiste błędy danych: `giza-pas-oriona`, `wenus-pozycja`, `syriusz-kalendarz-egiptu`, `tsunami-2004` (model fali),
  `zwiastun-kamienne-olbrzymy` (piramidion obelisku).
- Dane wymyślone tam, gdzie istnieją prawdziwe: `paski-magnetyczne`, `tiamat-zderzenie` (tło gwiazd).
- Pozostałe klipy są zgodne ze źródłami; w kilku README dopisano sprawdzenie.
- Stan poprawek: rozdział „Poprawki” poniżej.

## Poprawki (stan na 16.11.2026, wieczór)

Wszystkie siedem klipów z błędami ma poprawiony `scena.py`, nowy pełny render (`klip.mp4`, `kadr.jpg`) i uzupełnione
`README.md`. Długości klipów się nie zmieniły, frazy w `klip.json` też nie.

| Klip | Co zmienione | Jak sprawdzone |
|---|---|---|
| `giza-pas-oriona` | położenia Chefrena i Mykerinosa wprost z pomiaru Petriego (§92); napis „odchyłki do 18 m” liczony z dopasowania (było „do 14 m”) | dopasowanie: obrót 164,7°, odchyłki 9,1 / 18,0 / 8,9 m; arkusz kadrów |
| `wenus-pozycja` | Wenus i Ziemia z równania Keplera na elipsach (było: długość średnia na okręgach); pas Zodiaku z 13 odcinków według granic IAU, z Wężownikiem; liczba okrążeń liczona z dat | Wenus 214,49°, Ziemia 90,36° (JPL Horizons: 214,50° i 90,36°); arkusz kadrów |
| `syriusz-kalendarz-egiptu` | niebo na świt 19 lipca 1322 r. p.n.e. w Memfis (ruch własny i precesja), łuna świtu w azymucie Słońca, podpis w kadrze | Syriusz wschodzi w azymucie 110°, Słońce 11° pod horyzontem w azymucie 55°; te same wzory dają dla 139 r. n.e. 20–21 lipca (Cenzoryn); arkusz kadrów |
| `tsunami-2004` | czoło fali liczone na batymetrii ETOPO1 (v = √(g·h)), źródło wzdłuż rowu Sundajskiego; czasy stacji NOAA bez zmian | model względem pomiaru: Kolombo 0 min, Ćennaj +5, Phuket +28, Perth −20, Port Elizabeth −35; mediana 26 min dla 96 mareografów; arkusz kadrów |
| `zwiastun-kamienne-olbrzymy` | piramidion obelisku 4,5 m (było 3,2 m), wymiary z Engelbacha (1922) | kadry próbne 305 i 400; arkusz kadrów |
| `paski-magnetyczne` | pasy według skali Cande'a i Kenta (1995) od 2,3 mln lat temu do dziś, licznik czasu i podpis źródła w kadrze | sześć granic widocznych w klipie (0,78–2,58 mln lat) zgodnych z tabelami wtórnymi; starsze granice z tabeli w `scena.py` niewidoczne w klipie i niesprawdzone; arkusz kadrów |
| `tiamat-zderzenie` | tło: gwiazdy z katalogu HYG w układzie ekliptycznym (było: losowe) | arkusz kadrów |

Nowe pliki wspólne: `_wspolne/epoka.py` (precesja, ruch własny, Słońce na dowolną datę), `_dane/hyg/gwiazdy_mag6_ruch.csv`,
`_dane/etopo/etopo1_ocean_indyjski_5min.npz` (opisane w `_dane/ZRODLA.md`).

README uzupełnione bez renderu: `stonehenge-swit-2012`, `niebo-gwiazdozbiory`, `grzbiet-atlantycki`, `ziemia-z-kosmosu`,
`obliczenia-biegun`, `kalendarz-majow-2012`, `zwiastun-atlantyda-platona`.

Sprawdzenie składania filmu: `npx tsx scripts/wideo.ts podcast/02-wielki-uskok <mp3> --zakres 0-1` kończy się
„Gotowe” i nie wypisuje „Nie zmieściły się klipy”; sześć przerobionych klipów odcinka jest w planie
(klipy `zwiastun-*` należą do odcinka wstępnego).

Zostało:
- `ziemia-z-kosmosu`: liczby poprawne, ale kierunek Słońca, obrót tła gwiazd i strona Ziemi nie odpowiadają żadnej
  dacie. Można ustawić konkretny dzień; zmieni to wygląd pierwszego ujęcia.
- `tsunami-2004`: model nie jest dopasowywany do pomiarów, więc izochrony różnią się od mareografów (mediana 26 min).
  Dokładniej da się tylko z modelem źródła o skończonych rozmiarach i gęstszą batymetrią przy brzegach.
- `stonehenge-swit-2012` i `niebo-gwiazdozbiory`: gwiazdy bez precesji od 2000 r. (błąd do 0,2°), opisane w README.

