// WHY: bkz. wiki/decisions/0047-kural-deposu.md. Kurallar sayfası: QC'nin ve kullanıcının YAP/YAPMA kuralları.
// Silme mezar taşı bırakır: QC aynı kuralı yeniden önermez; yeniden açmak için "Silinen" süzgecinden aç.
import { Check, Download, Eye, Pencil, Plus, Power, Trash2, Upload, X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Diyalog, DosyaSec, Dugme, Iskelet } from "../ortak";

export interface Kanit { proje?: string | null; zaman?: number | null; kare?: string | null; not?: string | null }
export interface Kural {
  id: string; metin: string; neden: string; kapsam: "global" | "studyo" | "stil" | "proje"; kapsam_deger?: string | null;
  hedef_rol: "E1" | "E2" | "E3" | "hepsi"; kategori: string; onem: "P0" | "P1" | "P2"; kaynak: string; kanit: Kanit[];
  durum: "aktif" | "oneri" | "pasif" | "silinen"; tekrar: number; olcut?: string | null; olusturma: string; guncelleme: string;
}
interface Ozet { kurallar: Kural[]; ayar: { onay_bekle: boolean; butce_token: number }; kategoriler: string[]; kapi_onerileri: string[] }

const ROL_AD: Record<string, string> = { E1: "Kesim", E2: "Grafik", E3: "Ses ve stil", hepsi: "Hepsi" };
const DURUM_AD: Record<string, string> = { aktif: "Etkin", oneri: "Onay bekliyor", pasif: "Kapalı", silinen: "Silinen" };
const BOS_TASLAK = { metin: "YAP: ", neden: "", kategori: "genel", onem: "P1", hedef_rol: "hepsi", kapsam: "global", kapsam_deger: "", olcut: "" };

// Süzgeç ve arama saf fonksiyon: panel testinde sınanır.
export const suz = (l: Kural[], f: { ara: string; durum: string; rol: string; kategori: string; onem: string }) => {
  const a = f.ara.trim().toLocaleLowerCase("tr-TR");
  return l.filter((k) => (f.durum === "hepsi" ? k.durum !== "silinen" : k.durum === f.durum)
    && (f.rol === "hepsi" || k.hedef_rol === f.rol) && (f.kategori === "hepsi" || k.kategori === f.kategori)
    && (f.onem === "hepsi" || k.onem === f.onem)
    && (!a || `${k.id} ${k.metin} ${k.neden}`.toLocaleLowerCase("tr-TR").includes(a)))
    .sort((x, y) => x.onem.localeCompare(y.onem) || y.tekrar - x.tekrar || x.id.localeCompare(y.id));
};

export const KurallarPaneli: React.FC = () => {
  const { hata, bildir, onayla } = useDepo();
  const [o, setO] = useState<Ozet | null>(null);
  const [f, setF] = useState({ ara: "", durum: "hepsi", rol: "hepsi", kategori: "hepsi", onem: "hepsi" });
  const [secili, setSecili] = useState<Set<string>>(new Set());
  const [taslak, setTaslak] = useState<(typeof BOS_TASLAK & { id?: string }) | null>(null);
  const [kare, setKare] = useState<string | null>(null);

  const al = () => istek<Ozet>("/api/kurallar").then(setO).catch(hata);
  useEffect(() => { al(); }, []);
  const liste = useMemo(() => (o ? suz(o.kurallar, f) : []), [o, f]);
  const bekleyen = o?.kurallar.filter((k) => k.durum === "oneri").length ?? 0;

  const durum = async (idler: string[], d: Kural["durum"]) => {
    if (!idler.length) return;
    if (d === "silinen" && !(await onayla({ baslik: `${idler.length} kural silinsin mi?`, metin: "Silinen kural editörlere gitmez ve kalite kontrol onu yeniden önermez. Silinen süzgecinden geri açabilirsin.", onay: "Sil", tehlike: true }))) return;
    try {
      setO(await istek<Ozet>("/api/kurallar/durum", { method: "POST", json: { idler, durum: d } }));
      setSecili(new Set());
      bildir(`${idler.length} kural: ${DURUM_AD[d].toLocaleLowerCase("tr-TR")}`);
    } catch (e) { hata(e); }
  };
  const kaydet = async () => {
    if (!taslak) return;
    const { id, ...g } = taslak;
    const govde = { ...g, kapsam_deger: g.kapsam === "global" ? null : g.kapsam_deger || null, olcut: g.olcut || null };
    try {
      const r = await istek<Ozet>(id ? `/api/kurallar/${id}` : "/api/kurallar", { method: id ? "PATCH" : "POST", json: govde });
      setO(r); setTaslak(null); bildir(id ? "Kural güncellendi" : "Kural eklendi");
    } catch (e) { hata(e); }
  };
  const disa = async () => {
    try {
      const d = await istek("/api/kurallar/disa");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 1)], { type: "application/json" }));
      a.download = "kurallar.json"; a.click(); URL.revokeObjectURL(a.href);
    } catch (e) { hata(e); }
  };
  const ice = async (dosyalar: File[]) => {
    try {
      const r = await istek<Ozet & { eklenen: number }>("/api/kurallar/ice", { method: "POST", json: JSON.parse(await dosyalar[0].text()) });
      setO(r); bildir(`${r.eklenen} yeni kural içe aktarıldı (benzeri olanlar atlandı)`);
    } catch (e) { hata(e); }
  };
  const onayAyari = async (v: boolean) => {
    try { setO(await istek<Ozet>("/api/kurallar/ayar", { method: "PUT", json: { ...o!.ayar, onay_bekle: v } })); } catch (e) { hata(e); }
  };

  if (!o) return <div className="panel"><Iskelet /></div>;
  const sec = (s: string, d: string, secenek: [string, string][]) => (
    <select value={s} onChange={(e) => setF({ ...f, [d]: e.target.value })} aria-label={d}>{secenek.map(([v, ad]) => <option key={v} value={v}>{ad}</option>)}</select>
  );
  return (
    <div className="panel">
      <div className="arac" style={{ flexWrap: "wrap", gap: 6 }}>
        <input type="search" placeholder="Kurallarda ara" value={f.ara} onChange={(e) => setF({ ...f, ara: e.target.value })} style={{ flex: 1, minWidth: 140 }} />
        {sec(f.durum, "durum", [["hepsi", "Silinmemiş"], ["aktif", "Etkin"], ["oneri", `Onay bekliyor (${bekleyen})`], ["pasif", "Kapalı"], ["silinen", "Silinen"]])}
        {sec(f.rol, "rol", Object.entries(ROL_AD).map(([v, a]) => [v, v === "hepsi" ? "Tüm roller" : a]))}
        {sec(f.kategori, "kategori", [["hepsi", "Tüm kategoriler"], ...o.kategoriler.map((k) => [k, k] as [string, string])])}
        {sec(f.onem, "onem", [["hepsi", "Tüm önem"], ["P0", "P0"], ["P1", "P1"], ["P2", "P2"]])}
        <Dugme tur="birincil" onClick={() => setTaslak({ ...BOS_TASLAK })}><Plus size={14} /> Kural ekle</Dugme>
      </div>
      <div className="arac" style={{ flexWrap: "wrap", gap: 6 }}>
        <label title="Kapalıyken kalite kontrolün yeni kuralı hemen etkin olur">
          <input type="checkbox" checked={o.ayar.onay_bekle} onChange={(e) => onayAyari(e.target.checked)} /> Yeni kurallar onayımı beklesin
        </label>
        <span style={{ flex: 1 }} />
        {secili.size > 0 && <>
          <Dugme onClick={() => durum([...secili], "aktif")}><Power size={14} /> Aç</Dugme>
          <Dugme onClick={() => durum([...secili], "pasif")}>Kapat</Dugme>
          <Dugme tur="tehlike" onClick={() => durum([...secili], "silinen")}><Trash2 size={14} /> Sil ({secili.size})</Dugme>
        </>}
        <Dugme onClick={disa} title="Dışa aktar"><Download size={14} /></Dugme>
        <DosyaSec kabul=".json" sec={ice}><Upload size={14} /></DosyaSec>
      </div>
      {!!o.kapi_onerileri.length && <p className="ipucu" style={{ padding: "4px 8px", margin: 0 }}>Koda kapı olarak yazılması önerilen (iki kez tekrarlandı, ölçülebilir): {o.kapi_onerileri.join(", ")}</p>}
      <div className="icerik">
        {!liste.length && <Bos baslik="Kural yok" metin={f.ara ? "Aramayla eşleşen kural yok." : "Kalite kontrol bulgularından ve senin düzeltmelerinden kural oluşur."} />}
        {liste.map((k) => (
          <div key={k.id} className="bulgu" style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 8, alignItems: "start", opacity: k.durum === "pasif" || k.durum === "silinen" ? 0.6 : 1 }}>
            <input type="checkbox" aria-label={`${k.id} seç`} checked={secili.has(k.id)} onChange={(e) => { const s = new Set(secili); if (e.target.checked) s.add(k.id); else s.delete(k.id); setSecili(s); }} />
            <div style={{ minWidth: 0 }}>
              <div className="bulgu-ust">
                <span className={`rozet ${({ P0: "hata", P1: "uyari", P2: "" } as Record<string, string>)[k.onem]}`}>{k.onem}</span>
                <span className="bulgu-kod">{k.id}</span>
                <span className="ipucu">{ROL_AD[k.hedef_rol]} · {k.kategori} · {k.kapsam === "global" ? "genel" : `${k.kapsam}: ${k.kapsam_deger}`}{k.tekrar > 1 ? ` · ×${k.tekrar}` : ""} · {k.kaynak === "kullanici" ? "senin" : k.kaynak}</span>
                {k.durum !== "aktif" && <span className="rozet">{DURUM_AD[k.durum]}</span>}
              </div>
              <div style={{ wordBreak: "break-word" }}>{k.metin}</div>
              {k.neden && <div className="ipucu">Neden: {k.neden}</div>}
              {k.olcut && <div className="ipucu">Kapı: {k.olcut}</div>}
            </div>
            <div style={{ display: "flex", gap: 2 }}>
              {k.durum === "oneri" && <>
                <Dugme tur="ikon" title="Onayla" onClick={() => durum([k.id], "aktif")}><Check size={14} /></Dugme>
                <Dugme tur="ikon" title="Reddet (bir daha önerilmez)" onClick={() => durum([k.id], "silinen")}><X size={14} /></Dugme>
              </>}
              {k.kanit.some((x) => x.kare) && <Dugme tur="ikon" title="Kanıt karesi" onClick={() => setKare(k.kanit.filter((x) => x.kare).at(-1)!.kare!)}><Eye size={14} /></Dugme>}
              <Dugme tur="ikon" title="Düzenle" onClick={() => setTaslak({ id: k.id, metin: k.metin, neden: k.neden, kategori: k.kategori, onem: k.onem, hedef_rol: k.hedef_rol, kapsam: k.kapsam, kapsam_deger: k.kapsam_deger ?? "", olcut: k.olcut ?? "" })}><Pencil size={14} /></Dugme>
              {k.durum === "aktif" ? <Dugme tur="ikon" title="Kapat (editörlere gitmez)" onClick={() => durum([k.id], "pasif")}><Power size={14} /></Dugme>
                : k.durum !== "oneri" && <Dugme tur="ikon" title="Aç" onClick={() => durum([k.id], "aktif")}><Power size={14} /></Dugme>}
              {k.durum !== "silinen" && <Dugme tur="ikon" title="Sil" onClick={() => durum([k.id], "silinen")}><Trash2 size={14} /></Dugme>}
            </div>
          </div>
        ))}
      </div>
      <Diyalog acik={!!taslak} kapat={() => setTaslak(null)}>
        {taslak && <>
          <h2>{taslak.id ? `${taslak.id} düzenle` : "Yeni kural"}</h2>
          <label>Kural (tek satır, YAP: ya da YAPMA: ile başlar)
            <textarea rows={2} value={taslak.metin} onChange={(e) => setTaslak({ ...taslak, metin: e.target.value })} />
          </label>
          <label>Neden<input value={taslak.neden} onChange={(e) => setTaslak({ ...taslak, neden: e.target.value })} /></label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <label>Rol<select value={taslak.hedef_rol} onChange={(e) => setTaslak({ ...taslak, hedef_rol: e.target.value })}>{Object.entries(ROL_AD).map(([v, a]) => <option key={v} value={v}>{a}</option>)}</select></label>
            <label>Kategori<select value={taslak.kategori} onChange={(e) => setTaslak({ ...taslak, kategori: e.target.value })}>{o.kategoriler.map((k) => <option key={k}>{k}</option>)}</select></label>
            <label>Önem<select value={taslak.onem} onChange={(e) => setTaslak({ ...taslak, onem: e.target.value })}>{["P0", "P1", "P2"].map((x) => <option key={x}>{x}</option>)}</select></label>
            <label>Kapsam<select value={taslak.kapsam} onChange={(e) => setTaslak({ ...taslak, kapsam: e.target.value })}>{[["global", "Genel"], ["studyo", "Stüdyo"], ["stil", "Stil"], ["proje", "Proje"]].map(([v, a]) => <option key={v} value={v}>{a}</option>)}</select></label>
            {taslak.kapsam !== "global" && <label>Değer<input value={taslak.kapsam_deger} placeholder="ör. instagram" onChange={(e) => setTaslak({ ...taslak, kapsam_deger: e.target.value })} /></label>}
          </div>
          <label>Makine denetimi (isteğe bağlı)<input value={taslak.olcut} placeholder="ör. kurgu-denetle MOTION_SURE" onChange={(e) => setTaslak({ ...taslak, olcut: e.target.value })} /></label>
          <div className="eylemler">
            <Dugme onClick={() => setTaslak(null)}>Vazgeç</Dugme>
            <Dugme tur="birincil" onClick={kaydet} disabled={!/^(YAP|YAPMA): \S/.test(taslak.metin.trim())}>Kaydet</Dugme>
          </div>
        </>}
      </Diyalog>
      <Diyalog acik={!!kare} kapat={() => setKare(null)}>
        {kare && <><h2>Kanıt karesi</h2><img src={`/api/kurallar/kare/${kare.split("/").map(encodeURIComponent).join("/")}`} alt="Kuralı doğuran kare" style={{ maxWidth: "100%", maxHeight: "70vh" }} /></>}
      </Diyalog>
    </div>
  );
};
