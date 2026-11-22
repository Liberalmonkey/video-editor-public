import { Plus, Type } from "lucide-react";
import React from "react";
import { useDepo } from "../depo";
import { Bos, Dugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { METIN_SABLONLARI, SABLONLAR, type MetinSablon, type Sablon } from "./sablonlar";

export const GrafikPaneli: React.FC = () => {
  const var_ = useKurgu((d) => !!d.kurgu);
  const aktifSec = (id: string | undefined) => { if (id) useKurgu.getState().sec([id]); };

  const ekle = (s: Sablon) => {
    const d = useKurgu.getState();
    let id: string | undefined;
    d.duzenle(`${s.ad} ekle`, (f) => { id = K.sahneEkle(f, d.zaman, JSON.parse(JSON.stringify(s.sahne)), s.sure)?.id; });
    aktifSec(id);
    if (!id) useDepo.getState().bildir("Kilitsiz video izi yok", true);
  };
  const metin = () => {
    const d = useKurgu.getState();
    let id: string | undefined;
    d.duzenle("Metin ekle", (f) => { id = K.metinEkle(f, d.zaman, "Metin")?.id; });
    aktifSec(id);
  };
  const metinGrafik = (s: MetinSablon) => {
    const d = useKurgu.getState();
    let id: string | undefined;
    d.duzenle(`${s.ad} ekle`, (f) => {
      id = K.klipEkle(f, { tur: "metin", iz: K.bosIz(f, d.zaman, d.zaman + s.sure), bas: d.zaman, sure: s.sure, metin: s.metin,
        metin_stil: { tip: s.tip, ...JSON.parse(JSON.stringify(s.stil)) } })?.id;
    });
    aktifSec(id);
  };

  if (!var_) return <div className="panel"><Bos baslik="Kurgu yok" metin="Grafik eklemek için bir proje aç." /></div>;
  return (
    <div className="panel">
      <div className="arac"><Dugme onClick={metin} title="Metin ekle (T)"><Type size={14} /> Metin</Dugme><span className="ipucu">Oynatma kafasına eklenir</span></div>
      <div className="icerik">
        <div className="baslik">Sahneler</div>
        {SABLONLAR.map((s) => (
          <div key={s.kind} className="satir" title={s.aciklama}>
            <span className="ad"><b style={{ fontWeight: 550 }}>{s.ad}</b> <span className="ipucu">{s.aciklama}</span></span>
            <Dugme aria-label={`${s.ad} ekle`} onClick={() => ekle(s)}><Plus size={13} /></Dugme>
          </div>
        ))}
        <div className="baslik">Motion metin</div>
        {METIN_SABLONLARI.map((s) => (
          <div key={s.tip} className="satir" title={s.aciklama}>
            <span className="ad"><b style={{ fontWeight: 550 }}>{s.ad}</b> <span className="ipucu">{s.aciklama}</span></span>
            <Dugme aria-label={`${s.ad} ekle`} onClick={() => metinGrafik(s)}><Plus size={13} /></Dugme>
          </div>
        ))}
        <p className="ipucu" style={{ padding: 8, margin: 0 }}>Hazır motion klipleri ve panolar Kütüphane panelinde.</p>
      </div>
    </div>
  );
};
