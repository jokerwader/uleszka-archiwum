# Chefren SAR 3D: hipoteza obiegu wodno-powietrznego

Kopia projektu z dodaną animowaną warstwą „hipoteza: obieg wodno-powietrzny”.

**To trzecia kategoria w modelu, obok „potwierdzone” i „twierdzenia autorów”.** Warstwa jest naszą hipotezą
roboczą: pomocą do zrozumienia, czy budowa opisywana przez Biondiego i Malangę mogłaby w ogóle działać jako
urządzenie wodno-powietrzne. Nie jest rekonstrukcją i nie pochodzi od autorów. W modelu ma własny kolor
(turkusowy), własny prefiks nazw (`Hipo_`, `hipo_`) i etykietę „Hipoteza” w podglądzie.

Oryginał projektu (`piramida Biondi.blend` użytkownika oraz folder nadrzędny `chefren-sar/`) nie został zmieniony.
W kopii nie edytowano żadnego istniejącego obiektu ani materiału.

## Pliki

| Plik | Co to jest |
|---|---|
| `piramida-biondi-hipoteza.blend` | Kopia projektu z kolekcją `HIPOTEZA_OBIEG_WODNO_POWIETRZNY` i trzema ścieżkami NLA |
| `dodaj_hipoteze.py` | Skrypt, który dodaje obiekty, materiały i animacje, zapisuje plik i eksportuje `.glb` |
| `chefren-sar-hipoteza.glb` | Model z trzema animacjami glTF: `Wariant_A`, `Wariant_B1`, `Wariant_B2` (4,1 MB) |
| `podglad-3d-hipoteza.html` | Podgląd w przeglądarce (three.js r147): odtwarzanie, przełącznik wariantów, suwak czasu, opis fazy i ciśnienia, warstwa „hipoteza” |
| `zrzuty/` | Zrzuty ekranu faz wariantu B oraz wariantu A z podglądu |

Odtworzenie (z katalogu repozytorium, Blender 5.3):

```bash
blender -b grafiki/3d/chefren-sar/hipoteza/piramida-biondi-hipoteza.blend --python grafiki/3d/chefren-sar/hipoteza/dodaj_hipoteze.py -- --save --glb
```

Skrypt można uruchamiać wielokrotnie: przy każdym uruchomieniu usuwa tylko własne obiekty `Hipo_` i tworzy je od nowa.

## Warianty

Cykl ma 360 klatek (12 s przy 30 kl./s). Skrzynia południowa pracuje z przesunięciem o pół okresu.

**Wariant A, zrzut wody (środkowy kanał otwarty).** Woda schodzi po spiralach do skrzyni, wypierane powietrze
wychodzi środkiem szybu. Poziom wody rośnie od dna do stropu (klatki 1–336). Ciśnienie cały czas 1 bar.

**Wariant B, tłok wodny (środkowy kanał zanurzony 20 m poniżej stropu).**

| Faza | Klatki | Co się dzieje |
|---|---|---|
| 1. Napełnianie | 1–96 | Poziom wody 0 → 60 m, powietrze uchodzi środkiem, 1 bar |
| 2. Zamknięcie | 96 | Woda sięga dolnej krawędzi kanału; zostaje poduszka powietrza 20 m |
| 3. Sprężanie | 96–216 | Woda podnosi się w kanale do poziomu gruntu; ciśnienie rośnie do 65,8 bar, poduszka kurczy się do 0,30 m |
| 4. Tłoczenie | 216–264 | Zawór w stropie otwarty, sprężone powietrze idzie wąskim przewodem do góry, ciśnienie stałe |
| 5. Powrót wody | 264–360 | Dwa podwarianty, patrz niżej |

- **B1, magazyn:** z góry wtłaczane jest powietrze, które wypiera wodę ze skrzyni drugim szybem do zbiornika
  na powierzchni (`Hipo_B1_Zbiornik`, 300 × 300 × 6 m, położenie umowne, materiał „nieznane”).
- **B2, przepływ:** woda przechodzi dołem przez skrzynię i wraca drugim szybem do wylotu na powierzchni
  położonego 4 m niżej niż wlot. Strzałki w obu szybach jednocześnie: w jednym w dół, w drugim w górę.

Poniżej skrzyń nie ma żadnego odpływu.

Model ciśnienia (ten sam w skrypcie i w podglądzie): ciśnienie poduszki p = 1 bar + 1 bar na każde 10 m słupa wody
ponad lustro w skrzyni; wysokość poduszki = 20 m / p.

## Dodane obiekty (59) i materiały (6)

Materiały: `hipo_woda`, `hipo_powietrze_1bar`, `hipo_powietrze_sprezone`, `hipo_strzalki`, `hipo_nieznane`,
`hipo_zalozenie` (elementy, których istnienie jest założeniem hipotezy: kanał, przewód, zawór, wlot).

Obiekty wspólne dla wszystkich wariantów:

- `Hipo_Woda_skrzynia_polnocna`, `_poludniowa`: woda w skrzyni (skala w pionie od dna)
- `Hipo_Powietrze_skrzynia_polnocna`, `_poludniowa`: powietrze 1 bar nad wodą
- `Hipo_Strzalki_woda_1`…`_8`: woda schodząca po spiralach
- `Hipo_Strzalki_powietrze_1`…`_8`: powietrze uchodzące środkiem szybu

Tylko warianty B1 i B2 (`Hipo_B_`):

- `Hipo_B_Kanal_zanurzony_1`…`_8`: zanurzony koniec środkowego kanału (założenie)
- `Hipo_B_Woda_szyb_1`…`_8`: słup wody w środkowym kanale
- `Hipo_B_Poduszka_polnocna`, `_poludniowa`: poduszka sprężonego powietrza
- `Hipo_B_Przewod_sprezonego_polnocna`, `_poludniowa`: wąski przewód, średnica 1 m
- `Hipo_B_Zawor_polnocna`, `_poludniowa`: zawór w stropie skrzyni
- `Hipo_B_Strzalki_sprezone_polnocna`, `_poludniowa`: sprężone powietrze w górę (faza 4)
- `Hipo_B_Strzalki_powrot_polnocna`, `_poludniowa`: woda w górę szybem powrotnym (faza 5)

Tylko B1 (`Hipo_B1_`): `Zbiornik`, `Zbiornik_woda`, `Zbiornik_znak_zapytania`, `Przewod_do_zbiornika_polnocna`,
`_poludniowa`, `Strzalki_wtlaczanie_polnocna`, `_poludniowa`.

Tylko B2 (`Hipo_B2_`): `Strzalki_dno_polnocna`, `_poludniowa`, `Wlot_polnocna`, `_poludniowa`, `Wylot_polnocna`,
`_poludniowa`.

## Przyjęte założenia

Żadne z nich nie pochodzi od autorów ani ze specyfikacji; trzeba je było przyjąć, żeby animacja była kompletna.

1. „Środkowy kanał” to cała rura szybu. Model autorów nie ma osobnego kanału w środku.
2. Słup wody w kanale ma promień 4,2 m (szyb 5,5 m).
3. Do każdej skrzyni należą cztery szyby odczytane ze sceny: południowa 1, 2, 5, 6; północna 3, 4, 7, 8.
4. Szyb powrotny w fazie 5 to szyb wschodni bliższy środka (6 i 7). Szyb wlotowy w B2 to szyb po przekątnej (1 i 4).
5. Wąski przewód sprężonego powietrza i zawór są w środku stropu skrzyni; przewód biegnie pionowo do poziomu gruntu.
6. W B1 powietrze wtłaczane w fazie 5 idzie tym samym wąskim przewodem, w dół.
7. W B1 woda z trzech pozostałych kanałów opada razem z wodą w skrzyni; kanał powrotny zostaje pełny.
8. W B1 zbiornik stoi na wschód od piramidy. Jego poziom liczony jest z bilansu wody obu skrzyń (1,6–5,9 m);
   woda w kanałach nie jest w bilansie.
9. W B2 skrzynia i kanały zostają pełne przez całą fazę 5; słup w kanale powrotnym kończy się 4 m niżej.
10. W fazie 3 woda podnosi się we wszystkich czterech kanałach jednocześnie i liniowo w czasie.
11. W fazie 4 poduszka maleje od 0,30 m do zera przy stałym ciśnieniu.
12. Wariant A kończy się pełną skrzynią w klatce 336; potem animacja wraca do początku bez pokazywania odpływu.
13. Skok spirali 8 m wzięty ze skryptu budującego model (z siatki nie da się go pewnie odczytać).
    Początkowy kąt spirali odczytany z siatki.
14. Strzałki pokazują kierunek, nie prędkość. Na spirali przesuwają się o 3 zwoje na cykl.

## Gdzie geometria modelu nie pozwala zamknąć obiegu

1. **Wlot wody do skrzyni.** Spirale biegną na zewnątrz rur szybów (promień 9 m wobec 5,5 m) i kończą się na stropie
   skrzyni. Model nie ma otworu, którym woda ze spirali wchodziłaby do środka.
2. **Źródło wody u góry.** Szyby zaczynają się na poziomie podstawy piramidy. Nic w modelu nie doprowadza tam wody.
3. **Woda według autorów.** Model twierdzeń ma płaszczyznę wody na ok. 470 m. Gdyby to był poziom wód gruntowych,
   skrzynie na 648–728 m byłyby stale zalane. Hipoteza tę płaszczyznę pomija.
4. **Brak odpływu.** Skrzynie nie mają żadnego wyjścia poza czterema szybami. Dlatego w fazie 5 woda może wrócić
   tylko szybem do góry (B1, B2).
5. **B1: zbiornik się nie mieści.** Zbiornik 300 × 300 m postawiony obok piramidy wystaje 65 m poza blok gruntu modelu,
   a przewody do niego biegną pod podstawą piramidy. Do wypchnięcia wody 648 m w górę potrzeba powietrza o ciśnieniu
   co najmniej ok. 66 bar.
6. **B2: cykl się nie domyka.** Skrzynia się nie opróżnia, więc po fazie 5 nie ma naturalnego powrotu do fazy 1.
   Animacja po prostu zaczyna od nowa. Wylot „kilka metrów niżej” wypada poniżej poziomu gruntu, bo wszystkie szyby
   kończą się w modelu na tej samej wysokości.
7. **Wariant A.** Po napełnieniu skrzyni woda nie ma dokąd odejść, więc zrzut jest jednorazowy.
8. **Wąski przewód.** Nie ma w modelu odpowiednika; jego górny koniec wypada pod podstawą piramidy, wśród
   korytarzy z modelu autorów.

## Ograniczenia techniczne

- Przez eksport glTF przechodzą przesunięcia, obroty i skale obiektów. Animacja materiałów wymagałaby rozszerzenia
  `KHR_animation_pointer`, którego three.js r147 nie obsługuje. Dlatego poziom wody to skala w pionie, „znikanie”
  to skala bliska zera, a powietrze 1 bar i sprężone to dwa osobne obiekty.
- Eksporter usuwa kanały, które w danej animacji są stałe. Obiekty należące tylko do części wariantów podgląd
  chowa po nazwie (`Hipo_B_`, `Hipo_B1_`, `Hipo_B2_`).
- W Blenderze domyślnie odtwarza się ścieżka `Wariant_B1`; pozostałe dwie są wyciszone w edytorze NLA.

Autor: jokerwader (uleszka.net).
