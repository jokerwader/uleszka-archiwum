/**
 * Znacznik wersji pliku do adresu (np. „atlas.css?v=3f9a1c2b”): skrót z treści pliku.
 * Gdy plik się zmieni, zmienia się adres, więc przeglądarka nie użyje starej kopii z pamięci.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

export const wersja = (sciezka: string) => createHash("sha1").update(readFileSync(sciezka)).digest("hex").slice(0, 8);
export const zWersja = (adres: string, sciezka: string) => `${adres}?v=${wersja(sciezka)}`;
