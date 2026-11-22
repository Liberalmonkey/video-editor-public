// SplitReel sahne türleri için başlangıç içeriği. Alanlar SplitReel.tsx'in okuduklarıyla aynıdır.
export interface Sablon { kind: string; ad: string; aciklama: string; sure: number; sahne: Record<string, any> }

export const SABLONLAR: Sablon[] = [
  { kind: "hook", ad: "Hook", aciklama: "Tam ekran konuşmacı üstünde büyük başlık", sure: 2, sahne: { layout: "full", kind: "hook", title: "BAŞLIK", size: 132, subtitle: "Alt başlık" } },
  { kind: "stat", ad: "Sayı", aciklama: "Sayaçla büyüyen rakam ve etiket", sure: 3, sahne: { layout: "split", bg: "dark", kind: "stat", value: 100, decimals: 0, prefix: "", unit: "%", label: "Etiket yaz" } },
  { kind: "text", ad: "Yazı", aciklama: "Satır satır gelen başlık", sure: 3, sahne: { layout: "split", bg: "light", kind: "text", lines: [{ t: "İlk satır", size: 96, at: 0.1 }, { t: "Vurgulu satır", size: 96, accent: true, at: 0.5 }] } },
  { kind: "chips", ad: "Liste", aciklama: "Tiklenen kısa maddeler ve şerit", sure: 4, sahne: { layout: "split", bg: "dark", kind: "chips", items: [{ t: "Birinci", at: 0.1, done: 0.6 }, { t: "İkinci", at: 0.5, done: 1 }], banner: { at: 1.4, text: "Sonuç" } } },
  { kind: "steps", ad: "Adımlar", aciklama: "Numaralı adım listesi", sure: 4, sahne: { layout: "split", bg: "dark", kind: "steps", items: [{ n: "1", t: "İlk adım", at: 0.1 }, { n: "2", t: "İkinci adım", at: 0.6 }, { n: "3", t: "Üçüncü adım", at: 1.1 }] } },
  { kind: "timeline", ad: "Zaman çizgisi", aciklama: "İki tarih arasında ilerleme", sure: 4, sahne: { layout: "split", bg: "dark", kind: "timeline", nodes: [{ date: "2024", text: "Başlangıç", at: 0.1, y: 340 }, { date: "2026", text: "Bugün", at: 0.8, y: 720 }], line: { at: 0.5, text: "2 yıl" } } },
  { kind: "shot", ad: "Ekran görüntüsü", aciklama: "Görsel üzerinde kayan odak", sure: 3, sahne: { layout: "split", bg: "dark", kind: "shot", img: null, iw: 1920, ih: 1080, focus: { x: 0, y: 0, w: 1920 }, kicker: [{ at: 0, text: "Başlık" }] } },
  { kind: "cta", ad: "Çağrı", aciklama: "Video sonu kutusu", sure: 3, sahne: { layout: "full", kind: "cta", title: "Yorum yaz", size: 120, subtitle: "" } },
];

// Motion metin türleri (studio/remotion/MotionMetin.tsx, ADR 0031). Alanlar metin_stil'e yazılır.
export interface MetinSablon { tip: string; ad: string; aciklama: string; sure: number; metin: string; stil: Record<string, any> }
export const METIN_SABLONLARI: MetinSablon[] = [
  { tip: "anahtar", ad: "Anahtar kelime", aciklama: "Büyük kelime, zıplayarak gelir; *yıldızlı* kısım turuncu", sure: 1.5, metin: "Bu *çok* önemli", stil: {} },
  { tip: "altbant", ad: "Alt bant", aciklama: "Ad ve unvan, iki satır", sure: 4, metin: "Ad Soyad\nUnvan", stil: {} },
  { tip: "etiket", ad: "Etiket", aciklama: "Yuvarlak kutulu kısa etiket", sure: 2.5, metin: "Konu etiketi", stil: {} },
  { tip: "cagri", ad: "Çağrı oku", aciklama: "Etiket ve hedef noktaya çizgi", sure: 2.5, metin: "Buraya bak", stil: { hedef: { x: 0.7, y: 0.35 } } },
  { tip: "daktilo", ad: "Daktilo", aciklama: "Harf harf yazılan metin", sure: 3, metin: "Şunu yazıyoruz", stil: {} },
  { tip: "sayac", ad: "Sayaç", aciklama: "Sayarak büyüyen rakam ve etiket", sure: 2.5, metin: "etiket", stil: { deger: 100, sonek: "%", ondalik: 0 } },
  { tip: "ilerleme", ad: "İlerleme", aciklama: "Adım çubuğu: kaçıncı adımdayız", sure: 3, metin: "Adım adı", stil: { adim: 1, toplam: 3 } },
  { tip: "bolum", ad: "Bölüm kartı", aciklama: "Numara ve başlık, silerek gelir", sure: 2.5, metin: "Bölüm başlığı", stil: { numara: "01" } },
  { tip: "vurgu", ad: "Vurgu çizimi", aciklama: "Karede bir alanı el çizimiyle çevreler", sure: 2, metin: "", stil: { bicim: "daire", kutu: { x: 0.3, y: 0.4, w: 0.4, h: 0.1 } } },
];
