"""Teslim kodlaması: her motorun son adımı, doğru renk ve yüksek kalite, sonra ölçümle kapı.

# WHY: bkz. wiki/decisions/0016-earshot-render-standardi-ajan-duzeni.md — Remotion çıktısı tam aralık
# BT.601 etiketliydi (yuvj420p, bt470bg); platformlar sınırlı aralık BT.709 bekler, renk kayabilir.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import ff

PRESET = "slow"
SES_KBPS = 320
# YouTube'un SDR yükleme önerisi (30 fps, Mbps); kısa kenara göre. Sade grafik altında kalabilir: yalnız uyarı.
REHBER_MBPS = {720: 5, 1080: 8, 1440: 16, 2160: 35}
# WHY: bkz. wiki/decisions/0035-teslim-ayarlari.md. CLI, sunucu ve arayüz seçenekleri yalnız bu tablolardan okur.
COZUNURLUK = {720: "HD 720p", 1080: "FHD 1080p", 1440: "QHD 1440p (2K)", 2160: "UHD 2160p (4K)"}
KALITE = {  # CRF: H.265 aynı görsel kaliteyi yaklaşık 4 kademe yukarıda verir
    "arsiv": {"ad": "Arşiv", "crf": {"h264": 14, "h265": 18}},
    "yayin": {"ad": "Yayın", "crf": {"h264": 16, "h265": 20}},
    "hafif": {"ad": "Hafif", "crf": {"h264": 20, "h265": 24}},
}
KODEK = {
    "h264": {"ad": "H.264 / AVC, High", "ffmpeg": ["-c:v", "libx264", "-profile:v", "high"], "rehber": 1.0},
    # hvc1 etiketi olmadan Apple oynatıcıları HEVC MP4'ü açmaz
    "h265": {"ad": "H.265 / HEVC, Main", "ffmpeg": ["-c:v", "libx265", "-tag:v", "hvc1", "-x265-params", "log-level=error"], "rehber": 0.6},
}
FPS = (30, 60)
CRF = KALITE["yayin"]["crf"]["h264"]


def eval_kesir(k: str | None) -> float:
    pay, _, payda = str(k or "0/1").partition("/")
    return float(pay) / float(payda or 1) if float(payda or 1) else 0.0


def _cift(x: float) -> int:
    return int(round(x / 2)) * 2


def hedef_boyut(w: int, h: int, kisa: int | None) -> tuple[int, int]:
    """Sekans yönünü koruyarak kısa kenarı `kisa` yapan boyut; kodek çift sayı ister."""
    if not kisa:
        return w, h
    k = kisa / min(w, h)
    return _cift(w * k), _cift(h * k)


def secenekler() -> dict:
    return {"cozunurluk": [{"deger": k, "ad": ad, "rehber_mbps": REHBER_MBPS[k]} for k, ad in COZUNURLUK.items()],
            "kalite": [{"deger": k, "ad": v["ad"], "crf": v["crf"]} for k, v in KALITE.items()],
            "kodek": [{"deger": k, "ad": v["ad"], "rehber": v["rehber"]} for k, v in KODEK.items()],
            "fps": list(FPS), "preset": PRESET, "ses_kbps": SES_KBPS}
HDR_TRC = {"smpte2084", "arib-std-b67"}


def _akislar(yol: Path) -> tuple[dict, dict | None]:
    cikti = ff.run([ff.FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(yol)]).stdout
    veri = json.loads(cikti)
    akislar = veri.get("streams", [])
    video = next((s for s in akislar if s.get("codec_type") == "video"), None)
    if not video:
        raise ValueError(f"Video akışı yok: {yol}")
    video["_toplam_bit"] = int(veri.get("format", {}).get("bit_rate") or 0)
    return video, next((s for s in akislar if s.get("codec_type") == "audio"), None)


def renk_filtresi(video: dict) -> str:
    """Girdinin gerçek aralık ve matrisinden sınırlı aralık BT.709'a dönüşüm."""
    if video.get("color_transfer") in HDR_TRC:
        raise ValueError("HDR girdi: renk haritalama gerekir, teslim bunu sessizce yapmaz.")
    tam = video.get("color_range") == "pc" or str(video.get("pix_fmt", "")).startswith("yuvj")
    matris = video.get("color_space")
    if matris == "bt709":
        girdi = "bt709"
    elif matris in ("bt470bg", "smpte170m"):
        girdi = "bt601"
    else:  # etiketsiz: HD ve üstü BT.709, altı BT.601 kabul edilir (oynatıcıların yaptığı gibi)
        girdi = "bt709" if min(int(video["width"]), int(video["height"])) >= 720 else "bt601"
    aralik = "full" if tam else "limited"
    # setparams: filtre sonrası kare etiketi boş kalırsa -color_* bayrakları dosyaya yazılmıyor (kapı yakaladı)
    return (f"scale=in_range={aralik}:out_range=limited:in_color_matrix={girdi}:out_color_matrix=bt709,format=yuv420p,"
            "setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709")


def ses_argumanlari(ses: dict | None) -> list[str]:
    if ses is None:
        return []
    temiz = ses.get("codec_name") == "aac" and int(ses.get("bit_rate") or 0) >= 256_000 and ses.get("sample_rate") == "48000"
    # Yeniden AAC nesil kaybı getirir; zaten yeterliyse kopyalanır. Loudness'a dokunulmaz.
    return ["-map", "0:a:0", "-c:a", "copy"] if temiz else ["-map", "0:a:0", "-c:a", "aac", "-b:a", f"{SES_KBPS}k", "-ar", "48000"]


def denetle(video: dict, platform: str | None = None) -> tuple[list[str], list[str]]:
    """(hatalar, uyarılar). Renk ya da piksel biçimi yanlışsa hata, bitrate düşükse yalnız uyarı."""
    hatalar = [f"{ad}={video.get(ad)} (beklenen {bek})" for ad, bek in
               (("pix_fmt", "yuv420p"), ("color_range", "tv"), ("color_space", "bt709"),
                ("color_primaries", "bt709"), ("color_transfer", "bt709")) if video.get(ad) != bek]
    g, y = int(video["width"]), int(video["height"])
    kisa = min(g, y)
    uyarilar = []
    pay, _, payda = str(video.get("avg_frame_rate") or "30/1").partition("/")
    fps = float(pay) / float(payda or 1) if float(payda or 1) else 30.0
    esik = next((m for k, m in sorted(REHBER_MBPS.items(), reverse=True) if kisa >= k), None)
    if esik:
        esik = esik * (1.5 if fps > 40 else 1) * (KODEK["h265"]["rehber"] if video.get("codec_name") == "hevc" else 1)
        mbps = int(video.get("bit_rate") or video.get("_toplam_bit") or 0) / 1e6
        if mbps < esik:
            uyarilar.append(f"bitrate {mbps:.1f} Mbps, rehber {esik:g} Mbps (sade grafikte normal olabilir; karede bak)")
    if platform == "youtube" and kisa < 1440:
        uyarilar.append(f"{g}x{y}: YouTube 1440p ve üstüne daha iyi kodek ayırır; kod sahnesini gerçek 1440p render et")
    if platform == "reels" and (g, y) != (1080, 1920):
        uyarilar.append(f"{g}x{y}: Reels için 1080x1920 beklenir; Instagram yüklemeyi 1080p'ye indirir")
    return hatalar, uyarilar


def kodla(girdi: Path, cikti: Path | None = None, platform: str | None = None, *, kodek: str = "h264",
          kalite: str = "yayin", beklenen: tuple[int, int] | None = None, kapak: Path | None = None) -> dict:
    crf = KALITE[kalite]["crf"][kodek]
    girdi = Path(girdi)
    cikti = Path(cikti) if cikti else girdi.with_name(f"{girdi.stem}.teslim.mp4")
    if cikti.resolve() == girdi.resolve():
        raise ValueError("Çıktı girdinin üzerine yazamaz.")
    video, ses = _akislar(girdi)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    gecici = cikti.with_name(f".{cikti.stem}.tmp.mp4")
    try:
        if kapak:
            # WHY: bkz. wiki/decisions/0040-ikinci-repo-dalgasi.md (brag, MIT). X, Discord, Slack önizlemede ilk kareyi
            # gösterir; kapak yalnız 0. kareye gömülür, süre ve ses senkronu değişmez. Oynatmada bir kare görünür.
            w, h = int(video["width"]), int(video["height"])
            goruntu = ["-i", str(kapak), "-filter_complex",
                       f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[k];"
                       f"[0:v][k]overlay=0:0:enable='eq(n,0)',{renk_filtresi(video)}[v]", "-map", "[v]"]
        else:
            goruntu = ["-map", "0:v:0", "-vf", renk_filtresi(video)]
        ff.ffmpeg("-i", str(girdi), *goruntu,
                  *KODEK[kodek]["ffmpeg"], "-preset", PRESET, "-crf", str(crf),
                  "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                  *ses_argumanlari(ses), "-movflags", "+faststart", str(gecici))
        sonuc, _ = _akislar(gecici)
        hatalar, uyarilar = denetle(sonuc, platform)
        if beklenen and (int(sonuc["width"]), int(sonuc["height"])) != tuple(beklenen):
            hatalar.append(f"boyut {sonuc['width']}x{sonuc['height']} (beklenen {beklenen[0]}x{beklenen[1]})")
        if hatalar:
            raise RuntimeError("Teslim kapısı: " + "; ".join(hatalar))
        gecici.replace(cikti)
    finally:
        gecici.unlink(missing_ok=True)
    return {"cikti": str(cikti), "boyut": f"{sonuc['width']}x{sonuc['height']}",
            "mbps": round(int(sonuc.get("bit_rate") or 0) / 1e6, 1), "uyarilar": uyarilar,
            "kodek": KODEK[kodek]["ad"], "crf": crf, "fps": round(eval_kesir(sonuc.get("avg_frame_rate")), 2),
            "once": f"{video.get('pix_fmt')}/{video.get('color_range')}/{video.get('color_space')}"}
