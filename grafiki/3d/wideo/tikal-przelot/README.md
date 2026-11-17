# Tikal: cyfrowa rekonstrukcja centrum („rentgen”) i trójkąt Świątyń IV, I, V

**Rodzaj:** rekonstrukcja · **Długość:** 16 s (400 klatek, 25 kl./s) · **Rozdział:** 8 „Siedemnaście stopni Dänikena”
· Wersja 2 z 16.11.2026: styl „rentgen” zamiast realistycznej dżungli (prawdziwe ujęcia Tikal z drona są już w filmie,
więc 3D pokazuje to, czego kamera nie widzi).

## Co widać

Granatowe tło filmu, budowle jako półprzezroczyste błękitne bryły ze świecącymi krawędziami, dżungla i grunt jako chmura
punktów (jak skan lidarowy z samolotu). Złoto jest tylko dla tego, co ukryte, i dla linii trójkąta.

1. **0–4 s.** Kamera stoi nisko na Placu Głównym. Linia skanu jedzie na zachód i odsłania Świątynię II: tarasy, schody
   i trzy złote komory na szczycie. W prawym górnym rogu mały napis „rekonstrukcja 3D w stylu skanu lidarowego”.
2. **4–9 s.** Kamera cofa się i wznosi. Skan dochodzi do Świątyni III. Po prawej Akropol Północny (napis „w środku starsze
   budowle i grobowce władców”), w nim złote starsze
   budowle i grobowce.
3. **9–12 s.** Niski przelot obok Świątyni I: pod piramidą złoty grobowiec władcy, do niego linia pionu od komór na szczycie
   i tunel archeologów od stóp schodów. Napis „grobowiec władcy, odkryty tunelem w 1962 r.”.
4. **12–16 s.** Kamera wznosi się na 330 m. Na ziemi rysuje się złoty trójkąt Świątyń IV, I i V ze znakiem kąta prostego
   i napisem „90°” przy Świątyni I (cytat Dänikena z frazy klipu). Ostatnia klatka: całe centrum z trójkątem.

## Na czym się opiera

| Co | Źródło | Licencja |
|---|---|---|
| Układ budowli (plan) | „Tikal map.JPG”, Simon Burchell, Wikimedia Commons: https://commons.wikimedia.org/wiki/File:Tikal_map.JPG | CC BY-SA 3.0 |
| Skala planu | Współrzędne świątyń II, III, IV, V, Akropolu Północnego, Akropolu Centralnego i Mundo Perdido z artykułów Wikipedii (en). Odległości między nimi dają skalę ok. 1,09 m na piksel planu. | fakty |
| Wysokości i tarasy | Świątynia I: 47 m, 9 tarasów · II: 38 m, 3 tarasy · III: ok. 55 m · IV: 64,6 m, 7 tarasów · V: 57 m · Wielka Piramida Mundo Perdido: ok. 31 m. Artykuły Wikipedii (en) „Tikal Temple I” … „Tikal Temple V”. | fakty |
| Wnętrza | Artykuły Wikipedii (en), sprawdzone 16.11.2026: „Tikal Temple I”–„V”, „North Acropolis, Tikal” (szczegóły niżej). | fakty |

Położenia w scenie (x = wschód, y = północ, od środka placu): Świątynia I (52, −1), II (−54, 0), III (−254, −15),
IV (−662, 163), V (−6, −283), Mundo Perdido (−452, −241). Kąt przy Świątyni I w trójkącie IV–I–V wynosi ok. 91°.

### Wnętrza: co mówią źródła i co pokazuje klip

| Element w klipie | Źródło | Co jest umowne |
|---|---|---|
| Świątynia I: trzy wąskie komory na szczycie, jedna za drugą | „three narrow, dark chambers … accessible only through a single doorway” | wymiary komór |
| Świątynia I: grobowiec Jasaw Chan K'awiila I (Pochówek 116) | „a large vaulted chamber deep within the pyramid, below the level of the Great Plaza”; grobowiec zbudowano najpierw, piramidę nad nim; odkryty w 1962 r. (Aubrey Trik), wejście „after exploratory tunneling from the bottom of the temple stairway” | głębokość, wymiary i dokładne miejsce (źródło ich nie podaje); linia pionu to znak graficzny, nie szyb |
| Świątynia II: trzy komory | „contains three chambers”; grobowca nie znaleziono | wymiary |
| Świątynia III: dwie komory | „only possesses two rooms instead of the usual three”; nie była badana | wymiary |
| Świątynia IV: trzy komory | „three chambers situated one behind the other”; grobowiec tylko przypuszczalny, więc go nie ma w klipie | wymiary |
| Świątynia V: jedna mała komora | głębokość 90 cm, szerokość 3,95 m, wysokość 4,4 m | brak |
| Akropol Północny: grobowce pod świątyniami 34 (Pochówek 10), 33 (Pochówek 48), 32 (Pochówek 195) i 26 (Pochówek 85) | „North Acropolis, Tikal”: nekropolia królewska używana ponad 1300 lat | położenia w planie i głębokości schematyczne |
| Akropol Północny: starsze budowle w środku, trzy wersje świątyni 33 | „Temple 33 … three phases”; większość budowli miała po dwie fazy | kształty i wymiary starszych budowli (tylko idea „budowla w budowli”) |

## Co jest uproszczone

- Budowle mają te same położenia, wymiary i liczbę tarasów co w wersji realistycznej (`scena.py`, funkcja `miasto`).
  Dla czytelności rysunku tarasy są bez narożnych uskoków i gzymsów, a stopnie schodów są co 1,5 m.
- Akropole i budowle Placu Wschodniego to bryły ułożone według planu: dziedzińce i pałace są przybliżone.
  Platforma Akropolu Północnego ma w modelu 9 m nad placem (źródło: 12 m).
- Chmura punktów jest wygenerowana (ok. 228 tys. punktów na koronach 17,5 tys. drzew, ok. 61 tys. punktów gruntu).
  To nie jest prawdziwy skan lidarowy Tikal, a rzeźba terenu jest umowna. Mówi o tym napis na początku klipu.
- Trójkąt IV–I–V pokazuje to, co mówi cytat. Z planu wynika kąt ok. 91° przy Świątyni I (szczegóły w `tikal-kompas/README.md`).

## Pliki

- `rentgen/scena.py`: **scena tego klipu** (Blender 5.3, EEVEE). Wczytuje geometrię z `scena.py` i pokazuje ją w stylu „rentgen”.
  Bez argumentów robi pełny render do `klip.mp4` i `kadr.jpg` (z blokadą `.renderuje`), kadry próbne:
  `-- probne 1,30,140,255,290,400 blekit` (wariant `zloto` został jako próba, użytkownik wybrał `blekit`).
- `scena.py`: poprzednia, realistyczna wersja klipu (dżungla o świcie) i źródło geometrii budowli. Realistyczny klip można
  z niej odtworzyć (`-- pelny`, ok. 12 min), ale nadpisze `klip.mp4`.
- `rentgen/arkusz-probny.jpg`, `rentgen/README.md`: pierwsza próba stylu (oba warianty koloru), zostawione do wglądu.
- `klip.mp4`: 1920×1080, H.264, CRF 18 · `kadr.jpg`: klatka 258 (grobowiec pod Świątynią I) · `klip.json`: opis dla `wideo.ts`.

Render: 400 klatek w 579 s przy wolnej karcie (ok. 1,4 s na klatkę), drugi raz 1424 s przy karcie zajętej innym programem (EEVEE, 32 próbki, RTX 2060 SUPER), 16.11.2026. Plik ma ok. 33 MB, bo chmura punktów słabo się kompresuje.
