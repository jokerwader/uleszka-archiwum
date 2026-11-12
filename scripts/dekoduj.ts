const iso = new TextDecoder("iso-8859-2");
const cp1250 = new TextDecoder("windows-1250");

/**
 * Strony deklarują kodowanie ISO-8859-2. Pojedyncze bajty 0x80–0x9F (w ISO-8859-2 to znaki sterujące)
 * pochodzą z Windows-1250 (np. „š”), więc te bajty dekodujemy jako Windows-1250.
 */
export function dekoduj(buf: Buffer): string {
  let out = "";
  let start = 0;
  for (let i = 0; i < buf.length; i++) {
    if (buf[i] >= 0x80 && buf[i] <= 0x9f) {
      out += iso.decode(buf.subarray(start, i)) + cp1250.decode(buf.subarray(i, i + 1));
      start = i + 1;
    }
  }
  return out + iso.decode(buf.subarray(start));
}
