// Panellerin ortak alanları. Metin Enter ya da odak kaybında işlenir; sayı sürüklenince tek geri alma adımı olur.
import React, { useEffect, useRef, useState } from "react";

const yuvarla = (v: number, adim: number) => {
  const r = Math.round(v / adim) * adim;
  return Number(r.toFixed(Math.max(0, Math.ceil(-Math.log10(adim)))));
};

export const Sayi: React.FC<{
  deger: number; degis: (v: number) => void; adim?: number; min?: number; max?: number; carpan?: number; birim?: string; etiket: string; disabled?: boolean;
}> = ({ deger, degis, adim = 1, min = -Infinity, max = Infinity, carpan = 1, birim, etiket, disabled }) => {
  const goster = yuvarla(deger * carpan, adim);
  const [taslak, setTaslak] = useState<string | null>(null);
  const bas = useRef<{ x: number; v: number } | null>(null);
  const sinirla = (v: number) => Math.min(max, Math.max(min, v));
  const isle = () => {
    if (taslak === null) return;
    const n = Number(taslak.replace(",", "."));
    setTaslak(null);
    if (Number.isFinite(n)) degis(sinirla(n) / carpan);
  };
  return (
    <span className="sayi-alan">
      <span
        className="sayi-tut" title="Sürükle" aria-hidden
        onPointerDown={(e) => { if (disabled) return; e.currentTarget.setPointerCapture(e.pointerId); bas.current = { x: e.clientX, v: goster }; }}
        onPointerMove={(e) => { if (bas.current) degis(sinirla(yuvarla(bas.current.v + (e.clientX - bas.current.x) * adim * (e.shiftKey ? 10 : 1), adim)) / carpan); }}
        onPointerUp={() => { bas.current = null; }}
      >↔</span>
      <input aria-label={etiket} inputMode="decimal" disabled={disabled} value={taslak ?? String(goster)} onChange={(e) => setTaslak(e.target.value)} onBlur={isle}
        onKeyDown={(e) => { if (e.key === "Enter") { isle(); e.currentTarget.blur(); } if (e.key === "Escape") { setTaslak(null); e.currentTarget.blur(); } }} />
      {birim && <span className="ipucu">{birim}</span>}
    </span>
  );
};

export const Metin: React.FC<{ deger: string; degis: (v: string) => void; etiket: string; cok?: boolean; yer?: string }> = ({ deger, degis, etiket, cok, yer }) => {
  const [t, setT] = useState(deger);
  useEffect(() => setT(deger), [deger]);
  const isle = () => { if (t !== deger) degis(t); };
  return cok
    ? <textarea aria-label={etiket} rows={3} value={t} placeholder={yer} onChange={(e) => setT(e.target.value)} onBlur={isle} />
    : <input aria-label={etiket} value={t} placeholder={yer} onChange={(e) => setT(e.target.value)} onBlur={isle} onKeyDown={(e) => { if (e.key === "Enter") { isle(); e.currentTarget.blur(); } if (e.key === "Escape") { setT(deger); e.currentTarget.blur(); } }} />;
};

export const Secim: React.FC<{ deger: string; degis: (v: string) => void; etiket: string; secenekler: [string, string][] }> = ({ deger, degis, etiket, secenekler }) => (
  <select aria-label={etiket} value={deger} onChange={(e) => degis(e.target.value)}>{secenekler.map(([d, a]) => <option key={d} value={d}>{a}</option>)}</select>
);

export const Satir: React.FC<{ ad: string; children: React.ReactNode }> = ({ ad, children }) => (
  <div className="ef-satir"><span className="ef-ad">{ad}</span><span className="ef-deger">{children}</span></div>
);

export const Bolum: React.FC<{ ad: string; acik?: boolean; children: React.ReactNode }> = ({ ad, acik = true, children }) => (
  <details className="ef-bolum" open={acik}><summary>{ad}</summary><div className="ef-ic">{children}</div></details>
);
