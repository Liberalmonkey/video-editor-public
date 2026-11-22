import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vedit import paths
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    (tmp_path / "out" / "instagram" / "x" / "work" / "public").mkdir(parents=True)
    (tmp_path / "out" / "instagram" / "x" / "work" / "public" / "a.txt").write_text("merhaba")
    (tmp_path / "out" / "instagram" / "sir.txt").write_text("gizli")
    c = TestClient(create_app("t0k", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    return c


def giris(c):
    r = c.get("/?token=t0k")
    assert r.status_code == 303 and "httponly" in r.headers["set-cookie"].lower()
    return c


def test_tokensiz_reddedilir(client):
    assert client.get("/api/projeler").status_code == 401
    assert client.get("/?token=yanlis").status_code == 401
    assert client.get("/pub/instagram/x/a.txt").status_code == 401


def test_yabanci_host_ve_origin(client):
    giris(client)
    assert client.get("/api/projeler", headers={"host": "evil.test"}).status_code == 403
    assert client.get("/api/projeler", headers={"origin": "http://evil.test"}).status_code == 403
    assert client.get("/api/projeler").status_code == 200


def test_yazma_origin_ister(client):
    giris(client)
    assert client.post("/api/kurgu/instagram/x/icerial").status_code == 403
    r = client.post("/api/kurgu/instagram/x/icerial", headers={"origin": f"http://{HOST}"})
    assert r.status_code != 403


@pytest.mark.parametrize("url", [
    "/pub/instagram/x/../../sir.txt", "/pub/instagram/x/..%2F..%2Fsir.txt",
    "/dosya/instagram/x/public/..%2F..%2F..%2Fsir.txt", "/dosya/instagram/x/raw/a.txt",
    "/api/kurgu/..%2F/x", "/pub/instagram/..%2Fx/a.txt",
])
def test_kok_disi_yol(client, url):
    giris(client)
    r = client.get(url)
    assert r.status_code != 200 or "gizli" not in r.text


def test_kok_ici_dosya_ve_range(client):
    giris(client)
    assert client.get("/pub/instagram/x/a.txt").text == "merhaba"
    r = client.get("/pub/instagram/x/a.txt", headers={"range": "bytes=0-2"})
    assert r.status_code == 206 and r.text == "mer"
