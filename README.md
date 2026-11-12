# Uleszka.net – „Uwierz we własny rozum”

### Archiwum strony, z którą można porozmawiać

**uleszka.net** to polska strona internetowa z lat ok. 2004–2007. Na długo przed erą blogów i mediów społecznościowych zadawała pytania, których w szkole nikt nie zadawał. Kto zbudował piramidy i Tiahuanaco? Czy potop był jeden? Gdzie leżała Atlantyda? Dlaczego oficjalna historia ma tyle luk? Pisała też o zapomnianej medycynie naturalnej i o tym, co jemy.

Dla wielu czytelników była to pierwsza strona, która pokazała, że o te sprawy w ogóle można pytać. Stała się inspiracją dla wielu późniejszych stron i blogów o podobnej tematyce, a jej teksty do dziś są przedrukowywane w sieci.

Strona zniknęła z internetu. To repozytorium zachowuje **całość jej treści w niezmienionej formie**. Do tego daje możliwość, której wtedy nie było: **rozmowy z archiwum przez sztuczną inteligencję**. Można pytać o teksty, sprawdzać historię i porównywać tezy autora z tym, co wiemy dziś.

> „Zwrócić na coś uwagę większości, znaczy pomóc zdrowemu rozsądkowi wpaść na właściwy ślad” – G. E. Lessing, motto strony

---

## 💬 Jak porozmawiać z archiwum

Wybierz sposób, który ci pasuje:

| Sposób | Dla kogo | Instalacja |
|---|---|---|
| [A. Własny GPT w ChatGPT](#a-chatgpt--własny-gpt) | użytkownicy ChatGPT | nie, tylko wgranie plików |
| [B. Projekt w Claude](#b-claude--projekt) | użytkownicy Claude.ai | nie, tylko wgranie plików |
| [C. Serwer MCP w Claude Desktop lub Claude Code](#c-claude-desktop--claude-code-serwer-mcp) | najlepsza jakość: AI samo przeszukuje archiwum i czyta całe artykuły | tak, Node.js |
| [D. Serwer MCP pod adresem internetowym](#d-serwer-mcp-pod-adresem-internetowym) | ChatGPT i Claude.ai przez adres URL | nie dla użytkownika; serwer trzeba uruchomić w sieci |

### A. ChatGPT – własny GPT

1. Pobierz pliki z folderu [`dla-ai/`](dla-ai): kliknij plik, a potem *Download raw file*. Całość ma ok. 5 MB, a każdy dział to jeden plik.
2. W ChatGPT: **Odkrywaj GPT → Utwórz → Konfiguruj**.
3. W polu **Instrukcje** wklej tekst z [docs/instrukcje-asystenta.md](docs/instrukcje-asystenta.md).
4. W sekcji **Wiedza** wgraj pliki z `dla-ai/`.
5. Włącz **Wyszukiwanie w sieci**, żeby GPT mógł porównywać tezy z dzisiejszą wiedzą.
6. Zapisz. Jeśli wybierzesz *Każdy, kto ma link*, możesz udostępnić rozmowę z archiwum innym.

### B. Claude – projekt

1. Na [claude.ai](https://claude.ai) utwórz **nowy projekt**.
2. W **Instrukcjach projektu** wklej tekst z [docs/instrukcje-asystenta.md](docs/instrukcje-asystenta.md).
3. W **Wiedzy projektu** dodaj pliki z [`dla-ai/`](dla-ai). Możesz je wgrać ręcznie albo przez *Dodaj z GitHub* wybrać to repozytorium i folder `dla-ai`.
4. Rozmawiaj w tym projekcie.

### C. Claude Desktop / Claude Code (serwer MCP)

Ten sposób działa najlepiej. AI dostaje narzędzia: spis treści, wyszukiwarkę (odporną na brak polskich znaków i literówki), czytanie całych artykułów, szukanie w artykule i oglądanie zdjęć.

Potrzebny jest [Node.js](https://nodejs.org) w wersji 20 lub nowszej.

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

### D. Serwer MCP pod adresem internetowym

Ten sam serwer może działać w internecie. Wtedy wystarczy wkleić jego adres:

- w **Claude.ai**: *Ustawienia → Konektory → Dodaj własny konektor*,
- w **ChatGPT** (plany płatne): *Ustawienia → Aplikacje i konektory → tryb deweloperski → Utwórz konektor*.

Publiczny adres: *jeszcze nie uruchomiony*.

Każdy może uruchomić własny serwer, np. na Railway, Render albo własnym serwerze:

```bash
PORT=3000 npm start
```

Serwer odpowiada pod adresem `/mcp` (protokół MCP Streamable HTTP).

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
| [`dla-ai/`](dla-ai) | Całe archiwum w kilku plikach do wgrania do ChatGPT lub Claude (sposoby A i B) |
| [`zrodlo/`](zrodlo) | Oryginalna kopia strony: pliki HTML i ok. 1500 zdjęć, bajt w bajt |
| [`src/`](src) | Serwer MCP |
| [`scripts/`](scripts) | Konwersja, kontrola wierności, pliki dla AI, testy |
| [`docs/`](docs) | Instrukcje dla asystenta AI |

### Wierność tekstów

Teksty są przeniesione **bez zmian**. Zmienił się tylko zapis: Markdown zamiast HTML i współczesne kodowanie polskich znaków. Usunięte są elementy techniczne: ramki, menu i licznik odwiedzin. Błędy i pomyłki z oryginału też są zachowane.

Każdy może to sprawdzić. Skrypt porównuje litera po literze każdy oryginalny plik z wersją w archiwum:

```bash
npm run sprawdz
```

Wynik: `Sprawdzono 148 artykułów (3642740 liter i cyfr). Różnic: 0.`

### Dla programistów

```bash
npm run konwertuj   # odtwarza artykuly/ i KATALOG.md z zrodlo/
```

```bash
npm run pakiety     # odtwarza dla-ai/
```

```bash
npm run build && npm test   # testy serwera MCP: lokalnie (stdio) i przez HTTP
```

Narzędzia serwera: `list_articles`, `search`, `read_article`, `find_in_article`, `get_image`. Zasób: `uleszka://katalog`.

---

## ⚖️ Prawa autorskie

Treści strony uleszka.net (`artykuly/`, `zrodlo/`, `dla-ai/`, `KATALOG.md`) należą do ich autora i jego spadkobierców i **nie** są objęte licencją MIT. Archiwum ma charakter dokumentacyjny i niekomercyjny: chroni przed zniknięciem stronę, która nie działa już w sieci. Jeśli masz prawa do tych treści i zastrzeżenia, załóż zgłoszenie (Issue), a treści zostaną usunięte.

Teksty są poglądami autora sprzed ok. 20 lat. Dotyczy to zwłaszcza działu o zdrowiu: nie są poradą medyczną.

Licencja MIT ([LICENSE](LICENSE)) dotyczy tylko kodu (`src/`, `scripts/`).
