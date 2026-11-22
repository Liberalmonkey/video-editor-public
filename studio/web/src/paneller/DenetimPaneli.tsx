import { CircleAlert, CircleCheck, Images, Play } from "lucide-react";
import React, { useEffect, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme } from "../ortak";
import { useKurgu, zamanKodu } from "../zaman/depo";
import { git } from "../zaman/oynatici";

interface Bulgu { kod: string; seviye: string; bas: number; bit: number; kanit: string; oneri: string }
interface Denetim {
  video: string | null; bulgular: Bulgu[]; hukum: string; onay: { zaman: string } | null; eski: boolean; kareler: string | null;
  format: { w: number; h: number; fps: number; sure: number }; loudness: { I: number; TP: number; LRA: number }; ses_tamam: boolean;
  kesim: { benzerlik: number; eksik: number; fazla: number } | null;
}

const RENK: Record<string, string> = { P0: "hata", P1: "uyari", P2: "" };

export const DenetimPaneli: React.FC = () => {
  const anahtar = useKurgu((d) => d.anahtar);
  const surum = useDepo((d) => d.surum);
  const { onayla, hata, goster, bildir } = useDepo();
  const [v, setV] = useState<Denetim | null>(null);

  useEffect(() => {
    if (!anahtar) { setV(null); useKurgu.setState({ bulgular: [] }); return; }
    istek(`/api/denetim/${anahtar}`).then((d) => {
      setV(d);
      // Eski denetimin zamanları güncel kurguya denk düşmez; timeline'a işaretlenmez.
      useKurgu.setState({ bulgular: d.video && !d.eski ? d.bulgular : [] });
    }).catch(hata);
  }, [anahtar, surum]);

  if (!anahtar) return <div className="panel"><Bos baslik="Proje seçilmedi" /></div>;
  if (!v?.video) return <div className="panel"><Bos baslik="Henüz denetim yok" metin="Final denetimi kendiliğinden çalıştırır. Bulgular zaman damgasıyla burada görünür, hiçbiri kendiliğinden uygulanmaz." /></div>;

  const kotu = v.hukum === "YAYINLANAMAZ";
  const onayVer = async () => {
    const tamam = await onayla({ baslik: "Yine de teslim et", onay: "Teslim et", tehlike: true, metin: `${v.video}\n\nÖlçüm bu videoyu yayınlanamaz buldu. Kararın kayda geçer.` });
    if (!tamam) return;
    try { setV(await istek(`/api/denetim/${anahtar}/onay`, { method: "POST" })); bildir("Teslim kararı kaydedildi"); } catch (e) { hata(e); }
  };

  return (
    <div className="panel">
      <div className={`hukum ${kotu ? "kotu" : "iyi"}`} role="status" data-hukum={v.hukum}>
        {kotu ? <CircleAlert size={16} /> : <CircleCheck size={16} />}
        <span style={{ flex: 1 }}>{kotu ? "Yayınlanamaz" : "Ölçümler temiz"}</span>
        {kotu && !v.onay && <Dugme tur="tehlike" onClick={onayVer}>Yine de teslim et</Dugme>}
        {kotu && v.onay && <span className="rozet uyari" title={v.onay.zaman}>Kararınla teslim</span>}
      </div>
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <span className="ad" style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={v.video}>{v.video}</span>
        {v.eski && <span className="rozet uyari" title="Kurgu bu denetimden sonra değişti">Eski</span>}
        {v.kareler && <Dugme onClick={() => goster({ tur: "gorsel", url: v.kareler!, ad: "Kontak sayfası" })}><Images size={14} /> Kareler</Dugme>}
      </div>
      <div className="icerik">
        <dl className="tani" style={{ padding: 8, margin: 0, borderBottom: "1px solid var(--cizgi)" }}>
          <dt>Format</dt><dd>{v.format.w}x{v.format.h} · {v.format.fps} fps · {v.format.sure.toFixed(1)} sn</dd>
          <dt>Ses</dt><dd style={{ color: v.ses_tamam ? undefined : "var(--hata)" }}>{v.loudness.I.toFixed(1)} LUFS · {v.loudness.TP.toFixed(1)} dBTP · LRA {v.loudness.LRA.toFixed(1)}</dd>
          {v.kesim && <><dt>Kesim</dt><dd>Benzerlik {v.kesim.benzerlik} · eksik {v.kesim.eksik} · fazla {v.kesim.fazla}</dd></>}
        </dl>
        {!v.bulgular.length && <Bos baslik="Şüphe bulunmadı" metin="Görsel rubrik ölçülmez; kareler için denetim skill'ini terminalden çalıştır." />}
        {v.bulgular.map((b, i) => (
          <button key={i} type="button" className="bulgu" onClick={() => git(b.bas)} title="Bu ana git">
            <span className="bulgu-ust">
              <span className={`rozet ${RENK[b.seviye] ?? ""}`}>{b.seviye}</span>
              <span className="bulgu-kod">{b.kod}</span>
              <span className="bulgu-t">{zamanKodu(b.bas, useKurgu.getState().kurgu?.sekans.fps ?? 30)}</span>
              <Play size={11} color="var(--y3)" />
            </span>
            <p>{b.kanit}</p>
            <p style={{ color: "var(--y1)" }}>{b.oneri}</p>
          </button>
        ))}
        {!!v.bulgular.length && <p className="ipucu" style={{ padding: 8, margin: 0 }}>Öneriler senin onayın olmadan uygulanmaz.</p>}
      </div>
    </div>
  );
};
