# poslizg-skorupy

Poślizg twardej litosfery po półpłynnym płaszczu na głębokości 400–600 km. Rozdział 03 „Laik i trzęsienia Ziemi”.
20 s. Rodzaj: `hipoteza`.

Tekst Leszka: „Jak wiadomo, na pewnej głębokości skorupa Ziemi przechodzi stopniowo w półpłynny płaszcz i zapewne
gdzieś w tym miejscu, na głębokości 400-600 km, traci swą »przyczepność«. To w tym miejscu może dochodzić do
»poślizgu« twardej litosfery na półpłynnym płaszczu.”

## Co widać

1. Ziemia z wyciętą ćwiartką. Warstwy w skali: twarda skorupa (litosfera) – złota strefa 400–600 km – półpłynny
   płaszcz – jądro zewnętrzne (do 3480 km od środka) – jądro wewnętrzne (do 1220 km). Podpisy z kreskami.
2. Kamera zbliża się do brzegu przekroju: powierzchnia u góry, głębokość w dół. Podziałka 0 / 400 / 600 km,
   złoty pas „strefa poślizgu 400–600 km” i jasna linia granicy w jej środku (500 km).
3. Skorupa razem z lądami przesuwa się skokami (zatrzymuje się i rusza, jak przy poślizgu), a płaszcz pod nią stoi:
   ciemne kreski skorupy jadą, kreski płaszcza zostają w miejscu. Złota strzałka „skorupa ślizga się po płaszczu”.
4. Kamera wraca do całej Ziemi; lądy są już przesunięte (łącznie o 12°).

## Wierność tekstowi i zastrzeżenia

- Głębokość poślizgu jest **według tekstu** (400–600 km). W klipie granica ruchomej powłoki leży w połowie tej strefy.
- To ilustracja hipotezy (rodzaj `hipoteza`), nie opis nauki. Według dzisiejszej geologii litosfera ma zwykle
  ok. 100 km grubości i to pod nią (w astenosferze, ok. 100–250 km) skały są najbardziej plastyczne; płyty przesuwają się
  osobno, a nie cała skorupa naraz. Klip nie pokazuje tych liczb, żeby nie mieszać ich z tekstem Leszka.
- Grubości jądra i płaszcza są prawdziwe (promień Ziemi 6371 km). Skorupa obraca się wokół osi poziomej
  (prostopadłej do przekroju), żeby ruch było widać w płaszczyźnie cięcia; ruch jest przesadzony dla czytelności.
- Jak to zrobiono: bryły są nieruchome (kula obrócona wokół środka pokrywa się sama ze sobą), obracają się tylko wzory
  na skorupie (lądy, siatka, kreski) – dzięki temu przekrój zostaje ciągły.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Promienie warstw Ziemi: ogólnie znane wartości (model PREM): promień 6371 km, granica jądra zewnętrznego 3480 km,
  jądra wewnętrznego 1220 km.
- Geometria i wzory wykonane od zera w `scena.py`.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/poslizg-skorupy/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/poslizg-skorupy/scena.py -- --proba 60,240,500
```
