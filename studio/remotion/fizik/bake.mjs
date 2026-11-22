// Fizik sahnesi bake: preset + parametre → kare kare yörünge, temas anları, kamera yolu ve ölçüm (tek JSON).
// WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Rapier (react-three-rapier'ın motoru) gerçek zamanlı adımlar;
// Remotion kareleri sırasız ve paralel çizer. Simülasyon kare 0'dan sabit adımla bir kez koşar, render yalnız okur:
// önizleme ve render aynı kareyi gösterir, temas anları ses olayına kare kesinliğinde gider.
// Kullanım: node bake.mjs <girdi.json> <cikti.json>   girdi: {preset, param, fps, sure, w, h}
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import RAPIER from "@dimforge/rapier3d-compat";

const BURASI = path.dirname(fileURLToPath(import.meta.url));
const KATALOG = JSON.parse(fs.readFileSync(path.join(BURASI, "presetler.json"), "utf8"));
const ALT_ADIM = 4; // kare başına fizik adımı: hızlı çarpışmada tünelleme olmasın
const G = 9.81;
const RAD = Math.PI / 180;

const qEuler = (x = 0, y = 0, z = 0) => {
  const [cx, sx] = [Math.cos(x * RAD / 2), Math.sin(x * RAD / 2)];
  const [cy, sy] = [Math.cos(y * RAD / 2), Math.sin(y * RAD / 2)];
  const [cz, sz] = [Math.cos(z * RAD / 2), Math.sin(z * RAD / 2)];
  return { x: sx * cy * cz - cx * sy * sz, y: cx * sy * cz + sx * cy * sz, z: cx * cy * sz - sx * sy * cz, w: cx * cy * cz + sx * sy * sz };
};
const qCarp = (a, b) => ({
  w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z, x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
  y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x, z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
});

function parametre(preset, verilen) {
  const tanim = KATALOG.presetler[preset];
  if (!tanim) throw new Error(`bilinmeyen fizik preseti: ${preset}`);
  const p = {};
  for (const [ad, t] of Object.entries(tanim.param)) {
    let v = verilen?.[ad] ?? t.vars;
    if (t.tip === "sayi") v = Math.min(t.max, Math.max(t.min, Number(v)));
    p[ad] = v;
  }
  return p;
}

// Dünya kurucu yardımcıları. Her gövde görsel tanımını (parca) ve fizik gövdesini birlikte taşır.
function dunya() {
  const w = new RAPIER.World({ x: 0, y: -G, z: 0 });
  const govdeler = [];
  const ekle = ({ id, tip = "dinamik", poz = [0, 0, 0], aci = [0, 0, 0], q, hiz, aciHiz, parca, sekme = 0.3, surtunme = 0.6, yogunluk = 1, ses = true, renk = "vurgu", ccd = false, sonum = 0 }) => {
    const d = tip === "sabit" ? RAPIER.RigidBodyDesc.fixed() : tip === "kinematik" ? RAPIER.RigidBodyDesc.kinematicPositionBased() : RAPIER.RigidBodyDesc.dynamic();
    d.setTranslation(...poz).setRotation(q ?? qEuler(...aci)).setCcdEnabled(ccd);
    if (hiz) d.setLinvel(...hiz);
    if (aciHiz) d.setAngvel({ x: aciHiz[0], y: aciHiz[1], z: aciHiz[2] });
    if (sonum) d.setAngularDamping(sonum);
    const b = w.createRigidBody(d);
    for (const pc of parca) {
      const c = pc.sekil === "kure" ? RAPIER.ColliderDesc.ball(pc.boyut[0])
        : pc.sekil === "silindir" ? RAPIER.ColliderDesc.cylinder(pc.boyut[1], pc.boyut[0])
        : RAPIER.ColliderDesc.cuboid(...pc.boyut);
      c.setRestitution(sekme).setFriction(surtunme).setDensity(yogunluk)
        .setRestitutionCombineRule(RAPIER.CoefficientCombineRule.Max)
        .setActiveEvents(RAPIER.ActiveEvents.COLLISION_EVENTS);
      if (pc.ofset) c.setTranslation(...pc.ofset);
      if (pc.aci) c.setRotation(qEuler(...pc.aci));
      if (pc.carpmaz) c.setSensor(true);
      w.createCollider(c, b);
    }
    const g = { id, b, tip, ses, renk, parca: parca.map(({ carpmaz, ...r }) => ({ renk, ...r })) };
    govdeler.push(g);
    return g;
  };
  return { w, govdeler, ekle };
}

function zeminEkle(d, { boy = 200, en = 40, sekme = 0.3, surtunme = 0.8 } = {}) {
  return d.ekle({ id: "zemin", tip: "sabit", poz: [0, -0.05, 0], parca: [{ sekil: "kutu", boyut: [boy / 2, 0.05, en / 2], gizli: true }], sekme, surtunme, ses: false, renk: "zemin" });
}

// Preset kurucuları: dünya, kamera hedefi, ölçüm işlevi, kinematik sürücü.
const KURUCU = {
  "top-dusme"(d, p) {
    zeminEkle(d, { sekme: p.sekme });
    const top = d.ekle({ id: "top", poz: [-p.yatay_hiz * 0.8, p.yukseklik, 0], hiz: [p.yatay_hiz, 0, 0], parca: [{ sekil: "kure", boyut: [p.yaricap] }], sekme: p.sekme, ccd: true, sonum: 0.3 });
    return { odak: "top", kameraKip: "sabit", olcum: () => Math.max(0, top.b.translation().y - p.yaricap) }; // düşüşün tamamı kadrajda kalsın
  },
  yuvarlanma(d, p) {
    zeminEkle(d, { surtunme: p.surtunme });
    const a = p.egim * RAD, L = p.uzunluk;
    // Rampa: üst ucu solda. Kutunun merkezi rampanın ortası; kalınlık 0,1 m.
    const cx = -Math.cos(a) * L / 2, cy = Math.sin(a) * L / 2;
    d.ekle({ id: "rampa", tip: "sabit", poz: [cx, cy - 0.05 * Math.cos(a), 0], aci: [0, 0, -p.egim], parca: [{ sekil: "kutu", boyut: [L / 2, 0.05, 0.8] }], surtunme: p.surtunme, ses: false, renk: "soluk" });
    const r = p.yaricap;
    const ux = -Math.cos(a) * (L - r * 1.5), uy = Math.sin(a) * (L - r * 1.5);
    const top = d.ekle({ id: "top", poz: [ux + Math.sin(a) * r, uy + Math.cos(a) * r + 0.01, 0], parca: [{ sekil: "kure", boyut: [r] }], surtunme: p.surtunme, sekme: 0.2, ccd: true });
    if (p.engel === "kutu") for (let i = 0; i < 3; i++) d.ekle({ id: `kutu${i}`, poz: [L * 0.55 + 0.4, 0.3 + i * 0.6, (i - 1) * 0.05], parca: [{ sekil: "kutu", boyut: [0.3, 0.3, 0.3] }], yogunluk: 0.15, renk: "ikincil" });
    if (p.engel === "duvar") d.ekle({ id: "duvar", tip: "sabit", poz: [L * 0.6 + 0.2, 0.6, 0], parca: [{ sekil: "kutu", boyut: [0.1, 0.6, 1] }], sekme: 0.5, renk: "soluk" });
    return { odak: "top", olcum: () => { const v = top.b.linvel(); return Math.hypot(v.x, v.y, v.z); } };
  },
  "araba-ivme"(d, p, { fps }) {
    zeminEkle(d, { boy: 2000 });
    const R = 0.34;
    const govde = d.ekle({ id: "araba", tip: "kinematik", poz: [0, 0.55, 0], renk: "vurgu", parca: [
      { sekil: "kutu", boyut: [1.15, 0.22, 0.5] },
      { sekil: "kutu", boyut: [0.6, 0.2, 0.45], ofset: [-0.15, 0.4, 0], renk: "yazi" },
    ] });
    const tekerler = [[0.75, 0.48], [0.75, -0.48], [-0.75, 0.48], [-0.75, -0.48]].map(([x, z], i) =>
      d.ekle({ id: `teker${i}`, tip: "kinematik", poz: [x, R, z], q: qEuler(90, 0, 0), parca: [{ sekil: "silindir", boyut: [R, 0.1], carpmaz: true }], renk: "zemin", ses: false }));
    for (let i = 0; i < p.dubalar; i++) d.ekle({ id: `duba${i}`, poz: [12 + i * 6, 0.35, (i % 2 ? 0.25 : -0.25)], parca: [{ sekil: "silindir", boyut: [0.16, 0.35] }], yogunluk: 0.3, renk: "ikincil" });
    const t1 = p.en_hiz / p.ivme;
    const konum = (t) => t < t1 ? 0.5 * p.ivme * t * t : 0.5 * p.ivme * t1 * t1 + p.en_hiz * (t - t1);
    const hizi = (t) => Math.min(p.en_hiz, p.ivme * t);
    // Süspansiyon: kalkışta arka çöker (burun kalkar), ivme bitince yaylanır. Kritik altı sönümlü yay, sabit adım.
    let egim = 0, egimHiz = 0;
    return {
      odak: "araba",
      olcum: (t) => hizi(Math.max(0, t - 0.15)) * 3.6,
      kinematik(t, dt) {
        const hedef = (t > 0.15 && t < t1 ? 1 : 0) * Math.min(0.05, p.ivme * 0.006);
        egimHiz += ((hedef - egim) * 90 - egimHiz * 9) * dt; egim += egimHiz * dt;
        const x = konum(Math.max(0, t - 0.15)); // 0,15 sn bekleme: izleyici durgun arabayı görsün
        const qg = { x: 0, y: 0, z: Math.sin(egim / 2), w: Math.cos(egim / 2) };
        govde.b.setNextKinematicTranslation({ x, y: 0.55, z: 0 });
        govde.b.setNextKinematicRotation(qg);
        const donus = -x / R;
        tekerler.forEach((tk, i) => {
          const [ox, oz] = [[0.75, 0.48], [0.75, -0.48], [-0.75, 0.48], [-0.75, -0.48]][i];
          tk.b.setNextKinematicTranslation({ x: x + ox, y: R, z: oz });
          tk.b.setNextKinematicRotation(qCarp({ x: 0, y: 0, z: Math.sin(donus / 2), w: Math.cos(donus / 2) }, qEuler(90, 0, 0)));
        });
      },
      kameraKip: p.kamera,
    };
  },
  domino(d, p) {
    zeminEkle(d, { surtunme: 0.5 });
    const n = Math.round(p.adet);
    let x = 0, z = 0;
    const taslar = [];
    for (let i = 0; i < n; i++) {
      const yon = (p.kivrim * (n > 1 ? i / (n - 1) : 0)) * RAD;
      if (i) { x += Math.cos(yon) * p.aralik; z -= Math.sin(yon) * p.aralik; }
      // İlk taş ön alt köşesi üstünde 15° eğik başlar: kritik açı (atan(0,035/0,25) ≈ 8°) aşılmış, itme gerekmez.
      // Merkezinden döndürülen taş köşesini zemine gömüp sürtünmeyle duruyordu.
      const e = i === 0 ? 15 * RAD : 0;
      const poz = i === 0 ? [x + 0.035 - 0.035 * Math.cos(e) + 0.25 * Math.sin(e), 0.035 * Math.sin(e) + 0.25 * Math.cos(e) + 0.002, z] : [x, 0.25, z];
      taslar.push(d.ekle({ id: `tas${i}`, poz, aci: [0, yon / RAD, -e / RAD], parca: [{ sekil: "kutu", boyut: [0.035, 0.25, 0.12] }],
        aciHiz: i === 0 ? [0, 0, -1.2] : undefined, surtunme: 0.45, sekme: 0.05, renk: i === n - 1 ? "vurgu" : i % 2 ? "ikincil" : "yazi" }));
    }
    return { odak: null, olcum: () => taslar.filter((t) => { const q = t.b.rotation(); return 1 - 2 * (q.x * q.x + q.z * q.z) < 0.7; }).length };
  },
  sarkac(d, p) {
    zeminEkle(d);
    const n = Math.round(p.adet), r = 0.18, ustY = p.boy + 0.6;
    const tavan = d.ekle({ id: "tavan", tip: "sabit", poz: [0, ustY + 0.05, 0], parca: [{ sekil: "kutu", boyut: [n * r + 0.4, 0.05, 0.15] }], ses: false, renk: "soluk" });
    const toplar = [];
    for (let i = 0; i < n; i++) {
      const px = (i - (n - 1) / 2) * r * 2.02;
      const a = i === 0 ? -p.aci * RAD : 0;
      const top = d.ekle({ id: `top${i}`, poz: [px + Math.sin(a) * p.boy, ustY - Math.cos(a) * p.boy, 0], parca: [{ sekil: "kure", boyut: [r] }], sekme: 0.96, surtunme: 0, yogunluk: 7, renk: i === 0 ? "vurgu" : "yazi" });
      const ust = { x: px, y: -0.05, z: 0 };
      d.w.createImpulseJoint(RAPIER.JointData.spherical(ust, { x: -Math.sin(a) * p.boy, y: Math.cos(a) * p.boy, z: 0 }), tavan.b, top.b, true);
      top.ip = [px, ustY, 0];
      toplar.push(top);
    }
    return { odak: null, olcum: () => { const t = toplar[0].b.translation(); const px = -(n - 1) / 2 * r * 2.02; return Math.atan2(t.x - px, ustY - t.y) / RAD; } };
  },
  firlatma(d, p) {
    zeminEkle(d, { sekme: 0.45 });
    const a = p.aci * RAD;
    const top = d.ekle({ id: "top", poz: [0, 0.3, 0], hiz: [Math.cos(a) * p.hiz, Math.sin(a) * p.hiz, 0], parca: [{ sekil: "kure", boyut: [0.28] }], sekme: 0.45, ccd: true, sonum: 0.4 });
    top.iz = p.iz === "acik";
    return { odak: null, olcum: () => Math.max(0, top.b.translation().y - 0.28) };
  },
  "kule-cokus"(d, p) {
    zeminEkle(d);
    const kutular = [];
    for (let i = 0; i < p.kat; i++) for (let j = 0; j < 2; j++) {
      const dik = i % 2 === 1;
      kutular.push(d.ekle({ id: `kutu${i}_${j}`, poz: dik ? [0, 0.15 + i * 0.3, (j - 0.5) * 0.4] : [(j - 0.5) * 0.4, 0.15 + i * 0.3, 0],
        parca: [{ sekil: "kutu", boyut: dik ? [0.4, 0.15, 0.19] : [0.19, 0.15, 0.4] }], yogunluk: 0.4, surtunme: 0.7, sekme: 0.1, renk: (i + j) % 3 ? "yazi" : "ikincil" }));
    }
    const h = p.kat * 0.3 * 0.55;
    const vy = 0.2 * G; // 0,2 sn sonra hedef yükseklikte olsun diye hafif yukarı atış
    d.ekle({ id: "top", poz: [-p.top_hizi * 0.6, h, 0], hiz: [p.top_hizi, vy, 0], parca: [{ sekil: "kure", boyut: [0.3] }], yogunluk: 4, ccd: true, sekme: 0.2 });
    return { odak: null, olcum: () => kutular.filter((k) => { const q = k.b.rotation(); return 1 - 2 * (q.x * q.x + q.z * q.z) < 0.7 || k.b.translation().y < 0.1; }).length };
  },
};

function guc(hiz) {
  return hiz >= 4 ? "sert" : hiz >= 1.5 ? "orta" : "yumusak";
}

// Sabit kamera: tüm yörüngelerin sınır kutusunu kadraja sığdırır (yatay/dikey oranına göre).
function sigdir(kutu, en_boy, fov = 35) {
  const [mn, mx] = kutu;
  const mer = mn.map((v, i) => (v + mx[i]) / 2);
  const gen = Math.max(mx[0] - mn[0], 0.5), yuk = Math.max(mx[1] - mn[1], 0.5);
  const yf = Math.tan((fov * RAD) / 2);
  // Pay %12 ve 0,8 m: nesne kadrajın çoğunu doldursun; ilk sürümde %35 + 1,5 m top ve kuleyi küçük gösteriyordu.
  const uzak = Math.max(yuk / 2 / yf, gen / 2 / (yf * en_boy)) * 1.12 + (mx[2] - mn[2]) / 2 + 0.8;
  return [mer[0], mer[1] + uzak * 0.22, mer[2] + uzak, mer[0], mer[1], mer[2]];
}

export async function bake({ preset, param, fps = 30, sure, w = 1920, h = 1080 }) {
  await RAPIER.init();
  const p = parametre(preset, param);
  const d = dunya();
  const kur = KURUCU[preset](d, p, { fps });
  const kare = Math.max(1, Math.round((sure ?? KATALOG.presetler[preset].sure) * fps));
  const dt = 1 / (fps * ALT_ADIM);
  d.w.timestep = dt;
  const eq = new RAPIER.EventQueue(true);
  const gorunen = d.govdeler.filter((g) => !g.parca.every((pc) => pc.gizli));
  const yorunge = Object.fromEntries(gorunen.map((g) => [g.id, []]));
  const olcum = [], temas = [], sonTemas = new Map();
  const tutamak = new Map(d.govdeler.map((g) => [g.b.handle, g]));
  const kutu = [[Infinity, Infinity, Infinity], [-Infinity, -Infinity, -Infinity]];
  const kaydet = (t) => {
    for (const g of gorunen) {
      const a = g.b.translation(), q = g.b.rotation();
      yorunge[g.id].push(...[a.x, a.y, a.z, q.x, q.y, q.z, q.w].map((v) => Math.round(v * 1e4) / 1e4));
      const r = g.yaricap ??= Math.max(...g.parca.map((pc) => Math.max(...pc.boyut)));
      if (g.tip !== "sabit") [a.x, a.y, a.z].forEach((v, i) => { kutu[0][i] = Math.min(kutu[0][i], v - r); kutu[1][i] = Math.max(kutu[1][i], v + r); });
    }
    olcum.push(Math.round(kur.olcum(t) * 100) / 100);
  };
  kaydet(0);
  for (let n = 1; n < kare; n++) {
    for (let s = 0; s < ALT_ADIM; s++) {
      const t = (n - 1) / fps + s * dt;
      kur.kinematik?.(t, dt);
      const once = new Map(d.govdeler.map((g) => [g.b.handle, g.b.linvel()]));
      d.w.step(eq);
      eq.drainCollisionEvents((h1, h2, basladi) => {
        if (!basladi) return;
        const g1 = tutamak.get(d.w.getCollider(h1).parent().handle), g2 = tutamak.get(d.w.getCollider(h2).parent().handle);
        if (!g1 || !g2 || (!g1.ses && !g2.ses)) return;
        const v1 = once.get(g1.b.handle), v2 = once.get(g2.b.handle);
        const hiz = Math.hypot(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z);
        const cift = [g1.id, g2.id].sort().join("|");
        const tt = t + dt;
        // Aynı çiftin 80 ms içindeki tekrar temasları tek olaydır; yavaş sürtünme teması ses değildir.
        if (hiz < 0.4 || tt - (sonTemas.get(cift) ?? -1) < 0.08) return;
        sonTemas.set(cift, tt);
        temas.push({ t: Math.round(tt * 1000) / 1000, kare: Math.round(tt * fps), a: g1.id, b: g2.id, hiz: Math.round(hiz * 100) / 100, guc: guc(hiz) });
      });
    }
    kaydet(n / fps);
  }
  // Kamera: takip edilen gövde varsa yumuşatılmış takip, yoksa sığdırılmış sabit.
  const enBoy = w / h;
  const sabit = sigdir(kutu, enBoy);
  let kamera;
  const odak = kur.odak && yorunge[kur.odak];
  const kip = kur.kameraKip ?? (kur.odak ? "takip" : "sabit");
  if (odak && kip !== "sabit") {
    kamera = [];
    let cx = odak[0];
    for (let n = 0; n < kare; n++) {
      const hx = odak[n * 7], hy = odak[n * 7 + 1];
      cx += (hx - cx) * (n ? 0.18 : 1); // kritik sönümlü takip: kamera nesnenin biraz arkasından gelir, hız hissi
      kamera.push(kip === "yan"
        ? [cx, 1.6, 9, cx, 0.6, 0].map((v) => Math.round(v * 1e3) / 1e3)
        : [cx - 6.5, Math.max(1.8, hy + 1.4), 6.5, cx + 2.5, Math.max(0.4, hy * 0.7), 0].map((v) => Math.round(v * 1e3) / 1e3));
    }
  }
  eq.free(); d.w.free(); // WASM belleği: galeri çok sahneyi aynı süreçte bake eder
  const tanim = KATALOG.presetler[preset];
  return {
    surum: 1, preset, fps, kare, param: p,
    govdeler: gorunen.map((g) => ({ id: g.id, parca: g.parca, ...(g.ip ? { ip: g.ip } : {}), ...(g.iz ? { iz: true } : {}) })),
    yorunge, temas, kamera: kamera ?? null, sabit_kamera: sabit.map((v) => Math.round(v * 1e3) / 1e3),
    olcum: { ad: tanim.olcum, deger: olcum }, etiket: p.etiket || "",
    zemin: { boy: Math.max(30, (kutu[1][0] - kutu[0][0]) * 3) },
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [girdi, cikti] = process.argv.slice(2);
  const sonuc = await bake(JSON.parse(fs.readFileSync(girdi, "utf8")));
  fs.writeFileSync(cikti, JSON.stringify(sonuc));
  console.log(JSON.stringify({ kare: sonuc.kare, temas: sonuc.temas.length }));
}
