import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { RangeCardSheet } from "../../src/components/RangeCardSheet";
import type { Scenario, Unit } from "../../src/types";

function unit(name: string, command: string): Unit {
  return {
    name,
    command,
    type: "Inf",
    size: "Brig",
    manpowerValue: "1",
    hexLocation: "N0101",
    notes: [],
  };
}

function scenario(number: number, unionUnits: Unit[]): Scenario {
  return {
    number,
    name: `Scenario ${number}`,
    confederateUnits: [],
    unionUnits,
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateGunboats: [],
    unionGunboats: [],
  };
}

describe("RangeCardSheet", () => {
  test("renders range footers, summary counts, and unit applicability labels", () => {
    const scenarios = [
      scenario(5, [unit("McCunn", "V"), unit("Stable", "I")]),
      scenario(6, [unit("McCunn", "-"), unit("Stable", "I")]),
    ];

    const { container } = render(
      <RangeCardSheet
        scenarios={scenarios}
        gameName="Test Game"
        gameId="test"
        confederateBodyColor="#cccccc"
        unionBodyColor="#abcdef"
      />,
    );

    expect(screen.getByText("2 physical units")).toBeInTheDocument();
    expect(screen.getByText("3 cards")).toBeInTheDocument();
    expect(screen.getByText("1 moving-command slot")).toBeInTheDocument();
    expect(screen.getAllByText("Scenarios 5-6")).toHaveLength(3);
    expect(screen.getByText("S5")).toBeInTheDocument();
    expect(screen.getByText("S6")).toBeInTheDocument();
    expect(screen.getByText("S5-6")).toBeInTheDocument();
    expect(container.querySelectorAll(".command-card")).toHaveLength(3);
  });
});
