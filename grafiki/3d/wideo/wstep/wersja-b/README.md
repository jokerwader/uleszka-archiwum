# Wstęp odcinka, wersja B (sceny dawnej czołówki pod zapowiedź lektora)

Druga wersja 30-sekundowego wstępu. Wersja A (`../klip.mp4`) to przelot wśród rysunków Leszka i Ziemia z orbity.
Wersja B bierze sceny i tempo dawnej czołówki (Ziemia ze złotymi równikami, Giza, Tikal, Kamień Słońca, Stonehenge)
i układa je pod zapowiedź. Klip nie ma dźwięku, bo dźwięk to nagranie odcinka.

| Plik | Co to jest |
|---|---|
| `scena.py` | Skrypt Blendera 5.3 (EEVEE): buduje scenę, renderuje klatki do `_klatki/`, składa klip i podgląd |
| `klip.mp4` | Wstęp B: 1920×1080, 25 kl./s, 750 klatek, H.264 yuv420p, CRF 18, bez dźwięku |
| `kadr.jpg` | Kadr z montażu (klatka 250, Giza), 1600 px |
| `podglad.mp4` | Do obejrzenia całości: klip + pierwsze 30 s nagrania odcinka 2 + przykładowy tytuł odcinka na środku (14,3–24,5 s) |
| `arkusz-czolowki.jpg` | Dziewięć kadrów dawnej czołówki (3×3), na której wzorowana jest ta wersja |

Bez `klip.json`. `wideo.ts` nadal używa wersji A (`grafiki/3d/wideo/wstep/klip.mp4`); żeby wstawić B, trzeba zmienić tam ścieżkę `WSTEP`.

## Co widać (numery klatek = numery klatek filmu, od 0)

| Klatki | Czas | Lektor / muzyka | Obraz |
|---|---|---|---|
| 0–47 | 0,0–1,9 s | „Uwierz we własny rozum.” | Z ciemności złoty błysk (kl. 4), fala drobin i tytuł |
| 47–172 | 1,9–6,9 s | „Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi.” | Spokojny kadr hołdu: tytuł odsuwa się w górę, w ciepłej poświacie „w hołdzie śp.” i „Leszkowi Wiktorowi Klimkowi” (tak jak w wersji A) |
| 172–229 | 6,9–9,1 s | „Jego teksty ze strony uleszka.net…”, akcent basu 6,86 s | Ziemia: Słońce wychodzi zza krawędzi, rozbłyskują dwa złote równiki (dzisiejszy i dawny, z biegunem na wyspie Akpatok) |
| 229–274 | 9,1–11,0 s | „…z lat 2004–2007,”, akcent 9,14 s | Giza: trzy piramidy w złotym konturze, nad nimi gwiazdy pasa Oriona |
| 274–322 | 11,0–12,9 s | akcent 10,95 s | Tikal: Świątynia I nad dżunglą |
| 322–358 | 12,9–14,3 s | „czytane bez zmian.”, akcent 12,88 s | Kamień Słońca Azteków w złocie |
| 358–625 | 14,3–25,0 s | „Odcinek …”, potem „Czyta lektor wygenerowany przez sztuczną inteligencję.” | Stonehenge o wschodzie Słońca, kamienie nisko w kadrze, **środek pusty na tytuł odcinka**. Na kl. 422 (akcent 16,89 s) Słońce wchodzi w szczelinę wielkiego trylitu |
| 625–750 | 25,0–30,0 s | muzyka wygasa | Kamera odpływa w górę i w tył. Ostatnia klatka: krąg we mgle, Słońce nad horyzontem, gwiazdy (nie czarna, ruch wyhamowuje) |

Cięcia montażu (172, 229, 274, 322, 358) leżą na skokach basu zmierzonych w pierwszych 30 s nagrania odcinka 2
(pasmo poniżej 90 Hz, gdzie głos lektora przeszkadza najmniej) i mają krótkie rozjaśnienie, jak w czołówce.
Małe napisy dokłada ffmpeg przy składaniu klipu: „uleszka.net · 2004–2007” (kl. 196–320, y ≈ 960 px; znika przed
Kamieniem Słońca, bo złoty napis na złotym kamieniu był nieczytelny) i „lektor: głos wygenerowany przez AI”
(kl. 500–647, y ≈ 990 px, na ciemnej ziemi pod kamieniami).

### Przejście Kamień Słońca → Stonehenge (klatki 344–380)

Zamiast twardego cięcia: od klatki 346 kamera przyspiesza ku twarzy Słońca w środku kamienia i rozlewa się z niej
złota poświata. Na klatkach 357–358 światło wypełnia cały kadr (tu jest cięcie), potem do klatki 380 zbiega się
do łuny nad horyzontem za Stonehenge, czyli tam, gdzie na klatce 422 wschodzi Słońce.
Poświatę dokłada kompozytor Blendera (maska, rozmycie, mieszanie), więc do zmiany wystarczy render klatek 344–381.
Ustawienia na górze `scena.py`: `PRZ0`, `PRZ1`, `PRZ_MIEKKOSC`, `PRZ_HORYZONT`.

### Miejsce na tytuł odcinka

Między klatką 358 a 625 nad kamieniami jest samo niebo z gwiazdami: wolny jest pas od góry kadru do ok. y = 680 px.
Szczyt wielkiego trylitu jest na ok. y = 710 px, Słońce na ok. y = 845 px w środku szerokości (zmierzone na klatce 450).
Niebo jest tu ciepłe (brąz i złoto od mgły), nie granatowe jak w wersji A; złoty tytuł z ciemnym obrysem jest na nim czytelny,
co widać w `podglad.mp4`.

### Czasy do przestawienia

Słownik `T` na górze `scena.py`: `blysk`, `hold`, `montaz`, `adres`, `giza`, `tikal`, `kamien`, `stone`, `slonce`, `lektor`, `odplyw`.

## Uruchomienie (z katalogu repozytorium)

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/wersja-b/scena.py -- --proba 40,110,200,250,300,340,450,749
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/wersja-b/scena.py -- --czekaj
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/wersja-b/scena.py -- --zloz
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/wersja-b/scena.py -- --podglad <nagranie odcinka.mp3>
```

## Źródła i licencje

| Co | Źródło | Licencja |
|---|---|---|
| Tekstura Ziemi | NASA Blue Marble 2002 (`_dane/blue-marble/`) | domena publiczna |
| Gwiazdy (5070 do 6 mag) | katalog HYG v4.4, David Nash / astronexus (`_dane/hyg/`) | CC BY-SA 4.0 |
| Kamień Słońca | fotografia „Piedra del Sol en MNA”, Juan Carlos Fonseca Mata, Wikimedia Commons (`_dane/kamien-slonca/`); płaskorzeźba 3D powstaje z jasności zdjęcia, jak w klipie `kamien-slonca-4-ollin` | CC BY-SA 4.0 |
| Położenie i wymiary piramid w Gizie | W. M. F. Petrie, 1883; odległość Mykerinosa E–W z Wikidata | domena publiczna, CC0 |
| Dawny biegun (wyspa Akpatok, 60°N 70°W) i dawny równik | tabela i rysunek Leszka Klimka `zrodlo/webacja/02uskok/uskok.jpg` | materiał archiwum |
| Świątynie w Tikal, Stonehenge | własne uproszczone bryły według ogólnie znanych wymiarów | własne |
| Czcionki | Georgia, Georgia Bold, Arial Bold (systemowe) | – |
| Dźwięk w `podglad.mp4` | pierwsze 30 s nagrania odcinka 2 (lektor ElevenLabs i muzyka z nagrania) | tylko do podglądu |

**Uwaga do opisu filmów**, jeśli wejdzie wersja B: zdjęcie Kamienia Słońca i katalog HYG są na CC BY-SA 4.0, więc klip jest
utworem zależnym na tej licencji i w opisie trzeba podać: „Kamień Słońca: fot. Juan Carlos Fonseca Mata, CC BY-SA 4.0;
gwiazdy: katalog HYG v4.4 (astronexus), CC BY-SA 4.0; Ziemia: NASA Blue Marble”.

W kadrze nie ma ludzi. Opracowanie: jokerwader.
