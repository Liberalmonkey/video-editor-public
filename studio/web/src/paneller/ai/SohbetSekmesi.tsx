import { CircleStop, MessageSquarePlus, Send } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { istek } from "../../api";
import { useDepo } from "../../depo";
import { Dugme, IkonDugme } from "../../ortak";
import { MotorSatiri } from "./MotorSatiri";

// Sohbet sekmesi: serbest soru ya da tek düzeltme; aynı oturum sürer, "Yeni sohbet" sıfırlar.
// WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md
export const SohbetSekmesi: React.FC = () => {
  const { ajanDurum, ajan, isler, gunlukler, sohbetBasi, aktif, ajanSec, ajanGonder, yeniSohbet, hata } = useDepo();
  const [istem, setIstem] = useState("");
  const kutu = useRef<HTMLDivElement>(null);
  const sohbet = isler.filter((x) => x.komut === "ajan" && x.id >= sohbetBasi).reverse();
  const calisan = sohbet.find((x) => x.durum === "calisiyor" || x.durum === "sirada");
  const motor = ajanDurum?.[ajan.motor];
  const satirSayisi = sohbet.reduce((n, x) => n + (gunlukler[x.id]?.length ?? 0), 0);
  useEffect(() => {
    const k = kutu.current;
    if (k && k.scrollHeight - k.scrollTop - k.clientHeight < 120) k.scrollTop = k.scrollHeight;
  }, [satirSayisi, sohbet.length]);

  const gonder = async () => {
    if (!istem.trim() || !motor?.kurulu) return;
    if (await ajanGonder(istem)) setIstem("");
  };

  return (
    <div className="ai-sohbet">
      <div className="ai-sohbet-ust">
        <MotorSatiri>
          <select aria-label="Çalışma modu" value={ajan.mod} onChange={(e) => ajanSec({ mod: e.target.value as "duzenle" | "plan" })}
            title={`Düzenle: ${motor?.mod_ipucu?.duzenle ?? "dosya düzenleyebilir"}. Yalnız plan: ${motor?.mod_ipucu?.plan ?? "okur ve önerir, dosyaya dokunmaz"}.`}>
            <option value="duzenle">Düzenle</option><option value="plan">Yalnız plan</option>
          </select>
          <IkonDugme ad="Yeni sohbet" onClick={yeniSohbet}><MessageSquarePlus size={14} /></IkonDugme>
        </MotorSatiri>
      </div>
      <div ref={kutu} className="gunluk" tabIndex={0} aria-label="Sohbet" aria-live="polite">
        {!sohbet.length && <span className="ipucu">{aktif ? `Mesaj ${aktif.studyo}/${aktif.ad} projesiyle gönderilir. ` : ""}Aynı sohbet sürer; "Yeni sohbet" sıfırlar.</span>}
        {sohbet.map((x) => (
          <div key={x.id} className="ajan-tur">
            <div className="ajan-baslik">{x.baslik}</div>
            {(gunlukler[x.id] ?? []).map((l, i) => <div key={i} className={l.startsWith("→") ? "ajan-arac" : l.startsWith("Hata") ? "uyar" : undefined}>{l || " "}</div>)}
            {x.durum === "calisiyor" && <div className="ajan-nabiz">Çalışıyor…</div>}
          </div>
        ))}
      </div>
      <div className="ajan-girdi">
        <textarea value={istem} rows={2} aria-label="Mesaj" placeholder="Soru sor ya da tek bir düzeltme iste (Ctrl+Enter gönderir)"
          onChange={(e) => setIstem(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); gonder(); } }} />
        {calisan
          ? <Dugme tur="tehlike" onClick={() => istek(`/api/isler/${calisan.id}/iptal`, { method: "POST" }).catch(hata)}><CircleStop size={14} /> Durdur</Dugme>
          : <Dugme tur="birincil" disabled={!istem.trim() || !motor?.kurulu} onClick={gonder}><Send size={14} /> Gönder</Dugme>}
      </div>
    </div>
  );
};
