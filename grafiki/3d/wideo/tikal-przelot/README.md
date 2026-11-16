# Tikal o świcie: przelot nad Placem Głównym

**Rodzaj:** rekonstrukcja · **Długość:** 16 s (400 klatek, 25 kl./s) · **Rozdział:** 8 „Siedemnaście stopni Dänikena”

Kamera startuje nisko na Placu Głównym, przy schodach Świątyni I, i patrzy na zachód na Świątynię II, oświetloną
wschodzącym Słońcem. Potem cofa się na południowy wschód i wznosi. Z prawej przesuwa się Świątynia I, pojawiają się
Akropol Północny, Akropol Centralny, a ponad zamgloną dżunglą Świątynie III i IV oraz grobla Tozzera.
Ostatni kadr pokazuje cały zespół z wysokości ok. 120 m.

## Na czym się opiera

| Co | Źródło | Licencja |
|---|---|---|
| Układ budowli (plan) | „Tikal map.JPG”, Simon Burchell, Wikimedia Commons: https://commons.wikimedia.org/wiki/File:Tikal_map.JPG | CC BY-SA 3.0 |
| Skala planu | Współrzędne świątyń II, III, IV, V, Akropolu Północnego, Akropolu Centralnego i Mundo Perdido z artykułów Wikipedii (en). Odległości między nimi dają skalę ok. 1,09 m na piksel planu, a podziałka na samym planie jest za duża. | fakty |
| Wysokości | Świątynia I: 47 m · Świątynia II: ok. 38 m (podstawa 37,6 × 41 m) · Świątynia III: ok. 55 m · Świątynia IV: 65 m (część źródeł podaje 70 m z platformą) · Świątynia V: ok. 57 m · Wielka Piramida Mundo Perdido: ok. 31 m. Plac między podstawami schodów Świątyń I i II ma ok. 70 m. Źródła: artykuły Wikipedii „Tikal Temple I”, „… II”, „… IV”, World History Encyclopedia „Tikal”. | fakty |
| Wygląd (do porównania) | Zdjęcia z Wikimedia Commons: „Temple of the Great Jaguar.jpg” (CC BY-SA 2.0), „Tikal Temple II.jpg” (CC BY 2.0). Służyły tylko za wzór kształtu i koloru kamienia, nie ma ich w klipie. | — |

Położenia w scenie (x = wschód, y = północ, od środka placu): Świątynia I (52, −1), II (−54, 0), III (−254, −15),
IV (−662, 163), V (−6, −283), Mundo Perdido (−452, −241). Świątynia I ma front na zachód, II, III i IV na wschód, V na północ.

## Co jest uproszczone

- Świątynie mają liczbę tarasów, wysokość i proporcje według źródeł (Świątynia I: 9 tarasów, Świątynia II: 3), ale detale
  (gzymsy, maski na grzebieniach dachowych, wnętrza) są uproszczone.
- Akropole i budowle Placu Wschodniego to bryły ułożone według planu: dziedzińce i pałace są przybliżone, a wysokości szacunkowe.
- Powierzchnie wyglądają jak dziś: szary wapień z ciemnymi zaciekami, trawa na placu. Dawnego czerwonego stiuku nie pokazujemy.
- Las to ok. 12 800 drzew w pobliżu i powierzchnia koron dalej. Mgła leży w pasie ok. 20–40 m nad ziemią.
- Słońce wschodzi z azymutu 82° na wysokości 5° nad horyzontem.

## Pliki

- `scena.py`: buduje scenę od zera i renderuje (Blender 5.3, EEVEE). Kadry próbne: `-- probne 1,160,300,400`, pełny render: `-- pelny`.
- `klip.mp4`: 1920×1080, H.264, CRF 18 · `kadr.jpg`: klatka 330 · `klip.json`: opis dla `wideo.ts`.

Daleki las przechodzi w stałą szaroróżową mgiełkę (kolor nieba przy horyzoncie po stronie przeciwnej do Słońca), żeby horyzont nie wyglądał jak morze.
Render: 400 klatek w 711 s (ok. 1,8 s na klatkę, EEVEE, RTX 2060 SUPER), 16.11.2026.
