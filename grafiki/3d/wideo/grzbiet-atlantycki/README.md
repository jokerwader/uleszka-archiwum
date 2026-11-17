# grzbiet-atlantycki

Grzbiet Śródatlantycki jako „główny winowajca” trzęsień Ziemi. Rozdział 03 „Laik i trzęsienia Ziemi”,
zdanie „Za głównego winowajcę, odpowiedzialnego za trzęsienia Ziemi, uważam Grzbiet Atlantycki.” 20 s.
Rodzaj: `hipoteza` (znaczek „Hipoteza z tekstu, nie fakt” dodaje `wideo.ts`).

## Fakt i hipoteza

| W klipie | Status |
|---|---|
| Wzdłuż Atlantyku biegnie podwodny grzbiet, przy którym z wnętrza Ziemi wypływa magma | fakt naukowy |
| Dno Atlantyku rozsuwa się od grzbietu na zachód i wschód (nowe dno powstaje przy grzbiecie) | fakt naukowy (kilka cm na rok) |
| Pacyfik się kurczy | fakt naukowy (dno Pacyfiku zanurza się pod kontynenty na jego brzegach) |
| Grzbiet jest głównym „rozpychającym się łokciami” i **główną przyczyną trzęsień Ziemi** | hipoteza Leszka Klimka |

Nauka uznaje za główną przyczynę trzęsień ruchy i naprężenia na granicach wszystkich płyt (najsilniejsze trzęsienia
zdarzają się przy zanurzaniu płyt, np. wokół Pacyfiku), a nie samego grzbietu. Klip pokazuje fakty, na których
Leszek opiera swoją tezę; sama teza zostaje w tekście lektora i w znaczku „hipoteza”.

## Co widać

1. Globus od strony Atlantyku (kolory jak na rysunkach Leszka). Pomarańczowa linia grzbietu rysuje się z północy
   na południe, od Morza Norweskiego przez Islandię po okolice Wyspy Bouveta. Podpis „Grzbiet Śródatlantycki”.
2. Przy grzbiecie świeci pomarańczowa poświata – „wypływ magmy z wnętrza Ziemi”.
3. Po obu stronach grzbietu pojawiają się jasne pasy dna, które odsuwają się od niego symetrycznie, a złote strzałki
   wskazują ruch na zachód i wschód. Podpis „Atlantyk rozszerza się na zachód i wschód” (słowa z tekstu).
   Młodsze dno przy grzbiecie jest jaśniejsze.
4. Globus obraca się na Pacyfik; przy jego brzegach złote strzałki wskazują do środka oceanu – „Pacyfik kurczy się”.

To schemat: pasy dna mają umowną szerokość (co 4° od osi grzbietu), strzałki pokazują kierunek, nie prędkość.
Strzałki na Atlantyku biegną wzdłuż równoleżników (rozsuwanie jest w przybliżeniu wschód–zachód),
na Pacyfiku wskazują zwężanie się oceanu przy jego brzegach.

## Dane i licencje

- Oś grzbietu: 38 punktów odczytanych z ogólnodostępnych map batymetrycznych dna (przybliżenie do ok. 1°),
  zapisane w `scena.py` (lista `GRZBIET`). Fakt geograficzny, bez cudzej grafiki.
- Lądy: Natural Earth 1:10 mln i 1:50 mln, domena publiczna (`_dane/natural-earth/`).
- Obszar Atlantyku dla pasów dna: maska lądów Natural Earth przycięta prostymi regułami (bez Pacyfiku, Morza
  Karaibskiego, Zatoki Meksykańskiej, Morza Śródziemnego, Bałtyku i Zatoki Hudsona).

## Sprawdzenie (audyt 16.11.2026)

38 punktów osi grzbietu porównano z granicami płyt PB2002 (P. Bird, „An updated digital model of plate boundaries”,
Geochemistry Geophysics Geosystems 4(3), 2003; granice Ameryka Płn.–Eurazja, Ameryka Płn.–Afryka, Afryka–Ameryka Płd.).
Średnia odległość punktu od granicy to 0,31° (34 km), największa 1,2° (131 km, ostatni punkt przy Wyspie Bouveta).
To się mieści w podanej wyżej dokładności ok. 1°; na globusie w kadrze 1° to kilka pikseli. Linia w klipie jest
wygładzona: nie pokazuje uskoków transformacyjnych, które przesuwają oś grzbietu (np. przy równiku).
Prędkość rozsuwania Atlantyku to ok. 2–2,5 cm na rok w północnej części i do ok. 3,5 cm w południowej (obie strony razem).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/grzbiet-atlantycki/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/grzbiet-atlantycki/scena.py -- --proba 150,290,500
```
