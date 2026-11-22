import { expect, test } from "vitest";
import type { Aday, Alan } from "./tipler";
import { adimDurumu, dosyaUrl, kutuNormal, metinAlani, motorMetni, tasanAlanlar, videoUrl } from "./yardimci";

test("metin alanı ayırıcıyı satırın içinden temizler", () => {
  expect(metinAlani({ satir1: " a|b ", satir2: "c" })).toBe("a b|c");
});

test("taşan alan: iç alan dışına taşma ve dış alana girme", () => {
  const alanlar: Alan[] = [{ ad: "Kenar", kutu: [4, 5, 96, 95], tur: "ic" }, { ad: "Rozet", kutu: [80, 82, 100, 100], tur: "dis" }];
  expect(tasanAlanlar([10, 10, 50, 50], alanlar)).toEqual([]);
  expect(tasanAlanlar([2, 10, 50, 50], alanlar)).toEqual(["Kenar"]);
  expect(tasanAlanlar([70, 80, 90, 94], alanlar)).toEqual(["Rozet"]);
});

test("kutu: ters çizim düzelir, kenara kırpılır, küçük kutu tıklama sayılır", () => {
  expect(kutuNormal([60, 40], [20, 10])).toEqual([20, 10, 60, 40]);
  expect(kutuNormal([-5, 50], [130, 120])).toEqual([0, 50, 100, 100]);
  expect(kutuNormal([10, 10], [11, 50])).toBeNull();
  expect(kutuNormal([10.123, 10], [40.456, 30])).toEqual([10.12, 10, 40.46, 30]);
});

const aday = (k: Partial<Aday>): Aday => ({
  n: 1, yol: "", aci: null, v: 0, olcum: null, puan: null, elestiri: "", ebeveyn: null, zemin_kaynagi: "agy", duzeltme: "", kare: null,
  video: null, satir1: "", satir2: "", vurgu: "", yerlesim: "ust", olcek: 1, karart: false, kutu: false, kalip: "klasik", stil: "turuncu", ek: "", ...k,
});

test("adım durumu: ilk eksik adım sırada, gerisi bekler", () => {
  const bos = { kareler: [], oneri: null, brief: [], adaylar: [], secim: null };
  expect(adimDurumu(bos).map((a) => a.durum)).toEqual(["sirada", "bekliyor", "bekliyor", "bekliyor", "bekliyor"]);
  const uretildi = { ...bos, kareler: [{ n: 1, yol: "k", el: false }], brief: [{ sahne: "x" }], adaylar: [aday({})] };
  expect(adimDurumu(uretildi).map((a) => a.durum)).toEqual(["tamam", "tamam", "tamam", "sirada", "bekliyor"]);
  const teslim = { ...uretildi, adaylar: [aday({ ebeveyn: 1 })], secim: { n: 1, dosya: "kapak.jpg", eski: false } };
  expect(adimDurumu(teslim).every((a) => a.durum === "tamam")).toBe(true);
  expect(adimDurumu({ ...teslim, secim: { n: 1, dosya: "kapak.jpg", eski: true } }).at(-1)?.durum).toBe("sirada");
});

test("görsel motoru: kota açıkken model adı, kapalıyken açılış süresi", () => {
  expect(motorMetni({ model: "gemini-3.1-flash-image", kapali: false }).metin).toContain("gemini-3.1-flash-image");
  expect(motorMetni({ model: null }).metin).toContain("agy varsayılanı");
  const m = motorMetni({ model: "m", acilis: "2026-11-22T15:00:00Z", kapali: true }, new Date("2026-11-22T14:30:00Z"));
  expect(m.kapali).toBe(true);
  expect(m.metin).toContain("30 dk");
});

test("dosya ve video adresi parçaları kodlar", () => {
  const p = { studyo: "instagram", ad: "x" };
  expect(dosyaUrl(p, "outputs", "work/a b/k#1.jpg", 5)).toBe("/dosya/instagram/x/outputs/work/a%20b/k%231.jpg?v=5");
  expect(videoUrl(p, "inputs:1.1.mp4")).toBe("/dosya/instagram/x/inputs/1.1.mp4");
});
