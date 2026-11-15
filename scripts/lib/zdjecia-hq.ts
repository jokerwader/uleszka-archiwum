/**
 * Zdjęcia wysokiej jakości z Wikimedia Commons (te z Atlasu Leszka) pobierane do pamięci podręcznej
 * podcast/.zdjecia/ (folder w .gitignore) – do filmów na YouTube. Pobieranie po kolei, z przerwami,
 * bo serwery Wikimedia odrzucają zbyt szybkie serie zapytań (kod 429).
 */
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { ZdjecieCommons } from "./atlas.js";

const FOLDER = "podcast/.zdjecia";
const UA = { "User-Agent": "uleszka-archiwum-wideo/1.0 (https://github.com/jokerwader/uleszka-archiwum)" };
const czekaj = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Zwraca ścieżkę pobranego pliku albo null, gdy się nie udało. */
export async function pobierzZdjecie(z: ZdjecieCommons): Promise<string | null> {
  mkdirSync(FOLDER, { recursive: true });
  const nazwa = z.plik.normalize("NFD").replace(/[^\w.-]+/g, "_").replace(/_+/g, "_").slice(-120);
  const plik = join(FOLDER, nazwa.toLowerCase().endsWith(".jpg") || nazwa.toLowerCase().endsWith(".jpeg") ? nazwa : `${nazwa}.jpg`);
  if (existsSync(plik)) return plik;
  for (let proba = 0; proba < 5; proba++) {
    const r = await fetch(z.duze, { headers: UA }).catch(() => null);
    if (r?.ok) {
      writeFileSync(plik, Buffer.from(await r.arrayBuffer()));
      await czekaj(700);
      return plik;
    }
    if (r && r.status !== 429 && r.status < 500) return null;
    await czekaj(4000 * (proba + 1));
  }
  return null;
}

/** Krótki podpis autorstwa do wideo: „fot. Jan Kowalski, CC BY-SA 4.0 · Wikimedia Commons”. */
export const podpisAutora = (z: ZdjecieCommons) => {
  const autor = z.autor.replace(/\s+/g, " ").trim();
  return `fot. ${autor.length > 45 ? `${autor.slice(0, 44)}…` : autor}, ${z.licencja} · Wikimedia Commons`;
};
