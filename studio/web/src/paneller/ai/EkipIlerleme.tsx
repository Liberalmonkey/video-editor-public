import React, { useEffect, useState } from "react";
import { yokla } from "../../yokla";
import { istek } from "../../api";
import { slotSirasi, sn, tokenEtiketi, type EkipDurum, type SlotDurumAdi } from "./seviye";

// Swarm ilerlemesi: kapı adımları (G0–G7), orkestratörün kurduğu ajan kartları (rol, model, durum, süre), açık bulgu ve kural
// sayısı; karta tıklayınca o ajanın günlüğü. Canlı durum iş sürerken yoklanır; bittiğinde son koşu görünür kalır (ADR 0053, 0059).

const DURUM_ADI: Record<SlotDurumAdi, string> = { bekliyor: "bekliyor", calisiyor: "çalışıyor", bitti: "bitti", hata: "hata", yedek: "yedekte", atlandi: "atlandı" };

export const EkipIlerleme: React.FC<{ yol: string; calisanId?: number }> = ({ yol, calisanId }) => {
  const [durum, setDurum] = useState<EkipDurum | null>(null);
  const [secili, setSecili] = useState<string | null>(null);
  const [cikti, setCikti] = useState<string[]>([]);

  useEffect(() => {
    let iptal = false;
    // Eski (v2) koşunun durum dosyasında kapı listesi yok: gösterilmez.
    const oku = () => istek(`${yol}/durum`).then((d) => { if (!iptal) setDurum(d.yok || !Array.isArray(d.kapilar) ? null : d); }).catch(() => {});
    oku();
    if (!calisanId) return () => { iptal = true; };
    const dur = yokla(oku, 1500);
    return () => { iptal = true; dur(); };
  }, [yol, calisanId]);
  useEffect(() => {
    if (!secili) { setCikti([]); return; }
    let iptal = false;
    const oku = () => istek(`${yol}/cikti/${secili}?son=300`).then((d) => { if (!iptal) setCikti(d.satirlar ?? []); }).catch(() => {});
    oku();
    if (!calisanId) return () => { iptal = true; };
    const dur = yokla(oku, 2000);
    return () => { iptal = true; dur(); };
  }, [yol, secili, calisanId]);

  if (!durum) return calisanId ? <div className="ipucu ekip-bekle">Ekip hazırlanıyor…</div> : null;
  const slotlar = Object.entries(durum.slotlar).sort(([a], [b]) => slotSirasi(a, b));
  const kr = durum.kurallar;
  return (
    <section className="ekip-ilerleme" aria-label="Ekip ilerlemesi">
      <ol className="kapilar" aria-label="Kapılar">
        {durum.kapilar.map((k) => (
          <li key={k.id} className={`kapi ${k.durum}`} title={`${k.id} ${k.ad}${k.not ? ` · ${k.not}` : ""}`}>
            <i aria-hidden="true" /><span>{k.ad}</span>
          </li>
        ))}
      </ol>
      <div className="ekip-ozet" role="status">
        <span><b>{durum.bitti ? "Bitti" : durum.asama}</b>{durum.dagitim ? ` · ${durum.dagitim === "orkestrator" ? "orkestratör kurdu" : durum.dagitim === "hizli" ? "hızlı (orkestratörsüz)" : "varsayılan dağıtım"}` : ""}
          {` · ${slotlar.length - (durum.slotlar.O ? 1 : 0)} ajan`}{durum.en_cok ? ` / en çok ${durum.en_cok}` : ""}</span>
        <span>Açık <b className={durum.acik.P0 ? "hata-yazi" : ""}>P0 {durum.acik.P0}</b> · P1 {durum.acik.P1} · P2 {durum.acik.P2}</span>
        {kr && <span title="Atanan zorunlu kural, işlenen yeni kural, depoda doğrulanan">Kural: atanan {kr.atanan} · yeni {kr.yeni} · doğrulanan {kr.dogrulanan}
          {kr.uyum_eksik ? <b className="hata-yazi"> · uyum eksik {kr.uyum_eksik}</b> : null}
          {kr.dogrulanamayan ? <b className="hata-yazi"> · işlenemeyen {kr.dogrulanamayan}</b> : null}</span>}
      </div>
      <div className="ajan-kartlari" role="list">
        {slotlar.map(([s, d]) => (
          <button key={s} type="button" role="listitem" className={`ajan-kart ${d.durum}`} aria-pressed={secili === s}
            onClick={() => setSecili(secili === s ? null : s)} title={`${s} · ${d.motor} ${d.model ?? ""} · ${DURUM_ADI[d.durum] ?? d.durum}`}>
            <span className="kart-ust"><b>{s}</b><i className="kart-nokta" aria-hidden="true" /><span className="kart-durum">{DURUM_ADI[d.durum] ?? d.durum}</span></span>
            <span className="kart-rol">{d.rol || "—"}</span>
            <span className="kart-model" title={`${d.motor} ${d.model ?? ""}`}>{d.model || d.motor}</span>
            <span className="kart-alt">
              {d.aralik ? `${sn(d.aralik[0])}–${sn(d.aralik[1])} sn` : ""}
              {d.sure ? ` · ${Math.round(d.sure)} sn` : ""}{d.token ? ` · ${tokenEtiketi(d.token, d.tahmini)}` : ""}
            </span>
          </button>
        ))}
      </div>
      {secili && (
        <div className="gunluk ekip-gunluk" tabIndex={0} aria-label={`${secili} çıktısı`}>
          {cikti.length ? cikti.map((l, i) => <div key={i} className={l.startsWith("→") ? "ajan-arac" : l.startsWith("Hata") ? "uyar" : undefined}>{l || " "}</div>)
            : <span className="ipucu">{secili} henüz çıktı yazmadı.</span>}
        </div>
      )}
    </section>
  );
};
