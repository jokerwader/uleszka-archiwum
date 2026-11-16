# kalendarz-majow-2012

Koła kalendarza Majów zazębione jak tryby i data Długiej Rachuby 13.0.0.0.0. Rozdział 13 „Czy możemy spać spokojnie?”,
fragment o liczeniu czasu „od początku jakiejś epoki, jakiegoś punktu zerowego” i dacie „23 grudnia 2012 r.”. 20 s.
Rodzaj: `ilustracja` (działanie kalendarza to fakt; o znaczeniu daty klip nic nie twierdzi).

## Co widać

1. Trzy koła, każde przesuwa się o jeden ząb na dzień:
   - koło 13 liczb Tzolk'in – liczby 1–13 zapisane cyframi Majów (kropka = 1, kreska = 5),
   - koło 20 nazw dni Tzolk'in (Imix, Ik', Ak'b'al … Ajaw),
   - koło 365 dni Haab' – widać tylko jego brzeg: numery dni 0–19 i nazwy miesięcy (18 × 20 dni + 5 dni Wayeb').
   Promienie są w proporcji liczby zębów 13 : 20 : 365, więc zęby naprawdę do siebie pasują, a koła obracają się
   z prawdziwym przełożeniem (sąsiednie w przeciwne strony).
2. Złote trójkąty wskazują miejsca odczytu. Po prawej odczyt na bieżąco: data Tzolk'in, data Haab' i licznik
   Długiej Rachuby. Koła startują 60 dni wcześniej (12.19.19.15.0 = 9 Ajaw 3 Sak'), kręcą się dzień po dniu,
   przyspieszają i zwalniają, aż do 13.0.0.0.0 = 4 Ajaw 3 K'ank'in.
3. Na końcu data 13.0.0.0.0 zapisana cyframi Majów (13 = trzy kropki nad dwiema kreskami, 0 = muszla),
   z nazwami pozycji b'ak'tun, k'atun, tun, winal, k'in, i odpowiednik w naszym kalendarzu.

## Data w naszym kalendarzu

13.0.0.0.0 to 21 grudnia 2012 r. według najczęściej używanego przelicznika (stała GMT 584283) albo 23 grudnia 2012 r.
według przelicznika 584285 – tę drugą datę podaje tekst Leszka. Klip pisze „21–23 grudnia 2012, zależnie od przyjętego
przelicznika”. Obie daty dają ten sam dzień kalendarzowy Majów 4 Ajaw 3 K'ank'in, bo różnią się tylko przyjętym
punktem zaczepienia w naszym kalendarzu (wszystkie obliczenia dni w `scena.py` są względem 13.0.0.0.0).

## Glify

Prawdziwych glifów dni i miesięcy nie odtwarzamy (to rysunki o złożonym kształcie, a nie znaleźliśmy kompletu
na wolnej licencji w jednym stylu). Zastępują je nazwy w nowej pisowni Akademii Języków Majańskich Gwatemali.
Cyfry Majów (kropki, kreski, uproszczona muszla zera) narysowano od zera w `scena.py`.

## Źródła i licencje

- Budowa kalendarza (Tzolk'in 13 × 20, Haab' 18 × 20 + 5, Długa Rachuba 20/18/20/20, data 13.0.0.0.0 = 4 Ajaw 3 K'ank'in):
  wiedza ogólna, sprawdzona rachunkiem w `scena.py`.
- Geometria kół, tekstury (szum Blendera) i cyfry: wykonane od zera, bez cudzych grafik.
- Czcionki: Arial, Georgia (Windows), tylko do renderu.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/kalendarz-majow-2012/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/kalendarz-majow-2012/scena.py -- --proba 120,500
```
