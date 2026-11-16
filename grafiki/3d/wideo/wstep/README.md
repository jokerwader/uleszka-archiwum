# Wstęp odcinka (30 s, pod zapowiedź lektora)

Animacja 3D na pierwsze 30 sekund każdego filmu podcastu „Uwierz we własny rozum – teksty Leszka Klimka”.
Lektor czyta wtedy zapowiedź na tle muzyki, która jest już w nagraniu, więc klip **nie ma dźwięku**.
Zastępuje nieruchomą planszę z okładką. Jest wspólny dla wszystkich odcinków: tytuł konkretnego odcinka
nakłada `scripts/wideo.ts` w pustym środku kadru (14,3–25 s).

| Plik | Co to jest |
|---|---|
| `scena.py` | Skrypt Blendera 5.3 (EEVEE). Buduje całość od zera i renderuje klatki do `_klatki/` |
| `klip.mp4` | Gotowy wstęp: 1920×1080, 25 kl./s, 750 klatek, H.264 yuv420p, CRF 18, bez dźwięku |
| `kadr.jpg` | Kadr z tytułem (klatka 40), 1600 px |
| `PLAN.md` | Plan obrazu i czasy zapowiedzi |

Folder celowo **nie ma `klip.json`**: `wideo.ts` wstawiłby wtedy wstęp w środek odcinka jak zwykły klip.

## Co widać (numery klatek = numery klatek filmu, od 0)

| Klatki | Czas | Lektor | Obraz |
|---|---|---|---|
| 0–47 | 0,0–1,9 s | „Uwierz we własny rozum.” | Z ciemności złoty błysk (kl. 4), fala złotych drobin i tytuł „Uwierz we własny rozum” |
| 47–163 | 1,9–6,5 s | „Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi.” | Tytuł odsuwa się w górę i maleje. W ciepłej poświacie pojawia się „w hołdzie śp.” i „Leszkowi Wiktorowi Klimkowi”. Drobiny unoszą się powoli jak iskry |
| 163–318 | 6,5–12,7 s | „Jego teksty ze strony uleszka.net z lat 2004–2007,” | Przelot wśród 13 rysunków Leszka w złotych ramkach. Od kl. 190 napis „uleszka.net · 2004–2007” |
| 318–358 | 12,7–14,3 s | „czytane bez zmian.” | Rysunki układają się w trzy równe rzędy (ruszają od kl. 304, stoją od ok. kl. 342) |
| 358–625 | 14,3–25,0 s | „Odcinek …”, od 20,0 s „Czyta lektor wygenerowany przez sztuczną inteligencję.” | Ziemia z orbity, nisko nad krawędzią, i gwiazdy. **Środek kadru jest pusty na tytuł odcinka.** Na kl. 425 (akcent muzyki ok. 17 s) Słońce wychodzi zza krawędzi po lewej. Od kl. 500 mały napis „lektor: głos wygenerowany przez AI” na dole |
| 625–750 | 25,0–30,0 s | muzyka wygasa | Kamera odpływa: Ziemia maleje, wokół niej rysuje się złoty krąg zodiaku. Ostatnia klatka nie jest czarna (Ziemia z kręgiem na tle gwiazd), ruch na końcu wyhamowuje, więc można ją przytrzymać |

Cięcia między trzema ujęciami (kl. 163 i 358) to krótkie przyciemnienia, bez ostrych skoków, bo to spokojna zapowiedź z hołdem.
W kadrze nie ma ludzi ani portretu.

### Gdzie `wideo.ts` może położyć tytuł odcinka

Między klatką 370 a 625 wolny jest obszar mniej więcej od y = 150 do y = 700 px na całej szerokości
(samo granatowe niebo z gwiazdami). Krawędź Ziemi ma szczyt ok. y = 770 px, błysk Słońca jest w lewym dolnym rogu
(ok. x = 500, y = 830 px), a napis o lektorze na y = 1010 px.

### Czasy do przestawienia

Wszystkie momenty są w słowniku `T` na górze `scena.py` (numery klatek): `blysk`, `hold`, `rysunki`, `adres`,
`uklad`, `ziemia`, `slonce`, `lektor`, `odplyw`. Wziąłem je z zapowiedzi odcinka 2 (`PLAN.md`) i z pomiaru
pierwszych 30 s nagrania `ElevenLabs_uLeszka_-_Wielki_Uskok.mp3`: głośniejsze fale muzyki wypadają ok. 0, 4, 10–10,5,
13, 17 i 20,5 s, a od 25 s muzyka gaśnie. Pomiar jest z miksu z głosem. Gdy będzie czysta muzyka, wystarczy
poprawić liczby w `T` i wyrenderować jeszcze raz (kilkanaście minut).

## Jak to jest zrobione

- Jedna scena Blendera, trzy kamery przełączane znacznikami na osi czasu. Obiekty każdego ujęcia są ukrywane
  poza swoim zakresem klatek (klucze `hide_render`).
- Tytuł: Georgia Bold, złoty gradient `#fff6e0` → `#f0c46f` → `#b47a22`, wytłoczony w 3D, z przesuwającym się połyskiem.
- Rysunki to płaszczyzny z teksturą (powiększone trzykrotnie filtrem Lanczos, przezroczyste GIF-y na białym tle),
  każdy z własnym torem lotu i miejscem w układzie końcowym.
- Ziemia i atmosfera świecą światłem policzonym w shaderze od kierunku Słońca. Tor kamery jest policzony tak,
  żeby Słońce wyszło zza krawędzi dokładnie na klatce `T["slonce"]`.
- Drobiny i gwiazdy to chmury punktów z Geometry Nodes.
- Kompozycja w Blenderze: poświata, smugi wokół najjaśniejszych punktów, lekka aberracja, winieta, błysk na początku
  i przyciemnienia na cięciach. Widok „Khronos PBR Neutral”.

Uruchomienie (z katalogu repozytorium):

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/scena.py -- --proba 40,100,250,345,560,749
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/scena.py -- --czekaj
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/scena.py -- --zloz
```

Pierwsze polecenie robi tylko kadry próbne PNG, drugie pełny render (czeka na zwolnienie blokady `.renderuje`,
potem samo składa `klip.mp4` i `kadr.jpg`), trzecie tylko składa film z gotowych klatek.
Są też `--od N --do M` (render części klatek) i `--skala 50` (połowa rozdzielczości do prób).

## Źródła i licencje

| Co | Źródło | Licencja |
|---|---|---|
| Rysunki w ramkach (13 sztuk) | rysunki Leszka Klimka z artykułu „Wielki uskok…”, `zrodlo/webacja/02uskok/`: `tektonika.gif`, `uskok.jpg`, `17std3.jpg`, `obliczenia.jpg`, `masy1.jpg`, `masy2.jpg`, `masy3.jpg`, `ollinstone.jpg`, `ollin.gif`, `temperatura.jpg`, `stonehenge.jpg`, `tikal.jpg`, `absyda.jpg` | materiał archiwum |
| Tekstura Ziemi | NASA Blue Marble 2002 (`_dane/blue-marble/`) | domena publiczna |
| Gwiazdy (5070 do 6 mag) | katalog HYG v4.4, David Nash / astronexus (`_dane/hyg/`) | CC BY-SA 4.0 |
| Czcionki | Georgia, Georgia Bold (systemowe) | – |

Pominąłem zdjęcia z artykułu (nie znamy ich autorów) i mapę `lodowiec.gif` (wygląda na obcą, z angielskimi podpisami).
Szczegóły pobranych danych są w `../_dane/ZRODLA.md`.

**Uwaga do opisu filmów:** gwiazdy pochodzą z katalogu HYG na licencji CC BY-SA 4.0, więc w opisie filmu trzeba podać:
„gwiazdy: katalog HYG v4.4 (astronexus), CC BY-SA 4.0; Ziemia: NASA Blue Marble”.

Opracowanie: jokerwader.
