# Wstęp odcinka (30 s, pod zapowiedź i muzykę z nagrania)

Pierwsze 30 s każdego odcinka to zapowiedź: lektor czyta ją na tle muzyki, która jest już w nagraniu.
Do tej pory przez cały ten czas stała w filmie jedna nieruchoma plansza z okładką. Zastąpi ją ta animacja.
Animacja jest **wspólna dla wszystkich odcinków**. Tytuł konkretnego odcinka nakłada na nią `wideo.ts` w pustym środku kadru (14,3–25 s).

## Czas (odcinek 2, `podcast/02-wielki-uskok/mowa.jsonl`; w odcinku 1 obwiednia dźwięku jest prawie taka sama)

| s | klatka | lektor |
|---|---|---|
| 0,0 | 0 | „Uwierz we własny rozum.” |
| 1,9 | 47 | „Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi.” |
| 6,5 | 163 | „Jego teksty ze strony uleszka.net z lat 2004–2007,” |
| 12,7 | 318 | „czytane bez zmian.” |
| 14,3 | 358 | „Odcinek drugi: Wielki uskok…” (tu `wideo.ts` nakłada tytuł odcinka) |
| 20,0 | 500 | „Czyta lektor wygenerowany przez sztuczną inteligencję.” |
| ok. 25 | 625 | koniec mowy; 25–30 s muzyka wygasa |
| 30 | 750 | lektor zaczyna czytać artykuł |

Mocniejsze akcenty muzyki, zmierzone na miksie z głosem, wypadają mniej więcej w 0, 4, 10, 13, 17 i 20 s.
Dokładne czasy zmierzymy na czystej muzyce, którą podeśle użytkownik.

## Obraz

1. **0–47:** z ciemności złoty błysk i tytuł „Uwierz we własny rozum” (Georgia Bold, złoty gradient).
2. **47–163:** spokojnie i z szacunkiem: ciepłe światło, napis „w hołdzie śp. Leszkowi Wiktorowi Klimkowi”. Bez ludzi i bez portretu.
3. **163–358:** przelot wśród unoszących się w przestrzeni rysunków Leszka z artykułów (`zrodlo/webacja/02uskok/`, w złotych ramkach), napis „uleszka.net · 2004–2007”.
   Przy „czytane bez zmian” obrazy układają się w porządek.
4. **358–625:** spokojne, szerokie ujęcie (Ziemia, niebo) z **pustym środkiem kadru** na tytuł odcinka.
   Od klatki 500 mały napis „lektor: głos wygenerowany przez AI”.
5. **625–750:** kamera odpływa w granatową ciemność. Ostatnia klatka ma być ładna, nie czarna, bo `wideo.ts` może ją przytrzymać do planszy artykułu.

Styl jak w `ZASADY.md`. Bez ludzi.

## Pliki

`scena.py`, `klip.mp4` (1920×1080, 25 kl./s, 750 klatek, CRF 18, **bez dźwięku**), `kadr.jpg`, `README.md`. **Bez `klip.json`.**
Wstęp wstawia `wideo.ts` w miejsce planszy zapowiedzi i sam dokłada tytuł odcinka.
