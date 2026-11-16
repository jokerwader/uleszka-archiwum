# tiamat-zderzenie

Ilustracja **hipotezy** do rozdziału 03 „Laik i trzęsienia ziemi”. 18 s.

Rodzaj: `hipoteza`. To hipoteza Zecharii Sitchina (odczytanie sumeryjskiego mitu o walce Marduka z Tiamat jako
kosmicznej katastrofy), na której Leszek opiera dalszy wywód. **Nauka jej nie przyjmuje**: według astronomii
pas planetoid to materiał, z którego nigdy nie powstała planeta (przeszkadzała grawitacja Jowisza), a nie szczątki
rozbitej planety, a Ziemia powstała na swojej orbicie.

## Co widać (według tekstu Leszka)

1. Układ słoneczny z ukosa: Słońce, Merkury, Wenus, Mars, Jowisz, a między Marsem a Jowiszem Tiamat (praZiemia),
   niebieska, bo „cała ponoć była pokryta płaszczem wody”. Ziemi jeszcze nie ma. Napis „Tiamat i Marduk według Z. Sitchina”.
2. Z zewnątrz nadlatuje Marduk (obce ciało, czerwonawe, z jasnym śladem toru) i uderza w Tiamat. Błysk.
3. Tiamat maleje (traci część masy) i odsłania się na niej gorący płaszcz w miejscu, gdzie zniknęła skorupa
   (tekst: „widoczna jest tylko utrata ponad 2/3 skorupy”). Marduk leci dalej.
4. Gruz rozchodzi się po dawnej orbicie Tiamat i zamyka się w pierścień: „pas planetoid”.
5. Tiamat zostaje zepchnięta do wnętrza układu, na przerywaną złotą „dzisiejszą orbitę Ziemi”. Rana stygnie
   i zalewa ją woda, pojawiają się białe chmury (tekst mówi o parze wodnej, która utworzyła pierwszą atmosferę).
   Podpis zmienia się z „Tiamat (praZiemia)” na „Ziemia”, u góry „praZiemia zepchnięta na dzisiejszą orbitę”.

## Uproszczenia

- Odległości i wielkości nie są w skali: orbity są zagęszczone (promienie mniej więcej jak pierwiastek z odległości),
  planety powiększone, a ruch po orbitach mocno spowolniony i wyrównany (wewnętrzne planety krążą tylko trochę szybciej).
- Tor Marduka i miejsce zderzenia są umowne – tekst ich nie opisuje.
- Gwiazdy w tle są losowe (tło, nie prawdziwe niebo).
- Marduk po zderzeniu odlatuje powoli i jeszcze pod koniec klipu widać go przy lewym dolnym brzegu kadru.
- Pominięte z tekstu: „przybranie na wadze” Jowisza i powstanie komet.

## Dane i licencje

- Bez danych zewnętrznych: cała scena jest zbudowana w skrypcie.
- Czcionki napisów: Arial Bold, Georgia (systemowe).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tiamat-zderzenie/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tiamat-zderzenie/scena.py -- --proba 1,180,238,300,450
```

Ruch planet, gruzu (650 bryłek w jednej siatce) i kamery liczy funkcja wywoływana przy każdej klatce
(`frame_change_pre`). Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 450 klatek: 304 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
