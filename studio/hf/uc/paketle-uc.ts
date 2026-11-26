// three.js HyperFrames çekirdeğini tek IIFE pakete çevirir: library/vendor/uc.js (window.HFUC).
// WHY: bkz. wiki/decisions/0063-gsap-eklentileri-ve-threejs-hf.md. Şablon klasik <script src="uc.js"> ile yükler;
// HyperFrames render kopyası proje dışını okumaz, vedit dosyayı kopyaya koyar (hf_grafik._hazirla).
import { build } from "esbuild";
import { statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const burasi = dirname(fileURLToPath(import.meta.url));
const hedef = resolve(burasi, "../../../library/vendor/uc.js");
await build({ entryPoints: [join(burasi, "uc.ts")], bundle: true, format: "iife", target: "es2020", minify: true,
  outfile: hedef, logLevel: "error", legalComments: "inline",
  banner: { js: "/* HFUC: three.js 0.172.0 (MIT) + çekirdek. Üretim: studio npm run uc. Elle düzenlenmez. */" } });
process.stdout.write(`uc.js: ${Math.round(statSync(hedef).size / 1024)} KB\n`);
