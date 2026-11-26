import { Save, Star } from "lucide-react";
import React, { useState } from "react";
import type { MotorDurum } from "../../depo";
import { Dugme } from "../../ortak";
import { ModelSecici, MotorSec, SeviyeSec } from "./MotorModel";
import { editorSlotlari, GRUP_ADI, GRUPLAR, grup, kkSlotlari, tavan, type EkipAyar, type Grup, type Slot } from "./seviye";

// Swarm ayarları çekmecesi: üç grubun varsayılan modeli (orkestratör kartta başka model seçebilir), isteğe bağlı slot ezmesi
// (orkestratörün seçimini ezer), eşzamanlılık, ön ayar. Günlük kullanımda kapalı kalır (ADR 0059).

const SlotSatiri: React.FC<{ ad: string; sl: Slot; durum: Record<string, MotorDurum> | null; yaz: (ek: Partial<Slot>) => void }> = ({ ad, sl, durum, yaz }) => {
  const m = durum?.[sl.motor];
  const ym = sl.yedek_motor ? durum?.[sl.yedek_motor] : undefined;
  return (
    <div className="ekip-grup" role="group" aria-label={ad}>
      <b>{ad}</b>
      <div className="ekip-grup-alan">
        <MotorSec etiket={`${ad} motor`} deger={sl.motor} durum={durum} sec={(v) => yaz({ motor: v, model: null, seviye: null })} />
        <ModelSecici etiket={`${ad} model`} motor={m} secili={sl.model ?? m?.varsayilan ?? ""} sec={(id) => yaz({ model: id })} />
        <SeviyeSec etiket={`${ad} effort`} m={m} deger={sl.seviye} sec={(v) => yaz({ seviye: v })} />
      </div>
      <div className="ekip-grup-alan ekip-yedek" title="Bir yeniden denemeden sonra bu motora geçer">
        <MotorSec etiket={`${ad} yedek motor`} bos deger={sl.yedek_motor} durum={durum} sec={(v) => yaz({ yedek_motor: v || null, yedek_model: null })} />
        {ym && <ModelSecici etiket={`${ad} yedek model`} motor={ym} secili={sl.yedek_model ?? ym.varsayilan ?? ""} sec={(id) => yaz({ yedek_model: id })} />}
      </div>
    </div>
  );
};

export const EkipAyarlari: React.FC<{
  ayar: EkipAyar; setAyar: (a: EkipAyar) => void; durum: Record<string, MotorDurum> | null;
  onayarlar: Record<string, EkipAyar>; varsayilan: string | null; projeVar: boolean;
  onayarSec: (ad: string) => void; onayarKaydet: (ad: string, varsayilan: boolean) => void; projeyeKaydet: () => void;
}> = ({ ayar, setAyar, durum, onayarlar, varsayilan, projeVar, onayarSec, onayarKaydet, projeyeKaydet }) => {
  const [ad, setAd] = useState(ayar.ad);
  const grupYaz = (g: Grup, ek: Partial<Slot>) => setAyar({ ...ayar, gruplar: { ...ayar.gruplar, [g]: { ...ayar.gruplar[g], ...ek } } });
  const ezmeYaz = (s: string, sl: Slot | null) => {
    const ezme = { ...ayar.ezme };
    if (sl) ezme[s] = sl; else delete ezme[s];
    setAyar({ ...ayar, ezme });
  };
  // Tavanın dışında kalan eski ezmeler de görünür kalır: kurulu olmayan motoru taşıyorsa kullanıcı temizleyebilsin.
  const ezilebilir = [...new Set(["O", ...editorSlotlari(tavan(ayar)), ...kkSlotlari(tavan(ayar)), ...Object.keys(ayar.ezme ?? {})])];
  const ezilen = Object.keys(ayar.ezme ?? {}).filter((s) => ezilebilir.includes(s));
  return (
    <div className="ekip-ayarlari">
      {GRUPLAR.map((g) => <SlotSatiri key={g} ad={GRUP_ADI[g]} sl={ayar.gruplar[g]} durum={durum} yaz={(ek) => grupYaz(g, ek)} />)}
      <details className="ekip-ezme">
        <summary>Slot bazında ez{ezilen.length ? ` (${ezilen.length})` : ""}</summary>
        <p className="ipucu">Seçilen slot grubun ve orkestratörün seçimi yerine kendi motorunu kullanır (ör. yalnız E1 için daha güçlü model).</p>
        <div className="ezme-cipler">
          {ezilebilir.map((s) => (
            <label key={s} className="cip">
              <input type="checkbox" checked={!!ayar.ezme?.[s]} onChange={(e) => ezmeYaz(s, e.target.checked ? { ...ayar.gruplar[grup(s)] } : null)} />{s}
            </label>
          ))}
        </div>
        {ezilen.map((s) => <SlotSatiri key={s} ad={s} sl={ayar.ezme[s]} durum={durum} yaz={(ek) => ezmeYaz(s, { ...ayar.ezme[s], ...ek })} />)}
      </details>
      <label className="ekip-es" title="Aynı anda çalışan ajan; boş: editör sayısı">Eşzamanlı ajan
        <input type="number" min={1} max={15} value={ayar.eszamanlilik ?? ""} placeholder="otomatik"
          onChange={(e) => setAyar({ ...ayar, eszamanlilik: e.target.value ? Math.max(1, Math.min(15, +e.target.value)) : null })} />
      </label>
      <div className="ekip-onayar">
        <select aria-label="Ön ayar" value={onayarlar[ayar.ad] ? ayar.ad : ""} onChange={(e) => { onayarSec(e.target.value); setAd(e.target.value); }}>
          <option value="" disabled>Ön ayar seç</option>
          {Object.keys(onayarlar).map((k) => <option key={k} value={k}>{k}{k === varsayilan ? " · varsayılan" : ""}</option>)}
        </select>
        <input aria-label="Ön ayar adı" value={ad} onChange={(e) => setAd(e.target.value)} size={12} />
        <Dugme onClick={() => onayarKaydet(ad, false)} title="Ön ayarı library/ekip.json'a kaydet"><Save size={13} /> Kaydet</Dugme>
        <Dugme onClick={() => onayarKaydet(ad, true)} title="Kaydet ve her projede varsayılan yap"><Star size={13} /> Varsayılan</Dugme>
        <Dugme onClick={projeyeKaydet} disabled={!projeVar} title="Yalnız bu proje için (work/edit/ekip.json)">Projeye</Dugme>
      </div>
    </div>
  );
};
