import { CircleStop, Settings2, Undo2, Wand2 } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { istek, sor } from "../../api";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import { useKurgu } from "../../zaman/depo";
import { EkipAyarlari } from "./EkipAyarlari";
import { EkipIlerleme } from "./EkipIlerleme";
import { MotorSatiri } from "./MotorSatiri";
import { SuruSecici } from "./SuruSecici";
import { gerekenMotorlar, sn, type EkipAyar } from "./seviye";

// Edit sekmesi: istek, birkaç ayar, çalışma biçimi (tek ajan ya da swarm), tek birincil düğme; çalışırken ilerleme,
// bitince son edit özeti. WHY: bkz. wiki/decisions/0028-ai-edit.md (tek ajan), 0059-swarm-edit.md (swarm).

interface AiOzet { once_rev: number; rev: number; klip: [number, number]; sure: [number, number]; aralik: [number, number] | null; rapor: string[]; geri_alinabilir: boolean }

// ı ve i tek harf sayılır: Türkçe küçültme "AI"yı "aı" yapar, stil adı "ai-reels" ile eşleşmezdi.
const sade = (s: string) => ` ${s.toLocaleLowerCase("tr").replace(/ı/g, "i").replace(/[^\p{L}\p{N}]+/gu, " ").trim()} `;
// İstekte adı geçen stil: "ai-reels stiliyle editle" ve "ai reels" ikisi de eşleşir; en uzun ad kazanır.
export const istektekiStil = (istem: string, stiller: string[]) =>
  [...stiller].sort((a, b) => b.length - a.length).find((ad) => sade(istem).includes(sade(ad))) ?? null;

const yerel = (k: string, v?: string) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch { /* depolama kapalı */ } return null; };

export const EditSekmesi: React.FC = () => {
  const { ajanDurum, ajan, isler, gunlukler, aktif, isBaslat, bildir, hata, kurguAl } = useDepo();
  const [istem, setIstem] = useState("");
  const [stiller, setStiller] = useState<string[]>([]);
  const [stil, setStil] = useState(""); // boş: projenin seçili stili
  const [motion, setMotion] = useState("yogun");
  const [final, setFinal] = useState(false);
  const [kapsam, setKapsam] = useState<"hepsi" | "secim">("hepsi");
  const [ekipModu, setEkipModu] = useState(() => yerel("ekipModu") === "1");
  useEffect(() => { yerel("ekipModu", ekipModu ? "1" : "0"); }, [ekipModu]);
  const [ozet, setOzet] = useState<AiOzet | null>(null);
  const [ayar, setAyar] = useState<EkipAyar | null>(null);
  const [onayarlar, setOnayarlar] = useState<Record<string, EkipAyar>>({});
  const [varsayilan, setVarsayilan] = useState<string | null>(null);
  const gunlukKutu = useRef<HTMLDivElement>(null);

  const calisan = isler.find((x) => x.komut === "ai-edit" && (x.durum === "calisiyor" || x.durum === "sirada"));
  const sonEdit = isler.filter((x) => x.komut === "ai-edit").reduce<(typeof isler)[number] | undefined>((a, x) => (!a || x.id > a.id ? x : a), undefined);
  const bitenEdit = isler.filter((x) => x.komut === "ai-edit" && x.bitis).length;
  const motor = ajanDurum?.[ajan.motor];
  const yol = aktif ? `/api/ekip/${aktif.studyo}/${aktif.ad}` : null;

  // Kapsam: seçili kliplerin kapladığı süre, seçim yoksa giriş-çıkış işaretleri.
  const klipler = useKurgu((d) => d.kurgu?.klipler);
  const secim = useKurgu((d) => d.secim);
  const giris = useKurgu((d) => d.giris), cikis = useKurgu((d) => d.cikis);
  const aralik = useMemo((): [number, number] | null => {
    const sec = (klipler ?? []).filter((c) => secim.includes(c.id));
    if (sec.length) return [Math.min(...sec.map((c) => c.bas)), Math.max(...sec.map((c) => c.bas + c.sure))];
    return giris !== null && cikis !== null && cikis > giris ? [giris, cikis] : null;
  }, [klipler, secim, giris, cikis]);
  useEffect(() => { if (!aralik) setKapsam("hepsi"); }, [!aralik]);

  useEffect(() => {
    setStiller([]); setStil("");
    if (!aktif) return;
    istek(`/api/stil/${aktif.studyo}?${sor({ proje: aktif.ad })}`)
      .then((v) => setStiller(v.stiller.map((x: { ad: string }) => x.ad))).catch(hata);
  }, [aktif?.studyo, aktif?.ad]);
  useEffect(() => {
    if (!aktif) { setOzet(null); return; }
    istek(`/api/kurgu/${aktif.studyo}/${aktif.ad}/ai-ozet`).then(setOzet).catch(() => setOzet(null));
  }, [aktif?.studyo, aktif?.ad, bitenEdit]);
  useEffect(() => { const ad = istektekiStil(istem, stiller); if (ad) setStil(ad); }, [istem, stiller]);
  // Ekip ayarı: proje ezmesi, yoksa varsayılan ön ayar.
  useEffect(() => {
    (async () => {
      try {
        const g = await istek("/api/ekip");
        setOnayarlar(g.global.onayarlar ?? {}); setVarsayilan(g.global.varsayilan ?? null);
        const p = yol ? await istek(yol) : null;
        setAyar(p?.etkin ?? g.global.onayarlar?.[g.global.varsayilan] ?? g.varsayilan_ayar);
      } catch (e) { hata(e); }
    })();
  }, [yol]);
  const tekGunluk = !ekipModu && sonEdit ? gunlukler[sonEdit.id] ?? [] : [];
  useEffect(() => { const k = gunlukKutu.current; if (k) k.scrollTop = k.scrollHeight; }, [tekGunluk.length]);

  // Tarama bitmeden motor "kurulu değil" sayılmaz (yanlış alarm); düğme tarama bitince açılır.
  const eksik = useMemo(() => (ayar && ajanDurum ? gerekenMotorlar(ayar).filter((m) => !ajanDurum[m]?.kurulu) : []), [ayar, ajanDurum]);
  const hazir = ekipModu ? !!ayar && !!ajanDurum && !eksik.length : !!motor?.kurulu;
  const neden = !aktif ? "Önce bir proje aç" : ekipModu ? (!ajanDurum ? "Motorlar taranıyor…" : eksik.length ? `Kurulu olmayan motor: ${eksik.join(", ")}` : "")
    : motor?.kurulu ? "" : `${motor?.ad ?? ajan.motor} kurulu değil`;

  const editle = async () => {
    if (!aktif || !hazir) return;
    const ortak = { notu: istem.trim() || undefined, stil: stil || undefined, motion, final };
    if (ekipModu && ayar) await isBaslat("ai-edit", { ...ortak, ekip: true, ekip_ayar: { ...ayar, motion, stil: stil || null } });
    else await isBaslat("ai-edit", { ...ortak, motor: ajan.motor, model: ajan.model, ...(kapsam === "secim" && aralik ? { aralik } : {}) });
    setIstem("");
  };
  const geriAl = async () => {
    if (!aktif || !ozet) return;
    try {
      await useKurgu.getState().kaydet();
      await istek(`/api/kurgu/${aktif.studyo}/${aktif.ad}/geri/${ozet.once_rev}`, { method: "POST" });
      await kurguAl();
      setOzet({ ...ozet, geri_alinabilir: false });
      bildir("AI edit geri alındı; önceki kurgu yüklendi");
    } catch (e) { hata(e); }
  };
  const onayarKaydet = async (ad: string, vars: boolean) => {
    if (!ayar || !/^[a-z0-9][a-z0-9-]{0,39}$/.test(ad)) { hata(new Error("Ön ayar adı küçük harf, rakam, tire")); return; }
    try {
      const r = await istek(`/api/ekip/onayar/${ad}${vars ? "?varsayilan=true" : ""}`, { method: "PUT", json: { ...ayar, ad } });
      setVarsayilan(r.varsayilan); setOnayarlar({ ...onayarlar, [ad]: { ...ayar, ad } }); setAyar({ ...ayar, ad });
      bildir(vars ? `${ad} varsayılan ekip oldu` : `${ad} kaydedildi`);
    } catch (e) { hata(e); }
  };
  const projeyeKaydet = async () => {
    if (!ayar || !yol) return;
    try { await istek(yol, { method: "PUT", json: ayar }); bildir("Ekip ayarı bu projeye kaydedildi"); } catch (e) { hata(e); }
  };

  return (
    <div className="ai-edit">
      <div className="ai-govde">
        <label className="ai-alan">
          <span className="ai-etiket">İstek</span>
          <textarea value={istem} rows={3} aria-label="Edit isteği" placeholder={'Nasıl bir edit istiyorsun? Örn. "ai-reels stiliyle hızlı tempolu, sesi öne çıkar" (Ctrl+Enter başlatır)'}
            onChange={(e) => setIstem(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); editle(); } }} />
        </label>
        <div className="ai-ayarlar" aria-label="Edit ayarları">
          <label>Stil
            <select value={stil} onChange={(e) => setStil(e.target.value)} disabled={!aktif} title="İstekte stil adı geçerse kendiliğinden seçilir">
              <option value="">Proje stili</option>
              {stiller.map((ad) => <option key={ad} value={ad}>{ad}</option>)}
            </select>
          </label>
          <label>Motion
            <select value={motion} onChange={(e) => setMotion(e.target.value)}>
              <option value="yogun">Yoğun</option><option value="orta">Orta</option><option value="az">Az</option>
            </select>
          </label>
          {!ekipModu && (
            <label title={aralik ? "Seçim: ajan yalnız bu aralığı değiştirir" : "Timeline'da klip seç ya da giriş-çıkış işaretle"}>Kapsam
              <select value={kapsam} onChange={(e) => setKapsam(e.target.value as "hepsi" | "secim")}>
                <option value="hepsi">Tüm video</option>
                <option value="secim" disabled={!aralik}>{aralik ? `Seçim ${sn(aralik[0])}–${sn(aralik[1])} sn` : "Seçim (yok)"}</option>
              </select>
            </label>
          )}
          <label className="onay" title="Taslak temizse final render, ses ve denetim">
            <input type="checkbox" checked={final} onChange={(e) => setFinal(e.target.checked)} /> Teslim et
          </label>
        </div>

        <div className="ai-calisma">
          <div className="segment segment-genis" role="radiogroup" aria-label="Çalışma biçimi">
            <button type="button" role="radio" aria-checked={!ekipModu} onClick={() => setEkipModu(false)} title="Tek ajan kurguyu yazar, vedit doğrular ve taslak alır">Tek ajan</button>
            <button type="button" role="radio" aria-checked={ekipModu} onClick={() => setEkipModu(true)} title="Orkestratör ajan sayısını ve modellerini seçer; editörler ve kalite kontrol paralel çalışır (ADR 0059)">Swarm</button>
          </div>
          {!ekipModu && <MotorSatiri />}
          {ekipModu && ayar && (
            <>
              <SuruSecici ayar={ayar} setAyar={setAyar} durum={ajanDurum} kilitli={!!calisan} />
              <details className="ai-cekmece">
                <summary><Settings2 size={13} /> Swarm ayarları <span className="ipucu">varsayılan modeller, yedek, ön ayar{ayar.ad ? ` · ${ayar.ad}` : ""}</span></summary>
                <EkipAyarlari ayar={ayar} setAyar={setAyar} durum={ajanDurum} onayarlar={onayarlar} varsayilan={varsayilan} projeVar={!!aktif}
                  onayarSec={(ad) => onayarlar[ad] && setAyar(onayarlar[ad])} onayarKaydet={onayarKaydet} projeyeKaydet={projeyeKaydet} />
              </details>
            </>
          )}
          {ekipModu && !ayar && <span className="ipucu">Swarm ayarı yükleniyor…</span>}
        </div>

        <div className="ai-eylem">
          {calisan
            ? <Dugme tur="tehlike" onClick={() => istek(`/api/isler/${calisan.id}/iptal`, { method: "POST" }).catch(hata)}
                title={ekipModu ? "Bütün ajanları durdurur; kurgu son geçen kapıda kalır" : "AI editi durdurur"}><CircleStop size={14} /> {ekipModu ? "Hepsini durdur" : "Durdur"}</Dugme>
            : <Dugme tur="birincil" className="ai-ana" disabled={!aktif || !hazir} onClick={editle}
                title={neden || (ekipModu ? "Orkestratör ekibi kurar, editörler paralel yazar, kural kapısı ve QC denetler" : "AI kurguyu seçili stille yazar, vedit doğrular ve taslak alır")}>
                <Wand2 size={15} /> AI ile editle</Dugme>}
          {neden && !calisan && <span className="ipucu">{neden}</span>}
        </div>

        {ekipModu && yol && <EkipIlerleme yol={yol} calisanId={calisan?.id} />}
        {!ekipModu && sonEdit && tekGunluk.length > 0 && (
          <details className="ai-gunluk" open={!!calisan}>
            <summary>{calisan ? "Çalışıyor…" : "Son AI edit günlüğü"}</summary>
            <div ref={gunlukKutu} className="gunluk" tabIndex={0} aria-label="AI edit günlüğü" aria-live="polite">
              {tekGunluk.map((l, i) => <div key={i} className={l.startsWith("→") ? "ajan-arac" : l.startsWith("Hata") ? "uyar" : undefined}>{l || " "}</div>)}
            </div>
          </details>
        )}
      </div>

      {ozet && (
        <div className="ai-sonuc" role="status">
          <span className="ai-sonuc-metin"><b>Son AI edit</b> {ozet.klip[0]} → {ozet.klip[1]} klip · {sn(ozet.sure[0])} → {sn(ozet.sure[1])} sn{ozet.aralik ? ` · yalnız ${sn(ozet.aralik[0])}–${sn(ozet.aralik[1])} sn` : ""}</span>
          {ozet.geri_alinabilir && <Dugme onClick={geriAl} disabled={!!calisan} title={`Kurguyu AI edit öncesine (rev ${ozet.once_rev}) döndürür; şimdiki sürüm geçmişte kalır`}><Undo2 size={13} /> Geri al</Dugme>}
          {!!ozet.rapor.length && <details><summary>Rapor</summary><div className="ai-rapor">{ozet.rapor.map((l, i) => <div key={i}>{l || " "}</div>)}</div></details>}
        </div>
      )}
    </div>
  );
};
