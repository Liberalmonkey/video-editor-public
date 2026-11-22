import React, { useEffect, useState } from "react";
import { Diyalog, Dugme } from "../ortak";
import { KISAYOLLAR, kullaniciTuslari, tusAdi, tusKaydet, tusYaz } from "./kisayol";

const goster = (t: string) => (t === " " ? "Boşluk" : t.split(/\+(?!$)/).map((p) => (p.length === 1 ? p.toLocaleUpperCase("tr") : p[0].toUpperCase() + p.slice(1))).join(" + "));

export const KisayolDiyalog: React.FC<{ acik: boolean; kapat: () => void }> = ({ acik, kapat }) => {
  const [ozel, setOzel] = useState(kullaniciTuslari);
  const [dinle, setDinle] = useState<string | null>(null);
  const [uyari, setUyari] = useState("");

  useEffect(() => {
    if (!dinle) return;
    const f = (e: KeyboardEvent) => {
      if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) return;
      e.preventDefault(); e.stopPropagation();
      if (e.key === "Escape") { setDinle(null); return; }
      const t = tusAdi(e);
      const cakisan = KISAYOLLAR.find((k) => k.id !== dinle && tusYaz(k, ozel) === t);
      if (cakisan) { setUyari(`${goster(t)} zaten kullanılıyor: ${cakisan.ad}`); return; }
      const yeni = { ...ozel, [dinle]: t };
      setOzel(yeni); tusKaydet(yeni); setUyari(""); setDinle(null);
    };
    window.addEventListener("keydown", f, true);
    return () => window.removeEventListener("keydown", f, true);
  }, [dinle, ozel]);

  const gruplar = [...new Set(KISAYOLLAR.map((k) => k.grup))];
  return (
    <Diyalog acik={acik} kapat={() => { setDinle(null); kapat(); }}>
      <h2>Klavye kısayolları</h2>
      <p>Değiştirmek için tuşa tıkla, yeni tuşa bas. Esc vazgeçer.</p>
      {uyari && <p style={{ color: "var(--hata)" }} role="alert">{uyari}</p>}
      <div style={{ maxHeight: "58vh", overflow: "auto", marginBottom: 12 }}>
        {gruplar.map((g) => (
          <section key={g}>
            <div className="baslik" style={{ paddingLeft: 0 }}>{g}</div>
            {KISAYOLLAR.filter((k) => k.grup === g).map((k) => (
              <div key={k.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", minHeight: 28 }}>
                <span>{k.ad}</span>
                <Dugme onClick={() => { setUyari(""); setDinle(k.id); }} style={{ minWidth: 92, fontFamily: "var(--mono)", fontSize: 12 }} className={dinle === k.id ? "birincil" : ""}>
                  {dinle === k.id ? "Tuşa bas" : goster(tusYaz(k, ozel))}
                </Dugme>
              </div>
            ))}
          </section>
        ))}
      </div>
      <div className="eylemler">
        <Dugme onClick={() => { setOzel({}); tusKaydet({}); setUyari(""); }}>Varsayılana dön</Dugme>
        <Dugme tur="birincil" onClick={kapat}>Tamam</Dugme>
      </div>
    </Diyalog>
  );
};
