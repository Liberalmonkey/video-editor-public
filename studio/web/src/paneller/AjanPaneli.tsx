import { RefreshCw } from "lucide-react";
import React, { useEffect, useState } from "react";
import { istek } from "../api";
import { useDepo, type MotorDurum } from "../depo";
import { IkonDugme } from "../ortak";
import { EditSekmesi } from "./ai/EditSekmesi";
import { modelAdi } from "./ai/MotorModel";
import { slotSirasi, type EkipDurum, type SlotDurum } from "./ai/seviye";
import { SohbetSekmesi } from "./ai/SohbetSekmesi";

// AI paneli: iki sekme. Edit: istek, birkaç ayar, tek ajan ya da seviyeli ekip, tek birincil düğme, ilerleme ve sonuç.
// Sohbet: serbest soru ve tek düzeltme. WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md, 0028-ai-edit.md, 0053-seviyeli-ekip-orkestrator.md
export { istektekiStil } from "./ai/EditSekmesi";
export { modelAdi, modelGruplari, ModelSecici } from "./ai/MotorModel";

type Sekme = "edit" | "sohbet";
const ilkSekme = (): Sekme => { try { return localStorage.getItem("aiSekme") === "sohbet" ? "sohbet" : "edit"; } catch { return "edit"; } };

export const AjanPaneli: React.FC = () => {
  const { ajanDurum, ajanDurumAl, isler } = useDepo();
  const [sekme, setSekme] = useState<Sekme>(ilkSekme);
  useEffect(() => { try { localStorage.setItem("aiSekme", sekme); } catch { /* tarayıcı depolaması kapalı */ } }, [sekme]);
  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
  const sohbetCalisiyor = isler.some((x) => x.komut === "ajan" && (x.durum === "calisiyor" || x.durum === "sirada"));
  const editCalisiyor = isler.some((x) => x.komut === "ai-edit" && (x.durum === "calisiyor" || x.durum === "sirada"));
  return (
    <div className="panel ajan ai-panel">
      <div className="arac ai-baslik">
        <div className="segment" role="tablist" aria-label="AI bölümü">
          <button type="button" role="tab" aria-selected={sekme === "edit"} onClick={() => setSekme("edit")}>
            Edit{editCalisiyor && <i className="sekme-nabiz" aria-label="çalışıyor" />}
          </button>
          <button type="button" role="tab" aria-selected={sekme === "sohbet"} onClick={() => setSekme("sohbet")}>
            Sohbet{sohbetCalisiyor && <i className="sekme-nabiz" aria-label="çalışıyor" />}
          </button>
        </div>
        <span style={{ flex: 1 }} />
        <IkonDugme ad="Motorları ve modelleri yeniden tara" onClick={() => ajanDurumAl(true)}><RefreshCw size={13} /></IkonDugme>
      </div>
      {sekme === "edit" ? <EditSekmesi /> : <SohbetSekmesi />}
    </div>
  );
};

// Üst çubuk rozeti: hangi motor, hangi model, çalışıyor mu. Tıklayınca AI paneline gider.
export const AjanRozeti: React.FC<{ ac: () => void }> = ({ ac }) => {
  const { ajanDurum, ajan, isler, ajanDurumAl, aktif } = useDepo();
  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
  const motor = ajanDurum?.[ajan.motor];
  const calisan = isler.find((x) => (x.komut === "ajan" || x.komut === "ai-edit") && (x.durum === "calisiyor" || x.durum === "sirada"));
  const ekipDurum = useEkipCalisan(calisan?.motor === "ekip" && aktif ? `/api/ekip/${aktif.studyo}/${aktif.ad}/durum` : null);
  if (calisan?.motor === "ekip") return <EkipRozeti ac={ac} durum={ekipDurum} seviye={calisan.model} motorlar={ajanDurum} />;
  const durum = !ajanDurum ? "…" : !motor?.kurulu ? "Kurulu değil" : calisan ? "Çalışıyor" : "Hazır";
  const gosterilen = calisan ? ajanDurum?.[calisan.motor ?? ""] : motor;
  const mId = calisan?.model ?? ajan.model;
  const m = modelAdi(gosterilen, mId);
  const motorAd = gosterilen?.ad ?? calisan?.motor ?? ajan.motor;
  return (
    <button type="button" className={`ajan-rozet ${calisan ? "calisiyor" : ""} ${ajanDurum && !motor?.kurulu ? "yok" : ""}`} onClick={ac}
      title={`${motorAd} ${gosterilen?.surum ?? ""} · model ${mId} · ${durum}. AI panelini aç.`}>
      <i aria-hidden="true" /><span className="rozet-metin">{motorAd} · <b>{m}</b> · {durum}</span>
    </button>
  );
};

// Ekip koşusunda rozet tek ajan seçimini değil, o an çalışan slotları gösterir (O, E1…, K1…; motor ve model).
// WHY: ekip işi tek motora bağlı değil; rozet eskiden tek ajan seçimini (claude) gösteriyor, Antigravity seçilmiş gibi durmuyordu.
const useEkipCalisan = (yol: string | null): EkipDurum | null => {
  const [d, setD] = useState<EkipDurum | null>(null);
  useEffect(() => {
    if (!yol) { setD(null); return; }
    let iptal = false;
    const oku = () => istek(yol).then((x) => { if (!iptal) setD(x.yok || !x.slotlar ? null : x); }).catch(() => {});
    oku();
    const t = window.setInterval(oku, 2000);
    return () => { iptal = true; window.clearInterval(t); };
  }, [yol]);
  return d;
};

const EkipRozeti: React.FC<{ ac: () => void; durum: EkipDurum | null; seviye?: string | null; motorlar: Record<string, MotorDurum> | null }> = ({ ac, durum, seviye, motorlar }) => {
  const calisan = Object.entries(durum?.slotlar ?? {}).filter(([, s]) => s.durum === "calisiyor" || s.durum === "yedek").sort(([a], [b]) => slotSirasi(a, b));
  const ad = (s: SlotDurum) => `${motorlar?.[s.motor]?.ad ?? s.motor} ${modelAdi(motorlar?.[s.motor], s.model ?? "")}`.trim();
  const modeller = [...new Set(calisan.map(([, s]) => ad(s)))];
  const slotlar = calisan.map(([x]) => x).join(", ");
  const metin = calisan.length ? `${slotlar} · ` : `${durum?.asama ?? "hazırlanıyor"} · `;
  return (
    <button type="button" className="ajan-rozet calisiyor" onClick={ac}
      title={`Ekip ${seviye ?? ""}: ${calisan.map(([x, s]) => `${x} ${ad(s)}${s.durum === "yedek" ? " (yedek)" : ""}`).join("; ") || "ajan çalışmıyor"}. AI panelini aç.`}>
      <i aria-hidden="true" /><span className="rozet-metin">Ekip · {metin}<b>{modeller.length > 2 ? `${modeller.length} model` : modeller.join(" + ") || seviye}</b> · Çalışıyor</span>
    </button>
  );
};
