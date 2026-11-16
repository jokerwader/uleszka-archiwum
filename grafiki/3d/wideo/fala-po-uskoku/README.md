# fala-po-uskoku

Schemat ogólnoświatowej fali po „wielkim uskoku” – ilustracja hipotezy z tekstu (rozdziały 02, 05–07). 16 s.
Rodzaj: `hipoteza` (nauka tego nie potwierdza).

## Na czym się opiera

- Rozdz. 02: „Najpierw bezwładnie przesunęły się w kierunku południowym, a następnie gigantycznym tsunami
  ruszyły z powrotem.”, „Fala o wysokości kilku kilometrów (…) spłukiwała wszystko co stanęło na jej drodze.”
- Rozdz. 05: opisy „ziemia kilkakrotnie zapadała się pod wodę i wynurzała się” jako następujące po sobie fale tsunami.
- Rozdz. 06–07, 09: tsunami przetaczające się przez lądy (Jukatan, Andy), zasypujące ruiny osadami,
  zostawiające wodę uwięzioną w głębi lądów.

## Co widać

1. Spokojny globus (obie Ameryki), potem jasne pasy i białe szewrony na oceanach przesuwają się na południe
   (woda „bezwładnie” zostaje w tyle).
2. Wraca jasny grzbiet fali, biegnie po oceanach na północ; za nim pas zalanych wybrzeży (jasnoniebieski) –
   zasięg zależy od odległości od brzegu (do ok. 6° w głąb lądu, z szumem), Jukatan i Floryda znikają pod wodą.
3. Globus obraca się z Ameryk na Atlantyk; na końcu woda częściowo spływa, zostaje jaśniejszy pas wybrzeży.

To schemat w płaskich kolorach rysunków Leszka (zielone lądy, niebieskie morze), nie symulacja: wysokość terenu
nie jest brana pod uwagę, kształt i prędkość fali są umowne.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Odległość od brzegu policzona z tej samej maski lądów (erozja w numpy).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py -- --proba 100,250,400
```

## Render (16.11.2026)

Cycles na procesorze, 10 próbek, 400 klatek: 1473 s (ok. 25 min; karta była zajęta).
