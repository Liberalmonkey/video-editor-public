// Kapak alanı: video seç → fikir ve prompt → üret → düzelt (yazı ya da görsel) → master prompt ve teslim.
// WHY: bkz. wiki/decisions/0027-kapak-sayfasi.md, 0052-kapak-is-akisi-v2.md. agy isteyen her iş kuyrukta `vedit kapak` olarak çalışır.
import { Check, X } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { istek, sor } from "../../api";
import { useDepo } from "../../depo";
import { Bos, Dugme } from "../../ortak";
import { Secim } from "../alanlar";
import { AdayIzgarasi } from "./AdayIzgarasi";
import { FikirAdimi } from "./FikirAdimi";
import { GorselDuzelt } from "./GorselDuzelt";
import { MasterPrompt } from "./MasterPrompt";
import type { Aday, Durum } from "./tipler";
import { UretAdimi, type UretAyar } from "./UretAdimi";
import { VideoAdimi } from "./VideoAdimi";
import { adimDurumu, type AdimId, VARSAYILAN_PLATFORM } from "./yardimci";
import { type DuzYazi, YaziDuzenle } from "./YaziDuzenle";

const AYAR_ANAHTARI = "studio.kapak.ayar";
const ilkAyar = (): UretAyar => {
  const v: UretAyar = { adet: 1, kalip: "", stil: "", metinModel: "", gorselModel: "" };
  try { return { ...v, ...JSON.parse(localStorage.getItem(AYAR_ANAHTARI) ?? "{}"), kalip: "", stil: "" }; } catch { return v; }
};
const yaziOf = (a: Aday): DuzYazi => ({ n: a.n, satir1: a.satir1, satir2: a.satir2, vurgu: a.vurgu, yerlesim: a.yerlesim, olcek: a.olcek,
  karart: a.karart, kutu: a.kutu, kalip: a.kalip, stil: a.stil, ek: a.ek });

export const KapakPaneli: React.FC = () => {
  const aktif = useDepo((d) => d.aktif);
  const surum = useDepo((d) => d.surum);
  const biten = useDepo((d) => d.isler.filter((x) => x.komut === "kapak" && x.bitis).length);
  const calisiyor = useDepo((d) => d.isler.some((x) => x.komut === "kapak" && !x.bitis));
  const { hata, bildir } = useDepo();
  const [platform, setPlatform] = useState("youtube");
  const [video, setVideo] = useState<string | null>(null);
  const [seciliKare, setSeciliKare] = useState<number | null>(null);
  const [ayar, setAyar] = useState<UretAyar>(ilkAyar);
  const [d, setD] = useState<Durum | null>(null);
  const [duz, setDuz] = useState<DuzYazi | null>(null); // düzenlenen aday
  const [sekme, setSekme] = useState<"yazi" | "gorsel">("yazi");
  const [acik, setAcik] = useState<AdimId>("video");
  const [tazele, setTazele] = useState(0);
  const bekleyen = useRef<number | null>(null); // yeni aday açan iş başlarkenki son aday numarası
  const ilkAcilis = useRef(true);

  useEffect(() => {
    if (aktif) setPlatform(VARSAYILAN_PLATFORM[aktif.studyo] ?? "youtube");
    setSeciliKare(null);
    setVideo(null);
    ilkAcilis.current = true;
  }, [aktif?.studyo, aktif?.ad]);
  useEffect(() => { setDuz(null); bekleyen.current = null; }, [aktif?.studyo, aktif?.ad, platform]);
  useEffect(() => {
    try { localStorage.setItem(AYAR_ANAHTARI, JSON.stringify({ adet: ayar.adet, metinModel: ayar.metinModel, gorselModel: ayar.gorselModel })); } catch { /* özel pencere */ }
  }, [ayar.adet, ayar.metinModel, ayar.gorselModel]);
  useEffect(() => {
    if (!aktif) { setD(null); return; }
    let gecerli = true;
    istek(`/api/kapak/${aktif.studyo}/${aktif.ad}?${sor({ platform, video: video ?? undefined })}`)
      .then((r: Durum) => {
        if (!gecerli) return;
        setD(r);
        if (ilkAcilis.current) { // açılışta sıradaki adıma git
          ilkAcilis.current = false;
          setAcik(adimDurumu(r).find((a) => a.durum === "sirada")?.id ?? "uret");
        }
      })
      .catch((e) => { if (gecerli) hata(e); });
    return () => { gecerli = false; };
  }, [aktif?.studyo, aktif?.ad, platform, video, surum, biten, tazele]);
  // Varyasyon, görsel düzeltme ve içe alma yeni aday açar: aday görününce düzenleyici ona geçer. İş bitişi ile liste
  // yenilenmesi ayrı anlardır; bekleme yalnız yeni aday görününce biter.
  useEffect(() => {
    const once = bekleyen.current;
    const yeni = d?.adaylar.at(-1);
    if (once === null || !yeni || yeni.n <= once) return;
    bekleyen.current = null;
    setDuz(yaziOf(yeni));
    setAcik("duzelt");
  }, [d]);

  // Açılan adım görünür alana gelir: aday ızgarasındaki kalem düğmesi Düzelt'i sayfanın üstünde açar.
  useEffect(() => {
    document.getElementById(`kapak-adim-${acik}`)?.scrollIntoView({ block: "start", behavior: "smooth" });
  }, [acik, duz?.n]);

  const yenile = useCallback(() => setTazele((x) => x + 1), []);
  const bekle = useCallback(() => { bekleyen.current = d?.adaylar.at(-1)?.n ?? 0; }, [d]);
  const sec = async (n: number) => {
    if (!aktif) return;
    try {
      const r = await istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/sec`, { method: "POST", json: { platform, n } });
      bildir(`Teslim edildi: ${r.dosya} (master prompt yanında)`);
      yenile();
    } catch (e) { hata(e); }
  };
  const duzenle = (a: Aday | null) => {
    setDuz(a ? yaziOf(a) : null);
    if (a) setAcik("duzelt");
  };

  if (!aktif) return <div className="panel"><Bos baslik="Proje seçilmedi" metin="Kapak üretmek için Proje panelinden bir video seç." /></div>;
  const adimlar = adimDurumu(d);
  const duzAday = duz ? d?.adaylar.find((a) => a.n === duz.n) ?? null : null;

  // Düz fonksiyon (bileşen değil): render içinde tanımlı bileşen her render'da yeniden bağlanır ve alt durumu sıfırlardı.
  const adim = (id: AdimId, children: React.ReactNode, ek?: React.ReactNode) => {
    const a = adimlar.find((x) => x.id === id)!;
    const no = adimlar.indexOf(a) + 1;
    return (
      <section className={`kapak-adim ${a.durum}`} aria-labelledby={`kapak-adim-${id}`}>
        <button type="button" id={`kapak-adim-${id}`} className="kapak-adim-baslik" aria-expanded={acik === id} onClick={() => setAcik(id)}>
          <span className="kapak-adim-no">{a.durum === "tamam" ? <Check size={12} /> : no}</span> {a.ad} {ek}
        </button>
        {acik === id && children}
      </section>
    );
  };

  return (
    <div className="panel">
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <Secim etiket="Platform" deger={platform} degis={setPlatform} secenekler={[["youtube", "YouTube 16:9"], ["instagram", "Instagram Reels 9:16"]]} />
        <nav className="kapak-serit" aria-label="Kapak adımları">
          {adimlar.map((a, i) => (
            <button key={a.id} type="button" className={`kapak-serit-adim ${a.durum}`} aria-current={acik === a.id ? "step" : undefined}
              onClick={() => setAcik(a.id)} title={a.durum === "tamam" ? "Tamam" : a.durum === "sirada" ? "Sıradaki adım" : ""}>
              <span className="kapak-adim-no">{a.durum === "tamam" ? <Check size={11} /> : i + 1}</span>{a.ad}
            </button>
          ))}
        </nav>
        {calisiyor && <span className="rozet vurgu" role="status">Çalışıyor…</span>}
      </div>
      <div className="icerik">
        {!d ? <p className="ipucu" style={{ padding: 8 }}>Yükleniyor…</p> : (
          <>
            {adim("video", (
              <VideoAdimi d={d} video={video} setVideo={setVideo} seciliKare={seciliKare} setSeciliKare={setSeciliKare} yenile={yenile} />
            ), video && <span className="rozet">{d.videolar.find((v) => v.yol === video)?.ad}</span>)}
            {adim("fikir", (
              <FikirAdimi d={d} platform={platform} video={video} seciliKare={seciliKare} metinModel={ayar.metinModel} calisiyor={calisiyor} yenile={yenile} />
            ), !!d.oneri?.briefler.length && <span className="rozet">{d.oneri.briefler.length} öneri</span>)}
            {adim("uret", (
              <UretAdimi d={d} platform={platform} video={video} seciliKare={seciliKare} ayar={ayar} degis={(a) => setAyar((x) => ({ ...x, ...a }))}
                calisiyor={calisiyor} masterAc={() => setAcik("teslim")} />
            ))}
            {adim("duzelt", (
              duz && duzAday ? (
                <section className="kapak-duzenle" aria-label={`Kapak ${duz.n} düzeltme`}>
                  <div className="arac" style={{ justifyContent: "space-between" }}>
                    <div className="sekmeler" role="tablist" aria-label="Düzeltme türü">
                      <button type="button" role="tab" className="sekme" aria-selected={sekme === "yazi"} onClick={() => setSekme("yazi")}>Yazı</button>
                      <button type="button" role="tab" className="sekme" aria-selected={sekme === "gorsel"} onClick={() => setSekme("gorsel")}>Görsel</button>
                    </div>
                    <Dugme tur="ikon" onClick={() => setDuz(null)} title="Düzenleyiciyi kapat" aria-label="Düzenleyiciyi kapat"><X size={14} /></Dugme>
                  </div>
                  {sekme === "yazi"
                    ? <YaziDuzenle d={d} platform={platform} duz={duz} setDuz={setDuz} calisiyor={calisiyor} sec={sec} varyasyon={bekle} />
                    : <GorselDuzelt key={duz.n} d={d} a={duzAday} platform={platform} gorselModel={ayar.gorselModel} calisiyor={calisiyor} bekle={bekle} />}
                </section>
              ) : <p className="ipucu" style={{ padding: "0 8px" }}>Aşağıdaki adaylardan birinin kalem düğmesine bas: yazıyı ya da görseli düzelt.</p>
            ), duz && <span className="rozet vurgu">Aday #{duz.n}</span>)}
            {adim("teslim", (
              <MasterPrompt d={d} platform={platform} n={duz?.n ?? d.secim?.n ?? null} video={video} seciliKare={seciliKare} calisiyor={calisiyor} bekle={bekle} />
            ))}
            <h3 className="kapak-adaylar-baslik">Adaylar</h3>
            <AdayIzgarasi d={d} duzN={duz?.n ?? null} duzenle={duzenle} sec={sec} calisiyor={calisiyor} />
          </>
        )}
      </div>
    </div>
  );
};
