// Aday ızgarası: büyüt, düzenle (yazı ya da görsel), seç/teslim et. Rozetler zeminin kaynağını ve düzeltme zincirini gösterir.
import { Check, Pencil } from "lucide-react";
import React from "react";
import { useDepo } from "../../depo";
import { Bos, Dugme } from "../../ortak";
import { Guvenli } from "./Onizleme";
import type { Aday, Durum } from "./tipler";
import { dosyaUrl, KALIP, KAYNAK_ADI } from "./yardimci";

export const AdayIzgarasi: React.FC<{
  d: Durum | null; duzN: number | null; duzenle: (a: Aday | null) => void; sec: (n: number) => void; calisiyor: boolean;
}> = ({ d, duzN, duzenle, sec, calisiyor }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const goster = useDepo((s) => s.goster);
  if (!d?.adaylar.length) return <Bos baslik="Henüz aday yok" metin="Varsayılan tek aday; istersen 2-5 seç. Her aday farklı bir açı ve kalıp dener." />;
  const dikey = d.h > d.w;
  return (
    <>
      <div className="kapak-izgara" style={{ gridTemplateColumns: `repeat(auto-fill, minmax(${dikey ? 140 : 220}px, 1fr))` }}>
        {[...d.adaylar].reverse().map((a) => {
          const secili = d.secim?.n === a.n;
          const acik = duzN === a.n;
          const url = dosyaUrl(aktif, "outputs", a.yol, a.v);
          return (
            <figure key={a.n} className={`kapak-aday${secili || acik ? " secili" : ""}`}>
              <button type="button" onClick={() => goster({ tur: "gorsel", url, ad: `Kapak ${a.n}` })} title="Büyüt"
                className="kapak-aday-gorsel" style={{ aspectRatio: dikey ? "9 / 16" : "16 / 9" }}>
                <img src={url} alt={`Kapak adayı ${a.n}`} />
                <Guvenli alanlar={d.guvenli} />
              </button>
              <figcaption className="arac" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                <span className="ipucu" title={[a.aci, a.duzeltme && `Düzeltme: ${a.duzeltme}`, ...(a.olcum?.notlar ?? []), a.elestiri].filter(Boolean).join("\n") || undefined}>
                  #{a.n} · {KALIP[a.kalip]?.ad ?? a.kalip}
                  {a.puan !== null && <b> · {a.puan}/10</b>}
                  {a.ebeveyn !== null && <span className="rozet vurgu" style={{ marginLeft: 4 }}>#{a.ebeveyn}'ten düzeltme</span>}
                  {a.zemin_kaynagi && a.zemin_kaynagi !== "agy" && a.ebeveyn === null && <span className="rozet" style={{ marginLeft: 4 }}>{KAYNAK_ADI[a.zemin_kaynagi] ?? a.zemin_kaynagi}</span>}
                  {a.olcum && !a.olcum.gecti && <span className="rozet uyari" style={{ marginLeft: 4 }}>{a.olcum.notlar.length} uyarı</span>}
                </span>
                <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                  <Dugme tur="ikon" acik={acik} onClick={() => duzenle(acik ? null : a)} title="Yazıyı ya da görseli düzelt" aria-label={`Kapak ${a.n} düzelt`}><Pencil size={14} /></Dugme>
                  {secili && !d.secim?.eski
                    ? <span className="rozet"><Check size={12} /> {d.secim?.dosya}</span>
                    : <Dugme onClick={() => sec(a.n)} disabled={calisiyor} title={secili ? "Aday teslimden sonra değişti" : "Teslim klasörüne kopyalar; master prompt da yazılır"}>{secili ? "Yeniden teslim et" : "Seç"}</Dugme>}
                </span>
              </figcaption>
            </figure>
          );
        })}
      </div>
      <p className="ipucu" style={{ padding: "0 8px", margin: 0 }}>
        Çizgiler kırpma alanıdır: {d.guvenli.map((g) => g.ad).join(", ")}. Kırmızı bölgeyi platform arayüzü örter.
      </p>
    </>
  );
};
