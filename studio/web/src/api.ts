export class ApiHata extends Error {
  constructor(public durum: number, mesaj: string) { super(mesaj); }
}

const hataMetni = (durum: number, detay: unknown): string => {
  if (durum === 401) return "Oturum geçersiz: sunucu yeniden başlamış. Uygulamayı studio.bat ile yeniden aç.";
  if (typeof detay === "string") return detay;
  if (Array.isArray(detay)) return detay.map((d: any) => d.msg ?? String(d)).join("; ");
  return `Sunucu hatası (${durum})`;
};

export async function istek<T = any>(yol: string, secenek: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, ...ince } = secenek;
  let r: Response;
  try {
    r = await fetch(yol, json === undefined ? ince : { ...ince, headers: { "Content-Type": "application/json" }, body: JSON.stringify(json) });
  } catch {
    throw new ApiHata(0, "Sunucuya ulaşılamıyor. Terminalde vedit studio çalışıyor mu?");
  }
  if (!r.ok) {
    const veri = await r.json().catch(() => ({}));
    throw new ApiHata(r.status, hataMetni(r.status, veri.detail));
  }
  return r.json();
}

export const sor = (o: Record<string, string | number | boolean | undefined>) => {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(o)) if (v !== undefined && v !== "") p.set(k, String(v));
  return p.toString();
};

// XHR: fetch yükleme ilerlemesi vermez.
export const yukle = (url: string, dosya: File, ilerleme: (oran: number) => void) =>
  new Promise<void>((coz, reddet) => {
    const x = new XMLHttpRequest();
    x.open("PUT", url);
    x.upload.onprogress = (e) => e.lengthComputable && ilerleme(e.loaded / e.total);
    x.onload = () => {
      if (x.status < 300) return coz();
      let detay: unknown;
      try { detay = JSON.parse(x.responseText).detail; } catch { /* metin değil */ }
      reddet(new ApiHata(x.status, hataMetni(x.status, detay)));
    };
    x.onerror = () => reddet(new ApiHata(0, "Yükleme kesildi. Dosya kaydedilmedi."));
    x.send(dosya);
  });

export const boyutYaz = (b: number) => {
  if (b < 1024) return `${b} B`;
  if (b < 1 << 20) return `${(b / 1024).toFixed(0)} KB`;
  if (b < 1 << 30) return `${(b / (1 << 20)).toFixed(1)} MB`;
  return `${(b / (1 << 30)).toFixed(2)} GB`;
};

export const sureYaz = (s?: number | null) => {
  if (s == null) return "";
  const t = Math.round(s);
  if (s < 10) return `${s.toFixed(1)} sn`;
  return t >= 3600 ? `${Math.floor(t / 3600)}:${String(Math.floor(t / 60) % 60).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}` : `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
};
