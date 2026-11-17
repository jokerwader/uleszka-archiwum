# tikal-przelot / rentgen

Tu leży scena aktualnego klipu `tikal-przelot` (styl „rentgen”): `scena.py`. Opis klipu, źródła i licencje są w `../README.md`.

- `scena.py`: wczytuje geometrię budowli z `../scena.py` (bez zmian w tamtym pliku) i pokazuje ją jako półprzezroczyste
  bryły ze świecącymi krawędziami, z chmurą punktów zamiast dżungli. Bez argumentów robi pełny render do `../klip.mp4`
  i `../kadr.jpg` (blokada `.renderuje`). Kadry próbne: `-- probne 1,30,140,255,290,400 blekit` (albo `zloto`).
  Klatki trafiają do `../_klatki/rentgen/` (folder ignorowany przez git).
- `arkusz-probny.jpg`: pierwsza próba stylu z 16.11.2026, przed poprawkami (2 kolumny × 4 wiersze): wariant błękitny
  w klatkach 1, 45, 150, 270, 400 i wariant złoty w klatkach 45, 150, 400. Użytkownik wybrał błękitny.

## Co zmieniono po próbie

- Skan rusza od pierwszej klatki (linia jest już na schodach Świątyni II) i jest mały napis „rekonstrukcja 3D w stylu skanu lidarowego”.
- Grobowiec pod Świątynią I: niski przelot obok piramidy, linia pionu od komór na szczycie i tunel archeologów od stóp schodów.
- Napisy są większe, mają ciemny obrys i wiszą wysoko nad budowlami; „90°” jest czytelne.
- Wnętrza sprawdzone w artykułach Wikipedii (tabela w `../README.md`): dodany Pochówek 85 pod świątynią 26, komora Świątyni V
  ma wymiary ze źródła, usunięte sformułowania, których źródła nie potwierdzają.

## Jak działa styl

- Krawędzie mają stałą grubość na ekranie (Geometry Nodes: krawędzie zamieniane na rurki skalowane odległością od kamery).
- Bryły świecą addytywnie (jaśniej tam, gdzie powierzchnia jest widziana pod ostrym kątem), więc przez ściany widać wnętrza.
- Punkty koron i gruntu to wierzchołki siatek zamienione na punkty; jasność zależy od atrybutu `jas` i od linii skanu.
- Linia skanu to wartość `skan` (położenie x) we wszystkich materiałach: na wschód od niej wszystko jest odsłonięte.
