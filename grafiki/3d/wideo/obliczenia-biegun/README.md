# obliczenia-biegun

Ożywiony rysunek Leszka `zrodlo/webacja/02uskok/obliczenia.jpg` i jego tabela z rozdziału 10
„Co wyszło z obliczeń?” (tło: rozdział 09 „Jak to wygląda w praktyce?”). 16 s.

## Co widać

1. Trójkąt sferyczny z rysunku Leszka: A – poprzedni biegun (okolice wyspy Akpatok, 60,00°N 70,00°W według
   tabeli), B – biegun dzisiejszy, C – budowla (tu Teotihuacan). Boki a (B–C), c (A–B) białe, bok b (C–A) złoty;
   łuczek przy C to kąt między dzisiejszą północą a kierunkiem na Akpatok (Leszek liczył go wzorem z rysunku).
2. Z kolejnych budowli z tabeli wychodzą złote łuki ich „dawnej północy” (koła wielkie do Akpatok) i zbiegają się
   przy Akpatok: Teotihuacan, Monte Alban, Palenque, Tikal, Machu Picchu, Tiahuanaco, Giza.
3. Przy nazwach liczby z tabeli Leszka: kąt zmierzony | kąt obliczony („?” – Leszek nie podał pomiaru).
   Legenda w prawym górnym rogu.

| Miejsce | zmierzony | obliczony (Leszek) | azymut na Akpatok z prawdziwych współrzędnych |
|---|---|---|---|
| Teotihuacan | 18° | 19° | 19,9° E |
| Monte Alban | ? | 23° | 17,9° E |
| Palenque | 15° | 19° | 15,3° E |
| Tikal | ? | 15,5° | 13,7° E |
| Machu Picchu | 1,5° | 2° | 1,3° E |
| Tiahuanaco | 1,5° | 2° | 0,7° W |
| Giza | 20° | 24° | 31,6° W |

## Uwagi

- Miejsca leżą na globusie w prawdziwych współrzędnych. W tabeli Leszka część współrzędnych jest błędna
  (np. Tiahuanaco 26,93°S, Machu Picchu 27,14°S zamiast ok. 16,5°S i 13,2°S; sam pisze, że brał je z atlasu
  i nie wszystkie zdołał odczytać), więc rysowanie ich wprost przeniosłoby budowle w złe miejsca.
- Na ekranie są liczby z tabeli Leszka, a łuki są geometrycznie dokładne. Kierunki łuków zgadzają się z jego
  wynikami w granicach kilku stopni (tabela wyżej), poza Gizą (31,6° wobec jego 24°).
- Pominąłem Tulę, Villahermosę i Uxmal (są w tabeli tylko z kątem obliczonym): przy tej wielkości globusa
  podpisy w Meksyku zlewałyby się. Abydos i Sakkara nie mają w tabeli liczb.

## Sprawdzenie (audyt 16.11.2026)

Azymuty z ostatniej kolumny tabeli przeliczono od nowa wzorem na azymut koła wielkiego ze współrzędnych wpisanych
w `scena.py`: 19,9°; 17,9°; 15,3°; 13,7°; 1,3° na wschód; 0,7° i 31,6° na zachód. Zgadzają się.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Rysunek i tabela: Leszek Klimek, uleszka.net (materiał archiwum).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/obliczenia-biegun/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/obliczenia-biegun/scena.py -- --proba 110,400
```

## Render (16.11.2026)

Cycles na procesorze, 10 próbek, 400 klatek: 1463 s (ok. 24 min; karta była zajęta).
