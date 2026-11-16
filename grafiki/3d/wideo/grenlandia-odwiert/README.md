# Klip „grenlandia-odwiert”

16 s, 1920×1080, 25 kl./s. Rozdział 04 „Po co zrobiono dziurę w Grenlandii?”.

## Co pokazuje

1. Przekrój lądolodu Grenlandii: kopuła lodu z warstwami, które w głąb są coraz cieńsze, pod spodem skała.
   Na szczycie wieża wiertnicza; wiertło schodzi do dna (ok. 3000 m), po drodze pojawiają się znaczniki 1000, 2000 i 3000 m.
2. Złoty nawias zaznacza odcinek 1000–3000 m, czyli zakres osi głębokości na wykresie Leszka.
3. Rdzeń lodowy z tego odcinka wychodzi z otworu, obraca się poziomo i kładzie pod wykresem
   (3000 m po lewej, 1000 m po prawej, jak na osi Leszka).
4. Wykres wyrasta z rdzenia: złota linia przesuwa się wzdłuż rdzenia, a nad nią rysuje się krzywa temperatury.
5. Na koniec jasny pas między 12 a 10 tys. lat (jest na rysunku) i złota klamra „ok. 7°C”.

## Wierność rysunkowi

- Krzywa nie jest narysowana „na oko”: `scena.py` odczytuje piksele niebieskiej linii z `zrodlo/webacja/02uskok/temperatura.jpg`
  (kolumna po kolumnie, najniższy i najwyższy piksel) i buduje z nich linię 3D. 21 z 529 kolumn nie miało niebieskich pikseli
  (linia przechodzi tam przez ciemne linie siatki); te miejsca są uzupełnione liniowo z sąsiednich kolumn.
- Siatka (13 linii poziomych co 1°C, pionowe linie przy liczbach wieku), liczby, podpisy osi, jasny pas 12–10 tys. lat
  i szara tablica stoją w tych samych miejscach i kolorach co na rysunku. Podpisy przepisane dosłownie
  (w tym „(w tys. lat)”, „(w m.)” i pionowy „ZMIANA TEMPERATURY O 1 STOPIEŃ CELSJUSZA”).
- Rysunek nie ma zera na osi temperatury (Leszek o tym pisze); klip też go nie dodaje.
- Dodane od nas: przekrój lodu z wiertłem, rdzeń i złota klamra „ok. 7°C”. Liczba 7°C pochodzi z tekstu Leszka
  („pomiędzy 12 a 10 tysiącami lat temu wzrost średniej temperatury wyniósł około 7°C”), nie z rysunku.
  Klamra sięga od dołka krzywej przy 12 tys. lat do poziomu po skoku, czyli ok. 6 linii siatki (ok. 6–7°C).

## Tło (nie pokazane w klipie)

Leszek nie podaje, z którego odwiertu jest wykres. Na szczycie lądolodu wykonano dwa głębokie odwierty:
europejski GRIP (1989–1992, ok. 3029 m do skały) i amerykański GISP2 (1989–1993, ok. 3053 m).
Wykresy temperatury z tych rdzeni powstały z pomiarów izotopów tlenu w lodzie.
Przekrój w klipie ma w osi odwiertu ok. 3075 m lodu, a kopuła jest mocno przewyższona (szerokość setek km, grubość 3 km).

## Źródła i licencje

- Rysunek: Leszek Klimek, uleszka.net (2004–2007), `zrodlo/webacja/02uskok/temperatura.jpg`.
- Geometria lodu, wiertła i rdzenia: wykonana od zera w `scena.py` (bez cudzych modeli i tekstur).
- Czcionki: Arial (Windows), tylko do renderu.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/grenlandia-odwiert/scena.py`
(kadry próbne: `... -- --test 1,150,300,400`). EEVEE, 48 próbek, 400 klatek w ok. 7 min (415 s) na RTX 2060 SUPER.
