# Wschód Słońca ze szczytu piramidy i zielony promień

**Rodzaj:** ilustracja (prawdziwe zjawisko) · **Długość:** 20 s (500 klatek, 25 kl./s) · **Rozdział:** 11 „Zielony promień Słońca”
· Wersja 2 z 16.11.2026 (widok z zewnątrz zamiast wnętrza świątyni, okienko lunety z zielonym promieniem).

## Co widać

1. **0–11 s, dolot.** Kamera nadlatuje od południowego zachodu nad dżunglą do schodkowej piramidy (świątynia na szczycie,
   podłoga na wys. 40 m) i zatrzymuje się tuż za świątynią, na wysokości jej dachu. Patrzymy na wschód ponad lasem:
   korony drzew, mgły w zagłębieniach, dwie dalsze piramidy wystające z lasu, na horyzoncie łuna świtu.
2. **11–13 s, okienko lunety.** W prawym górnym rogu pojawia się okrągłe okienko: ten sam wschód widziany teleobiektywem
   z progu świątyni (pole widzenia 0,9°). Złota linia łączy je z miejscem wschodu na horyzoncie.
3. **13–14,5 s, zielony promień.** W okienku nad horyzont wychyla się zielony skrawek, obok pojawia się podpis
   „zielony promień, trwa około sekundy”.
4. **14,5–20 s, wschód.** Wschodzi pomarańczowa, spłaszczona tarcza z zieloną obwódką na górnym brzegu. W szerokim ujęciu
   Słońce rozświetla horyzont, a korony drzew dostają złote krawędzie. Kamera cały czas powoli sunie do przodu.

Ostatnia klatka: świątynia po lewej, Słońce w trzech czwartych nad horyzontem, okienko z tarczą i podpisem.

## Jak to jest zrobione (fizyka)

- Słońce ma prawdziwą średnicę kątową (0,53°). Tuż nad horyzontem refrakcja spłaszcza je w pionie (przyjęto 0,86).
  W szerokim ujęciu tarcza ma więc ok. 20 px, dlatego szczegóły pokazuje okienko lunety.
- Atmosfera działa jak słaby pryzmat: obraz zielony Słońca leży nieco wyżej niż czerwony, a niebieski jest w większości
  rozproszony. Dlatego przy wschodzie jako pierwszy wychyla się zielony skrawek, a na górnym brzegu zostaje zielona obwódka.
  Tarcza jest złożona z trzech obrazów (czerwonego, zielonego i niebieskiego), przesuniętych w pionie.
- **Powiększenie:** przesunięcie obrazu zielonego jest mocno powiększone (18% promienia tarczy), żeby skrawek był czytelny
  w okienku. W rzeczywistości jest dużo mniejsze, a gołym okiem widać błysk dzięki mirażom nad płaskim horyzontem.
- **Czas:** przyspieszony ok. 15 razy, a sam zielony skrawek jest widoczny ok. 1,4 s, czyli tyle, co w naturze (ok. 1–2 s).
- Niebo to model rozpraszania światła w atmosferze z Blendera (Multiple Scattering), z wysokością Słońca zgodną z tarczą.
  Mgiełka nad lasem i mgły biorą kolor z tego samego nieba. Poświata wokół Słońca w szerokim ujęciu jest dodana (olśnienie).
  Ekspozycja zmienia się płynnie jak w aparacie; okienko lunety ma własną, ciemniejszą.
- Piramida i świątynia są ogólne, w stylu Majów (Petén): osiem stopni, schody od wschodu, grube mury, wejście 2,2 × 2,9 m,
  gzymsy, grzebień dachowy. Dwie dalsze piramidy to kopie tej samej bryły. To nie są konkretne budowle. Ludzi nie ma.

Wszystko w klipie jest wygenerowane w Blenderze: nie ma w nim zdjęć ani cudzych grafik. Napisy: czcionki Georgia i Arial.

## Pliki

- `scena.py`: buduje scenę od zera i renderuje (Blender 5.3, EEVEE). Klip składa się z trzech przebiegów łączonych ffmpeg-iem:
  ujęcie główne (`_klatki/k_####.png`), luneta 430×430 px (`_klatki/lupa_####.png`, od klatki 285) i dwie przezroczyste
  nakładki (pierścienie z linią, podpis). Tryby: `-- probne 1,140,270,345,360,500` (kadry próbne, już złożone),
  `-- pelny` (pełny render z blokadą `.renderuje`), `-- zloz` (samo ponowne złożenie mp4 z gotowych klatek).
- `klip.mp4`: 1920×1080, H.264, CRF 18 · `kadr.jpg`: klatka 341 (zielony skrawek w okienku) · `klip.json`: opis dla `wideo.ts`.

Render: 500 klatek ujęcia głównego i 216 klatek lunety w 1776 s (ok. 30 min; EEVEE, 48 próbek, RTX 2060 SUPER, karta współdzielona z innymi renderami), 16.11.2026.
