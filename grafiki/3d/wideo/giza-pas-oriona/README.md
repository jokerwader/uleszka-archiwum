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
   Napisy u góry: „Pas Oriona nad piramidami w Gizie” i „mapa nieba obrócona o 165° (południe u góry), odchyłki do 18 m”.

## Dane i obliczenia (wszystko prawdziwe, nic nie dopasowane „na oko”)

- Położenia środków piramid: pomiar triangulacyjny W. M. Flindersa Petriego, „The Pyramids and Temples of Gizeh”
  (1883, domena publiczna), §92, tabela odległości środków (cale; pierwsza liczba północ–południe, druga wschód–zachód):
  Cheops–Chefren 13 931,6 i 13 165,8 (353,9 m na południe, 334,4 m na zachód); Cheops–Mykerinos 29 102,0 i 22 616,0
  (739,2 m i 574,4 m); Chefren–Mykerinos 15 170,4 i 9 450,2. Tekst sprawdzony 16.11.2026:
  http://www.ronaldbirdsall.com/gizeh/petrie/c13.html
- Poprawka z 16.11.2026 (audyt): wcześniej odległość wschód–zachód Chefren–Mykerinos pochodziła ze współrzędnych
  Wikidata (254,6 m, zaokrąglonych do 1″, czyli do ok. 30 m), a nie z Petriego (240,0 m). Mykerinos stał przez to
  14,6 m za daleko na zachód, a dopasowanie wychodziło za dobre (odchyłki do 14 m zamiast do 18 m).
- Boki i wysokości: Cheops 230,3 m / 146,6 m, Chefren 215,3 m / 143,5 m, Mykerinos 104,6 × 102,2 m / 65,5 m.
  Piramidy ustawione dokładnie według stron świata (w rzeczywistości odchyłki rzędu minut kątowych). Pominięto małe
  piramidy królowych, świątynie i Sfinksa oraz to, że Chefren stoi ok. 10 m wyżej.
- Gwiazdy: katalog HYG v4.4 (`_dane/hyg/gwiazdy_mag6.csv`, CC BY-SA 4.0), położenia J2000, rzut gnomoniczny wokół Alnilama.
  Wielkość kul zależy od jasności gwiazdy. Ruch własny gwiazd i precesja nie zmieniają kształtu pasa w widocznym stopniu.
- Dopasowanie: obrót + skala + przesunięcie metodą najmniejszych kwadratów (bez odbicia lustrzanego). Wynik:
  obrót −164,7°, skala 342,3 m na stopień łuku, odchyłki 9,1 m (Cheops), 18,0 m (Chefren), 8,9 m (Mykerinos).
  Dla porównania: przy mapie nieba „z góry” (wschód po prawej) najlepszy obrót to 89° i odchyłki do 54 m.
  Linia piramid załamuje się przy Chefrenie o 11,5°.
  Skrypt wypisuje wynik dopasowania przy każdym uruchomieniu (`[dopasowanie] …`).

## Licencje

- Petrie 1883: domena publiczna. HYG: CC BY-SA 4.0 (podać w opisie filmu: „katalog gwiazd HYG, D. Nash, CC BY-SA 4.0”).
- Czcionki napisów: Georgia, Arial (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/giza-pas-oriona/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/giza-pas-oriona/scena.py -- --proba 1,150,230,400
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 400 klatek: 293 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
