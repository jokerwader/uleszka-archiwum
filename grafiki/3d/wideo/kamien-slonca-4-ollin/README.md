# kamien-slonca-4-ollin

Aztecki Kamień Słońca (Piedra del Sol, Muzeum Narodowe Antropologii w Meksyku) w 3D, do rozdziału 01
„Czy boimy się zrozumieć?”, przy cytacie z Annales de Cuauhtitlan („Piąte Słońce – Jego znakiem jest 4-Ollin…”). 16 s.

Rodzaj: `rekonstrukcja` (płaskorzeźba odtworzona z fotografii kamienia). Rysunek Leszka, na którym opiera się
układ wyróżnionych pól: `zrodlo/webacja/02uskok/ollin.gif` (jego podpis: „Aztecki znak Ollin – trzęsienie”).
To środek kamienia: twarz w kręgu i cztery kwadraty ułożone w znak Ollin.

## Co widać

1. Kamień w ukośnym świetle, kamera powoli krąży (ok. 30° w poziomie, kilka stopni w pionie).
2. Kolejno rozjaśniają się na złoto cztery kwadraty znaku Ollin, czyli cztery poprzednie Słońca (ery świata),
   każdy z podpisem: I Słońce – 4 Jaguar (Nahui Ocelotl, prawy górny), II – 4 Wiatr (Nahui Ehecatl, lewy górny),
   III – 4 Deszcz ognia (Nahui Quiahuitl, lewy dolny), IV – 4 Woda (Nahui Atl, prawy dolny).
   Taki układ i kolejność podaje opis kamienia (np. hasło „Aztec sun stone” w Wikipedii).
3. Na koniec świeci cały znak 4-Ollin (cztery kwadraty z twarzą pośrodku), u góry tytuł
   „V Słońce · 4-Ollin – Słońce Ruchu”. Reszta kamienia jest wtedy przyciemniona. Ostatnia klatka nadaje się do zatrzymania.

## Jak to zrobiono

- Fotografia jest prostowana do koła: zdjęcie zrobiono lekko od dołu, więc tarcza wychodzi na nim jako lekko
  spłaszczona elipsa. Środek twarzy i krawędzie tarczy odczytałem z siatki na zdjęciu, potem pierścienie
  (znaki dni, promienie) sprawdziłem na okręgach kontrolnych – trafiają z dokładnością ok. 1–2% promienia.
- Wysokość płaskorzeźby to jasność zdjęcia bez dużych plam światła (filtr górnoprzepustowy), głębokość 5,5 cm.
  To przybliżenie: jasność zdjęcia to w części cień, a nie wysokość, więc relief jest „wrażeniem” płaskorzeźby,
  a nie pomiarem. Kolor kamienia pochodzi wprost ze zdjęcia.
- Średnica tarczy 3,58 m. Bok i tył to prosty walec (prawdziwy monolit ma wokół tarczy nieregularny blok, pominięty).
- Środki kwadratów odczytane z wyprostowanego zdjęcia; maski świecenia są miękkie (nie obrysowują dokładnie kartuszy).

## Dane i licencje

- Fotografia kamienia: „Piedra del Sol en MNA.jpg”, autor Juan Carlos Fonseca Mata, 2019, licencja CC BY-SA 4.0,
  https://commons.wikimedia.org/wiki/File:Piedra_del_Sol_en_MNA.jpg (kopia w `_dane/kamien-slonca/`).
  Klip jest utworem zależnym i podlega tej samej licencji (CC BY-SA 4.0) – w opisie filmu trzeba podać autora zdjęcia.
- Rysunek: Leszek Klimek, uleszka.net (materiał archiwum).
- Czcionki napisów: Georgia, Arial (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/kamien-slonca-4-ollin/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/kamien-slonca-4-ollin/scena.py -- --proba 1,80,200,400
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`. Pliki pośrednie (wyprostowane zdjęcie, wysokości, maski)
powstają przy pierwszym uruchomieniu w `%TEMP%\uskok3d_cache\kamien_*_v1.*`.

## Render

EEVEE, 1920×1080, 25 kl./s, 400 klatek: 324 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
