# lod-przy-biegunie

Ilustracja słów Einsteina cytowanych w rozdziale 02 („Charles Hapgood i jego hipoteza”) – hipoteza Hapgooda. 16 s.
Rodzaj: `hipoteza` – klip łączy kilka rysunków Leszka i dodaje ruch, którego na rysunkach nie ma.

> „W strefie polarnej trwa nieustanne nawarstwianie się lodu, występujące nierównomiernie wokół bieguna.
> Rotacja Ziemi oddziałuje na tę masę lodu, wytwarzając moment odśrodkowy, który przenosi się na twardą
> skorupę naszej planety. Siła ta, osiągnąwszy pewną wartość, powoduje przesuwanie skorupy ziemskiej”.

## Co widać

1. Globus ustawiony jak przed uskokiem: nieruchoma oś N–S (jak na `masy1.jpg`) przechodzi przez okolicę wyspy
   Akpatok (czerwona kropka, 60°N 70°W według tabeli Leszka). Ziemia powoli się obraca.
2. Lód narasta nierównomiernie wokół bieguna (biała, wypukła czapa) aż do zasięgu z mapy `lodowiec.gif`
   („największy zasięg zlodowaceń”, której Leszek używa w tym rozdziale).
3. Czerwone strzałki (styl `masy1.jpg` / `masy3.jpg`): siła odśrodkowa działająca na masy lodu, skierowana od osi,
   i gruba strzałka wypadkowej z podpisem „moment odśrodkowy”.
4. Skorupa razem z lodem obraca się o kilka stopni względem nieruchomej osi (niebieski łuk ze strzałką jak na
   `masy3.jpg`, podpis „przesuwanie skorupy ziemskiej”).

## Jak to zrobiono i co jest umowne

- Zasięg lodu: piksele koloru „Ice sheet or glacier” z `lodowiec.gif`, przeliczone z odwzorowania Robinsona
  (dopasowanego do lądów: środek 250,127 px, R = 93 px) na kulę; tylko półkula północna powyżej 35°N.
- Grubość lodu jest umowna (przesadzona, żeby było widać „masę”), kolejność narastania: od Akpatok na zewnątrz z szumem.
- Kierunek wypadkowej i przesuwania przyjęto tak jak w tekście i w klipie `uskok-globus`: skorupa rusza
  „w kierunku południowym wzdłuż 70° zachodniego południka”. Lód po tej stronie jest w klipie nieco grubszy,
  żeby nierównomierność była widoczna. To ilustracja mechanizmu, nie obliczenie: środek masy samego zasięgu
  z mapy wypada bliżej dzisiejszego bieguna (ok. 80°N 69°W).
- Przesunięcie w klipie to tylko początek ruchu (8°), nie całe 30°.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Zasięg lodu odczytany z mapy `lodowiec.gif` z artykułu Leszka (sama mapa nie jest wstawiana do klipu).
- Rysunki `masy1.jpg`, `masy3.jpg`: Leszek Klimek, uleszka.net (wzór stylu strzałek).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/lod-przy-biegunie/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/lod-przy-biegunie/scena.py -- --proba 150,260,400
```

## Render (16.11.2026)

Cycles na procesorze, 10 próbek, 400 klatek: 1498 s (ok. 25 min; karta była zajęta).
