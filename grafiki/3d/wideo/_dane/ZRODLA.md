# Źródła danych wspólnych dla klipów 3D

## natural-earth/
Natural Earth (naturalearthdata.com), domena publiczna. Pliki `ne_10m_*`, `ne_50m_*` (lądy, jeziora) w formacie GeoJSON.

## blue-marble/blue-marble-2002-8192x4096.jpg
NASA Blue Marble 2002, „Land Surface, Shallow Water, and Shaded Topography” (Reto Stöckli, NASA Earth Observatory).
Domena publiczna (dzieło NASA). Pobrane z Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Land_shallow_topo_2048.jpg (plik 21600×10800, zmniejszony ffmpeg-iem do 8192×4096).
Odwzorowanie walcowe równoodległościowe: lewa krawędź 180°W, górna 90°N.

## hyg/gwiazdy_mag6.csv
Wyciąg z katalogu gwiazd HYG v4.4 (David Nash, astronexus; połączenie katalogów Hipparcos, Yale Bright Star i Gliese).
Licencja: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), wyciąg udostępniamy na tej samej licencji.
Pobrane: https://codeberg.org/astronexus/hyg (plik `data/hyg/CURRENT/hyg_v44.csv.gz`), 16.11.2026.
Zawartość: 5070 gwiazd jaśniejszych niż 6,0 mag (bez Słońca), kolumny: hip, hr, proper (nazwa), ra_h (rektascensja, godz.),
dec_deg (deklinacja, °), mag, ci (wskaźnik barwy B−V), bayer, flam, con (gwiazdozbiór). Epoka i równonoc J2000.
Używa: `niebo-gwiazdozbiory`.

## kamien-slonca/Piedra_del_Sol_en_MNA.jpg
Fotografia azteckiego Kamienia Słońca w Muzeum Narodowym Antropologii w Meksyku. Autor: Juan Carlos Fonseca Mata (2019).
Licencja: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Pobrane 16.11.2026 z Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Piedra_del_Sol_en_MNA.jpg (oryginał 3335×2822, bez zmian).
Używa: `kamien-slonca-4-ollin` (klip jest utworem zależnym na tej samej licencji).

## epica/EPICA_DomeC_deuter_temperatura.tab
Rdzeń lodowy EPICA Dome C (Antarktyda): zawartość deuteru i oszacowanie temperatury z ostatnich 800 tys. lat (5800 próbek,
skala wieku EDC3). Jouzel, J., Masson-Delmotte, V. (2007): „EPICA Dome C Ice Core 800KYr deuterium data and temperature
estimates”, PANGAEA, https://doi.org/10.1594/PANGAEA.683655 (dodatek do: Jouzel i in., Science 317, 793–797, 2007).
Licencja: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/). Pobrane 16.11.2026 w formacie tekstowym, bez zmian.
Kolumny: głębokość [m], wiek [tys. lat przed 1950], δD [‰], odchylenie temperatury [°C] od średniej z ostatniego tysiąclecia.
Używa: `epoki-lodowcowe`.

## hyg/gwiazdy_mag6_ruch.csv
Te same 5070 gwiazd co w `gwiazdy_mag6.csv` (ta sama kolejność), z dodatkowymi kolumnami z katalogu HYG v4.4:
pmra_mas i pmdec_mas (ruch własny w rektascensji i deklinacji, milisekundy łuku na rok; pmra zawiera już cos δ),
dist_pc (odległość, parseki), rv_kms (prędkość radialna, km/s). Licencja jak wyżej: CC BY-SA 4.0. Pobrane 16.11.2026.
Służy do liczenia nieba w innych epokach (ruch własny + precesja): `_wspolne/epoka.py`.
Używa: `syriusz-kalendarz-egiptu`.

## etopo/etopo1_ocean_indyjski_5min.npz
Wycinek modelu rzeźby Ziemi ETOPO1 („Ice Surface”, 1 minuta kątowa): ocean Indyjski z otoczeniem, 15°E–160°E i 75°S–32°N,
co piąty punkt siatki (5 minut kątowych, 1285 × 1741 punktów). Amante, C., Eakins, B. W. (2009): „ETOPO1 1 Arc-Minute
Global Relief Model: Procedures, Data Sources and Analysis”, NOAA Technical Memorandum NESDIS NGDC-24.
Dzieło rządu USA (NOAA), domena publiczna. Pobrane 16.11.2026 z serwera NOAA ERDDAP:
https://upwell.pfeg.noaa.gov/erddap/griddap/etopo180 (zmienna `altitude`), zapisane jako tablica numpy.
Zawartość pliku: `wys` (wysokość w metrach, liczby całkowite; morze ujemne, wiersz 0 = 75°S), `szer0`, `dlug0` (współrzędne
pierwszego punktu), `krok` (odstęp siatki w stopniach).
Używa: `tsunami-2004` (prędkość fali z głębokości).

## zacmienie-0790/
Dane NASA o całkowitym zaćmieniu Słońca z 16 lipca 790 r. (kalendarz juliański), nr 06652 w katalogu
„Five Millennium Canon of Solar Eclipses: -1999 to +3000” (Fred Espenak, Jean Meeus, NASA/TP-2006-214141).
Domena publiczna (dzieło NASA); NASA prosi o dopisek: „Eclipse Predictions by Fred Espenak, NASA's GSFC”.
- `nasa_SEdata_07900716.html` – elementy Bessela i okoliczności największego zaćmienia. Strona
  https://eclipse.gsfc.nasa.gov/SEsearch/SEdata.php?Ecl=07900716 16.11.2026 zwracała błąd serwera, więc plik pochodzi
  z kopii w Wayback Machine z 10.09.2023: https://web.archive.org/web/20230910161808/https://eclipse.gsfc.nasa.gov/SEsearch/SEdata.php?Ecl=07900716
- `nasa_SEsearchmap_07900716.html` – strona mapy tego zaćmienia (kopia Wayback z 10.09.2023,
  https://web.archive.org/web/20230910162047/https://eclipse.gsfc.nasa.gov/SEsearch/SEsearchmap.php?Ecl=07900716).
  W kodzie strony są te same elementy Bessela (tablica `elements`) i punkty toru policzone przez NASA co 0,5° długości:
  granica północna, południowa i linia środkowa (`polylineN`, `polylineS`, `polylineC`). Czyta je `zacmienie-slonca/bessel.py`.
- `nasa_5MCSE_mapa_0790-07-16.gif` – mapka zaćmienia z katalogu, https://eclipse.gsfc.nasa.gov/5MCSEmap/0701-0800/790-07-16.gif
- `horizons/horizons_*.txt` – położenia Słońca (10), Księżyca (301), Merkurego (199), Wenus (299) oraz układów Marsa (4),
  Jowisza (5) i Saturna (6) widziane ze środka Ziemi 16 VII 790 o 20:29:30 TT, z systemu JPL Horizons (efemeryda DE441),
  https://ssd.jpl.nasa.gov/api/horizons.api, pobrane 16.11.2026. Domena publiczna (NASA/JPL).
Używa: `zacmienie-slonca`.

## zacmienie-1991/
Dane NASA o zaćmieniu z 11 lipca 1991 r., użyte tylko do sprawdzenia rachunku (`zacmienie-slonca/sprawdz.py`), bo dla
zaćmień z lat 1901–2100 NASA podaje gotową tabelę toru co minutę. Domena publiczna (Fred Espenak, NASA's GSFC). Pobrane 16.11.2026.
- `nasa_SE1991Jul11Tbeselm.html` – https://eclipse.gsfc.nasa.gov/SEbeselm/SEbeselm1951/SE1991Jul11Tbeselm.html
- `nasa_SE1991Jul11Tpath.html` – https://eclipse.gsfc.nasa.gov/SEpath/SEpath1951/SE1991Jul11Tpath.html

## ksiezyc/lroc_color_poles_4k.jpg
Mapa barwna Księżyca z sondy Lunar Reconnaissance Orbiter (kamera LROC WAC), z zestawu „CGI Moon Kit”
(NASA Scientific Visualization Studio, Ernie Wright, 2019), https://svs.gsfc.nasa.gov/4720 . Domena publiczna (dzieło NASA).
Pobrane 16.11.2026: https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_4k.tif (4096×2048), zapisane jako JPG.
Odwzorowanie walcowe równoodległościowe, środek obrazu = 0° długości (środek strony widocznej z Ziemi), góra = biegun północny.
Używa: `zacmienie-slonca`.

## blue-marble/bmng-200407-*.jpg
NASA Blue Marble Next Generation, lipiec 2004, wersja z rzeźbą terenu i dna morza („topography and bathymetry”;
Reto Stöckli, NASA Earth Observatory). Domena publiczna (dzieło NASA). Pobrane 16.11.2026 z
https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/bmng-topography-bathymetry/july/ :
- `bmng-200407-8192x4096.jpg` – cały glob, zmniejszony z `world.topo.bathy.200407.3x21600x10800.jpg`;
- `bmng-200407-ameryka-srodkowa-114W-78W-4N-28N.jpg` – wycinek 114°W–78°W, 4°N–28°N w pełnej rozdzielczości 500 m
  (8640×5760 px, 240 px na stopień), złożony z kafli `...3x21600x21600.A1.jpg` i `B1.jpg`.
Odwzorowanie walcowe równoodległościowe. Używa: `zacmienie-slonca` (zbliżenie nad Meksyk i Amerykę Środkową).

## korona/Solar_eclipse_1999_4.jpg
Fotografia korony Słońca podczas całkowitego zaćmienia 11 sierpnia 1999 r. (Francja). Autor: Luc Viatour (https://lucnix.be).
Licencja: CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/). Pobrane 16.11.2026 z Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Solar_eclipse_1999_4.jpg (oryginał 3543×3489, bez zmian).
Używa: `zacmienie-slonca` (ostatnie ujęcie; klip jest w tej części utworem zależnym na tej samej licencji, podpis autora jest w kadrze).
