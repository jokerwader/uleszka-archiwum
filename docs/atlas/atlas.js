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

  // „Pokaż wszystkie” – rozwija zwiniętą listę (artykuły, badania, zdjęcia) i znika
  document.querySelectorAll(".pokaz-wszystkie").forEach((p) => p.addEventListener("click", () => {
    p.previousElementSibling?.classList.add("rozwiniete");
    p.hidden = true;
  }));
  // filtr (lata badań, rodzaj zdjęć): wybrana wartość pokazuje wszystkie pasujące wpisy, bez zwijania
  const filtruj = (grupa, lista, atrybut, pasuje) => {
    const przyciski = [...document.querySelectorAll(`${grupa} button`)];
    if (!lista || !przyciski.length) return;
    przyciski.forEach((b) => b.addEventListener("click", () => {
      const w = b.dataset[atrybut];
      przyciski.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      for (const li of lista.children) li.hidden = !!w && !pasuje(li, w);
      if (w) {
        lista.classList.add("rozwiniete");
        const wiecej = lista.nextElementSibling;
        if (wiecej?.classList.contains("pokaz-wszystkie")) wiecej.hidden = true;
      }
    }));
  };
  filtruj(".lata-filtr", document.querySelector(".os-badan"), "rok", (li, w) => li.dataset.rok === w);
  filtruj(".przelacznik-zdjec", document.querySelector(".mozaika"), "grupa", (li, w) => li.dataset.grupa === w);
  // link do „#badania” z części „W skrócie” rozwija najnowsze badanie
  document.querySelectorAll('a[href="#badania"]').forEach((a) => a.addEventListener("click", () => {
    const d = document.querySelector(".os-badan details");
    if (d) d.open = true;
  }));
  // pasek części karty: podświetla tę, którą się właśnie czyta
  const linkiSekcji = [...document.querySelectorAll(".sekcje a")];
  if (linkiSekcji.length) {
    const sekcje = linkiSekcji.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
    const zaznacz = (id) => linkiSekcji.forEach((a) => {
      const tu = a.getAttribute("href") === `#${id}`;
      a.classList.toggle("tu", tu);
      if (tu) { a.setAttribute("aria-current", "true"); const n = a.parentElement; n.scrollTo({ left: a.offsetLeft - (n.clientWidth - a.clientWidth) / 2, behavior: "smooth" }); } else a.removeAttribute("aria-current");
    });
    // bieżąca część: ostatnia, której początek minął pasek nawigacji
    let czeka = false, ostatnia;
    const sprawdz = () => {
      czeka = false;
      let biez = "";
      for (const s of sekcje) if (s.getBoundingClientRect().top <= 160) biez = s.id;
      if (biez !== ostatnia) { ostatnia = biez; zaznacz(biez); }
    };
    addEventListener("scroll", () => { if (!czeka) { czeka = true; requestAnimationFrame(sprawdz); } }, { passive: true });
    sprawdz();
  }

  const start = () => {
    if (!window.L) return;
    // mini mapa na karcie miejsca
    const mini = document.getElementById("mini-mapa");
    if (mini) {
      const p = [+mini.dataset.lat, +mini.dataset.lon];
      const m = L.map(mini, { scrollWheelZoom: false });
      L.tileLayer(KAFELKI, { attribution: OSM, maxZoom: 18 }).addTo(m);
      L.marker(p).addTo(m).bindPopup(esc(mini.dataset.nazwa));
      // miejsca z atlasu w promieniu 400 km jako małe punkty; mapa obejmuje je wszystkie (bez nich – widok regionu)
      const blisko = JSON.parse(mini.dataset.blisko || "[]").filter((b) => b[4] <= 400);
      for (const [la, lo, n, s, km] of blisko) {
        L.circleMarker([la, lo], { radius: 6, color: "#fff", weight: 1.5, fillColor: "#9a5f12", fillOpacity: 0.9 })
          .addTo(m).bindPopup(`<b>${esc(n)}</b>${km} km stąd<br><a class="otworz" href="${s}.html">Otwórz kartę →</a>`);
      }
      if (blisko.length) m.fitBounds(L.latLngBounds([p, ...blisko.map((b) => [b[0], b[1]])]), { padding: [30, 30], maxZoom: 9 });
      else m.setView(p, 7);
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
