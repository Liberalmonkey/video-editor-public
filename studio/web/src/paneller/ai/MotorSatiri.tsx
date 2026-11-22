import React, { useEffect } from "react";
import { useDepo } from "../../depo";
import { ModelSecici, motorSebebi } from "./MotorModel";

// Tek ajanın motoru ve modeli: tek satır. Edit ve Sohbet sekmeleri aynı seçimi paylaşır (depo `ajan`).
const YEDEK = [["claude", "Claude Code"], ["antigravity", "Antigravity"], ["codex", "Codex"], ["opencode", "OpenCode"]];

export const MotorSatiri: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { ajanDurum, ajan, ajanDurumAl, ajanSec } = useDepo();
  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
  const motor = ajanDurum?.[ajan.motor];
  const sebep = ajanDurum ? motorSebebi(motor) : "";
  const durum = !ajanDurum ? "bekliyor" : !motor?.kurulu ? "yok" : motor.hata ? "uyari" : "hazir";
  return (
    <div className="motor-satiri">
      <span className="motor-sec-sar" title={sebep || `${motor?.ad ?? ""} ${motor?.surum ?? ""}`}>
        <i className={`motor-nokta ${durum}`} aria-hidden="true" />
        <select aria-label="AI motoru" value={ajan.motor} onChange={(e) => ajanSec({ motor: e.target.value })}>
          {(ajanDurum ? Object.entries(ajanDurum).map(([k, v]) => [k, v.ad, v.kurulu] as const) : YEDEK.map(([k, ad]) => [k, ad, true] as const))
            .map(([k, ad, kurulu]) => <option key={k} value={k} disabled={!kurulu}>{ad}{kurulu ? "" : " (kurulu değil)"}</option>)}
        </select>
      </span>
      <ModelSecici motor={motor} secili={ajan.model} sec={(id) => ajanSec({ model: id })} />
      {children}
      {sebep && ajanDurum && <span className="ipucu motor-sebep" role="status">{sebep}</span>}
    </div>
  );
};
