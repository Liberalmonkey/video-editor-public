import { ChevronLeft, ChevronRight, Diamond, KeyRound, ScanFace, RotateCcw, Timer, Trash2 } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { HAZIR, cozumle, type Param } from "../../../remotion/hazirEfekt";
import { kfDeger } from "../../../remotion/izdusum";
import { varsayilanKonum } from "../../../remotion/metinOlcu";
import type { KF, Klip, MetinStil } from "../../../remotion/tipler";
import { Bos, Dugme, IkonDugme } from "../ortak";
import { istek } from "../api";
import { useDepo } from "../depo";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { git } from "../zaman/oynatici";
import { Bolum, Metin, Satir, Sayi, Secim } from "./alanlar";
import { SahneFormu } from "./SahneFormu";

const EGRILER: [KF["ease"], string][] = [["dogrusal", "Doğrusal"], ["yumusak", "Yumuşak"], ["giris", "Yavaş başla"], ["cikis", "Yavaş bitir"], ["tut", "Tut"]];
const GECISLER: [string, string][] = [["", "Yok"], ["capraz", "Çapraz"], ["kararma", "Kararma"], ["kaydir", "Kaydırma"], ["zoom", "Zoom"], ["it", "İtme"], ["savur", "Savurma"], ["bulanik", "Bulanık"]];
const FONTLAR: [string, string][] = [["Space Grotesk", "Space Grotesk"], ["Montserrat", "Montserrat"], ["Inter", "Inter"], ["JetBrains Mono", "JetBrains Mono"]];

// Motion şablonu (ADR 0036): yazı ve sayılar burada değişir, "yeniden üret" webm'i yeniler. Sınırları sunucu denetler.
const SablonFormu: React.FC<{ c: Klip }> = ({ c }) => {
  const kayitli = c.sablon?.param ?? {};
  const [param, setParam] = useState<Record<string, string | number>>(kayitli);
  const [is, setIs] = useState(false);
  useEffect(() => setParam(c.sablon?.param ?? {}), [c.id, c.sablon]);
  const ayni = JSON.stringify(param) === JSON.stringify(kayitli);
  const uygula = async () => { setIs(true); try { await useKurgu.getState().sablonGuncelle(c.id, param); } finally { setIs(false); } };
  return (
    <Bolum ad={`Şablon: ${c.sablon!.ad}`}>
      {Object.entries(param).map(([ad, v]) => (
        <Satir key={ad} ad={ad}>
          <input aria-label={`Şablon ${ad}`} type={typeof v === "number" ? "number" : "text"} step="any" value={v}
            onChange={(e) => setParam({ ...param, [ad]: typeof v === "number" ? Number(e.target.value) : e.target.value })} />
        </Satir>
      ))}
      {!Object.keys(param).length && <p className="ipucu" style={{ margin: 0 }}>Bu şablonun değişen alanı yok.</p>}
      <Dugme tur="birincil" disabled={is || ayni} onClick={uygula} title="Grafiği yeni değerlerle yeniden üretir">{is ? "Üretiliyor…" : "Şablonu yeniden üret"}</Dugme>
    </Bolum>
  );
};

const AlanSatiri: React.FC<{ c: Klip; alan: K.KfAlan; ad: string; varsayilan: number; adim: number; carpan?: number; birim?: string; min?: number; max?: number }> = ({ c, alan, ad, varsayilan, adim, carpan, birim, min, max }) => {
  const duzenle = useKurgu((d) => d.duzenle);
  const zaman = useKurgu((d) => d.zaman);
  const t = Math.max(0, Math.min(c.sure, zaman - c.bas));
  const l = c.donus[alan];
  const anim = c.donus.anim.includes(alan) || l.length > 1;
  const v = kfDeger(l, t, varsayilan);
  const yarim = 1 / (2 * (useKurgu.getState().kurgu?.sekans.fps ?? 30));
  const burada = anim ? l.find((f) => Math.abs(f.t - t) < yarim) : undefined;
  const onceki = [...l].reverse().find((f) => f.t < t - yarim);
  const sonraki = l.find((f) => f.t > t + yarim);
  const cizgi = useRef<HTMLDivElement>(null);
  const surukleTemizle = useRef<(() => void) | null>(null);
  // WHY: sürükleme sürerken klip/proje değişir veya bileşen unmount olursa window dinleyicileri sızmasın.
  useEffect(() => () => { surukleTemizle.current?.(); }, []);
  const yaz = (x: number) => duzenle(`${ad}`, (d) => K.degerYaz(d, c.id, alan, t, x), `${c.id}.${alan}`);

  const surukle = (f: KF, e: React.PointerEvent) => {
    e.preventDefault();
    surukleTemizle.current?.();
    const r = cizgi.current?.getBoundingClientRect();
    if (!r || !(r.width > 0)) return;
    let son = f.t;
    const hareket = (m: PointerEvent) => {
      const yeni = Math.max(0, Math.min(1, (m.clientX - r.left) / r.width)) * c.sure;
      const fps = useKurgu.getState().kurgu?.sekans.fps ?? 30;
      const kare = K.kareYuvarla(yeni, fps);
      duzenle("Keyframe taşı", (d) => K.kfTasi(d, c.id, alan, son, kare), `${c.id}.${alan}.kf`);
      son = kare;
    };
    const birak = () => {
      window.removeEventListener("pointermove", hareket);
      window.removeEventListener("pointerup", birak);
      window.removeEventListener("pointercancel", birak);
      if (surukleTemizle.current === birak) surukleTemizle.current = null;
    };
    surukleTemizle.current = birak;
    window.addEventListener("pointermove", hareket);
    window.addEventListener("pointerup", birak);
    window.addEventListener("pointercancel", birak);
  };

  return (
    <div className="ef-kf">
      <div className="ef-satir">
        <IkonDugme ad={`${ad} animasyonu ${anim ? "kapat" : "aç"}`} acik={anim} aria-pressed={anim} className="kucuk-d" onClick={() => duzenle(`${ad} animasyon`, (d) => K.animDegistir(d, c.id, alan, t, varsayilan))}><Timer size={13} /></IkonDugme>
        <span className="ef-ad">{ad}</span>
        <span className="ef-deger">
          <Sayi etiket={ad} deger={v} degis={yaz} adim={adim} carpan={carpan} birim={birim} min={min} max={max} />
          {anim && <>
            <IkonDugme ad="Önceki keyframe" className="kucuk-d" disabled={!onceki} onClick={() => onceki && git(c.bas + onceki.t)}><ChevronLeft size={13} /></IkonDugme>
            <IkonDugme ad={burada ? "Keyframe sil" : "Keyframe ekle"} acik={!!burada} className="kucuk-d" onClick={() => duzenle("Keyframe", (d) => K.kfDegistir(d, c.id, alan, t, varsayilan))}><Diamond size={12} fill={burada ? "currentColor" : "none"} /></IkonDugme>
            <IkonDugme ad="Sonraki keyframe" className="kucuk-d" disabled={!sonraki} onClick={() => sonraki && git(c.bas + sonraki.t)}><ChevronRight size={13} /></IkonDugme>
          </>}
        </span>
      </div>
      {anim && (
        <div className="ef-serit">
          <div ref={cizgi} className="ef-cizgi">
            <i className="ef-kafa" style={{ left: `${(t / c.sure) * 100}%` }} />
            {l.map((f) => (
              <button key={f.t} type="button" className={`ef-elmas ${burada === f ? "secili" : ""}`} style={{ left: `${(f.t / c.sure) * 100}%` }} aria-label={`Keyframe ${f.t.toFixed(2)} sn`}
                onClick={() => git(c.bas + f.t)} onPointerDown={(e) => surukle(f, e)} />
            ))}
          </div>
          {burada && <Secim etiket={`${ad} eğrisi`} deger={burada.ease} degis={(e) => duzenle("Eğri", (d) => K.kfEgri(d, c.id, alan, t, e as KF["ease"]))} secenekler={EGRILER} />}
        </div>
      )}
    </div>
  );
};

// Kazanç keyframe'lenebilir: kapalıyken tek değer, açıkken oynatma kafasında keyframe (render ve önizleme aynı eğri).
const SesKazanc: React.FC<{ c: Klip }> = ({ c }) => {
  const duzenle = useKurgu((d) => d.duzenle);
  const zaman = useKurgu((d) => d.zaman);
  const t = Math.max(0, Math.min(c.sure, zaman - c.bas));
  const anim = !!c.ses.kf?.length;
  const yarim = 1 / (2 * (useKurgu.getState().kurgu?.sekans.fps ?? 30));
  const burada = anim && c.ses.kf!.some((f) => Math.abs(f.t - t) < yarim);
  return (
    <div className="ef-satir">
      <IkonDugme ad={`Kazanç animasyonu ${anim ? "kapat" : "aç"}`} acik={anim} aria-pressed={anim} className="kucuk-d" onClick={() => duzenle("Kazanç animasyon", (d) => K.sesKfAnim(d, c.id, t))}><Timer size={13} /></IkonDugme>
      <span className="ef-ad">Kazanç</span>
      <span className="ef-deger">
        <Sayi etiket="Kazanç" deger={K.kazancAni(c, t)} adim={0.5} birim="dB" min={-60} max={24} degis={(v) => duzenle("Kazanç", (d) => K.kazancYaz(d, c.id, v, anim ? t : undefined), `${c.id}.gain`)} />
        {anim && <IkonDugme ad={burada ? "Kazanç keyframe sil" : "Kazanç keyframe ekle"} acik={burada} className="kucuk-d" onClick={() => duzenle("Kazanç keyframe", (d) => K.sesKfDegistir(d, c.id, t, yarim))}><Diamond size={12} fill={burada ? "currentColor" : "none"} /></IkonDugme>}
      </span>
    </div>
  );
};

// Yüz takibiyle kareyi doldurur: sunucu hesaplar, sonuç geri alınabilir düzenleme olarak yazılır.
export const reframeYap = async (id: string) => {
  const { anahtar, kaydet, duzenle } = useKurgu.getState();
  const { bildir, hata } = useDepo.getState();
  if (!anahtar) return;
  bildir("Yüz aranıyor");
  try {
    await kaydet();
    // WHY: kayıt veya reframe isteği sürerken başka projeye geçilirse eski sonuç yeni kurguya yazılmasın.
    if (useKurgu.getState().anahtar !== anahtar) return;
    const r = await istek(`/api/reframe/${anahtar}`, { method: "POST", json: { klip: id } });
    if (useKurgu.getState().anahtar !== anahtar) return;
    duzenle("Otomatik reframe", (d) => {
      const x = d.klipler.find((q) => q.id === id);
      if (!x) return;
      x.donus.x = r.x; x.donus.olcek = r.olcek;
      x.donus.anim = [...new Set([...x.donus.anim.filter((a) => a !== "x" && a !== "olcek"), ...r.anim])] as any;
    });
    bildir(r.yuz_orani > 0 ? `Reframe: karelerin %${Math.round(r.yuz_orani * 100)}'inde yüz bulundu` : "Yüz bulunamadı; kare ortalandı ve dolduruldu", r.yuz_orani === 0);
  } catch (e) {
    if (useKurgu.getState().anahtar === anahtar) hata(e);
  }
};

// WHY: bkz. wiki/decisions/0033-hazir-efektler.md. Hazır efekt kayıt olarak durur; alanlar hazirEfekt.json'dan, sınırlar onun min/max'ı.
const HAZIR_ADLARI: [string, string][] = [["", "Ekle..."], ...Object.keys(HAZIR).map((a): [string, string] => [a, a.replace("_", " ")])];
const PARAM_ADI: Record<string, string> = { sure: "Süre", s: "Ölçek", x: "Odak X", y: "Odak Y", geri_don: "Geri dön", tut: "Tutma", yon: "Yön", mesafe: "Mesafe", guc: "Güç", adet: "Adet", aci: "Açı" };
const YONLER: Record<string, string> = { sol: "Sol", sag: "Sağ", yukari: "Yukarı", asagi: "Aşağı" };
const adimi = (a: string, pr: Param) => (a === "sure" || a === "tut" ? 0.05 : (pr.max ?? 1) - (pr.min ?? 0) > 10 ? 1 : 0.01);

const HazirEfektler: React.FC<{ c: Klip }> = ({ c }) => {
  const duzenle = useKurgu((d) => d.duzenle);
  const zaman = useKurgu((d) => d.zaman);
  const l = c.hazir ?? [];
  return (
    <Bolum ad="Hazır efekt" acik={l.length > 0}>
      <Satir ad="Oynatma kafasına"><Secim etiket="Hazır efekt ekle" deger="" secenekler={HAZIR_ADLARI} degis={(ad) => ad && duzenle("Hazır efekt ekle", (d) => K.hazirEkle(d, c.id, ad, zaman - c.bas))} /></Satir>
      {l.map((h, i) => {
        const tn = HAZIR[h.ad];
        const yaz = (alan: string, v: number | string | boolean | undefined) => duzenle("Hazır efekt", (d) => K.hazirYaz(d, c.id, i, alan, v), `${c.id}.hz${i}${alan}`);
        return (
          <div key={i} className="ef-kf">
            <div className="ef-satir">
              <span className="ef-ad" title={tn?.amac} style={{ fontWeight: 600 }}>{h.ad.replace("_", " ")}</span>
              <span className="ef-deger">
                {tn && <IkonDugme ad="Keyframe'e çevir" className="kucuk-d" onClick={() => duzenle("Keyframe'e çevir", (d) => K.hazirPisir(d, c.id, i))}><KeyRound size={13} /></IkonDugme>}
                <IkonDugme ad="Hazır efekti sil" className="kucuk-d" onClick={() => duzenle("Hazır efekt sil", (d) => K.hazirSil(d, c.id, i))}><Trash2 size={13} /></IkonDugme>
              </span>
            </div>
            {!tn ? <p className="ipucu" style={{ margin: 0 }}>Bilinmeyen efekt, render'da reddedilir.</p> : <>
              <Satir ad="Başlangıç"><Sayi etiket="Başlangıç" deger={cozumle(c, h, 0).t} adim={0.05} birim="sn" min={0} max={c.sure} degis={(v) => yaz("t", v)} /></Satir>
              {Object.entries(tn.param).map(([a, pr]) => (
                <Satir key={a} ad={PARAM_ADI[a] ?? a}>
                  {typeof pr.vars === "boolean"
                    ? <input type="checkbox" aria-label={PARAM_ADI[a] ?? a} checked={h[a] ?? pr.vars} style={{ minHeight: 0 }} onChange={(e) => yaz(a, e.target.checked)} />
                    : pr.secenek
                      ? <Secim etiket={PARAM_ADI[a] ?? a} deger={h[a] ?? ""} secenekler={[["", "Oto"], ...pr.secenek.map((y): [string, string] => [y, YONLER[y] ?? y])]} degis={(v) => yaz(a, v || undefined)} />
                      : <Sayi etiket={PARAM_ADI[a] ?? a} deger={h[a] ?? pr.vars} adim={adimi(a, pr)} birim={a === "sure" || a === "tut" ? "sn" : undefined}
                          min={a === "sure" && pr.vars === 0 ? 0 : pr.min} max={pr.max} degis={(v) => yaz(a, v)} />}
                </Satir>
              ))}
              {tn.ses && <Satir ad="Ses olayı"><input type="checkbox" aria-label="Ses olayı" title="Render'da efektin rol sesi eklenir" checked={h.ses !== false} style={{ minHeight: 0 }} onChange={(e) => yaz("ses", e.target.checked ? undefined : false)} /></Satir>}
              <p className="ipucu" style={{ margin: 0 }}>{tn.ne_zaman}</p>
            </>}
          </div>
        );
      })}
    </Bolum>
  );
};

const TURLER: [string, string][] = [["", "Düz metin"], ["anahtar", "Anahtar kelime"], ["altbant", "Alt bant"], ["etiket", "Etiket"], ["cagri", "Çağrı oku"],
  ["daktilo", "Daktilo"], ["sayac", "Sayaç"], ["ilerleme", "İlerleme"], ["bolum", "Bölüm kartı"], ["vurgu", "Vurgu çizimi"]];
const BICIMLER: [string, string][] = [["kutu", "Kutu"], ["daire", "Daire"], ["alt_cizgi", "Alt çizgi"]];
type Degis = (ad: string, f: (x: Klip) => void, birlestir?: string) => void;

// Motion metin (ADR 0031): tür ve türün gerektirdiği birkaç alan. Oranlar kareye (görselde görsele) göre % gösterilir.
const MotionAlanlari: React.FC<{ c: Klip; degis: Degis; turler: [string, string][]; yatay: boolean }> = ({ c, degis, turler, yatay }) => {
  const m: MetinStil = c.metin_stil ?? {};
  const yaz = (ad: string, f: (s: MetinStil) => void, b?: string) => degis(ad, (x) => { const s = { ...(x.metin_stil ?? {}) }; f(s); x.metin_stil = s; }, b);
  const vk = varsayilanKonum(m.tip ?? "", yatay);
  const oran = (ad: string, n: "konum" | "hedef" | "kutu", a: string, vars: number) => (
    <Satir key={n + a} ad={ad}><Sayi etiket={ad} deger={(m[n] as Record<string, number> | undefined)?.[a] ?? vars} adim={1} carpan={100} birim="%" min={0} max={100} degis={(v) => yaz(ad, (s) => { (s as Record<string, any>)[n] = { ...s[n], [a]: v }; }, `${n}${a}`)} /></Satir>
  );
  const sayi = (ad: string, a: string, vars: number, adim = 1) => <Satir key={a} ad={ad}><Sayi etiket={ad} deger={Number(m[a] ?? vars)} adim={adim} degis={(v) => yaz(ad, (s) => { s[a] = v; }, a)} /></Satir>;
  const yazi = (ad: string, a: string) => <Satir key={a} ad={ad}><Metin etiket={ad} deger={String(m[a] ?? "")} degis={(v) => yaz(ad, (s) => { s[a] = v || undefined; })} /></Satir>;
  return (
    <>
      <Satir ad="Tür"><Secim etiket="Metin türü" deger={m.tip ?? ""} secenekler={turler} degis={(v) => yaz("Metin türü", (s) => { s.tip = (v || undefined) as MetinStil["tip"]; })} /></Satir>
      {m.tip && m.tip !== "vurgu" && <>{oran("Konum X", "konum", "x", vk.x)}{oran("Konum Y", "konum", "y", vk.y)}</>}
      {m.tip && <Satir ad="Vurgu rengi"><input type="color" aria-label="Vurgu rengi" value={m.vurgu ?? "#ff7a00"} onChange={(e) => yaz("Vurgu rengi", (s) => { s.vurgu = e.target.value; }, "mv")} /></Satir>}
      {m.tip === "cagri" && <>{oran("Hedef X", "hedef", "x", 0.5)}{oran("Hedef Y", "hedef", "y", 0.4)}</>}
      {m.tip === "sayac" && <>{sayi("Sayı", "deger", 0, 0.1)}{sayi("Ondalık", "ondalik", 0)}{yazi("Ön ek", "onek")}{yazi("Son ek", "sonek")}</>}
      {m.tip === "ilerleme" && <>{sayi("Adım", "adim", 1)}{sayi("Toplam", "toplam", 3)}</>}
      {m.tip === "bolum" && yazi("Numara", "numara")}
      {m.tip === "vurgu" && <>
        <Satir ad="Biçim"><Secim etiket="Vurgu biçimi" deger={m.bicim ?? "kutu"} secenekler={BICIMLER} degis={(v) => yaz("Vurgu biçimi", (s) => { s.bicim = v as MetinStil["bicim"]; })} /></Satir>
        {oran("Kutu X", "kutu", "x", 0.3)}{oran("Kutu Y", "kutu", "y", 0.4)}{oran("Kutu gen.", "kutu", "w", 0.4)}{oran("Kutu yük.", "kutu", "h", 0.1)}
      </>}
      {m.tip && m.tip !== "vurgu" && <p className="ipucu" style={{ margin: "2px 0" }}>Montserrat. *yıldızlı* kısım vurgu renginde. Altyazı bandına ve üst kenara inmez.</p>}
    </>
  );
};

export const EfektPaneli: React.FC = () => {
  // Bağlı grupta tıklanan klip düzenlenir: yoksa A/V çiftinin kazancına ulaşılamazdı.
  const c = useKurgu((d) => {
    const id = d.secim.length === 1 ? d.secim[0] : d.kurgu && d.odakKlip && d.secim.includes(d.odakKlip) && K.baglilar(d.kurgu, [d.odakKlip]).length === d.secim.length ? d.odakKlip : null;
    return id ? d.kurgu?.klipler.find((x) => x.id === id) : undefined;
  });
  const adet = useKurgu((d) => d.secim.length);
  const sekansYatay = useKurgu((d) => !!d.kurgu && d.kurgu.sekans.w > d.kurgu.sekans.h); // reframe düğmesi sekans değişince yenilensin
  const duzenle = useKurgu((d) => d.duzenle);
  if (!c) return <div className="panel"><Bos baslik={adet > 1 ? `${adet} klip seçili` : "Klip seçilmedi"} metin={adet > 1 ? "Klibi düzenlemek için tek klip seç." : "Timeline'da bir klibe tıkla, ayarları burada görünür."} /></div>;

  const degis = (ad: string, f: (x: Klip) => void, birlestir?: string) =>
    duzenle(ad, (d) => { const x = d.klipler.find((q) => q.id === c.id); if (x) f(x); }, birlestir ? `${c.id}.${birlestir}` : undefined);
  const gorsel = c.tur !== "ses";
  const hareketli = gorsel && c.tur !== "sahne";
  const videolu = c.tur === "video" || c.tur === "motion" || c.tur === "ses";
  const renk = c.efekt;

  return (
    <div className="panel">
      <div className="icerik ef">
        <div className="ef-baslik"><span className="rozet">{c.tur}</span><span className="ad" title={c.id}>{c.iz} · {c.sure.toFixed(2)} sn</span></div>

        {c.tur === "sahne" && <Bolum ad="Sahne"><SahneFormu c={c} /></Bolum>}
        {c.tur === "metin" && (
          <Bolum ad="Metin">
            <Metin cok etiket="Metin" deger={c.metin ?? ""} degis={(v) => degis("Metin", (x) => { x.metin = v; })} />
            <Satir ad="Boyut"><Sayi etiket="Boyut" deger={c.metin_stil?.boyut ?? 96} min={12} max={400} degis={(v) => degis("Metin boyutu", (x) => { x.metin_stil = { ...x.metin_stil, boyut: v }; }, "mb")} /></Satir>
            <Satir ad="Renk"><input type="color" aria-label="Metin rengi" value={c.metin_stil?.renk ?? "#ffffff"} onChange={(e) => degis("Metin rengi", (x) => { x.metin_stil = { ...x.metin_stil, renk: e.target.value }; }, "mr")} /></Satir>
            {!c.metin_stil?.tip && <Satir ad="Font"><Secim etiket="Metin fontu" deger={c.metin_stil?.font ?? "Space Grotesk"} secenekler={FONTLAR} degis={(v) => degis("Metin fontu", (x) => { x.metin_stil = { ...x.metin_stil, font: v }; })} /></Satir>}
            <MotionAlanlari c={c} degis={degis} turler={TURLER} yatay={sekansYatay} />
          </Bolum>
        )}
        {c.tur === "gorsel" && (
          <Bolum ad="Vurgu" acik={c.metin_stil?.tip === "vurgu"}>
            <MotionAlanlari c={c} degis={degis} turler={[["", "Yok"], ["vurgu", "Vurgu çizimi"]]} yatay={sekansYatay} />
          </Bolum>
        )}

        {c.sablon && <SablonFormu c={c} />}

        {hareketli && (
          <Bolum ad="Hareket">
            <AlanSatiri c={c} alan="x" ad="Konum X" varsayilan={0} adim={1} birim="px" />
            <AlanSatiri c={c} alan="y" ad="Konum Y" varsayilan={0} adim={1} birim="px" />
            <AlanSatiri c={c} alan="olcek" ad="Ölçek" varsayilan={1} adim={0.1} carpan={100} birim="%" min={0} max={1000} />
            <AlanSatiri c={c} alan="opaklik" ad="Opaklık" varsayilan={1} adim={1} carpan={100} birim="%" min={0} max={100} />
            {c.tur === "video" && !c.konusmaci && c.kaynak && (() => {
              const kay = useKurgu.getState().kurgu?.kaynaklar[c.kaynak!];
              return kay?.w && kay.h && (kay.w > kay.h) !== sekansYatay;
            })() && <Dugme onClick={() => reframeYap(c.id)} title="Klip sekansla farklı yönde: yüzü takip ederek kareyi doldurur"><ScanFace size={13} /> Yüzü takip et, kareyi doldur</Dugme>}
            {c.tur === "video" && <Satir ad="Konuşmacı düzeni"><input type="checkbox" aria-label="Konuşmacı düzeni" title="Bölünmüş sahnede bu klip yer açar. Kapalıysa sahneyi örter." checked={c.konusmaci} style={{ minHeight: 0 }} onChange={(e) => degis("Konuşmacı düzeni", (x) => { x.konusmaci = e.target.checked; })} /></Satir>}
            {c.konusmaci && <Satir ad="Taban zoom"><Sayi etiket="Taban zoom" deger={c.zoom} adim={0.01} min={1} max={3} degis={(v) => degis("Taban zoom", (x) => { x.zoom = v; }, "zoom")} /></Satir>}
          </Bolum>
        )}

        {hareketli && <HazirEfektler c={c} />}

        {/* WHY: ses izi render'da ffmpeg miksine gider, hız uygulanmaz; önizleme yalan söylemesin. */}
        {(c.tur === "video" || c.tur === "motion") && (
          <Bolum ad="Hız">
            {c.ses_kapali && <p className="ipucu" style={{ margin: "0 0 4px" }}>Ses ayrıyken hız değişmez: render'da ayrık sese hız uygulanmaz. Önce sesi birleştir ya da bağı çöz (Ctrl+L).</p>}
            <Satir ad="Hız"><Sayi etiket="Hız" deger={c.hiz} adim={1} carpan={100} birim="%" min={10} max={800} degis={(v) => duzenle("Hız", (d) => K.hizAyarla(d, c.id, v), `${c.id}.hiz`)} /></Satir>
          </Bolum>
        )}

        {hareketli && (
          <Bolum ad="Renk ve görüntü" acik={renk.parlaklik !== 1 || renk.kontrast !== 1 || renk.doygunluk !== 1 || renk.bulanik > 0 || !!renk.kirp}>
            <Satir ad="Parlaklık"><Sayi etiket="Parlaklık" deger={renk.parlaklik} adim={1} carpan={100} birim="%" min={0} max={300} degis={(v) => degis("Parlaklık", (x) => { x.efekt.parlaklik = v; }, "par")} /></Satir>
            <Satir ad="Kontrast"><Sayi etiket="Kontrast" deger={renk.kontrast} adim={1} carpan={100} birim="%" min={0} max={300} degis={(v) => degis("Kontrast", (x) => { x.efekt.kontrast = v; }, "kon")} /></Satir>
            <Satir ad="Doygunluk"><Sayi etiket="Doygunluk" deger={renk.doygunluk} adim={1} carpan={100} birim="%" min={0} max={300} degis={(v) => degis("Doygunluk", (x) => { x.efekt.doygunluk = v; }, "doy")} /></Satir>
            <Satir ad="Bulanıklık"><Sayi etiket="Bulanıklık" deger={renk.bulanik} adim={1} birim="px" min={0} max={200} degis={(v) => degis("Bulanıklık", (x) => { x.efekt.bulanik = v; }, "bul")} /></Satir>
            {(["ust", "alt", "sol", "sag"] as const).map((u) => (
              <Satir key={u} ad={`Kırp ${{ ust: "üst", alt: "alt", sol: "sol", sag: "sağ" }[u]}`}><Sayi etiket={`Kırp ${u}`} deger={renk.kirp?.[u] ?? 0} adim={1} carpan={100} birim="%" min={0} max={100} degis={(v) => degis("Kırp", (x) => { const r = { ...(x.efekt.kirp ?? {}), [u]: v }; x.efekt.kirp = Object.values(r).some(Boolean) ? r : null; }, `kirp${u}`)} /></Satir>
            ))}
            <Dugme onClick={() => degis("Renk sıfırla", (x) => { x.efekt = { parlaklik: 1, kontrast: 1, doygunluk: 1, bulanik: 0, kirp: null }; })}><RotateCcw size={13} /> Sıfırla</Dugme>
          </Bolum>
        )}

        {videolu && (
          <Bolum ad="Ses">
            <p className="ipucu" style={{ margin: "0 0 4px" }}>{c.ses_kapali ? "Bu klibin sesi ayrı klipte; kazanç orada ayarlanır. " : ""}Ses araçları: Ses paneli</p>
            <SesKazanc c={c} />
            <Satir ad="Fade in"><Sayi etiket="Fade in" deger={c.ses.fade_in} adim={0.05} birim="sn" min={0} max={30} degis={(v) => degis("Fade in", (x) => { x.ses.fade_in = v; }, "fi")} /></Satir>
            <Satir ad="Fade out"><Sayi etiket="Fade out" deger={c.ses.fade_out} adim={0.05} birim="sn" min={0} max={30} degis={(v) => degis("Fade out", (x) => { x.ses.fade_out = v; }, "fo")} /></Satir>
            {c.olay?.muzik && <Satir ad="Konuşmada kıs"><input type="checkbox" aria-label="Konuşmada kıs" checked={c.ses.duck} style={{ minHeight: 0 }} onChange={(e) => degis("Ducking", (x) => { x.ses.duck = e.target.checked; })} /></Satir>}
          </Bolum>
        )}

        {hareketli && (
          <Bolum ad="Geçişler" acik={!!c.gecis_giris || !!c.gecis_cikis}>
            <Satir ad="Giriş"><Secim etiket="Giriş geçişi" deger={c.gecis_giris?.tur ?? ""} secenekler={GECISLER} degis={(v) => degis("Geçiş", (x) => { x.gecis_giris = v ? { tur: v as any, sure: x.gecis_giris?.sure ?? 0.3 } : null; })} /></Satir>
            {c.gecis_giris && <Satir ad="Süre"><Sayi etiket="Giriş geçişi süresi" deger={c.gecis_giris.sure} adim={0.05} birim="sn" min={0.04} max={5} degis={(v) => degis("Geçiş süresi", (x) => { if (x.gecis_giris) x.gecis_giris.sure = v; }, "gg")} /></Satir>}
            {c.gecis_giris && ["it", "savur"].includes(c.gecis_giris.tur) && <Satir ad="Yön"><Secim etiket="Giriş geçişi yönü" deger={c.gecis_giris.yon ?? "sol"} secenekler={[["sol", "Sola"], ["sag", "Sağa"], ["yukari", "Yukarı"], ["asagi", "Aşağı"]]} degis={(v) => degis("Geçiş yönü", (x) => { if (x.gecis_giris) x.gecis_giris.yon = v as any; })} /></Satir>}
            <Satir ad="Çıkış"><Secim etiket="Çıkış geçişi" deger={c.gecis_cikis ? "kararma" : ""} secenekler={[["", "Yok"], ["kararma", "Kararma"]]} degis={(v) => degis("Geçiş", (x) => { x.gecis_cikis = v ? { tur: "kararma", sure: x.gecis_cikis?.sure ?? 0.3 } : null; })} /></Satir>
            {c.gecis_cikis && <Satir ad="Süre"><Sayi etiket="Çıkış geçişi süresi" deger={c.gecis_cikis.sure} adim={0.05} birim="sn" min={0.04} max={5} degis={(v) => degis("Geçiş süresi", (x) => { if (x.gecis_cikis) x.gecis_cikis.sure = v; }, "gc")} /></Satir>}
            <p className="ipucu" style={{ margin: "4px 0 0" }}>Çapraz ve kaydırma bir önceki bitişik klibin kuyruğunu kullanır.</p>
          </Bolum>
        )}
      </div>
    </div>
  );
};
