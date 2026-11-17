# zacmienie-slonca

Całkowite zaćmienie Słońca z 16 lipca 790 r. nad krajem Majów: cień Księżyca widziany z kosmosu, pas zaćmienia nad
Ameryką Środkową i korona Słońca widziana z ziemi. Na końcu podpis o tablicy zaćmień w Kodeksie drezdeńskim.
Rozdział 12 „Po co przekazano nam wiedzę astronomiczną?”, pytanie: „Skąd więc u Majów tak dokładne tabele zaćmień?”. 18 s.
Rodzaj: `ilustracja` (zjawisko potwierdzone). Klip nie rozstrzyga, skąd Majowie mieli swoją wiedzę – pokazuje, co przewidywali.

Zasada klipu: położenia, rozmiary i czasy są policzone z danych NASA, nie wymyślone. Lista tego, co umowne, jest niżej.

## Dlaczego to zaćmienie

Zaćmienie z 16 lipca 790 r. (kalendarz juliański) uchodzi za jedyny znany zapis zaćmienia Słońca z dokładną datą
w inskrypcjach Majów epoki klasycznej: stela 3 w Santa Elena Poco Uinic (Chiapas), data 9.17.19.13.16 5 Kib 14 Ch'en. Pas całkowitości przeszedł przez wybrzeże
Pacyfiku dzisiejszego Meksyku, Gwatemali i Salwadoru, czyli południowy skraj kraju Majów. To epoka klasyczna, do której
odnosi się pytanie z tekstu. Poprzednia wersja klipu używała zaćmienia z 11 lipca 1991 r. i toru wpisanego z pamięci.

Według rachunku (i według pracy Hayakawy, Sômy i Kinsmana z 2021 r.) przy samej steli zaćmienie nie było całkowite:
Księżyc zakrył 95% tarczy Słońca (faza 0,951), a północna granica pasa biegła 180 km na południe. Klip mówi to wprost
(podpis przy steli). Pas objąłby stelę dopiero, gdyby ΔT było większe o ok. 1100 s niż przyjmuje NASA.

## Co widać

1. **Klatki 1–140, widok od strony Słońca z 1,5 mln km** (teleobiektyw, okolice punktu L1, skąd dziś Ziemię fotografuje
   sonda DSCOVR). Ziemia się obraca, Księżyc (strona niewidoczna z Ziemi) przesuwa się na jej tle, a po Pacyfiku sunie
   ciemna plama półcienia. Rozmiary i odległości Ziemi i Księżyca są w skali. Zegar pokazuje czas uniwersalny.
2. **Klatki 140–335, dolot nad Amerykę Środkową.** Złoty okrąg to granica cienia (zaćmienie całkowite), za nim zostaje złoty
   pas o szerokości ok. 100 km. Podpisane miasta Majów: Palenque, Tikal, Calakmul, Copán, Chichén Itzá oraz stela
   w Santa Elena Poco Uinic. Biały pierścień: miejsce, z którego patrzymy w ujęciu 3.
3. **Klatki 336–450, widok z ziemi** ze środka pasa (14,50°N, 91,74°W, wybrzeże Pacyfiku w dzisiejszej Gwatemali, ten sam
   południk co stela; Słońce 68° nad horyzontem, ok. 13:30 czasu słonecznego). Ostatnie 90 s przed zakryciem, potem
   korona; zaćmienie całkowite trwało tu 2 min 46 s. Podpis: „Tablica zaćmień w Kodeksie drezdeńskim Majów: 405 lunacji
   = 11 960 dni, niecałe 33 lata”.

## Co jest policzone

Dane wejściowe: wielomianowe **elementy Bessela NASA** dla tego zaćmienia (Fred Espenak, „Five Millennium Canon of Solar
Eclipses”, zaćmienie nr 06652; efemerydy VSOP87/ELP2000-82; ΔT = 3015,4 s). Pliki: `_dane/zacmienie-0790/`.
Wzory: Jean Meeus, „Elements of Solar Eclipses 1951–2200” (1989), oraz „Explanatory Supplement to the Astronomical
Almanac” (1992), rozdz. 8. Kod: `bessel.py` (czysty Python). Z elementów wynikają:

- **oś cienia na Ziemi** w każdej klatce (przecięcie osi z elipsoidą o spłaszczeniu 1/298,257) i **obrót Ziemi**
  (kąt godzinny osi μ poprawiony o ΔT); kierunek światła Słońca (deklinacja osi d);
- **położenie Księżyca**: z promienia półcienia l1 i kąta stożka f1 wychodzi jego odległość (58,6 promienia Ziemi,
  373 880 km); Słońce leży na tej samej osi 151,7 mln km od Ziemi;
- **półcień i cień**: shader Ziemi liczy dla każdego punktu powierzchni odległość od osi cienia, promienie stożków
  na tej głębokości i z nich zakrytą część tarczy Słońca (wzór na pole wspólne dwóch kół). Złoty okrąg leży tam,
  gdzie odległość od osi równa się promieniowi cienia;
- **granice pasa całkowitości**: dla każdego południka (co 0,25°) szerokość, na której najmniejsza w czasie odległość
  od osi równa się promieniowi cienia (bisekcja);
- **widok z ziemi**: kierunki do środków Słońca i Księżyca z miejsca obserwacji, ich rozmiary kątowe i wzajemny ruch
  (stąd chwile początku i końca zaćmienia całkowitego), pociemnienie brzegowe tarczy Słońca (współczynnik 0,6);
- **gwiazdy**: katalog HYG (J2000) przeliczony na rok 790 macierzą precesji (Meeus, „Astronomical Algorithms”,
  wzory 21.2–21.4), obrócony czasem gwiazdowym (kąt godzinny osi + rektascensja Słońca z JPL Horizons).
  W kadrze teleobiektywu nie ma jasnych gwiazd ani planet: Merkury stał 17,6° od Słońca, Wenus 32° (JPL Horizons).

## Sprawdzenie obliczeń

`sprawdz.py` porównuje rachunek z danymi NASA; pełny wynik jest w `sprawdzenie.txt`.

| Co porównano | Nasz rachunek | NASA |
|---|---|---|
| 16 VII 790: chwila największego zaćmienia | 19:49:25 TDT = 18:59:10 UT | 19:49:25 TDT = 18:59:10 UT |
| miejsce największego zaćmienia | 18,0331°N, 104,1354°W | 18,0331°N, 104,1354°W |
| gamma | −0,0525 | −0,0525 |
| wysokość i azymut Słońca | 87,1°, 5,6° | 87,1°, 5,6° |
| szerokość pasa, czas trwania | 100,4 km, 3 min 03 s | 100,5 km, 3 min 03 s |
| linia środkowa i obie granice pasa, 210 południków co 0,5° | różnica szerokości poniżej 0,01 km | punkty toru ze strony NASA |
| 11 VII 1991 (kontrola na tabeli NASA co minutę, 189 wierszy) | linia środkowa do 0,18 km, granice do 0,15 km, szerokość pasa do 0,6 km, czas trwania do 0,2 s | tabela zaokrąglona do 0,1′ (ok. 0,2 km) |
| 16 VII 790, 20:29:30 TT: odległość Księżyca | 373 879 km | 373 878 km (JPL Horizons, DE441) |
| deklinacja Słońca / Księżyca | 20,9142° / 20,8279° | 20,9140° / 20,8279° (JPL Horizons) |

Elementy NASA liczono z teorii VSOP87/ELP2000-82, a JPL Horizons z efemerydy DE441, więc ostatnie dwa wiersze to
niezależne potwierdzenie. Dla steli w Poco Uinic rachunek daje fazę 0,951 o 13:29 czasu słonecznego; Hayakawa i in. (2021)
podają 0,946 o 13:29.

## Co jest umowne albo uproszczone

- **ΔT (tempo obrotu Ziemi w VIII w.)**: NASA przyjmuje 3015 s według Morrisona i Stephensona (2004). Błąd standardowy
  ΔT w tabeli NASA to 139 s dla roku 500 i 54 s dla roku 1000, czyli ok. 90 s dla roku 790. To przesuwa cały pas
  o ok. 0,4° długości (ok. 40 km) na wschód lub zachód. Napis w kadrze o tym mówi. Hayakawa i in. dopuszczają większe wahania.
- **Chmur nie ma**, bo pogody z 790 r. nie znamy. Obraz Ziemi to mozaika NASA z lipca 2004 r. (dzisiejsza roślinność i wybrzeża).
- **Jasność półcienia**: (odsłonięta część tarczy Słońca) do potęgi 0,7. Liniowo półcień zalałby mapę czernią.
- **Odblask Słońca w oceanie** i niebieska mgiełka atmosfery: przybliżone (model Blinna–Phonga, poświata przy brzegu tarczy).
- **Księżyc** jest zwrócony ku Ziemi południkiem 0° i ma biegun ku północy ekliptyki; libracji (do ok. 8°) nie liczono.
- **Korona Słońca** to fotografia zaćmienia z 11 sierpnia 1999 r. (Luc Viatour). Wyglądu korony z 790 r. nikt nie zna;
  jej ustawienie w kadrze jest dowolne. Rozmiar dopasowano tak, by tarcza Księżyca ze zdjęcia miała rozmiar tarczy
  policzonej (w 1999 r. stosunek średnic Księżyca i Słońca był taki sam: 1,029). Podpis autora jest w kadrze.
- **Brzeg Księżyca** jest gładkim kołem (bez gór), więc nie ma „pereł Baily'ego”. Kolory nieba są dobrane do planszy
  filmu; jasność nieba maleje z logarytmem odsłoniętej części tarczy.
- **Czas w klipie jest przyspieszony**: ujęcie 1 obejmuje 17:28–18:40 UT, ujęcie 2 do 19:36 UT, ujęcie 3 ostatnie 90 s
  przed zakryciem i pierwsze 83 s zaćmienia całkowitego (19:36:21–19:39:14 UT).
- Kamera w ujęciu 1 stoi 1° od linii Słońce–Ziemia, dlatego Księżyc widać obok jego cienia, a nie dokładnie nad nim.

## Tablica zaćmień w Kodeksie drezdeńskim

Strony 51–58 kodeksu: tablica ostrzeżeń przed zaćmieniami obejmująca 405 miesięcy księżycowych, czyli 11 960 dni
(405 × 29,530588 = 11 959,9 dnia; 11 960 = 46 × 260 dni kalendarza obrzędowego), niecałe 33 lata.
Źródła: H. M. Bricker, V. R. Bricker, „Classic Maya Prediction of Solar Eclipses”, Current Anthropology 24(1), 1983, s. 1–23;
A. F. Aveni, „Skywatchers”, University of Texas Press 2001; J. Justeson, J. Lowry, praca o tablicy zaćmień Kodeksu
drezdeńskiego w Science Advances 2025, https://doi.org/10.1126/sciadv.adt9039 .

Stela z Poco Uinic: J. E. Teeple, „Maya Astronomy”, Carnegie Institution of Washington 1931; S. Martin, J. Skidmore,
„Exploring the 584286 Correlation between the Maya and European Calendars”, The PARI Journal 13(2), 2012, s. 3–16;
H. Hayakawa, M. Sôma, J. H. Kinsman, „Analyses of a Datable Solar Eclipse Record in Maya Classic Period Monumental
Inscriptions”, Publications of the Astronomical Society of Japan 73(6), 2021, L31, https://doi.org/10.1093/pasj/psab088 .

## Źródła i licencje (szczegóły w `_dane/ZRODLA.md`)

- Elementy Bessela, tor i mapka zaćmienia: NASA, „Eclipse Predictions by Fred Espenak, NASA's GSFC” (domena publiczna).
- Położenia Słońca, Księżyca i planet do kontroli: JPL Horizons, DE441 (domena publiczna).
- Ziemia: NASA Blue Marble Next Generation, lipiec 2004 (domena publiczna); cały glob 8192×4096 i wycinek Ameryki
  Środkowej w rozdzielczości 500 m.
- Księżyc: mapa barwna LRO z zestawu NASA „CGI Moon Kit” (domena publiczna).
- Gwiazdy: katalog HYG v4.4 (CC BY-SA 4.0).
- Korona: Luc Viatour, „Solar eclipse 1999 4”, CC BY-SA 3.0 (Wikimedia Commons). Ostatnie ujęcie klipu jest utworem
  zależnym na tej samej licencji.
- Współrzędne miast Majów: `atlas/atlas.json` (Wikidata); Santa Elena Poco Uinic 16,5875°N, 91,7390°W (Wikipedia).

## Pliki

- `bessel.py` – wzory (elementy Bessela → oś cienia, obserwator, granice pasa, Księżyc i Słońce), wczytanie danych NASA.
- `sprawdz.py`, `sprawdzenie.txt` – porównanie z NASA i JPL.
- `scena.py` – scena Blendera (korzysta z `bessel.py` i `_wspolne/`).

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/zacmienie-slonca/scena.py`
(450 klatek, EEVEE, 32 próbki). Kadry próbne: `-- --proba 60,130,236,300,350,370,450`.
Sprawdzenie rachunku: `S:\Blender\5.3\python\bin\python.exe grafiki/3d/wideo/zacmienie-slonca/sprawdz.py`.
