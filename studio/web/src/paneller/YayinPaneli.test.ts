import { expect, test } from "vitest";
import { bolumAyir, etiketUzunlugu, hashtagAyir, kopyaMetni, sayacDurumu } from "./YayinPaneli";

test("kopyalanan metin sunucudaki biçimle aynı: açıklama, bölümler, hashtag satırı", () => {
  expect(kopyaMetni({ aciklama: "Metin ", bolumler: [{ t: "0:00", baslik: "Giriş" }], hashtagler: ["#a", "#b"] })).toBe("Metin\n\n0:00 Giriş\n\n#a #b");
  expect(kopyaMetni({ aciklama: "Metin", bolumler: [], hashtagler: [] })).toBe("Metin");
});

test("sayaç: sınırı aşan hata, görünen uzunluğu aşan uyarı", () => {
  expect(sayacDurumu(50, 100, 55)).toBe("iyi");
  expect(sayacDurumu(60, 100, 55)).toBe("uyari");
  expect(sayacDurumu(101, 100, 55)).toBe("hata");
});

test("hashtag, etiket ve bölüm ayrıştırma", () => {
  expect(hashtagAyir("#kurgu claude, ##ai")).toEqual(["#kurgu", "#claude", "#ai"]);
  expect(etiketUzunlugu(["ab", "c d"])).toBe(8); // yayin.etiket_uzunlugu ile aynı
  expect(bolumAyir("0:00 Giriş\nboş satır\n1:05:10 Son")).toEqual([{ t: "0:00", baslik: "Giriş" }, { t: "1:05:10", baslik: "Son" }]);
});
