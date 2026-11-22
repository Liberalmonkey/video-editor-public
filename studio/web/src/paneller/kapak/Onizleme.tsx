// Kapak önizlemesi ve kırpma alanları. Gerçek şablon gerçek ölçüde (w×h) bir iframe'de durur ve kutuya sığacak kadar küçültülür.
import React, { useEffect, useRef, useState } from "react";
import type { Alan } from "./tipler";

export const Guvenli: React.FC<{ alanlar: Alan[]; etiket?: boolean }> = ({ alanlar, etiket }) => (
  <>
    {alanlar.map((g) => (
      <span key={g.ad} aria-hidden className={`kapak-guvenli ${g.tur}`}
        style={{ left: `${g.kutu[0]}%`, top: `${g.kutu[1]}%`, width: `${g.kutu[2] - g.kutu[0]}%`, height: `${g.kutu[3] - g.kutu[1]}%` }}>
        {etiket && <i>{g.ad}</i>}
      </span>
    ))}
  </>
);

// vw/vh render'daki gibi çözülür; olc: yazı tipi yüklendikten sonra öndeki yazı kutuları (tuval yüzdesi).
export const Onizleme: React.FC<{ html: string; w: number; h: number; alanlar: Alan[]; olc: (r: number[][]) => void }> = ({ html, w, h, alanlar, olc }) => {
  const kutu = useRef<HTMLDivElement>(null);
  const [olcek, setOlcek] = useState(0);
  useEffect(() => {
    const el = kutu.current;
    if (!el) return;
    const g = new ResizeObserver(() => setOlcek(el.clientWidth / w));
    g.observe(el);
    return () => g.disconnect();
  }, [w]);
  return (
    <div ref={kutu} className="kapak-onizleme" style={{ aspectRatio: `${w} / ${h}`, maxWidth: w > h ? 560 : 280 }}>
      {/* sandbox: betik çalışmaz; allow-same-origin yalnız zemin ve yazı tipinin yüklenmesi için */}
      <iframe title="Kapak önizlemesi" sandbox="allow-same-origin" srcDoc={html} style={{ width: w, height: h, transform: `scale(${olcek})` }}
        onLoad={(e) => {
          const belge = e.currentTarget.contentDocument;
          belge?.fonts.ready.then(() => {
            // Öndeki bütün yazılar (kapak.OLC_JS ile aynı küme); öznenin arkasındaki dev söz (z-index 1) bilerek taşar.
            const g = belge.defaultView!;
            olc([...belge.querySelectorAll(".baslik,.ek,.etiket")]
              .filter((el) => g.getComputedStyle(el).display !== "none" && g.getComputedStyle(el).zIndex !== "1" && el.textContent?.trim())
              .map((el) => el.getBoundingClientRect()).filter((r) => r.width > 0)
              .map((r) => [r.left / w, r.top / h, r.right / w, r.bottom / h].map((v) => v * 100)));
          });
        }} />
      <Guvenli alanlar={alanlar} etiket />
    </div>
  );
};
