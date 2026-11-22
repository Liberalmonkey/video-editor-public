import { CircleStop, Save, Star, Users } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo, type MotorDurum } from "../depo";
import { Dugme } from "../ortak";
import { ModelSecici } from "./AjanPaneli";

// WHY: bkz. wiki/decisions/0044-ekip-motoru.md. Ekip modu: 3 editör (E1 kesim, E2 grafik, E3 ses/stil) + 3 kalite kontrol.
// Model listeleri canlı motor taramasından gelir (motorlar.py); kurulu olmayan motor soluk ve sebebiyle görünür.

export const SLOTLAR = ["E1", "E2", "E3", "K1", "K2", "K3"] as const;
export type SlotAd = (typeof SLOTLAR)[number];
export const SLOT_ADI: Record<SlotAd, string> = {
  E1: "E1 Kurgu", E2: "E2 Grafik", E3: "E3 Ses ve stil", K1: "K1 Kurgu denetimi", K2: "K2 Görsel denetimi", K3: "K3 Ses denetimi",
};
export interface Slot { motor: string; model?: string | null; seviye?: string | null; yedek_motor?: string | null; yedek_model?: string | null; yedek_seviye?: string | null }
export interface EkipAyar { ad: string; slotlar: Record<SlotAd, Slot>; bolus: "rol" | "zaman"; tur: number; motion: string; stil?: string | null; eszamanlilik: number }
export interface SlotDurum { durum: "bekliyor" | "calisiyor" | "bitti" | "hata" | "yedek"; motor: string; model?: string | null; sure?: number | null; token?: number | null; tahmini?: boolean }
export interface EkipDurum { yok?: boolean; tur: number; tur_sinir: number; asama: string; bitti: boolean; acik: { P0: number; P1: number; P2: number }; kapanan: number; slotlar: Record<SlotAd, SlotDurum> }

const DURUM_ADI: Record<SlotDurum["durum"], string> = { bekliyor: "bekliyor", calisiyor: "çalışıyor", bitti: "bitti", hata: "hata", yedek: "yedekte" };

// Seçilen motor kurulu değilse ya da model listesi boşsa sebebi döner; boş metin: hazır.
export const motorSebebi = (m?: MotorDurum) => (!m ? "taranıyor" : !m.kurulu ? `kurulu değil. ${m.kurulum ?? ""}` : m.hata ?? "");

const MotorSec: React.FC<{ deger?: string | null; bos?: boolean; sec: (m: string) => void; durum: Record<string, MotorDurum> | null; etiket: string }> = ({ deger, bos, sec, durum, etiket }) => (
  <select aria-label={etiket} value={deger ?? ""} onChange={(e) => sec(e.target.value)}>
    {bos && <option value="">yok</option>}
    {Object.entries(durum ?? {}).map(([k, v]) => {
      const sebep = motorSebebi(v);
      return <option key={k} value={k} disabled={!v.kurulu} title={sebep || `${v.ad} ${v.surum}`}>{v.ad}{sebep ? ` (${!v.kurulu ? "kurulu değil" : "uyarı"})` : ""}</option>;
    })}
  </select>
);

const SeviyeSec: React.FC<{ m?: MotorDurum; deger?: string | null; sec: (s: string | null) => void; etiket: string }> = ({ m, deger, sec, etiket }) => (
  <select aria-label={etiket} value={deger ?? ""} disabled={!m?.seviyeler?.length} onChange={(e) => sec(e.target.value || null)}
    title={m?.seviyeler?.length ? "Akıl yürütme seviyesi" : "Bu motorda seviye model adındadır"}>
    <option value="">seviye: varsayılan</option>
    {(m?.seviyeler ?? []).map((s) => <option key={s} value={s}>{s}</option>)}
  </select>
);

export const EkipPaneli: React.FC<{ stil: string; motion: string; final: boolean; notu: string; bitti: () => void }> = ({ stil, motion, final, notu, bitti }) => {
  const { ajanDurum, aktif, isler, isBaslat, hata, bildir } = useDepo();
  const [ayar, setAyar] = useState<EkipAyar | null>(null);
  const [onayarlar, setOnayarlar] = useState<Record<string, EkipAyar>>({});
  const [varsayilan, setVarsayilan] = useState<string | null>(null);
  const [ad, setAd] = useState("");
  const [durum, setDurum] = useState<EkipDurum | null>(null);
  const [sekme, setSekme] = useState<SlotAd>("E1");
  const [cikti, setCikti] = useState<string[]>([]);
  const calisan = isler.find((x) => x.komut === "ai-edit" && (x.durum === "calisiyor" || x.durum === "sirada"));
  const yol = aktif ? `/api/ekip/${aktif.studyo}/${aktif.ad}` : null;

  const yukle = async () => {
    try {
      const g = await istek("/api/ekip");
      setOnayarlar(g.global.onayarlar ?? {}); setVarsayilan(g.global.varsayilan ?? null);
      const p = yol ? await istek(yol) : null;
      const a: EkipAyar = p?.etkin ?? g.global.onayarlar?.[g.global.varsayilan] ?? g.varsayilan_ayar;
      setAyar(a); setAd(a.ad);
    } catch (e) { hata(e); }
  };
  useEffect(() => { yukle(); }, [yol]);
  // Canlı durum: iş sürerken yoklanır; bittiğinde bir kez daha okunur.
  useEffect(() => {
    if (!yol) return;
    let iptal = false;
    const oku = () => istek(`${yol}/durum`).then((d) => { if (!iptal) setDurum(d.yok ? null : d); }).catch(() => {});
    oku();
    if (!calisan) return () => { iptal = true; };
    const t = window.setInterval(oku, 1500);
    return () => { iptal = true; window.clearInterval(t); };
  }, [yol, calisan?.id]);
  useEffect(() => {
    if (!yol) return;
    let iptal = false;
    const oku = () => istek(`${yol}/cikti/${sekme}?son=300`).then((d) => { if (!iptal) setCikti(d.satirlar ?? []); }).catch(() => {});
    oku();
    if (!calisan) return () => { iptal = true; };
    const t = window.setInterval(oku, 2000);
    return () => { iptal = true; window.clearInterval(t); };
  }, [yol, sekme, calisan?.id]);

  const slotYaz = (s: SlotAd, ek: Partial<Slot>) => ayar && setAyar({ ...ayar, slotlar: { ...ayar.slotlar, [s]: { ...ayar.slotlar[s], ...ek } } });
  const eksik = useMemo(() => (ayar ? SLOTLAR.filter((s) => !ajanDurum?.[ayar.slotlar[s].motor]?.kurulu) : []), [ayar, ajanDurum]);

  const onayarKaydet = async (vars: boolean) => {
    if (!ayar || !/^[a-z0-9][a-z0-9-]{0,39}$/.test(ad)) { hata(new Error("Ön ayar adı küçük harf, rakam, tire")); return; }
    try {
      const r = await istek(`/api/ekip/onayar/${ad}${vars ? "?varsayilan=true" : ""}`, { method: "PUT", json: { ...ayar, ad } });
      setVarsayilan(r.varsayilan); setOnayarlar({ ...onayarlar, [ad]: { ...ayar, ad } });
      bildir(vars ? `${ad} varsayılan ekip oldu` : `${ad} kaydedildi`);
    } catch (e) { hata(e); }
  };
  const projeyeKaydet = async () => {
    if (!ayar || !yol) return;
    try { await istek(yol, { method: "PUT", json: ayar }); bildir("Ekip ayarı bu projeye kaydedildi"); } catch (e) { hata(e); }
  };
  const baslat = async () => {
    if (!ayar || !aktif || eksik.length) return;
    await isBaslat("ai-edit", { ekip: true, ekip_ayar: { ...ayar, motion, stil: stil || null }, notu: notu.trim() || undefined, stil: stil || undefined, motion, final });
    bitti();
  };

  if (!ayar) return <div className="ipucu">Ekip ayarı yükleniyor…</div>;
  return (
    <div className="ekip">
      <div className="ekip-onayar">
        <select aria-label="Ön ayar" value={onayarlar[ad] ? ad : ""} onChange={(e) => { const a = onayarlar[e.target.value]; if (a) { setAyar(a); setAd(a.ad); } }}>
          <option value="" disabled>Ön ayar seç</option>
          {Object.keys(onayarlar).map((k) => <option key={k} value={k}>{k}{k === varsayilan ? " · varsayılan" : ""}</option>)}
        </select>
        <input aria-label="Ön ayar adı" value={ad} onChange={(e) => setAd(e.target.value)} size={14} />
        <Dugme onClick={() => onayarKaydet(false)} title="Ön ayarı library/ekip.json'a kaydet"><Save size={13} /> Kaydet</Dugme>
        <Dugme onClick={() => onayarKaydet(true)} title="Kaydet ve her projede varsayılan yap"><Star size={13} /> Varsayılan</Dugme>
        <Dugme onClick={projeyeKaydet} disabled={!aktif} title="Yalnız bu proje için (work/edit/ekip.json)">Projeye</Dugme>
      </div>
      <div className="ekip-izgara" role="table" aria-label="Ekip slotları">
        {SLOTLAR.map((s) => {
          const sl = ayar.slotlar[s], m = ajanDurum?.[sl.motor], ym = sl.yedek_motor ? ajanDurum?.[sl.yedek_motor] : undefined;
          const d = durum?.slotlar?.[s];
          return (
            <div key={s} className="ekip-slot" role="row">
              <b title={SLOT_ADI[s]}>{s}</b>
              <MotorSec etiket={`${s} motor`} deger={sl.motor} durum={ajanDurum} sec={(v) => slotYaz(s, { motor: v, model: null, seviye: null })} />
              <ModelSecici motor={m} secili={sl.model ?? m?.varsayilan ?? ""} sec={(id) => slotYaz(s, { model: id })} />
              <SeviyeSec etiket={`${s} seviye`} m={m} deger={sl.seviye} sec={(v) => slotYaz(s, { seviye: v })} />
              <span className="ekip-yedek" title="Bir yeniden denemeden sonra bu motora geçer">
                yedek <MotorSec etiket={`${s} yedek motor`} bos deger={sl.yedek_motor} durum={ajanDurum} sec={(v) => slotYaz(s, { yedek_motor: v || null, yedek_model: null })} />
                {ym && <ModelSecici motor={ym} secili={sl.yedek_model ?? ym.varsayilan ?? ""} sec={(id) => slotYaz(s, { yedek_model: id })} />}
              </span>
              {d && <span className={`rozet ekip-${d.durum}`} title={d.model ?? ""}>{DURUM_ADI[d.durum]}{d.sure ? ` · ${Math.round(d.sure)} sn` : ""}{d.token ? ` · ${d.tahmini ? "~" : ""}${Math.round(d.token / 1000)}k tok` : ""}</span>}
              {!d && motorSebebi(m) && <span className="ipucu" title={motorSebebi(m)}>{m?.kurulu ? "uyarı" : "kurulu değil"}</span>}
            </div>
          );
        })}
      </div>
      <div className="ajan-edit">
        <label>Bölüş
          <select value={ayar.bolus} onChange={(e) => setAyar({ ...ayar, bolus: e.target.value as EkipAyar["bolus"] })}
            title="Rol: E1 kesim, E2 grafik, E3 ses. Zaman: video kelime sınırında üçe bölünür, her editör bir aralığı yapar">
            <option value="rol">Role göre</option><option value="zaman">Zamana göre</option>
          </select>
        </label>
        <label>Tur <input type="number" min={1} max={6} value={ayar.tur} onChange={(e) => setAyar({ ...ayar, tur: Math.max(1, Math.min(6, +e.target.value || 1)) })} style={{ width: 48 }} /></label>
        <label title="Aynı anda çalışan ajan">Eşzamanlı <input type="number" min={1} max={6} value={ayar.eszamanlilik} onChange={(e) => setAyar({ ...ayar, eszamanlilik: Math.max(1, Math.min(6, +e.target.value || 6)) })} style={{ width: 48 }} /></label>
        {durum && <span className="ekip-ozet" role="status">Tur {durum.tur}/{durum.tur_sinir} · {durum.asama} · açık <b>P0 {durum.acik.P0}</b> · P1 {durum.acik.P1} · P2 {durum.acik.P2} · kapanan {durum.kapanan}</span>}
      </div>
      <div className="ekip-sekmeler" role="tablist" aria-label="Ajan çıktısı">
        {SLOTLAR.map((s) => <button key={s} type="button" role="tab" className="sekme" aria-selected={sekme === s} onClick={() => setSekme(s)}>{s}</button>)}
      </div>
      <div className="gunluk ekip-gunluk" tabIndex={0} aria-label={`${sekme} çıktısı`}>
        {cikti.length ? cikti.map((l, i) => <div key={i} className={l.startsWith("→") ? "ajan-arac" : l.startsWith("Hata") ? "uyar" : undefined}>{l || " "}</div>)
          : <span className="ipucu">{sekme} henüz çalışmadı.</span>}
      </div>
      <div className="ajan-dugmeler">
        {calisan
          ? <Dugme tur="tehlike" onClick={() => istek(`/api/isler/${calisan.id}/iptal`, { method: "POST" }).catch(hata)}
              title="Bütün ajanları durdurur; kurgu son birleşen turda kalır"><CircleStop size={14} /> Hepsini durdur</Dugme>
          : <Dugme tur="birincil" disabled={!aktif || !!eksik.length} onClick={baslat}
              title={eksik.length ? `Kurulu olmayan motor: ${eksik.join(", ")}` : "3 editör yazar, vedit birleştirir, 3 denetçi izler; P0/P1 kalmayınca durur"}>
              <Users size={14} /> Ekiple editle</Dugme>}
      </div>
    </div>
  );
};
