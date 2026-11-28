// kurgu.json (render props) → HyperFrames kompozisyonu. Tarayıcıda (önizleme srcdoc) ve Node'da (render) aynı kod.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Remotion'daki Kurgu.tsx'in HyperFrames karşılığı:
// medya HyperFrames klibidir (zamanı ve sesi motor yönetir), dönüşüm ve efektler çalışma zamanında (calisma.ts) tek
// paused GSAP zaman çizelgesinin onUpdate'inde hesaplanır. Henüz taşınmamış özellik `desteklenmeyen` listesine girer;
// liste boş değilse motor seçimi Remotion'a düşer (son çare).
import type { Iz, Klip, KurguProps } from "../remotion/tipler";
import { izdusum, sesEgrisi } from "../remotion/izdusum";
import type { MotionMeta } from "../remotion/motion/cekirdek/tipler";
import { altyaziBandi, guvenliAlan, platformBolgeleri, yerles, yuzPayi } from "../remotion/motion/cekirdek/yerlesim";
import type { Yer as NativeYer } from "./native/cekirdek";
import type { AdaKayit } from "./ada";
import { CAP_VARSAYILAN, kutuStili, type AltyaziVeri } from "./altyazi";
import { dbGuc, kuyrukPayi, onPayi, ortaMi, sahneZemin } from "./zaman";

export interface DerleOrtam {
  mod: "render" | "onizleme";
  medyaUrl: (id: string) => string;          // kaynak id → kompozisyona göre adres
  calismaUrl: string;                         // çalışma zamanı betiği
  adaUrl?: string;                            // React adası (metin grafik, sahne); yalnız ada varsa yüklenir
  gsapUrl: string;
  temaCssUrl?: string | null;                 // seçili stilin token CSS'i (@font-face dahil)
  // WHY: ADR 0051 hız. Taslak yarım çözünürlükte çizilir (Remotion --scale=0.5 karşılığı): yakalanan piksel 4'te 1.
  olcek?: number;
  // HyperFrames'e taşınmış native bileşenler (library/motion/hf/<aile>-<ad>/sahne.html): ad → meta ve param varsayılanı.
  // Listede olmayan native klip `desteklenmeyen`e düşer (motor Remotion).
  native?: Record<string, NativeKayit>;
  // Canlı HF grafik kompozisyonları (library/motion/hf/<ad>/index.html ve work/edit/hf/<ad>/index.html): ad → ölçü/varsayılan.
  grafikler?: Record<string, { w: number; h: number; sure: number; varsayilan: Record<string, unknown> }>;
  cekirdekUrl?: string;                       // window.HFN (studio/hf/native/cekirdek.ts paketi)
  // Bir native bağlamasının sahne adresi. Render: cli.ts hf/n/<kök>.html yazar. Önizleme: sunucu /hfs/ altından üretir.
  sahneUrl?: (kok: string, ad: string) => string;
  // Canlı HF grafik bağlamasının adresi. Render: cli.ts hf/g/<kök>.html yazar. Önizleme: sunucu /hfg/ altından üretir.
  grafikUrl?: (kok: string, ad: string) => string;
  // Render-time motion blur (data-motion-blur="on"): hızlı optik geçiş/kamera hareketlerinde seçmeli.
  hareketBulaniklik?: boolean;
  // Fizik ve karakter sahneleri (three.js, ADR 0039): klip kimliği → Remotion'da ön render edilmiş saydam webm adresi.
  // HyperFrames içinde video klibi olarak oynar; projenin geri kalanı HyperFrames'te kalır (ADR 0051 son çare yolu).
  onRender?: Record<string, string>;
  // Önizleme: göreli adreslerin (fontlar, hf/) çözüleceği yer, <base href>. srcdoc'un kendi adresi yoktur.
  taban?: string | null;
  // Aralık render'ı: yalnız [a, b) penceresine değen klipler derlenir, zaman a'dan başlar. HyperFrames her medya
  // klibinin karelerini çıkarıp özetler; pencere dışındaki klipler bu maliyeti boşuna ödetiyordu.
  pencere?: [number, number] | null;
}

export interface NativeKayit { meta: MotionMeta; varsayilan: Record<string, unknown> }
// Bir native ya da grafik bağlaması: cli.ts sahne dosyasını `kok` adıyla kopyalar (__KOK__, __W__, __H__ doldurulur).
export interface Baglama { kok: string; ad: string; src: string }
export interface DerleSonuc { html: string; desteklenmeyen: string[]; bitis: number; baglamalar: Baglama[]; grafikBaglamalar: Baglama[] }

// Çalışma zamanının okuduğu sade klip kaydı.
export interface CizKlip {
  id: string; tur: Klip["tur"]; bas: number; sure: number; on: number; kuyruk: number;
  konusmaci: boolean; zoom: number; punches: Klip["punches"]; giris: number; hiz: number;
  donus: Klip["donus"]; efekt: Klip["efekt"]; gecis_giris?: Klip["gecis_giris"]; gecis_cikis?: Klip["gecis_cikis"];
  cikis: Klip["gecis_giris"]; hazir?: Klip["hazir"];
  ham?: boolean; // Kurgu.tsx'te Donusum'a sarılmayan katman (tam ekran sahne): dönüşüm ve geçiş uygulanmaz
}

const kac = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const sn = (n: number) => String(Math.round(n * 1000) / 1000);

type GrafikOlcu = { w: number; h: number };
type DestekSecenek = { onRender?: boolean | Record<string, string>; grafikler?: Record<string, GrafikOlcu> };
type KlipYol =
  | { yol: "canliHf" | "medya" | "native" | "gorsel" | "metinGrafik" | "metin" | "onRender" | "tamSahne" | "bolunmusSahne" | "ses" | "atla" }
  | { yol: "yok"; neden: string };

// WHY: desteklenmeyenler() ve derle() aynı kararı vermezse HF'de çizilemeyen klip destekli sayılıp sessizce kaybolur.
const klipYolu = (
  k: Klip,
  sekans: { w: number; h: number },
  native: Record<string, unknown> = {},
  secenek: DestekSecenek = {},
): KlipYol => {
  if (k.tur === "ses") return { yol: "ses" };
  if (k.tur === "motion") {
    if (k.bilesen) return native[k.bilesen.ad] ? { yol: "native" } : { yol: "yok", neden: `native:${k.bilesen.ad}` };
    const gy = k.hf?.ad ? secenek.grafikler?.[k.hf.ad] : undefined;
    // Canlı gömme yalnız özel tema yoksa ve kompozisyon sekansla aynı yöndeyse; aksi halde WebM kaynağı (k.kaynak) gerekir.
    if (k.hf?.ad && gy && !k.hf.tema && (gy.w >= gy.h) === (sekans.w >= sekans.h)) return { yol: "canliHf" };
    return k.kaynak ? { yol: "medya" } : { yol: "yok", neden: "motion:kaynaksız" };
  }
  if (k.tur === "video") return k.kaynak ? { yol: "medya" } : { yol: "yok", neden: "video:kaynaksız" };
  if (k.tur === "gorsel") return k.kaynak ? { yol: "gorsel" } : { yol: "yok", neden: "gorsel:kaynaksız" };
  if (k.tur === "metin") return k.metin_stil?.tip ? { yol: "metinGrafik" } : { yol: "metin" };
  if (k.tur === "sahne") {
    // Metin grafikleri ve sahneler React adasında (ada.tsx). Fizik ve karakter yalnız render'da, ön render ile (önizleme Remotion).
    if (k.sahne?.kind === "fizik" || k.sahne?.kind === "karakter") {
      const hazir = typeof secenek.onRender === "boolean" ? secenek.onRender : !!secenek.onRender?.[k.id];
      return hazir ? { yol: "onRender" } : { yol: "yok", neden: `sahne:${k.sahne.kind}` };
    }
    if (k.sahne?.layout === "split") return { yol: "bolunmusSahne" };
    if (k.sahne?.layout === "full" && k.sahne.kind) return { yol: "tamSahne" };
    // WHY: yerleşimi split/full olmayan sahneyi Remotion da çizmez (Kurgu.tsx); desteklenmeyen saymak yalnız motoru boşuna değiştirir.
    return { yol: "atla" };
  }
  return { yol: "yok", neden: `tur:${String(k.tur)}` };
};

// Taşınan özellikler dışında kalanlar. Her Faz 1 adımı buradan bir maddeyi siler (ADR 0051).
export const desteklenmeyenler = (
  p: KurguProps,
  native: Record<string, unknown> = {},
  secenek: DestekSecenek = {},
): string[] => {
  const d = new Set<string>();
  const izler = new Map(p.izler.map((i) => [i.id, i]));
  for (const k of p.klipler) {
    if (izler.get(k.iz)?.gizli) continue;
    const sonuc = klipYolu(k, p.sekans, native, secenek);
    if (sonuc.yol === "yok") d.add(sonuc.neden);
  }
  return [...d].sort();
};

const sirali = (p: KurguProps) => {
  const m = new Map<string, Klip[]>();
  for (const c of p.klipler) m.set(c.iz, [...(m.get(c.iz) ?? []), c]);
  for (const l of m.values()) l.sort((a, b) => a.bas - b.bas);
  return m;
};

// Kazanç keyframe'i (ses.kf, ducking): Remotion'un sesEgrisi'si (kazanç, kf, fade, geçiş, kuyruk) kare kare örneklenip
// HyperFrames ses zarfına (data-automation volume şeridi, t öğenin başından sn) yazılır; iki motor aynı eğriyi çalar.
// on: orta noktalı geçişin ön payı (Kurgu.tsx onluSes), kayma: pencereli derlemede öğenin kesilen başı.
const ZARF_NOKTA = 400; // HyperFrames şerit başına en çok 512 nokta
const sesZarfi = (k: Klip, iz: Iz, fps: number, kuyruk: number, on: number, kayma: number): string => {
  const egri = sesEgrisi(k, iz.gain_db, fps, kuyruk);
  const onKare = Math.round(on * fps);
  const n = Math.ceil((k.sure + on + kuyruk) * fps);
  const adim = Math.max(1, Math.ceil(n / ZARF_NOKTA));
  const noktalar: { t: number; v: number }[] = [];
  for (let e = 0; e <= n; e += adim) {
    const t = e / fps - kayma;
    if (t < -adim / fps) continue;
    const v = e < onKare ? 0 : egri(e - onKare);
    noktalar.push({ t: Math.max(0, +t.toFixed(4)), v: +Math.min(3.98, Math.max(0, v)).toFixed(4) });
  }
  return JSON.stringify({ version: 1, lanes: [{ target: "volume", points: noktalar }] });
};

// Ses: klip kendi sesini taşır (data-has-audio). Geçiş girişi ve çapraz kuyruk HyperFrames fade'iyle; ses.kf zarfla.
const sesNitelik = (k: Klip, iz: Iz, kuyruk: number, sessiz: boolean, zarf?: { fps: number; on: number; kayma: number }): string => {
  if (sessiz) return "muted";
  if (k.ses.kf?.length && zarf) {
    return `data-has-audio="true" data-automation="${kac(sesZarfi(k, iz, zarf.fps, kuyruk, zarf.on, zarf.kayma))}"`;
  }
  const gGiris = k.gecis_giris && k.gecis_giris.tur !== "kaydir" ? k.gecis_giris.sure : 0;
  const fi = Math.max(k.ses.fade_in, gGiris), fo = kuyruk > 0 ? kuyruk : k.ses.fade_out;
  return `data-has-audio="true" data-volume="${sn(dbGuc(k.ses.gain_db + iz.gain_db))}"`
    + (fi > 0 ? ` data-fade-in="${sn(fi)}"` : "") + (fo > 0 ? ` data-fade-out="${sn(fo)}"` : "");
};

// Pencereye göre klip zamanı: kesişim yoksa null; başı pencereden önceyse medya başı ileri kayar.
const kes = (bas: number, sure: number, medya: number, hiz: number, pen: [number, number] | null) => {
  if (!pen) return { bas, sure, medya };
  const a = Math.max(bas, pen[0]), b = Math.min(bas + sure, pen[1]);
  if (b - a <= 1e-3) return null;
  return { bas: a - pen[0], sure: b - a, medya: medya + (a - bas) * hiz };
};

export const derle = (p: KurguProps, o: DerleOrtam): DerleSonuc => {
  const { w, h, fps } = p.sekans;
  const tamBitis = p.bitis ?? Math.max(0.04, ...p.klipler.map((c) => c.bas + c.sure));
  const pen = o.pencere ? [Math.max(0, o.pencere[0]), Math.min(tamBitis, o.pencere[1])] as [number, number] : null;
  const bitis = pen ? pen[1] - pen[0] : tamBitis;
  const olcek = o.olcek && o.olcek > 0 && o.olcek !== 1 ? o.olcek : 1;
  const W = Math.round(w * olcek), H = Math.round(h * olcek);
  const izler = new Map(p.izler.map((i) => [i.id, i]));
  const s = sirali(p);
  const ciz: CizKlip[] = [];
  const katman: string[] = [];
  const adalar: AdaKayit[] = [];
  const kare = (n: number) => Math.round(n * fps);
  const ada = (a: AdaKayit) => { adalar.push(a); return `<div class="kz-ada" id="ada-${a.id}"></div>`; };
  const yatay = w > h;
  const baglamalar: Baglama[] = [];
  const grafikBaglamalar: Baglama[] = [];
  const hfParamlar: Record<string, Record<string, unknown>> = {};
  const yerler: Record<string, NativeYer> = {};
  // Katman.tsx + Kurgu.tsx bolgeKaynagi: yerleşim klibin girişinde bir kez, klip boyunca görünen yüzlerden ve altyazı bandından kaçar.
  const altyaziY = p.altyazi.stil?.konum != null ? p.altyazi.stil.konum * h : yatay ? 945 : 1402;
  const nativeYer = (k: Klip, nk: NativeKayit): NativeYer => {
    const basKare = kare(k.bas), sureKare = Math.max(1, kare(k.sure));
    const t0 = basKare / fps, t1 = (basKare + sureKare) / fps;
    const yuzler = (p.bolgeler?.yuzler ?? []).filter((a) => a.son > t0 && a.bas <= t1)
      .flatMap((a) => a.kutular.map((b) => yuzPayi({ x: b.x * w, y: b.y * h, w: b.w * w, h: b.h * h })));
    const bol = { guvenli: guvenliAlan(w, h), altyazi: p.altyazi.acik ? altyaziBandi(w, altyaziY, p.altyazi.stil?.boyut ?? 84) : null,
      yuzler, platform: platformBolgeleri(w, h) };
    const b = k.bilesen!;
    const hedefPx = b.hedef ? { x: b.hedef.x * w, y: b.hedef.y * h } : null;
    const s = yerles(nk.meta, w, h, bol, b.yer && b.yer !== "oto" ? b.yer : undefined, hedefPx);
    const { odakKarart, ...ham } = (b.param ?? {}) as Record<string, unknown>;
    return {
      kutu: s.kutu, u: Math.min(w, h) / 1080, hedef: hedefPx && { x: hedefPx.x - s.kutu.x, y: hedefPx.y - s.kutu.y },
      sureKare, fps, ofset: pen && basKare / fps < pen[0] ? pen[0] - basKare / fps : 0,
      giris_sn: nk.meta.giris_sn, cikis_sn: nk.meta.cikis_sn, karart: b.odak_karart === true || odakKarart === true, w, h,
      param: { ...nk.varsayilan, ...ham },
    };
  };

  // Bölünmüş sahneler en altta (Kurgu.tsx): tam ekrana dönüşte 10 kare daha kalır, panel kapanırken arkası boş görünmez.
  // Düzen ilerlemesi (layoutP): 4-düzen (ADR 0062) + bölünmüş sahneler.
  const sahneler = p.klipler.filter((c) => c.tur === "sahne").sort((a, b) => a.bas - b.bas)
    .map((c) => ({ layout: c.sahne?.layout ?? null, duzen: c.sahne?.duzen ?? null, start: c.bas }));
  for (const k of p.klipler.filter((c) => !izler.get(c.iz)?.gizli && klipYolu(c, p.sekans, o.native, o).yol === "bolunmusSahne").sort((a, b) => a.bas - b.bas)) {
    const sonra = sahneler.find((x) => x.start >= k.bas + k.sure - 0.001);
    const sure = Math.max(1, kare(k.sure)) + (sonra?.layout === "full" ? 10 : 0);
    if (pen && (k.bas + sure / fps <= pen[0] || k.bas >= pen[1])) continue;
    katman.push(ada({ id: `st${k.id}`, tur: "bolunmus", bas: kare(k.bas), sure, sahne: { ...k.sahne, start: k.bas, end: k.bas + k.sure } }));
  }
  let serit = 0;

  // İz listesi Premiere gibi üstten alta; çizim alttan üste (Kurgu.tsx ile aynı).
  for (const iz of [...p.izler].reverse().filter((i) => i.tur === "video" && !i.gizli)) {
    const l = s.get(iz.id) ?? [];
    serit += 2; // çapraz geçişte örtüşen klipler komşu şeride düşer (Studio şeridi; miks değişmez)
    l.forEach((k, i) => {
      const kuyruk = kuyrukPayi(p, k, l[i + 1]);
      const on = onPayi(k);
      const sonra = l[i + 1];
      const cikis = kuyruk > 0 && sonra && ortaMi(sonra.gecis_giris) ? sonra.gecis_giris : null;
      const z = kes(k.bas - on, k.sure + on + kuyruk, Math.max(0, k.giris - on * k.hiz), k.hiz, pen);
      if (!z) return;
      const ortak = `data-start="${sn(z.bas)}" data-duration="${sn(z.sure)}" data-track-index="${serit - 1 + (i % 2)}"`;
      let ic = "";
      // Canlı gömme yalnız kompozisyon sekansla aynı yöndeyse; 16:9 şablon 9:16 sekansta sekans boyutunda WebM'iyle gelir
      // (hf_grafik.ayni_yon ile aynı kural). WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md.
      const yol = klipYolu(k, p.sekans, o.native, o).yol;
      if (yol === "canliHf") {
        // Canlı HF grafik kompozisyonu (ADR 0051 Faz 1 Adım 6 / ADR 0062): çevrimdışı WebM olmadan doğrudan alt kompozisyon.
        const kok = `g-${k.id.replace(/[^A-Za-z0-9_-]/g, "_")}`;
        const gk = o.grafikler![k.hf!.ad];
        // WHY: pencereli derlemede klip pencereye yalnız geçiş ön payı/kuyruğuyla değiyorsa sz null olur; çökme ve bozuk bağlama önlenir.
        const sz = kes(kare(k.bas) / fps, Math.max(1, kare(k.sure)) / fps, 0, 1, pen);
        if (!sz) return;
        hfParamlar[kok] = { ...gk.varsayilan, ...(k.hf!.param ?? {}) };
        const src = o.grafikUrl ? o.grafikUrl(kok, k.hf!.ad) : `hf/g/${kok}.html`;
        grafikBaglamalar.push({ kok, ad: k.hf!.ad, src });
        const pay = sz.bas > 0 ? 0.01 / fps : 0;
        ic = `<div id="${kok}" data-composition-id="${kok}" data-composition-src="${kac(src)}" data-start="${+(sz.bas - pay).toFixed(6)}" data-duration="${+(sz.sure + pay).toFixed(6)}"`
          + ` data-track-index="${serit - 1 + (i % 2)}" data-width="${w}" data-height="${h}"`
          + ` data-variable-values="${kac(JSON.stringify(hfParamlar[kok]))}" style="position:absolute;inset:0"></div>`;
      } else if (yol === "medya") {
        const sessiz = iz.sessiz || k.tur === "motion" || !!k.ses_kapali;
        const medya = `id="m-${k.id}" class="clip" src="${kac(o.medyaUrl(k.kaynak!))}" ${ortak}`
          + ` data-media-start="${sn(z.medya)}"` + (k.hiz !== 1 ? ` data-playback-rate="${sn(k.hiz)}"` : "")
          + ` ${sesNitelik(k, iz, kuyruk, sessiz, { fps, on, kayma: pen ? Math.max(0, pen[0] - (k.bas - on)) : 0 })} playsinline`;
        // Konuşmacı paneli bölünmüş sahnede iner (dikey) ya da sağa çekilir (yatay); video panelden bağımsız tam kare boyutunda.
        ic = k.konusmaci
          ? `<div class="kz-panel" id="p-${k.id}"><div class="kz-odak" id="o-${k.id}"><video ${medya} style="position:absolute;left:0;top:0;width:${w}px;height:${h}px;object-fit:cover;transform-origin:${yatay ? "50% 50%" : "50% 0%"}"></video></div></div>`
          : `<video ${medya} style="width:100%;height:100%;object-fit:contain"></video>`;
      } else if (yol === "native") {
        // Native bileşen HyperFrames sahnesidir: alt kompozisyon, kendi saati host'un data-start'ında 0'dan başlar.
        const kok = `n-${k.id.replace(/[^A-Za-z0-9_-]/g, "_")}`;
        const nk = o.native![k.bilesen!.ad];
        // Remotion Sequence from = round(bas·fps): host da kare ızgarasında başlar, yoksa sahne saati yarım kare kayar.
        // WHY: pencereli derlemede klip pencereye yalnız geçiş ön payı/kuyruğuyla değiyorsa sz null olur; çökme ve bozuk bağlama önlenir.
        const sz = kes(kare(k.bas) / fps, Math.max(1, kare(k.sure)) / fps, 0, 1, pen);
        if (!sz) return;
        yerler[kok] = nativeYer(k, nk);
        const src = o.sahneUrl ? o.sahneUrl(kok, k.bilesen!.ad) : `hf/n/${kok}.html`;
        baglamalar.push({ kok, ad: k.bilesen!.ad, src });
        // data-start ms'ye yuvarlanınca (50/30 → 1.667) HyperFrames sahneyi bir kare geç açıyordu: başlangıç kare sınırının
        // 0,01 kare önüne, tam hassasiyetle yazılır; sahne karesi round(t·fps) olduğundan ilk kare yine 0'dır.
        const pay = sz.bas > 0 ? 0.01 / fps : 0;
        ic = `<div id="${kok}" data-composition-id="${kok}" data-composition-src="${kac(src)}" data-start="${+(sz.bas - pay).toFixed(6)}" data-duration="${+(sz.sure + pay).toFixed(6)}"`
          + ` data-track-index="${serit - 1 + (i % 2)}" data-width="${w}" data-height="${h}"`
          + ` data-variable-values="${kac(JSON.stringify(yerler[kok].param))}" style="position:absolute;inset:0"></div>`;
      } else if (yol === "gorsel") {
        ic = `<img id="m-${k.id}" class="clip" src="${kac(o.medyaUrl(k.kaynak!))}" ${ortak} alt="" style="width:100%;height:100%;object-fit:contain">`;
        // Kurgu.tsx: görselin vurgu izi aynı Sequence içinde (kare görsel klibinin başından).
        if (k.metin_stil?.tip === "vurgu") ic += ada({ id: k.id, tur: "vurgu", bas: kare(k.bas - on), sure: Math.max(1, kare(k.sure + on) + kare(kuyruk)),
          klip: k, kaynak: p.kaynaklar[k.kaynak!] ?? null });
      } else if (yol === "metinGrafik") {
        ic = ada({ id: k.id, tur: "metin", bas: kare(k.bas), sure: Math.max(1, kare(k.sure) + kare(kuyruk)), klip: k });
      } else if (yol === "onRender") {
        // Ön render: Kurgu.tsx'teki Donusum dahil çizildi; burada dönüşüm uygulanmaz (ham).
        ic = `<video id="m-${k.id}" class="clip" src="${kac(o.onRender![k.id])}" ${ortak} data-media-start="${sn(z.medya)}" muted playsinline`
          + ` style="width:100%;height:100%;object-fit:contain"></video>`;
      } else if (yol === "tamSahne") {
        const baslik = k.sahne!.kind === "hook" || k.sahne!.kind === "cta";
        ic = ada({ id: k.id, tur: baslik ? "baslik" : "tam", bas: kare(k.bas), sure: Math.max(1, kare(k.sure)), sahne: { ...k.sahne, start: k.bas, end: k.bas + k.sure } });
      } else if (yol === "metin") {
        const m = k.metin_stil ?? {};
        const boyut = m.boyut ?? 96;
        ic = `<div id="m-${k.id}" class="clip kz-metin" ${ortak} style="font-size:${boyut}px;-webkit-text-stroke:${sn(boyut * 0.05)}px var(--kontur-renk, #000)`
          + (m.font ? `;font-family:'${kac(m.font)}'` : "") + (m.renk ? `;color:${kac(m.renk)}` : "") + `">${kac(k.metin ?? "")}</div>`;
      } else {
        return; // bölünmüş sahne ayrı çizildi; desteklenmeyen tür desteklenmeyenler() ile Remotion'a düşer
      }
      const karisim = (p.tema as { karisim?: Record<string, string> } | undefined)?.karisim?.[k.kaynak ?? ""] === "screen" ? ";mix-blend-mode:screen" : "";
      // Sarma sırası Kurgu.tsx ile aynı: çıkış geçişi dışta, giriş geçişi içte, dönüşüm en içte; ışık katmanları kardeş.
      katman.push(`<div class="kz-k" id="k-${k.id}" style="visibility:hidden${karisim}"><div class="kz-t" id="cx-${k.id}"><div class="kz-t" id="gx-${k.id}">`
        + `<div class="kz-t" id="d-${k.id}">${ic}</div></div><div class="kz-t kz-gk" id="gkg-${k.id}"></div></div><div class="kz-t kz-gk" id="gkc-${k.id}"></div></div>`);
      ciz.push({ id: k.id, tur: k.tur, bas: k.bas, sure: k.sure, on, kuyruk, konusmaci: k.konusmaci, zoom: k.zoom, punches: k.punches,
        giris: k.giris, hiz: k.hiz, donus: k.donus, efekt: k.efekt, gecis_giris: k.gecis_giris, gecis_cikis: k.gecis_cikis, cikis, hazir: k.hazir,
        ...(k.tur === "sahne" ? { ham: true } : {}) });
    });
  }

  // Ayrı ses izleri: <audio> klibi (gain, fade). Sessiz iz karışmaz.
  for (const iz of p.izler.filter((i) => i.tur === "ses" && !i.sessiz)) {
    for (const k of s.get(iz.id) ?? []) {
      if (k.tur !== "ses" || !k.kaynak) continue;
      const z = kes(k.bas, k.sure, k.giris, k.hiz, pen);
      if (!z) continue;
      katman.push(`<audio id="a-${k.id}" class="clip" src="${kac(o.medyaUrl(k.kaynak))}" data-start="${sn(z.bas)}" data-duration="${sn(z.sure)}"`
        + ` data-media-start="${sn(z.medya)}"` + (k.hiz !== 1 ? ` data-playback-rate="${sn(k.hiz)}"` : "") + ` data-track-index="${++serit}" `
        + `${sesNitelik(k, iz, 0, false, { fps, on: 0, kayma: pen ? Math.max(0, pen[0] - k.bas) : 0 }).replace('data-has-audio="true" ', "")}></audio>`);
    }
  }

  // Altyazı (ADR 0014/0043): stil kurguda verildiyse o, seçili stilde stilin token'ı, değilse standart.
  const tema = p.tema as { altyazi?: { font: string; agirlik: number; renk: string; aktif_renk: string; kontur: number; kontur_renk: string };
    altyazi_stilli?: boolean; dosyalar?: Record<string, string> } | undefined;
  const words = p.words ?? izdusum(p);
  const stil = p.altyazi.stil ?? (tema?.altyazi_stilli && tema.altyazi ? {
    font: tema.altyazi.font, agirlik: tema.altyazi.agirlik, boyut: 72, renk: tema.altyazi.renk, aktif_renk: tema.altyazi.aktif_renk,
    kontur: tema.altyazi.kontur, kontur_renk: tema.altyazi.kontur_renk, kip: "kelime" as const, en_kelime: 3, en_karakter: 18, konum: null, dosya: null,
  } : null);
  const altyazi: AltyaziVeri | null = p.altyazi.acik && words.length
    ? { acik: true, words, stil, renk: CAP_VARSAYILAN, yatay: w > h, w, h } : null;
  if (altyazi) katman.push(`<div id="altyazi" style="${kutuStili(altyazi)}"></div>`);
  const fontYuzleri = [
    ...(p.altyazi.stil?.dosya ? [[p.altyazi.stil.font, p.altyazi.stil.dosya]] : []),
    ...Object.entries(tema?.dosyalar ?? {}),
  ].map(([ad, dosya]) => `@font-face { font-family: '${kac(ad)}'; font-weight: 100 900; src: url("fonts/${kac(dosya)}"); }`).join("\n  ");

  const renk = (p.tema as { renk?: Record<string, string> } | undefined)?.renk;
  const veri = { sekans: p.sekans, bitis, kaydir: pen ? pen[0] : 0, altyazi, renk, klipler: ciz, adalar, sahneler, sahneZemin: sahneZemin((p.tema as { renk?: Record<string, string> } | undefined)?.renk), tema: adalar.length ? p.tema ?? null : null, tum: p.klipler.map((c) => ({ ...c, sahne: undefined, olay: undefined })) };
  const hizliBlur = o.hareketBulaniklik === true;
  const html = `<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
${o.taban ? `<base href="${kac(o.taban)}">` : ""}
${o.temaCssUrl ? `<link rel="stylesheet" href="${kac(o.temaCssUrl)}">` : ""}
<style>
  ${fontYuzleri}
  html, body { margin: 0; background: #000; }
  #root { position: relative; width: ${W}px; height: ${H}px; overflow: hidden; background: var(--zemin, #000); }
  #sahne { position: absolute; left: 0; top: 0; width: ${w}px; height: ${h}px; transform-origin: 0 0;${olcek !== 1 ? ` transform: scale(${olcek});` : ""} }
  /* Ana kompozisyonun sınıfları kz- önekli: native sahneler aynı sayfaya bağlanır, genel sınıf adı onlara sızar (altbant-blok .panel). */
  .kz-k, .kz-t { position: absolute; inset: 0; }
  .kz-gk { pointer-events: none; }
  .kz-ada { position: absolute; inset: 0; }
  .kz-odak { position: absolute; inset: 0; overflow: hidden; }
  .kz-panel { position: absolute; left: 0; top: 0; width: ${w}px; height: ${h}px; overflow: hidden; }
  .kz-metin { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; text-align: center;
    padding: 60px; box-sizing: border-box; white-space: pre-wrap; line-height: 1.1; paint-order: stroke fill;
    font-family: var(--font, sans-serif); font-weight: var(--agirlik, 800); color: var(--yazi, #fff); }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${sn(bitis)}" data-width="${W}" data-height="${H}" data-fps="${fps}"${hizliBlur ? ' data-motion-blur="on" data-motion-blur-shutter="180"' : ""}>
<div id="sahne">
${katman.join("\n")}
</div>
</div>
<script>window.__KURGU = ${JSON.stringify(veri).replace(/</g, "\\u003c")};</script>
${baglamalar.length ? `<script>window.__TEMA = ${JSON.stringify(p.tema ?? null).replace(/</g, "\\u003c")}; window.__HFN_YER = ${JSON.stringify(yerler).replace(/</g, "\\u003c")};</script>` : ""}
${grafikBaglamalar.length ? `<script>window.__HF_PARAM = ${JSON.stringify(hfParamlar).replace(/</g, "\\u003c")};</script>` : ""}
<script src="${kac(o.gsapUrl)}"></script>
${baglamalar.length && o.cekirdekUrl ? `<script src="${kac(o.cekirdekUrl)}"></script>` : ""}
${adalar.length && o.adaUrl ? `<script src="${kac(o.adaUrl)}"></script>` : ""}
<script src="${kac(o.calismaUrl)}"></script>
</body>
</html>
`;
  // WHY: onRender boolean değil harita olarak geçirilmeli ki yalnızca eşlemesi olmayan fizik/karakter sahnesi desteklenmeyen listesine düşsün.
  return { html, desteklenmeyen: desteklenmeyenler(p, o.native, { onRender: o.onRender, grafikler: o.grafikler }), bitis, baglamalar, grafikBaglamalar };
};
