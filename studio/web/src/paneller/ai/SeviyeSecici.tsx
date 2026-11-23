import React from "react";
import { HIZLI_OZET, SEVIYE, SEVIYE_ADI, SEVIYELER, seviyeOzet, type Seviye } from "./seviye";

// Ekip seviyesi: beş parçalı segment; altında seçilen seviyenin ekibi. Ajan sayısı seviyeyle sabittir (ADR 0053).
// Hızlı (ADR 0054): seviye low'a kilitlenir, orkestratör çağrılmaz.
export const SeviyeSecici: React.FC<{ deger: Seviye; sec: (s: Seviye) => void; kilitli?: boolean; hizli?: boolean; hizliSec?: (h: boolean) => void }> = ({ deger, sec, kilitli, hizli, hizliSec }) => (
  <div className="seviye-secici">
    {hizliSec && (
      <label className="onay" title="2 editör ve 1 kalite kontrol; orkestratör çağrılmaz, kural kapısı deterministik, düzeltmeden sonra render yalnız gerekince (ADR 0054)">
        <input type="checkbox" checked={!!hizli} disabled={kilitli} onChange={(e) => hizliSec(e.target.checked)} /> Hızlı
      </label>
    )}
    <div className="segment" role="radiogroup" aria-label="Ekip seviyesi">
      {SEVIYELER.map((s) => (
        <button key={s} type="button" role="radio" aria-checked={hizli ? s === "low" : deger === s} disabled={kilitli || hizli} onClick={() => sec(s)}
          title={`${SEVIYE[s].editor} editör, ${SEVIYE[s].kk} kalite kontrol ve orkestratör`}>
          <span className="seviye-ad">{SEVIYE_ADI[s]}</span>
          <span className="seviye-sayi">{SEVIYE[s].editor}+{SEVIYE[s].kk}</span>
        </button>
      ))}
    </div>
    <span className="ipucu">{hizli ? HIZLI_OZET : seviyeOzet(deger)}</span>
  </div>
);
