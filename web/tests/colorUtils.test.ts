import { describe, expect, it } from "vitest";
import { getContrastingTextColor } from "../src/utils/colorUtils";

describe("getContrastingTextColor", () => {
  it("uses white text on dark command colors", () => {
    expect(getContrastingTextColor("#234579")).toBe("#ffffff");
    expect(getContrastingTextColor("#315d46")).toBe("#ffffff");
  });

  it("uses dark text on light command colors", () => {
    expect(getContrastingTextColor("#f0a000")).toBe("#151515");
    expect(getContrastingTextColor("#b9daea")).toBe("#151515");
  });

  it("uses dark text when the color cannot be parsed", () => {
    expect(getContrastingTextColor("not-a-color")).toBe("#151515");
  });
});
