// Menu górne całej strony: na wąskich ekranach linki chowają się pod przyciskiem „hamburgera”.
// Używają go: strona główna, czytelnia i atlas (przycisk .hamburger z aria-controls wskazującym panel z linkami).
(() => {
  const przycisk = document.querySelector(".hamburger");
  const panel = przycisk && document.getElementById(przycisk.getAttribute("aria-controls"));
  if (!przycisk || !panel) return;
  const otwarte = () => przycisk.getAttribute("aria-expanded") === "true";
  const ustaw = (tak) => {
    przycisk.setAttribute("aria-expanded", String(tak));
    przycisk.setAttribute("aria-label", tak ? "Zamknij menu" : "Otwórz menu");
    document.documentElement.classList.toggle("menu-otwarte", tak);
  };
  przycisk.addEventListener("click", (e) => { e.stopPropagation(); ustaw(!otwarte()); });
  panel.addEventListener("click", (e) => { if (e.target.closest("a")) ustaw(false); });
  document.addEventListener("click", (e) => { if (otwarte() && !panel.contains(e.target)) ustaw(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && otwarte()) { ustaw(false); przycisk.focus(); } });
  matchMedia("(min-width: 821px)").addEventListener("change", (m) => { if (m.matches) ustaw(false); });

  // strona główna: menu nad sceną 3D dostaje tło dopiero po przewinięciu
  const pasek = document.querySelector(".pasek");
  if (pasek) {
    const tlo = () => pasek.classList.toggle("przewiniete", scrollY > 40);
    addEventListener("scroll", tlo, { passive: true });
    tlo();
  }
})();
