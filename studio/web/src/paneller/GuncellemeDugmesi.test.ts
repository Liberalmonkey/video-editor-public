// WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md
import { expect, test } from "vitest";
import { gorunum, type GuncellemeDurum } from "./GuncellemeDugmesi";

const taban = (ek: Partial<GuncellemeDurum> = {}): GuncellemeDurum => ({
  destek: true,
  dal: "main",
  hedef: "origin/main",
  mevcut: "40bcff2",
  uzak: "40bcff2",
  geride: 0,
  ileride: 0,
  yeni: [],
  kirli: [],
  mesgul: [],
  son_kontrol: "2026-11-28T14:00:00",
  hata: null,
  calisiyor: false,
  son_sonuc: null,
  ...ek,
});

test("destek false ya da veri yokken düğme gizli", () => {
  expect(gorunum(null).tur).toBe("gizli");
  expect(gorunum(undefined).tur).toBe("gizli");
  expect(gorunum({ destek: false })).toEqual({ tur: "gizli", etiket: "", ipucu: "" });
});

test("geride 0 iken sönük Güncel görünümü ve son kontrol zamanı", () => {
  const g = gorunum(taban({ geride: 0, son_kontrol: "2026-11-28T14:00:00" }));
  expect(g.tur).toBe("guncel");
  expect(g.etiket).toBe("Güncel");
  expect(g.ipucu).toContain("2026-11-28 14:00");

  const kontrolsuz = gorunum(taban({ geride: 0, son_kontrol: null }));
  expect(kontrolsuz.tur).toBe("guncel");
  expect(kontrolsuz.ipucu.length).toBeGreaterThan(0);
});

test("geride > 0 iken Güncelle vurgusu", () => {
  const g = gorunum(taban({ geride: 3, uzak: "6d4b198" }));
  expect(g.tur).toBe("yeni");
  expect(g.etiket).toBe("Güncelle");
  expect(g.ipucu).toContain("3");
});

test("calisiyor true iken Güncelleniyor durumu baskındır", () => {
  const g = gorunum(taban({ calisiyor: true, geride: 3, hata: "geçici ağ hatası" }));
  expect(g.tur).toBe("calisiyor");
  expect(g.etiket).toBe("Güncelleniyor");
});

test("hata alanı doluysa uyarı durumu ve hata metni ipucunda", () => {
  const g = gorunum(taban({ geride: 0, hata: "origin erişilemiyor: ağ yok" }));
  expect(g.tur).toBe("hata");
  expect(g.ipucu).toBe("origin erişilemiyor: ağ yok");
});

test("son_sonuc yeniden_baslat true ise Yeniden başlat vurgulu görünür", () => {
  const g = gorunum(
    taban({
      geride: 0,
      son_sonuc: {
        ts: "20261128-140501",
        durum: "basarili",
        ozet: "3 commit alındı",
        korunan: ["library/kurallar/kurallar.json"],
        geri_alinabilir: true,
        yeniden_baslat: true,
      },
    }),
  );
  expect(g.tur).toBe("bitti");
  expect(g.etiket).toBe("Yeniden başlat");
  expect(g.ipucu).toBe("3 commit alındı");
});

test("son_sonuc yeniden_baslat false iken normal duruma düşer", () => {
  const g = gorunum(
    taban({
      geride: 0,
      son_sonuc: {
        ts: "20261128-140501",
        durum: "uyari",
        ozet: "İşlem tamamlandı",
        yeniden_baslat: false,
      },
    }),
  );
  expect(g.tur).toBe("guncel");
});
