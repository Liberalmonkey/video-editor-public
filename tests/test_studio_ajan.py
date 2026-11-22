import json
import sys
import time

import pytest

pytest.importorskip("fastapi")

from vedit import ajan_cagri, motorlar
from vedit.studio import ajan, isler

MODELLER = ["haiku", "gemini-3.8-flash-low", "gpt-6-luna", "opencode/big-pickle"]


def A(**k):
    return ajan.argumanlar(ajan.AjanIstek(**{"motor": "claude", "model": "haiku", "istem": "selam", **k}), MODELLER)


def test_argumanlar_claude_ve_agy():
    assert A() == ["-p", "selam", "--model", "haiku", "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits"]
    assert A(mod="plan", oturum="b11b9fbc-0811-417c")[-3:] == ["plan", "--resume", "b11b9fbc-0811-417c"]
    g = A(motor="antigravity", model="gemini-3.8-flash-low", oturum="0b9f4982-97bc")
    assert g[-4:] == ["--mode", "accept-edits", "--conversation", "0b9f4982-97bc"]
    assert A(studyo="instagram", ad="x")[1].startswith("Proje: Projeler/inputs/instagram/x")
    assert A(istem="--dangerously-skip-permissions")[1] == " --dangerously-skip-permissions"


def test_argumanlar_codex_ve_opencode():
    assert A(motor="codex", model="gpt-6-luna") == ["exec", "--json", "-c", 'sandbox_mode="workspace-write"', "-m", "gpt-6-luna", "selam"]
    # devam: `exec resume <id>`; resume -s almadığı için sandbox -c ile
    assert A(motor="codex", model="gpt-6-luna", mod="plan", oturum="01a1e962-d72a-7fb1-8423-79e08566ab62") == \
        ["exec", "resume", "01a1e962-d72a-7fb1-8423-79e08566ab62", "--json", "-c", 'sandbox_mode="read-only"', "-m", "gpt-6-luna", "selam"]
    assert A(motor="opencode", model="opencode/big-pickle") == \
        ["run", "--format", "json", "-m", "opencode/big-pickle", "--agent", "build", "selam"]
    assert A(motor="opencode", model="opencode/big-pickle", mod="plan", oturum="ses_e1696ff83ffe5idjJO4sVcMBtP")[-4:] == \
        ["plan", "-s", "ses_e1696ff83ffe5idjJO4sVcMBtP", "selam"]
    for m, model in (("codex", "gpt-6-luna"), ("opencode", "opencode/big-pickle")):
        a = A(motor=m, model=model, istem="--dangerously-bypass-approvals-and-sandbox")
        assert a[-1] == " --dangerously-bypass-approvals-and-sandbox" and "--auto" not in a
        assert not any(x.startswith("--dangerously") for x in a)


def test_argumanlar_beyaz_liste():
    for kotu in (dict(motor="bash"), dict(model="opus; calc"), dict(mod="bypassPermissions"), dict(oturum="a b;c"),
                 dict(istem="   "), dict(studyo="instagram", ad="../x"), dict(motor="codex", model="haiku-yok")):
        with pytest.raises(Exception) as e:
            A(**kotu)
        assert getattr(e.value, "status_code", 0) == 400, kotu


def test_ajan_cagri_model_yoksa_varsayilan(monkeypatch):
    monkeypatch.setattr(motorlar, "bas", lambda m: ["X"])
    monkeypatch.setattr(motorlar, "_codex_modeller", lambda b: ([], None))
    assert ajan_cagri.komut("-x", "codex", None, None) == ["X", "exec", "--json", "-c", 'sandbox_mode="workspace-write"', " -x"]
    # Codex'te model verilmezse CLI kataloğunun varsayılanı yazılır (config'teki model CLI'da olmayabilir)
    monkeypatch.setattr(motorlar, "_codex_modeller", lambda b: ([{"id": "gpt-5.6-luna"}], "gpt-5.6-luna"))
    assert ajan_cagri.komut("a", "codex", None, None)[-3:] == ["-m", "gpt-5.6-luna", "a"]
    assert ajan_cagri.komut("a", "opencode", None, "ses_12345678") == ["X", "run", "--format", "json", "--agent", "build", "-s", "ses_12345678", "a"]
    with pytest.raises(SystemExit):
        ajan_cagri.komut("a", "bash", None, None)


def test_model_ayristiricilar():
    o = {"models": [{"slug": "gizli", "visibility": "hide", "priority": 1}, {"slug": "b", "display_name": "B", "priority": 3},
                    {"slug": "a", "display_name": "A", "visibility": "list", "priority": 2}]}
    assert [(m["id"], m["ad"]) for m in motorlar.codex_ayristir(o)] == [("a", "A"), ("b", "B")]
    assert motorlar.codex_ayristir({}) == []
    oc = motorlar.opencode_ayristir("openrouter/x/y:free\nopenai/gpt-5\nopencode/big-pickle\nbozuk satır\ncloudflare-workers-ai/@cf/m")
    assert [m["id"] for m in oc] == ["opencode/big-pickle", "openai/gpt-5", "openrouter/x/y:free", "cloudflare-workers-ai/@cf/m"]
    assert [m.get("ucretsiz", False) for m in oc] == [True, False, True, False]
    assert oc[0]["grup"] == "OpenCode Zen" and oc[3]["grup"] == "Cloudflare Workers AI" and oc[2]["ad"] == "x/y:free"
    ag = motorlar.agy_ayristir("Fetching available models...\ngemini-4-argon-low\tGemini 4 Argon (Low)\nclaude-opus-5-5-low\tClaude Opus 5.5 (Low)")
    assert [(m["id"], m["grup"]) for m in ag] == [("gemini-4-argon-low", "Gemini"), ("claude-opus-5-5-low", "Claude")]


def test_cevirici_claude():
    is_ = isler.Is(1, "ajan", "t", [])
    c = ajan.cevirici()
    j = lambda o: c(is_, json.dumps(o))
    assert j({"type": "system", "subtype": "hook_started", "session_id": "s"}) == []
    assert j({"type": "system", "subtype": "init", "session_id": "s1", "model": "claude-sonnet-5-5"}) == ["Model: claude-sonnet-5-5"]
    assert j({"type": "assistant", "message": {"content": [{"type": "text", "text": "a\nb"},
              {"type": "tool_use", "name": "Edit", "input": {"file_path": "work/edit/kurgu.json"}}]}}) == ["a", "b", "→ Edit work/edit/kurgu.json"]
    assert j({"type": "result", "duration_ms": 4200, "session_id": "s2"}) == ["Bitti · 4 sn"]
    assert is_.oturum == "s2"
    assert c(is_, "düz satır") == ["düz satır"]


def test_cevirici_agy():
    is_ = isler.Is(1, "ajan", "t", [])
    c = ajan.cevirici()
    j = lambda o: c(is_, json.dumps(o))
    assert j({"event": "init", "conversation_id": "k1", "init": {"model": "gemini-3.8-flash-low"}}) == ["Model: gemini-3.8-flash-low"]
    adim = lambda d, s: {"event": "step_update", "step_update": {"step_type": "agent_response", "state": s, "text_delta": d}}
    assert j(adim("mer", "ACTIVE")) == [] and j(adim("haba\n", "DONE")) == ["merhaba"]
    for tur in ("system_message", "error_message"):
        assert j({"event": "step_update", "step_update": {"step_type": tur, "state": "DONE"}}) == []
    assert j({"event": "step_update", "step_update": {"step_type": "read_file", "state": "DONE"}}) == ["→ read_file"]
    assert j({"event": "result", "result": {"conversation_id": "k2", "status": "SUCCESS", "duration_seconds": 3.8}}) == ["Bitti · 4 sn"]
    assert is_.oturum == "k2"


def test_cevirici_codex():
    # Satırlar codex-cli 0.154.0 `exec --json` çıktısından (2026-11-17 ölçümü)
    is_ = isler.Is(1, "ajan", "t", [], model="gpt-5.6-luna")
    c = ajan.cevirici()
    j = lambda o: c(is_, json.dumps(o))
    assert c(is_, "Reading additional input from stdin...") == []
    assert j({"type": "thread.started", "thread_id": "01a1e962-d72a-7fb1-8423-79e08566ab62"}) == ["Model: gpt-5.6-luna"]
    assert is_.oturum == "01a1e962-d72a-7fb1-8423-79e08566ab62"
    assert j({"type": "turn.started"}) == []
    assert j({"type": "item.completed", "item": {"id": "item_0", "type": "error", "message": "Skill descriptions were shortened"}}) == []
    assert j({"type": "item.completed", "item": {"type": "agent_message", "text": "Okuyorum.\nTamam"}}) == ["Okuyorum.", "Tamam"]
    k = "\"C:\\\\WINDOWS\\\\System32\\\\WindowsPowerShell\\\\v1.0\\\\powershell.exe\" -Command 'Get-Content -LiteralPath README.md -TotalCount 1'"
    assert j({"type": "item.started", "item": {"type": "command_execution", "command": k}}) == []
    assert j({"type": "item.completed", "item": {"type": "command_execution", "command": k, "exit_code": 0}}) == \
        ["→ Komut Get-Content -LiteralPath README.md -TotalCount 1"]
    assert j({"type": "item.completed", "item": {"type": "file_change", "changes": [{"path": "work/edit/kurgu.json", "kind": "update"}]}}) == \
        ["→ Düzenle work/edit/kurgu.json"]
    assert j({"type": "turn.completed", "usage": {"input_tokens": 1}})[0].startswith("Bitti · ")
    hata = json.dumps({"type": "error", "status": 400, "error": {"message": "The 'x' model is not supported"}})
    assert j({"type": "error", "message": hata}) == []
    assert j({"type": "turn.failed", "error": {"message": hata}}) == ["Hata: The 'x' model is not supported"]


def test_cevirici_opencode():
    # Satırlar opencode v2.3.0 `run --format json` çıktısından (2026-11-17 ölçümü)
    is_ = isler.Is(1, "ajan", "t", [], model="opencode/big-pickle")
    c = ajan.cevirici()
    s = "ses_e1696ff83ffe5idjJO4sVcMBtP"
    j = lambda t, ts, **p: c(is_, json.dumps({"type": t, "timestamp": ts, "sessionID": s, "part": p}))
    assert j("step_start", 1794917338371, type="step-start") == []
    assert is_.oturum == s
    assert j("tool_use", 1794917338612, type="tool", tool="read", state={"status": "completed", "input": {"path": "README.md"}}) == \
        ["Model: opencode/big-pickle", "→ read README.md"]
    assert j("step_finish", 1794917338760, type="step-finish", reason="tool-calls") == []
    assert j("text", 1794917342538, type="text", text="# AI Video Editor") == ["# AI Video Editor"]
    assert j("step_finish", 1794917342668, type="step-finish", reason="stop") == ["Bitti · 4 sn"]
    assert c(is_, json.dumps({"type": "error", "sessionID": s, "error": {"type": "provider.no-route",
                                                                          "message": "Model unavailable: openai/yok"}})) == \
        ["Hata: Model unavailable: openai/yok"]


def test_ajan_kuyrugu_ayri_ve_cevirili():
    k = isler.Kuyruk(exe=sys.executable)
    is_ = k.ekle("ajan", "t", ["-c", "print('{\"type\": \"system\", \"subtype\": \"init\", \"session_id\": \"zz\", \"model\": \"m\"}')"],
                 exe=sys.executable, motor="claude", model="m", cevir=ajan.cevirici())
    for _ in range(200):
        if is_.bitis:
            break
        time.sleep(0.05)
    assert (is_.durum, is_.satirlar, is_.ozet()["oturum"]) == ("bitti", ["Model: m"], "zz")
