import fs from "node:fs";
import path from "node:path";
import { Config } from "@remotion/cli/config";

// WHY: bkz. wiki/decisions/0016-earshot-render-standardi-ajan-duzeni.md. openmontage ayarlarıyla aynı.
Config.setVideoImageFormat("png");
Config.setColorSpace("bt709");
Config.setCrf(16);
if (!process.argv.some((a) => a.includes("vp9") || a.includes("prores"))) Config.setX264Preset("slow");
Config.setAudioBitrate("320k");

// WHY: SplitReel openmontage altında durur; takma ad olmadan ikinci remotion ve react kopyası yüklenir.
const nm = path.resolve(process.cwd(), "node_modules");
Config.overrideWebpackConfig((c) => ({
  ...c,
  resolve: {
    ...c.resolve,
    alias: {
      ...(c.resolve?.alias ?? {}),
      remotion: path.join(nm, "remotion"),
      react: path.join(nm, "react"),
      "react-dom": path.join(nm, "react-dom"),
    },
  },
}));

// openmontage'ın indirdiği Chrome varsa ikinci kez indirme.
const chrome = path.resolve(
  process.cwd(),
  "../openmontage/remotion-composer/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe",
);
if (fs.existsSync(chrome)) Config.setBrowserExecutable(chrome);
