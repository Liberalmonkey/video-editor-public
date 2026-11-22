import { X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useDepo } from "./depo";

export const Dugme: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { tur?: "birincil" | "tehlike" | "ikon"; acik?: boolean }> = ({ tur, acik, className, ...p }) => (
  <button type="button" {...p} className={["dugme", tur, acik && "acik", className].filter(Boolean).join(" ")} />
);

export const IkonDugme: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { ad: string; acik?: boolean }> = ({ ad, ...p }) => (
  <Dugme tur="ikon" title={ad} aria-label={ad} {...p} />
);

export const Bos: React.FC<{ baslik: string; metin?: string; children?: React.ReactNode }> = ({ baslik, metin, children }) => (
  <div className="bos"><h3>{baslik}</h3>{metin && <p>{metin}</p>}{children}</div>
);

export const Iskelet: React.FC<{ n?: number }> = ({ n = 6 }) => <>{Array.from({ length: n }, (_, i) => <div key={i} className="iskelet" />)}</>;

// <dialog>: odak hapsi, Esc ve üst katman tarayıcıdan gelir.
export const Diyalog: React.FC<{ acik: boolean; kapat: () => void; children: React.ReactNode }> = ({ acik, kapat, children }) => {
  const d = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (acik && !d.current?.open) d.current?.showModal();
    if (!acik && d.current?.open) d.current?.close();
  }, [acik]);
  return <dialog ref={d} onCancel={(e) => { e.preventDefault(); kapat(); }}>{acik && children}</dialog>;
};

export const OnayKatmani: React.FC = () => {
  const s = useDepo((d) => d.sorgu);
  return (
    <Diyalog acik={!!s} kapat={() => s?.coz(false)}>
      {s && <>
        <h2>{s.baslik}</h2>
        <p>{s.metin}</p>
        <div className="eylemler">
          <Dugme onClick={() => s.coz(false)} autoFocus>Vazgeç</Dugme>
          <Dugme tur={s.tehlike ? "tehlike" : "birincil"} onClick={() => s.coz(true)}>{s.onay}</Dugme>
        </div>
      </>}
    </Diyalog>
  );
};

export const Bildirimler: React.FC = () => {
  const l = useDepo((d) => d.bildirimler);
  const kapat = useDepo((d) => d.kapat);
  return (
    <div className="bildirimler" role="status" aria-live="polite">
      {l.map((b) => (
        <div key={b.id} className={`bildirim ${b.hata ? "hata" : ""}`}>
          <span>{b.metin}</span>
          <IkonDugme ad="Kapat" onClick={() => kapat(b.id)} style={{ width: 20, minHeight: 20, padding: 1 }}><X size={13} /></IkonDugme>
        </div>
      ))}
    </div>
  );
};

// Tek paylaşılan ses: aynı anda bir önizleme çalar.
const ses = typeof Audio === "undefined" ? null : new Audio();
export const useDinle = () => {
  const [calan, setCalan] = useState<string | null>(null);
  useEffect(() => {
    if (!ses) return;
    const dur = () => setCalan(null);
    ses.addEventListener("ended", dur);
    return () => { ses.removeEventListener("ended", dur); ses.pause(); };
  }, []);
  return {
    calan,
    cal: (url: string) => {
      if (!ses) return;
      if (calan === url) { ses.pause(); setCalan(null); return; }
      ses.src = url;
      ses.play().catch(() => setCalan(null));
      setCalan(url);
    },
  };
};

export const DosyaSec: React.FC<{ kabul?: string; sec: (d: File[]) => void; children: React.ReactNode; disabled?: boolean }> = ({ kabul, sec, children, disabled }) => {
  const g = useRef<HTMLInputElement>(null);
  return (
    <>
      <input ref={g} type="file" multiple hidden accept={kabul} onChange={(e) => { sec([...(e.target.files ?? [])]); e.target.value = ""; }} />
      <Dugme disabled={disabled} onClick={() => g.current?.click()}>{children}</Dugme>
    </>
  );
};
