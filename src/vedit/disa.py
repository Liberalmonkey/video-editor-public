"""Kurgu.json'u NLE'ye aktarır: FCPXML 1.10 (Final Cut Pro, DaVinci Resolve) ve xmeml 5 (Premiere Pro)."""
# WHY: kurguyu başka editörde açabilmek için; bkz. wiki/decisions/0024-oneri-araclari.md
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from . import ff, kurgu
from .schemas import Klip, Kurgu


def _xml(kok: ET.Element, doctype: str) -> str:
    ET.indent(kok)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE {doctype}>\n' + ET.tostring(kok, encoding="unicode") + "\n"


def _medya(p, k: Kurgu) -> dict[str, dict]:
    """Kaynak anahtarı -> url, ad, süre, boyut, ses var mı."""
    m = {}
    for ad, kk in k.kaynaklar.items():
        f = kurgu.dosya(p, kk.yol)
        uz = f.suffix.lower()
        resim, salt_ses = uz in (".png", ".jpg", ".jpeg", ".webp"), uz in (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")
        x = {"url": f.as_uri(), "ad": f.name, "sure": 0.0 if resim else kk.sure, "w": kk.w, "h": kk.h,
             "ses": kk.ses and not resim, "goruntu": not salt_ses}
        if (not x["sure"] and not resim) or (x["goruntu"] and x["w"] is None):
            b = ff.probe(f)
            x["sure"] = x["sure"] or (0.0 if resim else b["duration"])
            x["ses"] = x["ses"] and "audio" in b
            if "video" in b:
                x["w"], x["h"] = x["w"] or b["video"]["width"], x["h"] or b["video"]["height"]
        m[ad] = x
    return m


def _yerinde(k: Kurgu, c: Klip) -> bool:
    return c.tur not in ("sahne", "metin") and bool(c.kaynak) and c.kaynak in k.kaynaklar


def yer_tutucular(k: Kurgu) -> list[str]:
    """XML'de karşılığı olmayan, ayrıca render edilmesi gereken klipler."""
    return [f"{c.iz} {c.bas:.2f}-{c.bas + c.sure:.2f} sn: {c.tur} {c.id} ({(c.sahne or {}).get('kind') or c.metin or ''}) render gerekli"
            for c in sorted(k.klipler, key=lambda c: c.bas) if not _yerinde(k, c)]


def _sure(k: Kurgu) -> float:
    return max([c.bas + c.sure for c in k.klipler] + [i.t for i in k.isaretler] + [1 / k.sekans.fps])


def fcpxml(p, k: Kurgu) -> str:
    fps = k.sekans.fps
    t = lambda s: f"{round(s * fps)}/{fps}s"  # kareye oturan rasyonel zaman
    m = _medya(p, k)
    kok = ET.Element("fcpxml", version="1.10")
    res = ET.SubElement(kok, "resources")
    ET.SubElement(res, "format", id="r0", frameDuration=f"1/{fps}s", width=str(k.sekans.w), height=str(k.sekans.h))
    for i, (ad, x) in enumerate(m.items(), 1):
        a = ET.SubElement(res, "asset", id=f"r{i}", name=x["ad"], start="0s", duration=t(x["sure"]),
                          hasVideo="1" if x["goruntu"] else "0", hasAudio="1" if x["ses"] else "0")
        if x["goruntu"]:
            a.set("format", "r0")
        ET.SubElement(a, "media-rep", kind="original-media", src=x["url"])
        x["ref"] = f"r{i}"
    proje = ET.SubElement(ET.SubElement(ET.SubElement(kok, "library"), "event", name="vedit"), "project", name=p.ad)
    seq = ET.SubElement(proje, "sequence", format="r0", duration=t(_sure(k)), tcStart="0s", tcFormat="NDF", audioLayout="stereo", audioRate="48k")
    # Boş ana hikâye hattı: tüm klipler ona bağlı, iz sırası lane ile korunur.
    ana = ET.SubElement(ET.SubElement(seq, "spine"), "gap", name="vedit", offset="0s", start="0s", duration=t(_sure(k)))
    imler = [ET.Element("marker", start=t(i.t), duration=f"1/{fps}s", value=i.ad or "isaret") for i in k.isaretler]
    vid = [i for i in k.izler if i.tur == "video"]
    ses = [i for i in k.izler if i.tur == "ses"]
    lane = {i.id: len(vid) - n for n, i in enumerate(vid)}  # listede üstteki iz üst lane
    lane |= {i.id: -(n + 1) for n, i in enumerate(ses)}
    izler = {i.id: i for i in k.izler}
    for c in sorted(k.klipler, key=lambda c: (c.bas, c.iz)):
        iz = izler[c.iz]
        if not _yerinde(k, c):
            imler.append(ET.Element("marker", start=t(c.bas), duration=t(c.sure), value=f"{c.tur}: {c.id} (render gerekli)",
                                    note=str((c.sahne or {}).get("kind") or c.metin or "")))
            continue
        x = m[c.kaynak]
        e = ET.SubElement(ana, "asset-clip", ref=x["ref"], lane=str(lane[c.iz]), offset=t(c.bas), name=c.id,
                          start=t(c.giris), duration=t(c.sure))
        if iz.gizli or (iz.tur == "ses" and iz.sessiz):
            e.set("enabled", "0")
        if iz.tur == "video" and (c.ses_kapali or iz.sessiz):
            e.set("srcEnable", "video")
        if c.hiz != 1:
            # shortcut: sabit hız iki noktalı doğrusal timeMap; rampa yok, Resolve bazen hızı yok sayar, o zaman elle ayarla.
            tm = ET.SubElement(e, "timeMap")
            ET.SubElement(tm, "timept", time=t(c.giris), value=t(c.giris), interp="linear")
            ET.SubElement(tm, "timept", time=t(c.giris + c.sure), value=t(c.giris + c.sure * c.hiz), interp="linear")
        db = c.ses.gain_db + iz.gain_db
        if x["ses"] and db:
            ET.SubElement(e, "adjust-volume", amount=f"{db:g}dB")
    ana.extend(imler)  # DTD: işaretler kliplerden sonra gelir
    return _xml(kok, "fcpxml")


def xmeml(p, k: Kurgu) -> str:
    fps = k.sekans.fps
    n = lambda s: str(round(s * fps))
    m = _medya(p, k)
    yazildi: set[str] = set()

    def rate(e):
        r = ET.SubElement(e, "rate")
        ET.SubElement(r, "timebase").text = str(fps)
        ET.SubElement(r, "ntsc").text = "FALSE"

    def alt(e, **kv):
        for a, v in kv.items():
            ET.SubElement(e, a).text = str(v)

    def file(e, ad):
        x = m[ad]
        f = ET.SubElement(e, "file", id=f"f-{ad}")
        if ad in yazildi:  # aynı dosya ikinci kez yalnız id ile anılır
            return
        yazildi.add(ad)
        alt(f, name=x["ad"], pathurl=x["url"])
        rate(f)
        alt(f, duration=n(x["sure"]))
        md = ET.SubElement(f, "media")
        if x["goruntu"]:
            sc = ET.SubElement(ET.SubElement(md, "video"), "samplecharacteristics")
            alt(sc, width=x["w"] or k.sekans.w, height=x["h"] or k.sekans.h)
        if x["ses"]:
            ET.SubElement(ET.SubElement(md, "audio"), "channelcount").text = "2"

    def efekt(e, ad, eid, kat, tip, parametreler):
        ef = ET.SubElement(ET.SubElement(e, "filter"), "effect")
        alt(ef, name=ad, effectid=eid, effectcategory=kat, effecttype=tip, mediatype="audio" if tip == "audiolevels" else "video")
        for pid, v in parametreler.items():
            alt(ET.SubElement(ef, "parameter"), parameterid=pid, name=pid, value=v)

    def klip(iz_e, c, iz, ses_mi):
        x = m[c.kaynak]
        ci = ET.SubElement(iz_e, "clipitem", id=f"{c.id}-{'a' if ses_mi else 'v'}")
        alt(ci, name=c.id, duration=n(x["sure"]))
        rate(ci)
        alt(ci, start=n(c.bas), end=n(c.bas + c.sure), **{"in": n(c.giris), "out": n(c.giris + c.sure * c.hiz)})
        file(ci, c.kaynak)
        if c.hiz != 1:
            # shortcut: sabit hız Time Remap parametresiyle; değişken hız yok, Premiere okumazsa hızı elle ver.
            efekt(ci, "Time Remap", "timeremap", "motion", "motion", {"variablespeed": 0, "speed": f"{c.hiz * 100:g}", "reverse": "FALSE"})
        db = c.ses.gain_db + iz.gain_db
        if ses_mi and db:
            efekt(ci, "Audio Levels", "audiolevels", "Audio Levels", "audiolevels", {"level": f"{10 ** (db / 20):.5f}"})

    kok = ET.Element("xmeml", version="5")
    seq = ET.SubElement(kok, "sequence", id="sequence-1")
    alt(seq, name=p.ad, duration=n(_sure(k)))
    rate(seq)
    media = ET.SubElement(seq, "media")
    video, audio = ET.SubElement(media, "video"), ET.SubElement(media, "audio")
    sc = ET.SubElement(ET.SubElement(video, "format"), "samplecharacteristics")
    rate(sc)
    alt(sc, width=k.sekans.w, height=k.sekans.h)
    # xmeml'de V1 en alttadır; kurgu listesinde üstteki iz önce gelir.
    for iz in reversed([i for i in k.izler if i.tur == "video"]):
        cs = sorted((c for c in k.klipler if c.iz == iz.id and _yerinde(k, c)), key=lambda c: c.bas)
        tr = ET.SubElement(video, "track")
        alt(tr, enabled="FALSE" if iz.gizli else "TRUE")
        for c in cs:
            klip(tr, c, iz, False)
        bagli = [c for c in cs if c.tur == "video" and not c.ses_kapali and m[c.kaynak]["ses"]]
        if bagli:
            atr = ET.SubElement(audio, "track")
            alt(atr, enabled="FALSE" if iz.sessiz else "TRUE")
            for c in bagli:
                klip(atr, c, iz, True)
    for iz in (i for i in k.izler if i.tur == "ses"):
        tr = ET.SubElement(audio, "track")
        alt(tr, enabled="FALSE" if iz.sessiz else "TRUE")
        for c in sorted((c for c in k.klipler if c.iz == iz.id and _yerinde(k, c)), key=lambda c: c.bas):
            klip(tr, c, iz, True)
    for i in k.isaretler:
        alt(ET.SubElement(seq, "marker"), name=i.ad or "isaret", comment="", **{"in": n(i.t), "out": -1})
    for c in k.klipler:
        if not _yerinde(k, c):
            alt(ET.SubElement(seq, "marker"), name=f"{c.tur}: {c.id} (render gerekli)",
                comment=str((c.sahne or {}).get("kind") or c.metin or ""), **{"in": n(c.bas), "out": n(c.bas + c.sure)})
    return _xml(kok, "xmeml")


def yaz(p, k: Kurgu, cikti_klasoru: Path) -> list[Path]:
    cikti_klasoru.mkdir(parents=True, exist_ok=True)
    yollar = [cikti_klasoru / f"{p.ad}.fcpxml", cikti_klasoru / f"{p.ad}.xml"]
    yollar[0].write_text(fcpxml(p, k), encoding="utf-8")
    yollar[1].write_text(xmeml(p, k), encoding="utf-8")
    return yollar
