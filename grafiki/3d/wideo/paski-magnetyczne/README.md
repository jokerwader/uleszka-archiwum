# paski-magnetyczne

Zastygła lawa grzbietu atlantyckiego zapisuje kierunek pola magnetycznego Ziemi.
Rozdział 08 „Siedemnaście stopni Daenikena”. 16 s. Rodzaj: `ilustracja` (zjawisko potwierdzone).

Tekst Leszka: „Wspomnieć też trzeba o badaniach warstw lawy wypływającej z grzbietu atlantyckiego i odkryciu,
że w zastygłych pokładach zachował się układ linii ówczesnego pola magnetycznego. To być może pozwoli na określenie
położenia biegunów w dawnych czasach.”

## Co widać

1. Blok dna oceanu w przekroju: pod grzbietem unosi się magma, w szczelinie świeci lawa.
2. Dno rozsuwa się na obie strony (złote strzałki). Stygnąca lawa przyjmuje kolor aktualnego kierunku pola:
   pomarańczowy „jak dziś”, niebieski „odwrócone”. Białe strzałki na pasach pokazują zapisany kierunek.
3. Igła nad blokiem pokazuje kierunek pola; odwraca się w chwilach prawdziwych odwróceń pola, a przy grzbiecie
   zaczyna wtedy powstawać pas drugiego koloru. Po obu stronach grzbietu pasy są lustrzanym odbiciem.
4. Licznik po prawej biegnie od „2,3 mln lat temu” do „dziś”.

## Skąd kolejność pasów

Odwrócenia pola według skali S. C. Cande i D. V. Kenta (1995). Okresy pola „jak dziś” (wiek w mln lat):
0–0,78 (Brunhes), 0,99–1,07 (Jaramillo), 1,77–1,95 (Olduvai), 2,581–3,04, 3,11–3,22 i 3,33–3,58 (Gauss, z przerwami
Kaena i Mammoth), 4,18–4,29 (Cochiti), 4,48–4,62 (Nunivak), 4,80–4,89 (Sidufjall), 4,98–5,23 (Thvera).
Między nimi pole było odwrócone (Matuyama, Gilbert). Klip zaczyna się 2,3 mln lat temu i kończy dziś, więc igła
obraca się 1,95, 1,77, 1,07, 0,99 i 0,78 mln lat temu. W ostatniej klatce środkowy pomarańczowy pas to Brunhes,
wąski pomarańczowy pasek obok to Jaramillo, następny Olduvai, a przy krawędzi bloku zaczyna się Gauss (blok sięga
3 mln lat). Skala bloku: 1 jednostka sceny = 0,5 mln lat; przy rozsuwaniu Atlantyku ok. 2,5 cm na rok (obie strony
razem) blok miałby ok. 75 km szerokości.

## Zastrzeżenia

- Blok jest schematem, nie mapą żadnego odcinka grzbietu: prędkość rozsuwania jest stała i taka sama po obu stronach,
  rzeźba dna uproszczona, 2,3 mln lat ściśnięte do 16 sekund. Pominięto epizod Réunion (2,14–2,15 mln lat temu):
  trwał 10 tys. lat i pas byłby cieńszy niż piksel. Strzałki stoją tylko na pasach szerszych niż 0,2 mln lat.
- Poprawka z 16.11.2026 (audyt): wcześniej chwile odwróceń liczyła wymyślona funkcja (suma sinusów).
- Sprawdzenie dat (16.11.2026): sześć granic widocznych w klipie (0,78; 0,99; 1,07; 1,77; 1,95 i 2,58 mln lat)
  porównano z tabelami wtórnymi, które powołują się na Cande'a i Kenta (lista „List of geomagnetic reversals”
  w Wikipedii, tabele programu wierceń oceanicznych IODP); zgadzają się. Samego artykułu z 1995 r. nie otwierano.
  Starsze granice z tabeli w `scena.py` (3,04–5,23 mln lat) nie są w klipie widoczne i nie były sprawdzane.
- Nauka: symetryczne pasy namagnesowania dna po obu stronach grzbietów opisali F. Vine i D. Matthews oraz L. Morley
  (1963). Zapis w lawie mówi o odwróceniach pola magnetycznego i o dawnym położeniu biegunów magnetycznych względem
  płyt; nie jest dowodem nagłego przesunięcia całej skorupy. Klip pokazuje tylko sam mechanizm zapisu.

## Dane i licencje

- Skala odwróceń: S. C. Cande, D. V. Kent, „Revised calibration of the geomagnetic polarity timescale for the Late
  Cretaceous and Cenozoic”, Journal of Geophysical Research 100 (B4), 1995, s. 6093–6095 (daty wpisane w `scena.py`;
  same daty są faktami naukowymi).
- Geometria i wzory wykonane od zera w `scena.py`.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/paski-magnetyczne/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/paski-magnetyczne/scena.py -- --proba 1,150,260,400
```
