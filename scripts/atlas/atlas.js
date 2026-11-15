// Atlas Leszka: mapa z filtrami (index.html), mini mapa na karcie miejsca i podgląd zdjęć
(() => {
  const KOLORY = { piramidy: "#c9861a", megality: "#8a6d4b", miasta: "#b0503a", podziemia: "#5c5470", astronomia: "#2f6f9f", kataklizmy: "#3f8a7a", zamki: "#7a7f2a", zagadki: "#9b4f8f" };
  const KAFELKI = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  const OSM = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  const odm = (n, [a, b, c]) => (n === 1 ? a : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? b : c);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // podgląd zdjęcia w dużym formacie; strzałki (i klawisze ← →) przechodzą między widocznymi zdjęciami
  // podpis „opis · autor · licencja|adres” – część po „|” to link do źródła zdjęcia albo artykułu
  const dlg = document.getElementById("podglad");
  let biezacy = null;
  const widoczne = () => [...document.querySelectorAll(".powieksz")].filter((b) => !b.closest("[hidden]"));
  const pokaz = (b) => {
    biezacy = b;
    const [tekst, adres] = (b.dataset.podpis || "").split("|");
    const lista = widoczne();
    // od razu miniatura (jest już w pamięci przeglądarki), a duże zdjęcie (1920 px) podmieniamy, gdy się wczyta
    const img = dlg.querySelector("img");
    const mini = b.querySelector("img")?.currentSrc;
    img.src = mini || b.dataset.duze;
    img.alt = b.querySelector("img")?.alt || "";
    dlg.classList.toggle("laduje", !!mini && mini !== b.dataset.duze);
    if (mini && mini !== b.dataset.duze) {
      const duze = new Image();
      duze.onload = () => { if (biezacy === b) { img.src = b.dataset.duze; dlg.classList.remove("laduje"); } };
      duze.onerror = () => dlg.classList.remove("laduje");
      duze.src = b.dataset.duze;
    }
    const p = dlg.querySelector("p");
    p.textContent = "";
    if (lista.length > 1) p.append(Object.assign(document.createElement("span"), { className: "licznik-zdj", textContent: `${lista.indexOf(b) + 1} / ${lista.length}` }));
    p.append(tekst || "");
    if (adres) p.append(" · ", Object.assign(document.createElement("a"), { href: adres, textContent: adres.includes("czytelnia") ? "artykuł" : "źródło", rel: "noopener" }));
    dlg.querySelectorAll(".nawigacja").forEach((n) => (n.hidden = lista.length < 2));
  };
  const przejdz = (o) => { const l = widoczne(); if (biezacy && l.length) pokaz(l[(l.indexOf(biezacy) + o + l.length) % l.length]); };
  if (dlg) {
    for (const [klasa, znak, o] of [["wstecz", "‹", -1], ["dalej", "›", 1]]) {
      const n = Object.assign(document.createElement("button"), { type: "button", className: `nawigacja ${klasa}`, textContent: znak });
      n.setAttribute("aria-label", o < 0 ? "Poprzednie zdjęcie" : "Następne zdjęcie");
      n.addEventListener("click", (e) => { e.stopPropagation(); przejdz(o); });
      dlg.append(n);
    }
    dlg.addEventListener("keydown", (e) => { if (e.key === "ArrowLeft") przejdz(-1); if (e.key === "ArrowRight") przejdz(1); });
    dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".powieksz");
    if (!b || !dlg?.showModal) return;
    pokaz(b);
    dlg.showModal();
  });

  // „Pokaż wszystkie” – rozwija zwiniętą listę (badania, artykuły) i znika
  document.querySelectorAll(".pokaz-wszystkie").forEach((p) => p.addEventListener("click", () => {
    p.previousElementSibling?.classList.add("rozwiniete");
    p.hidden = true;
  }));
  // długi opis badania: „więcej” pokazuje cały tekst
  document.querySelectorAll(".badanie .wiecej").forEach((w) => w.addEventListener("click", () => {
    w.previousElementSibling.classList.add("caly");
    w.remove();
  }));
  // kalendarz lat: wybrany rok pokazuje tylko jego badania (wszystkie, bez zwijania); „Wszystkie” wraca do listy
  const kal = document.querySelector(".kalendarz");
  if (kal) {
    const lista = document.querySelector(".lista-badan");
    const przycisk = lista.parentElement.querySelector(".pokaz-wszystkie");
    const rozwinieta = lista.classList.contains("rozwiniete");
    kal.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-rok]");
      if (!b || b.disabled) return;
      const rok = b.dataset.rok;
      kal.querySelectorAll("button[data-rok]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      for (const li of lista.children) li.hidden = !!rok && !li.dataset.lata.split(" ").includes(rok);
      if (rok) { lista.classList.add("rozwiniete"); if (przycisk) przycisk.hidden = true; }
      else if (!rozwinieta && przycisk && przycisk.isConnected && !przycisk.dataset.uzyty) { lista.classList.remove("rozwiniete"); przycisk.hidden = false; }
    });
    przycisk?.addEventListener("click", () => (przycisk.dataset.uzyty = "1"));
  }

  // karta miejsca: przełącznik rodzaju zdjęć
  const przyciski = [...document.querySelectorAll(".przelacznik-zdjec button")];
  przyciski.forEach((p) => p.addEventListener("click", () => {
    przyciski.forEach((x) => x.setAttribute("aria-pressed", String(x === p)));
    document.querySelectorAll(".siatka-zdjec li").forEach((li) => (li.hidden = !!p.dataset.grupa && li.dataset.grupa !== p.dataset.grupa));
  }));

  const start = () => {
    if (!window.L) return;
    // mini mapa na karcie miejsca
    const mini = document.getElementById("mini-mapa");
    if (mini) {
      const p = [+mini.dataset.lat, +mini.dataset.lon];
      const m = L.map(mini, { scrollWheelZoom: false }).setView(p, 6);
      L.tileLayer(KAFELKI, { attribution: OSM, maxZoom: 18 }).addTo(m);
      L.marker(p).addTo(m).bindPopup(esc(mini.dataset.nazwa));
      return;
    }
    // mapa wszystkich miejsc
    const el = document.getElementById("mapa");
    const daneEl = document.getElementById("dane-mapy");
    if (!el || !daneEl) return;
    const dane = JSON.parse(daneEl.textContent);
    const mapa = L.map(el, { worldCopyJump: true, scrollWheelZoom: false }).setView([25, 15], 2);
    L.tileLayer(KAFELKI, { attribution: OSM, maxZoom: 18 }).addTo(mapa);
    el.addEventListener("click", () => mapa.scrollWheelZoom.enable(), { once: true });
    const znaczniki = new Map();
    for (const d of dane) {
      const k = L.circleMarker([d.la, d.lo], { radius: 7 + Math.min(d.a, 10) * 0.6, color: "#fff", weight: 1.5, fillColor: KOLORY[d.r[0]] || "#9a5f12", fillOpacity: 0.9 });
      k.bindPopup(`${d.f ? `<img src="${esc(d.f)}" alt="">` : ""}<b>${esc(d.n)}</b>${d.a} ${odm(d.a, ["artykuł", "artykuły", "artykułów"])} Leszka · ${d.z} zdj.<br><a class="otworz" href="${d.s}.html">Otwórz kartę miejsca →</a>`);
      k.addTo(mapa);
      znaczniki.set(d.s, { k, d });
    }
    const karty = [...document.querySelectorAll("#karty li")];
    const filtry = [...document.querySelectorAll(".filtr")];
    const szukaj = document.getElementById("szukaj-miejsca");
    let rodzaj = "";
    const odswiez = () => {
      const q = szukaj.value.trim().toLowerCase();
      let ile = 0;
      for (const { k, d } of znaczniki.values()) {
        const tak = (!rodzaj || d.r.includes(rodzaj)) && (!q || d.n.toLowerCase().includes(q));
        if (tak) { k.addTo(mapa); ile++; } else k.remove();
      }
      for (const li of karty) li.hidden = !((!rodzaj || li.dataset.r.split(" ").includes(rodzaj)) && (!q || li.dataset.n.includes(q)));
      document.getElementById("ile-widac").textContent = ile;
    };
    const ustawRodzaj = (r) => {
      rodzaj = r;
      filtry.forEach((f) => f.setAttribute("aria-pressed", String(f.dataset.r === r)));
      odswiez();
    };
    filtry.forEach((f) => f.addEventListener("click", () => { ustawRodzaj(f.dataset.r); history.replaceState(null, "", f.dataset.r ? `#${f.dataset.r}` : "#"); }));
    szukaj.addEventListener("input", odswiez);
    // adres #rodzaj filtruje, #miejsce pokazuje punkt (także po zmianie samego # w adresie)
    const wedlugAdresu = () => {
      const h = decodeURIComponent(location.hash.slice(1));
      if (filtry.some((f) => f.dataset.r === h)) ustawRodzaj(h);
      else if (znaczniki.has(h)) {
        ustawRodzaj("");
        const { k } = znaczniki.get(h);
        mapa.setView(k.getLatLng(), 8);
        k.openPopup();
        el.scrollIntoView({ block: "center" });
      }
    };
    wedlugAdresu();
    window.addEventListener("hashchange", wedlugAdresu);
  };
  if (document.readyState === "complete") start(); else window.addEventListener("load", start);
})();
