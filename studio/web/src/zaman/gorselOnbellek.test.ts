import { afterEach, describe, expect, it, vi } from "vitest";
import { degisinceHaberVer, seritAl, temizle } from "./gorselOnbellek";

describe("gorselOnbellek (bulgu 11 & 12)", () => {
  afterEach(() => {
    temizle();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("img.onerror sonrası önbellek temizlenip yeniden denemeye açılır", async () => {
    vi.useFakeTimers();
    let imgInst: { onload?: () => void; onerror?: () => void; src?: string } | null = null;
    class FakeImage {
      onload?: () => void;
      onerror?: () => void;
      src = "";
      constructor() { imgInst = this; }
    }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ n: 4, k: 1, url: "/serit.jpg" }) });
    vi.stubGlobal("Image", FakeImage);
    vi.stubGlobal("fetch", fetchMock);

    const haber = vi.fn();
    const coz = degisinceHaberVer(haber);
    expect(seritAl("s/p", "inputs:a.mp4")).toBeNull();
    await vi.waitFor(() => expect(imgInst).not.toBeNull());
    imgInst!.onerror?.();

    // 5 sn bekleme dolunca önbellek anahtarı silinir ve dinleyici çağrılır
    await vi.advanceTimersByTimeAsync(5000);
    expect(haber).toHaveBeenCalledTimes(1);
    seritAl("s/p", "inputs:a.mp4");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    coz();
  });

  it("degisinceHaberVer iptal fonksiyonu eski aboneliği kaldırır, yenisini bozmaz", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockRejectedValue(new Error("ağ"));
    vi.stubGlobal("fetch", fetchMock);

    const eski = vi.fn();
    const yeni = vi.fn();
    const cozEski = degisinceHaberVer(eski);
    const cozYeni = degisinceHaberVer(yeni);
    cozEski(); // eski iptal yeni dinleyiciyi silmemeli
    seritAl("s/p", "inputs:b.mp4");
    await vi.advanceTimersByTimeAsync(5000);
    expect(eski).not.toHaveBeenCalled();
    expect(yeni).toHaveBeenCalledTimes(1);

    cozYeni();
    seritAl("s/p", "inputs:c.mp4");
    await vi.advanceTimersByTimeAsync(5000);
    expect(yeni).toHaveBeenCalledTimes(1);
  });
});
