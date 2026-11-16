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
