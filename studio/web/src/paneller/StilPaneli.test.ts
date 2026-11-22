import { expect, test } from "vitest";
import {
  kabulUzantilari,
  nativeGrupla,
  varlikFiltrele,
  type NativeOge,
  type StilVarlikOge,
} from "./StilVarliklari";

const v = (id: string, tur: StilVarlikOge["tur"], ek: Partial<StilVarlikOge> = {}): StilVarlikOge => ({
  id,
  ad: id,
  tur,
  dosya: `varliklar/${tur}/${id}/${id}.webm`,
  orijinal: `varliklar/${tur}/${id}/orijinal.webm`,
  poster: null,
  yontem: "alfa",
  sure: 2,
  w: 1080,
  h: 1080,
  ne_zaman: "",
  etiketler: [],
  lisans: "Kendi üretimim",
  kaynak_url: "",
  atif: "",
  eklenme: "2026-11-21",
  kurgu_yolu: `stil:instagram/demo/varliklar/${tur}/${id}/${id}.webm`,
  onizleme_url: `/api/stil/instagram/demo/varlik/${id}/onizleme`,
  indir_url: `/api/stil/instagram/demo/varlik/${id}/indir`,
  ...ek,
});

const n = (ad: string, tur: string, ek: Partial<NativeOge> = {}): NativeOge => ({
  ad,
  tur,
  ne_zaman: "",
  sure: 2,
  etiketler: [],
  ...ek,
});

const VARLIKLAR: StilVarlikOge[] = [
  v("parlama", "motion", { ad: "Işık Parlaması", ne_zaman: "Hook girişinde", etiketler: ["ışık", "hook"] }),
  v("ok-ciz", "animasyon", { ad: "Çizim Ok", yontem: "lottie", ne_zaman: "Vurgu yaparken", etiketler: ["işaret"] }),
  v("maskot", "karakter", { ad: "Maskot İkon", yontem: "karakter_json", ne_zaman: "Açıklama anında" }),
  v("arka-kart", "gorsel", { ad: "Kâğıt Doku", yontem: "ham", etiketler: ["doku"] }),
  v("alkis", "ses", { ad: "İnce Alkış", yontem: "ham", ne_zaman: "Final kapanışta" }),
];

const NATIVELER: NativeOge[] = [
  n("tipografi/baslik", "tipografi", { ne_zaman: "Bölüm girişi", etiketler: ["başlık", "kinetik"] }),
  n("kart/cta-karti", "cta", { ne_zaman: "Abone çağrısı", etiketler: ["buton", "çağrı"] }),
  n("kart/altbant-blok", "altbant", { ne_zaman: "Konuşmacı adı" }),
  n("ikon/tik", "ikon", { ne_zaman: "Doğrulama anı", etiketler: ["onay", "işaret"] }),
  n("dis/lottie", "ikon", { ne_zaman: "Dış Lottie dosyası" }),
  n("veri/sayac", "veri", { ne_zaman: "Rakam artışı", etiketler: ["sayı", "istatistik"] }),
  n("cizim/ok", "cizim", { ne_zaman: "Hedefi gösterir" }),
  n("parcacik/konfeti", "parcacik", { ne_zaman: "Kutlama" }),
  n("cerceve/bant", "cerceve", { ne_zaman: "Kanıt gösterimi" }),
  n("zemin/izgara", "zemin", { ne_zaman: "Arka plan dokusu" }),
];

test("varlikFiltrele kategori çipleriyle doğru süzer", () => {
  expect(varlikFiltrele(VARLIKLAR, "", "").length).toBe(5);
  expect(varlikFiltrele(VARLIKLAR, "tumu", "").length).toBe(5);
  expect(varlikFiltrele(VARLIKLAR, "motion-animasyon", "").map((x) => x.id)).toEqual(["parlama", "ok-ciz"]);
  expect(varlikFiltrele(VARLIKLAR, "motion", "").map((x) => x.id)).toEqual(["parlama"]);
  expect(varlikFiltrele(VARLIKLAR, "animasyon", "").map((x) => x.id)).toEqual(["ok-ciz"]);
  expect(varlikFiltrele(VARLIKLAR, "karakter", "").map((x) => x.id)).toEqual(["maskot"]);
  expect(varlikFiltrele(VARLIKLAR, "gorsel", "").map((x) => x.id)).toEqual(["arka-kart"]);
  expect(varlikFiltrele(VARLIKLAR, "ses", "").map((x) => x.id)).toEqual(["alkis"]);
});

test("varlikFiltrele Türkçe-duyarlı çok kelimeli arama yapar", () => {
  expect(varlikFiltrele(VARLIKLAR, "", "IŞIK").map((x) => x.id)).toEqual(["parlama"]);
  expect(varlikFiltrele(VARLIKLAR, "", "İŞARET lottie").map((x) => x.id)).toEqual(["ok-ciz"]);
  expect(varlikFiltrele(VARLIKLAR, "", "İNCE kapanışta").map((x) => x.id)).toEqual(["alkis"]);
  expect(varlikFiltrele(VARLIKLAR, "karakter", "İkon").map((x) => x.id)).toEqual(["maskot"]);
  expect(varlikFiltrele(VARLIKLAR, "ses", "lottie")).toEqual([]);
});

test("nativeGrupla ailelere ve Türkçe aramaya göre süzer", () => {
  expect(nativeGrupla(NATIVELER, "", "").length).toBe(NATIVELER.length);
  expect(nativeGrupla(NATIVELER, "Hepsi", "").length).toBe(NATIVELER.length);
  expect(nativeGrupla(NATIVELER, "tipografi", "").map((x) => x.ad)).toEqual(["tipografi/baslik"]);
  expect(nativeGrupla(NATIVELER, "kart", "").map((x) => x.ad)).toEqual(["kart/cta-karti", "kart/altbant-blok"]);
  expect(nativeGrupla(NATIVELER, "ikon", "").map((x) => x.ad)).toEqual(["ikon/tik", "dis/lottie"]);
  expect(nativeGrupla(NATIVELER, "veri", "").map((x) => x.ad)).toEqual(["veri/sayac"]);
  expect(nativeGrupla(NATIVELER, "cizim", "").map((x) => x.ad)).toEqual(["cizim/ok"]);
  expect(nativeGrupla(NATIVELER, "parcacik", "").map((x) => x.ad)).toEqual(["parcacik/konfeti"]);
  expect(nativeGrupla(NATIVELER, "cerceve", "").map((x) => x.ad)).toEqual(["cerceve/bant"]);
  expect(nativeGrupla(NATIVELER, "zemin", "").map((x) => x.ad)).toEqual(["zemin/izgara"]);
  expect(nativeGrupla(NATIVELER, "", "İSTATİSTİK").map((x) => x.ad)).toEqual(["veri/sayac"]);
  expect(nativeGrupla(NATIVELER, "kart", "ÇAĞRISI").map((x) => x.ad)).toEqual(["kart/cta-karti"]);
});

test("kabulUzantilari türe göre doğru uzantı listesini döner", () => {
  const m = kabulUzantilari("motion").split(",");
  expect(m).toContain(".webm");
  expect(m).toContain(".lottie");
  expect(m).toContain(".svg");
  expect(kabulUzantilari("animasyon")).toBe(kabulUzantilari("motion"));

  const k = kabulUzantilari("karakter").split(",");
  expect(k).toContain(".json");
  expect(k).toContain(".png");
  expect(k).toContain(".webm");

  const g = kabulUzantilari("gorsel").split(",");
  expect(g).toEqual([".png", ".jpg", ".jpeg", ".webp", ".svg"]);

  const s = kabulUzantilari("ses").split(",");
  expect(s).toEqual([".wav", ".mp3", ".ogg", ".m4a", ".flac"]);

  expect(kabulUzantilari("bilinmeyen").split(",")).toContain(".wav");
  expect(kabulUzantilari("bilinmeyen").split(",")).toContain(".lottie");
});
