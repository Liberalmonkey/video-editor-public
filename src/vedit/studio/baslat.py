"""Video Stüdyo hızlı başlatıcı: pencere önce açılır, ağır sunucu modülleri o sırada yüklenir.

WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md (Stüdyo açılışı). Eskiden studio.bat iki Python süreci
açıyordu (hazırlık denetimi + vedit.exe) ve Edge penceresi FastAPI, uvicorn ve tüm vedit modülleri yüklendikten
sonra başlıyordu. Şimdi tek süreç: hazırlık denetimi, port ve token seçimi, pencere iş parçacığı, sonra import.
Pencere sunucu dinlemeye başlayana kadar portu yoklar; tarayıcının kendi açılışı import ile paralel geçer.

Çıkış kodu: `--denetle` ile 0 hazır, 1 Python bağımlılığı eksik, 2 arayüz yeniden derlenmeli. Normal çağrıda hazır
değilse 11 (kurulum) ya da 12 (derleme) döner; studio.bat bu kodlarla kurulum ya da derleme yoluna gider.
"""

from __future__ import annotations

import importlib.util
import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
DIST = KOK / "studio" / "web" / "dist" / "index.html"
# Arayüzü etkileyen her şey; SplitReel openmontage altından içe aktarılır.
KAYNAK = [KOK / "studio" / p for p in ("web/src", "web/public", "web/index.html", "web/vite.config.ts", "remotion",
                                       "package.json", "package-lock.json", "tsconfig.json")]
KAYNAK.append(KOK / "openmontage" / "remotion-composer" / "src")
_T0 = time.perf_counter()


def zaman(asama: str) -> None:
    """VEDIT_ZAMAN=1 iken aşama süresini log'a yazar (studio.vbs çıktısı %TEMP%\\vedit-studio-log.txt)."""
    if os.environ.get("VEDIT_ZAMAN"):
        print(f"[zaman] {asama}: {time.perf_counter() - _T0:.2f} sn", flush=True)


def _en_yeni(p: Path) -> float:
    if p.is_file():
        return p.stat().st_mtime
    return max((f.stat().st_mtime for f in p.rglob("*") if f.is_file()), default=0.0)


def hazirlik() -> int:
    """0 hazır, 1 Python bağımlılığı eksik, 2 arayüz yeniden derlenmeli. Ağır modül yüklemez."""
    if any(importlib.util.find_spec(m) is None for m in ("fastapi", "send2trash", "uvicorn")):
        return 1
    if not DIST.exists() or max(_en_yeni(p) for p in KAYNAK if p.exists()) > DIST.stat().st_mtime:
        return 2
    return 0


def pencere(url: str) -> None:
    """Edge ya da Chrome --app penceresi; pencere kapanınca sunucu da kapanır.

    Soket zaten dinlediği için beklemeden açılır: istek, uvicorn kabul edene kadar backlog'da bekler.
    """
    port = int(url.split(":")[2].split("/")[0])
    adaylar = [shutil.which("msedge"), shutil.which("chrome"),
               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    exe = next((a for a in adaylar if a and Path(a).exists()), None)
    zaman("pencere açılıyor")
    if not exe:
        # shortcut: varsayılan tarayıcı sekmesi izlenemez, sunucu açık kalır; gerekirse kapatma düğmesi ekle.
        webbrowser.open(url)
        return
    # Ayrı profil: açık Edge oturumuna devredilmez, süreç pencereyle birlikte biter.
    # Porta özel: ikinci pencere ilk sunucunun profiline devredilip hemen kapanmaz.
    profil = Path(os.environ.get("LOCALAPPDATA", Path.home())) / f"vedit-studio-profil-{port}"
    bas = time.monotonic()
    subprocess.Popen([exe, f"--app={url}", "--window-size=1600,950", f"--user-data-dir={profil}", "--no-first-run",
                      "--no-default-browser-check", "--disable-extensions", "--disable-component-update",
                      "--disable-background-networking", "--disable-features=msEdgeStartupBoost"]).wait()
    if time.monotonic() - bas < 5:
        # WHY: tarayıcı pencereyi zaten açık bir sürece devredip hemen çıktıysa pencere hâlâ açıktır; sunucu kapanmasın.
        print("Pencere başka tarayıcı sürecine devredildi; sunucu açık kalır (kapatmak için bu süreci sonlandır).", flush=True)
        return
    os._exit(0)


def soket_ac(bas: int) -> socket.socket:
    """İlk boş portu bağlar ve dinlemeye başlar; ikinci pencere ilk sunucuyu bozmaz.

    WHY: Windows'ta kapalı porta connect_ex yaklaşık 2 sn sürer (SYN yeniden denenir). Eski port yoklaması ve
    pencere bekleme döngüsü açılışa bu yüzden saniyeler ekliyordu. bind anında sonuç verir.
    """
    for port in range(bas, bas + 20):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows: başka süreç aynı portu paylaşamasın
            sk.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sk.bind(("127.0.0.1", port))
        except OSError:
            sk.close()
            continue
        sk.listen(128)
        return sk
    raise SystemExit(f"Boş port yok: {bas}-{bas + 19}")


def _motorlari_isit() -> None:
    """AI panelinin motor taraması (claude, agy, codex, opencode sürüm ve model listesi) arka planda önceden yapılır.

    WHY: tarama birkaç alt süreç başlatır; ilk sayfa yüklenirken CPU yarışmasın diye kısa bekler (ADR 0050).
    """
    time.sleep(3)
    try:
        from .. import motorlar
        motorlar.durum()
    except Exception:  # WHY: ısıtma başarısızsa panel ilk istekte yeniden dener
        pass
    try:  # Uygulama güncellemesi: 30 dakikada bir origin kontrolü (ADR 0065); hf döngüsü bloklamasın diye ayrı thread
        from .. import guncelle
        threading.Thread(target=guncelle.arka_plan, daemon=True).start()
    except Exception as e:
        print(f"Uygulama güncelleme zamanlayıcısı durdu: {e}", flush=True)
    try:  # HyperFrames güncellemesi: haftada bir (Cuma 13:00), iş varken ertelenir; sonsuz döngü (ADR 0051)
        from .. import hf_guncel
        hf_guncel.arka_plan()
    except Exception as e:
        print(f"HyperFrames güncelleme zamanlayıcısı durdu: {e}", flush=True)


def calistir(*, port: int = 8765, ac: bool = True) -> None:
    sk = soket_ac(port)
    port = sk.getsockname()[1]
    token = secrets.token_urlsafe(24)
    url = f"http://127.0.0.1:{port}/?token={token}"
    print(f"Video Stüdyo: {url}", flush=True)
    if ac:
        threading.Thread(target=pencere, args=(url,), daemon=True).start()
    try:
        import uvicorn

        from .app import create_app
        zaman("modüller yüklendi")
        app = create_app(token, izinli_hostlar={f"127.0.0.1:{port}", f"localhost:{port}"})
    except BaseException:
        sk.close()  # bekleyen pencere isteği bağlantı hatası alır, port serbest kalır
        raise
    threading.Thread(target=_motorlari_isit, daemon=True).start()
    sunucu = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
    sunucu.run(sockets=[sk])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    zaman("python açıldı")
    if "--denetle" in argv:
        return hazirlik()
    if (kod := hazirlik()) != 0:
        return 10 + kod  # 11 kurulum, 12 derleme: studio.bat bunu yapıp yeniden çağırır; sunucu hatası 1 kalır
    port = 8765
    if "--port" in argv:
        try:
            port = int(argv[argv.index("--port") + 1])
        except (IndexError, ValueError):
            print("--port bir sayı ister", file=sys.stderr)
            return 2
    calistir(port=port, ac="--acma" not in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
