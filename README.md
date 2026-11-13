# Uleszka.net – „Uwierz we własny rozum”

### Archiwum strony, z którą można porozmawiać

> 👉 **Prosta instrukcja dla każdego, bez GitHuba: [jokerwader.github.io/uleszka-archiwum](https://jokerwader.github.io/uleszka-archiwum/)**

**uleszka.net** to polska strona internetowa z lat ok. 2004–2007. Na długo przed erą blogów i mediów społecznościowych zadawała pytania, których w szkole nikt nie zadawał. Kto zbudował piramidy i Tiahuanaco? Czy potop był jeden? Gdzie leżała Atlantyda? Dlaczego oficjalna historia ma tyle luk? Pisała też o zapomnianej medycynie naturalnej i o tym, co jemy.

Dla wielu czytelników była to pierwsza strona, która pokazała, że o te sprawy w ogóle można pytać. Stała się inspiracją dla wielu późniejszych stron i blogów o podobnej tematyce, a jej teksty do dziś są przedrukowywane w sieci.

Strona zniknęła z internetu. To repozytorium zachowuje **całość jej treści w niezmienionej formie**. Do tego daje możliwość, której wtedy nie było: **rozmowy z archiwum przez sztuczną inteligencję**. Można pytać o teksty, sprawdzać historię i porównywać tezy autora z tym, co wiemy dziś.

**To archiwum jest ukłonem w stronę autora, Leszka Klimka, i próbą przełożenia jego pracy na język nowych technologii.** Jego teksty pozostają nietknięte. Sztuczna inteligencja pozwala dziś z nimi rozmawiać, porównywać je z tym, co wiemy po 20 latach, i sprawdzać źródła, do których sięgał.

> „Zwrócić na coś uwagę większości, znaczy pomóc zdrowemu rozsądkowi wpaść na właściwy ślad” – G. E. Lessing, motto strony

### Co jest w archiwum

| | |
|---|---|
| 📄 **148 stron oryginału** | wszystkie artykuły w niezmienionej formie, ze zdjęciami ([katalog](KATALOG.md)) |
| 🧭 **Opracowania** | dla każdego artykułu: streszczenie, tezy autora z dosłownymi cytatami, tematy, osoby, miejsca i daty ([spis](opracowania/README.md)) |
| 🖼️ **Opisy 1714 zdjęć** | co przedstawia każde zdjęcie, mapa i rysunek, razem z przepisanymi napisami |
| 📚 **Biblioteka 30 dawnych dzieł** | pełne teksty źródeł, na które powołuje się autor: Platon, Herodot, Księga Rodzaju, Owidiusz, Księga Henocha, Popol Vuh, Gilgamesz, Mahabharata i in. ([biblioteka](biblioteka/README.md)) |
| 🏛️ **17 tekstów w językach oryginału** | greka (Platon, Herodot, Iliada, Strabon, Argonautyki), łacina (Owidiusz, Pliniusz, Cezar, Apulejusz, Augustyn), hebrajski (Księga Rodzaju), dawny francuski (Nostradamus, Calmet) i sanskryt (Ramajana, Mahabharata) – z numeracją miejsc, np. Platon [24e], Herodot [2.148], Księga Rodzaju [6:4]; AI może je przetłumaczyć i porównać z przekładem |
| 🔎 **Wyszukiwanie po znaczeniu** | pytanie „katastrofy z kosmosu” znajdzie teksty o kometach i Tiamat, choć tych słów w pytaniu nie ma |

Opracowania i opisy zdjęć przygotowała sztuczna inteligencja. Są oddzielone od oryginału, który pozostał nietknięty. Każdy cytat w opracowaniach jest automatycznie sprawdzany: musi występować w artykule dosłownie.

---

## 💬 Jak porozmawiać z archiwum

Wybierz sposób, który ci pasuje:

| Sposób | Dla kogo | Instalacja |
|---|---|---|
| [A. Własny GPT w ChatGPT](#a-chatgpt--własny-gpt) | użytkownicy ChatGPT | nie, tylko wgranie plików |
| [B. Projekt w Claude](#b-claude--projekt) | użytkownicy Claude.ai | nie, tylko wgranie plików |
| [C. Serwer MCP w Claude Desktop lub Claude Code](#c-claude-desktop--claude-code-serwer-mcp) | działa bez internetu, na własnym komputerze | tak, Node.js |
| [D. Serwer MCP pod adresem internetowym](#d-serwer-mcp-pod-adresem-internetowym) | **najprościej i najpełniej:** Claude.ai i ChatGPT, wszystkie narzędzia | nie, wystarczy wkleić adres |

> **Najszybciej:** w Claude.ai dodaj konektor z adresem `https://uleszka-mcp-production.up.railway.app/mcp` (szczegóły w [punkcie D](#d-serwer-mcp-pod-adresem-internetowym)).

### A. ChatGPT – własny GPT

1. Pobierz pliki z folderu [`dla-ai/`](dla-ai): kliknij plik, a potem *Download raw file*.
   - `00`–`06`: archiwum strony. Każdy dział to jeden plik, a `06-opracowania.md` zawiera streszczenia i tezy wszystkich artykułów. Razem ok. 5 MB.
   - `07`–`17`: biblioteka, czyli pełne teksty 30 dawnych dzieł, na które powołuje się autor (Platon, Herodot, Księga Henocha, Popol Vuh, Mahabharata…). Są potrzebne, gdy AI ma sprawdzać, co naprawdę mówi źródło. Razem ok. 32 MB.
2. W ChatGPT: **Odkrywaj GPT → Utwórz → Konfiguruj**.
3. W polu **Instrukcje** wklej tekst z [docs/instrukcje-asystenta.md](docs/instrukcje-asystenta.md).
4. W sekcji **Wiedza** wgraj pliki z `dla-ai/`. Wszystkie 19 mieszczą się w limicie ChatGPT (20 plików). Jeśli chcesz, wgraj tylko część biblioteki.
5. Włącz **Wyszukiwanie w sieci**, żeby GPT mógł porównywać tezy z dzisiejszą wiedzą.
6. Zapisz. Jeśli wybierzesz *Każdy, kto ma link*, możesz udostępnić rozmowę z archiwum innym.

### B. Claude – projekt

1. Na [claude.ai](https://claude.ai) utwórz **nowy projekt**.
2. W **Instrukcjach projektu** wklej tekst z [docs/instrukcje-asystenta.md](docs/instrukcje-asystenta.md).
3. W **Wiedzy projektu** dodaj pliki z [`dla-ai/`](dla-ai). Możesz je wgrać ręcznie albo przez *Dodaj z GitHub* wybrać to repozytorium i folder `dla-ai`. Jeśli projekt nie przyjmie wszystkiego, wgraj pliki `00`–`06` (archiwum) i tylko te książki z `07`–`17`, których potrzebujesz. Pełną bibliotekę bez limitu daje konektor z punktu D.
4. Rozmawiaj w tym projekcie.

### C. Claude Desktop / Claude Code (serwer MCP)

Ten sposób działa najlepiej. AI dostaje 12 narzędzi:

| Narzędzie | Co robi |
|---|---|
| `list_articles` | spis treści (z tematami) |
| `search` | wyszukiwanie po słowach (w artykułach, opracowaniach i opisach zdjęć albo w bibliotece); działa bez polskich znaków i przy literówkach |
| `search_by_meaning` | wyszukiwanie po znaczeniu, także w bibliotece |
| `read_article` | pełny tekst artykułu, z opisem każdego zdjęcia |
| `get_article_notes` | opracowanie: streszczenie, tezy z cytatami, tematy, osoby, miejsca, daty |
| `related_articles` | artykuły powiązane znaczeniowo i tematycznie |
| `find_in_article` | wszystkie miejsca w artykule lub książce, gdzie pada dane słowo |
| `get_image` | zdjęcie razem z opisem |
| `list_books` | książki cytowane przez autora i gdzie je legalnie przeczytać |
| `list_library`, `read_book` | biblioteka dawnych źródeł w pełnym brzmieniu |
| `author_profile` | rys autora (fakty, poglądy, styl) i jego wywiad – do pytań „kim był Leszek” i do „Rozmowy z Leszkiem” |

Potrzebny jest [Node.js](https://nodejs.org) w wersji 20 lub nowszej. Przy pierwszym wyszukiwaniu po znaczeniu serwer pobiera jednorazowo model językowy (ok. 120 MB). Potem działa bez internetu.

```bash
git clone https://github.com/jokerwader/uleszka-archiwum.git
```

```bash
cd uleszka-archiwum && npm install
```

**Claude Desktop:** *Settings → Developer → Edit Config*. Dopisz poniższy wpis (ścieżkę zmień na swoją) i uruchom Claude ponownie:

```json
{
  "mcpServers": {
    "uleszka": {
      "command": "node",
      "args": ["C:\\sciezka\\do\\uleszka-archiwum\\dist\\server.js"]
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add uleszka -- node /sciezka/do/uleszka-archiwum/dist/server.js
```

Gotowe polecenia (prompty) dostępne w Claude:

- **omow_artykul**: wierne streszczenie tez artykułu i zestawienie każdej z dzisiejszą wiedzą.
- **szukaj_odzwierciedlen**: wszystko, co archiwum mówi na dany temat, i co mówią o tym obecne badania.
- **sprawdz_zrodlo**: czy autor wiernie oddał dawne źródło, np. Platona o Atlantydzie. AI porównuje jego słowa z oryginałem z biblioteki.

### D. Serwer MCP pod adresem internetowym

Serwer archiwum działa publicznie w internecie, bezpłatnie dla użytkowników i bez logowania. Ma te same 11 narzędzi i 3 gotowe polecenia co w punkcie C.

**Adres serwera:**

```
https://uleszka-mcp-production.up.railway.app/mcp
```

- **Claude.ai** (także na darmowym koncie i w aplikacji na telefon): *Customize → Connectors → + → Add custom connector*. Nazwa np. `U Leszka`, adres jak wyżej. Ostrzeżenie „Couldn't check the server” można pominąć (*Continue anyway*), a w części *Authentication* zostawić **No sign-in**. Potem w rozmowie włącz konektor ikoną narzędzi pod polem wiadomości.
- **ChatGPT** (plany płatne): *Ustawienia → Aplikacje i konektory → Zaawansowane → tryb deweloperski*, potem *Utwórz*. Wklej adres i wybierz uwierzytelnianie *Brak*.
- **Inne programy obsługujące MCP** (Cursor, VS Code, LM Studio…): dodaj serwer typu „HTTP” / „Streamable HTTP” z tym adresem.

Serwer ma limit 120 zapytań na minutę z jednego adresu, żeby nikt go nie przeciążył. Zwykła rozmowa nie zbliża się do tego limitu.

Możesz też uruchomić własną kopię, np. na Railway (plik [`railway.json`](railway.json) jest gotowy), Render albo własnym serwerze. Serwer potrzebuje ok. 1 GB pamięci.

```bash
PORT=3000 npm start
```

Serwer odpowiada pod adresem `/mcp` (protokół MCP Streamable HTTP). Pod adresem `/health` zwraca krótki opis. Działanie serwera zdalnego sprawdza `npx tsx scripts/test-mcp.ts --url <adres>`.

---

## ❓ O co można zapytać

- „Jakie artykuły są w dziale Cywilizacja Bogów? Od czego zacząć?”
- „Co autor pisał o Tiahuanaco? Zacytuj najważniejsze fragmenty.”
- „Omów artykuł o potopie i porównaj jego tezy z dzisiejszą geologią.”
- „Autor pisał o Piramidzie w Visoko w 2006 roku. Co ustalono od tamtej pory?”
- „Które przewidywania z artykułu o roku 2012 się sprawdziły, a które nie?”
- „Co archiwum mówi o fluorze, a co mówią aktualne badania?”
- „Jakie pytania autora pozostają otwarte do dziś?”

---

## 🎙️ Rozmowa z Leszkiem

AI może poprowadzić rozmowę **stylem i poglądami Leszka Klimka**: gawędziarsko, z jego porównaniami i dosłownymi cytatami z archiwum. Opiera się na [rysie autora](docs/leszek-rys.md), który powstał wyłącznie z jego tekstów i [wywiadu dla nandi.pl](materialy/wywiad-nandi-pl.md). Leszek Klimek nie żyje, dlatego każda taka rozmowa zaczyna się informacją, że to rekonstrukcja AI. AI nie dopisuje mu faktów z życia, a przy tematach zdrowotnych wychodzi z roli. W Claude: **+ → konektor → „Rozmowa z Leszkiem”**. W ChatGPT i projektach Claude służy do tego plik `dla-ai/18-rozmowa-z-leszkiem.md`.

Inne wypowiedzi autora i teksty o nim są zebrane w [`materialy/`](materialy/README.md).

## 📚 Książki, na które powołuje się autor

Leszek Klimek cytuje setki książek i dawnych tekstów: od Platona, Herodota i Księgi Henocha po Dänikena i Sitchina. Zestawienie [**docs/ksiazki.md**](docs/ksiazki.md) pokazuje, które z nich można legalnie przeczytać lub pobrać za darmo i gdzie, a także w których artykułach są cytowane.

W [**bibliotece**](biblioteka/README.md) jest 30 takich dzieł w przekładach polskich i angielskich, a dla 17 z nich także tekst w języku oryginału. Dzięki temu można sprawdzić nie tylko, czy autor wiernie oddał przekład, ale i czy sam przekład oddaje oryginał. Przykładowe pytanie do AI: *„Co dokładnie mówi Platon w Kritiasie o zagładzie Atlantydy? Przetłumacz grecki oryginał i porównaj z przekładem Witwickiego”*. Tłumaczenia AI z oryginału są robocze i należy je tak traktować. Teksty w językach oryginału są dostępne przez serwer MCP (sposoby C i D); do paczki `dla-ai/` nie trafiły, bo są zbyt obszerne.

Oryginałów nie ma tam, gdzie nie istnieje wolny tekst cyfrowy: Księga Henocha (gyyz), Gilgamesz i Hammurabi (pismo klinowe), Księga Umarłych (hieroglify), Popol Vuh (kicze).

## 📜 Historia strony

- **Autor:** Leszek Klimek. Jak mówił w wywiadzie, tematem zajął się w 1992 roku, po przejściu na emeryturę. Inspiracją był Erich von Däniken, ale nie wszystko w jego tezach przekonywało autora, więc zaczął dociekać sam. W internecie był od 2004 roku. ([wywiad, nandi.pl](https://nandi.pl/index.php?go=art_uleszka))
- **Motto:** „Uwierz we własny rozum”. Strona zachęcała, by „zapomnieć na dłuższą chwilę o tym, czego nauczyłeś się w szkole”.
- **Działy:** *Cywilizacja Bogów* (dawne cywilizacje, budowle, mity, katastrofy), *Zapomniana medycyna* (medycyna naturalna, zdrowie, żywność), *Różności* (publicystyka, teksty prywatne, fotografie) i *Pamiętam*.
- **Ostatnia aktualizacja** w zachowanej kopii: 5 kwietnia 2007.
- **Po zniknięciu strony** jej treści przetrwały dzięki czytelnikom. W 2014 roku zostały ponownie opublikowane na blogach „ULESZKA.NET – Reaktywacja” ([uwierzwewlasnyrozum](https://uwierzwewlasnyrozum.wordpress.com/), [zapomnianamedycyna](https://zapomnianamedycyna.wordpress.com/), [uleszkaroznosci](https://uleszkaroznosci.wordpress.com/informacje/)), a w 2023 roku przypomniał je [Czesław Białczyński](https://bialczynski.pl/2023/12/29/uleszka-net-reaktywacja-uwierz-we-wlasny-rozum-archiwum-2001-2006/). Według tego ostatniego wpisu portal reaktywowano po śmierci autora.

To repozytorium zachowuje stronę w pierwotnym układzie działów, razem ze zdjęciami i z wiernością tekstu, którą każdy może sprawdzić.

---

## 📂 Co jest w repozytorium

| Miejsce | Zawartość |
|---|---|
| [`KATALOG.md`](KATALOG.md) | Spis treści: 148 stron w kolejności z menu strony, w działach |
| [`artykuly/`](artykuly) | Każda strona jako osobny plik Markdown, z opisem (tytuł, dział, adres oryginału) i zdjęciami |
| [`dla-ai/`](dla-ai) | Całe archiwum, biblioteka i rys autora w 19 plikach do wgrania do ChatGPT lub Claude (sposoby A i B) |
| [`zrodlo/`](zrodlo) | Oryginalna kopia strony: pliki HTML i ok. 1500 zdjęć, bajt w bajt |
| [`opracowania/`](opracowania) | Opracowania AI każdego artykułu (JSON) i [ich spis](opracowania/README.md) |
| [`biblioteka/`](biblioteka) | 30 dawnych dzieł z domeny publicznej, na które powołuje się autor, i 17 tekstów w językach oryginału ([spis](biblioteka/README.md)) |
| [`materialy/`](materialy/README.md) | wypowiedzi autora spoza strony (wywiad dla nandi.pl) i teksty o nim |
| [`dane/`](dane) | Opisy AI zdjęć (`opisy-obrazow/`) i wektory do wyszukiwania po znaczeniu (`wektory/`) |
| [`src/`](src) | Serwer MCP |
| [`scripts/`](scripts) | Konwersja, kontrola wierności, pliki dla AI, testy |
| [`docs/`](docs) | Instrukcje dla asystenta AI oraz [książki cytowane przez autora i gdzie je legalnie przeczytać za darmo](docs/ksiazki.md) |

### Wierność tekstów

Teksty są przeniesione **bez zmian**. Zmienił się tylko zapis: Markdown zamiast HTML i współczesne kodowanie polskich znaków. Usunięte są elementy techniczne: ramki, menu i licznik odwiedzin. Błędy i pomyłki z oryginału też są zachowane.

Każdy może to sprawdzić. Skrypt porównuje litera po literze każdy oryginalny plik z wersją w archiwum:

```bash
npm run sprawdz
```

Wynik: `Sprawdzono 148 artykułów (3642740 liter i cyfr). Różnic: 0.`

Druga kontrola dotyczy warstwy AI. Sprawdza, że każdy artykuł ma opracowanie, każdy z ponad 1000 cytatów w opracowaniach występuje w artykule dosłownie i każde zdjęcie ma opis:

```bash
npm run sprawdz-opracowania
```

### Dla programistów

```bash
npm run konwertuj   # odtwarza artykuly/ i KATALOG.md z zrodlo/
```

```bash
npm run biblioteka  # pobiera brakujące dzieła do biblioteka/ (Gutenberg, Wolne Lektury, Wikiźródła)
```

```bash
npm run wektory     # wektory znaczenia dla archiwum; "npm run wektory -- biblioteka" dla biblioteki
```

```bash
npm run pakiety     # odtwarza dla-ai/
```

```bash
npm run build && npm test   # testy serwera MCP: lokalnie (stdio) i przez HTTP
```

Zasób MCP: `uleszka://katalog`. Model do wyszukiwania po znaczeniu: [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small), uruchamiany lokalnie przez transformers.js.

---

## ⚖️ Prawa autorskie

Treści strony uleszka.net (`artykuly/`, `zrodlo/`, `dla-ai/`, `KATALOG.md`) należą do ich autora i jego spadkobierców i **nie** są objęte licencją MIT. Archiwum ma charakter dokumentacyjny i niekomercyjny: chroni przed zniknięciem stronę, która nie działa już w sieci. Jeśli masz prawa do tych treści i zastrzeżenia, załóż zgłoszenie (Issue), a treści zostaną usunięte.

Teksty są poglądami autora sprzed ok. 20 lat. Dotyczy to zwłaszcza działu o zdrowiu: nie są poradą medyczną.

Licencja MIT ([LICENSE](LICENSE)) dotyczy tylko kodu (`src/`, `scripts/`).

Dzieła w `biblioteka/` są w domenie publicznej. Pliki z Project Gutenberg zawierają oryginalną licencję PG, a wydania Wolnych Lektur i transkrypcje Wikiźródeł mają licencje CC BY-SA, podane w nagłówku każdego pliku. Opracowania i opisy zdjęć przygotowane przez AI (`opracowania/`, `dane/opisy-obrazow/`) udostępniamy na licencji [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pl).
