import { produce } from "immer";
import { describe, expect, it } from "vitest";
import * as K from "./komutlar";

const kaynak = { yol: "public:a.mp4", sure: 100, ses: true };
const temel = (ek: Partial<K.K> = {}): K.K => ({
  sekans: { w: 1080, h: 1920, fps: 30 }, kaynaklar: { A: kaynak }, kelimeler: {},
  izler: [
    { id: "V2", tur: "video", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
    { id: "V1", tur: "video", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
    { id: "A2", tur: "ses", ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 },
  ],
  klipler: [], altyazi: { acik: true, iz: "V1" }, isaretler: [], ...ek,
});
const klip = (k: K.K, id: string, iz: string, bas: number, sure: number, ek: any = {}) => ({ ...K.klipYap(k, { tur: "video", iz, bas, sure, kaynak: "A", giris: bas }), id, ...ek });
// a [0,10) b [10,20) c [20,30), kaynak zamanı sekansla aynı
const uclu = (ek: Partial<K.K> = {}) => { const k = temel(ek); k.klipler = [klip(k, "a", "V1", 0, 10), klip(k, "b", "V1", 10, 10), klip(k, "c", "V1", 20, 10)]; return k; };
const yap = (k: K.K, f: (d: K.K) => void) => { const s = produce(k, f); expect(K.cakisma(s)).toBeNull(); return s; };
const al = (k: K.K, id: string) => k.klipler.find((c) => c.id === id)!;
const dizi = (k: K.K, iz = "V1") => k.klipler.filter((c) => c.iz === iz).sort((a, b) => a.bas - b.bas).map((c) => [c.bas, c.sure, c.giris]);

describe("razor", () => {
  it("iki parça, kaynak sürekli", () => {
    expect(dizi(yap(uclu(), (d) => { K.kes(d, "a", 4); }))).toEqual([[0, 4, 0], [4, 6, 4], [10, 10, 10], [20, 10, 20]]);
  });
  it("hızı hesaba katar", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10, { hiz: 2, giris: 1 })];
    expect(dizi(yap(k, (d) => { K.kes(d, "a", 4); }))).toEqual([[0, 4, 1], [4, 6, 9]]);
  });
  it("uçta ve sahnede bölmez, kilidi aşmaz", () => {
    expect(yap(uclu(), (d) => { K.kes(d, "a", 0); K.kes(d, "a", 10); }).klipler).toHaveLength(3);
    const k = temel(); k.klipler = [klip(k, "s", "V1", 0, 10, { tur: "sahne", kaynak: null })];
    expect(yap(k, (d) => { K.kes(d, "s", 5); }).klipler).toHaveLength(1);
    const l = uclu(); l.izler[1].kilit = true;
    expect(yap(l, (d) => { K.kes(d, "a", 5); }).klipler).toHaveLength(3);
  });
  it("keyframe'ler parçasına gider", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10)];
    k.klipler[0].donus.opaklik = [{ t: 2, v: 0, ease: "dogrusal" }, { t: 6, v: 1, ease: "dogrusal" }];
    const s = yap(k, (d) => { K.kes(d, "a", 4); });
    const sag = s.klipler.find((c) => c.id !== "a")!;
    // Kesimde değer korunur: animasyon sıçramaz.
    expect(al(s, "a").donus.opaklik.map((f) => [f.t, f.v])).toEqual([[2, 0], [4, 0.5]]);
    expect(sag.donus.opaklik.map((f) => [f.t, f.v])).toEqual([[0, 0.5], [2, 1]]);
  });
  it("kafada keser: seçim yoksa tüm izler, seçim varsa yalnız o", () => {
    const k = uclu(); k.klipler.push(klip(k, "u", "V2", 0, 30));
    expect(yap(k, (d) => K.kafadaKes(d, 5, [])).klipler).toHaveLength(6);
    expect(yap(k, (d) => K.kafadaKes(d, 5, ["u"])).klipler).toHaveLength(5);
  });
});

describe("silme", () => {
  it("sil boşluk bırakır", () => { expect(dizi(yap(uclu(), (d) => K.sil(d, ["b"])))).toEqual([[0, 10, 0], [20, 10, 20]]); });
  it("ripple sil boşluğu kapatır", () => { expect(dizi(yap(uclu(), (d) => K.rippleSil(d, ["b"])))).toEqual([[0, 10, 0], [10, 10, 20]]); });
  it("ripple sil diğer izi senkron tutar: video bölünür, müzik kısalır, SFX gider ya da kayar", () => {
    const k = uclu();
    k.klipler.push(klip(k, "ust", "V2", 5, 20));
    k.klipler.push(klip(k, "muzik", "A2", 0, 40, { tur: "ses", olay: { muzik: true }, kaynak: null }));
    const s = yap(k, (d) => K.rippleSil(d, ["b"]));
    expect(dizi(s, "V2")).toEqual([[5, 5, 5], [10, 5, 20]]);
    expect(dizi(s, "A2")).toEqual([[0, 30, 0]]);
  });
  it("SFX aralıktaysa gider, sonrasındaysa kayar", () => {
    const k = uclu(); k.klipler.push(klip(k, "s1", "A2", 12, 1, { tur: "ses", kaynak: null }), klip(k, "s2", "A2", 25, 1, { tur: "ses", kaynak: null }));
    expect(dizi(yap(k, (d) => K.rippleSil(d, ["b"])), "A2")).toEqual([[15, 1, 25]]);
  });
  it("kilitli iz kaymaz, kilitli klip silinmez", () => {
    const k = uclu(); k.klipler.push(klip(k, "u", "V2", 25, 2)); k.izler[0].kilit = true;
    const s = yap(k, (d) => K.rippleSil(d, ["b", "u"]));
    expect(dizi(s, "V2")).toEqual([[25, 2, 25]]);
    expect(dizi(s)).toEqual([[0, 10, 0], [10, 10, 20]]);
  });
  it("çoklu ripple", () => { expect(dizi(yap(uclu(), (d) => K.rippleSil(d, ["a", "c"])))).toEqual([[0, 10, 10]]); });
  it("aralık silme klibi içinden böler", () => {
    expect(dizi(yap(uclu(), (d) => K.aralikSil(d, 5, 15)))).toEqual([[0, 5, 0], [5, 5, 15], [10, 10, 20]]);
  });
});

describe("taşıma", () => {
  it("üzerine yazar: tam örtülen gider, kısmi kırpılır", () => {
    const s = yap(uclu(), (d) => K.tasi(d, ["c"], -15, 0));
    expect(dizi(s)).toEqual([[0, 5, 0], [5, 10, 20], [15, 5, 15]]);
  });
  it("ortayı delerse klip ikiye bölünür", () => {
    const k = temel(); k.klipler = [klip(k, "uzun", "V1", 0, 30), klip(k, "kisa", "V2", 10, 5, { giris: 50 })];
    const s = yap(k, (d) => K.tasi(d, ["kisa"], 0, 1));
    expect(dizi(s)).toEqual([[0, 10, 0], [10, 5, 50], [15, 15, 15]]);
    expect(dizi(s, "V2")).toEqual([]);
  });
  it("sıfırın altına ve ses izine geçmez", () => {
    const s = yap(uclu(), (d) => K.tasi(d, ["a"], -5, 2));
    expect(al(s, "a").bas).toBe(0);
    expect(al(s, "a").iz).toBe("V1");
  });
  it("kilitli hedef ize taşımaz", () => {
    const k = uclu(); k.izler[0].kilit = true;
    expect(al(yap(k, (d) => K.tasi(d, ["a"], 0, -1)), "a").iz).toBe("V1");
  });
  it("insert yer açar, üzerine yazmaz", () => {
    const k = uclu(); k.klipler.push(klip(k, "x", "V2", 40, 5, { giris: 70 }));
    const s = yap(k, (d) => K.tasi(d, ["x"], -35, 1, true));
    expect(dizi(s)).toEqual([[0, 5, 0], [5, 5, 70], [10, 5, 5], [15, 10, 10], [25, 10, 20]]);
  });
  it("birlikte taşır, kendi eski yerine çarpmaz", () => {
    expect(dizi(yap(uclu(), (d) => K.tasi(d, ["a", "b"], 2, 0)))).toEqual([[2, 10, 0], [12, 10, 10], [22, 8, 22]]);
  });
  it("kendi üstüne küçük kayma klibi kaybetmez", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 5, 10)];
    expect(dizi(yap(k, (d) => K.tasi(d, ["a"], 3, 0)))).toEqual([[8, 10, 5]]);
  });
});

describe("kırpma", () => {
  it("son: komşuya ve kaynağa dayanır", () => {
    expect(al(yap(uclu(), (d) => K.kirp(d, "a", "son", 5)), "a").sure).toBe(10);
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10, { giris: 95 })];
    expect(al(yap(k, (d) => K.kirp(d, "a", "son", 50)), "a").sure).toBe(10); // kaynak 100, giris 95: uzun klip küçülmeye zorlanmaz
    const l = temel(); l.klipler = [klip(l, "a", "V1", 0, 2, { giris: 95 })];
    expect(al(yap(l, (d) => K.kirp(d, "a", "son", 50)), "a").sure).toBe(5);
  });
  it("baş: kaynak ve komşu sınırı, giriş izler", () => {
    const s = yap(uclu(), (d) => K.kirp(d, "b", "bas", 3));
    expect([al(s, "b").bas, al(s, "b").sure, al(s, "b").giris]).toEqual([13, 7, 13]);
    expect(al(yap(s, (d) => K.kirp(d, "b", "bas", -100)), "b").bas).toBe(10);
    const k = temel(); k.klipler = [klip(k, "a", "V1", 10, 5, { giris: 2 })];
    expect(al(yap(k, (d) => K.kirp(d, "a", "bas", -100)), "a").bas).toBe(8);
  });
  it("en az bir kare kalır", () => {
    const s = yap(uclu(), (d) => K.kirp(d, "b", "bas", 999));
    expect(al(s, "b").sure).toBeCloseTo(1 / 30);
    expect(al(yap(uclu(), (d) => K.kirp(d, "b", "son", -999)), "b").sure).toBeCloseTo(1 / 30);
  });
  it("görsel süresiz uzar", () => {
    const k = temel({ kaynaklar: { G: { yol: "inputs:g.png", sure: 0, ses: false } } });
    k.klipler = [{ ...K.klipYap(k, { tur: "gorsel", iz: "V1", bas: 0, sure: 5, kaynak: "G" }), id: "g" }];
    expect(al(yap(k, (d) => K.kirp(d, "g", "son", 100)), "g").sure).toBe(105);
  });
});

describe("ripple kırpma", () => {
  it("son: sonrakiler kayar, boşluk açılmaz", () => {
    expect(dizi(yap(uclu(), (d) => K.rippleKirp(d, "a", "son", -4)))).toEqual([[0, 6, 0], [6, 10, 10], [16, 10, 20]]);
  });
  it("baş: yer sabit, giriş değişir, sonrakiler kayar", () => {
    expect(dizi(yap(uclu(), (d) => K.rippleKirp(d, "b", "bas", 3)))).toEqual([[0, 10, 0], [10, 7, 13], [17, 10, 20]]);
  });
  it("kilitli izi kaydırmaz", () => {
    const k = uclu(); k.klipler.push(klip(k, "u", "V2", 15, 2)); k.izler[0].kilit = true;
    expect(dizi(yap(k, (d) => K.rippleKirp(d, "a", "son", -4)), "V2")).toEqual([[15, 2, 15]]);
  });
});

describe("ripple kırpma, diğer izde uzun klip", () => {
  it("sonraki klip uzun klibin altına girmez, iz senkron kalır", () => {
    const k = uclu();
    k.klipler.push(klip(k, "uzun", "V2", 0, 30), klip(k, "sonra", "V2", 30, 5));
    const s = yap(k, (d) => K.rippleKirp(d, "a", "son", -4));
    expect(dizi(s, "V2")).toEqual([[0, 6, 0], [6, 20, 10], [26, 5, 30]]);
  });
  it("sürekli içerik (müzik) kısalır, bölünmez", () => {
    const k = uclu(); k.klipler.push(klip(k, "m", "A2", 0, 40, { tur: "ses", kaynak: null, olay: { muzik: true } }));
    expect(dizi(yap(k, (d) => K.rippleKirp(d, "a", "son", -4)), "A2")).toEqual([[0, 36, 0]]);
  });
  it("insert sürekli içeriğin üstüne bindirmez", () => {
    const k = temel(); k.klipler = [klip(k, "g", "V1", 0, 20, { tur: "gorsel" })];
    yap(k, (d) => { K.klipEkle(d, { tur: "video", iz: "V1", bas: 5, sure: 2, kaynak: "A" }, true); });
  });
});

describe("rolling, slip, slide", () => {
  it("rolling toplam süreyi korur", () => {
    const s = yap(uclu(), (d) => K.rolling(d, "a", "b", 3));
    expect(dizi(s)).toEqual([[0, 13, 0], [13, 7, 13], [20, 10, 20]]);
  });
  it("rolling sınırda durur", () => {
    expect(dizi(yap(uclu(), (d) => K.rolling(d, "a", "b", -5)))[1]).toEqual([5, 15, 5]);
    expect(al(yap(uclu(), (d) => K.rolling(d, "a", "b", 999)), "b").sure).toBeCloseTo(1 / 30);
  });
  it("slip yeri korur, kaynak sınırında durur", () => {
    expect(dizi(yap(uclu(), (d) => K.slip(d, "b", 5)))[1]).toEqual([10, 10, 15]);
    expect(al(yap(uclu(), (d) => K.slip(d, "b", -100)), "b").giris).toBe(0);
    expect(al(yap(uclu(), (d) => K.slip(d, "b", 500)), "b").giris).toBe(90);
  });
  it("slide içeriği korur, komşular uyum sağlar", () => {
    expect(dizi(yap(uclu(), (d) => K.slide(d, "b", 3)))).toEqual([[0, 13, 0], [13, 10, 10], [23, 7, 23]]);
    expect(dizi(yap(uclu(), (d) => K.slide(d, "b", -3)))).toEqual([[0, 7, 0], [7, 10, 10], [17, 13, 17]]);
  });
  it("slide komşuyu yok etmez", () => {
    const s = yap(uclu(), (d) => K.slide(d, "b", 999));
    expect(al(s, "c").sure).toBeCloseTo(1 / 30);
  });
});

describe("bağlı klipler", () => {
  it("bağla, birlikte seç, ayır", () => {
    let k = uclu();
    k = yap(k, (d) => K.bagla(d, ["a", "c"]));
    expect(K.baglilar(k, ["a"]).sort()).toEqual(["a", "c"]);
    expect(K.baglilar(k, ["b"])).toEqual(["b"]);
    k = yap(k, (d) => K.bagla(d, ["a", "c"]));
    expect(K.baglilar(k, ["a"])).toEqual(["a"]);
  });
  it("bölünen parça bağı taşımaz", () => {
    let k = yap(uclu(), (d) => K.bagla(d, ["a", "c"]));
    k = yap(k, (d) => { K.kes(d, "a", 5); });
    expect(K.baglilar(k, ["c"]).sort()).toEqual(["a", "c"]);
  });
});

describe("görüntü ve sesi ayırma", () => {
  const ayrik = (ek: any = {}) => {
    const k = temel(); k.klipler = [klip(k, "v", "V1", 2, 10, ek)];
    const s = yap(k, (d) => { K.sesiAyir(d, ["v"]); });
    return { s, ses: s.klipler.find((c) => c.tur === "ses")! };
  };
  it("sesi aynı yerde ve kaynak anında bağlı klibe çıkarır, A1 ses izlerinin başına gelir", () => {
    const { s, ses } = ayrik({ giris: 3 });
    expect(al(s, "v").ses_kapali).toBe(true);
    expect([ses.bas, ses.sure, ses.giris, ses.kaynak, ses.iz]).toEqual([2, 10, 3, "A", "A1"]);
    expect(ses.bag).toBe(al(s, "v").bag);
    expect(ses.olay).toEqual({ konusma: true });
    expect(s.izler.map((i) => i.id)).toEqual(["V2", "V1", "A1", "A2"]);
  });
  it("iz kazancı klibe geçer, birleştirince geri döner", () => {
    const k = temel(); k.izler[1].gain_db = -6; k.klipler = [klip(k, "v", "V1", 0, 5)]; k.klipler[0].ses.gain_db = 2;
    const s = yap(k, (d) => { K.sesiAyir(d, ["v"]); });
    expect(s.klipler.find((c) => c.tur === "ses")!.ses.gain_db).toBe(-4);
    const b = yap(s, (d) => { K.sesiBirlestir(d, ["v"]); });
    expect(b.klipler).toHaveLength(1);
    expect([al(b, "v").ses_kapali, al(b, "v").ses.gain_db, al(b, "v").bag]).toEqual([false, 2, null]);
  });
  it("hızlı ve sessiz kaynak ayrılmaz, ayrılmış klip yeniden ayrılmaz", () => {
    let r: any;
    const k = temel(); k.klipler = [klip(k, "v", "V1", 0, 5, { hiz: 2 })];
    yap(k, (d) => { r = K.sesiAyir(d, ["v"]); });
    expect(r).toEqual({ yeni: [], hizli: 1 });
    const m = temel({ kaynaklar: { A: { ...kaynak, ses: false } } }); m.klipler = [klip(m, "v", "V1", 0, 5)];
    yap(m, (d) => { r = K.sesiAyir(d, ["v"]); });
    expect(r.yeni).toHaveLength(0);
    const { s } = ayrik();
    expect(yap(s, (d) => { K.sesiAyir(d, ["v"]); }).klipler).toHaveLength(2);
  });
  it("SFX ve müzik izine karışmaz, aynı anda iki video iki ayrı iz açar", () => {
    const k = temel(); k.klipler = [klip(k, "v", "V1", 0, 5), klip(k, "u", "V2", 0, 5)];
    const s = yap(k, (d) => { K.sesiAyir(d, ["v", "u"]); });
    const izler = s.klipler.filter((c) => c.tur === "ses").map((c) => c.iz);
    expect(new Set(izler).size).toBe(2);
    expect(izler).not.toContain("A2");
  });
  it("bölme iki tarafı aynı anda keser, sağ parçalar birbirine bağlı kalır", () => {
    const { s, ses } = ayrik();
    const b = yap(s, (d) => { K.kes(d, "v", 6); });
    expect(b.klipler).toHaveLength(4);
    const sagV = b.klipler.find((c) => c.tur === "video" && c.bas === 6)!, sagS = b.klipler.find((c) => c.tur === "ses" && c.bas === 6)!;
    expect(sagV.bag).toBe(sagS.bag);
    expect(sagV.bag).not.toBe(ses.bag);
    expect(sagS.giris).toBe(sagV.giris);
    expect(K.baglilar(b, ["v"]).sort()).toEqual(["v", ses.id].sort());
  });
  it("kırpma ve ripple kırpma eşi izler, senkron kaymaz", () => {
    for (const f of [K.kirp, K.rippleKirp]) for (const kenar of ["bas", "son"] as const) for (const dt of [1.5, -1]) {
      const { s, ses } = ayrik({ giris: 5 });
      const b = yap(s, (d) => f(d, "v", kenar, dt));
      const v = al(b, "v"), a = al(b, ses.id);
      expect([a.bas, a.sure, a.giris]).toEqual([v.bas, v.sure, v.giris]);
      expect(a.bag).toBe(v.bag);
    }
  });
  it("ripple kırpma sonraki bağlı çifti de hizalı kaydırır", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10), klip(k, "b", "V1", 10, 10)];
    const s = yap(k, (d) => { K.sesiAyir(d, ["a", "b"]); });
    const r = yap(s, (d) => K.rippleKirp(d, "a", "son", -4));
    const v = r.klipler.filter((c) => c.tur === "video").sort((x, y) => x.bas - y.bas), a = r.klipler.filter((c) => c.tur === "ses").sort((x, y) => x.bas - y.bas);
    expect(a.map((c) => [c.bas, c.sure])).toEqual(v.map((c) => [c.bas, c.sure]));
    expect(a.map((c) => [c.bas, c.sure])).toEqual([[0, 6], [6, 10]]);
  });
  it("ripple silme ayrık sesi SFX gibi düşürmez", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10), klip(k, "b", "V1", 10, 10)];
    const s = yap(k, (d) => { K.sesiAyir(d, ["a", "b"]); });
    const r = yap(s, (d) => K.rippleSil(d, K.baglilar(d, ["a"])));
    expect(r.klipler.map((c) => [c.tur, c.bas, c.sure]).sort()).toEqual([["ses", 0, 10], ["video", 0, 10]]);
  });
  it("slip eşi de kaydırır; hız kilitlidir", () => {
    const { s, ses } = ayrik({ giris: 5 });
    const b = yap(s, (d) => K.slip(d, "v", 2));
    expect(al(b, ses.id).giris).toBe(al(b, "v").giris);
    expect(al(yap(s, (d) => K.hizAyarla(d, "v", 2)), "v").hiz).toBe(1);
  });
  it("tek başına taşınan ses eş olmaktan çıkar, birleşemez, kırpımı ayrılır", () => {
    const { s, ses } = ayrik();
    const b = yap(s, (d) => K.tasi(d, [ses.id], 0.4, 0));
    let r: any;
    const c = yap(b, (d) => { r = K.sesiBirlestir(d, ["v"]); });
    expect(r).toEqual({ birlesen: 0, kayik: 1 });
    expect(c.klipler).toHaveLength(2);
    expect(al(yap(b, (d) => K.kirp(d, "v", "son", -2)), ses.id).sure).toBe(10);
  });
  it("altyazı sesi izler", () => {
    const k = temel({ kelimeler: { A: [{ w: "x", s: 1, e: 2 }] } }); k.klipler = [klip(k, "v", "V1", 0, 5)];
    const s = yap(k, (d) => { K.sesiAyir(d, ["v"]); });
    const sesId = s.klipler.find((c) => c.tur === "ses")!.id;
    expect(K.kelimeSatirlari(s).map((w) => [w.klip, w.s])).toEqual([[sesId, 1]]);
    const b = yap(s, (d) => K.tasi(d, [sesId], 3, 0));
    expect(K.kelimeSatirlari(b).map((w) => w.s)).toEqual([4]);
    expect(K.kelimeSatirlari(yap(s, (d) => K.sil(d, [sesId])))).toEqual([]);
  });
});

describe("sekans ve ses kontrolü", () => {
  it("boş kurguya gelen yatay video sekansı yataya çevirir, kare dikey kalır", () => {
    const k = temel();
    const s = yap(k, (d) => { expect(K.sekansKaynaktan(d, 1920, 1080)).toBe("16:9"); });
    expect(s.sekans).toMatchObject({ w: 1920, h: 1080, fps: 30 });
    yap(k, (d) => { expect(K.sekansKaynaktan(d, 1080, 1080)).toBeNull(); expect(K.sekansKaynaktan(d, null, null)).toBeNull(); });
  });
  it("bölünmüş sahne altındaki videoyu konuşmacı düzenine alır, tam ekran sahne almaz", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 5), klip(k, "b", "V1", 5, 5)];
    const s = yap(k, (d) => { K.sahneEkle(d, 6, { layout: "split", kind: "stat" }, 2); });
    expect([al(s, "a").konusmaci, al(s, "b").konusmaci]).toEqual([false, true]);
    expect(al(yap(k, (d) => { K.sahneEkle(d, 6, { layout: "full", kind: "hook" }, 2); }), "b").konusmaci).toBe(false);
  });
  it("kazanç yarım dB adımla, sınırda, yalnız sesli klipte ve kilide saygılı", () => {
    const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 5), klip(k, "g", "V2", 0, 5, { tur: "gorsel" })];
    let s = yap(k, (d) => K.kazancEkle(d, ["a", "g"], 1.3));
    expect([al(s, "a").ses.gain_db, al(s, "g").ses.gain_db]).toEqual([1.5, 0]);
    expect(al(yap(k, (d) => K.kazancYaz(d, "a", 99)), "a").ses.gain_db).toBe(24);
    const l = temel(); l.izler[1].kilit = true; l.klipler = [klip(l, "a", "V1", 0, 5)];
    expect(al(yap(l, (d) => K.kazancYaz(d, "a", 6)), "a").ses.gain_db).toBe(0);
    s = yap(k, (d) => { K.sesiAyir(d, ["a"]); });
    expect(K.sesli(s, al(s, "a"))).toBe(false);
  });
});

describe("Q/W ve ekleme", () => {
  it("q kafaya kadar olan kısmı siler", () => {
    expect(dizi(yap(uclu(), (d) => K.qw(d, 14, "q", [])))).toEqual([[0, 10, 0], [10, 6, 14], [16, 10, 20]]);
  });
  it("w kafadan sonrasını siler", () => {
    expect(dizi(yap(uclu(), (d) => K.qw(d, 14, "w", [])))).toEqual([[0, 10, 0], [10, 4, 10], [14, 10, 20]]);
  });
  it("overwrite ve insert ekleme", () => {
    const y = { tur: "video" as const, iz: "V1", bas: 5, sure: 2, kaynak: "A", giris: 50 };
    expect(dizi(yap(uclu(), (d) => { K.klipEkle(d, y); }))).toEqual([[0, 5, 0], [5, 2, 50], [7, 3, 7], [10, 10, 10], [20, 10, 20]]);
    expect(dizi(yap(uclu(), (d) => { K.klipEkle(d, y, true); }))).toEqual([[0, 5, 0], [5, 2, 50], [7, 5, 5], [12, 10, 10], [22, 10, 20]]);
  });
  it("kilitli ize eklemez", () => {
    const k = uclu(); k.izler[1].kilit = true;
    expect(yap(k, (d) => { K.klipEkle(d, { tur: "video", iz: "V1", bas: 40, sure: 2 }); }).klipler).toHaveLength(3);
  });
});

describe("izler ve yapışma", () => {
  it("video üste, ses alta; dolu ve son iz silinmez", () => {
    let k = temel();
    k = yap(k, (d) => { K.izEkle(d, "video"); K.izEkle(d, "ses"); });
    expect(k.izler.map((i) => i.id)).toEqual(["V3", "V2", "V1", "A2", "A1"]);
    k = uclu();
    expect(produce(k, (d) => { expect(K.izSil(d, "V1")).toBe(false); expect(K.izSil(d, "A2")).toBe(false); expect(K.izSil(d, "V2")).toBe(true); }).izler).toHaveLength(2);
  });
  it("eşik içinde en yakın", () => {
    expect(K.yapis(10.1, [0, 10, 10.2, 30], 0.3)).toBe(10.2);
    expect(K.yapis(5, [0, 10], 0.3)).toBeNull();
  });
  it("kesim noktaları, hariç ve işaret", () => {
    const k = uclu({ isaretler: [{ t: 7, ad: "" }] });
    expect(K.kesimNoktalari(k, ["a"])).toEqual([0, 7, 10, 20, 30]);
  });
});

describe("efekt komutları", () => {
  const tek = () => { const k = temel(); k.klipler = [klip(k, "a", "V1", 0, 10)]; return k; };
  it("sabit değer tek kalır, oynatma kafası değiştirmez", () => {
    let k = yap(tek(), (d) => K.degerYaz(d, "a", "olcek", 3, 1.5));
    k = yap(k, (d) => K.degerYaz(d, "a", "olcek", 7, 2));
    expect(al(k, "a").donus.olcek).toEqual([{ t: 0, v: 2, ease: "dogrusal" }]);
  });
  it("animasyon açılınca keyframe yazar, aynı karede günceller", () => {
    let k = yap(tek(), (d) => K.animDegistir(d, "a", "olcek", 2, 1));
    k = yap(k, (d) => K.degerYaz(d, "a", "olcek", 6, 2));
    k = yap(k, (d) => K.degerYaz(d, "a", "olcek", 2.001, 1.5));
    expect(al(k, "a").donus.olcek.map((f) => [f.t, f.v])).toEqual([[2, 1.5], [6, 2]]);
  });
  it("animasyon kapanınca o anki değer sabit olur", () => {
    let k = yap(tek(), (d) => { K.animDegistir(d, "a", "x", 0, 0); K.degerYaz(d, "a", "x", 4, 100); });
    k = yap(k, (d) => K.animDegistir(d, "a", "x", 2, 0));
    expect(al(k, "a").donus.x).toEqual([{ t: 0, v: 50, ease: "dogrusal" }]);
    expect(al(k, "a").donus.anim).toEqual([]);
  });
  it("sabit değer baş kırpma ve razor'da kaybolmaz", () => {
    let k = yap(tek(), (d) => K.degerYaz(d, "a", "olcek", 0, 2));
    k = yap(k, (d) => K.kirp(d, "a", "bas", 3));
    expect(al(k, "a").donus.olcek).toEqual([{ t: 0, v: 2, ease: "dogrusal" }]);
    k = yap(k, (d) => { K.kes(d, "a", 5); });
    for (const c of k.klipler) expect(c.donus.olcek[0].v).toBe(2);
  });
  it("baş kırpma animasyonun değerini korur", () => {
    let k = yap(tek(), (d) => { K.animDegistir(d, "a", "x", 0, 0); K.degerYaz(d, "a", "x", 10, 100); });
    k = yap(k, (d) => K.kirp(d, "a", "bas", 4));
    expect(al(k, "a").donus.x.map((f) => [f.t, f.v])).toEqual([[0, 40], [6, 100]]);
  });
  it("pişirilen açı ve bulanıklık keyframe'leri baş kırpmada içerikte yerinde kalır", () => {
    let k = yap(tek(), (d) => {
      const c = d.klipler.find((x) => x.id === "a")!;
      c.donus.aci = [{ t: 0, v: 0, ease: "dogrusal" }, { t: 10, v: 100, ease: "dogrusal" }];
      c.efekt.bulanik_kf = [{ t: 0, v: 0, ease: "dogrusal" }, { t: 10, v: 50, ease: "dogrusal" }];
    });
    k = yap(k, (d) => K.kirp(d, "a", "bas", 4));
    expect(al(k, "a").donus.aci!.map((f) => [f.t, f.v])).toEqual([[0, 40], [6, 100]]);
    expect(al(k, "a").efekt.bulanik_kf!.map((f) => [f.t, f.v])).toEqual([[0, 20], [6, 50]]);
  });
  it("keyframe aç kapa, taşı, eğri", () => {
    let k = yap(tek(), (d) => { K.animDegistir(d, "a", "y", 1, 0); K.kfDegistir(d, "a", "y", 3, 0); });
    expect(al(k, "a").donus.y.map((f) => f.t)).toEqual([1, 3]);
    k = yap(k, (d) => K.kfTasi(d, "a", "y", 3, 99));
    expect(al(k, "a").donus.y[1].t).toBe(10);
    k = yap(k, (d) => K.kfEgri(d, "a", "y", 1, "yumusak"));
    expect(al(k, "a").donus.y[0].ease).toBe("yumusak");
    k = yap(k, (d) => K.kfDegistir(d, "a", "y", 1, 0));
    expect(al(k, "a").donus.y.map((f) => f.t)).toEqual([10]);
  });
  it("hız kaynak aralığını korur", () => {
    let k = yap(tek(), (d) => K.hizAyarla(d, "a", 2));
    expect([al(k, "a").sure, al(k, "a").hiz]).toEqual([5, 2]);
    k = yap(k, (d) => K.hizAyarla(d, "a", 0.5));
    expect(al(k, "a").sure).toBe(20);
  });
  it("yavaşlatma sonraki klibe dayanır, keyframe içerikle gider", () => {
    const u = uclu(); u.klipler[0].donus.x = [{ t: 0, v: 0, ease: "dogrusal" }, { t: 5, v: 1, ease: "dogrusal" }];
    const s = yap(u, (d) => K.hizAyarla(d, "a", 0.5));
    expect(al(s, "a").sure).toBe(10);
    expect(al(s, "a").donus.x[1].t).toBe(10);
  });
});

describe("üst katman ekleme", () => {
  it("metin dolu izi ezmez, boş iz yoksa yeni iz açar", () => {
    const k = uclu(); k.klipler.push(klip(k, "u", "V2", 0, 30));
    const s = yap(k, (d) => { K.metinEkle(d, 5, "x"); });
    expect(s.klipler.find((c) => c.tur === "metin")!.iz).toBe("V3");
    expect(s.klipler).toHaveLength(5);
    expect(s.izler[0].id).toBe("V3");
  });
  it("aralığı boş en üst izi kullanır", () => {
    const k = uclu(); k.klipler.push(klip(k, "u", "V2", 20, 5));
    expect(yap(k, (d) => { K.metinEkle(d, 5, "x"); }).klipler.find((c) => c.tur === "metin")!.iz).toBe("V2");
  });
  it("kilitli izi atlar", () => {
    const k = uclu(); k.izler[0].kilit = true;
    expect(yap(k, (d) => { K.metinEkle(d, 5, "x"); }).klipler.find((c) => c.tur === "metin")!.iz).toBe("V3");
  });
});

describe("altyazı kelimeleri", () => {
  const k0 = () => {
    const k = temel({ kelimeler: { A: [{ w: "bir", s: 1, e: 2 }, { w: "iki", s: 3, e: 4 }, { w: "üç", s: 12, e: 13 }] } });
    k.klipler = [klip(k, "a", "V1", 100, 10, { giris: 2 })];
    return k;
  };
  it("yalnız görünen kelimeler, sekans zamanıyla", () => {
    expect(K.kelimeSatirlari(k0()).map((x) => [x.w, x.s, x.i])).toEqual([["iki", 101, 1]]);
  });
  it("metin ve silme kaynakta olur, kesilen parçalar birlikte görür", () => {
    let k = yap(k0(), (d) => K.kelimeYaz(d, "A", 1, "İKİ"));
    expect(K.kelimeSatirlari(k)[0].w).toBe("İKİ");
    k = yap(k, (d) => K.kelimeSil(d, "A", 0));
    expect(k.kelimeler!.A.map((w) => w.w)).toEqual(["İKİ", "üç"]);
  });
  it("zaman komşuyu geçmez, sıfıra inmez", () => {
    const k = yap(k0(), (d) => K.kelimeZaman(d, "A", 1, -99, 99));
    expect([k.kelimeler!.A[1].s, k.kelimeler!.A[1].e]).toEqual([2, 12]);
    const l = yap(k0(), (d) => K.kelimeZaman(d, "A", 1, 5, -5));
    expect([l.kelimeler!.A[1].s, l.kelimeler!.A[1].e]).toEqual([3, 4]);
  });
});

// Rastgele komut dizisi: hangi sırada olursa olsun çakışma ya da sıfır süre doğmamalı.
describe("değişmez", () => {
  it("rastgele 3000 komut sonrası çakışma yok", () => {
    let t = 12345;
    const r = (n: number) => { t = (t * 1103515245 + 12345) & 0x7fffffff; return t % n; };
    let k = uclu();
    k.klipler.push(klip(k, "u", "V2", 3, 9), klip(k, "s", "A2", 2, 1, { tur: "ses", kaynak: null }), klip(k, "m", "A2", 6, 40, { tur: "ses", kaynak: null, olay: { muzik: true } }));
    for (let i = 0; i < 3000; i++) {
      const c = k.klipler[r(Math.max(1, k.klipler.length))];
      if (!c) break;
      const dt = (r(400) - 200) / 30, kenar = r(2) ? "bas" : "son";
      const once = k, tur = r(10);
      k = produce(k, (d) => {
        switch (tur) {
          case 0: K.kes(d, c.id, c.bas + r(100) / 10); break;
          case 1: K.kirp(d, c.id, kenar as any, dt); break;
          case 2: K.rippleKirp(d, c.id, kenar as any, dt); break;
          case 3: K.slip(d, c.id, dt); break;
          case 4: K.slide(d, c.id, dt); break;
          case 5: K.tasi(d, [c.id], dt, r(3) - 1, !!r(2)); break;
          case 6: K.rippleSil(d, [c.id]); break;
          case 7: K.klipEkle(d, { tur: "video", iz: "V1", bas: r(300) / 10, sure: 1 + r(50) / 10, kaynak: "A", giris: r(50) }, !!r(2)); break;
          case 8: K.qw(d, r(500) / 10, r(2) ? "q" : "w", []); break;
          case 9: { const l = d.klipler.filter((x) => x.iz === c.iz).sort((a, b) => a.bas - b.bas); const n = l.findIndex((x) => x.id === c.id); if (l[n + 1] && Math.abs(l[n].bas + l[n].sure - l[n + 1].bas) < 1e-6) K.rolling(d, c.id, l[n + 1].id, dt); }
        }
      });
      const c0 = K.cakisma(k);
      if (c0) {
        const oz = (x: K.K) => x.klipler.map((q) => `${q.id.slice(-3)}:${q.iz}:${q.tur}:${q.olay?.muzik ? "m" : ""}[${q.bas.toFixed(3)},${(q.bas + q.sure).toFixed(3)}]`).sort().join(" ");
        throw new Error(`komut ${i} tur ${tur} klip ${c.id.slice(-3)} dt ${dt} kenar ${kenar}: ${c0}\nÖNCE ${oz(once)}\nSONRA ${oz(k)}`);
      }
      if (k.klipler.length < 3) k = produce(k, (d) => { d.klipler.push(K.klipYap(d, { tur: "video", iz: "V2", bas: Math.max(0, ...d.klipler.map((x) => x.bas + x.sure)) + 1, sure: 5, kaynak: "A" })); });
    }
  });
});
