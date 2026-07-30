import { describe, expect, it } from "vitest";
import type { Scenario, Unit } from "../src/types";
import {
  buildRangeCards,
  formatScenarioNumbers,
  getPhysicalUnitIdentity,
  normalizeCardCommand,
} from "../src/utils/cardUtils";

function unit(
  name: string,
  command: string,
  type = "Inf",
  size = "Brig",
  tableName?: string,
): Unit {
  return {
    name,
    command,
    type,
    size,
    manpowerValue: "1",
    hexLocation: "N0101",
    notes: [],
    tableName,
  };
}

function scenario(
  number: number,
  confederateUnits: Unit[] = [],
  unionUnits: Unit[] = [],
): Scenario {
  return {
    number,
    name: `Scenario ${number}`,
    confederateUnits,
    unionUnits,
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateGunboats: [],
    unionGunboats: [],
  };
}

describe("range card utilities", () => {
  it("normalizes independent command aliases", () => {
    expect(["", "-", "—", "(-)"].map(normalizeCardCommand)).toEqual([
      "-",
      "-",
      "-",
      "-",
    ]);
  });

  it("distinguishes units with the same name but different counter types", () => {
    expect(
      getPhysicalUnitIdentity("union", unit("Thomas", "-", "Inf")),
    ).not.toBe(
      getPhysicalUnitIdentity("union", unit("Thomas", "-", "Cav", "Regt")),
    );
  });

  it("formats compact scenario ranges", () => {
    expect(formatScenarioNumbers([3, 4, 5, 7, 9, 10])).toBe("S3-5,7,9-10");
  });

  it("deduplicates stable physical units across scenarios and setup tables", () => {
    const cards = buildRangeCards(
      "test",
      [
        scenario(1, [unit("Ward", "M", "Inf", "Brig", "Setup A")]),
        scenario(2, [
          unit("Ward", "M", "Inf", "Brig", "Setup B"),
          unit("Ward", "M", "Inf", "Brig", "Setup C"),
        ]),
      ],
      "confederate",
    );

    expect(cards).toHaveLength(1);
    expect(cards[0].units).toHaveLength(1);
    expect(cards[0].units[0]).toMatchObject({
      scenarioNumbers: [1, 2],
      scenarioLabel: "S1-2",
    });
  });

  it("duplicates and labels a unit that changes command", () => {
    const cards = buildRangeCards(
      "test",
      [
        scenario(5, [], [unit("McCunn", "V")]),
        scenario(6, [], [unit("McCunn", "(-)")]),
        scenario(7, [], [unit("McCunn", "-")]),
      ],
      "union",
    );

    expect(cards.map((card) => card.commandCode)).toEqual(["V", "-"]);
    expect(cards.map((card) => card.units[0].scenarioLabel)).toEqual([
      "S5",
      "S6-7",
    ]);
  });

  it("balances large command supersets across cards", () => {
    const cards = buildRangeCards(
      "test",
      [
        scenario(
          1,
          Array.from({ length: 10 }, (_, index) =>
            unit(`Unit ${index + 1}`, "P"),
          ),
        ),
      ],
      "confederate",
    );

    expect(cards.map((card) => card.units.length)).toEqual([5, 5]);
    expect(cards.map((card) => card.cardIndex)).toEqual([1, 2]);
  });

  it("uses a consistent leader name and canonical range overrides", () => {
    const cards = buildRangeCards(
      "aga",
      [
        scenario(3, [
          unit("Beauregard", "-", "Ldr", "District"),
          unit("Cocke", "P"),
          unit("Johnston", "S", "Ldr", "District"),
          unit("Jackson", "S"),
        ]),
      ],
      "confederate",
    );

    expect(cards.map((card) => card.title)).toEqual([
      "P Beauregard",
      "S Johnston",
    ]);
  });
});
