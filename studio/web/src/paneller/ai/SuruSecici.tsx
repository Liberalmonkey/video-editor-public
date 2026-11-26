import React, { useEffect, useState } from "react";
import type { MotorDurum } from "../../depo";
import { ModelSecici, MotorSec } from "./MotorModel";
import { EN_COK, EN_AZ, EN_COK_SINIR, SEVIYELER, suruOzet, tavan, type EkipAyar } from "./seviye";

// Swarm ayarı (ADR 0059): orkestratörün motoru ve modeli, ajan tavanı (editör + kalite kontrol), Hızlı anahtarı.
// Sayıyı, dağılımı ve her ajanın modelini orkestratör seçer; tavan yalnız üst sınırdır. Hızlıda plan çağrısı yoktur (ADR 0054).
export const SuruSecici: React.FC<{ ayar: EkipAyar; setAyar: (a: EkipAyar) => void; durum: Record<string, MotorDurum> | null; kilitli?: boolean }> = ({ ayar, setAyar, durum, kilitli }) => {
  const t = tavan(ayar);
  // Sayı kutusu yazılırken sıkıştırılmaz (1 → 12 yazılabilsin); sınır odak kaybında uygulanır.
  const [ham, setHam] = useState(String(t));
  useEffect(() => setHam(String(t)), [t]);
  const tavanYaz = () => {
    const n = Math.round(Number(ham));
    if (!Number.isFinite(n) || !ham.trim()) { setHam(String(t)); return; }
    setAyar({ ...ayar, en_cok: Math.max(EN_AZ, Math.min(EN_COK_SINIR, n)) });
  };
  const o = ayar.gruplar.orkestrator;
  const om = durum?.[o.motor];
  // Üstteki seçici O slot ezmesinden de üstündür; yoksa ön ayardaki ezme.O seçimi sessizce ezerdi.
  const orkYaz = (ek: Partial<typeof o>) => {
    const { O: _O, ...ezme } = ayar.ezme ?? {};
    setAyar({ ...ayar, ezme, gruplar: { ...ayar.gruplar, orkestrator: { ...o, ...ek } } });
  };
  return (
    <fieldset className="seviye-secici suru-secici" disabled={kilitli}>
      <label className="onay" title="Plan çağrısı yok: 2 editör, zaman dilimi başına kalite kontrol, kural kapısı deterministik, düzeltmeden sonra render yalnız gerekince (ADR 0054, 0058)">
        <input type="checkbox" checked={!!ayar.hizli} onChange={(e) => setAyar({ ...ayar, hizli: e.target.checked })} /> Hızlı
      </label>
      {!ayar.hizli && (
        <>
          <div className="suru-orkestrator" role="group" aria-label="Orkestratör">
            <span className="ai-etiket">Orkestratör</span>
            <MotorSec etiket="Orkestratör motor" deger={ayar.ezme?.O?.motor ?? o.motor} durum={durum} sec={(v) => orkYaz({ motor: v, model: null, seviye: null })} />
            <ModelSecici etiket="Orkestratör model" motor={om} secili={o.model ?? om?.varsayilan ?? ""} sec={(id) => orkYaz({ model: id })} />
          </div>
          <div className="segment" role="radiogroup" aria-label="En çok ajan">
            {SEVIYELER.map((s) => (
              <button key={s} type="button" role="radio" aria-checked={t === EN_COK[s]}
                onClick={() => setAyar({ ...ayar, ekip_seviye: s, en_cok: EN_COK[s] })} title={`En çok ${EN_COK[s]} ajan (editör + kalite kontrol)`}>
                <span className="seviye-ad">{EN_COK[s]}</span>
                <span className="seviye-sayi">ajan</span>
              </button>
            ))}
          </div>
          <label className="suru-tavan" title={`Editör + kalite kontrol üst sınırı (${EN_AZ}-${EN_COK_SINIR}); orkestratör daha azını seçebilir`}>En çok ajan
            <input type="number" min={EN_AZ} max={EN_COK_SINIR} value={ham} onChange={(e) => setHam(e.target.value)} onBlur={tavanYaz}
              onKeyDown={(e) => { if (e.key === "Enter") tavanYaz(); }} />
          </label>
        </>
      )}
      <span className="ipucu">{suruOzet(ayar)}</span>
    </fieldset>
  );
};
