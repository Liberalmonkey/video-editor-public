// Kısayollar: Premiere düzeni, kullanıcı değiştirebilir, tarayıcıda saklanır.
import { sesiAyirUygula, useKurgu, type Arac } from "./depo";
import * as K from "./komutlar";
import { degistir, durdur, git, kareGit, kesimeGit, bitisi, shuttle } from "./oynatici";

export interface Kisayol { id: string; ad: string; tus: string; grup: string; calis: () => void }

const kd = () => useKurgu.getState();
const arac = (a: Arac) => () => kd().ayarla({ arac: a });
const zoom = (d: string) => () => window.dispatchEvent(new CustomEvent("studio-zoom", { detail: d }));

const alan = (ad: string) => () => window.dispatchEvent(new CustomEvent("studio-alan", { detail: ad }));
const kaynakEkle = (insert: boolean) => () => window.dispatchEvent(new CustomEvent("studio-kaynak-ekle", { detail: insert }));
const kaynakVideo = () => document.querySelector<HTMLVideoElement>("[data-kaynak-video]");
const kaynaktaMi = () => kd().odak === "kaynak" && !!kaynakVideo();

// Kaynak monitörü odaktaysa oynatma ve işaret tuşları oraya gider.
const j = (yon: 1 | -1) => () => {
  const v = kaynakVideo();
  if (kaynaktaMi() && v) {
    // WHY: tarayıcı video öğesi geri oynatmaz; J kaynakta bir saniye geri atlar.
    if (yon < 0) { v.currentTime = Math.max(0, v.currentTime - 1); return; }
    v.playbackRate = !v.paused && v.playbackRate < 4 ? v.playbackRate * 2 : 1;
    // WHY: otomatik oynatma engeli veya hazır olmayan medyada play() reddi yakalanmamış rejection üretmesin.
    v.play()?.catch(() => {});
    return;
  }
  shuttle(yon);
};
const k = () => { const v = kaynakVideo(); if (kaynaktaMi() && v) v.pause(); else durdur(); };
// WHY: play() promise reddi yakalanmazsa konsolda unhandled rejection oluşur.
const bosluk = () => { const v = kaynakVideo(); if (kaynaktaMi() && v) { if (v.paused) v.play()?.catch(() => {}); else v.pause(); } else degistir(); };
const kare = (n: number) => () => {
  const v = kaynakVideo();
  if (kaynaktaMi() && v) { v.pause(); v.currentTime = Math.max(0, v.currentTime + n / (useKurgu.getState().kurgu?.sekans.fps ?? 30)); } else kareGit(n);
};
const isaretle = (uc: "giris" | "cikis") => () => {
  const v = kaynakVideo();
  if (kaynaktaMi() && v) kd().ayarla(uc === "giris" ? { kaynakGiris: v.currentTime } : { kaynakCikis: v.currentTime });
  else kd().ayarla({ [uc]: kd().zaman });
};

export const KISAYOLLAR: Kisayol[] = [
  { id: "oynat", grup: "Oynatma", ad: "Oynat / durdur", tus: " ", calis: bosluk },
  { id: "j", grup: "Oynatma", ad: "Geri oynat, hızlandır", tus: "j", calis: j(-1) },
  { id: "k", grup: "Oynatma", ad: "Durdur", tus: "k", calis: k },
  { id: "l", grup: "Oynatma", ad: "İleri oynat, hızlandır", tus: "l", calis: j(1) },
  { id: "kareGeri", grup: "Oynatma", ad: "Bir kare geri", tus: "arrowleft", calis: kare(-1) },
  { id: "kareIleri", grup: "Oynatma", ad: "Bir kare ileri", tus: "arrowright", calis: kare(1) },
  { id: "kare5Geri", grup: "Oynatma", ad: "Beş kare geri", tus: "shift+arrowleft", calis: kare(-5) },
  { id: "kare5Ileri", grup: "Oynatma", ad: "Beş kare ileri", tus: "shift+arrowright", calis: kare(5) },
  { id: "kesimGeri", grup: "Oynatma", ad: "Önceki kesim", tus: "arrowup", calis: () => kesimeGit(-1) },
  { id: "kesimIleri", grup: "Oynatma", ad: "Sonraki kesim", tus: "arrowdown", calis: () => kesimeGit(1) },
  { id: "basa", grup: "Oynatma", ad: "Başa git", tus: "home", calis: () => git(0) },
  { id: "sona", grup: "Oynatma", ad: "Sona git", tus: "end", calis: () => git(bitisi()) },

  { id: "aracSec", grup: "Araçlar", ad: "Seç", tus: "v", calis: arac("sec") },
  { id: "aracRazor", grup: "Araçlar", ad: "Razor", tus: "c", calis: arac("razor") },
  { id: "aracRipple", grup: "Araçlar", ad: "Ripple kırp", tus: "b", calis: arac("ripple") },
  { id: "aracRolling", grup: "Araçlar", ad: "Rolling", tus: "n", calis: arac("rolling") },
  { id: "aracSlip", grup: "Araçlar", ad: "Slip", tus: "y", calis: arac("slip") },
  { id: "aracSlide", grup: "Araçlar", ad: "Slide", tus: "u", calis: arac("slide") },
  { id: "aracEl", grup: "Araçlar", ad: "El", tus: "h", calis: arac("el") },
  { id: "yapisma", grup: "Araçlar", ad: "Yapışma aç / kapat", tus: "s", calis: () => kd().ayarla({ yapisma: !kd().yapisma }) },

  { id: "kes", grup: "Kurgu", ad: "Oynatma kafasında kes", tus: "ctrl+k", calis: () => { const d = kd(); d.duzenle("Kes", (f) => K.kafadaKes(f, d.zaman, d.secim)); } },
  { id: "sil", grup: "Kurgu", ad: "Sil, boşluk kalsın", tus: "delete", calis: () => { const d = kd(); if (d.secim.length) { d.duzenle("Sil", (f) => K.sil(f, d.secim)); d.sec([]); } } },
  { id: "sil2", grup: "Kurgu", ad: "Sil (ikinci tuş)", tus: "backspace", calis: () => { const d = kd(); if (d.secim.length) { d.duzenle("Sil", (f) => K.sil(f, d.secim)); d.sec([]); } } },
  { id: "rippleSil", grup: "Kurgu", ad: "Ripple sil", tus: "shift+delete", calis: () => { const d = kd(); if (d.secim.length) { d.duzenle("Ripple sil", (f) => K.rippleSil(f, d.secim)); d.sec([]); } } },
  { id: "q", grup: "Kurgu", ad: "Kafaya kadar ripple kırp", tus: "q", calis: () => { const d = kd(); const t = d.zaman; d.duzenle("Ripple kırp", (f) => K.qw(f, t, "q", d.secim)); } },
  { id: "w", grup: "Kurgu", ad: "Kafadan sonrasını ripple kırp", tus: "w", calis: () => { const d = kd(); d.duzenle("Ripple kırp", (f) => K.qw(f, d.zaman, "w", d.secim)); } },
  { id: "insert", grup: "Kurgu", ad: "Kaynağı araya ekle", tus: ",", calis: kaynakEkle(true) },
  { id: "overwrite", grup: "Kurgu", ad: "Kaynağı üzerine yaz", tus: ".", calis: kaynakEkle(false) },
  { id: "metin", grup: "Kurgu", ad: "Metin ekle", tus: "t", calis: () => { const d = kd(); let id: string | undefined; d.duzenle("Metin ekle", (f) => { id = K.metinEkle(f, d.zaman, "Metin")?.id; }); if (id) d.sec([id]); } },
  { id: "bagla", grup: "Kurgu", ad: "Bağla / ayır", tus: "ctrl+l", calis: () => { const d = kd(); if (d.secim.length) d.duzenle("Bağla", (f) => K.bagla(f, d.secim)); } },
  { id: "sesAyir", grup: "Kurgu", ad: "Sesi ayır / birleştir", tus: "shift+a", calis: sesiAyirUygula },
  { id: "kazancArti", grup: "Kurgu", ad: "Seçili klibin sesini 1 dB aç", tus: "alt+arrowup", calis: () => { const d = kd(); if (d.secim.length) d.duzenle("Kazanç", (f) => K.kazancEkle(f, d.secim, 1), "kazanc"); } },
  { id: "kazancEksi", grup: "Kurgu", ad: "Seçili klibin sesini 1 dB kıs", tus: "alt+arrowdown", calis: () => { const d = kd(); if (d.secim.length) d.duzenle("Kazanç", (f) => K.kazancEkle(f, d.secim, -1), "kazanc"); } },
  { id: "tumu", grup: "Kurgu", ad: "Tümünü seç", tus: "ctrl+a", calis: () => { const d = kd(); d.sec((d.kurgu?.klipler ?? []).filter((c) => !d.kurgu!.izler.find((i) => i.id === c.iz)?.kilit).map((c) => c.id)); } },
  { id: "secimYok", grup: "Kurgu", ad: "Seçimi kaldır", tus: "escape", calis: () => kd().sec([]) },
  { id: "geri", grup: "Kurgu", ad: "Geri al", tus: "ctrl+z", calis: () => kd().geriAl() },
  { id: "ileri", grup: "Kurgu", ad: "Yinele", tus: "ctrl+y", calis: () => kd().yinele() },
  { id: "ileri2", grup: "Kurgu", ad: "Yinele (ikinci tuş)", tus: "ctrl+shift+z", calis: () => kd().yinele() },

  { id: "giris", grup: "İşaret", ad: "Giriş işareti", tus: "i", calis: isaretle("giris") },
  { id: "cikis", grup: "İşaret", ad: "Çıkış işareti", tus: "o", calis: isaretle("cikis") },
  { id: "ioTemizle", grup: "İşaret", ad: "Giriş ve çıkışı temizle", tus: "ctrl+shift+x", calis: () => kd().ayarla({ giris: null, cikis: null }) },
  { id: "cikar", grup: "İşaret", ad: "Aralığı çıkar, boşluk kapat", tus: "'", calis: () => { const d = kd(); if (d.giris !== null && d.cikis !== null && d.cikis > d.giris) { const a = d.giris, b = d.cikis; d.duzenle("Aralığı çıkar", (f) => K.aralikSil(f, a, b)); d.ayarla({ giris: null, cikis: null }); } } },
  { id: "isaret", grup: "İşaret", ad: "İşaret ekle", tus: "m", calis: () => { const d = kd(); d.duzenle("İşaret", (f) => { (f.isaretler ??= []).push({ t: d.zaman, ad: "" }); }); } },

  { id: "alan1", grup: "Görünüm", ad: "Kurgu çalışma alanı", tus: "alt+1", calis: alan("kurgu") },
  { id: "alan2", grup: "Görünüm", ad: "Teslim çalışma alanı", tus: "alt+2", calis: alan("teslim") },
  { id: "alan3", grup: "Görünüm", ad: "Kütüphane çalışma alanı", tus: "alt+3", calis: alan("kutuphane") },
  { id: "yakin", grup: "Görünüm", ad: "Yakınlaş", tus: "=", calis: zoom("yakin") },
  { id: "yakin2", grup: "Görünüm", ad: "Yakınlaş (ikinci tuş)", tus: "+", calis: zoom("yakin") },
  { id: "uzak", grup: "Görünüm", ad: "Uzaklaş", tus: "-", calis: zoom("uzak") },
  { id: "sigdir", grup: "Görünüm", ad: "Tümünü sığdır", tus: "\\", calis: zoom("sigdir") },
];

const SAKLA = "studio.kisayol.v1";
export const kullaniciTuslari = (): Record<string, string> => {
  try { return JSON.parse(localStorage.getItem(SAKLA) ?? "{}"); } catch { return {}; }
};
export const tusKaydet = (t: Record<string, string>) => { try { localStorage.setItem(SAKLA, JSON.stringify(t)); } catch { /* özel pencere */ } tabloYap(); };
export const tusYaz = (k: Kisayol, ozel = kullaniciTuslari()) => ozel[k.id] ?? k.tus;

// WHY: Türkçe klavyede I tuşu `ı` üretir; Premiere alışkanlığı için `i` sayılır.
export const tusAdi = (e: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "shiftKey" | "altKey">) => {
  let a = e.key.toLocaleLowerCase("en-US");
  if (a === "ı" || a === "i̇") a = "i";
  return [(e.ctrlKey || e.metaKey) && "ctrl", e.altKey && "alt", e.shiftKey && a.length > 1 && "shift", e.shiftKey && /^[a-z]$/.test(a) && "shift", a].filter(Boolean).join("+");
};

let tablo = new Map<string, Kisayol>();
function tabloYap() {
  const o = kullaniciTuslari();
  tablo = new Map(KISAYOLLAR.map((k) => [tusYaz(k, o), k]));
}

export const kisayollariBagla = () => {
  tabloYap();
  const f = (e: KeyboardEvent) => {
    const h = e.target as HTMLElement;
    if (h.closest?.("input, textarea, select, dialog, [contenteditable]")) return;
    const k = tablo.get(tusAdi(e));
    if (!k) return;
    e.preventDefault();
    k.calis();
  };
  window.addEventListener("keydown", f);
  return () => window.removeEventListener("keydown", f);
};
