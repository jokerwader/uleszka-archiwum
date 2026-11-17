# epoki-lodowcowe

Temperatura z ostatnich 800 tys. lat zapisana w lodzie Antarktydy, pokazana jako grzbiet w 3D. Rozdział 10
„Co wyszło z obliczeń?”, pytanie: „Czy takich epok lodowcowych kończących się z "wielkim hukiem" było na Ziemi kilka?”. 17 s.
Rodzaj: `ilustracja` (dane pomiarowe). Klip odpowiada tylko na pierwszą część pytania: epok lodowcowych było wiele.
O tym, czy kończyły się „wielkim uskokiem”, niczego nie twierdzi.

## Co widać

1. Kamera leci wzdłuż wykresu od 800 tys. lat temu do dziś. Oś pozioma to czas (podziałka co 100 tys. lat),
   wysokość to odchylenie temperatury od średniej z ostatniego tysiąclecia. Kolory: niebieski = zimno, złoty = ciepło.
2. Złota linia przerywana: temperatura dzisiejsza. Niebieska linia przerywana: o 9°C zimniej (tyle wynosiło
   ochłodzenie w szczycie epok lodowcowych nad Antarktydą).
3. Nad najzimniejszym punktem każdej epoki lodowcowej pojawia się numer 1–8, a licznik u góry rośnie.
4. Na końcu widok całości i podpis: „8 epok lodowcowych; ostatnia skończyła się ok. 11,7 tys. lat temu”.

## Skąd liczby

- Dane: rdzeń lodowy EPICA Dome C (Antarktyda), 5800 próbek deuteru przeliczonych na temperaturę, skala wieku EDC3.
  Plik `_dane/epica/EPICA_DomeC_deuter_temperatura.tab` (opis w `_dane/ZRODLA.md`).
- Wykres: dane przeliczone na równy krok 500 lat i lekko wygładzone (średnia z 1,5 tys. lat).
- Najzimniejsze punkty epok skrypt wyszukuje sam w ośmiu przedziałach czasu (średnia z 3,5 tys. lat):
  ok. 744, 640, 546, 438, 342, 272, 156 i 26 tys. lat temu, każdy o 8–10°C zimniejszy niż dziś.
  Przedziały odpowiadają zimnym okresom, które nauka numeruje jako stadia izotopowe 18, 16, 14, 12, 10, 8, 6 i 2–4.
- Koniec ostatniej epoki lodowcowej ok. 11,7 tys. lat temu to przyjęta granica plejstocenu i holocenu.
  Leszek pisze o ok. 12,5 tys. lat – to ten sam okres gwałtownego ocieplenia.
- Temperatura dotyczy Antarktydy, nie całej Ziemi (globalne zmiany były mniej więcej o połowę mniejsze).

## Źródła i licencje

- Jouzel, J., Masson-Delmotte, V. (2007): „EPICA Dome C Ice Core 800KYr deuterium data and temperature estimates”,
  PANGAEA, https://doi.org/10.1594/PANGAEA.683655 (dodatek do: Jouzel i in., Science 317, 793–797), licencja CC BY 3.0.
  Autorów danych wymienia napis w kadrze; w opisie filmu trzeba podać to samo źródło.
- Geometria wykresu i napisy: wykonane od zera w `scena.py`. Czcionka Georgia (Windows), tylko do renderu.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/epoki-lodowcowe/scena.py`
(425 klatek, EEVEE, 24 próbki, ok. 4 min). Kadry próbne: `-- --proba 1,150,300,425`.
