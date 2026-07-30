import { describe, expect, it } from "vitest";
import type { Scenario } from "../src/types";
import {
  copyCardPaletteParams,
  normalizeScenarioRange,
} from "../src/utils/rangeUtils";

const scenarios = [1, 3, 5].map(
  (number): Scenario => ({
    number,
    name: `Scenario ${number}`,
    confederateUnits: [],
    unionUnits: [],
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateGunboats: [],
    unionGunboats: [],
  }),
);

describe("range URL utilities", () => {
  it("defaults missing scenario parameters to the full game", () => {
    expect(normalizeScenarioRange(scenarios, null, null)).toMatchObject({
      from: 1,
      to: 5,
      scenarios,
    });
  });

  it("normalizes reversed ranges by scenario position", () => {
    const range = normalizeScenarioRange(scenarios, 5, 3);
    expect(range.from).toBe(3);
    expect(range.to).toBe(5);
    expect(range.scenarios.map((scenario) => scenario.number)).toEqual([3, 5]);
  });

  it("falls back to valid boundaries for unknown scenarios", () => {
    expect(normalizeScenarioRange(scenarios, 2, 8)).toMatchObject({
      from: 1,
      to: 5,
    });
  });

  it("copies only card palette parameters", () => {
    const source = new URLSearchParams(
      "view=cards&confederateColor=%23112233&unionColor=%23445566",
    );
    const destination = new URLSearchParams("from=3&to=5");

    copyCardPaletteParams(source, destination);

    expect(destination.toString()).toBe(
      "from=3&to=5&confederateColor=%23112233&unionColor=%23445566",
    );
  });
});
