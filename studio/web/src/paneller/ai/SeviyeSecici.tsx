import React from "react";
import { SEVIYE, SEVIYE_ADI, SEVIYELER, seviyeOzet, type Seviye } from "./seviye";

// Ekip seviyesi: beş parçalı segment; altında seçilen seviyenin ekibi. Ajan sayısı seviyeyle sabittir (ADR 0053).
export const SeviyeSecici: React.FC<{ deger: Seviye; sec: (s: Seviye) => void; kilitli?: boolean }> = ({ deger, sec, kilitli }) => (
  <div className="seviye-secici">
    <div className="segment" role="radiogroup" aria-label="Ekip seviyesi">
      {SEVIYELER.map((s) => (
        <button key={s} type="button" role="radio" aria-checked={deger === s} disabled={kilitli} onClick={() => sec(s)}
          title={`${SEVIYE[s].editor} editör, ${SEVIYE[s].kk} kalite kontrol ve orkestratör`}>
          <span className="seviye-ad">{SEVIYE_ADI[s]}</span>
          <span className="seviye-sayi">{SEVIYE[s].editor}+{SEVIYE[s].kk}</span>
        </button>
      ))}
    </div>
    <span className="ipucu">{seviyeOzet(deger)}</span>
  </div>
);
