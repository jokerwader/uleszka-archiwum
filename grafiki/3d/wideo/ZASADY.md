# Klipy 3D do filmów podcastu (YouTube)

Wspólne zasady dla wszystkich klipów w `grafiki/3d/wideo/`. Klipy wstawia do filmu skrypt `scripts/wideo.ts`
w chwili, gdy lektor czyta fragment tekstu wskazany w `klip.json`.

## Pliki jednego klipu: `grafiki/3d/wideo/<nazwa-klipu>/`

| Plik | Co to jest |
|---|---|
| `scena.py` | Skrypt Blendera budujący scenę od zera i renderujący klip (uruchamiany bez okna, patrz niżej) |
| `klip.mp4` | Gotowy klip: 1920×1080, 25 kl./s, H.264 yuv420p, CRF 18, bez dźwięku, 10–20 s |
| `kadr.jpg` | Jeden reprezentatywny kadr, 1600 px szerokości (podgląd, miniatura) |
| `klip.json` | Opis dla `wideo.ts` (format niżej) |
| `README.md` | Co pokazuje klip, na jakim rysunku lub źródle się opiera, skąd dane (z licencjami) |

`klip.json`:

```json
{
  "tytul": "Przesunięcie skorupy ziemskiej według Hapgooda",
  "podpis": "Krótki podpis na dole kadru, do ok. 70 znaków",
  "rodzaj": "rysunek-leszka",
  "rysunek": "zrodlo/webacja/02uskok/uskok.jpg",
  "fraza": "dosłowny fragment tekstu odcinka (min. 40 znaków), przy którym klip ma się pojawić"
}
```

- `rodzaj`: `rysunek-leszka` (ożywiony rysunek z artykułu), `hipoteza` (ilustracja tezy z tekstu, której nauka nie potwierdza),
  `rekonstrukcja` (odtworzenie budowli lub miejsca według pomiarów i planów), `ilustracja` (zjawisko potwierdzone, np. wschód Słońca).
  Od rodzaju zależy znaczek w rogu kadru, który dodaje `wideo.ts`.
- `fraza`: skopiowana dosłownie z `podcast/<folder odcinka>/rozdzialy-studio/*.txt` (bez znaczników w nawiasach kwadratowych).
  Może być kilka miejsc: zamiast `fraza` pole `frazy` z listą. `wideo.ts` szuka fraz każdego klipu w każdym odcinku, więc fraza
  ma być na tyle długa i charakterystyczna, żeby pasowała tylko do miejsca, o które chodzi.
- Nazwa folderu: klipy do odcinka 2 bez przedrostka (jak dotąd), do odcinka 1 z przedrostkiem `potop-`, do zwiastuna (odcinek 0) `zwiastun-`.
  Folder `wstep/` to animacja pod zapowiedź każdego odcinka (bez `klip.json`).

## Wygląd

- Tło: ciemny granat jak plansze filmu (od `#1b2a4d` do `#05070c`), akcenty złote `#f0c46f`.
- Ożywiony rysunek Leszka zachowuje jego kod kolorów i treść (np. niebieskie morze, zielone lądy, czerwona strzałka,
  białe linie, żółte podpisy), położenia i podpisy z rysunku. Ma wyglądać jak ten rysunek „w 3D”, piękniej, ale niczego nie dodawać od siebie.
- Napisy w scenie po polsku, czcionki `C:\Windows\Fonts\georgia.ttf`, `georgiab.ttf`, `arial.ttf` (mają polskie litery).
- Dolne 200 px i lewy górny róg (400×120 px) zostaw bez ważnych treści: tam `wideo.ts` kładzie podpis i znaczek.
- Ruch spokojny, płynny (wolny obrót, przelot kamery, wygładzone przejścia); klip ma się dać obejrzeć bez dźwięku.
- Ostatnia klatka ma być ładna, bo jeśli lektor mówi dłużej, `wideo.ts` przytrzyma ją kilka sekund.

## Render

- Bez okna Blendera: `S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/<nazwa>/scena.py`
  (Blender 5.3, EEVEE, karta RTX 2060 SUPER 8 GB). Nie ruszaj Blendera otwartego na pulpicie użytkownika ani jego plików.
- Najpierw kilka kadrów próbnych (PNG) i ich obejrzenie, dopiero potem pełny render.
- Kilka sesji renderuje na jednej karcie: przed pełnym renderem sprawdź, czy istnieje `grafiki/3d/wideo/.renderuje`.
  Jeśli tak, zajmij się czymś innym i sprawdź później. Jeśli nie, utwórz go z nazwą klipu, a po renderze usuń.
- Klatki pośrednie trzymaj w `%TEMP%` albo w `grafiki/3d/wideo/<nazwa>/_klatki/` (folder jest ignorowany przez git), mp4 składaj ffmpeg-iem.

## Dane i licencje

- Tylko domena publiczna, CC0, CC BY, CC BY-SA. Mapy: Natural Earth (domena publiczna), tekstury Ziemi: NASA Blue Marble (domena publiczna).
- Pobrane dane wspólne trzymaj w `grafiki/3d/wideo/_dane/` z plikiem `ZRODLA.md` (skąd, licencja).
- Rysunki Leszka: `zrodlo/webacja/02uskok/`. Tekst artykułu: `podcast/02-wielki-uskok/rozdzialy-studio/`.
- Nie pokazujemy ludzi.

## Git

Nie commituj i nie zmieniaj gałęzi: w tym samym folderze pracuje kilka sesji naraz. Zmieniaj tylko swoje foldery klipów
(i `_dane/`). Commit zrobi sesja główna.
