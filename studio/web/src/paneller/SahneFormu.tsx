import { Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import type { Klip } from "../../../remotion/tipler";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Dugme, IkonDugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import { Metin, Satir, Sayi, Secim } from "./alanlar";

type Alan = { a: string; ad: string; tip: "metin" | "sayi" | "secim"; adim?: number; secenek?: [string, string][] };
const ZEMIN: Alan = { a: "bg", ad: "Zemin", tip: "secim", secenek: [["dark", "Koyu"], ["light", "Açık"], ["saydam", "Saydam"]] };
const ALANLAR: Record<string, Alan[]> = {
  hook: [{ a: "title", ad: "Başlık", tip: "metin" }, { a: "size", ad: "Boyut", tip: "sayi" }, { a: "subtitle", ad: "Alt başlık", tip: "metin" }],
  cta: [{ a: "title", ad: "Başlık", tip: "metin" }, { a: "size", ad: "Boyut", tip: "sayi" }, { a: "subtitle", ad: "Alt başlık", tip: "metin" }],
  stat: [ZEMIN, { a: "value", ad: "Sayı", tip: "sayi", adim: 0.1 }, { a: "decimals", ad: "Ondalık", tip: "sayi" }, { a: "prefix", ad: "Ön ek", tip: "metin" }, { a: "unit", ad: "Birim", tip: "metin" }, { a: "label", ad: "Etiket", tip: "metin" }],
  text: [ZEMIN], chips: [ZEMIN], steps: [ZEMIN], timeline: [ZEMIN], shot: [ZEMIN],
};
type Liste = { a: string; ad: string; alanlar: Alan[]; yeni: () => any };
const LISTELER: Record<string, Liste> = {
  text: { a: "lines", ad: "Satırlar", alanlar: [{ a: "t", ad: "Yazı", tip: "metin" }, { a: "size", ad: "Boyut", tip: "sayi" }, { a: "at", ad: "Giriş sn", tip: "sayi", adim: 0.1 }, { a: "accent", ad: "Vurgu", tip: "secim", secenek: [["", "Hayır"], ["1", "Evet"]] }], yeni: () => ({ t: "Yeni satır", size: 96, at: 0.1 }) },
  chips: { a: "items", ad: "Maddeler", alanlar: [{ a: "t", ad: "Yazı", tip: "metin" }, { a: "at", ad: "Giriş sn", tip: "sayi", adim: 0.1 }, { a: "done", ad: "Tik sn", tip: "sayi", adim: 0.1 }], yeni: () => ({ t: "Yeni", at: 0.1, done: 0.6 }) },
  steps: { a: "items", ad: "Adımlar", alanlar: [{ a: "n", ad: "No", tip: "metin" }, { a: "t", ad: "Yazı", tip: "metin" }, { a: "at", ad: "Giriş sn", tip: "sayi", adim: 0.1 }], yeni: () => ({ n: "•", t: "Yeni adım", at: 0.1 }) },
};
// Zaman çizgisi tam iki düğüm ister: SplitReel nodes[0] ve nodes[1] okur.
const SABIT_DUGUM: Alan[] = [{ a: "date", ad: "Tarih", tip: "metin" }, { a: "text", ad: "Yazı", tip: "metin" }, { a: "at", ad: "Giriş sn", tip: "sayi", adim: 0.1 }];

const AlanGir: React.FC<{ alan: Alan; deger: any; degis: (v: any) => void }> = ({ alan, deger, degis }) => {
  if (alan.tip === "sayi") return <Sayi etiket={alan.ad} deger={Number(deger ?? 0)} adim={alan.adim ?? 1} degis={degis} />;
  if (alan.tip === "secim") return <Secim etiket={alan.ad} deger={alan.a === "accent" ? (deger ? "1" : "") : String(deger ?? alan.secenek![0][0])} secenekler={alan.secenek!} degis={(v) => degis(alan.a === "accent" ? !!v : v)} />;
  return <Metin etiket={alan.ad} deger={String(deger ?? "")} degis={degis} />;
};

export const SahneFormu: React.FC<{ c: Klip }> = ({ c }) => {
  const duzenle = useKurgu((d) => d.duzenle);
  const anahtar = useKurgu((d) => d.anahtar);
  const { hata, surum } = useDepo();
  const s = c.sahne ?? {};
  const kind = String(s.kind ?? "");
  const degis = (f: (x: Record<string, any>) => void, birlestir?: string) =>
    duzenle("Sahne", (d) => { const x = d.klipler.find((q) => q.id === c.id); if (x?.sahne) f(x.sahne); }, birlestir ? `${c.id}.${birlestir}` : undefined);

  const [gorseller, setGorseller] = useState<{ yol: string; ad: string }[]>([]);
  const [json, setJson] = useState<string | null>(null);
  const [jsonHata, setJsonHata] = useState("");
  useEffect(() => {
    if (kind !== "shot" || !anahtar) return;
    istek(`/api/dosyalar/${anahtar}/inputs`).then((l: any[]) => setGorseller(l.filter((d) => d.tur === "gorsel"))).catch(hata);
  }, [kind, anahtar, surum]);

  const gorselSec = async (yol: string) => {
    try {
      const r = await istek(`/api/public-bagla/${anahtar}`, { method: "POST", json: { yol: `inputs:${yol}` } });
      degis((x) => { x.img = r.img; x.iw = r.iw; x.ih = r.ih; x.focus = { x: 0, y: 0, w: r.iw }; delete x.focus2; });
    } catch (e) { hata(e); }
  };

  const liste = LISTELER[kind];
  const kayit: any[] = liste ? s[liste.a] ?? [] : [];
  const kickerVar = s.layout === "split";
  // Saydam zemin yalnız tam ekranda render edilir (kurgu.denetle); bölünmüşte seçenek hiç sunulmaz.
  const saydamSuz = (a: Alan): Alan => (a.a === "bg" && s.layout !== "full" ? { ...a, secenek: a.secenek?.filter(([d]) => d !== "saydam") } : a);

  return (
    <div className="sahne-form">
      <Satir ad="Yerleşim"><Secim etiket="Yerleşim" deger={String(s.layout ?? "split")} secenekler={[["split", "Bölünmüş"], ["full", "Tam ekran"]]} degis={(v) => degis((x) => { x.layout = v; if (v !== "full" && x.bg === "saydam") x.bg = "dark"; })} /></Satir>
      {!kind && <p className="ipucu">Tam ekran konuşmacı: bu klip yalnız düzeni belirler, üstünde içerik yok.</p>}
      {(ALANLAR[kind] ?? []).map(saydamSuz).map((a) => <Satir key={a.a} ad={a.ad}><AlanGir alan={a} deger={s[a.a]} degis={(v) => degis((x) => { x[a.a] = v; }, a.tip === "sayi" ? `s.${a.a}` : undefined)} /></Satir>)}
      {kickerVar && kind && <Satir ad="Üst yazı"><Metin etiket="Üst yazı" deger={s.kicker?.[0]?.text ?? ""} degis={(v) => degis((x) => { x.kicker = v ? [{ at: 0, text: v }] : undefined; })} /></Satir>}
      {kickerVar && kind && <Satir ad="Kaynak"><Metin etiket="Kaynak" deger={s.source ?? ""} degis={(v) => degis((x) => { x.source = v || undefined; })} /></Satir>}

      {kind === "shot" && (
        <>
          <Satir ad="Görsel">
            <Secim etiket="Görsel" deger={String(s.img ?? "").replace(/^shot\//, "")} secenekler={[["", gorseller.length ? "Seç" : "Medya'da görsel yok"], ...gorseller.map((g) => [g.yol, g.ad] as [string, string])]} degis={(v) => v && gorselSec(v)} />
          </Satir>
          {(["x", "y", "w"] as const).map((u) => <Satir key={u} ad={`Odak ${u}`}><Sayi etiket={`Odak ${u}`} deger={s.focus?.[u] ?? 0} degis={(v) => degis((x) => { x.focus = { ...x.focus, [u]: v }; }, `f${u}`)} /></Satir>)}
        </>
      )}

      {liste && (
        <div className="sahne-liste">
          <div className="baslik" style={{ padding: "6px 0 2px" }}>{liste.ad}</div>
          {kayit.map((o, i) => (
            <div key={i} className="sahne-oge">
              {liste.alanlar.map((a) => <Satir key={a.a} ad={a.ad}><AlanGir alan={a} deger={o[a.a]} degis={(v) => degis((x) => { x[liste.a][i][a.a] = v; }, a.tip === "sayi" ? `l${i}.${a.a}` : undefined)} /></Satir>)}
              <IkonDugme ad={`${liste.ad} ${i + 1} sil`} disabled={kayit.length <= 1} onClick={() => degis((x) => { x[liste.a].splice(i, 1); })}><Trash2 size={13} /></IkonDugme>
            </div>
          ))}
          <Dugme onClick={() => degis((x) => { x[liste.a] = [...(x[liste.a] ?? []), liste.yeni()]; })}><Plus size={13} /> Ekle</Dugme>
        </div>
      )}
      {kind === "chips" && <Satir ad="Şerit"><Metin etiket="Şerit yazısı" deger={s.banner?.text ?? ""} degis={(v) => degis((x) => { x.banner = { ...x.banner, text: v }; })} /></Satir>}
      {kind === "timeline" && (
        <>
          {[0, 1].map((i) => <div key={i} className="sahne-oge">{SABIT_DUGUM.map((a) => <Satir key={a.a} ad={`${i + 1}. ${a.ad}`}><AlanGir alan={a} deger={s.nodes?.[i]?.[a.a]} degis={(v) => degis((x) => { x.nodes[i][a.a] = v; }, a.tip === "sayi" ? `n${i}` : undefined)} /></Satir>)}</div>)}
          <Satir ad="Çizgi yazısı"><Metin etiket="Çizgi yazısı" deger={s.line?.text ?? ""} degis={(v) => degis((x) => { x.line = { ...x.line, text: v }; })} /></Satir>
        </>
      )}

      <details className="sahne-json" onToggle={(e) => { if ((e.target as HTMLDetailsElement).open) { setJson(JSON.stringify(s, null, 1)); setJsonHata(""); } else setJson(null); }}>
        <summary>Gelişmiş: JSON</summary>
        {json !== null && (
          <>
            <textarea aria-label="Sahne JSON" rows={8} value={json} onChange={(e) => setJson(e.target.value)} spellCheck={false} style={{ width: "100%", fontFamily: "var(--mono)", fontSize: 11 }} />
            {jsonHata && <p role="alert" style={{ color: "var(--hata)", margin: "2px 0" }}>{jsonHata}</p>}
            <Dugme onClick={() => {
              try {
                const v = JSON.parse(json);
                if (typeof v !== "object" || !v || Array.isArray(v)) throw new Error("Nesne olmalı");
                duzenle("Sahne JSON", (d) => { const x = d.klipler.find((q) => q.id === c.id); if (x) x.sahne = v; });
                setJsonHata("");
              } catch (e) { setJsonHata(`Geçersiz JSON: ${(e as Error).message}`); }
            }}>Uygula</Dugme>
          </>
        )}
      </details>
    </div>
  );
};
