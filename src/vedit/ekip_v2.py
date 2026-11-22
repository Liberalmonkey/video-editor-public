"""Ekip motoru v2: sözleşme, paralel düzenleme, deterministik birleştirme, tek QC, tek düzeltme (ADR 0048).

WHY: v1 (ADR 0044) E1'i önce, E2 ve E3'ü sonra çalıştırıyor, en çok üç tam tur dönüyordu. Her editör bütün kataloğu,
manifestleri ve kurgunun tamamını okuyordu (ölçülen koşu: Claude slotlarında 3,33 M token, 3688 ajan saniyesi).
v2 akışı sabittir, açık uçlu döngü yoktur:
  1. sözleşme  : tek ucuz E1 çağrısı (hook) + vedit → ekip/sozlesme.json (kesim iskeleti, ayrılmış bölgeler, ritim, stil, kurallar)
  2. düzenleme : E1, E2, E3 aynı anda; her biri yalnız kendi katmanına yama yazar, olayları kelimeye çapalar, panoya not bırakır
  3. birleştirme: deterministik; E2/E3 tabana uygulanır, çapasız klipler çapalanır, E1 uygulanır, çapalar yeniden eşlenir,
                 çakışan grafik itilir ya da sahibine bulgu olur; tek render
  4. QC        : K1, K2, K3 aynı anda ve bir kez, ortak kare/ölçüm paketiyle; birleştirici tekilleştirir, tek sahibe yollar
  5. düzeltme  : yalnız P0/P1 bulgusu olan editör, yalnız bulgu farkıyla, bir kez; etkilenen aralıklar yeniden render edilip eklenir
  6. son       : deterministik denetimler; ikinci QC yalnız P0 kapısı düşerse ve yalnız o aralıkta
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import ValidationError

from . import aiedit, capa, ekip, ff, hizli, kural, kurgu, kurgu_kalite, native_motion, paths, tema_token, yuz_bolge
from .ekip_sema import EDITORLER, HEDEF, KONTROLLER, ROL_ADI, ROL_TANIM, EkipAyar, Mesaj, Yama
from .schemas import Kurgu

ROL_KLASORU = ekip.ROL_KLASORU

# ---------------------------------------------------------------- sahiplik

def sahip(k: Kurgu, iz: str) -> str:
    """Katmanın sahibi: E1 V1 (+A1), E2 diğer görüntü izleri, E3 diğer ses izleri."""
    tur = next((i.tur for i in k.izler if i.id == iz), None)
    if iz in ("V1", "A1"):
        return "E1"
    return "E2" if tur == "video" else "E3"


ALANLAR = {"E1": {"isaretler", "hook"}, "E2": set(), "E3": {"altyazi", "motion_tema"}}


HF_EN_BUYUK = 200_000  # bayt; tek kompozisyon HTML'i


def hf_hatalari(rol: str, y: Yama) -> list[str]:
    """`hf` alanı yalnız E2'nindir; ad kök dışına çıkamaz, içerik HTML kompozisyonudur (ADR 0050)."""
    h = []
    if y.hf and rol != "E2":
        h.append(f"{rol}: hf alanı bu editörün değil")
    for ad, html in y.hf.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", ad):
            h.append(f"{rol}: geçersiz kompozisyon adı '{ad}'")
        elif len(html.encode("utf-8")) > HF_EN_BUYUK or "data-composition-id" not in html:
            h.append(f"{rol}: {ad} geçerli bir HyperFrames kompozisyonu değil (data-composition-id yok ya da çok büyük)")
    return h


def hf_yaz(p, y: Yama) -> list[str]:
    """E2'nin döndürdüğü kompozisyonları `work/edit/hf/<ad>/index.html` olarak yazar; yazılan adları döner."""
    from . import hf_grafik
    yazilan = []
    if hf_hatalari("E2", y):
        return yazilan
    for ad, html in y.hf.items():
        f = hf_grafik.proje_kok(p.work) / ad / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
        yazilan.append(ad)
    return yazilan


def yama_hatalari(k: Kurgu, rol: str, y: Yama) -> list[str]:
    var = {c.id: c for c in k.klipler}
    h = []
    for c in y.ekle:
        if c.get("id") in var:
            h.append(f"{rol}: {c.get('id')} zaten var (ekle değil guncelle)")
        if sahip(k, c.get("iz", "")) != rol:
            h.append(f"{rol}: {c.get('id')} {c.get('iz')} izine eklenemez (sahibi {sahip(k, c.get('iz', ''))})")
    for g in y.guncelle:
        c = var.get(g.get("id"))
        if c is None:
            h.append(f"{rol}: güncellenecek {g.get('id')} yok")
        elif sahip(k, c.iz) != rol or ("iz" in g and sahip(k, g["iz"]) != rol):
            h.append(f"{rol}: {c.id} başka editörün nesnesi ({c.iz})")
    for kid in y.sil:
        c = var.get(kid)
        if c is not None and sahip(k, c.iz) != rol:
            h.append(f"{rol}: {kid} başka editörün nesnesi, silinemez")
    for alan in ("isaretler", "altyazi", "motion_tema", "hook"):
        if getattr(y, alan) is not None and alan not in ALANLAR[rol]:
            h.append(f"{rol}: {alan} alanı bu editörün değil")
    h += hf_hatalari(rol, y)
    for kid, kay in y.kaynaklar.items():
        if kid in k.kaynaklar and k.kaynaklar[kid].model_dump() != {**k.kaynaklar[kid].model_dump(), **kay}:
            h.append(f"{rol}: mevcut kaynak değiştirilemez: {kid}")
    return h


def _capa_bas(k: Kurgu, c: dict) -> float | None:
    """`bas` yazılmamış çapalı klibin sekans zamanı (çapa kelimesinden, `once_kare` önce)."""
    ca = c.get("capa") or {}
    kel = k.kelimeler.get(ca.get("kaynak") or "") or []
    i = ca.get("kelime")
    t = kel[i].s if isinstance(i, int) and 0 <= i < len(kel) else ca.get("t")
    if t is None:
        return None
    s = capa.sekans_zamani(k, ca["kaynak"], t)
    return None if s is None else round(max(0.0, s - (ca.get("once_kare") or 0) / k.sekans.fps), 3)


def _kurgu_dict(k: Kurgu, y: Yama, ekle: list[dict], gun: dict[str, dict], kaynaklar: dict) -> dict:
    d = k.model_dump()
    sil = set(y.sil)
    d["klipler"] = [{**c, **gun.get(c["id"], {})} for c in d["klipler"] if c["id"] not in sil] + ekle
    for kid, kay in kaynaklar.items():
        d["kaynaklar"].setdefault(kid, kay)
    for alan in ("isaretler", "altyazi", "motion_tema"):
        if getattr(y, alan) is not None:
            d[alan] = getattr(y, alan)
    return d


def yama_uygula(k: Kurgu, rol: str, y: Yama, dusen: list[str] | None = None) -> Kurgu:
    """Sahiplik denetimli uygulama; sahiplik hatası SystemExit (yama birleşmez).
    Şema hatasında yalnız hatalı öğeler düşer, gerisi birleşir; düşenler `dusen` listesine yazılır."""
    # WHY: instagram/1 v2 koşularında tek bozuk öğe (kaynakta `dosya`, çapalı klipte `bas` yok) bütün E2/E3 katmanını düşürdü.
    # Başka editörün skaler alanı (ör. E2'nin motion_tema'sı) yamayı düşürmez; yalnız o alan düşer.
    yabanci = [a for a in ("isaretler", "altyazi", "motion_tema", "hook") if getattr(y, a) is not None and a not in ALANLAR[rol]]
    if yabanci:
        y = y.model_copy(update={a: None for a in yabanci})
    if h := yama_hatalari(k, rol, y):
        raise SystemExit("; ".join(h))
    ekle = copy.deepcopy(list(y.ekle))
    for c in ekle:
        if "bas" not in c and c.get("capa"):
            if (b := _capa_bas(k, c)) is not None:
                c["bas"] = b
        if "sure" not in c:
            if c.get("tur") == "motion" and isinstance(c.get("bilesen"), dict):
                m = (native_motion.kayitlar().get(c["bilesen"].get("ad")) or {}).get("meta", {})
                c["sure"] = (m.get("sure") or {}).get("varsayilan") or 1.5
            elif c.get("tur") == "motion" and isinstance(c.get("hf"), dict):
                from . import hf_grafik  # süre kompozisyonun kökünden: önce bu yamadaki, sonra kütüphanedeki
                ad = c["hf"].get("ad") or ""
                try:
                    if ad in y.hf:
                        c["sure"] = hf_grafik.olcu_metin(y.hf[ad], ad)["sure"]
                    elif d := hf_grafik.bul(ad):
                        c["sure"] = hf_grafik.olcu(d)["sure"]
                except ValueError:
                    pass
                c.setdefault("sure", 2.0)
            elif c.get("olay"):
                c["sure"] = 0.3  # olaysesi: klip süresi yalnız görsel işarettir
    gun = {g["id"]: g for g in copy.deepcopy(list(y.guncelle))}
    kaynaklar = dict(y.kaynaklar)
    if dusen is not None:
        dusen += [f"{rol}:{a}" for a in yabanci]
    d = _kurgu_dict(k, y, ekle, gun, kaynaklar)
    try:
        return Kurgu.model_validate(d)
    except ValidationError as e:
        hata = e
    # Bilinmeyen alt alan (ör. ses.seviye) öğeyi düşürmez: alan atılır, bir kez yeniden denenir.
    fazla = [er["loc"] for er in hata.errors() if er.get("type") == "extra_forbidden" and len(er.get("loc", ())) >= 3
             and er["loc"][0] == "klipler" and isinstance(er["loc"][1], int) and er["loc"][1] < len(d["klipler"])]
    if fazla:
        ek_id = {c.get("id") for c in ekle}
        for loc in fazla:
            c = d["klipler"][loc[1]]
            hedef = next((x for x in ekle if x.get("id") == c["id"]), None) if c["id"] in ek_id else gun.get(c["id"])
            if hedef is None:
                continue
            for anahtar in loc[2:-1]:
                hedef = hedef.get(anahtar) if isinstance(hedef, dict) else None
            if isinstance(hedef, dict) and hedef.pop(loc[-1], None) is not None and dusen is not None:
                dusen.append(f"{rol}:{c['id']}." + ".".join(str(x) for x in loc[2:]))
        d = _kurgu_dict(k, y, ekle, gun, kaynaklar)
        try:
            return Kurgu.model_validate(d)
        except ValidationError as e:
            hata = e
    kotu_klip, kotu_kay = set(), set()
    for er in hata.errors():
        loc = er.get("loc", ())
        if len(loc) >= 2 and loc[0] == "klipler" and isinstance(loc[1], int):
            kotu_klip.add(d["klipler"][loc[1]]["id"] if loc[1] < len(d["klipler"]) else None)
        elif len(loc) >= 2 and loc[0] == "kaynaklar" and loc[1] in kaynaklar:
            kotu_kay.add(loc[1])
    if not kotu_klip and not kotu_kay:
        raise SystemExit(f"{rol}: şema: {str(hata)[:500]}") from hata
    kaynaklar = {kid: v for kid, v in kaynaklar.items() if kid not in kotu_kay}
    yeni_ekle = [c for c in ekle if c.get("id") not in kotu_klip and c.get("kaynak") not in kotu_kay]
    gun = {kid: g for kid, g in gun.items() if kid not in kotu_klip}
    atilan = [c.get("id") for c in ekle if c not in yeni_ekle] + sorted(x for x in kotu_klip if x in {g.get("id") for g in y.guncelle}) + sorted(kotu_kay)
    try:
        sonuc = Kurgu.model_validate(_kurgu_dict(k, y, yeni_ekle, gun, kaynaklar))
    except ValidationError as e:
        raise SystemExit(f"{rol}: şema: {str(e)[:500]}") from e
    if dusen is not None:
        dusen += [f"{rol}:{a}" for a in atilan]
    return sonuc



# ---------------------------------------------------------------- birleştirme

def _konusma_kaynagi(k: Kurgu, t: float) -> str | None:
    """t anında V1'de görünen konuşma kaynağı (çapalama için)."""
    for c in k.klipler:
        if c.iz == "V1" and c.tur == "video" and c.kaynak and c.bas <= t < c.bas + c.sure and k.kelimeler.get(c.kaynak):
            return c.kaynak
    return None


def birlestir(taban: Kurgu, yamalar: dict[str, Yama]) -> tuple[Kurgu, dict]:
    """E2 ve E3 tabana (E1'den önceki kesime) uygulanır; çapasız olayları vedit çapalar; sonra E1; çapalar yeniden eşlenir."""
    rapor: dict = {"uygulanan": [], "red": {}, "dusen": [], "capalanan": 0, "tasinan": [], "capa_bulgu": [], "itilen": [], "cakisma_bulgu": []}
    k = taban
    for rol in ("E2", "E3"):
        if rol in yamalar:
            try:
                k = yama_uygula(k, rol, yamalar[rol], rapor["dusen"])
                rapor["uygulanan"].append(rol)
            except SystemExit as e:
                rapor["red"][rol] = str(e)
    for c in k.klipler:
        if c.capa is None and sahip(k, c.iz) in ("E2", "E3") and (kay := _konusma_kaynagi(k, c.bas + 0.1)):
            capa.capala(k, c, kay)
            rapor["capalanan"] += c.capa is not None
    if "E1" in yamalar:
        try:
            k = yama_uygula(k, "E1", yamalar["E1"], rapor["dusen"])
            rapor["uygulanan"].append("E1")
        except SystemExit as e:
            rapor["red"]["E1"] = str(e)
    rapor["tasinan"], rapor["capa_bulgu"] = capa.esle(k)
    rapor["itilen"], rapor["cakisma_bulgu"] = cakisma_coz(k)
    rapor["sigdirilan"] = cekime_sigdir(k)
    rapor["kirpilan"] = sona_kirp(k)
    return k, rapor


CEKIME_BAGLI = {"ikon", "kart", "cizim", "cta", "parcacik"}


def cekime_sigdir(k: Kurgu) -> list[str]:
    """Çekime bağlı native grafik başladığı V1 çekiminin sonunu aşmaz: önce kısalır (meta `min` altına inmez), yetmezse öne kayar."""
    # WHY: instagram/1 v2 koşularında ikonlar kesimden sonra 0,3-0,6 sn sonraki çekime taştı (piksel-8bit'te QC P0, temiz-kurumsal'da kaçtı).
    v1 = sorted((c for c in k.klipler if c.iz == "V1"), key=lambda c: c.bas)
    degisen = []
    for c in k.klipler:
        if c.tur != "motion" or not c.bilesen:
            continue
        m = (native_motion.kayitlar().get(c.bilesen.ad) or {}).get("meta", {})
        if m.get("tur") not in CEKIME_BAGLI:
            continue
        cek = next((v for v in v1 if v.bas - 1e-3 <= c.bas < v.bas + v.sure), None)
        if cek is None:
            continue
        son = cek.bas + cek.sure
        if c.bas + c.sure <= son + 1e-3:
            continue
        alt = (m.get("sure") or {}).get("min") or native_motion.SURE_SINIRI.get(m.get("tur"), (0.5, None))[0]
        if son - c.bas >= alt:
            c.sure = round(son - c.bas, 3)
        elif son - alt >= cek.bas:
            c.bas, c.sure = round(son - alt, 3), alt
        else:
            continue  # çekim grafikten kısa: dokunulmaz, QC görür
        degisen.append(c.id)
    return degisen


def sona_kirp(k: Kurgu) -> list[str]:
    """Sekans V1 ile biter: E1 kesimi kısalttıysa taşan müzik/grafik kırpılır, sonra başlayan düşer (yerinde)."""
    # WHY: instagram/1 piksel-8bit v2 koşusunda A3 müziği V1 sonundan 4,3 sn taştı; taslağın sonu siyah kaldı.
    v1 = [c for c in k.klipler if c.iz == "V1"]
    if not v1:
        return []
    son = max(c.bas + c.sure for c in v1)
    degisen, kalan = [], []
    for c in k.klipler:
        if c.iz != "V1" and c.bas >= son - 0.05:
            degisen.append(c.id)
            continue
        if c.iz != "V1" and c.bas + c.sure > son + 1e-3:
            c.sure = round(son - c.bas, 3)
            if c.ses is not None and c.tur == "ses":
                c.ses.fade_out = max(c.ses.fade_out, min(1.0, c.sure / 4))
            degisen.append(c.id)
        kalan.append(c)
    k.klipler[:] = kalan
    return degisen


def _hero(c) -> bool:
    if not c.bilesen:
        return c.tur == "sahne" or (c.metin_stil or {}).get("tip") in ("anahtar", "cagri", "bolum")
    m = (native_motion.kayitlar().get(c.bilesen.ad) or {}).get("meta", {})
    return c.bilesen.hero if c.bilesen.hero is not None else bool(m.get("hero"))


def cakisma_coz(k: Kurgu, *, en_cok_itme: float = 0.6) -> tuple[list[str], list[dict]]:
    """Öncelik: konuşma/kesim > okunurluk > grafik > SFX. Çakışan grafik güvenli payda itilir, olmuyorsa sahibine bulgu."""
    itilen, bulgu = [], []
    grafik = sorted((c for c in k.klipler if sahip(k, c.iz) == "E2" and c.tur in ("motion", "metin", "sahne", "gorsel")), key=lambda c: c.bas)
    # 1) Kesim geçişinin üstüne binen grafik: geçiş bitene kadar it (geçiş okunurluğu bozar).
    gecisler = [(c.bas - c.gecis_giris.sure / 2, c.bas + c.gecis_giris.sure / 2) for c in k.klipler
                if c.iz == "V1" and c.gecis_giris and c.gecis_giris.tur not in ("kararma",)]
    for c in grafik:
        for a, b in gecisler:
            if a - 1e-3 < c.bas < b:
                ek = b - c.bas
                if ek <= en_cok_itme:
                    c.bas = round(b, 3)
                    itilen.append(c.id)
                else:
                    bulgu.append({"hedef": "E2", "klip": c.id, "zaman": [a, b], "sorun": "grafik kesim geçişinin üstünde"})
    # 2) Aynı anda iki hero: sonraki öncekinin bitişine itilir.
    son = None
    for c in sorted(grafik, key=lambda c: c.bas):
        if not _hero(c):
            continue
        if son and c.bas < son.bas + son.sure - 1e-3:
            ek = son.bas + son.sure - c.bas
            if ek <= en_cok_itme:
                c.bas = round(son.bas + son.sure, 3)
                itilen.append(c.id)
            else:
                bulgu.append({"hedef": "E2", "klip": c.id, "zaman": [c.bas, c.bas + c.sure], "sorun": f"{son.id} ile aynı anda iki ana grafik"})
                continue
        son = c
    # 3) SFX yoğunluğu: 0,4 sn'de birden çok rol olayı (konuşmayı örter) → E3'e bulgu.
    sfx = sorted((c for c in k.klipler if c.tur == "ses" and (c.olay or {}).get("tur") and not (c.olay or {}).get("muzik")
                  and not (c.olay or {}).get("konusma")), key=lambda c: c.bas)
    for a, b in zip(sfx, sfx[1:]):
        if b.bas - a.bas < 0.4:
            bulgu.append({"hedef": "E3", "klip": b.id, "zaman": [a.bas, b.bas], "sorun": "0,4 sn içinde iki ses olayı"})
    return itilen, bulgu


# ---------------------------------------------------------------- sözleşme, pano, bağlam paketi

def sozlesme(p, k: Kurgu, hook: dict | None, ritim: dict | None) -> dict:
    t = tema_token.oku(kurgu.etkin_tema(p, k.motion_tema)) or tema_token.oku("varsayilan")
    W, H = k.sekans.w, k.sekans.h
    yuz = yuz_bolge.hesapla(p, k) if yuz_bolge.model_var() else []
    return {
        "surum": 2, "rev": k.rev, "sekans": k.sekans.model_dump(), "hook": hook,
        "kesim": [{"id": c.id, "bas": c.bas, "sure": c.sure, "kaynak": c.kaynak, "giris": c.giris, "hiz": c.hiz,
                   **({"gecis": c.gecis_giris.tur} if c.gecis_giris else {})} for c in sorted(k.klipler, key=lambda c: c.bas) if c.iz == "V1"],
        "ayrilmis": {"altyazi_bandi_y": [round(0.66 * H), round(0.80 * H)] if H > W else [round(0.82 * H), round(0.94 * H)],
                     "platform": "9:16 üst %10, alt %20, sağ sütun %14 (y %42-80)" if H > W else "yok",
                     "yuz_araliklari": len(yuz), "not": "Native grafik yerleşimi yüz ve altyazıdan kendiliğinden kaçar; bölge yazma."},
        # WHY: dizinler pakette yoktu; E2/E3 çapa dizinini tahmin ediyor ya da hiç çapalamıyordu (instagram/1 v2 koşusu).
        "kelimeler": {kay: " ".join(f"{i}:{w.w}@{w.s:.2f}" for i, w in enumerate(k.kelimeler.get(kay) or []))
                      for kay in dict.fromkeys(c.kaynak for c in sorted(k.klipler, key=lambda c: c.bas) if c.iz == "V1" and c.kaynak)
                      if k.kelimeler.get(kay)},
        "ritim": {"bpm": (ritim or {}).get("bpm"), "vurus": [round(x, 2) for x in ((ritim or {}).get("beats") or [])[:200]]},
        "stil": {"tema": t.ad, "vurgu": t.renk.vurgu, "ikincil": t.renk.ikincil, "baslik": t.font.baslik,
                 "egri": (t.hareket.egri.model_dump() if t.hareket.egri else t.hareket.easing)},
    }


def pano_ekle(kok: Path, rol: str, mesajlar: list[Mesaj]) -> None:
    f = kok / "pano.json"
    eski = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    eski += [{**m.model_dump(), "kimden": rol} for m in mesajlar]
    f.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")


def pano_oku(kok: Path, rol: str, aralik: tuple[float, float] | None = None) -> list[dict]:
    f = kok / "pano.json"
    if not f.exists():
        return []
    m = [x for x in json.loads(f.read_text(encoding="utf-8")) if x["kimden"] != rol]
    if aralik:
        m = [x for x in m if x["aralik"][0] <= aralik[1] and aralik[0] <= x["aralik"][1]]
    return m[-40:]


def _katman_ozeti(k: Kurgu, rol: str) -> list[str]:
    """Başka editörlerin katmanından 3 satır: ne var, nerede yoğun."""
    sat = []
    for r in EDITORLER:
        if r == rol:
            continue
        ks = [c for c in k.klipler if sahip(k, c.iz) == r]
        if ks:
            sat.append(f"- {r}: {len(ks)} klip, {min(c.bas for c in ks):.1f}-{max(c.bas + c.sure for c in ks):.1f} sn; "
                       + ", ".join(sorted({c.tur for c in ks})))
    return sat


SABIT = """## Çıktı (yalnız bu JSON, başka metin yok)
```json
{"ekle": [<yeni klipler, kurgu.json klip şeması>], "guncelle": [{"id": "<klip>", <yalnız değişen alanlar>}], "sil": ["<klip id>"],
 "kaynaklar": {"<yeni kaynak id>": {"yol": "library:music/<klasör>/<dosya>.mp3", "sure": <sn>}}, "isaretler": null, "altyazi": null, "motion_tema": null, "hook": null, "hf": {},
 "pano": [{"tip": "claim|constraint|request|done", "aralik": [a, b], "metin": "<en çok 2 satır>"}],
 "rapor": "<ne yaptın, zaman damgalı, en çok 10 satır>"}
```
Kurallar:
- Yalnız kendi katmanına yaz. Başka editörün klibine dokunursan yaman birleşmez.
- Grafik ve ses olayını sekans saniyesine değil kaynak kelimesine çapala: `"capa": {"kaynak": "<id>", "kelime": <dizin>}`; dizinler sözleşmenin `kelimeler` alanında (`dizin:kelime@kaynak sn`); giriş kelimeden 2-4 kare önce (`once_kare`). Kesim değişirse vedit taşır.
- Grafik önce HyperFrames: `{"tur": "motion", "hf": {"ad": "<kompozisyon>", "param": {...}}}` (ADR 0050); webm'i vedit üretir. Katalogda uygun kompozisyon yoksa (yalnız E2) yeni kompozisyonu dosya yazmadan çıktının `"hf": {"<ad>": "<index.html içeriği>"}` alanına koy; sözleşme `library/motion/hf/SOZLESME.md`, vedit `work/edit/hf/<ad>/` altına yazar.
- Native grafik için `{"tur": "motion", "bilesen": {"ad": "<katalog adı>", "param": {...}}}`; konum yazma, yerleşim yüz ve altyazıdan kendiliğinden kaçar.
- Kaynak alanları yalnız `yol`, `sure`, `w`, `h`, `ses`; `yol` önekli yazılır (`library:`, `inputs:`, `public:`, `stil:`). Başka alan yamayı düşürür.
- Yanıtın tamamı tek JSON nesnesi olsun.
"""


def paket(p, k: Kurgu, rol: str, soz: dict, kok: Path, *, bulgular: list[dict] | None = None, kisitlar: list[str] | None = None) -> str:
    """Rol başına kompakt bağlam: sabit kısım önce (önbellek), değişken sonra. Ham medya, manifest ve tam kurgu yok."""
    from . import stil as stil_mod
    from . import stil_varlik

    try:
        stil_k = stil_mod.secili(p)
    except SystemExit:
        stil_k = None
    stil_ad = stil_k.name if stil_k else stil_mod.secili_adi(p)
    depo = stil_varlik.oku(p.studyo, stil_ad) if stil_ad else None
    ozel_varlik = stil_varlik.baglam_metni(p.studyo, stil_ad) if stil_ad else ""
    kurallar = kural.paket(kural.yukle(), rol=rol, studyo=p.studyo, stil=stil_ad, proje=f"{p.studyo}/{p.ad}")
    sabit = [f"# Ekip editörü {rol}: {ROL_TANIM[rol]}", f"Rol dosyan: `{(ROL_KLASORU / (ROL_ADI[rol] + '.md')).resolve()}` (bir kez oku).",
             SABIT, "## Etkin kurallar", kurallar or "- (yok)"]
    if ozel_varlik:
        sabit.append(ozel_varlik)
    gecis_listesi = ", ".join(kurgu.ORTA_GECIS)
    if rol == "E2":
        izinli_native = set(depo.secili_native) if (depo and depo.yalniz_bunlar) else None
        katalog_satirlari = native_motion.katalog_ozeti(izinli=izinli_native)
        sabit += [
            aiedit._hf_katalogu(p.work),  # birincil motor (ADR 0050)
            "## Native grafik kataloğu (HyperFrames karşılığı yoksa; yalnız bunlar)", *(katalog_satirlari or ["- (yalniz_bunlar aktif, seçili native bileşen yok)"]),
            "## Anlatı hiyerarşisi (rastgele ikon serpme YASAK)",
            "- Hook (0–3 sn): `tipografi/kinetik-baslik` (vurgu kelimesi patlar)\n"
            "- Bölüm / örnek ayrımları: `tipografi/bolum-baslik` (üst kapsül: `01 · KLASİK REKLAM`)\n"
            "- Değerlendirme / sonuç / metrik anları: `tipografi/durum-rozeti` veya `veri/*`\n"
            "- Zirve fikir / tezat anı: `tipografi/vurgu-soz` (~~eski~~ → **yeni**, gerekirse `odak_karart: true`) veya `veri/karsilastirma`\n"
            "- Kısa vurucu kelime: `tipografi/kayan-kelime`\n"
            "- Kapanış çağrısı: `kart/cta-karti`\n"
            "- İkonlar (`ikon/*`) yalnız 1–1.3 sn'lik seyrek destekçidir: V2 kliplerinin en çok %30'u ikon olabilir; konuşmacının yüzünü ve odak nesnesini/ürünü kapatma.",
            "## Kesim geçişleri (E1'in; yalnız bilgi)", gecis_listesi,
        ]
    if rol == "E3":
        from . import olaysesi
        sabit += [
            "## Ses rolleri (dosya seçme, rol yaz; olaysesi seçer)", ", ".join(sorted({*olaysesi.ROLLER, *olaysesi.KOMBOLAR})),
            "## Yönetmenlik kuralları (E3)",
            "- Her bölüm açılışında (`acilis`, `vurgu_guclu`), geçişte ve önemli grafik girişinde katmanlı, kulağı yormayan gerçek SFX rol olayı kullan (sentetik yok; orta noktalı V1 geçişinin ve sesli hazır efektin sesi kendiliğinden gelir, aynı yere ikinci geçiş sesi koyma).\n"
            "- Hikâye ve duygu anlarında müzikte dinamik nefes/ducking (`ses.duck: true`, gerekirse `ses.kf`) kur.",
        ]
    if rol == "E1":
        sabit += [
            "## Geçiş türleri (orta noktası kesimde, sesi kendiliğinden)", gecis_listesi,
            "## Yönetmenlik kuralları (E1)",
            "- 0.4 sn üstü ölü boşlukları, dolgu ve tekrarları kelime sınırında kırp.\n"
            "- Konuşan kafada durağanlığı kırmak için `el_kamerasi` + `hizli_zoom` / `punch` çeşitliliği kur.\n"
            "- Bölüm geçişlerinde seçili stile uygun `zoom_kirbac`, `film_yanigi`, `bolunme`, `yirtma`, `bozulma` (veya stilin `gecis` listesi) kullan.\n"
            "- Büyük tipografi zirvelerinde arka planı sakinleştirmek için `odak_karart` hazır efektini kullan.",
        ]
    kendi = [c.model_dump(exclude_defaults=True) for c in k.klipler if sahip(k, c.iz) == rol]
    degisken = ["## Sözleşme", "```json", json.dumps(soz, ensure_ascii=False)[:6000], "```",
                f"## Transkript özeti: `{(p.work / 'analysis' / 'digest.txt').resolve()}`",
                "## Senin katmanın (şu anki klipler)", "```json", json.dumps(kendi, ensure_ascii=False)[:8000], "```",
                "## Diğer katmanlar (özet)", *(_katman_ozeti(k, rol) or ["- (boş)"])]
    if pano := pano_oku(kok, rol):
        degisken += ["## Pano (diğer editörlerin notları)"] + [f"- [{m['kimden']} {m['tip']} {m['aralik'][0]:.1f}-{m['aralik'][1]:.1f}] {m['metin']}" for m in pano]
    if bulgular:
        degisken += ["## Düzelt (yalnız bunlar; başka şeye dokunma)", "```json", json.dumps(bulgular, ensure_ascii=False), "```"]
    if kisitlar:
        degisken += ["## Kısıtlar (başka editörün bulgusu senin alanına değiyor)"] + [f"- {x}" for x in kisitlar]
    return "\n\n".join(sabit) + "\n\n" + "\n\n".join(degisken) + "\n"


# ---------------------------------------------------------------- QC birleştirici

def bulgu_birlestir(k: Kurgu, listeler: dict[str, list[dict]]) -> tuple[list[dict], dict[str, list[str]]]:
    """Tekilleştir (aynı katman, kategori ve örtüşen zaman: en ağır kalır), tek sahibe yolla, öteki editöre kısıt üret."""
    hepsi = [b for kk in KONTROLLER for b in (listeler.get(kk) or [])]
    sira = {"P0": 0, "P1": 1, "P2": 2}
    kalan: list[dict] = []
    for b in sorted(hepsi, key=lambda b: sira[b["onem"]]):
        if any(x["kategori"] == b["kategori"] and x.get("katman") == b.get("katman") and x["zaman"][0] <= b["zaman"][1] + 0.3
               and b["zaman"][0] <= x["zaman"][1] + 0.3 for x in kalan):
            continue
        kalan.append(dict(b))
    kisit: dict[str, list[str]] = {e: [] for e in EDITORLER}
    for b in kalan:
        izler = {i.id for i in k.izler}
        katman_sahibi = sahip(k, b["katman"]) if b.get("katman") in izler else None
        if katman_sahibi and katman_sahibi != b["hedef"]:
            kisit[b["hedef"]].append(f"{b['zaman'][0]:.1f}-{b['zaman'][1]:.1f} sn: {b['sorun'][:160]} ({katman_sahibi} düzeltiyor; sen bu aralıkta buna uy)")
            b["hedef"] = katman_sahibi
    return kalan, kisit


# ---------------------------------------------------------------- ölçüm

def token_ozeti(meta: dict, istem_metni: str, cikti_metni: str, gorsel: int = 0) -> dict:
    """Motor token verdiyse o; vermediyse tahmin: (istem + çıktı) / 4 + görsel başına 1500 ('tahmini')."""
    t = meta.get("token") or {}
    toplam = sum(v for kk, v in t.items() if isinstance(v, (int, float)))
    if toplam:
        return {"token": int(toplam), "tahmini": False}
    return {"token": int((len(istem_metni) + len(cikti_metni)) / 4 + gorsel * 1500), "tahmini": True}


def taban_olcum(eski: Path) -> dict:
    """v1 koşusunun ajan başına token ve süresi (v2 raporundaki kıyas için). agy slotları aynı yöntemle tahmin edilir."""
    toplam_token, toplam_sn, tahmini, satir = 0, 0.0, 0, []
    baglam = (eski / "baglam.md").read_text(encoding="utf-8", errors="ignore") if (eski / "baglam.md").exists() else ""
    ek = sum((paths.ROOT / y).stat().st_size for y in aiedit.KURALLAR if (paths.ROOT / y).exists())
    for m in sorted(eski.glob("tur-*/*.meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        istem = m.with_name(m.name.replace(".meta.json", ".istem.md"))
        cik = m.with_name(m.name.replace(".meta.json", ".cikti.txt"))
        metin = (istem.read_text(encoding="utf-8", errors="ignore") if istem.exists() else "") + baglam + " " * ek
        o = token_ozeti(meta, metin, cik.read_text(encoding="utf-8", errors="ignore") if cik.exists() else "",
                        gorsel=40 if m.name.startswith("K") else 0)
        toplam_token += o["token"]
        toplam_sn += meta.get("sure") or 0
        tahmini += o["tahmini"]
        satir.append({"slot": f"{m.parent.name}/{m.name.split('.')[0]}", "sn": meta.get("sure"), **o})
    d = json.loads((eski / "durum.json").read_text(encoding="utf-8")) if (eski / "durum.json").exists() else {}
    # v1 durum.json bitiş yazmaz: son yazılan kayıt dosyasının zamanı bitiştir.
    bitis = d.get("bitis") or max((f.stat().st_mtime for f in eski.rglob("*") if f.is_file()), default=0)
    duvar = round(bitis - d["baslangic"]) if d.get("baslangic") and bitis > d["baslangic"] else None
    return {"token": toplam_token, "ajan_sn": round(toplam_sn), "tahmini_slot": tahmini, "slotlar": satir, "duvar_sn": duvar}


# ---------------------------------------------------------------- render

def parcali_render(p, araliklar: list[tuple[float, float]], *, es: int = 2) -> Path:
    """Etkilenen aralıkları paralel render eder ve mevcut taslağa ekler (taslak çözünürlüğü, veryfast)."""
    taslak = p.work / "renders" / "taslak.mp4"
    if not taslak.exists() or not araliklar:
        return hizli.taslak(p)
    props = hizli._props(p)
    hizli._public_hazirla(p)
    fps = kurgu.oku(p.work).sekans.fps
    kok = p.work / "renders" / "parca"
    kok.mkdir(parents=True, exist_ok=True)

    from . import hf_kurgu
    motor, neden = hf_kurgu.motor_sec(p, props)  # WHY: ADR 0051; motor bir kez seçilir, proje bir kez derlenir
    print(f"  Motor: {'HyperFrames' if motor == 'hf' else 'Remotion'} ({neden})", flush=True)
    def bir(i_ab):
        i, (a, b) = i_ab
        out = kok / f"p{i}.mp4"
        if motor == "hf":
            hf_kurgu.render(p, props, out, kalite="draft", aralik=(a, b), olcek=0.5)
        else:
            hizli._remotion(props, p.work / "public", out, "--image-format=jpeg", "--x264-preset=veryfast", "--crf=23", "--scale=0.5",
                            f"--frames={int(a * fps)}-{int(b * fps) - 1}")
        return out

    # HyperFrames parçaları sırayla: her parça work/public'e kendi pencereli derlemesini yazar (ADR 0051).
    with ThreadPoolExecutor(max_workers=1 if motor == "hf" else es) as h:
        parcalar = list(h.map(bir, enumerate(sorted(araliklar))))
    # Eski taslağın aralık dışı bölümleri + yeni parçalar; sınırda yeniden kodlama (taslak kalitesi yeter).
    tv = ff.probe(taslak).get("video") or {}
    tw, th = tv.get("width", 540), tv.get("height", 960)
    girdiler, filtre, n = ["-i", str(taslak)], [], 0
    sinir = [0.0] + [x for ab in sorted(araliklar) for x in ab] + [float(ff.probe(taslak)["duration"])]
    for j, (a, b) in enumerate(zip(sinir[::2], sinir[1::2])):
        if b - a > 1 / fps:
            filtre.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{n}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{n}]")
            n += 1
        if j < len(parcalar):
            girdiler += ["-i", str(parcalar[j])]
            # Parça başka motordan ya da ölçekten gelebilir: taslağın boyutuna eşitlenir (ADR 0051).
            filtre.append(f"[{len(girdiler) // 2 - 1}:v]scale={tw}:{th},setsar=1,setpts=PTS-STARTPTS[v{n}];[{len(girdiler) // 2 - 1}:a]asetpts=PTS-STARTPTS[a{n}]")
            n += 1
    zincir = ";".join(filtre) + ";" + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    yeni = p.work / "renders" / "taslak.yeni.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *girdiler, "-filter_complex", zincir, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", str(yeni)], check=True)
    os.replace(yeni, taslak)
    return taslak


# ---------------------------------------------------------------- akış

def _cagir(p, ayar: EkipAyar, rol: str, metin: str, kok: Path, mod: str, durum) -> tuple[str, dict]:
    """Tek ajan çağrısı: istem dosyası + yanıt; bir yeniden deneme, sonra yedek motor. (yanıt, ölçüm)."""
    f = kok / f"{rol}.istem.md"
    f.write_text(metin, encoding="utf-8")
    istem = (f"Read the file {f.resolve()} completely and do exactly what it says. "
             + ("Do not modify any file." if mod == "plan" else "Do not run shell commands and do not write files: return only the JSON."))
    for deneme, yedek in ((1, False), (2, True)):
        sl = ayar.slotlar[rol]
        if yedek and not sl.yedek_motor:
            break
        durum.slot(rol, durum="yedek" if yedek else "calisiyor", cikti=str(kok / f"{rol}.cikti.txt"))
        ok, yanit, meta = ekip.ajan(sl, istem, mod, kok / rol, yedek=yedek)
        gorsel = 30 if rol.startswith("K") else 0
        meta.update(deneme=deneme, **token_ozeti(meta, metin, yanit, gorsel))
        # WHY: v1 ölçümünde 5-8 sn ve 0 token biten Claude slotları başarılı sayılıyordu (sessiz başarısızlık).
        if ok and not yanit.strip():
            ok, meta["hata"] = False, "boş yanıt"
        (kok / f"{rol}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        if ok:
            durum.slot(rol, durum="bitti", sure=meta.get("sure"), token=meta["token"], tahmini=meta["tahmini"])
            return yanit, meta
    durum.slot(rol, durum="hata")
    return "", meta


def _bagla(p, k: Kurgu) -> None:
    """motion_bagla; render edilemeyen grafik (bilinmeyen hf adı, alfasız çıktı) ekip akışını düşürmez, klip çıkarılır."""
    try:
        kurgu.motion_bagla(p, k)
        return
    except (ValueError, RuntimeError) as e:
        hata = str(e)
    from . import hf_grafik
    kalan = []
    for c in k.klipler:
        if c.tur == "motion" and c.hf and not c.kaynak:
            if not hf_grafik.bul(c.hf.get("ad") or "", p.work):
                print(f"  ! {c.id}: HyperFrames kompozisyonu bulunamadı, klip çıkarıldı ({hata[:120]})")
                continue
        kalan.append(c)
    k.klipler = kalan
    try:
        kurgu.motion_bagla(p, k)
    except (ValueError, RuntimeError) as e:  # ikinci deneme de düşerse bağlanmayan hf klipleri çıkar
        print(f"  ! motion bağlanamadı: {str(e)[:200]}")
        k.klipler = [c for c in k.klipler if not (c.tur == "motion" and c.hf and not c.kaynak)]


def _yama_cikar(metin: str) -> Yama | None:
    dec = json.JSONDecoder()
    for i in [m for m in range(len(metin)) if metin[m] == "{"][:200]:
        try:
            o, _ = dec.raw_decode(metin[i:])
        except ValueError:
            continue
        if isinstance(o, dict) and any(a in o for a in ("ekle", "guncelle", "sil", "hook")):
            try:
                return Yama.model_validate(o)
            except ValidationError:
                return None
    return None


def calistir(p, ayar: EkipAyar, *, notu: str | None = None, final: bool = False, tekrar_denetle: bool = False) -> dict:
    kok = p.work / "edit" / "ekip"
    kok.mkdir(parents=True, exist_ok=True)
    (kok / "pano.json").unlink(missing_ok=True)
    durum = ekip.Durum(kok, ayar)
    t0 = time.time()
    if not aiedit._hazir_mi(p):
        hizli.hazirla(p)
    if ayar.stil:
        ekip._stil_sec(p, ayar.stil)
    k = aiedit._kurgu_hazirla(p)
    once = k
    olcum: dict[str, dict] = {}
    ritim_f = p.work / "edit" / "ritim.json"
    ritim = json.loads(ritim_f.read_text(encoding="utf-8")) if ritim_f.exists() else None
    havuz = ThreadPoolExecutor(max_workers=ayar.eszamanlilik)

    # 1) sözleşme: tek ucuz E1 çağrısı (hook ve sıra) + vedit
    durum.ayarla(asama="sozlesme")
    soz = sozlesme(p, k, None, ritim)
    sdir = kok / "sozlesme"
    sdir.mkdir(exist_ok=True)
    yanit, meta = _cagir(p, ayar, "E1", paket(p, k, "E1", soz, kok) + "\n\n## Bu çağrıda yalnız hook\n"
                         "Yalnız `hook` alanını doldur: {\"bas\", \"son\", \"neden\"} ve gerekiyorsa `guncelle` ile V1 sırası. Başka alan yazma.",
                         sdir, "duzenle", durum)
    olcum["E1-hook"] = meta
    y = _yama_cikar(yanit)
    if y and y.guncelle:
        try:
            k = yama_uygula(k, "E1", Yama(guncelle=y.guncelle))
        except SystemExit:
            pass
    soz = sozlesme(p, k, y.hook if y else None, ritim)
    (kok / "sozlesme.json").write_text(json.dumps(soz, ensure_ascii=False, indent=1), encoding="utf-8")

    # 2) paralel düzenleme
    durum.ayarla(asama="E1+E2+E3", tur=1)
    d1 = kok / "duzen"
    d1.mkdir(exist_ok=True)

    def editor(rol: str, bulgular=None, kisitlar=None, kdir=d1):
        yanit, meta = _cagir(p, ayar, rol, paket(p, k, rol, soz, kok, bulgular=bulgular, kisitlar=kisitlar), kdir, "duzenle", durum)
        olcum[f"{kdir.name}/{rol}"] = meta
        y = _yama_cikar(yanit)
        if y and y.pano:
            pano_ekle(kok, rol, y.pano)
        if y and rol == "E2" and y.hf:
            hf_yaz(p, y)  # kompozisyon klipten önce diskte olmalı: birleştirmede denetlenir (ADR 0050)
        return rol, y

    yamalar = {r: y for r, y in havuz.map(editor, EDITORLER) if y is not None}

    # 3) deterministik birleştirme + tek render
    durum.ayarla(asama="birlestir")
    taban_rev = kurgu.oku(p.work).rev
    yeni, br = birlestir(k, yamalar)
    hatalar = kurgu.denetle(p, yeni)
    if hatalar:
        br["denetle"] = hatalar[:10]
    kurgu.yaz(p.work, yeni, beklenen_rev=taban_rev)  # WHY: kullanıcı Stüdyo'da yazdıysa ezilmez (RevCakismasi)
    durum.ayarla(asama="render")
    yeni = kurgu.oku(p.work)
    _bagla(p, yeni)
    kurgu.yaz(p.work, yeni)
    video = hizli.taslak(p)

    # 4) QC bir kez, paralel, ortak paket
    durum.ayarla(asama="izle")
    qdir = kok / "qc"
    girdi = ekip.izle(p, video, qdir)

    def kontrol(kk: str):
        f = ekip.kontrol_istemi(p, kk, 1, girdi, [], ayar, None)
        yanit, meta = _cagir(p, ayar, kk, f.read_text(encoding="utf-8"), qdir, "plan", durum)
        olcum[f"qc/{kk}"] = meta
        o = ekip.json_cikar(yanit) if yanit else None
        c, _ = ekip.bulgu_dogrula(o, kk) if o is not None else (None, [])
        return kk, [b.model_dump() for b in c.bulgular] if c else []

    durum.ayarla(asama="K1+K2+K3")
    listeler = dict(havuz.map(kontrol, KONTROLLER))
    for b in br["capa_bulgu"] + br["cakisma_bulgu"]:  # vedit'in kendi bulguları da birleştiriciye girer
        listeler.setdefault("K2" if b.get("hedef", "E2") == "E2" else "K3", []).append(
            {"id": "K2-900", "hedef": b.get("hedef", "E2"), "onem": "P1", "zaman": list(b.get("zaman") or [0, 0.1]), "katman": b.get("iz", "V2"),
             "kategori": "tutarlilik", "kanit": "", "sorun": b["sorun"], "beklenen": "çakışma yok"})
    bulgular, kisit = bulgu_birlestir(yeni, listeler)
    kurallar = kural.qc_isle(bulgular, proje=f"{p.studyo}/{p.ad}")

    # 5) düzeltme bir kez, yalnız bulgu farkıyla
    gerek = sorted({b["hedef"] for b in bulgular if b["onem"] in ("P0", "P1")})
    duzeltilen, br2 = [], None
    if gerek:
        durum.ayarla(asama="duzelt:" + "+".join(gerek))
        d2 = kok / "duzelt"
        d2.mkdir(exist_ok=True)
        k = kurgu.oku(p.work)
        sonuc = dict(havuz.map(lambda r: editor(r, [b for b in bulgular if b["hedef"] == r], kisit.get(r), d2), gerek))
        sonuc = {r: y for r, y in sonuc.items() if y is not None}
        if sonuc:
            yeni2, br2 = birlestir(k, sonuc)
            _bagla(p, yeni2)  # yeni hf/şablon klibinin kaynağı diske de yazılsın; Stüdyo kaynaksız klipte düşer
            kurgu.yaz(p.work, yeni2, beklenen_rev=k.rev)
            duzeltilen = [r for r in br2["uygulanan"] if r in sonuc]
            araliklar = sorted({(max(0.0, b["zaman"][0] - 0.5), b["zaman"][1] + 0.5) for b in bulgular if b["hedef"] in sonuc})
            durum.ayarla(asama="render:parca")
            video = parcali_render(p, araliklar) if not any(r == "E1" for r in sonuc) else hizli.taslak(p)

    # 6) son: deterministik denetim; ikinci QC yalnız P0 kapısı düşerse ya da istenirse
    son = kurgu.oku(p.work)
    p0 = [h for h in kurgu.denetle(p, son)]
    uyari = kurgu_kalite.uyarilar(son, tema_token.oku(kurgu.etkin_tema(p, son.motion_tema)), p=p)
    if tekrar_denetle or p0:
        durum.ayarla(asama="tekrar-denetle")
        girdi = ekip.izle(p, video, kok / "qc2")
    havuz.shutdown()
    durum.ayarla(asama="bitti", bitti=True, bitis=time.time())
    ozet = {"sure_sn": round(time.time() - t0), "olcum": olcum, "birlestirme": br, "duzeltme_birlestirme": br2, "bulgular": bulgular, "kurallar": kurallar,
            "duzeltilen": duzeltilen, "son_denetim": {"hata": p0, "uyari": len(uyari)}}
    (kok / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rapor_yaz(p, once, son, ozet)
    return ozet


def rapor_yaz(p, once: Kurgu, son: Kurgu, o: dict) -> Path:
    toplam = sum((m or {}).get("token", 0) for m in o["olcum"].values())
    tahmini = sum(1 for m in o["olcum"].values() if (m or {}).get("tahmini"))
    stil_f = p.work / "edit" / "stil.txt"
    stil_ad = stil_f.read_text(encoding="utf-8").strip() if stil_f.exists() else ""
    # Kıyas tabanı: aynı stilin v1 koşusu, yoksa herhangi bir v1 koşusu.
    adaylar = [p.work / "edit" / f"ekip-{stil_ad}", p.work / "edit" / "ekip-v1", *sorted((p.work / "edit").glob("ekip-*"))]
    taban_kok = next((x for x in adaylar if x.is_dir() and (x / "durum.json").exists() and any(x.glob("tur-*/*.meta.json"))), None)
    taban = taban_olcum(taban_kok) if taban_kok else None
    sat = [f"# AI edit raporu (ekip v2, ADR 0048) · {p.studyo}/{p.ad}", "",
           f"- Duvar saati: {o['sure_sn']} sn · ajan çağrısı: {len(o['olcum'])} · token: {toplam:,}" + (f" ({tahmini} slot tahmini)" if tahmini else ""),
           f"- Birleştirme: uygulanan {', '.join(o['birlestirme']['uygulanan']) or '-'} · reddedilen {', '.join(o['birlestirme']['red']) or '-'} · "
           f"düşen öğe {len(o['birlestirme'].get('dusen', []))} · çekime sığdırılan {len(o['birlestirme'].get('sigdirilan', []))} · çapalanan {o['birlestirme']['capalanan']} · yeniden eşlenen {len(o['birlestirme']['tasinan'])} · itilen {len(o['birlestirme']['itilen'])}",
           f"- QC bulgusu: {len(o['bulgular'])} (P0 {sum(b['onem'] == 'P0' for b in o['bulgular'])}, P1 {sum(b['onem'] == 'P1' for b in o['bulgular'])}) · "
           f"düzeltilen: {', '.join(o['duzeltilen']) or '-'}" + (f" · düzeltmede reddedilen {', '.join((o.get('duzeltme_birlestirme') or {}).get('red', {})) or '-'}" if o.get('duzeltme_birlestirme') else ""),
           f"- Kurallar: yeni {len(o['kurallar']['yeni'])}, tekrar {len(o['kurallar']['tekrar'])}, mezar taşından düşen {len(o['kurallar']['mezar'])}, "
           f"ihlal {sum(o['kurallar']['ihlal'].values())}",
           f"- Son denetim: {len(o['son_denetim']['hata'])} hata, {o['son_denetim']['uyari']} uyarı", ""]
    if taban:
        oran = (1 - toplam / taban["token"]) * 100 if taban["token"] else 0
        sat += ["## Kıyas (v1 koşusu)", f"- v1: token {taban['token']:,} ({taban['tahmini_slot']} slot tahmini), ajan {taban['ajan_sn']} sn"
                + (f", duvar {taban['duvar_sn']} sn" if taban["duvar_sn"] else ""),
                f"- v2: token {toplam:,}, duvar {o['sure_sn']} sn · token farkı %{oran:.0f}", ""]
    sat += ["## Ajanlar", "| slot | motor | model | sn | token | tahmini |", "|---|---|---|---|---|---|"]
    sat += [f"| {s} | {m.get('motor')} | {m.get('model')} | {m.get('sure')} | {m.get('token')} | {'evet' if m.get('tahmini') else ''} |"
            for s, m in o["olcum"].items() if m]
    f = p.work / "edit" / "ai-edit.rapor.md"
    f.write_text("\n".join(sat) + "\n", encoding="utf-8")
    return f
