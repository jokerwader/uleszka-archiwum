# giza-pas-oriona

Ilustracja **hipotezy** do rozdziału 13 „Czy możemy spać spokojnie?”, przy cytacie (B. J. Leng) „Piramidy w Gizie
krzyczą o ruchach Oriona – obserwujcie Oriona, on niesie zagładę!”. 16 s.

Rodzaj: `hipoteza`. To tzw. korelacja Oriona Roberta Bauvala (1989–1994): trzy wielkie piramidy w Gizie miały być
ułożone jak trzy gwiazdy pasa Oriona. **Hipoteza jest sporna** – większość egiptologów i astronomów ją odrzuca
(m.in. dlatego, że trzeba odwrócić mapę nieba, a piramidy budowało kilku władców po kolei).

## Co widać

1. Nocny widok trzech piramid z ukosa od południowego wschodu (światło jak od Księżyca), podpisy Cheops, Chefren, Mykerinos.
2. Kamera unosi się nad piramidy (północ u góry). Nad nimi pojawiają się trzy gwiazdy pasa Oriona – Alnitak, Alnilam,
   Mintaka – w takim układzie, jak widać je z ziemi (północ u góry, wschód po lewej), w tej samej skali co dopasowanie.
3. Grupa gwiazd obraca się i ustawia nad piramidami: Alnitak nad Cheopsem, Alnilam nad Chefrenem, Mintaka nad Mykerinosem.
   Napisy u góry: „Pas Oriona nad piramidami w Gizie” i „mapa nieba obrócona o 165° (południe u góry), odchyłki do 14 m”.

## Dane i obliczenia (wszystko prawdziwe, nic nie dopasowane „na oko”)

- Środek Chefrena względem Cheopsa: 13 166 cali (334,4 m) na zachód i 13 931 cali (353,9 m) na południe – z pomiaru
  W. M. Flindersa Petriego, „The Pyramids and Temples of Gizeh” (1883, domena publiczna), wyliczone z jego odległości
  między bokami (za zestawieniem J. Legona) i długości boków (Cheops 9068,8 cala, Chefren 8474,9 cala).
- Mykerinos: odległość północ–południe od Chefrena też z Petriego (8856,1 cala między bokami + połowy boków = 385,3 m);
  odległość wschód–zachód z Wikidata (CC0, współrzędne Q208358 i Q238623): 254,6 m. Wynik zgadza się ze współrzędnymi
  z Wikipedii do ok. 30 m (tyle wynosi ich zaokrąglenie do 1″).
- Boki i wysokości: Cheops 230,3 m / 146,6 m, Chefren 215,3 m / 143,5 m, Mykerinos 104,6 × 102,2 m / 65,5 m.
  Piramidy ustawione dokładnie według stron świata (w rzeczywistości odchyłki rzędu minut kątowych). Pominięto małe
  piramidy królowych, świątynie i Sfinksa oraz to, że Chefren stoi ok. 10 m wyżej.
- Gwiazdy: katalog HYG v4.4 (`_dane/hyg/gwiazdy_mag6.csv`, CC BY-SA 4.0), położenia J2000, rzut gnomoniczny wokół Alnilama.
  Wielkość kul zależy od jasności gwiazdy. Ruch własny gwiazd i precesja nie zmieniają kształtu pasa w widocznym stopniu.
- Dopasowanie: obrót + skala + przesunięcie metodą najmniejszych kwadratów (bez odbicia lustrzanego). Wynik:
  obrót −165,4°, skala 345,5 m na stopień łuku, odchyłki 6,9 m (Cheops), 13,6 m (Chefren), 6,7 m (Mykerinos).
  Dla porównania: przy mapie nieba „z góry” (wschód po prawej) najlepszy obrót to 88° i odchyłki do 49 m.
  Skrypt wypisuje wynik dopasowania przy każdym uruchomieniu (`[dopasowanie] …`).

## Licencje

- Petrie 1883: domena publiczna. Wikidata: CC0. HYG: CC BY-SA 4.0 (podać w opisie filmu: „katalog gwiazd HYG, D. Nash, CC BY-SA 4.0”).
- Czcionki napisów: Georgia, Arial (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/giza-pas-oriona/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/giza-pas-oriona/scena.py -- --proba 1,150,230,400
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 400 klatek: 293 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
