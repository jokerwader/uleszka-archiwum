# Nowe odkrycia do Atlasu Leszka – instrukcja dla agenta

Na każdej karcie miejsca w atlasie (`https://uleszka.net/atlas/<miejsce>.html`) jest sekcja **„Najnowsze badania”**:
oś czasu z odkryciami i badaniami z lat **2007–dziś**, które dotyczą pytań stawianych przez Leszka Klimka na uleszka.net.
Dane są w jednym pliku: [`odkrycia.json`](odkrycia.json). Po zmianie: `npx tsx scripts/atlas.ts`.

## Zadanie

Dla wskazanych miejsc znajdź **2–6 najważniejszych odkryć lub badań od 2007 roku** (dla bardzo popularnych miejsc wolno więcej – strona ma kalendarz lat i zwijanie; liczy się jakość, nie liczba). Patrz oczami Leszka: co by go zainteresowało?
Np. nowe datowania, odkrycia pod ziemią, badania technik obróbki kamienia, ślady katastrof, odczytane inskrypcje, skanowanie (LiDAR, mion, georadar).
Ale opisuj **rzetelnie, jak dziennikarz naukowy**, a nie jak Leszek: co odkryto, kto, gdzie i na ile jest to pewne.

1. Najpierw sprawdź, co pisał Leszek o tym miejscu: serwer MCP archiwum (`list_places`, `search`, `read_article`) albo karta miejsca w atlasie.
2. Szukaj w źródłach: publikacje naukowe (Nature, Science, PNAS, Antiquity, Journal of Archaeological Science…), komunikaty uczelni i instytutów,
   ministerstwa i służby archeologiczne, rzetelne media (BBC, Smithsonian, National Geographic, Live Science, Nauka w Polsce PAP).
3. **Każdy adres URL otwórz i sprawdź**, że działa i mówi to, co piszesz. Nie podawaj źródeł z pamięci.
4. Nie przepisuj artykułów – pisz własnymi słowami, 2–4 zdania po polsku.
5. Sensacyjne doniesienia bez potwierdzenia oznaczaj jako `"doniesienie"` albo `"hipoteza"` i napisz, kto je kwestionuje.

## Format

Klucz to `id` miejsca z `atlas/atlas.json` (taki jak w adresie karty, np. `sacsayhuaman`, `piramidy-w-gizie`, `puma-punku`).

```json
{
  "sacsayhuaman": [
    {
      "rok": "2019",
      "tytul": "Krótki tytuł po polsku",
      "opis": "2–4 zdania: co odkryto lub zbadano, kto (instytucja), jaką metodą i na ile jest to pewne.",
      "pewnosc": "potwierdzone | publikacja naukowa | doniesienie | hipoteza",
      "zrodla": [
        { "nazwa": "Nazwa źródła, rok", "url": "https://…" }
      ],
      "artykul": "id artykułu Leszka, do którego odkrycie nawiązuje (opcjonalnie, np. 09tiahu/tiahu)",
      "cytat_leszka": "dosłowny cytat z tego artykułu – pytanie lub teza, do której odkrycie się odnosi (opcjonalnie)"
    }
  ]
}
```

- `rok` – jeden rok: odkrycia albo publikacji. Gdy badania trwały kilka lat (np. 2017–2024), wpisz rok końcowy (`"2024"`).
- `zrodla` – co najmniej jedno, najlepiej dwa niezależne.
- `cytat_leszka` musi być **słowo w słowo** z artykułu Leszka. Skrypt budujący stronę sprawdza to i pomija cytat, którego nie ma w tekście.
- Kolejność wpisów: od najstarszego do najnowszego.

## Kolejność miejsc

Najpierw miejsca z najbliższych odcinków podcastu (harmonogram: `podcast/harmonogram.json`, karta miejsca pokazuje datę premiery)
i najczęściej opisywane przez Leszka: Piramidy w Gizie, Wielki Sfinks, Tiahuanaco, Puma Punku, Sacsayhuamán, Machu Picchu,
Teotihuacan, Stonehenge, Baalbek, Abydos i Osireion, Ollantaytambo, Cusco i Coricancha, Wyspa Wielkanocna, Angkor, Linie z Nazca (gotowe).

Druga partia – Polska: Biskupin, Piramidy kujawskie, Jaskinia Maszycka, Ostrów Lednicki, Strzelno, Kolegiata w Tumie, Ślęża, Wawel,
Truso, Zamek w Malborku, Krzyżtopór, Zamek Ogrodzieniec, Zamek w Olsztynie, Zamek w Bobolicach, Zamek w Chęcinach.
Pozostałe polskie miejsca: Zamek w Mirowie, Ostrężniku, Proboszczowicach, Czorsztynie, Gniewie, Bytowie, Nidzicy, Zamek Bolczów.

Potem: wszystkie pozostałe miejsca z `atlas/atlas.json`, najpierw te z najbliższych odcinków podcastu (`podcast/harmonogram.json`),
potem te z największą liczbą artykułów Leszka (pole `artykuly`), na końcu reszta.

Wskazówki: przy polskich miejscach dobrze sprawdzają się Nauka w Polsce (PAP), komunikaty uczelni, muzeów i NID.
Nature, Science, Smithsonian i ScienceDirect często blokują pobieranie – wtedy szukaj komunikatu uczelni, PMC albo arXiv.

## Stan (15 listopada 2026)

Wpisy ma 176 ze 186 miejsc (554 wpisy). Druga runda („mniej znane znaleziska”) przeszukała prasę regionalną, muzea, konserwatorów,
ministerstwa, roczniki i sprawozdania z konferencji dla miejsc z 0–1 wpisem i dla Ślęży.
Nadal bez wpisów – brak sprawdzalnych badań po 2007 r. albo tylko źródła turystyczne i sensacyjne: Zawijet el-Arjan, Kerak,
zamek w Ostrężniku, zamek Bolczów, Qenko, Tambomachay, Aramu Muru, Ingapirca, Khajuraho, odcisk z Antelope Spring.
Tropy na przyszłość: studnia na dziedzińcu zamku w Bytowie (Kajkowski, Szczepanik, Acta Archaeologica Pomoranica 5, 2015),
misja florencka w Keraku (Jordan Times 2017–2019), konserwacja ruin w Mirowie i Bobolicach (Kurek 2024).
Wiele stron (gp24.pl, echodnia.eu, Jordan Times, ScienceDirect, Springer) blokuje automatyczne pobieranie – warto otworzyć je w przeglądarce.

Nie są źródłem: Wikipedia, Ancient Origins, Gaia, History Channel i podobne serwisy sensacyjne, strony biur podróży.
