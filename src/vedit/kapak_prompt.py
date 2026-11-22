"""Kapak prompt'ları: agy zemini için kısa prompt ve dış platformlar için master prompt. WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md

Saf fonksiyonlar; agy çağırmaz, dosya yazmaz. Brief yapılı alanlar taşır (sahne, ifade, kompozisyon, isik, palet, yazi_alani);
eski brief yalnız `prompt` taşır ve aynen okunur. Kurallar Google'ın Nano Banana rehberinden: etiket yığını değil cümle,
oran başta, kimlik kilidi, yazı tırnak içinde tam metin, yazı için boş alan açıkça tarif edilir.
"""

from __future__ import annotations

import re

BRIEF_ALANLARI = ("sahne", "ifade", "kompozisyon", "isik", "palet", "yazi_alani")
ORAN = {"youtube": "16:9", "instagram": "9:16"}
BOYUT = {"youtube": (1280, 720), "instagram": (1080, 1920)}
PLATFORM_TARIFI = {
    "youtube": "YouTube thumbnail, 16:9 (1280x720). It must read instantly at 168x94 px in the feed",
    "instagram": "Instagram Reels cover, 9:16 (1080x1920). Keep the subject and any text inside the central 3:4 area: "
                 "the profile grid crops the top and bottom 12.5%",
}
YOUTUBE_ROZET = "Keep the bottom-right corner calm: YouTube puts the video length badge there."
# Kalıbın zeminden istediği kompozisyon; görsel prompt'una eklenir. Kaynak: wiki/sources/2026-11-15-kapak-kalip-analizi.md
KALIP_PROMPT = {
    "dev-yazi": " Subject centered, chest-up, clear silhouette, large empty space above and beside the head, plain uncluttered backdrop.",
    "alt-bant": " Subject in the upper two thirds; keep the bottom third dark and empty.",
    "not": " Keep the bottom third dark and empty and leave empty space in the top left.",
    "bolunmus": " Split-screen composition: the left half and the right half show two contrasting versions of the same subject, "
                "with a clean vertical division exactly in the middle.",
    "rozet": " The scene tells the story without words: one dramatic action, subject large, top right corner calm.",
    "yazisiz": " The scene tells the story without words: one dramatic action, subject fills most of the frame.",
    "seri": " Subject centered, head and shoulders, looking at the camera, dark simple background, empty space on both sides of the head.",
}
REF_KURALI = (" Use the reference frame: keep the same person or subject (face, hair, clothing) recognizable; "
              "rebuild the background, lighting and composition as described.")
STIL_KURALI = (" Use the style reference only for layout, colour palette and lighting; "
               "do not copy its people, objects, text or logos.")
# Yerleşime göre yazı alanı (brief yazi_alani vermezse). İlk anahtar platform varsayılanıdır (kapak.YERLESIM ile aynı sıra).
YAZI_ALANI = {
    "youtube": {"sol": "the left third", "sag": "the right third", "ust": "the top quarter", "alt": "the bottom quarter"},
    "instagram": {"ust": "the upper part of the central area", "alt": "the lower part of the central area"},
}
REF_TARIF = {
    "kare": "a frame from the video: keep this person's face, hair and clothing exactly; rebuild background, light and framing",
    "yuz": "a photo of the same person: use it only to keep the face accurate",
    "stil": "a style reference: take only its layout, colour palette and lighting, never its people, objects, text or logos",
}
# Dış hedefler. yazi: o modelde yazı çiziminin güvenilirliği (master'ın uyarısı buna göre).
HEDEFLER = {
    "nano-banana-pro": {"ad": "Nano Banana Pro", "nerede": "Gemini uygulaması (Pro / Thinking), Google AI Studio, Flow",
                        "yazi": "iyi", "ref_sinir": 8},
    "nano-banana-21": {"ad": "Nano Banana 2.1", "nerede": "Gemini uygulaması (Fast), Google AI Studio, Flow",
                       "yazi": "iyi", "ref_sinir": 6},
    "chatgpt": {"ad": "ChatGPT (GPT Image)", "nerede": "ChatGPT: görselleri ekle, prompt'u yapıştır",
                "yazi": "iyi", "ref_sinir": 4},
    "midjourney": {"ad": "Midjourney", "nerede": "midjourney.com Create; referansı Image Prompt / Omni / Style alanına sürükle",
                   "yazi": "zayıf", "ref_sinir": 3},
    "ideogram": {"ad": "Ideogram", "nerede": "ideogram.ai; Magic Prompt kapalı, referansları Character / Style alanına",
                 "yazi": "çok iyi", "ref_sinir": 3},
    "leonardo": {"ad": "Leonardo", "nerede": "Leonardo Image; Prompt Enhance kapalı, referanslar Image Guidance'a",
                 "yazi": "iyi", "ref_sinir": 4},
}
TURKCE = re.compile(r"[çğıİöşüÇĞÖŞÜ]")


def hedef_listesi() -> list[dict]:
    return [{"id": k, "ad": v["ad"], "nerede": v["nerede"], "yazi": v["yazi"]} for k, v in HEDEFLER.items()]


def _cumle(s: object) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if not s or s[-1] in ".!?" else s + "."


def yapili(b: dict) -> bool:
    return any(str(b.get(a) or "").strip() for a in BRIEF_ALANLARI if a != "yazi_alani")


def yazi_alani(b: dict, platform: str) -> str:
    alan = str(b.get("yazi_alani") or "").strip().rstrip(".")
    if alan:
        # cümle içine girer ("Place it in the left third"): baştaki büyük harfli belirteç küçülür
        return alan[0].lower() + alan[1:] if re.match(r"(The|An|A) ", alan) else alan
    secenek = YAZI_ALANI[platform]
    return secenek.get(str(b.get("yerlesim") or ""), next(iter(secenek.values())))


def govde(b: dict, platform: str) -> str:
    """Brief'in sahne tarifi (İngilizce, yazısız). Yapılı alan yoksa eski `prompt` aynen döner."""
    if not yapili(b):
        return str(b.get("prompt") or "").strip()
    parcalar = [_cumle(b.get("sahne"))]
    for ad, on in (("ifade", "Expression: "), ("kompozisyon", "Composition: "), ("isik", "Lighting: "), ("palet", "Colour palette: ")):
        if str(b.get(ad) or "").strip():
            parcalar.append(on + _cumle(b[ad]))
    if (b.get("kalip") or "") != "yazisiz":
        parcalar.append(f"Keep {yazi_alani(b, platform)} clean and empty for a headline added later.")
    return " ".join(p for p in parcalar if p)


def agy_prompt(b: dict, platform: str, kalip: str | None = None, refler: list[tuple[str, str]] = ()) -> str:
    """agy zemini (Nano Banana): brief prompt'u + kalıp eki + referans kuralları. Yazı yok; yazı kodla eklenir.

    refler: [(rol, dosya)] rol kare | yuz | stil; sıra görsel numarasıdır (bkz. ref_metni)."""
    p = str(b.get("prompt") or "").strip() or govde(b, platform)
    p += KALIP_PROMPT.get(kalip or b.get("kalip") or "", "")
    roller = {r for r, _ in refler}
    if roller & {"kare", "yuz"}:
        p += REF_KURALI
    if "stil" in roller:
        p += STIL_KURALI
    if platform == "youtube":
        p += " " + YOUTUBE_ROZET
    return p


def ref_metni(refler: list[tuple[str, str]]) -> str:
    """gorsel.uret'e giden numaralı referans tarifi: genel "referansı koru" cümlesi stil referansıyla çelişir."""
    return " ".join(f"Image {i} ({yol}) is {REF_TARIF[rol]}." for i, (rol, yol) in enumerate(refler, 1)) + " "


# ---------------------------------------------------------------- yazı tarifi

def _renk(css: dict, ad: str, varsayilan: str) -> str:
    v = str(css.get(ad) or varsayilan)
    return varsayilan if v == "transparent" else v


def yazi_tarifi(b: dict, css: dict | None = None, kutu: bool | None = None) -> dict:
    """Kapak yazısının dış modele anlatılacak hali: satırlar, vurgu, renkler, yazı tipi.

    css: şablon varsayılanı + stil paketi (kapak.yazi_css); yoksa renkler adla anlatılır."""
    css = css or {}
    kalip = b.get("kalip") or "klasik"
    s1, s2 = str(b.get("satir1") or "").strip(), str(b.get("satir2") or "").strip()
    vurgu = str(b.get("vurgu") or "").strip() or s2
    kontursuz = css.get("--kontur-k") == "0" or css.get("--kontur") == "transparent"
    serif = "serif" in str(css.get("--vurgu-font") or "")
    return {
        "kalip": kalip, "satir1": s1, "satir2": s2, "vurgu": vurgu, "ek": str(b.get("ek") or "").strip(),
        "yazi_rengi": _renk(css, "--yazi", "white"), "vurgu_rengi": _renk(css, "--vurgu", "bright orange"),
        "kutu": bool(b.get("kutu")) if kutu is None else kutu, "kontur": not kontursuz,
        "font": ("a clean bold sans-serif for the first line and an elegant italic serif for the highlighted word"
                 if serif else "a heavy geometric sans-serif (like Montserrat ExtraBold), all caps"),
        "turkce": bool(TURKCE.search(" ".join((s1, s2, str(b.get("ek") or ""))))),
        "yok": kalip == "yazisiz" or not (s1 or s2),
    }


def _yazi_cumlesi(y: dict, platform: str, b: dict) -> str:
    if y["yok"]:
        return "No text anywhere in the image."
    alan = yazi_alani(b, platform)
    if y["kalip"] == "bolunmus":
        metin = f'Two short labels at the top: "{y["satir1"]}" over the left half and "{y["satir2"]}" over the right half.'
    else:
        satirlar = " / ".join(f'"{s}"' for s in (y["satir1"], y["satir2"]) if s)
        metin = f"Headline, exactly this text on {'two lines' if y['satir1'] and y['satir2'] else 'one line'}: {satirlar}. Place it in {alan}."
    stil = f" Typeface: {y['font']}, letters {y['yazi_rengi']}"
    stil += ", thick black outline." if y["kontur"] else ", no outline."
    if y["vurgu"] and y["kalip"] != "bolunmus":
        stil += (f' The word "{y["vurgu"]}" sits inside a solid {y["vurgu_rengi"]} box with white letters.' if y["kutu"]
                 else f' The word "{y["vurgu"]}" is coloured {y["vurgu_rengi"]}.')
    ek = ""
    if y["ek"] and y["kalip"] in ("dev-yazi", "alt-bant", "not", "seri"):
        ek = {"dev-yazi": f' Behind the subject, a giant word "{y["ek"]}" partly hidden by the head.',
              "alt-bant": f' A small helper line "{y["ek"]}" in the top left.',
              "not": f' A short handwritten note "{y["ek"]}" with a hand-drawn arrow pointing at the subject.',
              "seri": f' A large brand word "{y["ek"]}" behind the head.'}[y["kalip"]]
    tr = " Spell the Turkish letters (ç, ğ, ı, İ, ö, ş, ü) exactly as written; do not add any other words." if y["turkce"] \
        else " Do not add any other words."
    return metin + stil + ek + tr + " Text must be readable at thumbnail size."


def _bos_cumlesi(b: dict, platform: str) -> str:
    if (b.get("kalip") or "") == "yazisiz":
        return "No text, letters, numbers, logos or watermarks anywhere."
    return (f"Leave {yazi_alani(b, platform)} completely clean for a headline that will be added later. "
            "No text, letters, numbers, logos or watermarks anywhere.")


# ---------------------------------------------------------------- master prompt

def _sahne(b: dict, platform: str) -> list[tuple[str, str]]:
    """Yapılı alanlar (başlık, cümle). Yapılı alan yoksa tek sahne cümlesi eski prompt'tur."""
    if not yapili(b):
        return [("Scene", _cumle(b.get("prompt")))]
    adlar = (("sahne", "Scene"), ("ifade", "Expression"), ("kompozisyon", "Composition"), ("isik", "Lighting"), ("palet", "Colour palette"))
    satir = [(baslik, _cumle(b.get(a))) for a, baslik in adlar if str(b.get(a) or "").strip()]
    kalip_eki = KALIP_PROMPT.get(b.get("kalip") or "", "").strip()
    if kalip_eki:
        satir.append(("Layout", kalip_eki))
    return satir


def _sahne_cumlesi(sahne: list[tuple[str, str]]) -> str:
    """Kısa hedefler için tek paragraf: sahne çıplak, diğerleri etiketli ("Lighting: ...")."""
    return " ".join(c if a == "Scene" else f"{a}: {c}" for a, c in sahne)


def _kimlik(refler: list[tuple[str, str]]) -> str:
    kisi = [i for i, (r, _) in enumerate(refler, 1) if r in ("kare", "yuz")]
    if not kisi:
        return ""
    adlar = " and ".join(f"Image {i}" for i in kisi)
    return f"Keep the facial features of the person in {adlar} exactly the same; only expression and pose may change as described."


def master(b: dict, platform: str, hedef: str, yazili: bool, refler: list[tuple[str, str]] = (),
           css: dict | None = None, kutu: bool | None = None) -> dict:
    """Tek hedef için kopyalanacak prompt. refler: [(rol, dosya adı)] sırası eklenecek görsel sırasıdır.

    Dönen: {hedef, ad, yazili, prompt, ayar: [[ad, değer]], ekler: [{no, rol, dosya, tarif}], notlar}."""
    if hedef not in HEDEFLER:
        raise ValueError(f"Bilinmeyen hedef: {hedef}")
    h = HEDEFLER[hedef]
    oran = ORAN[platform]
    refler = list(refler)[: h["ref_sinir"]]
    y = yazi_tarifi(b, css, kutu)
    yazi = _yazi_cumlesi(y, platform, b) if yazili else _bos_cumlesi(b, platform)
    sahne = _sahne(b, platform)
    kimlik = _kimlik(refler)
    stil_no = [i for i, (r, _) in enumerate(refler, 1) if r == "stil"]
    stil = (f"Use Image {stil_no[0]} only as a style reference: take its layout, colour palette and lighting, "
            "never its people, objects, text or logos.") if stil_no else ""
    rozet = YOUTUBE_ROZET if platform == "youtube" else ""
    hedef_cumle = PLATFORM_TARIFI[platform] + "."
    notlar: list[str] = []
    ayar: list[list[str]] = [["Oran", oran]]

    if hedef == "nano-banana-pro":
        kanal = "a top YouTube channel" if platform == "youtube" else "a top Instagram creator"
        bolum = [f"ROLE: You are the art director of {kanal}. Design one {hedef_cumle}"]
        if refler:
            bolum.append("REFERENCES:\n" + "\n".join(f"- Image {i}: {REF_TARIF[r]}." for i, (r, _) in enumerate(refler, 1)))
        if kimlik:
            bolum.append("IDENTITY: " + kimlik)
        bolum.append("SCENE:\n" + "\n".join(f"- {a}: {c}" for a, c in sahne))
        bolum.append("TEXT: " + yazi)
        if stil:
            bolum.append("STYLE: " + stil)
        bolum.append("RULES: One clear focal point, at most three elements (subject, one object, text). Strong contrast between "
                     "subject, text and background. Photographic, natural skin texture, correct hands. " + rozet)
        prompt = "\n\n".join(bolum)
        ayar += [["Çözünürlük", "2K (4K gerekmez)"], ["Model", "Nano Banana Pro (Gemini 3 Pro Image)"]]
    elif hedef == "nano-banana-21":
        prompt = " ".join(x for x in [f"{hedef_cumle}", kimlik, _sahne_cumlesi(sahne), stil, yazi, rozet] if x)
        ayar += [["Çözünürlük", "1K-2K"], ["Model", "Nano Banana 2.1"]]
        notlar.append("2.1 kısa ve net prompt'u ödüllendirir; uzatma, düzeltmeyi aynı sohbette tek cümleyle iste.")
    elif hedef == "chatgpt":
        boyut = "1536x1024 (landscape)" if platform == "youtube" else "1024x1536 (portrait)"
        giris = "Create a " + PLATFORM_TARIFI[platform].split(".")[0] + f" as a single image, size {boyut}."
        refs = " ".join(f"The attached image {i} is {REF_TARIF[r]}." for i, (r, _) in enumerate(refler, 1))
        prompt = " ".join(x for x in [giris, refs, kimlik, _sahne_cumlesi(sahne), stil, yazi, rozet,
                                       "Make it look like a real photograph, not an illustration."] if x)
        ayar += [["Boyut", boyut]]
        notlar.append("Çıktı tam 16:9/9:16 değildir; Stüdyo'ya içe alınca ortadan kırpılır.")
    elif hedef == "midjourney":
        ifadeler = [PLATFORM_TARIFI[platform].split(",")[0].lower()] + [c.rstrip(".") for _, c in sahne]
        ifadeler += ["photographic, high contrast, sharp focus on the subject, one focal point"]
        if yazili and not y["yok"]:
            ifadeler.append(" ".join(f'"{s}"' for s in (y["satir1"], y["satir2"]) if s) + " bold headline text")
            notlar.append("Midjourney yazıyı güvenilir çizmez; boş zemin sürümünü üretip yazıyı Stüdyo'da eklemek daha sağlam.")
        else:
            ifadeler.append(f"clean empty space in {yazi_alani(b, platform)}")
        parametre = f"--ar {oran} --style raw"
        if not (yazili and not y["yok"]):
            parametre += " --no text, letters, words, logo, watermark"
        if any(r in ("kare", "yuz") for r, _ in refler):
            parametre += " --oref <kişi-görseli-URL> --ow 100"
            notlar.append("--oref yerine sürümün karakter referansı (--cref) geçerliyse onu kullan; URL'yi görseli yükleyip al.")
        if stil_no:
            parametre += " --sref <stil-görseli-URL>"
        prompt = ", ".join(i for i in ifadeler if i) + " " + parametre
        ayar += [["Parametre", parametre]]
    elif hedef == "ideogram":
        prompt = " ".join(x for x in [hedef_cumle, kimlik, _sahne_cumlesi(sahne), stil, yazi, rozet,
                                       "Realistic photographic style."] if x)
        ayar += [["Magic Prompt", "Kapalı"], ["Stil", "Realistic"]]
        if refler:
            notlar.append("Kişi görselini Character Reference'a, stil görselini Style Reference'a koy.")
    else:  # leonardo
        prompt = " ".join(x for x in [hedef_cumle, kimlik, _sahne_cumlesi(sahne), stil, yazi, rozet] if x)
        ayar += [["Prompt Enhance", "Kapalı"], ["Model", "yazı için Lucid Origin ya da Phoenix; zemin için Lucid Realism"]]
        if refler:
            notlar.append("Kişi görselini Image Guidance > Character Reference'a, stili Style Reference'a koy.")
    if yazili and not y["yok"] and h["yazi"] != "zayıf":
        notlar.append("Yazı hatalı çıkarsa aynı sohbette 'yalnız yazıyı düzelt: …' de; olmazsa boş zemin sürümünü kullan.")
    ekler = [{"no": i, "rol": r, "dosya": d, "tarif": REF_TARIF[r]} for i, (r, d) in enumerate(refler, 1)]
    return {"hedef": hedef, "ad": h["ad"], "nerede": h["nerede"], "yazili": yazili, "prompt": prompt.strip(),
            "ayar": ayar, "ekler": ekler, "notlar": notlar}


def master_md(b: dict, platform: str, refler: list[tuple[str, str]] = (), css: dict | None = None,
              kutu: bool | None = None, baslik: str = "") -> str:
    """Bütün hedefler, yazılı ve boş zemin sürümleri tek markdown'da (teslim ve indirme)."""
    satir = [f"# Kapak master prompt{(' · ' + baslik) if baslik else ''}", "",
             f"Platform: {platform} ({ORAN[platform]}). Yazı alanı: {yazi_alani(b, platform)}.", ""]
    if refler:
        satir += ["## Eklenecek görseller (bu sırayla)", ""]
        satir += [f"{i}. `{d}`: {REF_TARIF[r]}" for i, (r, d) in enumerate(refler, 1)] + [""]
    satir += ["Boş zemin sürümünü üretip Stüdyo > Kapak > Dış görseli içe al ile geri yüklersen yazı kodla eklenir "
              "(Türkçe harf bozulmaz).", ""]
    for hedef in HEDEFLER:
        for yazili in (True, False):
            m = master(b, platform, hedef, yazili, refler, css, kutu)
            satir += [f"## {m['ad']} · {'yazılı' if yazili else 'boş zemin'}", "", f"Nerede: {m['nerede']}", "",
                      "```text", m["prompt"], "```", ""]
            satir += [f"- {a}: {d}" for a, d in m["ayar"]] + [f"- Not: {n}" for n in m["notlar"]] + [""]
    return "\n".join(satir)
