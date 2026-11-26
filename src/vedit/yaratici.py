"""G0.5 yaratıcı yön (ADR 0064): videoya özgü brif (`work/edit/yaratici-brif.json`) okuma, yazma ve isteme çevirme.

WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Kurgu şablon eşlemesiyle başlıyordu: her video aynı gramerle (kinetik başlık,
bölüm kapsülü, rozet, CTA) çıkıyordu. Brif tezi, enerji eğrisini, imza anlarını ve yasak klişeleri bir kez yazar; editörler ve
kalite kontrol bu brife göre karar verir. Brif yoksa ya da bozuksa edit bugünkü gibi sürer: brif hiçbir zaman edit'i durdurmaz.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError

from . import paths
from .ekip_sema import YaraticiBrif

DOSYA = "yaratici-brif.json"
SKILL = ".claude/skills/yaratici-yon/SKILL.md"
SKILL_EN_COK = 6000  # karakter; brif istemi şişmesin

# Skill dosyası yoksa (ya da okunamazsa) istemin taşıdığı en kısa sözleşme. Uzun biçim skill'dedir.
KISA_KILAVUZ = """Brif bu videonun malzemesine dayanır (söylenen söz, görünen ürün, arayüz, sayı); her videoya uyan söz brif değildir.
- `tez`: izleyicinin aklında kalacak tek cümle (özet değil, vaat).
- `metafor`: fikri gözde canlandıran tek imge ya da nesne; konuşmadan çıkar.
- `iplik`: bütün grafikleri bağlayan tek tasarım öğesi (çizgi, şekil, renk rolü ya da hareket); başta tanıtılır, sonda döner.
- `enerji`: 3-7 bölüm, her biri 1-5 enerji ve neden; düz çizgi yok, doruktan önce nefes. Sakin bölüm bilinçli seçimdir.
- `imza_anlari`: paylaşılacak ya da hatırlanacak 1-3 an; söze çapalı (`soz`, yaklaşık `t`), ekranda ve seste ne olacağı tek cümle.
  Kataloğun ilk satırı değil, bu videoya özgü birleşim (metaforun gerçekleşmesi, sessizlik + vuruş, match cut).
- `ses`: müzik karakteri, sessizliğin ve vuruşun yeri.
- `riskler`: kalıbın dışına çıkan 1-3 karar ve gerekçesi (P0 kuralları her zaman geçerli).
- `yasak`: bu videoda bilerek kullanılmayacak 3-5 klişe.
Teslimden önce sor: bu brif başka videoya da uyuyor mu? Uyuyorsa malzemeye in."""

CIKTI_ORNEGI = ('{"tez": "<tek cümle>", "metafor": "<tek imge ve neden>", "iplik": "<tek tasarım öğesi>",\n'
                ' "enerji": [{"aralik": [0, 3.5], "seviye": 5, "neden": "<neden>"}],\n'
                ' "imza_anlari": [{"t": 12.4, "soz": "<söylenen söz>", "ne": "<ekranda ve seste ne olur>"}],\n'
                ' "ses": "<müzik karakteri, sessizlik ve vuruş>", "riskler": ["<karar: gerekçe>"], "yasak": ["<klişe>"]}')


def yol(work: Path) -> Path:
    return work / "edit" / DOSYA


def _istek(istek: str | None) -> str:
    return " ".join((istek or "").split())


def oku(work: Path) -> YaraticiBrif | None:
    f = yol(work)
    if not f.is_file():
        return None
    try:
        return YaraticiBrif.model_validate_json(f.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError):
        return None


def gecerli(work: Path, istek: str | None) -> YaraticiBrif | None:
    """Yeniden kullanılabilecek brif: kilitli ya da aynı istekle yazılmış. İstek değiştiyse None (yeniden üretilir)."""
    b = oku(work)
    if b is None:
        return None
    if b.kilit or b.istek is None or _istek(b.istek) == _istek(istek):
        return b
    return None


def dogrula(veri) -> YaraticiBrif | None:
    if not isinstance(veri, dict):
        return None
    try:
        return YaraticiBrif.model_validate(veri)
    except ValidationError:
        return None


def yaz(work: Path, veri, istek: str | None) -> YaraticiBrif | None:
    """Ajanın brifini doğrular ve yazar. Kilitli brifin üzerine yazmaz; geçersiz brifte None döner, dosyaya dokunmaz."""
    eski = oku(work)
    if eski and eski.kilit:
        return eski
    b = dogrula(veri)
    if b is None:
        return None
    b = b.model_copy(update={"istek": _istek(istek), "kilit": False})
    f = yol(work)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(b.model_dump_json(indent=1), encoding="utf-8")
    return b


def damgala(work: Path, istek: str | None) -> YaraticiBrif | None:
    """Tek ajanın kendi yazdığı brif: doğrular, isteği damgalar. Geçersizse dosyayı bırakır, None döner."""
    f = yol(work)
    if not f.is_file():
        return None
    try:
        veri = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(veri, dict) and veri.get("kilit"):
        return dogrula(veri)
    return yaz(work, veri, istek)


def metin(b: YaraticiBrif) -> str:
    """İsteme giden kısa brif. Editörler kararlarını buna bağlar."""
    sat = [f"- **Tez:** {b.tez}"]
    if b.metafor:
        sat.append(f"- **Görsel metafor:** {b.metafor}")
    if b.iplik:
        sat.append(f"- **İplik öğe:** {b.iplik}")
    if b.enerji:
        sat.append("- **Enerji eğrisi:** " + " · ".join(
            f"{e.aralik[0]:g}-{e.aralik[1]:g} sn **{e.seviye}**" + (f" ({e.neden})" if e.neden else "") for e in b.enerji))
    for i, a in enumerate(b.imza_anlari, 1):
        yer = (f"~{a.t:g} sn" if a.t is not None else "") + (f" «{a.soz}»" if a.soz else "")
        sat.append(f"- **İmza anı {i}** {yer.strip()}: {a.ne}")
    if b.ses:
        sat.append(f"- **Ses fikri:** {b.ses}")
    if b.riskler:
        sat.append("- **Bilinçli riskler:** " + "; ".join(b.riskler))
    if b.yasak:
        sat.append("- **Bu videoda yasak klişeler:** " + "; ".join(b.yasak))
    return "\n".join(sat)


def ekip_bolumu(b: YaraticiBrif | None) -> list[str]:
    """Editör paketine giden bölüm (ADR 0064). Brif yoksa boş."""
    if b is None:
        return []
    return ["## Yaratıcı brif (G0.5; bütün ekip aynı fikre hizmet eder)", metin(b),
            "Kararlarını bu brife bağla: yoğunluk ve hız enerji eğrisini izler (sakin bölüm boş bırakılabilir), aralığına düşen "
            "imza anını teslim et, yasak klişeleri kullanma. Raporda hangi brif maddesini nasıl taşıdığını bir satırla yaz. "
            "P0 kuralları brifin üstündedir."]


def skill_govdesi() -> str:
    """`yaratici-yon` skill'inin frontmatter'sız metni; yoksa kısa kılavuz."""
    f = paths.ROOT / SKILL
    try:
        t = re.sub(r"\A---\n.*?\n---\n\s*", "", f.read_text(encoding="utf-8"), flags=re.S).strip()
    except OSError:
        t = ""
    if not t:
        return KISA_KILAVUZ
    return t[:SKILL_EN_COK] + ("\n… (kırpıldı)" if len(t) > SKILL_EN_COK else "")


def plan_bolumu() -> list[str]:
    """Orkestratör plan istemine eklenen G0.5 bölümü: brif plan JSON'unun `yaratici_brif` alanında gelir."""
    return ["## G0.5 Yaratıcı yön (planla aynı yanıtta `yaratici_brif`)",
            "Dağıtımdan önce videonun yaratıcı yönünü yaz. Kartların `odak` satırları bu brife hizmet eder: imza anı hangi "
            "editörün aralığına düşüyorsa odağına yaz; dilimler aynı enerji eğrisini ve iplik öğeyi izler.",
            KISA_KILAVUZ]


def paket(istek: str | None, digest: str, *, sure: float, studyo: str, stil: str) -> str:
    """Hızlı modda (orkestratör planı yok) brifin tek kısa çağrısı."""
    return "\n\n".join([
        "# Ekip orkestratörü · yaratıcı yön (G0.5)",
        "Rol tanımın sistem isteminde (ya da bu metnin sonunda). Dosya okuma, komut ve dosya yazma yok: bütün bağlam bu metinde. "
        "Yanıtın tamamı tek JSON nesnesi: yaratıcı brif.",
        "## Kullanıcı isteği", _istek(istek) or "(özel istek yok: seçili stile ve videoya göre en iyi edit)",
        "## Video", f"- Süre {sure:.2f} sn, stüdyo `{studyo}`",
        "## Stil", stil or "(stil seçilmedi)",
        "## Transkript özeti", digest,
        "## Nasıl yazılır (yaratici-yon skill'i)", skill_govdesi(),
        "## Çıktı", "```json\n" + CIKTI_ORNEGI + "\n```",
    ]) + "\n"


def tek_ajan_bolumu(work: Path, istek: str | None, *, yazabilir: bool) -> str:
    """Tek ajan (`vedit ai-edit`) istemine giden bölüm: geçerli brif varsa ona uy, yoksa önce brifi yaz."""
    b = gecerli(work, istek)
    if b is not None:
        return ("## Yaratıcı Yön (G0.5, `work/edit/yaratici-brif.json`)\n" + metin(b) + "\n"
                "Bütün kararlarını bu brife bağla: yoğunluk ve hız enerji eğrisini izler, imza anlarını teslim et, yasak "
                "klişeleri kullanma. Raporda her imza anının saniyesini ve nasıl kurulduğunu yaz. P0 kuralları brifin üstündedir.")
    if not yazabilir:
        return ""
    return ("## Yaratıcı Yön (G0.5): önce bunu yaz\n"
            f"Kurguya başlamadan önce `{yol(work).resolve()}` dosyasına bu videonun yaratıcı brifini yaz "
            f"(ayrıntı `{(paths.ROOT / SKILL).resolve()}`; dosya yoksa aşağıdaki kılavuz yeter). Sonra bütün kurgu kararlarını "
            "bu brife bağla ve raporda her imza anının saniyesini yaz.\n\n" + KISA_KILAVUZ + "\n\nBiçim:\n```json\n" + CIKTI_ORNEGI + "\n```")
