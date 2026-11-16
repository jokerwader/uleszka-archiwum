# uskok-globus

Ożywiony rysunek Leszka `zrodlo/webacja/02uskok/uskok.jpg` (rozdział 02 „Charles Hapgood i jego hipoteza”). 15 s.

## Co widać

1. Globus w stanie sprzed ok. 12 000 lat: na osi obrotu leży okolica wyspy Akpatok (czerwona kropka,
   60°N 70°W według tabeli Leszka), wokół niej czapa lodowa i kreskowana siatka tamtego bieguna,
   „Równik sprzed 12000 lat” jest wtedy równikiem.
2. Rośnie czerwona strzałka „Kierunek przesunięcia skorupy ziemskiej”.
3. Skorupa przesuwa się o 30° w kierunku strzałki (obrót wokół osi leżącej w płaszczyźnie równika,
   prostopadłej do południka 70°W, czyli tak jak w tekście: „na południe wzdłuż 70° zachodniego południka”).
   Oś obrotu stoi w miejscu: Akpatok odjeżdża, na oś wjeżdża dzisiejszy biegun (czarna kropka),
   równik sprzed 12 000 lat jedzie razem ze skorupą, pojawia się ciągła siatka i równik dzisiejszy.
4. Ostatnia klatka odpowiada rysunkowi Leszka, z jego podpisami: „Położenie poprzedniego bieguna
   północnego”, „Położenie dzisiejszego bieguna północnego”, „Kierunek przesunięcia skorupy ziemskiej”,
   „Równik sprzed 12000 lat”, „Równik dzisiejszy”.

## Jak to zrobiono

- Rysunek Leszka to nie zwykły widok kuli, tylko rzut azymutalny (na jednej tarczy widać oba bieguny,
  Afrykę i Australię). Dopasowałem rzut azymutalny równoodległy do 5 punktów rysunku (oba bieguny,
  Przylądek Igielny, południe Madagaskaru, południe Indii): środek 48°N 34°E, brzeg tarczy 104° od środka.
  Średni błąd dopasowania ok. 14 px na rysunku 350 px – rysunek jest odręczny, więc kontury lądów
  różnią się od rysunku szczegółami, układ jest ten sam.
- Kopuła (półkula) z cieniowaniem; obraz na niej liczy shader: dla każdego punktu tarczy rzut odwrotny,
  potem obrót skorupy i odczyt mapy lądów. Dzięki temu skorupa „jedzie” płynnie, a oś stoi.
- Czerwona strzałka i obszar lodu są odczytane z pikseli rysunku (kolor), strzałka w układzie tarczy,
  lód przeliczony na współrzędne geograficzne (jedzie ze skorupą). Kolory próbkowane z rysunku:
  lądy #028F43, morze #00A2E9.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln (`_dane/natural-earth/ne_10m_land.geojson`, `ne_10m_lakes`), domena publiczna.
- Rysunek: Leszek Klimek, uleszka.net (materiał archiwum).
- Czcionka napisów: Arial Bold (systemowa).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/uskok-globus/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/uskok-globus/scena.py -- --proba 1,160,375
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`, `wezly.py`. Pliki pośrednie (maski, tekstury) w `%TEMP%\uskok3d_cache`.

## Render (16.11.2026)

Cycles na procesorze, 10 próbek, 375 klatek: 2128 s (ok. 35 min). Karta była wtedy w 100% zajęta przez inny program; w EEVEE ten sam kadr wygląda identycznie.
