// Ses araçlarının mantığı: ses çıkarma, Demucs ile ayırma, ayrılan kanalları kurguya koyma. Düğmeler MikserPaneli'nde.
// WHY: bkz. wiki/decisions/0034-ses-araclari.md. Uzun işler iş kuyruğunda çalışır; burada bitene kadar beklenir, kurgu değişimi tek geri alma adımıdır.
import { istek } from "../api";
import { useDepo } from "../depo";
import type { Klip } from "../../../remotion/tipler";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";

export interface Stem { id: string; yol: string; sure: number; url: string }
export type StemKipi = 2 | 4;
export const BICIMLER: [string, string][] = [["wav", "WAV"], ["mp3", "MP3"], ["m4a", "M4A"]];
const ETIKET: Record<string, string> = { muzik: "Müzik", davul: "Davul", bas: "Bas", diger: "Diğer sesler" };
const VOKAL = /^public:ayrisan\/.+\.vokal\.wav$/;

// Sesi taşıyan klip: ayrık konuşma klibi ya da sesi hâlâ içinde olan video. Bağlı grupta tıklanan değil, sesin gerçekte olduğu klip.
export const sesKlibi = (secim: string[]): Klip | undefined => {
  const k = useKurgu.getState().kurgu;
  if (!k) return undefined;
  const grup = K.baglilar(k, secim);
  return k.klipler.find((c) => grup.includes(c.id) && c.kaynak && (c.olay?.konusma || (c.tur === "video" && !c.ses_kapali && k.kaynaklar[c.kaynak]?.ses)));
};

export const kaynakYolu = (c: Klip) => (c.kaynak ? useKurgu.getState().kurgu?.kaynaklar[c.kaynak]?.yol : undefined);
export const ayrilmisMi = (c: Klip) => VOKAL.test(kaynakYolu(c) ?? "");

const stemId = (c: Klip, stem: StemKipi, ad: string) => `${c.kaynak!.replace(/_(s4_)?vokal$/, "")}_${stem === 4 ? "s4_" : ""}${ad}`;
const bekle = async (id: number): Promise<string> => {
  for (;;) { // WHY: akış olayı çok kısa işte kaçabilir; liste her zaman doğru
    const j = (await istek<{ id: number; durum: string }[]>("/api/isler")).find((x) => x.id === id);
    if (!j) throw new Error("İş listede yok");
    if (["bitti", "hata", "iptal"].includes(j.durum)) return j.durum;
    await new Promise((r) => setTimeout(r, 1000));
  }
};
const ayrilanAd = (durum: string) => durum === "iptal" ? "İş iptal edildi" : "İş başarısız oldu. İşler panelindeki günlüğe bak.";

const stemleriAl = async (yol: string, stem: StemKipi): Promise<Record<string, Stem>> => {
  const anahtar = useKurgu.getState().anahtar!;
  const r = await istek(`/api/ayristir/${anahtar}`, { method: "POST", json: { yol, stem } });
  if (r.hazir) return r.stemler;
  useDepo.getState().bildir(`Ses ${stem} kanala ayrılıyor. CPU'da sesin yaklaşık 2,5 katı sürer; bu sırada kurgu yapabilirsin.`);
  const d = await bekle(r.is);
  if (d !== "bitti") throw new Error(ayrilanAd(d));
  // WHY: ayırma dakikalar sürer; bu sırada başka proje açıldıysa sonuç onun kurgusuna yazılmamalı.
  if (useKurgu.getState().anahtar !== anahtar) throw new Error("Proje değişti: ayrılan ses hazır ama kurguya uygulanmadı. Projeyi açıp yeniden dene.");
  const s = await istek(`/api/ayristir/${anahtar}?yol=${encodeURIComponent(yol)}&stem=${stem}`);
  if (!s.hazir) throw new Error("Ayrılan dosyalar bulunamadı");
  return s.stemler;
};

const medyaYaz = (m: Record<string, string>) => useKurgu.setState({ medya: { ...useKurgu.getState().medya, ...m } });

// Konuşma kanalını klibe uygular (ses videodaysa önce ayrılır): tek geri alma adımı. "Arka plan müziğini kaldır" 2 kanallı özel hâlidir.
export const konusmayiAyir = async (c: Klip, stem: StemKipi, ad: string) => {
  const yol = kaynakYolu(c);
  if (!yol) return;
  await useKurgu.getState().kaydet();
  const v = (await stemleriAl(yol, stem)).vokal;
  const vid = stemId(c, stem, "vokal");
  medyaYaz({ [vid]: v.url });
  let yeni: string | null = null;
  useKurgu.getState().duzenle(ad, (d) => { yeni = K.vokaleGec(d, c.id, { id: vid, yol: v.yol, sure: v.sure }); });
  if (yeni) { useKurgu.getState().sec([c.id, yeni]); useDepo.getState().bildir(`${ad}: tamam. Ayrılan parçalar work/public/ayrisan altında.`); }
  else useDepo.getState().bildir("Klipte hız %100 değil: önce hızı %100 yap. Ayrılan dosyalar hazır, kurguya uygulanmadı.", true);
};

// Ayrılmış konuşma klibi için kardeş dosyalar adla bulunur; kaynağa dönmeden ağ isteği gerekmez.
const kardesler = (c: Klip, kipi: StemKipi): Record<string, Stem> => {
  const k = useKurgu.getState();
  const yol = kaynakYolu(c)!, url = k.medya[c.kaynak!] ?? "", sure = k.kurgu!.kaynaklar[c.kaynak!].sure;
  const adlar = kipi === 4 ? Object.keys(ETIKET) : ["muzik"];
  return Object.fromEntries(adlar.map((ad) => [ad, { id: "", yol: yol.replace(".vokal.wav", `.${ad}.wav`), url: url.replace(".vokal.wav", `.${ad}.wav`), sure }]));
};

export const stemleriEkle = async (c: Klip, istenen: StemKipi) => {
  const yol = kaynakYolu(c);
  if (!yol) return;
  if (c.hiz !== 1) { useDepo.getState().bildir("Klipte hız %100 değil: ayrık sese hız uygulanmaz. Önce hızı %100 yap.", true); return; }
  await useKurgu.getState().kaydet();
  const ayrik = ayrilmisMi(c);
  const kipi: StemKipi = ayrik ? (yol.includes(".s4.") ? 4 : 2) : istenen;
  const s = ayrik ? kardesler(c, kipi) : await stemleriAl(yol, kipi);
  const liste = ["muzik", "davul", "bas", "diger"].filter((ad) => s[ad]).map((ad) => ({ ad: ETIKET[ad], id: stemId(c, kipi, ad), yol: s[ad].yol, sure: s[ad].sure, url: s[ad].url }));
  medyaYaz(Object.fromEntries(liste.map((x) => [x.id, x.url])));
  let n = 0;
  useKurgu.getState().duzenle("Ayrılan sesleri ekle", (d) => { n = K.stemEkle(d, c.id, liste); });
  useDepo.getState().bildir(`${n} ses kanalı sessiz izlere eklendi. Dinlemek için izlerin M düğmesini kapat.`);
};

export const sesiDosyayaCikar = async (c: Klip, bicim: string) => {
  const yol = kaynakYolu(c), p = useDepo.getState().aktif;
  if (!yol || !p) return;
  await useKurgu.getState().kaydet();
  const j = await istek("/api/isler", { method: "POST", json: { komut: "ses-cikar", studyo: p.studyo, ad: p.ad, yol, bicim } });
  const d = await bekle(j.id);
  if (d !== "bitti") throw new Error(ayrilanAd(d));
  const satir = (await istek<string[]>(`/api/isler/${j.id}/gunluk`)).filter((x) => x.startsWith("Ses: ")).at(-1);
  useDepo.getState().bildir(`Ses dosyası hazır: ${satir?.slice(5) ?? "ses klasörü"}`);
};
