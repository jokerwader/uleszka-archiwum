# ziemia-z-kosmosu

Ziemia i Księżyc w prawdziwej skali rozmiarów i odległości. Rozdział 13 „Czy możemy spać spokojnie?”, zdanie:
„Jedynym rodzajem ratunku jest ucieczka w kosmos, a takiej możliwości jeszcze długo mieć nie będziemy”. 16 s.
Rodzaj: `ilustracja` (odległości to fakty).

## Co widać

1. Ziemia z bliska (Afryka i Europa), po czym kamera odsuwa się coraz dalej.
2. Ziemia maleje do małej kulki, w kadr wchodzi Księżyc. Pojawia się tytuł „Ziemia i Księżyc w prawdziwej skali”
   i przerywana linia z podpisem „384 400 km · 3 dni lotu”.
3. Na końcu podpis: „Do Marsa w najlepszym razie 55 mln km: ponad 140 razy dalej, ok. 7 miesięcy lotu”.

## Skąd liczby

- Średnia odległość Księżyca 384 400 km = 60,3 promienia Ziemi; promień Księżyca = 0,2727 promienia Ziemi. Obie wielkości w skali.
- „3 dni lotu”: tyle leciały na Księżyc statki Apollo.
- Mars zbliża się do Ziemi najbardziej na ok. 55–56 mln km (np. 55,8 mln km w 2003 r.), czyli ok. 143 razy dalej niż Księżyc.
  Sondy lecą tam zwykle ok. 7 miesięcy.
- Oświetlenie Ziemi i Księżyca jest umowne (jedno stałe Słońce z lewej), Księżyc to kula z szumem, bez zdjęcia.

## Sprawdzenie (audyt 16.11.2026)

Liczby w kadrze sprawdzone: 384 400 km / 6378 km = 60,27 promienia Ziemi; promień Księżyca 1737 km = 0,2727 promienia
Ziemi (6371 km); najmniejsza odległość Marsa 55,76 mln km (27 sierpnia 2003 r.), czyli 145 razy dalej niż Księżyc;
Apollo 11 leciał do orbity Księżyca 76 godzin. Nie są policzone (i tak było od początku): kierunek Słońca, obrót tła
gwiazd i strona Ziemi zwrócona do kamery; nie odpowiadają one żadnej konkretnej dacie.

## Źródła i licencje

- Tekstura Ziemi: NASA Blue Marble 2002 (domena publiczna), `_dane/blue-marble/`.
- Gwiazdy w tle: katalog HYG v4.4 (CC BY-SA 4.0), `_dane/hyg/` (obrócone dowolnie, to tylko tło).
- Reszta: od zera w `scena.py`.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/ziemia-z-kosmosu/scena.py`
(400 klatek, EEVEE, 24 próbki). Kadry próbne: `-- --proba 1,150,230,400`.
