"""Self-check for the Turkish patches in the yt-* tools.  python -X utf8 test_tr.py"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("yt-script", "yt-package", "yt-edit", "yt-chapters"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import hookscore, title, deadair, chapters

# Turkish letters survive tokenizing, İ does not split the word
assert title.words("İşletmenize Özel Çözüm") == ["işletmenize", "özel", "çözüm"]
assert chapters.keywords("İşletmenize gelen müşteriler") == {"işletmenize", "gelen", "müşteriler"}

# TR second person, stakes and curiosity are recognised
p = hookscore.score("Reklama ayda 20 bin lira yakıyorsun ama müşterilerin yarısı telefonu hiç açmıyor. Neden?")[0]
assert p["ADDRESS"] > 26 and p["STAKES"] > 22 and p["CURIOSITY"] > 24 and p["SPECIFICITY"] > 34, p
# English scoring is unchanged
assert hookscore.score("You lose 3 hours a day. Here is why.")[0]["ADDRESS"] > 26

# TR filler cue, and vedit transcript.json shape
assert deadair.FILLER_ONLY.match("ıı yani") and not deadair.FILLER_ONLY.match("yani bu çalışıyor")
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
    json.dump({"files": {"a-roll": {"segments": [{"start": 0, "end": 1.5, "text": "Merhaba"}]}}}, f)
assert deadair.load(f.name) == [(0.0, 1.5, "Merhaba")]
os.unlink(f.name)
print("ok")
