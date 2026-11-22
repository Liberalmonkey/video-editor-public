// Program monitörünün HyperFrames yolu (ADR 0051): derleyici tarayıcıda çalışır, <hyperframes-player srcdoc> oynatır.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Önizleme ve render aynı derleyiciyi (studio/hf/derle.ts) ve aynı
// çalışma zamanı paketlerini (npm run build → dist/hf) kullanır. HyperFrames yapamıyorsa monitör Remotion oynatıcısına döner.
import { derle, desteklenmeyenler, type NativeKayit } from "../../../hf/derle";
import type { KurguProps } from "../../../remotion/tipler";

export interface OnizlemeVerisi { native: Record<string, NativeKayit>; oto_hf: boolean }
export interface MotorSecimi { motor: "hf" | "remotion"; neden: string }

let veriSozu: Promise<OnizlemeVerisi> | null = null;
export const onizlemeVerisi = (yenile = false): Promise<OnizlemeVerisi> => {
  if (!veriSozu || yenile) {
    veriSozu = fetch("/api/hf/onizleme").then((r) => {
      if (!r.ok) throw new Error(`HyperFrames önizleme verisi alınamadı (${r.status})`);
      return r.json();
    });
    veriSozu.catch(() => { veriSozu = null; });
  }
  return veriSozu;
};

let oynaticiSozu: Promise<void> | null = null;
export const oynaticiYukle = (): Promise<void> => {
  if (customElements.get("hyperframes-player")) return Promise.resolve();
  oynaticiSozu ??= new Promise<void>((tamam, hata) => {
    const s = document.createElement("script");
    s.src = "/hf/hyperframes-player.global.js";
    s.onload = () => tamam();
    s.onerror = () => { oynaticiSozu = null; hata(new Error("HyperFrames oynatıcısı yüklenemedi (npm run build)")); };
    document.head.appendChild(s);
  });
  return oynaticiSozu;
};

// hf_kurgu.motor_sec ile aynı kural: kurgu remotion isterse o; derleyici her şeyi yapıyorsa ve hız kapısı açıksa (ya da
// kurgu açıkça hf istiyorsa) HyperFrames.
export const motorSec = (k: KurguProps, v: OnizlemeVerisi | null): MotorSecimi => {
  if (k.motor === "remotion") return { motor: "remotion", neden: "kurgu motor: remotion" };
  if (!v) return { motor: "remotion", neden: "HyperFrames verisi yükleniyor" };
  const eksik = desteklenmeyenler(k, v.native);
  // Fizik ve karakter sahnesi render'da Remotion'dan ön render edilip HyperFrames'e gömülür; tarayıcıda ön render yok.
  if (eksik.length && eksik.every((e) => e === "sahne:fizik" || e === "sahne:karakter"))
    return { motor: "remotion", neden: "fizik/karakter sahnesi: önizleme Remotion'da; render HyperFrames (sahne ön render edilir)" };
  if (eksik.length) return { motor: "remotion", neden: `HyperFrames'te henüz yok: ${eksik.join(", ")}` };
  if (k.motor !== "hf" && !v.oto_hf) return { motor: "remotion", neden: "hız kapısı kapalı (library/hf_motor.json)" };
  return { motor: "hf", neden: k.motor === "hf" ? "kurgu motor: hf" : "tüm özellikler HyperFrames'te" };
};

// Önizleme kompozisyonu: proje dosyaları /pub/<stüdyo>/<ad>/ altından (fontlar, hf/tema.css), medya önizleme adresinden
// (proxy), native sahneler /hfs/ altından.
export const onizlemeHtml = (k: KurguProps & { medya?: Record<string, string> }, v: OnizlemeVerisi, studyo: string, ad: string): string => {
  const taban = `/pub/${encodeURIComponent(studyo)}/${encodeURIComponent(ad)}/`;
  const { w, h } = k.sekans;
  return derle(k, {
    mod: "onizleme", medyaUrl: (id) => k.medya?.[id] ?? "", taban,
    calismaUrl: "/hf/calisma.js", adaUrl: "/hf/ada.js", gsapUrl: "/hf/gsap.min.js", cekirdekUrl: "/hf/native/cekirdek.js",
    temaCssUrl: `${taban}hf/tema.css`, native: v.native,
    sahneUrl: (kok, bilesen) => `/hfs/${bilesen.replace("/", "-")}/${kok}/${w}x${h}.html`,
  }).html;
};
