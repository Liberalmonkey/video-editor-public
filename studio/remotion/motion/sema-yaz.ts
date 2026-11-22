// npm run sema: her native bileşenin Zod şemasını JSON Schema'ya çevirir, meta.json ile birlikte
// library/motion/native/sema.json'a yazar. Python (kurgu-denetle, ai-edit kataloğu) yalnız bu dosyayı okur (ADR 0045).
// --denetle: dosya güncel değilse çıkış kodu 1.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { TUMU } from "./kayit";

const kok = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const hedef = path.join(kok, "library", "motion", "native", "sema.json");

export const semaMetni = () => {
  const bilesenler: Record<string, unknown> = {};
  for (const t of [...TUMU].sort((a, b) => a.meta.ad.localeCompare(b.meta.ad))) {
    const sema = z.toJSONSchema(t.sema, { io: "input", target: "draft-2020-12" }) as Record<string, unknown>;
    bilesenler[t.meta.ad] = { meta: t.meta, sema };
  }
  return JSON.stringify({ surum: 1, bilesenler }, null, 1) + "\n";
};

export const SEMA_DOSYASI = hedef;
export const guncelMi = () => (fs.existsSync(hedef) ? fs.readFileSync(hedef, "utf-8") : "") === semaMetni();

// Giriş noktası sema-calistir.ts (vite-node argv'den betik adını siler; burada main tespiti yapılamaz).
export const yaz = () => {
  const metin = semaMetni();
  if (guncelMi()) return false;
  fs.mkdirSync(path.dirname(hedef), { recursive: true });
  fs.writeFileSync(hedef, metin, "utf-8");
  console.log(`yazıldı: ${path.relative(kok, hedef)} (${TUMU.length} bileşen)`);
  return true;
};
