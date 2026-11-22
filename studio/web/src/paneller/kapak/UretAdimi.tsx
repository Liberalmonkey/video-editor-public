// 3. adım: üretim. Kaynak öneri (2. adım), videodan brief ya da elle yazı/prompt; modeller agy listesinden.
// Görsel modeli agy'de sabit; rozet adını ve kota açılışını gösterir (gorsel.kota). WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md
import { MessageSquareWarning, Sparkles } from "lucide-react";
import React, { useState } from "react";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import { Bolum, Metin, Satir, Secim, Sayi } from "../alanlar";
import { AgyModel } from "./AgyModel";
import type { Durum } from "./tipler";
import { KALIP, metinAlani, motorMetni } from "./yardimci";

export interface UretAyar { adet: number; kalip: string; stil: string; metinModel: string; gorselModel: string }

export const UretAdimi: React.FC<{
  d: Durum; platform: string; video: string | null; seciliKare: number | null; ayar: UretAyar; degis: (a: Partial<UretAyar>) => void;
  calisiyor: boolean; masterAc: () => void;
}> = ({ d, platform, video, seciliKare, ayar, degis, calisiyor, masterAc }) => {
  const isBaslat = useDepo((s) => s.isBaslat);
  const [s1, setS1] = useState("");
  const [s2, setS2] = useState("");
  const [ek, setEk] = useState("");
  const [prompt, setPrompt] = useState("");
  const motor = motorMetni(d.gorsel_motor);
  const oneriVar = !!d.oneri?.briefler.length;

  const uret = (kaynak: "oneri" | "brief" | "yeni") => isBaslat("kapak", {
    platform, adet: ayar.adet,
    ...(kaynak === "oneri" ? { oneri: true } : {}), ...(kaynak === "yeni" ? { yeni_brief: true } : {}),
    ...(video ? { kapak_video: video } : {}), ...(seciliKare !== null ? { kare: seciliKare } : {}),
    ...(ayar.metinModel ? { model: ayar.metinModel } : {}), ...(ayar.gorselModel ? { gorsel_model: ayar.gorselModel } : {}),
    ...(s1 || s2 ? { metin: metinAlani({ satir1: s1, satir2: s2 }) } : {}), ...(prompt && kaynak !== "oneri" ? { prompt } : {}),
    ...(ayar.kalip ? { kalip: ayar.kalip } : {}), ...(ayar.stil ? { stil: ayar.stil } : {}), ...(ek && KALIP[ayar.kalip]?.ek ? { ek } : {}),
  });

  return (
    <div className="kapak-adim-ic">
      <div className="kapak-uret-satir">
        <AgyModel etiket="Fikir ve brief modeli" deger={ayar.metinModel} degis={(v) => degis({ metinModel: v })}
          ipucu="Prompt'u geliştiren, brief yazan ve eleştiren agy modeli (ör. Gemini 4 Argon)" />
        <AgyModel etiket="Görseli çağıran model" deger={ayar.gorselModel} degis={(v) => degis({ gorselModel: v })}
          ipucu="generate_image aracını çağıran agy modeli; hızlı bir Flash modeli yeter. Görsel modelinin kendisi agy'de sabittir" />
        <span className={`rozet${motor.kapali ? " uyari" : ""}`} role="status" style={{ height: "auto", padding: "3px 6px" }}>{motor.metin}</span>
      </div>
      {motor.kapali && (
        <p className="ipucu" style={{ margin: 0 }}>
          Kota kapalıyken başka platformda üretebilirsin: <button type="button" className="baglanti" onClick={masterAc}>master prompt</button>,
          sonra görseli içe al.
        </p>
      )}
      <div className="kapak-uret-satir">
        <Sayi etiket="Aday sayısı" deger={ayar.adet} degis={(v) => degis({ adet: Math.round(v) })} min={1} max={d.en_cok} />
        <Secim etiket="Kalıp" deger={ayar.kalip} degis={(v) => degis({ kalip: v })} secenekler={[["", "Kalıbı brief seçsin"], ...d.kaliplar.map((k): [string, string] => [k, KALIP[k]?.ad ?? k])]} />
        <Secim etiket="Yazı stili" deger={ayar.stil} degis={(v) => degis({ stil: v })} secenekler={[["", "Stil: stüdyo ya da brief"], ...d.stiller.map((x): [string, string] => [x.ad, x.ad])]} />
      </div>
      <div className="kapak-uret-satir">
        <Dugme tur="birincil" onClick={() => uret("oneri")} disabled={calisiyor || !oneriVar}
          title={oneriVar ? "2. adımdaki öneri kartlarıyla üretir" : "Önce 2. adımda prompt'u geliştir ya da videodan öner"}>
          <Sparkles size={14} /> {calisiyor ? "Çalışıyor…" : "Öneriyle üret"}
        </Dugme>
        <Dugme onClick={() => uret("brief")} disabled={calisiyor} title="Kayıtlı brief'le (yoksa videodan yazdırarak) üretir">Videodan brief'le üret</Dugme>
        <Dugme onClick={() => uret("yeni")} disabled={calisiyor} title="Brief'i agy'ye yeniden yazdırır ve üretir">Brief'i yenile ve üret</Dugme>
        <Dugme onClick={() => isBaslat("kapak", { platform, adet: 0, elestir: true, ...(ayar.metinModel ? { model: ayar.metinModel } : {}) })}
          disabled={calisiyor || !d.adaylar.length} title="Adayları küçük boyutta puanlatır (1-10) ve tek düzeltme notu alır; seçim sende kalır">
          <MessageSquareWarning size={14} /> Eleştir
        </Dugme>
      </div>
      <Bolum ad="Elle yazı ve prompt (isteğe bağlı)" acik={false}>
        <Satir ad="1. satır"><Metin etiket="Birinci satır" deger={s1} degis={setS1} yer="boşsa öneriden ya da brief'ten" /></Satir>
        <Satir ad="2. satır"><Metin etiket="İkinci satır" deger={s2} degis={setS2} yer="vurgulu ikinci satır" /></Satir>
        {!!KALIP[ayar.kalip]?.ek && <Satir ad="Ek söz"><Metin etiket={KALIP[ayar.kalip].ek} deger={ek} degis={setEk} yer={KALIP[ayar.kalip].ek} /></Satir>}
        <Satir ad="Prompt"><Metin etiket="Görsel prompt'u" cok deger={prompt} degis={setPrompt} yer="İngilizce; boşsa brief. Öneriyle üretimde kullanılmaz" /></Satir>
        {ayar.kalip && <p className="ipucu" style={{ margin: 0 }}>{KALIP[ayar.kalip]?.ipucu} {ayar.stil && d.stiller.find((x) => x.ad === ayar.stil)?.aciklama}</p>}
        <p className="ipucu" style={{ margin: 0 }}>Kurallar: {d.h > d.w ? "kapak-instagram" : "kapak-youtube"} skill'i. Yazı her zaman kodla eklenir; Türkçe harf bozulmaz.</p>
      </Bolum>
    </div>
  );
};
