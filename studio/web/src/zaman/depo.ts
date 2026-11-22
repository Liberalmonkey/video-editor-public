// Kurgu durumu: tek kaynak, geri al yamaları, otomatik kayıt, terminal değişikliği izleme.
import { applyPatches, enablePatches, produceWithPatches, type Patch } from "immer";
import { create } from "zustand";
import type { KurguProps } from "../../../remotion/tipler";
import { ApiHata, istek } from "../api";
import { useDepo } from "../depo";
import * as K from "./komutlar";

enablePatches();

export type Arac = "sec" | "razor" | "ripple" | "rolling" | "slip" | "slide" | "el";
export type KayitDurum = "kayitli" | "bekliyor" | "kaydediliyor" | "hata";
export interface KaynakOge { yol: string; ad: string; tur: "video" | "ses" | "gorsel" | "motion"; muzik?: boolean; sfx?: boolean }
interface Adim { ad: string; yama: Patch[]; ters: Patch[]; anahtar?: string; zaman: number }

// /api/kurgu yanıtı: kurgu.json ve yanında yalnız önizleme için gelenler (tema token'ı, yüz bölgeleri).
export interface KurguYaniti { kurgu: KurguProps; medya: Record<string, string>; etag: string; tema?: Record<string, unknown> | null; bolgeler?: KurguProps["bolgeler"] | null }

interface KurguDepo {
  anahtar: string | null;
  kurgu: KurguProps | null;
  medya: Record<string, string>;
  tema: Record<string, unknown> | null; // ADR 0043: seçili stilin token'ı (önizleme render'la aynı görünür)
  bolgeler: KurguProps["bolgeler"] | null; // ADR 0045: native grafiklerin kaçınacağı yüzler (render'la aynı yerleşim)
  etag: string;
  kayit: KayitDurum;
  cakisma: boolean;
  geri: Adim[];
  ileri: Adim[];
  secim: string[];
  odakKlip: string | null; // bağlı grupta son tıklanan
  arac: Arac;
  yapisma: boolean;
  zaman: number;
  oynuyor: boolean;
  hiz: number;
  giris: number | null;
  cikis: number | null;
  kaynakGiris: number | null;
  kaynakCikis: number | null;
  odak: "program" | "kaynak";
  solo: string[];
  bulgular: { kod: string; seviye: string; bas: number; bit: number; kanit: string; oneri: string }[];

  ac: (anahtar: string | null, v: KurguYaniti | null) => void;
  tazele: (v: KurguYaniti) => void;
  duzenle: (ad: string, f: (d: KurguProps) => void, birlestir?: string) => void;
  geriAl: () => void;
  yinele: () => void;
  kaydet: () => Promise<void>;
  diskiAl: () => Promise<void>;
  benimkiniYaz: () => Promise<void>;
  sec: (idler: string[]) => void;
  ayarla: (p: Partial<KurguDepo>) => void;
  kaynaktanEkle: (o: KaynakOge, t: number, iz: string | null, insert: boolean, aralik?: [number, number] | null) => Promise<void>;
  sablonGuncelle: (klipId: string, param: Record<string, string | number>) => Promise<void>;
}

// Sesi ayır ya da birleştir: düğme, kısayol ve Efekt paneli aynı yerden geçer. Seçimde ayrılmış klip varsa birleştirir.
export const sesiAyirUygula = () => {
  const d = useKurgu.getState();
  const { bildir } = useDepo.getState();
  if (!d.kurgu || !d.secim.length) { bildir("Önce bir video klibi seç", true); return; }
  const grup = K.baglilar(d.kurgu, d.secim);
  if (d.kurgu.klipler.some((c) => grup.includes(c.id) && (c.ses_kapali || c.olay?.konusma))) {
    let r = { birlesen: 0, kayik: 0 };
    d.duzenle("Sesi birleştir", (f) => { r = K.sesiBirlestir(f, d.secim); });
    if (r.kayik) bildir(`${r.kayik} ses klibi görüntüden kaymış. Önce hizala, sonra birleştir.`, true);
    return;
  }
  let r: { yeni: string[]; hizli: number } = { yeni: [], hizli: 0 };
  d.duzenle("Sesi ayır", (f) => { r = K.sesiAyir(f, d.secim); });
  if (r.hizli) bildir(`${r.hizli} klipte hız %100 değil. Ayırmak için önce hızı %100 yap.`, true);
  else if (!r.yeni.length) bildir("Seçimde sesi olan video klibi yok", true);
  if (r.yeni.length) d.sec([...d.secim, ...r.yeni]);
};

const GECMIS = 200;
const BEKLEME = 800;
const BIRLESTIRME = 700;
let zamanlayici: ReturnType<typeof setTimeout> | undefined;
let izleyici: EventSource | null = null;

const yolu = (anahtar: string) => `/api/kurgu/${anahtar}`;

export const useKurgu = create<KurguDepo>((set, get) => ({
  anahtar: null, kurgu: null, medya: {}, tema: null, bolgeler: null, etag: "", kayit: "kayitli", cakisma: false, geri: [], ileri: [], secim: [], odakKlip: null,
  arac: "sec", yapisma: true, zaman: 0, oynuyor: false, hiz: 1, giris: null, cikis: null, kaynakGiris: null, kaynakCikis: null, odak: "program", solo: [], bulgular: [],

  ac: (anahtar, v) => {
    clearTimeout(zamanlayici);
    izleyici?.close();
    izleyici = null;
    set({ anahtar, kurgu: v?.kurgu ?? null, medya: v?.medya ?? {}, tema: v?.tema ?? null, bolgeler: v?.bolgeler ?? null, etag: v?.etag ?? "", kayit: "kayitli", cakisma: false, geri: [], ileri: [], secim: [], zaman: 0, giris: null, cikis: null, oynuyor: false, hiz: 1, solo: [], bulgular: [] });
    if (anahtar && v) izle(anahtar);
  },

  // Sunucudan yeni bilgi: içerik aynıysa yalnız adresler (proxy hazır oldu). Farklıysa dışarıdan değişmiştir.
  tazele: (v) => {
    const d = get();
    if (v.etag === d.etag || d.kayit === "kaydediliyor") { set({ medya: v.medya, tema: v.tema ?? d.tema, bolgeler: v.bolgeler ?? d.bolgeler }); return; }
    if (d.kayit === "bekliyor") { set({ cakisma: true, medya: v.medya, tema: v.tema ?? d.tema, bolgeler: v.bolgeler ?? d.bolgeler }); return; }
    set({ kurgu: v.kurgu, medya: v.medya, tema: v.tema ?? null, bolgeler: v.bolgeler ?? null, etag: v.etag, geri: [], ileri: [], secim: d.secim.filter((id) => v.kurgu.klipler.some((c) => c.id === id)) });
    useDepo.getState().bildir("Kurgu terminalden güncellendi");
  },

  // birlestir: aynı alanda arka arkaya değişiklik (sürükleme, ok tuşu) tek geri alma adımı olur.
  duzenle: (ad, f, birlestir) => {
    const { kurgu, geri } = get();
    if (!kurgu) return;
    const [yeni, yama, ters] = produceWithPatches(kurgu, f);
    if (!yama.length) return;
    const son = geri[geri.length - 1];
    const simdi = Date.now();
    const adimlar = birlestir && son?.anahtar === birlestir && simdi - son.zaman < BIRLESTIRME
      ? [...geri.slice(0, -1), { ...son, yama: [...son.yama, ...yama], ters: [...ters, ...son.ters], zaman: simdi }]
      : [...geri, { ad, yama, ters, anahtar: birlestir, zaman: simdi }].slice(-GECMIS);
    set({ kurgu: yeni, geri: adimlar, ileri: [], kayit: "bekliyor" });
    planla();
  },
  geriAl: () => {
    const { geri, ileri, kurgu } = get();
    const a = geri[geri.length - 1];
    if (!a || !kurgu) return;
    set({ kurgu: applyPatches(kurgu, a.ters) as KurguProps, geri: geri.slice(0, -1), ileri: [...ileri, a], kayit: "bekliyor" });
    planla();
  },
  yinele: () => {
    const { geri, ileri, kurgu } = get();
    const a = ileri[ileri.length - 1];
    if (!a || !kurgu) return;
    set({ kurgu: applyPatches(kurgu, a.yama) as KurguProps, ileri: ileri.slice(0, -1), geri: [...geri, a], kayit: "bekliyor" });
    planla();
  },

  kaydet: async () => {
    clearTimeout(zamanlayici);
    const { anahtar, kurgu, etag, kayit } = get();
    if (!anahtar || !kurgu || (kayit !== "bekliyor" && kayit !== "hata")) return;
    set({ kayit: "kaydediliyor" });
    try {
      const r = await istek(yolu(anahtar), { method: "PUT", headers: { "Content-Type": "application/json", "If-Match": etag }, body: JSON.stringify(kurgu) });
      if (get().anahtar !== anahtar) return;
      // Kayıt sürerken yeni düzenleme geldiyse o da yazılsın.
      const degisti = get().kurgu !== kurgu;
      set({ etag: r.etag, kayit: degisti ? "bekliyor" : "kayitli" });
      if (degisti) planla();
    } catch (e) {
      if (e instanceof ApiHata && e.durum === 409) set({ cakisma: true, kayit: "bekliyor" });
      else { set({ kayit: "hata" }); useDepo.getState().hata(e); }
    }
  },
  diskiAl: async () => {
    const { anahtar } = get();
    if (!anahtar) return;
    try {
      const v = await istek(yolu(anahtar));
      set({ kurgu: v.kurgu, medya: v.medya, etag: v.etag, geri: [], ileri: [], secim: [], kayit: "kayitli", cakisma: false });
    } catch (e) { useDepo.getState().hata(e); }
  },
  benimkiniYaz: async () => {
    const { anahtar } = get();
    if (!anahtar) return;
    try {
      const v = await istek(yolu(anahtar));
      set({ etag: v.etag, cakisma: false, kayit: "bekliyor" });
      await get().kaydet();
    } catch (e) { useDepo.getState().hata(e); }
  },

  sec: (secim) => set({ secim }),
  ayarla: (p) => set(p),

  sablonGuncelle: async (klipId, param) => {
    const { anahtar, kurgu } = get();
    const c = kurgu?.klipler.find((x) => x.id === klipId);
    if (!anahtar || !kurgu || !c?.sablon) return;
    try {
      const r = await istek(`/api/motion-sablon/${anahtar}`, { method: "POST",
        json: { ad: c.sablon.ad, param, tema: c.sablon.tema || kurgu.motion_tema || "varsayilan", w: kurgu.sekans.w, h: kurgu.sekans.h } });
      const var_ = Object.entries(kurgu.kaynaklar).find(([, k]) => k.yol === r.yol);
      const b = var_ ? null : await istek(`/api/kaynak/${anahtar}`, { method: "POST", json: { yol: r.yol } });
      if (get().anahtar !== anahtar || !get().kurgu) return; // üretim sürerken proje değişti
      const id = var_ ? var_[0] : yeniKaynakId(get().kurgu!, { yol: r.yol, ad: c.sablon.ad, tur: "motion" });
      if (b) set({ medya: { ...get().medya, [id]: b.url } });
      get().duzenle("Şablon parametresi", (d) => {
        const x = d.klipler.find((q) => q.id === klipId);
        if (!x?.sablon) return;
        if (b) d.kaynaklar[id] = { yol: r.yol, sure: b.sure, w: b.w, h: b.h, ses: b.ses };
        x.kaynak = id;
        x.sablon.param = param;
      });
    } catch (e) { useDepo.getState().hata(e); }
  },
  kaynaktanEkle: async (o, t, iz, insert, aralik) => {
    const { anahtar, kurgu } = get();
    if (!anahtar || !kurgu) return;
    const izTur = o.tur === "ses" ? "ses" : "video";
    const hedef = kurgu.izler.find((i) => i.id === iz && i.tur === izTur && !i.kilit) ?? kurgu.izler.filter((i) => i.tur === izTur && !i.kilit).at(-1 + (izTur === "ses" ? 1 : 0));
    if (!hedef) { useDepo.getState().bildir(`Kilitsiz ${izTur} izi yok`, true); return; }
    try {
      const var_ = Object.entries(kurgu.kaynaklar).find(([, k]) => k.yol === o.yol);
      const b = var_ ? null : await istek(`/api/kaynak/${anahtar}`, { method: "POST", json: { yol: o.yol } });
      const sure0 = var_ ? var_[1].sure : b.sure;
      const giris = aralik ? aralik[0] : 0;
      const sure = aralik ? aralik[1] - aralik[0] : o.tur === "gorsel" ? 5 : sure0;
      if (!(sure > 0)) throw new Error(`${o.ad}: süre okunamadı`);
      if (b) set({ medya: { ...get().medya, [yeniKaynakId(kurgu, o)]: b.url } });
      let yeniId = "";
      let oran: K.Oran | null = null;
      get().duzenle(`${o.ad} ekle`, (d) => {
        const id = var_ ? var_[0] : yeniKaynakId(d, o);
        if (b) {
          d.kaynaklar[id] = { yol: o.yol, sure: b.sure, w: b.w, h: b.h, ses: b.ses };
          if (b.kelimeler.length) (d.kelimeler ??= {})[id] = b.kelimeler;
        }
        if (o.tur === "video" && !d.klipler.length) oran = K.sekansKaynaktan(d, d.kaynaklar[id]?.w, d.kaynaklar[id]?.h);
        const sesAyari = o.muzik ? { gain_db: -14, duck: true, fade_in: 0.5, fade_out: 1.5 } : o.sfx ? { gain_db: -18 } : {};
        const olay = o.tur !== "ses" ? null : o.sfx ? { tur: "sfx" } : { muzik: true };
        // Hedef iz seçilmediyse motion üst katmandır, ana izi ezmez.
        const izId = o.tur === "motion" && !iz ? K.bosIz(d, t, t + sure) : hedef.id;
        yeniId = K.klipEkle(d, { tur: o.tur, iz: izId, bas: t, sure, kaynak: id, giris, olay, ses: sesAyari }, insert)?.id ?? "";
      });
      if (yeniId) get().sec([yeniId]);
      if (oran) useDepo.getState().bildir(`Sekans videoya uyarlandı: ${oran}`);
    } catch (e) { useDepo.getState().hata(e); }
  },
}));

// Kimlik yola bağlı: aynı dosya iki kez kaynak olmaz, geri al sonrası da aynı kalır.
const yeniKaynakId = (k: KurguProps, o: KaynakOge) => {
  const on = o.yol.replace(/[^\w]+/g, "_").slice(-40);
  return k.kaynaklar[on] && k.kaynaklar[on].yol !== o.yol ? `${on}_${Object.keys(k.kaynaklar).length}` : on;
};

function planla() {
  clearTimeout(zamanlayici);
  zamanlayici = setTimeout(() => useKurgu.getState().kaydet(), BEKLEME);
}

function izle(anahtar: string) {
  izleyici = new EventSource(`${yolu(anahtar)}/izle`);
  izleyici.onmessage = async (m) => {
    const d = useKurgu.getState();
    // Kendi kaydımız dönerken gelen olay yok sayılır; kayıt yanıtı etag'i zaten günceller.
    if (d.anahtar !== anahtar || d.kayit === "kaydediliyor" || m.data === d.etag) return;
    try { useKurgu.getState().tazele(await istek(yolu(anahtar))); } catch (e) { useDepo.getState().hata(e); }
  };
}

if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", (e) => {
    const k = useKurgu.getState().kayit;
    if (k === "bekliyor" || k === "kaydediliyor") { useKurgu.getState().kaydet(); e.preventDefault(); }
  });
}

export const zamanKodu = (t: number, fps: number) => {
  const f = Math.round(t * fps);
  const s = Math.floor(f / fps);
  const iki = (n: number) => String(n).padStart(2, "0");
  return `${iki(Math.floor(s / 3600))}:${iki(Math.floor(s / 60) % 60)}:${iki(s % 60)}:${iki(f % fps)}`;
};
