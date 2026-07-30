import { render, screen, within } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { ScenarioCardSheet } from "../../src/components/ScenarioCardSheet";
import type { Scenario, Unit } from "../../src/types";

function unit(overrides: Partial<Unit> = {}): Unit {
  return {
    name: "Test Unit",
    size: "Brig",
    command: "P",
    type: "Inf",
    manpowerValue: "1",
    hexLocation: "N0101",
    notes: [],
    ...overrides,
  };
}

const scenario: Scenario = {
  number: 5,
  name: "Test Scenario",
  confederateFootnotes: {},
  unionFootnotes: {},
  confederateGunboats: [],
  unionGunboats: [],
  confederateUnits: [
    unit({ name: "Leader", type: "Ldr", size: "Army" }),
    unit({ name: "Infantry" }),
    unit({ name: "Wagon", type: "Special" }),
  ],
  unionUnits: [unit({ name: "Cavalry", command: "I", type: "Cav" })],
};

describe("ScenarioCardSheet", () => {
  test("renders every combat unit once with two empty counter spaces", () => {
    const { container } = render(
      <ScenarioCardSheet
        scenario={scenario}
        gameName="Test Game"
        gameId="test"
        confederateBodyColor="#cccccc"
        unionBodyColor="#abcdef"
      />,
    );

    const cards = container.querySelectorAll(".command-card");
    expect(cards).toHaveLength(2);
    expect(screen.getByText("Infantry")).toBeInTheDocument();
    expect(screen.getByText("Cavalry")).toBeInTheDocument();
    expect(screen.queryByText("Leader")).not.toBeInTheDocument();
    expect(screen.queryByText("Wagon")).not.toBeInTheDocument();

    for (const card of cards) {
      expect(within(card as HTMLElement).getAllByLabelText(/space$/)).toHaveLength(2);
    }
  });

  test("uses fixed side flags and configurable body colors", () => {
    const { container } = render(
      <ScenarioCardSheet
        scenario={scenario}
        gameName="Test Game"
        gameId="test"
        confederateBodyColor="#cccccc"
        unionBodyColor="#abcdef"
      />,
    );

    expect(screen.getByLabelText("11-star Confederate First National flag")).toBeInTheDocument();
    expect(screen.getByLabelText("34-star United States flag")).toBeInTheDocument();
    expect(container.querySelector(".command-card--confederate")).toHaveStyle({
      "--body-color": "#cccccc",
    });
    expect(container.querySelector(".command-card--union")).toHaveStyle({
      "--body-color": "#abcdef",
    });
  });
});
