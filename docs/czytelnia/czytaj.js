// „Posłuchaj” – darmowe czytanie artykułu na głos syntezatorem mowy wbudowanym w przeglądarkę.
// Bez serwera i bez kosztów. Najlepsze polskie głosy ma Microsoft Edge (Zofia, Marek), dobre: Android, iPhone, Windows.
(() => {
  const synt = window.speechSynthesis;
  const panel = document.getElementById("odtwarzacz");
  const tresc = document.querySelector(".tresc");
  if (!synt || !panel || !tresc || typeof SpeechSynthesisUtterance === "undefined") return;
  panel.hidden = false;

  const graj = document.getElementById("graj"), grajTekst = document.getElementById("graj-tekst"), stop = document.getElementById("stop");
  const wyborGlosu = document.getElementById("glos"), wyborTempa = document.getElementById("tempo");
  const postep = document.getElementById("postep"), wskazowka = document.getElementById("wskazowka-glos");
  const pamiec = { czytaj: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, zapisz: (k, v) => { try { localStorage.setItem(k, v); } catch {} } };

  // fragmenty do czytania: akapity, punkty list, cytaty, nagłówki; długie dzielone na zdania (Chrome urywa bardzo długie wypowiedzi)
  const bloki = [...tresc.querySelectorAll("p, li, blockquote, h1, h2, h3, h4")].filter((el) => !el.closest("li p, blockquote p") || el.tagName !== "P").filter((el) => el.innerText.trim().length > 1);
  const fragmenty = [];
  bloki.forEach((el, nr) => {
    el.dataset.seg = nr;
    const tekst = el.textContent.replace(/\s+/g, " ").trim(); // textContent: inicjał „P” + „ora” = „Pora”
    // każde zdanie to osobna wypowiedź – syntezator robi wtedy wyraźną pauzę po kropce, pytajniku i wykrzykniku;
    // długie zdania dzielimy jeszcze na przecinkach, średnikach, dwukropkach i myślnikach (pauza także tam)
    const zdania = tekst.match(/[^.!?…]+[.!?…]+["”»)]*\s*|[^.!?…]+$/g) ?? [tekst];
    for (const z of zdania) {
      if (z.trim().length <= 150) { if (z.trim()) fragmenty.push({ el, tekst: z.trim() }); continue; }
      let kawalek = "";
      for (const c of z.split(/(?<=[,;:]|\s[–—-]\s)/)) {
        if ((kawalek + c).length > 150 && kawalek.trim().length >= 40) { fragmenty.push({ el, tekst: kawalek.trim() }); kawalek = ""; }
        kawalek += c;
      }
      if (kawalek.trim()) fragmenty.push({ el, tekst: kawalek.trim() });
    }
  });
  if (!fragmenty.length) { panel.hidden = true; return; }

  let glosy = [], indeks = 0, gra = false, aktywny = false;
  const ocenGlos = (g) => (/natural|online|neural|premium|enhanced/i.test(g.name) ? 3 : 0) + (/zofia|marek|gosia|ewa|paulina|zosia/i.test(g.name) ? 1 : 0) + (g.localService ? 0 : 0.5);
  const wczytajGlosy = () => {
    glosy = synt.getVoices().filter((g) => /^pl/i.test(g.lang)).sort((a, b) => ocenGlos(b) - ocenGlos(a));
    const zapamietany = pamiec.czytaj("uleszka-glos");
    wyborGlosu.innerHTML = "";
    glosy.forEach((g, i) => {
      const o = document.createElement("option");
      o.value = g.name;
      o.textContent = g.name.replace(/^Microsoft /, "").replace(/ - Polish \(Poland\)| \(Poland\)/, "").replace(/ Online \(Natural\)/, " – naturalny");
      if (g.name === zapamietany || (!zapamietany && i === 0)) o.selected = true;
      wyborGlosu.append(o);
    });
    wyborGlosu.parentElement.hidden = glosy.length < 2;

    // podpowiedź: najlepsze darmowe polskie głosy (Zofia, Marek – „naturalne”) ma przeglądarka Microsoft Edge
    const naturalny = glosy.some((g) => /natural|neural|premium|enhanced/i.test(g.name));
    const jestEdge = /Edg\//.test(navigator.userAgent);
    const telefon = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);
    const windows = /Windows/i.test(navigator.userAgent);
    wskazowka.innerHTML = "";
    if (!glosy.length) {
      wskazowka.textContent = "Twoja przeglądarka nie ma polskiego głosu – przeczyta tekst głosem domyślnym. Najładniej czyta Microsoft Edge (darmowe głosy Zofia i Marek).";
    } else if (!naturalny && !jestEdge && !telefon) {
      wskazowka.append("Ten głos brzmi sztucznie. Dużo ładniej czyta przeglądarka ");
      const b = document.createElement("b");
      b.textContent = "Microsoft Edge";
      wskazowka.append(b, " – ma darmowe, naturalne głosy Zofia i Marek. ");
      if (windows) {
        // na Windows ten odnośnik otwiera bieżącą stronę od razu w Edge
        const a = document.createElement("a");
        a.href = "microsoft-edge:" + location.href;
        a.textContent = "Otwórz tę stronę w Edge →";
        wskazowka.append(a);
      } else {
        wskazowka.append("Otwórz tę stronę w Edge i kliknij „Posłuchaj”.");
      }
    }
    wskazowka.hidden = !wskazowka.textContent;
  };
  wczytajGlosy();
  synt.addEventListener?.("voiceschanged", wczytajGlosy);
  const tempo = pamiec.czytaj("uleszka-tempo");
  if (tempo) wyborTempa.value = tempo;

  const zaznacz = (el) => {
    tresc.querySelectorAll(".czytane").forEach((x) => x.classList.remove("czytane"));
    if (!el) return;
    el.classList.add("czytane");
    const r = el.getBoundingClientRect();
    if (r.top < 70 || r.bottom > innerHeight - 40) el.scrollIntoView({ behavior: "smooth", block: "center" });
  };
  const pokazStan = () => {
    graj.classList.toggle("gra", gra);
    grajTekst.textContent = gra ? "Pauza" : indeks > 0 && aktywny ? "Wznów" : "Posłuchaj";
    stop.hidden = !aktywny;
    tresc.classList.toggle("slucha", aktywny);
    postep.textContent = aktywny ? Math.round((indeks / fragmenty.length) * 100) + "%" : "";
  };
  const mow = () => {
    if (indeks >= fragmenty.length) { zakoncz(); return; }
    const f = fragmenty[indeks];
    const u = new SpeechSynthesisUtterance(f.tekst);
    const g = glosy.find((x) => x.name === wyborGlosu.value) ?? glosy[0];
    if (g) u.voice = g;
    u.lang = g?.lang ?? "pl-PL";
    u.rate = Number(wyborTempa.value) || 1;
    u.onend = () => { if (!gra) return; indeks++; pokazStan(); mow(); };
    u.onerror = (e) => { if (e.error === "interrupted" || e.error === "canceled") return; indeks++; if (gra) mow(); };
    zaznacz(f.el);
    synt.speak(u);
  };
  const start = () => { synt.cancel(); gra = true; aktywny = true; pokazStan(); mow(); };
  const pauza = () => { gra = false; synt.cancel(); pokazStan(); };
  const zakoncz = () => { gra = false; aktywny = false; indeks = 0; synt.cancel(); zaznacz(null); pokazStan(); };

  graj.addEventListener("click", () => (gra ? pauza() : start()));
  stop.addEventListener("click", zakoncz);
  // kliknięcie akapitu w trakcie słuchania – czytaj od tego miejsca
  tresc.addEventListener("click", (e) => {
    if (!aktywny || e.target.closest("a")) return;
    const el = e.target.closest("[data-seg]");
    if (!el) return;
    const i = fragmenty.findIndex((f) => f.el === el);
    if (i >= 0) { indeks = i; start(); }
  });
  wyborGlosu.addEventListener("change", () => { pamiec.zapisz("uleszka-glos", wyborGlosu.value); if (gra) start(); });
  wyborTempa.addEventListener("change", () => { pamiec.zapisz("uleszka-tempo", wyborTempa.value); if (gra) start(); });
  addEventListener("pagehide", () => synt.cancel());
  pokazStan();
})();
