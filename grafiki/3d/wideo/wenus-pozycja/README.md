# wenus-pozycja

Ilustracja **twierdzenia cytowanego autora** do rozdziału 13 „Czy możemy spać spokojnie?”: Bogusław Jeff Leng pisze,
że Wenus „zmierza nieubłaganie ku swojej pozycji, identycznej, jaką miała w tym układzie w roku 9792 pne” i zajmie ją
„po okresie 11 804 lat od dnia 27 lipca 9792 roku pne” – 22–23 grudnia 2012 r. 14 s.

Rodzaj: `hipoteza`. Najmniej ważny klip serii, celowo prosty.

## Co widać

1. Widok z ukosa na Słońce, orbitę Wenus (złota) i orbitę Ziemi (niebieska). Wokół przerywane koło ekliptyki
   z kreskami na granicach gwiazdozbiorów i ich nazwami (kierunki widziane ze Słońca; 13 gwiazdozbiorów, bo ekliptyka
   przechodzi też przez Wężownika). Wenus stoi w złotym znaczniku, linia ze Słońca wskazuje kierunek: Panna,
   3° przed granicą Wagi. U góry „27 lipca 9792 p.n.e.” i „pozycja Wenus według B. J. Lenga”.
2. Licznik lat biegnie do 2012 r. Wenus robi w tym czasie ok. 19 200 okrążeń, więc przy dużej prędkości widać tylko
   rozjarzoną orbitę (napis „11 804 lata – ok. 19 200 okrążeń Wenus”). Pod koniec Wenus zwalnia, pojawia się Ziemia.
3. Koniec: „22 grudnia 2012”, Wenus z powrotem w znaczniku, Ziemia na swojej pozycji z tego dnia.

## Co jest policzone, a co jest twierdzeniem autora

- Położenia na końcu klipu (22 grudnia 2012, 0h) są policzone z elementów orbit E. M. Standisha (JPL, „Approximate
  Positions of the Planets”) i równania Keplera (`_wspolne/niebo.py`): długość heliocentryczna Wenus 214,49°, Ziemi 90,36°
  (ekliptyka J2000). Kontrola w efemerydzie JPL Horizons (DE441): Wenus 214,50°, Ziemia 90,36°.
  Orbity są elipsami o prawdziwych mimośrodach (Wenus 0,0068, Ziemia 0,0167) i kierunkach peryhelium; nachylenie orbity
  Wenus (3,4°) pominięto.
- To, że Wenus stała w tym samym miejscu 27 lipca 9792 r. p.n.e., jest **tylko twierdzeniem autora** i się nie potwierdza.
  JPL Horizons (DE441, kalendarz juliański proleptyczny) daje dla tamtego dnia długość heliocentryczną Wenus 98,7°
  (Bliźnięta), a nie 214,5°; widziana z Ziemi stała na 167,5° (Lew), a 22 grudnia 2012 r. na 247,1° (Skorpion, przy
  granicy Wężownika). Liczone względem gwiazd (ekliptyka J2000); względem punktu Barana tamtej epoki różnica jest
  jeszcze inna (precesja przesuwa go o ok. 164°). Elementy Standisha dają to samo co DE441 z dokładnością do 0,2°.
  Między datami mija 11 803,4 roku juliańskiego (autor podaje 11 804), czyli 19 186,3 okrążenia Wenus.
  Klip pokazuje twierdzenie autora (start i koniec w znaczniku, całkowita liczba okrążeń), a wynik rachunku jest tutaj.
- Granice gwiazdozbiorów na ekliptyce policzone z wielokątów granic IAU (E. Delporte 1930; plik
  `constellations.bounds.json` projektu d3-celestial): Ryby 351,64°–28,69°, Baran do 53,42°, Byk do 90,15°, Bliźnięta
  do 117,99°, Rak do 138,05°, Lew do 173,86°, Panna do 217,82°, Waga do 241,05°, Skorpion do 247,64°, Wężownik do
  266,25°, Strzelec do 299,67°, Koziorożec do 327,49°, Wodnik do 351,64° (długość ekliptyczna J2000).
- Poprawka z 16.11.2026 (audyt): wcześniej nazwy gwiazdozbiorów stały w miejscach wpisanych z pamięci (błąd 4–10°,
  bez Wężownika), a planety według długości średniej (Wenus 213,7°, Ziemia 90,8°), nie prawdziwej.

## Dane i licencje

- Bez plików zewnętrznych: elementy orbit (`_wspolne/niebo.py`) i granice gwiazdozbiorów to stałe liczbowe w skryptach.
  Efemeryda kontrolna: JPL Horizons, https://ssd.jpl.nasa.gov/horizons/ (NASA, domena publiczna).
- Czcionki napisów: Georgia, Arial (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wenus-pozycja/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wenus-pozycja/scena.py -- --proba 1,180,270,350
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 350 klatek: 161 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
