import { describe, expect, it } from "vitest";
import agaData from "../public/data/aga.json";
import hcrData from "../public/data/hcr.json";
import hsnData from "../public/data/hsn.json";
import otr2Data from "../public/data/otr2.json";
import sjwData from "../public/data/sjw.json";
import type { GameData, Scenario } from "../src/types";
import {
  buildRangeCards,
  type CardSide,
  type RangeCommandCard,
} from "../src/utils/cardUtils";

function game(data: unknown): GameData {
  return data as GameData;
}

function cardsFor(
  gameId: string,
  scenarios: Scenario[],
): RangeCommandCard[] {
  return (["confederate", "union"] as CardSide[]).flatMap((side) =>
    buildRangeCards(gameId, scenarios, side),
  );
}

function units(cards: RangeCommandCard[]) {
  return cards.flatMap((card) => card.units);
}

describe("range card game fixtures", () => {
  it("builds the AGA 3-5 superset with unit applicability labels", () => {
    const scenarios = game(agaData).scenarios.filter(
      (scenario) => scenario.number >= 3 && scenario.number <= 5,
    );
    const cards = cardsFor("aga", scenarios);

    expect(cards).toHaveLength(13);
    expect(units(cards)).toHaveLength(48);
    expect(units(cards).every((entry) => entry.scenarioLabel)).toBe(true);
  });

  it("labels both AGA placements when McCunn changes command", () => {
    const scenarios = game(agaData).scenarios.filter(
      (scenario) => scenario.number >= 5 && scenario.number <= 7,
    );
    const cards = cardsFor("aga", scenarios);
    const mcCunn = units(cards).filter((entry) => entry.unit.name === "McCunn");

    expect(
      mcCunn.map((entry) => entry.scenarioLabel).sort(),
    ).toEqual(["S5", "S6-7"]);
  });

  it("builds the full SJW deck without duplicate command placements", () => {
    const cards = cardsFor("sjw", game(sjwData).scenarios);

    expect(cards).toHaveLength(17);
    expect(new Set(units(cards).map((entry) => entry.identity)).size).toBe(
      units(cards).length,
    );
  });

  it("splits HCR command L across four cards", () => {
    const cards = cardsFor("hcr", game(hcrData).scenarios);
    const commandL = cards.filter(
      (card) => card.side === "confederate" && card.commandCode === "L",
    );

    expect(commandL).toHaveLength(4);
    expect(units(cards).every((entry) => entry.scenarioLabel)).toBe(true);
  });

  it("duplicates HSN units that move between commands", () => {
    const cards = cardsFor("hsn", game(hsnData).scenarios);
    const allUnits = units(cards);
    const identityCounts = new Map<string, number>();
    for (const entry of allUnits) {
      identityCounts.set(
        entry.identity,
        (identityCounts.get(entry.identity) ?? 0) + 1,
      );
    }
    const duplicatedIdentities = Array.from(identityCounts.values()).filter(
      (count) => count > 1,
    );

    expect(cards).toHaveLength(28);
    expect(duplicatedIdentities).toHaveLength(9);
    expect(allUnits.every((entry) => entry.scenarioLabel)).toBe(true);
  });

  it("collapses OTR2 scenario 9 alternative setup tables", () => {
    const scenario = game(otr2Data).scenarios.find(
      (entry) => entry.number === 9,
    );
    expect(scenario).toBeDefined();

    const cards = cardsFor("otr2", [scenario as Scenario]);
    const identities = units(cards).map((entry) => entry.identity);
    const duplicateIdentities = identities.filter(
      (identity, index) => identities.indexOf(identity) !== index,
    );

    expect(duplicateIdentities).toEqual([]);
    expect(identities).toHaveLength(114);
    expect(new Set(identities).size).toBe(114);
  });
});
