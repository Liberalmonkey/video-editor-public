import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { Bloom, EffectComposer, ToneMapping, Vignette } from "@react-three/postprocessing";
import { ToneMappingMode } from "postprocessing";
import * as THREE from "three";
import KATALOG from "./presetler.json";
import { useTema, yigin } from "../tema";

// WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Bake edilmiş yörüngeyi çizer; fizik burada koşmaz.
// Kare n her zaman bake'in n. kaydıdır: Remotion kareleri sırasız ve paralel çizse de görüntü aynıdır.

export type Parca = { sekil: "kure" | "kutu" | "silindir"; boyut: number[]; ofset?: number[]; aci?: number[]; renk: string; gizli?: boolean };
export type Bake = {
  surum: 1; preset: string; fps: number; kare: number; param: Record<string, any>;
  govdeler: { id: string; parca: Parca[]; ip?: number[]; iz?: boolean }[];
  yorunge: Record<string, number[]>;
  temas: { t: number; kare: number; a: string; b: string; hiz: number; guc: "yumusak" | "orta" | "sert" }[];
  kamera: number[][] | null; sabit_kamera: number[];
  olcum: { ad: string; deger: number[] }; etiket: string; zemin: { boy: number };
  renk?: Record<string, string>; font?: string;
};
type Isik = { yon: number[]; siddet: number; ortam: number; bloom: number; vinyet: number; golge: string; sicaklik?: number };

const ISIKLAR = (KATALOG as any).isik as Record<string, Isik>;
const RAD = Math.PI / 180;

// Kelvin → RGB (Tanner Helland yaklaşımı); ışık sıcaklığı preset rengini verir.
export const kelvin = (k = 6500): string => {
  const t = k / 100;
  const r = t <= 66 ? 255 : 329.7 * Math.pow(t - 60, -0.1332);
  const g = t <= 66 ? 99.47 * Math.log(t) - 161.12 : 288.12 * Math.pow(t - 60, -0.0755);
  const b = t >= 66 ? 255 : t <= 19 ? 0 : 138.52 * Math.log(t - 10) - 305.04;
  const c = (v: number) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
};

// İki hex rengi karıştırır (u: ikinciden pay). Işık sıcaklığı zemine ve sise biner: gün batımı sıcak, neon soğuk.
export const karistir = (a: string, b: string, u: number): string => {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  if (!/^#[0-9a-f]{6}$/i.test(a) || !/^#[0-9a-f]{6}$/i.test(b)) return a;
  const x = p(a), y = p(b);
  return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * u).toString(16).padStart(2, "0")).join("");
};

export const durum = (b: Bake, id: string, n: number) => {
  const y = b.yorunge[id];
  const i = Math.min(Math.max(0, n), b.kare - 1) * 7;
  return { p: [y[i], y[i + 1], y[i + 2]] as [number, number, number], q: [y[i + 3], y[i + 4], y[i + 5], y[i + 6]] as [number, number, number, number] };
};

// Kare kesirli: iki kayıt arası doğrusal konum, küresel dönüş. Hız izi (alt-kare hayaletleri) bunu kullanır.
export const araDurum = (b: Bake, id: string, f: number) => {
  const a = durum(b, id, Math.floor(f)), c = durum(b, id, Math.ceil(f)), u = f - Math.floor(f);
  const qa = new THREE.Quaternion(...a.q), qc = new THREE.Quaternion(...c.q);
  return { p: a.p.map((v, i) => v + (c.p[i] - v) * u) as [number, number, number], q: qa.slerp(qc, u) };
};

// Darbe: temas karesinden sonra 4 kare sönen değer (topun ezilmesi, kamera sarsıntısı).
export const darbe = (b: Bake, n: number, id?: string, enAz: "yumusak" | "orta" | "sert" = "yumusak") => {
  const sira = { yumusak: 0, orta: 1, sert: 2 };
  let v = 0;
  for (const t of b.temas) {
    if (id && t.a !== id && t.b !== id) continue;
    if (sira[t.guc] < sira[enAz]) continue;
    const d = n - t.kare;
    if (d >= 0 && d < 5) v = Math.max(v, (1 - d / 5) * Math.min(1, t.hiz / 8));
  }
  return v;
};

const Sekil: React.FC<{ pc: Parca; renk: (r: string) => string; opak?: number; golge?: boolean; isima?: number }> = ({ pc, renk, opak = 1, golge = true, isima = 0 }) => {
  if (pc.gizli) return null;
  const geo = pc.sekil === "kure" ? <sphereGeometry args={[pc.boyut[0], 48, 32]} />
    : pc.sekil === "silindir" ? <cylinderGeometry args={[pc.boyut[0], pc.boyut[0], pc.boyut[1] * 2, 40]} />
    : <boxGeometry args={[pc.boyut[0] * 2, pc.boyut[1] * 2, pc.boyut[2] * 2]} />;
  return (
    <mesh position={(pc.ofset ?? [0, 0, 0]) as any} rotation={(pc.aci ?? [0, 0, 0]).map((a) => a * RAD) as any} castShadow={golge} receiveShadow={golge}>
      {geo}
      {/* Vurgu rengi ışık yayar (bloom ile toplamsal parlama); boya gibi karışmaz. */}
      <meshStandardMaterial color={renk(pc.renk)} roughness={0.42} metalness={0.08} transparent={opak < 1} opacity={opak} depthWrite={opak === 1}
        emissive={pc.renk === "vurgu" && isima ? renk(pc.renk) : "#000000" /* ışımasız malzeme: fiziksel sabit, stil rengi değil */} emissiveIntensity={pc.renk === "vurgu" ? isima : 0} />
    </mesh>
  );
};

const Kamera: React.FC<{ b: Bake; n: number }> = ({ b, n }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  const k = b.kamera?.[Math.min(n, b.kare - 1)] ?? b.sabit_kamera;
  // Sert temasta 4 karelik sönümlü sarsıntı; ses ile aynı karede başlar.
  const s = darbe(b, n, undefined, "sert") * 0.06;
  camera.fov = 35;
  camera.position.set(k[0] + Math.sin(n * 2.7) * s, k[1] + Math.cos(n * 3.1) * s, k[2]);
  camera.lookAt(k[3], k[4], k[5]);
  camera.updateProjectionMatrix();
  return null;
};

const Ip: React.FC<{ a: number[]; b: number[]; renk: string }> = ({ a, b, renk }) => {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const boy = va.distanceTo(vb);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
  return (
    <mesh position={va.clone().add(vb).multiplyScalar(0.5)} quaternion={q}>
      <cylinderGeometry args={[0.012, 0.012, boy, 8]} />
      <meshStandardMaterial color={renk} />
    </mesh>
  );
};

// Ölçek ızgarası: 1 m göz, sönük. Parlak ızgara "hazır 3D şablon" görüntüsü verir; burada yalnız mesafe hissi için.
const Izgara: React.FC<{ boy: number; renk: string }> = ({ boy, renk }) => {
  const g = useMemo(() => {
    const h = new THREE.GridHelper(boy, Math.round(boy), renk, renk);
    const m = h.material as THREE.LineBasicMaterial;
    m.transparent = true; m.opacity = 0.14; m.depthWrite = false;
    return h;
  }, [boy, renk]);
  return <primitive object={g} position={[0, 0.002, 0]} />;
};

const Zemin: React.FC<{ b: Bake; renk: (r: string) => string }> = ({ b, renk }) => {
  const boy = b.zemin.boy;
  const araba = b.preset === "araba-ivme";
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[araba ? boy / 2 - 20 : 0, 0, 0]} receiveShadow>
        <planeGeometry args={[araba ? boy + 60 : boy, araba ? 16 : boy]} />
        <meshStandardMaterial color={renk("zemin")} roughness={0.9} />
      </mesh>
      {araba
        // Yol çizgileri hız hissinin ölçeğidir: 3 m aralıkla, kamera geçerken akar.
        ? Array.from({ length: Math.ceil((boy + 60) / 3) }, (_, i) => (
          <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[-20 + i * 3, 0.003, 1.4]}><planeGeometry args={[1.4, 0.12]} /><meshBasicMaterial color={renk("soluk")} /></mesh>))
        : <Izgara boy={boy} renk={renk("soluk")} />}
    </group>
  );
};

const Sahne3B: React.FC<{ b: Bake; isik: Isik; renk: (r: string) => string }> = ({ b, isik, renk }) => {
  const frame = useCurrentFrame();
  const n = Math.min(frame, b.kare - 1);
  const isikRenk = kelvin(isik.sicaklik);
  const [lx, ly, lz] = isik.yon;
  const sert = isik.golge === "sert";
  const isima = isik.bloom * 0.55;
  // Gökyüzü ve sis ışığın rengini taşır; pay sıcaklık 6500 K'dan uzaklaştıkça artar.
  const pay = Math.min(0.32, Math.abs((isik.sicaklik ?? 6500) - 6500) / 12000 + 0.06);
  const gok = karistir(renk("zemin"), isikRenk, pay);
  return (
    <>
      <Kamera b={b} n={n} />
      <color attach="background" args={[gok]} />
      <fog attach="fog" args={[gok, 25, 90]} />
      <ambientLight intensity={isik.ortam} color={isikRenk} />
      <hemisphereLight args={[isikRenk, renk("zemin"), isik.ortam * 0.6]} />
      <directionalLight position={[lx, ly, lz]} intensity={isik.siddet} color={isikRenk} castShadow
        shadow-mapSize={[2048, 2048]} shadow-radius={sert ? 1 : 6} shadow-bias={-0.0004}
        shadow-camera-left={-14} shadow-camera-right={14} shadow-camera-top={14} shadow-camera-bottom={-14} shadow-camera-far={80}>
      </directionalLight>
      <Zemin b={b} renk={renk} />
      {b.govdeler.map((g) => {
        const d = durum(b, g.id, n);
        const top = g.parca.length === 1 && g.parca[0].sekil === "kure";
        // Ezilme-uzama: top temas karesinde dünya y ekseninde %14'e kadar ezilir, 4 karede toparlanır.
        const ez = top ? darbe(b, n, g.id) * 0.14 : 0;
        const onceki = durum(b, g.id, n - 1).p;
        const hiz = Math.hypot(d.p[0] - onceki[0], d.p[1] - onceki[1], d.p[2] - onceki[2]) * b.fps;
        return (
          <React.Fragment key={g.id}>
            <group position={d.p} scale={[1 + ez * 0.5, 1 - ez, 1 + ez * 0.5]}>
              <group quaternion={new THREE.Quaternion(...d.q)}>
                {g.parca.map((pc, i) => <Sekil key={i} pc={pc} renk={renk} isima={isima} />)}
              </group>
            </group>
            {/* Hız izi: 180° obtüratör, yarım kare içinde 3 alt-kare hayaleti. Yavaş gövdede çizilmez. */}
            {hiz > 4 && [0.15, 0.3, 0.45].map((u) => {
              const a = araDurum(b, g.id, n - u);
              return (
                <group key={u} position={a.p} quaternion={a.q}>
                  {g.parca.map((pc, i) => <Sekil key={i} pc={pc} renk={renk} opak={0.22 * (1 - u)} golge={false} />)}
                </group>
              );
            })}
            {g.ip && <Ip a={g.ip} b={d.p} renk={renk("soluk")} />}
            {g.iz && Array.from({ length: Math.floor(n / 2) }, (_, i) => {
              const p = durum(b, g.id, i * 2).p;
              return <mesh key={i} position={p}><sphereGeometry args={[0.035, 10, 8]} /><meshBasicMaterial color={renk("vurgu")} transparent opacity={0.55} /></mesh>;
            })}
          </React.Fragment>
        );
      })}
      <EffectComposer multisampling={4}>
        <Bloom intensity={isik.bloom} luminanceThreshold={0.62} luminanceSmoothing={0.2} mipmapBlur />
        <Vignette darkness={isik.vinyet} offset={0.3} />
        <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      </EffectComposer>
    </>
  );
};

const birimli = (ad: string, v: number, tamsayi: boolean) => {
  const m = ad.match(/^(.*)\((.*)\)$/);
  const deger = tamsayi ? v.toFixed(0) : Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2);
  return m ? `${m[1].trim()} ${deger.replace(".", ",")} ${m[2]}` : `${ad} ${deger.replace(".", ",")}`;
};

export const FizikSahne: React.FC<{ url: string; s: Record<string, any> }> = ({ url, s }) => {
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const [b, setB] = useState<Bake | null>(null);
  const [h] = useState(() => delayRender(`fizik sahnesi ${url}`));
  useEffect(() => {
    let iptal = false;
    fetch(url).then((r) => r.json()).then((j) => { if (!iptal) setB(j); }).finally(() => continueRender(h));
    return () => { iptal = true; };
  }, [url, h]);
  const isik = ISIKLAR[s.isik?.preset ?? "studyo"] ?? ISIKLAR.studyo;
  // WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Bake'te renk yoksa stilin token'ı; sabit palet yok.
  const tema = useTema();
  const renk = useMemo(() => (r: string) => b?.renk?.[r] ?? (tema.renk as Record<string, string>)[r] ?? r, [b, tema]);
  if (!b) return null;
  const n = Math.min(frame, b.kare - 1);
  const goster = s.olcum !== false;
  // Sayım ölçümü (devrilen taş) ondalıksız yazılır.
  const tamsayi = b.olcum.deger.every(Number.isInteger);
  return (
    <AbsoluteFill style={{ background: renk("zemin") }}>
      <ThreeCanvas width={width} height={height} shadows gl={{ preserveDrawingBuffer: true, antialias: true }} camera={{ fov: 35, near: 0.05, far: 300 }}>
        <Sahne3B b={b} isik={isik} renk={renk} />
      </ThreeCanvas>
      {(b.etiket || goster) && (
        <div style={{ position: "absolute", left: width * 0.06, top: height * (width > height ? 0.08 : 0.14), fontFamily: yigin(b.font ?? tema.font.baslik), color: renk("yazi") }}>
          {b.etiket && <div style={{ fontSize: Math.round(Math.min(width, height) * 0.05), fontWeight: 800, lineHeight: 1.1 }}>{b.etiket}</div>}
          {goster && <div style={{ marginTop: 12, fontSize: Math.round(Math.min(width, height) * 0.034), fontWeight: 700, fontVariantNumeric: "tabular-nums", color: renk("vurgu") }}>{birimli(b.olcum.ad, b.olcum.deger[n], tamsayi)}</div>}
        </div>
      )}
    </AbsoluteFill>
  );
};
