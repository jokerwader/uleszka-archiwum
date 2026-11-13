// Czytelnia: wybór kolorów (motyw) i wielkości tekstu, spis treści, kopiowanie próśb do AI.
// Ustawienia czytelnika zapamiętywane są w przeglądarce (localStorage).
(() => {
  const html = document.documentElement;
  const pamiec = {
    czytaj: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
    zapisz: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
  };

  // ---------- motyw i wielkość tekstu ----------
  const panel = document.getElementById("panel-wygladu");
  const przyciskWygladu = document.getElementById("przycisk-wygladu");
  const ustawMotyw = (m) => {
    html.dataset.motyw = m;
    pamiec.zapisz("uleszka-motyw", m);
    panel?.querySelectorAll("[data-motyw]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.motyw === m)));
  };
  const ROZMIARY = [16, 17, 18, 19, 20, 22, 24, 26];
  const rozmiarWart = document.getElementById("rozmiar-wart");
  const ustawRozmiar = (px) => {
    html.style.setProperty("--rozmiar", px + "px");
    pamiec.zapisz("uleszka-rozmiar", String(px));
    if (rozmiarWart) rozmiarWart.textContent = Math.round((px / 19) * 100) + "%";
  };
  ustawMotyw(html.dataset.motyw || "sepia");
  ustawRozmiar(Number(pamiec.czytaj("uleszka-rozmiar")) || 19);
  panel?.querySelectorAll("[data-motyw]").forEach((b) => b.addEventListener("click", () => ustawMotyw(b.dataset.motyw)));
  panel?.querySelectorAll("[data-rozmiar]").forEach((b) =>
    b.addEventListener("click", () => {
      const teraz = Number(getComputedStyle(html).getPropertyValue("--rozmiar").replace("px", "")) || 19;
      const i = ROZMIARY.findIndex((r) => r >= teraz);
      const nowy = ROZMIARY[Math.min(ROZMIARY.length - 1, Math.max(0, (i < 0 ? ROZMIARY.length - 1 : i) + Number(b.dataset.rozmiar)))];
      ustawRozmiar(nowy);
    }),
  );
  const przelaczPanel = (pokaz) => {
    if (!panel) return;
    panel.hidden = !pokaz;
    przyciskWygladu?.setAttribute("aria-expanded", String(pokaz));
  };
  przyciskWygladu?.addEventListener("click", (e) => { e.stopPropagation(); przelaczPanel(panel.hidden); });
  document.addEventListener("click", (e) => { if (panel && !panel.hidden && !panel.contains(e.target)) przelaczPanel(false); });

  // ---------- spis treści (wysuwany panel) ----------
  const spis = document.getElementById("spis-panel");
  const zaslona = document.getElementById("zaslona");
  const przyciskSpisu = document.getElementById("przycisk-spisu");
  const pokazSpis = (pokaz) => {
    if (!spis) return;
    spis.hidden = !pokaz;
    zaslona.hidden = !pokaz;
    przyciskSpisu?.setAttribute("aria-expanded", String(pokaz));
    if (pokaz) (spis.querySelector("a.aktualny") ?? spis.querySelector("a"))?.scrollIntoView({ block: "center" });
  };
  przyciskSpisu?.addEventListener("click", () => pokazSpis(spis.hidden));
  document.getElementById("zamknij-spis")?.addEventListener("click", () => pokazSpis(false));
  zaslona?.addEventListener("click", () => pokazSpis(false));
  spis?.querySelectorAll("ol a").forEach((a) => a.addEventListener("click", () => pokazSpis(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { pokazSpis(false); przelaczPanel(false); } });

  // podświetlenie rozdziału, który właśnie czytasz
  const rozdzialy = [...document.querySelectorAll(".tresc .rozdzial")];
  if (rozdzialy.length && "IntersectionObserver" in window) {
    const linki = new Map([...document.querySelectorAll(".spis-panel ol a")].map((a) => [a.getAttribute("href").slice(1), a]));
    const obserwator = new IntersectionObserver((wpisy) => {
      for (const w of wpisy) {
        if (!w.isIntersecting) continue;
        linki.forEach((a) => a.classList.remove("widoczny"));
        linki.get(w.target.id)?.classList.add("widoczny");
      }
    }, { rootMargin: "-20% 0px -70% 0px" });
    rozdzialy.forEach((r) => obserwator.observe(r));
  }

  // ---------- kopiowanie próśb do AI ----------
  document.querySelectorAll("[data-kopiuj]").forEach((el) =>
    el.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(el.dataset.kopiuj); } catch {}
      const t = document.getElementById("toast");
      t.textContent = "Skopiowano ✓";
      t.classList.add("widoczny");
      setTimeout(() => t.classList.remove("widoczny"), 1800);
    }),
  );
})();

// poprawione literówki: dotknięcie pokazuje zapis z oryginału (na telefonie nie ma najechania)
document.addEventListener("click", (e) => {
  const p = e.target.closest?.(".poprawka");
  if (p && !p.closest(".slucha")) p.classList.toggle("pokaz");
});
