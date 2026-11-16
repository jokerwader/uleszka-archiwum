# tektonika-globus

Ożywiona mapa Leszka `zrodlo/webacja/02uskok/tektonika.gif` (rozdział 03 „Laik i trzęsienia Ziemi”). 16 s.

Podpis Leszka pod mapą: „Przypuszczalne granice płyt tektonicznych pokrywające się z rejonami sejsmicznymi
i tzw. gorące plamy”. Znaczenie znaków (z mapy i tekstu rozdziału 03):

- białe linie – przypuszczalne granice płyt (pokrywające się z rejonami sejsmicznymi),
- czerwone punkty – tzw. gorące plamy,
- pomarańczowe strzałki parami przy Grzbiecie Atlantyckim – „ocean Atlantycki rozszerza się od grzbietu
  środkowoatlantyckiego na zachód i wschód”,
- nazwy oceanów jak na mapie: PACYFIK (dwa razy, po obu brzegach mapy), ATLANTYK, INDYJSKI.

## Co widać

1. Płaska mapa w owalu z szarą obwódką, jak u Leszka (jego kolory: lądy #80C325, morze #75C3F3, napisy #0578C3).
2. Kolejno: rysują się granice płyt (od Atlantyku na boki), pojawiają się gorące plamy, potem strzałki.
3. Mapa zwija się w globus, globus obraca się do Atlantyku (ostatnia klatka: Grzbiet Atlantycki ze strzałkami).

## Jak to zrobiono

- Mapa Leszka jest w odwzorowaniu Mollweidego. Dopasowałem je do lądów Natural Earth (zgodność 83 %):
  środek owalu 298,153 px, półosie 289 i 142 px, południk środkowy 8°E.
- Linie, punkty, strzałki i napisy odczytane z pikseli rysunku (kolor), linie zwężone do osi (szkieletyzacja),
  wszystko przeliczone na współrzędne geograficzne i narysowane na nowo na kuli. Lądy pod spodem z Natural Earth.
- Zwijanie: siatka z dwoma kształtami (płaska mapa Mollweidego i kula), płynne przejście między nimi.
- Punkty i strzałki są nieco mniejsze niż na rysunku, żeby na globusie nie zasłaniały lądów.
  Na płaskiej mapie punkty są lekko owalne (to zniekształcenie odwzorowania).

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Mapa: Leszek Klimek, uleszka.net (materiał archiwum).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tektonika-globus/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tektonika-globus/scena.py -- --proba 60,175,250,400
```

## Render (16.11.2026)

EEVEE, 32 próbki, 400 klatek: 191 s. Uwaga: w Cycles płaska mapa (siatka z kształtem „Mapa”) renderuje się w poziome paski – ten klip renderować tylko w EEVEE.
