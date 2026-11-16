# Wschód Słońca ze szczytu piramidy i zielony promień

**Rodzaj:** ilustracja (prawdziwe zjawisko) · **Długość:** 20 s (500 klatek, 25 kl./s) · **Rozdział:** 11 „Zielony promień Słońca”

Patrzymy z wnętrza świątyni na szczycie schodkowej piramidy (podłoga na wys. 40 m) przez wejście na wschód,
na płaską równinę lasu. Jest świt i Słońce jest jeszcze pod horyzontem. Kamera podchodzi do progu, a potem
płynnie przybliża obraz (z 24 do 300 mm) na miejsce wschodu. W chwili, gdy nad horyzont wychyla się górny
brzeg tarczy, przez ok. 1,2 s błyska zielony skrawek (zielony promień). Potem wschodzi pomarańczowa, spłaszczona tarcza.

## Jak to jest zrobione (fizyka)

- Słońce ma prawdziwą średnicę kątową (0,53°). Tuż nad horyzontem refrakcja spłaszcza je w pionie (przyjęto 0,86).
- Atmosfera działa jak słaby pryzmat: obraz zielony Słońca leży nieco wyżej niż czerwony, a niebieski jest w większości
  rozproszony. Dlatego przy wschodzie jako pierwszy wychyla się zielony skrawek, a na górnym brzegu zostaje zielona obwódka.
  Tarcza jest złożona z trzech obrazów (czerwonego, zielonego i niebieskiego), przesuniętych w pionie.
- **Powiększenie:** przesunięcie obrazu zielonego jest powiększone (10% promienia). W rzeczywistości jest dużo mniejsze,
  a gołym okiem widać błysk dzięki mirażom nad płaskim horyzontem. Na zdjęciach z teleobiektywem błysk wygląda podobnie.
- **Czas:** przyspieszony ok. 15 razy, a sam błysk trwa ok. 1,2 s, czyli tyle, co w naturze (ok. 1–2 s).
- Niebo to model rozpraszania światła w atmosferze z Blendera (Multiple Scattering), z wysokością Słońca zgodną z tarczą.
  Ekspozycja zmienia się płynnie jak w aparacie: jaśniej w szerokim ujęciu przed świtem, ciemniej w zbliżeniu na Słońce.
- Piramida i świątynia są ogólne, w stylu Majów: grube mury, wejście ok. 2,2 × 2,9 m, sklepienie wspornikowe, grzebień dachowy.
  To nie jest konkretna budowla.

Wszystko w klipie jest wygenerowane w Blenderze: nie ma w nim zdjęć ani cudzych grafik.

## Pliki

- `scena.py`: buduje scenę od zera i renderuje (Blender 5.3, EEVEE). Kadry próbne: `-- probne 1,200,330,345,500`, pełny render: `-- pelny`.
- `klip.mp4`: 1920×1080, H.264, CRF 18 · `kadr.jpg`: klatka 470 · `klip.json`: opis dla `wideo.ts`.

Render: 500 klatek w 772 s (ok. 1,5 s na klatkę, EEVEE, RTX 2060 SUPER, karta współdzielona z innymi programami), 16.11.2026.
