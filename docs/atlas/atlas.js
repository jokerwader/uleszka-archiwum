// Atlas Leszka: mapa z filtrami (index.html), mini mapa na karcie miejsca i podgląd zdjęć
(() => {
  const KOLORY = { piramidy: "#c9861a", megality: "#8a6d4b", miasta: "#b0503a", podziemia: "#5c5470", astronomia: "#2f6f9f", kataklizmy: "#3f8a7a", zamki: "#7a7f2a", zagadki: "#9b4f8f" };
  const KAFELKI = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  const OSM = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // podgląd zdjęcia w dużym formacie
  const dlg = document.getElementById("podglad");
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".powieksz");
    if (!b || !dlg?.showModal) return;
    dlg.querySelector("img").src = b.dataset.duze;
    dlg.querySelector("p").textContent = b.dataset.podpis || "";
    dlg.showModal();
  });
  dlg?.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });

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
      k.bindPopup(`${d.f ? `<img src="${esc(d.f)}" alt="">` : ""}<b>${esc(d.n)}</b>${d.a} ${d.a === 1 ? "artykuł" : "artykuły"} Leszka · ${d.z} zdj.<br><a class="otworz" href="${d.s}.html">Otwórz kartę miejsca →</a>`);
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
