import { afterEach, describe, expect, it, vi } from "vitest";
import { useKurgu } from "./depo";
import { KISAYOLLAR } from "./kisayol";

describe("kisayol play() reddi koruması (bulgu 14)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    useKurgu.setState({ odak: "program" });
  });

  it("kaynak videosunda play() reddedilirse unhandled rejection üretmez", async () => {
    const play = vi.fn().mockRejectedValue(new Error("autoplay engeli"));
    const video = { paused: true, playbackRate: 1, currentTime: 0, play, pause: vi.fn() };
    vi.stubGlobal("document", { querySelector: () => video });
    useKurgu.setState({ odak: "kaynak" });

    const hatalar: unknown[] = [];
    const dinle = (e: unknown) => hatalar.push(e);
    process.on("unhandledRejection", dinle);
    try {
      KISAYOLLAR.find((x) => x.id === "oynat")!.calis();
      KISAYOLLAR.find((x) => x.id === "l")!.calis();
      await new Promise((r) => setTimeout(r, 10));
    } finally {
      process.off("unhandledRejection", dinle);
    }
    expect(play).toHaveBeenCalledTimes(2);
    expect(hatalar).toEqual([]);
  });
});
