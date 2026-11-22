// Node girişi: render props (kurgu.render.json) → HyperFrames proje klasörü. vedit (hizli.py) çağırır.
// Kullanım: vite-node hf/cli.ts -- <props.json> <proje-klasörü> [--denetle] [--olcek 0.5] [--pencere a,b]
// --denetle: yalnız desteklenmeyen listesini JSON yazar (motor seçimi); --on-render ile fizik/karakter ön render edilebilir sayılır.
// --onrender <json>: klip kimliği → ön render webm adresi (hf_kurgu yazar). Aksi halde index.html, hf/*.js ve hf/n/ bağlamaları.
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import type { KurguProps } from "../remotion/tipler";
import { derle, desteklenmeyenler } from "./derle";
import { nativeHarita, paketle, sahneKopyasi } from "./paketle";

const argv = process.argv.slice(2).filter((a) => a !== "--");
const [propsYol, projeYol] = argv;
const p = JSON.parse(readFileSync(propsYol, "utf-8")) as KurguProps;
const native = nativeHarita();

if (argv.includes("--denetle")) {
  process.stdout.write(JSON.stringify({ desteklenmeyen: desteklenmeyenler(p, native, { onRender: argv.includes("--on-render") }) }) + "\n");
  process.exit(0);
}

const proje = resolve(projeYol);
await paketle(join(proje, "hf"));
const medyaUrl = (id: string) => {
  const y = p.kaynaklar[id].yol;
  if (y.startsWith("public:")) return y.slice(7);
  return `_k/${id}${y.slice(y.lastIndexOf(".")).toLowerCase()}`;
};
const deger = (ad: string) => { const i = argv.indexOf(ad); return i >= 0 ? argv[i + 1] : undefined; };
const olcek = deger("--olcek") ? Number(deger("--olcek")) : 1;
const pencere = deger("--pencere") ? deger("--pencere")!.split(",").map(Number) as [number, number] : null;
const onRender = deger("--onrender") ? JSON.parse(readFileSync(deger("--onrender")!, "utf-8")) as Record<string, string> : undefined;
const s = derle(p, { mod: "render", medyaUrl, calismaUrl: "hf/calisma.js", adaUrl: "hf/ada.js", gsapUrl: "hf/gsap.min.js",
  cekirdekUrl: "hf/native/cekirdek.js", native, onRender,
  temaCssUrl: existsSync(join(proje, "hf", "tema.css")) ? "hf/tema.css" : null, olcek, pencere });
rmSync(join(proje, "hf", "n"), { recursive: true, force: true });
mkdirSync(join(proje, "hf", "n"), { recursive: true });
for (const b of s.baglamalar) {
  writeFileSync(join(proje, b.src), sahneKopyasi(readFileSync(native[b.ad].dosya, "utf-8"), b.kok, p.sekans.w, p.sekans.h), "utf-8");
}
writeFileSync(join(proje, "index.html"), s.html, "utf-8");
process.stdout.write(JSON.stringify({ desteklenmeyen: s.desteklenmeyen, bitis: s.bitis }) + "\n");
