import { describe, expect, it } from "vitest";
import { zamanKodu } from "./depo";
import { tusAdi } from "./kisayol";

const t = (key: string, ek: Partial<KeyboardEvent> = {}) => ({ key, ctrlKey: false, metaKey: false, shiftKey: false, altKey: false, ...ek }) as KeyboardEvent;

describe("zaman kodu", () => {
  it("kareye yuvarlar, taşma doğru", () => {
    expect(zamanKodu(0, 30)).toBe("00:00:00:00");
    expect(zamanKodu(1.5, 30)).toBe("00:00:01:15");
    expect(zamanKodu(3661 + 29 / 30, 30)).toBe("01:01:01:29");
    expect(zamanKodu(59.9999, 30)).toBe("00:01:00:00");
  });
});

describe("tuş adı", () => {
  it("Türkçe ı, i sayılır", () => {
    expect(tusAdi(t("ı"))).toBe("i");
    expect(tusAdi(t("i"))).toBe("i");
  });
  it("büyük küçük harf ve değiştirici", () => {
    expect(tusAdi(t("K", { ctrlKey: true }))).toBe("ctrl+k");
    expect(tusAdi(t("Z", { ctrlKey: true, shiftKey: true }))).toBe("ctrl+shift+z");
    expect(tusAdi(t("Delete", { shiftKey: true }))).toBe("shift+delete");
    expect(tusAdi(t("ArrowLeft"))).toBe("arrowleft");
  });
  it("shift ile yazılan noktalama tuşun kendisidir", () => {
    expect(tusAdi(t("+", { shiftKey: true }))).toBe("+");
    expect(tusAdi(t("'", {}))).toBe("'");
    expect(tusAdi(t(" "))).toBe(" ");
  });
});
