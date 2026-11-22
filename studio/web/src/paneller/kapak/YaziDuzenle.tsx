// Yazı düzenleyici: canlı önizleme (sunucu render'la aynı şablonu doldurur), kalıp, stil, güvenli alan, varyasyon.
// WHY: bkz. wiki/decisions/0027-kapak-sayfasi.md. Kalıcı çizim iş kuyruğunda `vedit kapak --duzenle` (agy'siz).
import { Download } from "lucide-react";
import React, { useEffect, useState } from "react";
import { istek } from "../../api";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import { Satir, Secim, Sayi } from "../alanlar";
import { Onizleme } from "./Onizleme";
import type { Durum, Yazi } from "./tipler";
import { dosyaUrl, KALIP, tasanAlanlar, YERLESIM_ADI, yaziAlanlari } from "./yardimci";

export type DuzYazi = Yazi & { n: number };

export const YaziDuzenle: React.FC<{
  d: Durum; platform: string; duz: DuzYazi; setDuz: React.Dispatch<React.SetStateAction<DuzYazi | null>>;
  calisiyor: boolean; sec: (n: number) => void; varyasyon: () => void;
}> = ({ d, platform, duz, setDuz, calisiyor, sec, varyasyon }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const { isBaslat, hata } = useDepo();
  const [onizle, setOnizle] = useState("");
  const [alanGoster, setAlanGoster] = useState(true);
  const [kutu, setKutu] = useState<number[][]>([]); // önizlemede ölçülen yazı kutuları, tuval yüzdesi
  // Yazı değiştikçe önizleme: sunucu render'la aynı şablonu doldurur, dosya yazmaz.
  useEffect(() => {
    let gecerli = true;
    const t = setTimeout(() => {
      istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/onizle`, { method: "POST", json: { platform, n: duz.n, ...yaziAlanlari(duz) } })
        .then((r) => { if (gecerli) setOnizle(r.html); }).catch((e) => { if (gecerli) hata(e); });
    }, 250);
    return () => { gecerli = false; clearTimeout(t); };
  }, [duz, platform, aktif.studyo, aktif.ad]);

  const dikey = d.h > d.w;
  const tasan = [...new Set(kutu.flatMap((r) => tasanAlanlar(r, d.guvenli)))];
  const degis = (y: Partial<Yazi>) => setDuz((x) => (x ? { ...x, ...y } : x));
  const duzAday = d.adaylar.find((a) => a.n === duz.n);
  const kayitli = !!duzAday && JSON.stringify(yaziAlanlari(duz)) === JSON.stringify(yaziAlanlari(duzAday));
  const yaz = (kopya: boolean) => {
    if (kopya) varyasyon();
    isBaslat("kapak", { platform, duzenle: duz.n, kopya, ...yaziAlanlari(duz) });
  };

  return (
    <div className="kapak-duzenle-ic">
      <Onizleme html={onizle} w={d.w} h={d.h} alanlar={alanGoster ? d.guvenli : []} olc={setKutu} />
      <div className="ef-ic" style={{ flex: "1 1 240px", minWidth: 0 }}>
        <Satir ad="1. satır"><input aria-label="Adayın birinci satırı" maxLength={55} value={duz.satir1} onChange={(e) => degis({ satir1: e.target.value })} /></Satir>
        <Satir ad="2. satır"><input aria-label="Adayın ikinci satırı" maxLength={55} value={duz.satir2} onChange={(e) => degis({ satir2: e.target.value })} /></Satir>
        <Satir ad="Vurgu"><input aria-label="Vurgu kelimesi" maxLength={40} value={duz.vurgu} placeholder="boşsa tüm 2. satır" onChange={(e) => degis({ vurgu: e.target.value })} /></Satir>
        <Satir ad="Kalıp"><Secim etiket="Kapak kalıbı" deger={duz.kalip} degis={(v) => degis({ kalip: v })} secenekler={d.kaliplar.map((k): [string, string] => [k, KALIP[k]?.ad ?? k])} /></Satir>
        {!!KALIP[duz.kalip]?.ek && <Satir ad="Ek söz"><input aria-label={KALIP[duz.kalip].ek} maxLength={40} value={duz.ek} placeholder={KALIP[duz.kalip].ek} onChange={(e) => degis({ ek: e.target.value })} /></Satir>}
        <Satir ad="Stil"><Secim etiket="Yazı stili" deger={duz.stil} degis={(v) => degis({ stil: v, kutu: d.stiller.find((x) => x.ad === v)?.kutu ?? duz.kutu })} secenekler={d.stiller.map((x): [string, string] => [x.ad, x.ad])} /></Satir>
        <Satir ad="Yerleşim"><Secim etiket="Başlık yerleşimi" deger={duz.yerlesim} degis={(v) => degis({ yerlesim: v })} secenekler={d.yerlesimler.map((y): [string, string] => [y, YERLESIM_ADI[y] ?? y])} /></Satir>
        <Satir ad="Boyut"><Sayi etiket="Yazı boyutu" deger={duz.olcek} carpan={100} adim={5} min={60} max={140} birim="%" degis={(v) => degis({ olcek: Math.round(v * 100) / 100 })} /></Satir>
        <Satir ad="Karartma"><input type="checkbox" aria-label="Yazı arkası karartma" style={{ minHeight: 0 }} checked={duz.karart} onChange={(e) => degis({ karart: e.target.checked })} /></Satir>
        <Satir ad="Vurgu kutusu"><input type="checkbox" aria-label="Vurgu renkli kutuda" style={{ minHeight: 0 }} checked={duz.kutu} onChange={(e) => degis({ kutu: e.target.checked })} /></Satir>
        <Satir ad="Kırpma alanı"><input type="checkbox" aria-label="Kırpma alanlarını göster" style={{ minHeight: 0 }} checked={alanGoster} onChange={(e) => setAlanGoster(e.target.checked)} /></Satir>
        {duzAday && kayitli && !!(duzAday.olcum?.notlar.length || duzAday.elestiri) && (
          <ul className="kapak-notlar" aria-label="Ölçüm ve eleştiri">
            {duzAday.olcum?.notlar.map((n) => <li key={n}>{n}</li>)}
            {duzAday.elestiri && <li>Eleştiri{duzAday.puan !== null ? ` (${duzAday.puan}/10)` : ""}: {duzAday.elestiri}</li>}
          </ul>
        )}
        {tasan.length > 0 && <p role="status" className="rozet uyari" style={{ height: "auto", padding: "3px 6px", margin: 0 }}>Yazı güvenli alanı aşıyor: {tasan.join(", ")}. Yazıyı kısalt ya da boyutu küçült.</p>}
        <p className="ipucu" style={{ margin: 0 }}>
          {KALIP[duz.kalip]?.ipucu} {d.kesitli.includes(duz.kalip) && "Özne kesiti \"Yazıyı uygula\" ile alınır; önizlemede yazı öznenin üstünde görünebilir. "}
          {d.guvenli.map((g) => `${g.ad}: ${g.tur === "dis" ? "yazı girmez" : "yazı içinde kalır"}`).join(" · ")}. Yazı kodla çizilir; zemin yeniden üretilmez.
        </p>
        {duzAday && (
          <div className="kapak-kucuk" title="İzleyicinin gördüğü boyut: karar bu boyutta verilir">
            <img src={dosyaUrl(aktif, "outputs", duzAday.yol, duzAday.v)} alt={`Kapak ${duz.n} küçük boyutta`} style={{ width: dikey ? 90 : 168, aspectRatio: dikey ? "3 / 4" : "16 / 9", objectFit: "cover" }} />
            <span className="ipucu">{dikey ? "Izgarada (3:4)" : "Akışta 168 px"}: kayıtlı aday</span>
          </div>
        )}
        <div className="arac" style={{ flexWrap: "wrap", borderBottom: 0, padding: 0 }}>
          <Dugme tur="birincil" onClick={() => yaz(false)} disabled={calisiyor || kayitli} title="Bu adayı yeni yazıyla yeniden çizer">Yazıyı uygula</Dugme>
          <Dugme onClick={() => yaz(true)} disabled={calisiyor} title="Aynı zeminle yeni aday açar; agy kotası harcamaz">Varyasyon olarak kaydet</Dugme>
          <Dugme onClick={() => sec(duz.n)} disabled={calisiyor || !kayitli} title={kayitli ? "Adayı teslim klasörüne kopyalar" : "Önce yazıyı uygula"}>Teslim et</Dugme>
          {duzAday && <a className="dugme" href={dosyaUrl(aktif, "outputs", duzAday.yol, duzAday.v)} download={`kapak-${platform}-${duz.n}.jpg`} title="Çizilmiş adayı indir"><Download size={14} /> İndir</a>}
        </div>
      </div>
    </div>
  );
};
