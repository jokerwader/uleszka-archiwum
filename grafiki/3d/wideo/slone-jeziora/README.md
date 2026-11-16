# Klip „slone-jeziora”

16 s, 1920×1080, 25 kl./s. Rozdział 07 „Czy woda może być śladem?”.

## Co pokazuje

Mapa świata jak na rysunku Leszka `zrodlo/webacja/02uskok/slonejeziora.jpg`, lekko w 3D (płyta mapy z delikatną rzeźbą lądów).
Kamera zaczyna nad obiema Amerykami, potem przelatuje nad Bliski Wschód i Azję Środkową, a na końcu pokazuje całą mapę.
Żółte trójkątne wskaźniki wyrastają po kolei od grotu, po każdym pojawia się biały podpis:

1. Salt Lake, 2. Wielka pustynia słona (USA), 3. Titicaca, 4. Salar del Uyuni,
5. m. Martwe, 6. m. Kaspijskie, 7. m. Aralskie, 8. jez. Bałchasz, 9. Wielka pustynia słona (Iran).

Ostatnia klatka to cała mapa ze wszystkimi dziewięcioma podpisami, tak jak na rysunku.

## Wierność rysunkowi

- Ten sam wycinek świata co u Leszka: odwzorowanie równoodległościowe, ok. 144°W–174°E i 80°N–50°S.
  Granice wyznaczone z położeń Salt Lake, Uyuni i Morza Martwego na rysunku (1,89 px na stopień).
- Wskaźniki stoją dokładnie tam, gdzie na rysunku: żółte piksele rysunku pogrupowano w 9 trójkątów,
  dla każdego zmierzono grot i podstawę (wartości wpisane w tabeli `JEZIORA` w `scena.py`). Nie poprawiano ich
  według prawdziwych współrzędnych jezior; np. wskaźnik „Wielka pustynia słona” w Iranie celuje, jak u Leszka,
  w okolice Zatoki Perskiej.
- Podpisy w miejscach i brzmieniu z rysunku. Jedyna zmiana: polskie litery. Na rysunku widać „Balchasz” i „slona”
  (w JPG z 2005 r. zabrakło „ł”); w klipie jest „Bałchasz” i „słona”, tak jak w tekście artykułu.
- Kolory: morza szaroniebieskie jak na rysunku (RGB ok. 80, 84, 118), wskaźniki żółte, podpisy białe z cieniem.

## Źródła i licencje

- Rysunek: Leszek Klimek, uleszka.net (2004–2007).
- Tekstura Ziemi: NASA Blue Marble 2002 „Land Surface, Shallow Water, and Shaded Topography” (R. Stöckli, NASA Earth Observatory),
  domena publiczna; plik z Wikimedia Commons (File:Land_shallow_topo_2048.jpg), zmniejszony do 8192×4096:
  `grafiki/3d/wideo/_dane/blue-marble/` (opis w `_dane/ZRODLA.md`). Morza przemalowuje shader (maska koloru niebieskiego).
- Czcionka: Arial Bold (Windows), tylko do renderu.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/slone-jeziora/scena.py`
(kadry próbne: `... -- --test 1,120,290,400`). EEVEE, 48 próbek, 400 klatek w ok. 5 min (315 s) na RTX 2060 SUPER.
