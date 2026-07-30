import { describe, expect, it } from "vitest";
import agaData from "../public/data/aga.json";
import type { Unit } from "../src/types";
import { buildScenarioCards } from "../src/utils/cardUtils";

function unit(
  name: string,
  command: string,
  type = "Inf",
  size = "Brig",
): Unit {
  return {
    name,
    command,
    type,
    size,
    manpowerValue: "1",
    hexLocation: "N0101",
    notes: [],
  };
}

describe("buildScenarioCards", () => {
  it("excludes leaders and special units from card slots", () => {
    const cards = buildScenarioCards("test", 1, "union", [
      unit("Leader", "I", "Ldr", "Corps"),
      unit("Infantry", "I"),
      unit("Wagon", "I", "Special", "-"),
    ]);

    expect(cards).toHaveLength(1);
    expect(cards[0].title).toBe("I Leader");
    expect(cards[0].units.map((entry) => entry.name)).toEqual(["Infantry"]);
  });

  it("balances commands across cards of no more than six units", () => {
    const cards = buildScenarioCards(
      "test",
      1,
      "confederate",
      Array.from({ length: 10 }, (_, index) => unit(`Unit ${index + 1}`, "P")),
    );

    expect(cards.map((card) => card.units.length)).toEqual([5, 5]);
    expect(cards.flatMap((card) => card.units.map((entry) => entry.name))).toEqual(
      Array.from({ length: 10 }, (_, index) => `Unit ${index + 1}`),
    );
    expect(cards.map((card) => card.cardIndex)).toEqual([1, 2]);
    expect(cards.map((card) => card.id)).toEqual([
      "confederate-p-1",
      "confederate-p-2",
    ]);
    expect(cards.every((card) => card.cardCount === 2)).toBe(true);
  });

  it("keeps nested division commands on separate cards", () => {
    const cards = buildScenarioCards("test", 1, "union", [
      unit("Corps Leader", "I", "Ldr", "Corps"),
      unit("Division Leader", "1-I", "Ldr", "Div"),
      unit("Corps Unit", "I"),
      unit("Division Unit", "1-I"),
    ]);

    expect(cards.map((card) => card.commandCode)).toEqual(["I", "1-I"]);
    expect(cards.map((card) => card.units[0].name)).toEqual([
      "Corps Unit",
      "Division Unit",
    ]);
  });

  it("applies scenario title and order overrides", () => {
    const cards = buildScenarioCards("aga", 5, "confederate", [
      unit("Jackson", "S"),
      unit("Cocke", "P"),
    ]);

    expect(cards.map((card) => card.title)).toEqual([
      "P Beauregard",
      "S Johnston",
    ]);
  });

  it("groups units without commands as independent", () => {
    const cards = buildScenarioCards("test", 1, "confederate", [
      unit("Cavalry", "-"),
    ]);

    expect(cards[0]).toMatchObject({
      commandCode: "-",
      title: "Independent",
    });
  });

  it("selects the same modal command color regardless of unit order", () => {
    const forward = buildScenarioCards("aga", 5, "confederate", [
      unit("Cocke", "P"),
      unit("Hunton", "P"),
      unit("Early", "P"),
    ]);
    const reversed = buildScenarioCards("aga", 5, "confederate", [
      unit("Early", "P"),
      unit("Hunton", "P"),
      unit("Cocke", "P"),
    ]);

    expect(forward[0].color).toBe("#f0a000");
    expect(reversed[0].color).toBe(forward[0].color);
  });

  it("includes every AGA scenario 5 combat unit exactly once", () => {
    const scenario = agaData.scenarios.find((entry) => entry.number === 5);
    expect(scenario).toBeDefined();

    for (const side of ["confederate", "union"] as const) {
      const units = scenario?.[`${side}Units`] ?? [];
      const expected = units.filter(
        (entry) => entry.type !== "Ldr" && entry.type !== "Special",
      );
      const cards = buildScenarioCards("aga", 5, side, units);
      const rendered = cards.flatMap((card) => card.units);

      expect(cards.every((card) => card.units.length <= 6)).toBe(true);
      expect(rendered).toHaveLength(expected.length);
      expect(new Set(rendered)).toEqual(new Set(expected));
    }
  });
});
