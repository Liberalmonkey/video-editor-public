import { produce } from "immer";
import { describe, expect, it } from "vitest";
import { sesEgrisi } from "../../../remotion/izdusum";
import * as K from "./komutlar";

const iz = (id: string, tur: "video" | "ses") => ({ id, tur, ad: "", kilit: false, sessiz: false, gizli: false, gain_db: 0 });
const temel = (): K.K => {
  const k: K.K = { sekans: { w: 1080, h: 1920, fps: 30 }, kaynaklar: { A: { yol: "inputs:a.mp4", sure: 100, ses: true } }, kelimeler: {},
    izler: [iz("V1", "video"), iz("A1", "ses")], klipler: [], altyazi: { acik: true, iz: "V1" } };
  k.klipler = [{ ...K.klipYap(k, { tur: "video", iz: "V1", bas: 0, sure: 10, kaynak: "A" }), id: "v" }];
  return k;
};
const yap = (k: K.K, f: (d: K.K) => void) => { const s = produce(k, f); expect(K.cakisma(s)).toBeNull(); return s; };
const v = (k: K.K) => k.klipler.find((c) => c.id === "v")!;

describe("kazanç keyframe'i", () => {
  it("animasyon açılır, oynatma kafasında keyframe yazılır, arası doğrusal", () => {
    let k = yap(temel(), (d) => K.sesKfAnim(d, "v", 0));
    k = yap(k, (d) => K.kazancYaz(d, "v", -12, 4));
    expect(v(k).ses.kf!.map((f) => [f.t, f.v])).toEqual([[0, 0], [4, -12]]);
    expect(K.kazancAni(v(k), 2)).toBe(-6);
    const e = sesEgrisi(v(k), 0, 30);
    expect(20 * Math.log10(e(60))).toBeCloseTo(-6, 1);
  });
  it("animasyonsuz yazım ve Alt+ok tüm eğriyi kaydırır", () => {
    let k = yap(temel(), (d) => { K.sesKfAnim(d, "v", 0); K.kazancYaz(d, "v", -12, 4); });
    k = yap(k, (d) => K.kazancEkle(d, ["v"], 3));
    expect(v(k).ses.kf!.map((f) => f.v)).toEqual([3, -9]);
  });
  it("kapatınca o anki değer sabit kalır; son keyframe silinince değer korunur", () => {
    let k = yap(temel(), (d) => { K.sesKfAnim(d, "v", 0); K.kazancYaz(d, "v", -12, 4); });
    const kapali = yap(k, (d) => K.sesKfAnim(d, "v", 2));
    expect([v(kapali).ses.kf, v(kapali).ses.gain_db]).toEqual([[], -6]);
    k = yap(k, (d) => K.sesKfDegistir(d, "v", 0, 0.1));
    k = yap(k, (d) => K.sesKfDegistir(d, "v", 4, 0.1));
    expect([v(k).ses.kf, v(k).ses.gain_db]).toEqual([[], -12]);
  });
  it("bölmede eğri parçalarında aynı kalır", () => {
    const k = yap(temel(), (d) => { K.sesKfAnim(d, "v", 0); K.kazancYaz(d, "v", -12, 4); K.kes(d, "v", 2); });
    const sag = k.klipler.find((c) => c.id !== "v")!;
    expect(K.kazancAni(sag, 0)).toBeCloseTo(-6);
    expect(K.kazancAni(sag, 2)).toBeCloseTo(-12);
    expect(K.kazancAni(v(k), 2)).toBeCloseTo(-6);
  });
  it("ayırma eğriyi iz kazancıyla ses klibine taşır", () => {
    const t = temel(); t.izler[0].gain_db = -3;
    const k = yap(t, (d) => { K.sesKfAnim(d, "v", 0); K.kazancYaz(d, "v", -12, 4); K.sesiAyir(d, ["v"]); });
    expect(k.klipler.find((c) => c.tur === "ses")!.ses.kf!.map((f) => f.v)).toEqual([-3, -15]);
  });
});

describe("konuşmayı müzikten ayırma", () => {
  it("video sesi ayrılır, ses klibi vokal kaynağına geçer, altyazı kelimeleri gelir", () => {
    const t = temel(); t.kelimeler = { A: [{ w: "x", s: 1, e: 2 }] };
    let id: string | null = null;
    const k = yap(t, (d) => { id = K.vokaleGec(d, "v", { id: "A_vokal", yol: "public:ayrisan/a.vokal.wav", sure: 100 }); });
    const s = k.klipler.find((c) => c.id === id)!;
    expect([s.tur, s.kaynak, v(k).ses_kapali]).toEqual(["ses", "A_vokal", true]);
    expect(K.kelimeSatirlari(k).map((w) => w.kaynak)).toEqual(["A_vokal"]);
  });
});

describe("stem'leri timeline'a ekleme", () => {
  it("her kanal kendi sessiz izine, klibin yeri ve kaynak anında girer", () => {
    const t = temel();
    const k = yap(t, (d) => { K.stemEkle(d, "v", [{ ad: "Müzik", id: "A_muzik", yol: "public:ayrisan/a.muzik.wav", sure: 100 }, { ad: "Davul", id: "A_davul", yol: "public:ayrisan/a.s4.davul.wav", sure: 100 }]); });
    const yeni = k.klipler.filter((c) => c.kaynak === "A_muzik" || c.kaynak === "A_davul");
    expect(yeni.map((c) => [c.tur, c.bas, c.sure, c.giris])).toEqual([["ses", v(k).bas, v(k).sure, v(k).giris], ["ses", v(k).bas, v(k).sure, v(k).giris]]);
    const izler = yeni.map((c) => k.izler.find((i) => i.id === c.iz)!);
    expect(new Set(izler.map((i) => i.id)).size).toBe(2);
    expect(izler.every((i) => i.sessiz)).toBe(true);
    expect(k.kaynaklar.A_muzik.yol).toBe("public:ayrisan/a.muzik.wav");
  });
});

describe("metinden ve öneriden kesme", () => {
  it("aralıkları birleştirir, sondan keser, toplamı döner", () => {
    let n = 0;
    const k = yap(temel(), (d) => { n = K.araliklariCikar(d, [[6, 7], [1, 2], [1.5, 3]]); });
    expect(n).toBe(3);
    expect(k.klipler.map((c) => [c.bas, c.sure, c.giris]).sort((a, b) => a[0] - b[0])).toEqual([[0, 1, 0], [1, 3, 3], [4, 3, 7]]);
  });
  it("ayrık seste görüntü ve ses birlikte kesilir", () => {
    const k = yap(temel(), (d) => { K.sesiAyir(d, ["v"]); K.araliklariCikar(d, [[2, 4]]); });
    const v = k.klipler.filter((c) => c.tur === "video").map((c) => [c.bas, c.sure, c.giris]).sort();
    expect(k.klipler.filter((c) => c.tur === "ses").map((c) => [c.bas, c.sure, c.giris]).sort()).toEqual(v);
  });
});
