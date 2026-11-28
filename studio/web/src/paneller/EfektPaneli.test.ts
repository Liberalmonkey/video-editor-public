import { afterEach, describe, expect, it, vi } from "vitest";

const istekMock = vi.fn();
vi.mock("../api", () => ({ istek: (...a: unknown[]) => istekMock(...a) }));

import { useKurgu } from "../zaman/depo";
import { reframeYap } from "./EfektPaneli";

describe("EfektPaneli reframeYap proje yarışı (bulgu 8)", () => {
  afterEach(() => {
    istekMock.mockReset();
    useKurgu.setState({ anahtar: null });
  });

  it("istek uçuşta iken başka projeye geçilirse eski reframe sonucu yeni kurguyu düzenlemez", async () => {
    const duzenle = vi.fn();
    const kaydet = vi.fn().mockResolvedValue(undefined);
    useKurgu.setState({ anahtar: "reels/eski", kaydet, duzenle });

    let coz!: (v: unknown) => void;
    istekMock.mockReturnValue(new Promise((r) => { coz = r; }));

    const islem = reframeYap("c1");
    await vi.waitFor(() => expect(istekMock).toHaveBeenCalledTimes(1));

    // Proje değişti
    useKurgu.setState({ anahtar: "reels/yeni" });
    coz({ x: [], olcek: [], anim: [], yuz_orani: 0.8 });
    await islem;

    expect(duzenle).not.toHaveBeenCalled();
  });
});
