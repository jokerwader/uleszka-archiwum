# teotihuacan-aleja

Ożywiony szkic Leszka `zrodlo/webacja/02uskok/teotihuacan.jpg`: plan Teotihuacan z Aleją Zmarłych odchyloną od północy.
Rozdział 09 „Jak to wygląda w praktyce?”. 16 s. Rodzaj: `rysunek-leszka`.

Tekst Leszka: „Tutaj kierunek zdaje się narzucać szeroka aleja nazwana, nie wiedzieć czemu, aleją zmarłych. Jest odchylona
od kierunku dzisiejszej północy o około 18° w kierunku wschodnim.” Klip pojawia się przy zdaniu „Ja sądzę, że przyczyny
należy szukać w tych 18 stopniach.”

## Co widać

1. Szkic leży jak plansza: miętowe tło, czarne budowle z białym środkiem, biała aleja. Na szkicu północ jest po prawej.
2. Budowle wyrastają z planu (piramidy schodkowe, małe budowle jako klocki).
3. Wzdłuż alei rośnie czerwona linia przerywana ze szkicu, potem granatowa strzałka „Pn”.
4. Złoty łuk łączy strzałkę północy z aleją, podpis „ok. 18°”. Kamera schodzi z widoku z góry do widoku z ukosa.

## Wierność szkicowi i zastrzeżenia

- Budowle są odczytane z pikseli szkicu (plamy czarnych pikseli zamienione na kwadraty równoległe do alei).
  Cytadela (cienki obrys) i grupa trzech stykających się platform przy alei są wpisane ręcznie według szkicu.
- Wysokości budowli są umowne: szkic ich nie podaje.
- Kąt między strzałką „Pn” a czerwoną linią zmierzony na szkicu wynosi ok. 19,4°. Podpis „ok. 18°” pochodzi z tekstu
  Leszka. Według dzisiejszych pomiarów oś Teotihuacan jest odchylona o ok. 15,5° na wschód od północy; klip tej liczby
  nie pokazuje.
- Dodane od nas (nie ma ich na szkicu): złoty łuk z „ok. 18°” oraz białe nazwy „Aleja Zmarłych”, „Piramida Słońca”,
  „Piramida Księżyca”, „Świątynia Quetzalcoatla” (nazwy z tekstu rozdziału).

## Dane i licencje

- Szkic: Leszek Klimek, uleszka.net (archiwum). Geometria wykonana od zera w `scena.py`, bez danych z zewnątrz.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/teotihuacan-aleja/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/teotihuacan-aleja/scena.py -- --proba 1,130,250,400
```
