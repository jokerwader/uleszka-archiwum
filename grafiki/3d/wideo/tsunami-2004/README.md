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

- **Punkty i ich czasy** to pomiary mareografów z bazy NOAA NCEI (domena publiczna), bez zmian.
- **Czoło fali i linie godzinowe** to przybliżony model, nie zapis rzeczywistej fali. Prędkość fali na płytkiej wodzie
  v = √(g·h); głębokość h szacowana z odległości od brzegu (50 m przy brzegu, 4000 m od ok. 230 km),
  płycej na Morzu Andamańskim (700 m) i w Zatoce Bengalskiej (2300 m). Droga tylko po wodzie (algorytm Dijkstry
  na siatce 0,25°, 16 kierunków). Źródłem fali jest cały pas zerwania uskoku (ok. 1300 km od 3,3°N 95,9°E do 14°N 92,9°E).
- Model dopasowano do 17 pomiarów NOAA (plik `dane_noaa.csv`): średni błąd bezwzględny 21 min (RMS 26 min).
  Daleko od ogniska zgadza się dobrze (Lamu: model 8:50, pomiar 8:53; Port Elizabeth: 12:08 i 12:13; Kolombo: 3:01 i 2:50),
  przy samym ognisku gorzej: w Phukecie model daje 0:58, a mareograf zanotował 1:56 (płytkie wody przy Tajlandii są
  w modelu tylko zgrubnie). Dlatego punkt Phuketu zapala się wyraźnie
  po przejściu czoła fali – tak jest uczciwie: punkty pokazują pomiar, nie model.
- Linie co godzinę mają od 0 h do 12 h; liczby godzin nie są podpisane, czas pokazuje zegar.

## Dane i licencje

- Czasy dotarcia: NOAA National Centers for Environmental Information, Global Historical Tsunami Database,
  zdarzenie nr 2439 (26.12.2004), pola `travHours`/`travMins` (rodzaj pomiaru: mareograf). Pobrane 16.11.2026 z
  https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/runups?tsunamiEventId=2439 . Domena publiczna
  (dzieło rządu USA). Wybrane rekordy w `dane_noaa.csv`.
- Ognisko: ta sama baza (3,295°N 95,982°E, 00:58:53 UTC).
- Lądy: Natural Earth 1:50 mln (model) i 1:10 mln (globus), domena publiczna (`_dane/natural-earth/`).
- Polskie nazwy miejsc: Ćennaj (Chennai), Kolombo, Male, Salala (Salalah).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tsunami-2004/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tsunami-2004/scena.py -- --proba 60,330,500
```

Pierwsze uruchomienie liczy pole czasu przejścia (ok. 1 min, zapis w `%TEMP%\uskok3d_cache\tsunami2004_T.npy`).
