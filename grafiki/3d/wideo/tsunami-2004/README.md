# tsunami-2004

Tsunami po trzęsieniu ziemi z 26 grudnia 2004 r. (Sumatra–Andamany, Mw 9,1) rozchodzi się po oceanie Indyjskim.
Rozdział 13 „Czy możemy spać spokojnie?”, zdanie „Czy po wydarzeniach z 26 grudnia 2004 r. w rejonie oceanu
Indyjskiego…”. 20 s. Rodzaj: `ilustracja` (zjawisko prawdziwe). Spokojny schemat, bez ludzi i bez zniszczeń.

## Co widać

1. Globus od strony Sumatry, czerwona kropka ogniska i podpis „Ognisko trzęsienia, 26.12.2004, 00:58 UTC”.
2. Zegar w prawym górnym rogu liczy czas od trzęsienia (do +12 h 30 min). Jasne czoło fali rozchodzi się po oceanie,
   za nim zostają cienkie linie co godzinę (jak na mapach czasu przejścia fali), obszar, do którego fala dotarła, jaśnieje.
3. Kamera powoli się oddala, aż widać cały ocean od Afryki po Australię.
4. Złote punkty na wybrzeżach zapalają się w **zmierzonym** czasie dotarcia fali, z podpisem (np. „Kolombo 2:50”):
   Phuket 1:56, Ćennaj 2:34, Kolombo 2:50, Male 3:15, Perth (Hillarys) 6:23, Port Louis 6:47, Salala 7:09,
   Lamu 8:53, Port Elizabeth 12:13.

## Fakty i model – co jest czym

- **Punkty i ich czasy** to pomiary mareografów z bazy NOAA NCEI (domena publiczna), bez zmian. Sprawdzone ponownie
  16.11.2026 przez API bazy: wszystkie 9 czasów i współrzędnych zgadza się co do minuty.
- **Czoło fali i linie godzinowe** to model policzony na prawdziwej głębokości oceanu, nie zapis rzeczywistej fali.
  Prędkość fali długiej v = √(g·h), głębokość h z modelu rzeźby dna ETOPO1 (NOAA) na siatce 5 minut kątowych
  (ok. 9 km). Czas dojścia to najkrótszy czas po wodzie (algorytm Dijkstry, 16 kierunków).
- Źródło fali: strefa zerwania uskoku, ok. 1300 km od okolic ogniska do 14°N (Lay i in., „The Great Sumatra-Andaman
  Earthquake of 26 December 2004”, Science 308, 2005). W modelu to linia 0,8° na wschód od osi rowu oceanicznego
  (oś rowu z granic płyt PB2002, P. Bird 2003), bo dno podniosło się między rowem a wyspami. Zerwanie biegło na północ
  ok. 2,5 km/s, więc północny koniec źródła rusza ok. 9 minut po ognisku.
- Model **nie jest do niczego dopasowywany**. Porównanie z pomiarami w punktach klipu (model minus pomiar):
  Kolombo 0 min, Salala −1, Ćennaj +5, Port Louis −7, Lamu −12, Male +13, Perth (Hillarys) −20, Phuket +28,
  Port Elizabeth −35. Dla wszystkich 96 mareografów z bazy NOAA leżących w obszarze modelu mediana różnicy to 26 minut.
  Różnice biorą się głównie z płytkich wód przy brzegu i w portach, których siatka 9 km nie oddaje.
  Punkty pokazują pomiar, nie model, więc mogą się zapalać nieco przed czołem fali albo po nim.
- Poprawka z 16.11.2026 (audyt): wcześniej głębokość była zgadywana z odległości od brzegu i dobierana tak, żeby model
  pasował do pomiarów; w Phukecie dawał 0:58 przy zmierzonym 1:56.
- Linie co godzinę mają od 0 h do 12 h; liczby godzin nie są podpisane, czas pokazuje zegar.

## Dane i licencje

- Czasy dotarcia: NOAA National Centers for Environmental Information, Global Historical Tsunami Database,
  zdarzenie nr 2439 (26.12.2004), pola `travHours`/`travMins` (rodzaj pomiaru: mareograf). Pobrane 16.11.2026 z
  https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/runups?tsunamiEventId=2439 . Domena publiczna
  (dzieło rządu USA). Wybrane rekordy w `dane_noaa.csv`.
- Ognisko: ta sama baza (3,295°N 95,982°E, 00:58:53 UTC).
- Głębokość oceanu: ETOPO1 (C. Amante, B. W. Eakins, NOAA 2009), domena publiczna, wycinek w
  `_dane/etopo/etopo1_ocean_indyjski_5min.npz` (opis w `_dane/ZRODLA.md`).
- Oś rowu Sundajskiego: P. Bird, „An updated digital model of plate boundaries”, Geochemistry Geophysics Geosystems 4(3),
  2003 (PB2002), współrzędne wpisane w `scena.py`.
- Lądy na globusie: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Polskie nazwy miejsc: Ćennaj (Chennai), Kolombo, Male, Salala (Salalah).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tsunami-2004/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tsunami-2004/scena.py -- --proba 60,330,500
```

Pierwsze uruchomienie liczy pole czasu przejścia (ok. 1,5 min, zapis w `%TEMP%\uskok3d_cache\tsunami2004_T_etopo1_v1.npz`).
Skrypt wypisuje porównanie modelu z pomiarami (`[tsunami] …`). Plik `dane_noaa.csv` to wyciąg 17 rekordów NOAA
(do wglądu; model z niego nie korzysta).
