"""Çalıştır: .venv/Scripts/python -X utf8 tests/test_teslim.py"""
import subprocess
import tempfile
from pathlib import Path

from vedit import ff, teslim

KART = {"pix_fmt": "yuv420p", "color_range": "tv", "color_space": "bt709", "color_primaries": "bt709",
        "color_transfer": "bt709", "width": 1920, "height": 1080, "avg_frame_rate": "30/1", "bit_rate": "9000000"}


def video(**degisen):
    return {**KART, **degisen}


# Kapı: temiz kart geçer, yanlış renk hata, düşük bitrate yalnız uyarı
assert teslim.denetle(video()) == ([], [])
assert teslim.denetle(video(color_space="bt470bg"))[0]
assert teslim.denetle(video(pix_fmt="yuvj420p"))[0]
hata, uyari = teslim.denetle(video(bit_rate="4000000"))
assert not hata and uyari
assert teslim.denetle(video(bit_rate="9000000", avg_frame_rate="60/1"))[1]  # 60 fps eşiği 12 Mbps
assert teslim.denetle(video(width=1080, height=1920), "reels") == ([], [])
assert teslim.denetle(video(), "reels")[1] and teslim.denetle(video(), "youtube")[1]

# Çözünürlük kademeleri: sekans yönü korunur, boyut çift sayı; H.265 rehberi düşer
assert [teslim.hedef_boyut(1080, 1920, k) for k in teslim.COZUNURLUK] == [(720, 1280), (1080, 1920), (1440, 2560), (2160, 3840)]
assert teslim.hedef_boyut(1920, 1080, 1440) == (2560, 1440) and teslim.hedef_boyut(1920, 1080, None) == (1920, 1080)
assert teslim.CRF == 16 and teslim.KALITE["yayin"]["crf"] == {"h264": 16, "h265": 20}
assert not teslim.denetle(video(bit_rate="5000000", codec_name="hevc"))[1] and teslim.denetle(video(bit_rate="5000000"))[1]

# Filtre: girdinin aralığı ve matrisi okunur, HDR reddedilir
f = teslim.renk_filtresi(video(pix_fmt="yuvj420p", color_range="pc", color_space="bt470bg"))
assert "rin=full" in f and "min=470bg" in f
assert "rin=limited" in teslim.renk_filtresi(video()) and "min=709" in teslim.renk_filtresi(video())
assert "min=709" in teslim.renk_filtresi(video(color_space=None))
assert "min=470bg" in teslim.renk_filtresi(video(color_space=None, width=640, height=360))
# ADR 0060: zscale dither'lı, 10-bit çıkış ve Master ön ayarı
assert "d=error_diffusion" in f and "format=yuv420p10le" in teslim.renk_filtresi(video(), 10)
assert teslim.bit_derinligi("master", "h265") == 10 and teslim.bit_derinligi("master", "h264") == 8
assert teslim.bit_derinligi("yayin", "h265") == 8 and teslim.KALITE["master"]["ara"] == "kayipsiz"
assert not teslim.denetle(video(pix_fmt="yuv420p10le"), bit=10)[0] and teslim.denetle(video(pix_fmt="yuv420p10le"))[0]
try:
    teslim.renk_filtresi(video(color_transfer="smpte2084"))
    raise SystemExit("HDR reddedilmeliydi")
except ValueError:
    pass

# Ses: yeterli AAC kopyalanır, gerisi kodlanır, ses yoksa eklenmez
assert "copy" in teslim.ses_argumanlari({"codec_name": "aac", "bit_rate": "320000", "sample_rate": "48000"})
assert "aac" in teslim.ses_argumanlari({"codec_name": "aac", "bit_rate": "128000", "sample_rate": "48000"})
assert "aac" in teslim.ses_argumanlari({"codec_name": "pcm_s24le", "bit_rate": "2304000", "sample_rate": "48000"})
assert teslim.ses_argumanlari(None) == []

# Uçtan uca: tam aralık BT.601 turuncu, BT.709 sınırlı aralığa geçince aynı renk kalmalı
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    kaynak = d / "kaynak.mp4"
    ff.ffmpeg("-f", "lavfi", "-i", "color=c=0xFF7A00:s=64x64:d=0.5:r=30",
              "-vf", "scale=out_range=full:out_color_matrix=bt601,format=yuvj420p",
              "-color_range", "pc", "-colorspace", "bt470bg", "-c:v", "libx264", "-crf", "1", str(kaynak))
    r = teslim.kodla(kaynak)
    cikti = Path(r["cikti"])
    v, _ = teslim._akislar(cikti)
    assert teslim.denetle(v)[0] == [], v
    assert r["sadakat"]["ssim"] > 0.97, r["sadakat"]
    ham = subprocess.run([ff.FFMPEG, "-v", "error", "-i", str(cikti), "-frames:v", "1", "-vf", "crop=8:8:28:28",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    orta = [sum(ham[i::3]) / (len(ham) / 3) for i in range(3)]
    assert all(abs(a - b) <= 6 for a, b in zip(orta, (0xFF, 0x7A, 0x00))), orta
    # H.265: hvc1 etiketi, aynı renk kapısı; yanlış beklenen boyut teslimi durdurur
    h = teslim.kodla(kaynak, d / "hevc.mp4", kodek="h265", kalite="hafif", beklenen=(64, 64))
    hv, _ = teslim._akislar(Path(h["cikti"]))
    assert (hv["codec_name"], hv["codec_tag_string"], h["crf"]) == ("hevc", "hvc1", 24) and teslim.denetle(hv)[0] == [], hv
    m = teslim.kodla(kaynak, d / "master.mp4", kodek="h265", kalite="master", vmaf=True)
    mv, _ = teslim._akislar(Path(m["cikti"]))
    assert (mv["pix_fmt"], mv["profile"], m["bit"]) == ("yuv420p10le", "Main 10", 10) and teslim.denetle(mv, bit=10)[0] == [], mv
    assert m["sadakat"]["vmaf"] > 90 and m["sadakat"]["psnr"] > 40, m["sadakat"]
    try:
        teslim.kodla(kaynak, d / "yanlis.mp4", beklenen=(128, 128))
        raise SystemExit("boyut kapısı durdurmalıydı")
    except RuntimeError:
        assert not (d / "yanlis.mp4").exists()
    try:
        teslim.kodla(cikti, cikti)
        raise SystemExit("üzerine yazma reddedilmeliydi")
    except ValueError:
        pass

print("test_teslim: tamam")
