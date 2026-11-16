# wenus-pozycja

Ilustracja **twierdzenia cytowanego autora** do rozdziału 13 „Czy możemy spać spokojnie?”: Bogusław Jeff Leng pisze,
że Wenus „zmierza nieubłaganie ku swojej pozycji, identycznej, jaką miała w tym układzie w roku 9792 pne” i zajmie ją
„po okresie 11 804 lat od dnia 27 lipca 9792 roku pne” – 22–23 grudnia 2012 r. 14 s.

Rodzaj: `hipoteza`. Najmniej ważny klip serii, celowo prosty.

## Co widać

1. Widok z ukosa na Słońce, orbitę Wenus (złota) i orbitę Ziemi (niebieska). Wokół złote napisy gwiazdozbiorów
   Zodiaku (kierunki widziane ze Słońca, przybliżone środki gwiazdozbiorów na ekliptyce). Wenus stoi w złotym
   znaczniku, linia ze Słońca wskazuje kierunek (Waga). U góry „27 lipca 9792 p.n.e.” i „pozycja Wenus według B. J. Lenga”.
2. Licznik lat biegnie do 2012 r. Wenus robi w tym czasie ok. 19 200 okrążeń, więc przy dużej prędkości widać tylko
   rozjarzoną orbitę (napis „11 804 lata – ok. 19 200 okrążeń Wenus”). Pod koniec Wenus zwalnia, pojawia się Ziemia.
3. Koniec: „22 grudnia 2012”, Wenus z powrotem w znaczniku, Ziemia na swojej pozycji z tego dnia.

## Co jest policzone, a co jest twierdzeniem autora

- Położenia na końcu klipu (22 grudnia 2012) są policzone ze średnich elementów orbit (J2000, E. M. Standish, JPL):
  długość heliocentryczna Wenus ok. 213,7°, Ziemi ok. 90,8° (Ziemia „w Bliźniętach” widziana ze Słońca = przesilenie zimowe).
  Orbity narysowane jako okręgi (mimośrody Wenus i Ziemi są bardzo małe).
- To, że Wenus stała w tym samym miejscu 27 lipca 9792 r. p.n.e., jest **tylko twierdzeniem autora**. Ten sam prosty
  rachunek (kalendarz juliański proleptyczny, rok astronomiczny −9791) daje dla tamtego dnia długość heliocentryczną Wenus
  ok. 101° (a nie 214°), a widzianą z Ziemi ok. 170° (Lew/Panna; w 2012: ok. 247°, Wężownik/Strzelec). Rachunek na
  średnich elementach jest przybliżony, ale różnica ponad 100° jest dużo większa niż jego błąd.
  Klip pokazuje twierdzenie autora (start i koniec w znaczniku, całkowita liczba okrążeń), a ten wynik zapisujemy tutaj.
- Gwiazdozbiory: przybliżone kierunki ich środków na ekliptyce (wiedza ogólna), tylko jako tło.

## Dane i licencje

- Bez danych zewnętrznych: elementy orbit to stałe liczbowe wpisane w skrypt.
- Czcionki napisów: Georgia, Arial (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wenus-pozycja/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wenus-pozycja/scena.py -- --proba 1,180,270,350
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 350 klatek: 161 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
