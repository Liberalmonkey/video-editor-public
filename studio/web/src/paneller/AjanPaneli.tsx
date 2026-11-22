import { CircleStop, MessageSquarePlus, RefreshCw, Send, Undo2, Wand2 } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { istek, sor } from "../api";
import { useDepo, type ModelOge, type MotorDurum } from "../depo";
import { Bos, Dugme, IkonDugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import { EkipPaneli } from "./EkipPaneli";

// Durum gelmeden önce de dört motor görünsün; kurulu olup olmadığını backend söyler.
const YEDEK_MOTORLAR: Record<string, MotorDurum> = Object.fromEntries(
  [["claude", "Claude Code"], ["antigravity", "Antigravity"], ["codex", "Codex"], ["opencode", "OpenCode"]]
    .map(([k, ad]) => [k, { ad, kurulu: true, surum: "", modeller: [] }]));
const ARAMA_ESIGI = 20; // bundan çok model varsa arama kutusu çıkar (OpenCode yüzlerce model listeler)

const ara = (s: string) => s.toLocaleLowerCase("tr").replace(/ı/g, "i");
// Modeller gruplarına ayrılır, sıra korunur; arama kimlik, ad ve grupta geçer. Seçili model süzülse de listede kalır.
export const modelGruplari = (modeller: ModelOge[], sorgu: string, secili?: string) => {
  const q = ara(sorgu.trim());
  const gruplar = new Map<string, ModelOge[]>();
  for (const m of modeller) {
    const uygun = !q || q.split(/\s+/).every((p) => ara(`${m.id} ${m.ad} ${m.grup ?? ""}${m.ucretsiz ? " ücretsiz free" : ""}`).includes(p));
    if (!uygun && m.id !== secili) continue;
    const g = m.grup ?? "Modeller";
    gruplar.set(g, [...(gruplar.get(g) ?? []), m]);
  }
  return [...gruplar].map(([grup, liste]) => ({ grup, liste }));
};
// Rozet ve başlık için okunur ad: listede varsa adı, yoksa kimliğin son parçası.
export const modelAdi = (motor: MotorDurum | undefined, id: string) =>
  motor?.modeller.find((m) => m.id === id)?.ad ?? id.split("/").pop() ?? id;
const etiket = (m: ModelOge, varsayilan?: string | null) =>
  `${m.ad}${m.ucretsiz ? " · ücretsiz" : ""}${m.id === varsayilan ? " · varsayılan" : ""}`;

export const ModelSecici: React.FC<{ motor?: MotorDurum; secili: string; sec: (id: string) => void }> = ({ motor, secili, sec }) => {
  const [sorgu, setSorgu] = useState("");
  const modeller = motor?.modeller ?? [];
  useEffect(() => setSorgu(""), [motor?.ad]);
  const gruplar = useMemo(() => modelGruplari(modeller, sorgu, secili), [modeller, sorgu, secili]);
  const tekGrup = gruplar.length === 1;
  const bulunan = gruplar.reduce((n, g) => n + g.liste.length, 0);
  const secOge = modeller.find((m) => m.id === secili);
  return (
    <span className="model-secici">
      {modeller.length > ARAMA_ESIGI && (
        <input type="search" value={sorgu} onChange={(e) => setSorgu(e.target.value)} aria-label="Model ara"
          placeholder={`Ara (${modeller.length})`} title="Kimlik, ad ya da sağlayıcıda arar; ücretsizler için free yaz" />
      )}
      <select aria-label="Model" value={secili} disabled={!modeller.length} title={secOge ? `${secOge.id}${secOge.aciklama ? ` · ${secOge.aciklama}` : ""}` : secili}
        onChange={(e) => sec(e.target.value)}>
        {!modeller.length && <option value={secili}>{motor?.kurulu === false ? "Kurulu değil" : "Modeller yükleniyor…"}</option>}
        {gruplar.map(({ grup, liste }) => {
          const ogeler = liste.map((m) => <option key={m.id} value={m.id}>{etiket(m, motor?.varsayilan)}</option>);
          return tekGrup ? ogeler : <optgroup key={grup} label={`${grup} (${liste.length})`}>{ogeler}</optgroup>;
        })}
      </select>
      {sorgu && <span className="ipucu" role="status">{bulunan ? `${bulunan} sonuç` : "Sonuç yok"}</span>}
    </span>
  );
};

interface AiOzet { once_rev: number; rev: number; klip: [number, number]; sure: [number, number]; aralik: [number, number] | null; rapor: string[]; geri_alinabilir: boolean }

// ı ve i tek harf sayılır: Türkçe küçültme "AI"yı "aı" yapar, stil adı "ai-reels" ile eşleşmezdi.
const sade = (s: string) => ` ${s.toLocaleLowerCase("tr").replace(/ı/g, "i").replace(/[^\p{L}\p{N}]+/gu, " ").trim()} `;
// İstekte adı geçen stil: "ai-reels stiliyle editle" ve "ai reels" ikisi de eşleşir; en uzun ad kazanır.
export const istektekiStil = (istem: string, stiller: string[]) =>
  [...stiller].sort((a, b) => b.length - a.length).find((ad) => sade(istem).includes(sade(ad))) ?? null;
const sn = (v: number) => v.toLocaleString("tr", { maximumFractionDigits: 1 });

// AI paneli: Claude Code, Antigravity, Codex ya da OpenCode'u seçilen modelle başlatır, çıktı canlı akar. WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md
// "AI ile editle" aynı isteği editöre not olarak `vedit ai-edit` işine verir. WHY: bkz. wiki/decisions/0028-ai-edit.md
export const AjanPaneli: React.FC = () => {
  const { ajanDurum, ajan, isler, gunlukler, sohbetBasi, aktif, ajanDurumAl, ajanSec, ajanGonder, yeniSohbet, hata, isBaslat, bildir, kurguAl } = useDepo();
  const [istem, setIstem] = useState("");
  const [stiller, setStiller] = useState<string[]>([]);
  const [stil, setStil] = useState(""); // boş: projenin seçili stili
  const [motion, setMotion] = useState("yogun");
  const [final, setFinal] = useState(false);
  const [yalnizAralik, setYalnizAralik] = useState(false);
  const [ekipModu, setEkipModu] = useState(() => { try { return localStorage.getItem("ekipModu") === "1"; } catch { return false; } });
  useEffect(() => { try { localStorage.setItem("ekipModu", ekipModu ? "1" : "0"); } catch { /* tarayıcı depolaması kapalı */ } }, [ekipModu]);
  const [ozet, setOzet] = useState<AiOzet | null>(null);
  const kutu = useRef<HTMLDivElement>(null);
  const sohbet = isler.filter((x) => (x.komut === "ajan" || x.komut === "ai-edit") && x.id >= sohbetBasi).reverse();
  const bitenEdit = isler.filter((x) => x.komut === "ai-edit" && x.bitis).length;
  // Kapsam: seçili kliplerin kapladığı süre, seçim yoksa giriş-çıkış işaretleri.
  const klipler = useKurgu((d) => d.kurgu?.klipler);
  const secim = useKurgu((d) => d.secim);
  const giris = useKurgu((d) => d.giris), cikis = useKurgu((d) => d.cikis);
  const aralik = useMemo((): [number, number] | null => {
    const sec = (klipler ?? []).filter((c) => secim.includes(c.id));
    if (sec.length) return [Math.min(...sec.map((c) => c.bas)), Math.max(...sec.map((c) => c.bas + c.sure))];
    return giris !== null && cikis !== null && cikis > giris ? [giris, cikis] : null;
  }, [klipler, secim, giris, cikis]);
  const calisan = sohbet.find((x) => x.durum === "calisiyor" || x.durum === "sirada");
  const motor = ajanDurum?.[ajan.motor];
  const satirSayisi = sohbet.reduce((n, x) => n + (gunlukler[x.id]?.length ?? 0), 0);

  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
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
  useEffect(() => { if (!aralik) setYalnizAralik(false); }, [!aralik]);
  useEffect(() => {
    const k = kutu.current;
    if (k && k.scrollHeight - k.scrollTop - k.clientHeight < 120) k.scrollTop = k.scrollHeight;
  }, [satirSayisi, sohbet.length]);

  const gonder = async () => {
    if (!istem.trim() || !motor?.kurulu) return;
    if (await ajanGonder(istem)) setIstem("");
  };
  const editle = async () => {
    if (!aktif || !motor?.kurulu) return;
    await isBaslat("ai-edit", { motor: ajan.motor, model: ajan.model, notu: istem.trim() || undefined, stil: stil || undefined, motion, final,
      ...(yalnizAralik && aralik ? { aralik } : {}) });
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

  return (
    <div className="panel ajan">
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <div className="arac-grup motorlar" role="radiogroup" aria-label="AI motoru">
          {Object.entries(ajanDurum ?? YEDEK_MOTORLAR).map(([k, v]) => {
            const durum = !ajanDurum ? "bekliyor" : !v.kurulu ? "yok" : v.hata ? "uyari" : "hazir";
            const ipucu = !ajanDurum ? `${v.ad} taranıyor…` : !v.kurulu ? `${v.ad} kurulu değil. ${v.kurulum ?? ""}`
              : `${v.ad} ${v.surum} · ${v.modeller.length} model${v.hata ? ` · ${v.hata}` : ""}`;
            return (
              <Dugme key={k} role="radio" aria-checked={ajan.motor === k} acik={ajan.motor === k} disabled={!!ajanDurum && !v.kurulu}
                title={ipucu} onClick={() => ajanSec({ motor: k })}><i className={`motor-nokta ${durum}`} aria-hidden="true" />{v.ad}</Dugme>
            );
          })}
        </div>
        <ModelSecici motor={motor} secili={ajan.model} sec={(id) => ajanSec({ model: id })} />
        <select aria-label="Çalışma modu" value={ajan.mod} onChange={(e) => ajanSec({ mod: e.target.value as "duzenle" | "plan" })}
          title={`Düzenle: ${motor?.mod_ipucu?.duzenle ?? "dosya düzenleyebilir"}. Yalnız plan: ${motor?.mod_ipucu?.plan ?? "okur ve önerir, dosyaya dokunmaz"}.`}>
          <option value="duzenle">Düzenle</option><option value="plan">Yalnız plan</option>
        </select>
        <span className="bosluk" style={{ flex: 1 }} />
        <IkonDugme ad="Yeni sohbet" onClick={yeniSohbet}><MessageSquarePlus size={14} /></IkonDugme>
        <IkonDugme ad="Motorları ve modelleri yeniden tara" onClick={() => ajanDurumAl(true)}><RefreshCw size={13} /></IkonDugme>
      </div>
      {ajanDurum && !motor?.kurulu && (
        <Bos baslik={`${motor?.ad ?? ajan.motor} kurulu değil`} metin={motor?.kurulum ?? "Motoru kur, giriş yap, sonra yeniden tara."} />
      )}
      {motor?.kurulu && motor.hata && <div className="uyar ajan-uyari" role="status">{motor.ad}: {motor.hata}</div>}
      <div ref={kutu} className="gunluk" tabIndex={0} aria-label="AI çıktısı" aria-live="polite">
        {!sohbet.length && <span className="ipucu">{aktif ? `İstek ${aktif.studyo}/${aktif.ad} projesiyle gönderilir. ` : ""}Aynı sohbet sürer; "Yeni sohbet" sıfırlar.</span>}
        {sohbet.map((x) => (
          <div key={x.id} className="ajan-tur">
            <div className="ajan-baslik">{x.baslik}</div>
            {(gunlukler[x.id] ?? []).map((l, i) => <div key={i} className={l.startsWith("→") ? "ajan-arac" : l.startsWith("Hata") ? "uyar" : undefined}>{l || " "}</div>)}
            {x.durum === "calisiyor" && <div className="ajan-nabiz">Çalışıyor…</div>}
          </div>
        ))}
      </div>
      {ozet && (
        <div className="ajan-ozet" role="status">
          <span><b>Son AI edit:</b> {ozet.klip[0]} → {ozet.klip[1]} klip · {sn(ozet.sure[0])} → {sn(ozet.sure[1])} sn{ozet.aralik ? ` · yalnız ${sn(ozet.aralik[0])}–${sn(ozet.aralik[1])} sn` : ""}</span>
          {ozet.geri_alinabilir && <Dugme onClick={geriAl} disabled={!!calisan} title={`Kurguyu AI edit öncesine (rev ${ozet.once_rev}) döndürür; şimdiki sürüm geçmişte kalır`}><Undo2 size={13} /> Geri al</Dugme>}
          {!!ozet.rapor.length && <details><summary>Rapor</summary>{ozet.rapor.map((l, i) => <div key={i}>{l || " "}</div>)}</details>}
        </div>
      )}
      <div className="ajan-edit" aria-label="AI edit ayarları">
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
        <label title={aralik ? "Ajan yalnız bu aralığı değiştirir; dışı aynı kalır" : "Timeline'da klip seç ya da giriş-çıkış işaretle"}>
          <input type="checkbox" checked={yalnizAralik} disabled={!aralik} onChange={(e) => setYalnizAralik(e.target.checked)} />
          {aralik ? `Yalnız ${sn(aralik[0])}–${sn(aralik[1])} sn` : "Yalnız seçim"}
        </label>
        <label title="Taslak temizse final render, ses ve denetim">
          <input type="checkbox" checked={final} onChange={(e) => setFinal(e.target.checked)} /> Teslim et
        </label>
        <label title="3 editör + 3 kalite kontrol ajanı, her slotta ayrı motor ve model (ADR 0044)">
          <input type="checkbox" checked={ekipModu} onChange={(e) => setEkipModu(e.target.checked)} /> Ekip modu
        </label>
      </div>
      {ekipModu && <EkipPaneli stil={stil} motion={motion} final={final} notu={istem} bitti={() => setIstem("")} />}
      <div className="ajan-girdi">
        <textarea value={istem} rows={3} aria-label="İstek" placeholder={'Nasıl bir edit istiyorsun? Örn. "ai-reels stiliyle hızlı tempolu animasyon" (Ctrl+Enter sohbete gönderir)'}
          onChange={(e) => setIstem(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); gonder(); } }} />
        {calisan
          ? <Dugme tur="tehlike" onClick={() => istek(`/api/isler/${calisan.id}/iptal`, { method: "POST" }).catch(hata)}><CircleStop size={14} /> Durdur</Dugme>
          : <span className="ajan-dugmeler">
              {!ekipModu && <Dugme tur="birincil" disabled={!aktif || !motor?.kurulu} onClick={editle}
                title="İsteği editöre not olarak verir: AI kurguyu seçili stille yazar, vedit doğrular ve taslak alır"><Wand2 size={14} /> AI ile editle</Dugme>}
              <Dugme disabled={!istem.trim() || !motor?.kurulu} onClick={gonder} title="Serbest sohbet: soru sor ya da tek bir düzeltme iste"><Send size={14} /> Gönder</Dugme>
            </span>}
      </div>
    </div>
  );
};

// Üst çubuk rozeti: hangi motor, hangi model, çalışıyor mu. Tıklayınca AI paneline gider.
export const AjanRozeti: React.FC<{ ac: () => void }> = ({ ac }) => {
  const { ajanDurum, ajan, isler, ajanDurumAl } = useDepo();
  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
  const motor = ajanDurum?.[ajan.motor];
  const calisan = isler.find((x) => (x.komut === "ajan" || x.komut === "ai-edit") && (x.durum === "calisiyor" || x.durum === "sirada"));
  const durum = !ajanDurum ? "…" : !motor?.kurulu ? "Kurulu değil" : calisan ? "Çalışıyor" : "Hazır";
  const gosterilen = calisan ? ajanDurum?.[calisan.motor ?? ""] : motor;
  const mId = calisan?.model ?? ajan.model;
  const m = modelAdi(gosterilen, mId);
  const motorAd = gosterilen?.ad ?? calisan?.motor ?? ajan.motor;
  return (
    <button type="button" className={`ajan-rozet ${calisan ? "calisiyor" : ""} ${ajanDurum && !motor?.kurulu ? "yok" : ""}`} onClick={ac}
      title={`${motorAd} ${gosterilen?.surum ?? ""} · model ${mId} · ${durum}. AI panelini aç.`}>
      <i aria-hidden="true" /><span className="rozet-metin">{motorAd} · <b>{m}</b> · {durum}</span>
    </button>
  );
};
