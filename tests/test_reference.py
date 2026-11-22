import json
import subprocess

import pytest

from vedit import reference


def test_analyze_url_indirme_basarisizsa_neden_soyler(tmp_path, monkeypatch):
    """Meta gelir ama video inmezse eksik digest yerine açık hata: yt-dlp çıkış kodu ve son satırı."""
    def sahte(*args):
        if "--dump-json" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps({"id": "abc", "duration": 30}), "")
        return subprocess.CompletedProcess(args, 1, "", "ERROR: Video unavailable")

    monkeypatch.setattr(reference, "_ytdlp", sahte)
    with pytest.raises(RuntimeError, match="video indirilemedi.*Video unavailable"):
        reference.analyze_url("https://example.invalid/v", tmp_path)
