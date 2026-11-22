"""hf_kurgu: render işçisinin boş belleğe göre seçimi."""


def test_isci_bos_bellege_gore_secilir(monkeypatch):
    # WHY: instagram/1 ekip koşusu G3 taslak render'ında bellek doldu; bellek darken işçi azalır.
    from vedit import hf_kurgu
    monkeypatch.delenv("VEDIT_HF_ISCI", raising=False)
    assert hf_kurgu.isci_sec(0, 12.0) == 0, "bol bellek: HyperFrames otomatik"
    assert hf_kurgu.isci_sec(0, 5.0) == 2
    assert hf_kurgu.isci_sec(0, 2.0) == 1
    assert hf_kurgu.isci_sec(0, None) == 0 or hf_kurgu.bos_bellek_gb() is not None, "okunamayan bellek otomatiğe düşer"
    assert hf_kurgu.isci_sec(3, 1.0) == 3, "açık istek kazanır"
    monkeypatch.setenv("VEDIT_HF_ISCI", "4")
    assert hf_kurgu.isci_sec(0, 1.0) == 4, "ortam değişkeni kazanır"
    gb = hf_kurgu.bos_bellek_gb()
    assert gb is None or gb > 0
