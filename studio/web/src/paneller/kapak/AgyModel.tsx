// Antigravity model seçici: AI panelinin model listesi (/api/ajan/durum, `agy models`) ve "agy varsayılanı" seçeneği.
// WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md. Görsel modeli (Nano Banana) agy'de sabittir; burada seçilen,
// brief yazan ya da generate_image'ı çağıran modeldir.
import React, { useEffect, useMemo } from "react";
import { useDepo } from "../../depo";
import { modelGruplari } from "../AjanPaneli";

export const AgyModel: React.FC<{ etiket: string; deger: string; degis: (id: string) => void; ipucu: string }> = ({ etiket, deger, degis, ipucu }) => {
  const motor = useDepo((s) => s.ajanDurum?.antigravity);
  const ajanDurumAl = useDepo((s) => s.ajanDurumAl);
  useEffect(() => { if (!motor) void ajanDurumAl(); }, [motor, ajanDurumAl]);
  const gruplar = useMemo(() => modelGruplari(motor?.modeller ?? [], "", deger), [motor, deger]);
  // Listeden kalkmış bir model seçili kaldıysa varsayılana dön (iş kuyruğu listede olmayan modeli reddeder).
  useEffect(() => {
    if (deger && motor?.modeller.length && !motor.modeller.some((m) => m.id === deger)) degis("");
  }, [deger, motor, degis]);
  return (
    <label className="kapak-model" title={ipucu}>
      <span className="ipucu">{etiket}</span>
      <select aria-label={etiket} value={deger} onChange={(e) => degis(e.target.value)} disabled={motor?.kurulu === false}>
        <option value="">{motor?.kurulu === false ? "agy kurulu değil" : "agy varsayılanı"}</option>
        {gruplar.map(({ grup, liste }) => (
          <optgroup key={grup} label={grup}>{liste.map((m) => <option key={m.id} value={m.id}>{m.ad}</option>)}</optgroup>
        ))}
      </select>
    </label>
  );
};
