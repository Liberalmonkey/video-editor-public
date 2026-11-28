import { create } from "zustand";
import { ApiHata, istek } from "./api";
import { useKurgu, type KaynakOge } from "./zaman/depo";

export interface Proje { studyo: string; ad: string; kurgu: boolean; props: boolean }
export interface Goruntu { tur: string; url: string; ad: string; kaynak?: KaynakOge }
export interface Bildirim { id: number; metin: string; hata: boolean }
export interface IsOzet { id: number; komut: string; baslik: string; durum: string; baslangic: number | null; bitis: number | null; kod: number | null; motor?: string | null; model?: string | null; oturum?: string | null }
export interface ModelOge { id: string; ad: string; grup?: string; ucretsiz?: boolean; aciklama?: string }
export interface MotorDurum {
  ad: string; kurulu: boolean; surum: string; modeller: ModelOge[];
  varsayilan?: string | null; kurulum?: string; mod_ipucu?: Record<string, string>; hata?: string;
  seviyeler?: string[]; // ADR 0044: akıl yürütme seviyesi (claude, agy --effort; codex reasoning)
}
export interface AjanSecim { motor: string; model: string; mod: "duzenle" | "plan" }
export interface Sorgu { baslik: string; metin: string; onay: string; tehlike?: boolean; coz: (e: boolean) => void }

interface Depo {
  studyolar: string[];
  projeler: Proje[];
  aktif: Proje | null;
  kurguDurum: "yok" | "yukleniyor" | "hazir" | "bos";
  goruntu: Goruntu | null;
  surum: number;                // dosya listeleri bunu izler
  bildirimler: Bildirim[];
  isler: IsOzet[];
  gunlukler: Record<number, string[]>;
  sorgu: Sorgu | null;
  baglanti: boolean;
  ajanDurum: Record<string, MotorDurum> | null;
  ajan: AjanSecim;
  sohbetBasi: number;           // bu kimlikten eski ajan işleri yeni sohbete devam ettirilmez

  projeleriAl: () => Promise<void>;
  projeAc: (p: Proje | null) => Promise<void>;
  kurguAl: () => Promise<void>;
  kurguOlustur: () => Promise<void>;
  goster: (g: Goruntu | null) => void;
  tazele: () => void;
  bildir: (metin: string, hata?: boolean) => void;
  hata: (e: unknown) => void;
  kapat: (id: number) => void;
  onayla: (s: Omit<Sorgu, "coz">) => Promise<boolean>;
  isBaslat: (komut: string, ek?: Record<string, unknown>) => Promise<void>;
  panoEkle: (dosya: string, ad: string, sure: number) => Promise<void>;
  ajanDurumAl: (yenile?: boolean) => Promise<void>;
  ajanSec: (s: Partial<AjanSecim>) => void;
  ajanGonder: (istem: string) => Promise<boolean>;
  yeniSohbet: () => void;
}

let sayac = 0;
// WHY: artan istek sayaçları; hızlı proje geçişi ve paralel kurguAl() çağrılarında geç dönen eski yanıtın yeni durumu ezmesini önler.
let projeAcNo = 0;
let kurguAlNo = 0;
const panoBekleyen = new Map<number, { oge: KaynakOge; t: number; anahtar: string | null }>();
// Motorun varsayılan modeli listede varsa o, yoksa listenin ilki.
export const varsayilanModel = (m: MotorDurum) =>
  (m.varsayilan && m.modeller.some((x) => x.id === m.varsayilan) ? m.varsayilan : m.modeller[0]?.id) ?? "";

const ajanIlk = (): AjanSecim => {
  try { const v = JSON.parse(localStorage.getItem("studio.ajan") ?? ""); if (v?.motor) return v; } catch { /* yok ya da bozuk */ }
  return { motor: "claude", model: "sonnet", mod: "duzenle" };
};

export const useDepo = create<Depo>((set, get) => ({
  studyolar: [], projeler: [], aktif: null, kurguDurum: "yok", goruntu: null, surum: 0,
  bildirimler: [], isler: [], gunlukler: {}, sorgu: null, baglanti: true,
  ajanDurum: null, ajan: ajanIlk(), sohbetBasi: 0,

  projeleriAl: async () => {
    try {
      const v = await istek("/api/projeler");
      set({ studyolar: v.studyolar, projeler: v.projeler });
    } catch (e) { get().hata(e); }
  },
  projeAc: async (p) => {
    // WHY: artan sayaç; hızlı proje geçişinde önceki kaydet() tamamlanınca yeni seçimi ezmesin.
    const no = ++projeAcNo;
    await useKurgu.getState().kaydet(); // WHY: geçiş bekleyen düzenlemeyi kaybetmesin
    if (no !== projeAcNo) return;
    kurguAlNo++; // WHY: önceki projeden uçuşta kalan kurguAl() yanıtı yeni projeye yazılmasın.
    useKurgu.getState().ac(null, null);
    set({ aktif: p, goruntu: null, kurguDurum: p ? "yukleniyor" : "yok", surum: get().surum + 1 });
    try { localStorage.setItem("studio.aktif", p ? `${p.studyo}/${p.ad}` : ""); } catch { /* özel pencere */ }
    if (p) await get().kurguAl();
  },
  kurguAl: async () => {
    const p = get().aktif;
    if (!p) return;
    // WHY: artan sayaç; aynı projede paralel kurguAl() çağrılarından geç dönen eski yanıt yeni kurguyu ezmesin.
    const no = ++kurguAlNo;
    (window as any).remotion_staticBase = `/pub/${p.studyo}/${p.ad}`;
    try {
      const v = await istek(`/api/kurgu/${p.studyo}/${p.ad}`);
      if (no !== kurguAlNo || get().aktif?.studyo !== p.studyo || get().aktif?.ad !== p.ad) return;
      const k = useKurgu.getState(), anahtar = `${p.studyo}/${p.ad}`;
      if (k.anahtar === anahtar) k.tazele(v); else k.ac(anahtar, v);
      set({ kurguDurum: "hazir" });
    } catch (e) {
      if (no !== kurguAlNo) return;
      if (e instanceof ApiHata && e.durum === 404) { useKurgu.getState().ac(null, null); set({ kurguDurum: "bos" }); }
      else { set({ kurguDurum: "bos" }); get().hata(e); }
    }
  },
  kurguOlustur: async () => {
    const p = get().aktif;
    if (!p) return;
    try {
      await istek(`/api/kurgu/${p.studyo}/${p.ad}/icerial`, { method: "POST" });
      await get().projeleriAl();
      await get().kurguAl();
    } catch (e) { get().hata(e); }
  },
  goster: (goruntu) => set({ goruntu }),
  tazele: () => set({ surum: get().surum + 1 }),
  bildir: (metin, hata = false) => {
    const id = ++sayac;
    set({ bildirimler: [...get().bildirimler, { id, metin, hata }].slice(-4) });
    setTimeout(() => get().kapat(id), hata ? 9000 : 4000);
  },
  hata: (e) => get().bildir(e instanceof Error ? e.message : String(e), true),
  kapat: (id) => set({ bildirimler: get().bildirimler.filter((b) => b.id !== id) }),
  onayla: (s) => new Promise((coz) => set({ sorgu: { ...s, coz: (x) => { set({ sorgu: null }); coz(x); } } })),
  panoEkle: async (dosya, ad, sure) => {
    const p = get().aktif;
    const k = useKurgu.getState();
    if (!p || !k.kurgu) { get().bildir("Önce kurgusu olan bir proje aç", true); return; }
    try {
      await k.kaydet();
      const r = await istek(`/api/pano/${p.studyo}/${p.ad}`, { method: "POST", json: { dosya, sure } });
      const oge = { yol: r.yol, ad, tur: "motion" as const };
      if (r.hazir) { await k.kaynaktanEkle(oge, k.zaman, null, false); return; }
      panoBekleyen.set(r.is, { oge, t: k.zaman, anahtar: k.anahtar });
      get().bildir(`${ad} hazırlanıyor. Bitince oynatma kafasına eklenecek.`);
    } catch (e) { get().hata(e); }
  },
  isBaslat: async (komut, ek = {}) => {
    const p = get().aktif;
    try {
      await useKurgu.getState().kaydet(); // WHY: render son düzenlemeyi görsün
      await istek("/api/isler", { method: "POST", json: { komut, ...(p ? { studyo: p.studyo, ad: p.ad } : {}), ...ek } });
    } catch (e) { get().hata(e); }
  },
  ajanDurumAl: async (yenile = false) => {
    try {
      const d: Record<string, MotorDurum> = await istek(`/api/ajan/durum${yenile ? "?yenile=true" : ""}`);
      set({ ajanDurum: d });
      // Seçili motor bilinmiyor ya da kurulu değilse ilk kurulu motora; seçili model listede yoksa motorun varsayılanına geç.
      const s = get().ajan;
      if (!d[s.motor]?.kurulu) {
        const k = Object.keys(d).find((x) => d[x].kurulu);
        if (k && k !== s.motor) { get().ajanSec({ motor: k }); return; }
      }
      const m = d[s.motor];
      if (m?.modeller.length && !m.modeller.some((x) => x.id === s.model)) get().ajanSec({ model: varsayilanModel(m) });
    } catch (e) { get().hata(e); }
  },
  ajanSec: (s) => {
    const d = get().ajanDurum, eski = get().ajan;
    const yeni = { ...eski, ...s };
    if (s.motor && s.motor !== eski.motor) {
      yeni.model = s.model ?? (d?.[s.motor] ? varsayilanModel(d[s.motor]) : "");
      set({ sohbetBasi: Math.max(0, ...get().isler.map((x) => x.id)) + 1 }); // motor değişince sohbet yeniden başlar
    }
    set({ ajan: yeni });
    try { localStorage.setItem("studio.ajan", JSON.stringify(yeni)); } catch { /* özel pencere */ }
  },
  ajanGonder: async (istem) => {
    const { aktif: p, ajan: s, isler, sohbetBasi } = get();
    const onceki = isler.find((x) => x.komut === "ajan" && x.id >= sohbetBasi && x.motor === s.motor && x.oturum);
    try {
      await useKurgu.getState().kaydet(); // WHY: ajan son düzenlemeyi görsün
      await istek("/api/ajan", { method: "POST", json: { ...s, istem, oturum: onceki?.oturum ?? undefined, ...(p ? { studyo: p.studyo, ad: p.ad } : {}) } });
      return true;
    } catch (e) { get().hata(e); return false; }
  },
  yeniSohbet: () => set({ sohbetBasi: Math.max(0, ...get().isler.map((x) => x.id)) + 1 }),
}));

// SSE tek bağlantı: durum ve günlük depoya akar. Biten iş dosya listelerini ve kurguyu tazeler.
export const isAkisiBaglan = () => {
  const es = new EventSource("/api/isler/akis");
  es.onopen = () => {
    // WHY: yeniden bağlantıda kayıt reddedilirse yakalanmamış promise hatası kalmasın.
    if (!useDepo.getState().baglanti) { useDepo.setState({ baglanti: true }); useKurgu.getState().kaydet().catch(useDepo.getState().hata); }
  };
  es.onerror = () => useDepo.setState({ baglanti: false });
  es.onmessage = (m) => {
    // WHY: kesilen veya şeması eksik SSE olayı işleyiciyi çökertip bitiş yenilemesini durdurmasın.
    try {
      const v = JSON.parse(m.data);
      if (!v || typeof v !== "object" || v.id == null) return;
      const d = useDepo.getState();
      const onceki = d.isler.find((x) => x.id === v.id);
      const yeni = Array.isArray(v?.yeni) ? v.yeni : [];
      useDepo.setState({
        isler: [...d.isler.filter((x) => x.id !== v.id), v].sort((a, b) => b.id - a.id),
        gunlukler: yeni.length ? { ...d.gunlukler, [v.id]: [...(d.gunlukler[v.id] ?? []), ...yeni] } : d.gunlukler,
      });
      if (onceki && onceki.durum !== v.durum && ["bitti", "hata", "iptal"].includes(v.durum)) {
        const pano = panoBekleyen.get(v.id);
        if (pano) {
          panoBekleyen.delete(v.id);
          // WHY: pano hazırlanırken başka proje açıldıysa klip onun kurgusuna eklenmez.
          if (v.durum === "bitti" && useKurgu.getState().anahtar === pano.anahtar) useKurgu.getState().kaynaktanEkle(pano.oge, pano.t, null, false).catch(useDepo.getState().hata);
          else if (v.durum === "bitti") d.bildir(`${pano.oge.ad} hazır ama proje değiştiği için eklenmedi. Kütüphaneden yeniden ekle.`, true);
        }
        d.bildir(v.durum === "bitti" ? `Bitti: ${v.baslik}` : v.durum === "iptal" ? `İptal edildi: ${v.baslik}` : `Hata: ${v.baslik}. Günlüğe bak.`, v.durum === "hata");
        d.tazele();
        d.projeleriAl().catch(useDepo.getState().hata);
        d.kurguAl().catch(useDepo.getState().hata);
      }
    } catch { /* bozuk ya da kesik SSE olayı */ }
  };
  return () => es.close();
};
