// Görsel düzeltme: adayın üstüne fareyle kutu çizilir (isteğe bağlı), istek yazılır; agy zemini "düzenle, baştan üretme"
// kuralıyla değiştirir ve sonuç yeni aday olur (eski aday kalır). Kutu varken varsayılan olarak yalnız kutu değişir.
// WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md (kırmızı kutu tekniği, geri yapıştırma).
import { SquareDashed, Wand2, X } from "lucide-react";
import React, { useRef, useState } from "react";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import type { Aday, Durum } from "./tipler";
import { dosyaUrl, DUZELT_CIPLER, kutuNormal } from "./yardimci";

type Bolge = [number, number, number, number];

export const GorselDuzelt: React.FC<{
  d: Durum; a: Aday; platform: string; gorselModel: string; calisiyor: boolean; bekle: () => void;
}> = ({ d, a, platform, gorselModel, calisiyor, bekle }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const isBaslat = useDepo((s) => s.isBaslat);
  const alan = useRef<HTMLDivElement>(null);
  const bas = useRef<[number, number] | null>(null);
  const [bolge, setBolge] = useState<Bolge | null>(null);
  const [taslak, setTaslak] = useState<Bolge | null>(null);
  const [istekMetni, setIstek] = useState("");
  const [yalniz, setYalniz] = useState(true);
  const dikey = d.h > d.w;

  const yuzde = (e: React.PointerEvent): [number, number] => {
    const r = alan.current!.getBoundingClientRect();
    return [((e.clientX - r.left) / r.width) * 100, ((e.clientY - r.top) / r.height) * 100];
  };
  const gonder = () => {
    bekle();
    isBaslat("kapak", {
      platform, gorsel_duzelt: a.n, istek_metni: istekMetni.trim(),
      ...(bolge ? { bolge, yalniz_bolge: yalniz } : {}), ...(gorselModel ? { gorsel_model: gorselModel } : {}),
    });
  };
  const goster = taslak ?? bolge;

  return (
    <div className="kapak-duzenle-ic">
      <div ref={alan} className="kapak-cizim" style={{ aspectRatio: `${d.w} / ${d.h}`, maxWidth: dikey ? 280 : 560 }}
        onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); bas.current = yuzde(e); setTaslak(null); }}
        onPointerMove={(e) => { if (bas.current) { const k = kutuNormal(bas.current, yuzde(e)); setTaslak(k); } }}
        onPointerUp={(e) => {
          if (!bas.current) return;
          const k = kutuNormal(bas.current, yuzde(e));
          bas.current = null;
          setTaslak(null);
          if (k) setBolge(k);
        }}
        role="application" aria-label="Düzeltilecek bölgeyi fareyle çiz">
        <img src={dosyaUrl(aktif, "outputs", a.yol, a.v)} alt={`Kapak ${a.n}`} draggable={false} />
        {goster && <span className="kapak-bolge" style={{ left: `${goster[0]}%`, top: `${goster[1]}%`, width: `${goster[2] - goster[0]}%`, height: `${goster[3] - goster[1]}%` }} />}
      </div>
      <div className="ef-ic" style={{ flex: "1 1 240px", minWidth: 0 }}>
        <p className="ipucu" style={{ margin: 0 }}>
          <SquareDashed size={12} /> Değişecek yeri görselin üstünde sürükleyerek çiz (isteğe bağlı). Kutu yoksa istek bütün görsele uygulanır.
          Yazı kodla çizildiği için yazıyı burada değil Yazı sekmesinde düzelt.
        </p>
        <label className="ipucu" htmlFor="kapak-duzelt-istek">Ne değişsin?</label>
        <textarea id="kapak-duzelt-istek" rows={2} maxLength={400} value={istekMetni} onChange={(e) => setIstek(e.target.value)}
          placeholder="Ör. arka planı koyu laciverte çevir, laptop ekranı daha parlak olsun" />
        <div className="kapak-cipler">
          {DUZELT_CIPLER.map((c) => <button key={c} type="button" className="kapak-cip" onClick={() => setIstek(c)}>{c}</button>)}
        </div>
        {bolge && (
          <div className="arac" style={{ borderBottom: 0, padding: 0, flexWrap: "wrap" }}>
            <span className="rozet vurgu">Kutu: %{bolge.map((v) => Math.round(v)).join(", ")}</span>
            <label className="ipucu"><input type="checkbox" checked={yalniz} onChange={(e) => setYalniz(e.target.checked)} style={{ minHeight: 0 }} /> Yalnız kutu değişsin (dışı piksel piksel korunur)</label>
            <Dugme tur="ikon" onClick={() => setBolge(null)} title="Kutuyu kaldır" aria-label="Kutuyu kaldır"><X size={14} /></Dugme>
          </div>
        )}
        <div className="arac" style={{ borderBottom: 0, padding: 0 }}>
          <Dugme tur="birincil" onClick={gonder} disabled={calisiyor || !istekMetni.trim()} title="agy ile düzeltir; sonuç yeni aday olur, yazı aynen kalır (1 görsel kotası)">
            <Wand2 size={14} /> {calisiyor ? "Çalışıyor…" : "Görseli düzelt"}
          </Dugme>
          {a.duzeltme && <span className="ipucu">Bu aday #{a.ebeveyn}'ten: “{a.duzeltme}”</span>}
        </div>
      </div>
    </div>
  );
};
