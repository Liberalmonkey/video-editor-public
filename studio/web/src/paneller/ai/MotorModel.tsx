import React, { useEffect, useMemo, useState } from "react";
import type { ModelOge, MotorDurum } from "../../depo";

// Motor, model ve akıl yürütme seviyesi seçicileri; AI panelinin iki sekmesi ve ekip ayarları ortak kullanır.
// Model listeleri canlı motor taramasından gelir (motorlar.py); kurulu olmayan motor soluk ve sebebiyle görünür.

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

// Seçilen motor kurulu değilse ya da model listesi boşsa sebebi döner; boş metin: hazır.
export const motorSebebi = (m?: MotorDurum) => (!m ? "taranıyor" : !m.kurulu ? `kurulu değil. ${m.kurulum ?? ""}` : m.hata ?? "");

export const ModelSecici: React.FC<{ motor?: MotorDurum; secili: string; sec: (id: string) => void; etiket?: string }> = ({ motor, secili, sec, etiket: e }) => {
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
        <input type="search" value={sorgu} onChange={(ev) => setSorgu(ev.target.value)} aria-label="Model ara"
          placeholder={`Ara (${modeller.length})`} title="Kimlik, ad ya da sağlayıcıda arar; ücretsizler için free yaz" />
      )}
      <select aria-label={e ?? "Model"} value={secili} disabled={!modeller.length} title={secOge ? `${secOge.id}${secOge.aciklama ? ` · ${secOge.aciklama}` : ""}` : secili}
        onChange={(ev) => sec(ev.target.value)}>
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

export const MotorSec: React.FC<{ deger?: string | null; bos?: boolean; sec: (m: string) => void; durum: Record<string, MotorDurum> | null; etiket: string }> = ({ deger, bos, sec, durum, etiket: e }) => (
  <select className="motor-sec" aria-label={e} value={deger ?? ""} onChange={(ev) => sec(ev.target.value)}>
    {bos && <option value="">yedek yok</option>}
    {Object.entries(durum ?? {}).map(([k, v]) => {
      const sebep = motorSebebi(v);
      return <option key={k} value={k} disabled={!v.kurulu} title={sebep || `${v.ad} ${v.surum}`}>{v.ad}{sebep ? ` (${!v.kurulu ? "kurulu değil" : "uyarı"})` : ""}</option>;
    })}
  </select>
);

export const SeviyeSec: React.FC<{ m?: MotorDurum; deger?: string | null; sec: (s: string | null) => void; etiket: string }> = ({ m, deger, sec, etiket: e }) => (
  <select className="effort-sec" aria-label={e} value={deger ?? ""} disabled={!m?.seviyeler?.length} onChange={(ev) => sec(ev.target.value || null)}
    title={m?.seviyeler?.length ? "Akıl yürütme seviyesi" : "Bu motorda seviye model adındadır"}>
    <option value="">effort: varsayılan</option>
    {(m?.seviyeler ?? []).map((s) => <option key={s} value={s}>effort: {s}</option>)}
  </select>
);
