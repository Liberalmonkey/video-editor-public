// 2. adım: fikir ve prompt. Kullanıcı fikrini yazar, agy onu skill kurallarıyla yapılı brief'e çevirir (oneri.json);
// kartlar düzenlenir ve kaydedilir (POST /oneri, agy'siz). Fikir boşsa öneri yalnız videodan yazılır.
import { Trash2, Wand2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { istek } from "../../api";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import { Metin, Satir, Secim, Sayi } from "../alanlar";
import type { Brief, Durum } from "./tipler";
import { KALIP } from "./yardimci";

const SAHNE_ALANLARI: [keyof Brief, string, string][] = [
  ["sahne", "Sahne", "tek özne, ne yapıyor, nerede"], ["ifade", "İfade", "yüz ifadesi"], ["kompozisyon", "Kompozisyon", "özne nerede, ne büyüklükte"],
  ["isik", "Işık", "ışık yönü ve sertliği"], ["palet", "Palet", "bir ana renk, bir vurgu"], ["yazi_alani", "Yazı alanı", "başlık için boş kalan yer"],
];

export const FikirAdimi: React.FC<{
  d: Durum; platform: string; video: string | null; seciliKare: number | null; metinModel: string; calisiyor: boolean; yenile: () => void;
}> = ({ d, platform, video, seciliKare, metinModel, calisiyor, yenile }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const { isBaslat, hata } = useDepo();
  const [fikir, setFikir] = useState(d.oneri?.fikir ?? "");
  const [adet, setAdet] = useState(1);
  useEffect(() => setFikir(d.oneri?.fikir ?? ""), [d.oneri?.fikir, aktif.studyo, aktif.ad, platform]);
  const briefler = d.oneri?.briefler ?? [];

  const gelistir = (metin: string) => isBaslat("kapak", {
    platform, gelistir: metin.trim(), adet, ...(metinModel ? { model: metinModel } : {}),
    ...(video ? { kapak_video: video } : {}), ...(seciliKare !== null ? { kare: seciliKare } : {}),
  });
  const kaydet = async (liste: Brief[]) => {
    try {
      await istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/oneri`, { method: "POST", json: { platform, fikir, briefler: liste.map(({ govde, ...b }) => b) } });
      yenile();
    } catch (e) { hata(e); }
  };
  const alan = (i: number, ad: keyof Brief, v: string) => kaydet(briefler.map((b, j) => (j === i ? { ...b, [ad]: v } : b)));

  return (
    <div className="kapak-adim-ic">
      <label className="ipucu" htmlFor="kapak-fikir">Fikrin (Türkçe; ne göstermek istiyorsun, hangi duygu, hangi söz)</label>
      <textarea id="kapak-fikir" rows={3} maxLength={800} value={fikir} onChange={(e) => setFikir(e.target.value)}
        placeholder="Ör. Ben laptopun başında şaşkın bakıyorum, ekranda video kendi kendine kurgulanıyor; yazı: 'Kurguyu AI yaptı'" />
      <div className="arac" style={{ flexWrap: "wrap", borderBottom: 0, padding: "4px 0" }}>
        <Dugme tur="birincil" onClick={() => gelistir(fikir)} disabled={calisiyor || !fikir.trim()}
          title="Fikrini kapak kurallarıyla (tek odak, kısa yazı, kontrast, kalıp) yapılı prompt'a çevirir; görsel üretmez">
          <Wand2 size={14} /> Prompt'u geliştir
        </Dugme>
        <Dugme onClick={() => gelistir("")} disabled={calisiyor} title="Fikir yazmadan, videonun metninden ve karelerinden öneri yazar; görsel üretmez">
          Videodan öner
        </Dugme>
        <Sayi etiket="Öneri sayısı" deger={adet} degis={(v) => setAdet(Math.round(v))} min={1} max={d.en_cok} />
        <span className="ipucu">Her öneri farklı açı dener. {seciliKare !== null && `Kare #${seciliKare} kullanılır.`}</span>
      </div>

      {briefler.map((b, i) => (
        <section key={i} className="kapak-brief" aria-label={`Öneri ${i + 1}`}>
          <div className="arac" style={{ justifyContent: "space-between", padding: "2px 0", borderBottom: 0 }}>
            <strong>Öneri {i + 1}{b.aci ? ` · ${b.aci}` : ""}</strong>
            {briefler.length > 1 && <Dugme tur="ikon" onClick={() => kaydet(briefler.filter((_, j) => j !== i))} title="Öneriyi sil" aria-label={`Öneri ${i + 1} sil`}><Trash2 size={12} /></Dugme>}
          </div>
          {b.not_tr && <p className="kapak-not">{b.not_tr}</p>}
          <Satir ad="1. satır"><Metin etiket="Birinci satır" deger={b.satir1 ?? ""} degis={(v) => alan(i, "satir1", v)} /></Satir>
          <Satir ad="2. satır"><Metin etiket="İkinci satır" deger={b.satir2 ?? ""} degis={(v) => alan(i, "satir2", v)} /></Satir>
          <Satir ad="Vurgu"><Metin etiket="Vurgu kelimesi" deger={b.vurgu ?? ""} degis={(v) => alan(i, "vurgu", v)} yer="2. satırdan tek kelime" /></Satir>
          <Satir ad="Kalıp"><Secim etiket="Kalıp" deger={b.kalip ?? ""} degis={(v) => alan(i, "kalip", v)}
            secenekler={[["", "—"], ...d.kaliplar.map((k): [string, string] => [k, KALIP[k]?.ad ?? k])]} /></Satir>
          {!!KALIP[b.kalip ?? ""]?.ek && <Satir ad="Ek söz"><Metin etiket={KALIP[b.kalip!].ek} deger={b.ek ?? ""} degis={(v) => alan(i, "ek", v)} /></Satir>}
          <Satir ad="Yazı stili"><Secim etiket="Yazı stili" deger={b.stil ?? ""} degis={(v) => alan(i, "stil", v)}
            secenekler={[["", "—"], ...d.stiller.map((x): [string, string] => [x.ad, x.ad])]} /></Satir>
          <details className="kapak-sahne">
            <summary>Sahne tarifi (görsel prompt'u, İngilizce)</summary>
            {SAHNE_ALANLARI.map(([ad, baslik, yer]) => (
              <Satir key={ad} ad={baslik}><Metin etiket={baslik} cok={ad === "sahne"} deger={String(b[ad] ?? "")} degis={(v) => alan(i, ad, v)} yer={yer} /></Satir>
            ))}
            <Satir ad="Elle prompt"><Metin etiket="Elle prompt" cok deger={b.prompt ?? ""} degis={(v) => alan(i, "prompt", v)}
              yer="boşsa yukarıdaki alanlardan kurulur" /></Satir>
            {b.govde && !b.prompt && <p className="ipucu" style={{ margin: 0 }}>agy'ye gidecek: {b.govde}</p>}
          </details>
        </section>
      ))}
      {!briefler.length && <p className="ipucu" style={{ margin: 0 }}>Henüz öneri yok. Fikrini yaz ya da videodan öner; sonra 3. adımda "Öneriyle üret".</p>}
    </div>
  );
};
