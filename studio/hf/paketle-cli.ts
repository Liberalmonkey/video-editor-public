// npm run build sonrası: vite-node hf/paketle-cli.ts -- <klasör> [--onizleme]
//   --onizleme: ayrıca HyperFrames çalışma zamanı ve <hyperframes-player> (yerel kopya; Stüdyo CDN'e gitmez).
import { resolve } from "node:path";
import { paketle } from "./paketle";

const argv = process.argv.slice(2).filter((a) => a !== "--");
const hedef = resolve(argv.find((a) => !a.startsWith("--")) ?? "web/dist/hf");
await paketle(hedef, { onizleme: argv.includes("--onizleme") });
process.stdout.write(`HyperFrames paketleri: ${hedef}
`);
