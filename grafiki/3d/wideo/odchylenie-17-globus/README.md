# odchylenie-17-globus

Ożywiony rysunek Leszka `zrodlo/webacja/02uskok/17std3.jpg`: dlaczego po przesunięciu bieguna budowle na Jukatanie
odchylają się od północy na północny wschód, a w Egipcie na północny zachód.
Rozdział 08 „Siedemnaście stopni Daenikena”. 16 s. Rodzaj: `rysunek-leszka`.

Tekst Leszka: „Przemieszczenie całej skorupy ziemskiej spowodowało przesunięcie się bieguna w nowe miejsce, dzisiejsze.
Spójrzmy na rysunek i zrozumiemy, że na Jukatanie musiało to spowodować przesunięcie się kierunków osi budowli
na północny wschód, natomiast w Europie i północnej Afryce w stronę odwrotną na północny zachód.”
Klip zaczyna się dwa zdania wcześniej („Muszę więc opierać się tylko na tej informacji…”), żeby czerwona strzałka
bieguna i podpisy trafiły w te słowa.

## Co widać (wszystko z rysunku)

1. Globus w kolorach rysunku (jasnoniebieskie morze, zielone lądy), zielony południk z żółtym kółkiem „70”,
   niebieski punkt „Titicaca”, czarny punkt „Akpatok”.
2. Żółte kwadraty „Jukatan” i „Egipt”; od każdego żółta linia przerywana do Akpatok (dawna północ).
3. Gruba czerwona strzałka od Akpatok do „Pn” (biegun przesuwa się na dzisiejsze miejsce).
4. Żółte linie ciągłe z grotami od kwadratów do „Pn” (dzisiejsza północ).
5. Małe czerwone strzałki kąta i podpisy „Odchylenie od północy na północny wschód” / „na północny zachód”.

Kamera przesuwa się znad Ameryki nad Atlantyk do widoku z rysunku i tam staje.

## Wierność rysunkowi i zastrzeżenia

- Rysunek Leszka jest odręczny; w klipie lądy pochodzą z prawdziwej mapy, więc położenia różnią się nieznacznie.
- Akpatok: 60°N 70°W, jak w tabeli Leszka z rozdziału „Co wyszło z obliczeń?”. Kwadraty: Jukatan 19,5°N 89,5°W,
  Egipt 27,5°N 31°E (środki kwadratów z rysunku, w przybliżeniu). Kwadraty są ustawione bokami według linii przerywanej.
- Linie to łuki kół wielkich. Z geometrii kuli wychodzi odchylenie ok. 14° na wschód dla Jukatanu i ok. 31° na zachód
  dla Egiptu. Klip nie pokazuje liczb, bo rysunek ich nie ma (liczby Leszka są w klipie `obliczenia-biegun`).
- To ilustracja hipotezy Leszka o przesunięciu bieguna, a nie ustalenie nauki; w kadrze znaczek
  „Według rysunku Leszka Klimka”.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Rysunek: Leszek Klimek, uleszka.net (archiwum). Kolory próbkowane z rysunku.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/odchylenie-17-globus/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/odchylenie-17-globus/scena.py -- --proba 1,120,250,400
```
