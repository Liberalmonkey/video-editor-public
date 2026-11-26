// three.js HyperFrames çekirdeği: window.HFUC. Paket: library/vendor/uc.js (npm run uc).
// WHY: bkz. wiki/decisions/0063-gsap-eklentileri-ve-threejs-hf.md. 3D şablonlar library/motion/hf/uc-*/ altında
// tek index.html olarak yazılır; three.js, eklentiler ve ortak kurulum bu pakettedir ki her şablon aynı alfa, ışık,
// tema ve zaman kuralını kullansın. Kural: kare yalnız `hf-seek` olayındaki zamandan çizilir (rAF, saat, setAnimationLoop yok).
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { SavePass } from "three/examples/jsm/postprocessing/SavePass.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

type Renk = THREE.Color;
export interface Tema {
  vurgu: Renk; ikincil: Renk; zemin: Renk; yazi: Renk; soluk: Renk; olumlu: Renk; olumsuz: Renk;
  css: (ad: string) => string; font: string; fontGovde: string; agirlik: string;
}

// Tohumlu üreteç (mulberry32): her rastgele seçim tohumdan; Math.random yok.
export const tohum = (s: number) => () => {
  s |= 0; s = (s + 0x6d2b79f5) | 0;
  let t = Math.imul(s ^ (s >>> 15), 1 | s);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const css = (ad: string) => getComputedStyle(document.documentElement).getPropertyValue(ad).trim();

// CSS renk metni → THREE.Color. Tarayıcı çözer (hex, rgb(), hsl(), color-mix dahil); token yoksa yedek.
const cozucu = (() => {
  let c: CanvasRenderingContext2D | null = null;
  return (deger: string, yedek: Renk): Renk => {
    if (!deger) return yedek.clone();
    c ??= document.createElement("canvas").getContext("2d");
    if (!c) return yedek.clone();
    c.clearRect(0, 0, 1, 1);
    c.fillStyle = "rgba(0,0,0,0)";
    c.fillStyle = deger;
    c.fillRect(0, 0, 1, 1);
    const [r, g, b] = c.getImageData(0, 0, 1, 1).data;
    return new THREE.Color().setRGB(r / 255, g / 255, b / 255, THREE.SRGBColorSpace);
  };
})();

export const tema = (): Tema => {
  const beyaz = new THREE.Color(1, 1, 1), siyah = new THREE.Color(0, 0, 0);
  const r = (ad: string, yedek: Renk) => cozucu(css(ad), yedek);
  return {
    vurgu: r("--vurgu", beyaz), ikincil: r("--ikincil", beyaz), zemin: r("--zemin", siyah), yazi: r("--yazi", beyaz),
    soluk: r("--soluk", beyaz), olumlu: r("--olumlu", beyaz), olumsuz: r("--olumsuz", beyaz),
    css, font: css("--font") || "sans-serif", fontGovde: css("--font-govde") || "sans-serif", agirlik: css("--agirlik") || "800",
  };
};

export interface KurSecenek {
  kok?: HTMLElement | string;
  fov?: number;
  kamera?: [number, number, number];
  hedef?: [number, number, number];
  bloom?: false | { guc?: number; yaricap?: number; esik?: number };
  ortam?: number; // ortam ışığı yoğunluğu (0.3-0.6; parlak metalde beyaz çizgi olmasın)
  isik?: "studyo" | "yok";
  pozlama?: number;
}

export interface Ctx {
  THREE: typeof THREE;
  kok: HTMLElement; w: number; h: number; dikey: boolean;
  renderer: THREE.WebGLRenderer; sahne: THREE.Scene; kamera: THREE.PerspectiveCamera;
  tema: Tema; isiklar: THREE.Group; ortamNesne: THREE.Object3D;
  hedef: THREE.Vector3;
  ciz: () => void;
}

// Alfa birleştirme: bloom ve ton eşleme alfayı bozar. Taban alfası ile parıltının en parlak kanalının büyüğü alınır;
// renk alfayı aşmaz (öncül çarpımlı çıktı). Saydam webm'de parıltı videonun üstüne doğru biner.
const ALFA = {
  uniforms: { tDiffuse: { value: null }, tTaban: { value: null } },
  vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
  fragmentShader: `uniform sampler2D tDiffuse; uniform sampler2D tTaban; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); float a0 = texture2D(tTaban, vUv).a;
      float a = clamp(max(a0, 0.85 * max(c.r, max(c.g, c.b))), 0.0, 1.0);
      gl_FragColor = vec4(min(c.rgb, vec3(a)), a); }`,
};

export const kur = (o: KurSecenek = {}): Ctx => {
  const kok = (typeof o.kok === "string" ? document.querySelector(o.kok) : o.kok) as HTMLElement | null
    ?? document.querySelector("[data-composition-id]") as HTMLElement;
  const w = Math.round(Number(kok.dataset.width) || kok.clientWidth || 1920);
  const h = Math.round(Number(kok.dataset.height) || kok.clientHeight || 1080);
  const tuval = document.createElement("canvas");
  tuval.className = "uc-tuval";
  Object.assign(tuval.style, { position: "absolute", inset: "0", width: "100%", height: "100%", display: "block" });
  kok.prepend(tuval);

  const renderer = new THREE.WebGLRenderer({ canvas: tuval, alpha: true, premultipliedAlpha: true, antialias: true,
    preserveDrawingBuffer: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1);
  renderer.setSize(w, h, false);
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = o.pozlama ?? 1;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const sahne = new THREE.Scene();
  const kamera = new THREE.PerspectiveCamera(o.fov ?? 35, w / h, 0.1, 400);
  kamera.position.set(...(o.kamera ?? [0, 0, 10]));
  const hedef = new THREE.Vector3(...(o.hedef ?? [0, 0, 0]));
  kamera.lookAt(hedef);

  // Ortam: koyu oda + yumuşak şeritler. Dönen ortamdır, nesne değil: parlaklık yüzeyde süzülür.
  const pmrem = new THREE.PMREMGenerator(renderer);
  const oda = new RoomEnvironment();
  const ortamDoku = pmrem.fromScene(oda, 0.04).texture;
  sahne.environment = ortamDoku;
  sahne.environmentIntensity = o.ortam ?? 0.5;
  const ortamNesne = new THREE.Object3D();

  // Işık: sıcak ana + soğuk kontur + hafif dolgu. Işık rengi marka rengi değildir, nötr sıcak/soğuk beyazdır.
  const isiklar = new THREE.Group();
  if (o.isik !== "yok") {
    const ana = new THREE.DirectionalLight(new THREE.Color(1, 0.94, 0.86), 2.4);
    ana.position.set(4, 6, 7);
    const kontur = new THREE.DirectionalLight(new THREE.Color(0.74, 0.84, 1), 1.8);
    kontur.position.set(-6, 2.5, -5);
    const dolgu = new THREE.HemisphereLight(new THREE.Color(0.9, 0.92, 1), new THREE.Color(0.08, 0.08, 0.1), 0.35);
    isiklar.add(ana, kontur, dolgu);
  }
  sahne.add(isiklar);

  let ciz: () => void;
  if (o.bloom === false) {
    ciz = () => renderer.render(sahne, kamera);
  } else {
    const b = o.bloom ?? {};
    const hedefRT = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 4 });
    const composer = new EffectComposer(renderer, hedefRT);
    composer.setPixelRatio(1);
    composer.setSize(w, h);
    composer.addPass(new RenderPass(sahne, kamera, undefined, new THREE.Color(0, 0, 0), 0));
    const taban = new SavePass(new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType }));
    composer.addPass(taban);
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(w, h), b.guc ?? 0.45, b.yaricap ?? 0.35, b.esik ?? 1.0));
    composer.addPass(new OutputPass());
    const alfa = new ShaderPass(ALFA);
    alfa.uniforms.tTaban.value = taban.renderTarget.texture;
    composer.addPass(alfa);
    ciz = () => composer.render();
  }

  return { THREE, kok, w, h, dikey: h > w, renderer, sahne, kamera, tema: tema(), isiklar, ortamNesne, hedef, ciz };
};

// Zaman sürücüsü: GSAP zaman çizelgesi (duraklatılmış) üç nesneyi ve DOM'u birlikte sürer; her seek'te tl.seek(t),
// sonra `kare(t)` (türetilmiş durum), sonra çizim. Zaman çizelgesi window.__timelines'a da kaydedilir: HyperFrames
// süreyi ve DOM katmanını oradan okur. Ağır kurulum buildReady sözündedir; ilk kare ve tek piksel okuma kurulumda.
export const sur = (ctx: Ctx, tl: { seek: (t: number, s?: boolean) => unknown } | null, kare?: (t: number) => void,
  anahtar = "uc") => {
  const ciz = (t: number) => {
    tl?.seek(t, false);
    kare?.(t);
    ctx.ciz();
  };
  const w = window as unknown as { __hf?: { buildReady?: Record<string, Promise<unknown>> } };
  w.__hf ??= {};
  w.__hf.buildReady ??= {};
  w.__hf.buildReady[anahtar] = (async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    await ctx.renderer.compileAsync(ctx.sahne, ctx.kamera);
    ciz(0);
    const gl = ctx.renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
  })();
  window.addEventListener("hf-seek", (e) => ciz(Number((e as CustomEvent).detail?.time) || 0));
  ciz(0);
  return ciz;
};

// Yazı dokusu: tema fontuyla canvas'a çizilir (Türkçe glif tam; TextGeometry font JSON'u gerektirmez).
export const yaziDokusu = (metin: string, o: { font?: string; agirlik?: string | number; boy?: number; renk?: string;
  dolgu?: number; harfAraligi?: number } = {}) => {
  const boy = o.boy ?? 220, dolgu = o.dolgu ?? Math.round(boy * 0.25);
  const font = `${o.agirlik ?? css("--agirlik") ?? 800} ${boy}px ${o.font ?? (css("--font") || "sans-serif")}`;
  const olc = document.createElement("canvas").getContext("2d")!;
  olc.font = font;
  const satirlar = metin.split("\n");
  const gen = Math.max(...satirlar.map((s) => olc.measureText(s).width)) + (o.harfAraligi ?? 0) * metin.length;
  const c = document.createElement("canvas");
  c.width = Math.ceil(gen + dolgu * 2);
  c.height = Math.ceil(boy * 1.18 * satirlar.length + dolgu * 2);
  const x = c.getContext("2d")!;
  x.font = font;
  x.textAlign = "center";
  x.textBaseline = "middle";
  x.fillStyle = o.renk ?? (css("--yazi") || "white");
  if (o.harfAraligi) (x as unknown as { letterSpacing: string }).letterSpacing = `${o.harfAraligi}px`;
  satirlar.forEach((s, i) => x.fillText(s, c.width / 2, dolgu + boy * 1.18 * (i + 0.5)));
  const doku = new THREE.CanvasTexture(c);
  doku.colorSpace = THREE.SRGBColorSpace;
  doku.anisotropy = 8;
  return { doku, oran: c.width / c.height, tuval: c };
};

// Katmanlı ekstrüzyon: aynı yazı dokusu derinlik boyunca N düzlemde, arkaya doğru koyulaşarak. Her font, her glif.
export const katmanliYazi = (metin: string, o: { yukseklik?: number; derinlik?: number; katman?: number;
  on?: Renk; yan?: Renk; boy?: number } = {}) => {
  const t = tema();
  const { doku, oran } = yaziDokusu(metin, { boy: o.boy ?? 220, renk: "white" });
  const yuk = o.yukseklik ?? 1.6, gen = yuk * oran, n = o.katman ?? 28, der = o.derinlik ?? 0.5;
  const grup = new THREE.Group();
  const geo = new THREE.PlaneGeometry(gen, yuk);
  const on = o.on ?? t.yazi, yan = o.yan ?? t.vurgu;
  for (let i = n - 1; i >= 0; i--) {
    const k = i / Math.max(1, n - 1);
    const renk = i === 0 ? on.clone() : yan.clone().multiplyScalar(0.55 + 0.45 * (1 - k));
    const m = new THREE.MeshBasicMaterial({ map: doku, color: renk, transparent: true, alphaTest: 0.35,
      depthWrite: i === 0, side: THREE.DoubleSide, toneMapped: i !== 0 });
    const d = new THREE.Mesh(geo, m);
    d.position.z = -k * der;
    d.renderOrder = n - i;
    grup.add(d);
  }
  // Parıltı süzmesi: ışık bandı yalnız harflerin içinde gezer (yazı dokusu maske). `parilti.uniforms.konum` -1→1
  // soldan sağa; renk 1'in üstünde olduğundan yalnız bu bant bloom alır.
  const parilti = new THREE.ShaderMaterial({
    uniforms: { harita: { value: doku }, konum: { value: -1.5 }, renk: { value: t.yazi.clone().multiplyScalar(2.4) },
      genislik: { value: 0.09 }, egim: { value: 0.35 }, guc: { value: 1 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: `uniform sampler2D harita; uniform float konum, genislik, egim, guc; uniform vec3 renk; varying vec2 vUv;
      void main(){ float m = texture2D(harita, vUv).a; float x = (vUv.x * 2.0 - 1.0) + (vUv.y - 0.5) * egim;
        float b = smoothstep(genislik, 0.0, abs(x - konum)) * m * guc; if (b < 0.004) discard;
        gl_FragColor = vec4(renk * b, b); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false,
  });
  const parMesh = new THREE.Mesh(geo, parilti);
  parMesh.position.z = 0.004;
  parMesh.renderOrder = n + 1;
  grup.add(parMesh);
  return { grup, gen, yuk, parilti };
};

// Yuvarlak köşeli panel (cam kart, katman): fiziksel malzeme, tema rengi.
export const panel = (gen: number, yuk: number, der = 0.08, malzeme?: THREE.Material) =>
  new THREE.Mesh(new RoundedBoxGeometry(gen, yuk, der, 6, Math.min(gen, yuk) * 0.06),
    malzeme ?? new THREE.MeshPhysicalMaterial({ color: tema().zemin, roughness: 0.35, metalness: 0.1, clearcoat: 1 }));

// Kapalı-form yay (cekirdek.ts yayCoz ile aynı aile): 0→1, aşma ve oturma; t saniye.
export const yay = (t: number, { frekans = 1.6, sonum = 0.42 } = {}) => {
  if (t <= 0) return 0;
  const w0 = 2 * Math.PI * frekans, z = Math.min(0.999, sonum), wd = w0 * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
};

// Kameranın nesneye dalışı: yörünge değil, tek yönlü yaklaşma (HF 3d.md). k 0→1.
export const dalis = (ctx: Ctx, k: number, bas: THREE.Vector3, son: THREE.Vector3, egri = 0.35) => {
  const orta = bas.clone().lerp(son, 0.5).add(new THREE.Vector3(0, egri, 0));
  const a = bas.clone().lerp(orta, k), b = orta.clone().lerp(son, k);
  ctx.kamera.position.copy(a.lerp(b, k));
  ctx.kamera.lookAt(ctx.hedef);
};

// Metin noktaları: yazıyı tuvale çizip dolu piksellerden tohumlu örnekler; parçacık hedefi olarak kullanılır.
export const metinNoktalari = (metin: string, adet: number, o: { genislik?: number; boy?: number; tohumDeger?: number } = {}) => {
  const { tuval } = yaziDokusu(metin, { boy: o.boy ?? 180, renk: "white", dolgu: 10 });
  const x = tuval.getContext("2d")!;
  const v = x.getImageData(0, 0, tuval.width, tuval.height).data;
  const dolu: number[] = [];
  for (let y = 0; y < tuval.height; y += 2) for (let xx = 0; xx < tuval.width; xx += 2)
    if (v[(y * tuval.width + xx) * 4 + 3] > 128) dolu.push(xx, y);
  const r = tohum(o.tohumDeger ?? 7), gen = o.genislik ?? 8, olcek = gen / tuval.width;
  const out = new Float32Array(adet * 3), n = dolu.length / 2;
  for (let i = 0; i < adet; i++) {
    const j = Math.floor(r() * n) * 2;
    out[i * 3] = (dolu[j] - tuval.width / 2) * olcek;
    out[i * 3 + 1] = -(dolu[j + 1] - tuval.height / 2) * olcek;
    out[i * 3 + 2] = (r() - 0.5) * 0.08;
  }
  return out;
};

// Yumuşak nokta dokusu (parçacık): radyal gradyan, renk yok (malzeme rengi verir).
export const noktaDokusu = () => {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const x = c.getContext("2d")!;
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.4, "rgba(255,255,255,0.55)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  x.fillStyle = g;
  x.fillRect(0, 0, 64, 64);
  const d = new THREE.CanvasTexture(c);
  d.colorSpace = THREE.SRGBColorSpace;
  return d;
};

const HFUC = { THREE, kur, sur, tema, tohum, yaziDokusu, katmanliYazi, panel, yay, dalis, metinNoktalari, noktaDokusu,
  mergeGeometries, RoundedBoxGeometry };
(window as unknown as { HFUC: typeof HFUC }).HFUC = HFUC;
export default HFUC;
