import { describe, test, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { RosterSheet } from "../../src/components/RosterSheet";
import type { Scenario, Unit, Gunboat } from "../../src/types";

// Helper to create a minimal unit fixture
function createUnit(overrides: Partial<Unit> = {}): Unit {
  return {
    name: "Test Unit",
    size: "Brig",
    command: "1",
    type: "Inf",
    manpowerValue: "5",
    hexLocation: "A1010",
    notes: [],
    ...overrides,
  };
}

// Helper to create a leader unit
function createLeader(overrides: Partial<Unit> = {}): Unit {
  return createUnit({
    name: "Test Leader",
    size: "Div",
    type: "Ldr",
    manpowerValue: "-",
    ...overrides,
  });
}

// Helper to create a minimal scenario fixture
function createScenario(overrides: Partial<Scenario> = {}): Scenario {
  return {
    number: 1,
    name: "Test Scenario",
    confederateUnits: [],
    unionUnits: [],
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateGunboats: [],
    unionGunboats: [],
    ...overrides,
  };
}

describe("RosterSheet", () => {
  describe("Unit rendering", () => {
    test("renders correct number of Confederate units", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({ name: "1st Texas", command: "1" }),
          createUnit({ name: "2nd Texas", command: "1" }),
          createUnit({ name: "3rd Texas", command: "1" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Each unit name should appear once
      expect(screen.getByText("1st Texas")).toBeInTheDocument();
      expect(screen.getByText("2nd Texas")).toBeInTheDocument();
      expect(screen.getByText("3rd Texas")).toBeInTheDocument();
    });

    test("renders correct number of Union units", () => {
      const scenario = createScenario({
        unionUnits: [
          createUnit({ name: "1st Maine", command: "I" }),
          createUnit({ name: "2nd Maine", command: "I" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("1st Maine")).toBeInTheDocument();
      expect(screen.getByText("2nd Maine")).toBeInTheDocument();
    });

    test("renders units from both sides", () => {
      const scenario = createScenario({
        confederateUnits: [createUnit({ name: "1st Virginia", command: "1" })],
        unionUnits: [createUnit({ name: "1st New York", command: "I" })],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("1st Virginia")).toBeInTheDocument();
      expect(screen.getByText("1st New York")).toBeInTheDocument();
    });
  });

  describe("Footnote symbols", () => {
    test("footnote symbol appears on unit with note", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({ name: "Fatigued Unit", command: "1", notes: ["*"] }),
        ],
        confederateFootnotes: { "*": "Starts fatigued" },
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // The unit should show the footnote symbol
      const notesElements = screen.getAllByText("*");
      expect(notesElements.length).toBeGreaterThanOrEqual(1);
    });

    test("multiple footnote symbols appear on unit with multiple notes", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Multi-note Unit",
            command: "1",
            notes: ["*", "†"],
          }),
        ],
        confederateFootnotes: {
          "*": "Note one",
          "†": "Note two",
        },
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Unit should show combined symbols
      expect(screen.getByText("*†")).toBeInTheDocument();
    });
  });

  describe("Footnote legend", () => {
    test("footnote definitions appear in legend", () => {
      const scenario = createScenario({
        confederateUnits: [createUnit({ name: "Test Unit", command: "1" })],
        confederateFootnotes: {
          "*": "Starts with Fatigue Level 1",
          "†": "Deploy anywhere in hex",
        },
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("Starts with Fatigue Level 1")).toBeInTheDocument();
      expect(screen.getByText("Deploy anywhere in hex")).toBeInTheDocument();
    });

    test("legend does not render when no footnotes exist", () => {
      const scenario = createScenario({
        confederateUnits: [createUnit({ name: "Test Unit", command: "1" })],
        confederateFootnotes: {},
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // No legend-key section should exist for confederate side
      const confederateSection = screen.getByText("Confederate").closest("section");
      expect(confederateSection).not.toContainHTML("legend-key__footnotes");
    });
  });

  describe("Leaders", () => {
    test("leader renders in group header", () => {
      const scenario = createScenario({
        confederateUnits: [
          createLeader({ name: "Longstreet", command: "1", size: "Corps" }),
          createUnit({ name: "1st Texas", command: "1" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Leader should appear in a leader-header element
      const leaderHeaders = document.querySelectorAll(".leader-header");
      expect(leaderHeaders.length).toBeGreaterThanOrEqual(1);
      
      // Longstreet's name should appear
      expect(screen.getByText("Longstreet")).toBeInTheDocument();
    });

    test("army leader renders in army header section", () => {
      const scenario = createScenario({
        confederateUnits: [
          createLeader({ name: "Lee", command: "ANV", size: "Army" }),
          createUnit({ name: "1st Texas", command: "1" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Army leader should appear in the army header
      const armyHeader = document.querySelector(".army-header");
      expect(armyHeader).toBeInTheDocument();
      expect(within(armyHeader as HTMLElement).getByText("Lee")).toBeInTheDocument();
    });

    test("leaders are excluded from unit grid (rendered in headers only)", () => {
      const scenario = createScenario({
        confederateUnits: [
          createLeader({ name: "Jackson", command: "2", size: "Corps" }),
          createUnit({ name: "1st Virginia", command: "2" }),
          createUnit({ name: "2nd Virginia", command: "2" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // The leader should appear in a leader-header, not in unit-row elements
      const unitRows = document.querySelectorAll(".unit-row");
      
      // Should have 2 unit rows (for the infantry units), not 3
      expect(unitRows.length).toBe(2);
      
      // Jackson should still be visible (in leader header)
      expect(screen.getByText("Jackson")).toBeInTheDocument();
    });
  });

  describe("Gunboats", () => {
    test("gunboats render in separate section", () => {
      const scenario = createScenario({
        unionUnits: [createUnit({ name: "1st Maine", command: "I" })],
        unionGunboats: [
          { name: "USS Monitor", location: "James River" },
          { name: "USS Galena", location: "York River" },
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Gunboats section should have a title
      expect(screen.getByText("Gunboats")).toBeInTheDocument();
      
      // Each gunboat should appear
      expect(screen.getByText("USS Monitor")).toBeInTheDocument();
      expect(screen.getByText("USS Galena")).toBeInTheDocument();
    });

    test("gunboat locations are displayed", () => {
      const scenario = createScenario({
        unionGunboats: [{ name: "USS Monitor", location: "James River" }],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText(/James River/)).toBeInTheDocument();
    });

    test("gunboats section does not render when no gunboats exist", () => {
      const scenario = createScenario({
        unionUnits: [createUnit({ name: "1st Maine", command: "I" })],
        unionGunboats: [],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.queryByText("Gunboats")).not.toBeInTheDocument();
    });
  });

  describe("Scenario header", () => {
    test("renders game name and scenario info", () => {
      const scenario = createScenario({
        number: 3,
        name: "Battle of Gettysburg",
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Gettysburg: The Turning Point"
          showImages={false}
          variant="flow"
        />
      );

      expect(
        screen.getByText(/Gettysburg: The Turning Point/)
      ).toBeInTheDocument();
      expect(screen.getByText(/Scenario 3/)).toBeInTheDocument();
      expect(screen.getByText(/Battle of Gettysburg/)).toBeInTheDocument();
    });
  });

  describe("Starting fatigue", () => {
    test("fatigue level is extracted from footnote and displayed", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Tired Unit",
            command: "1",
            notes: ["*"],
          }),
        ],
        confederateFootnotes: {
          "*": "Starts with Fatigue Level 2",
        },
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Should show F2 for fatigue level 2
      expect(screen.getByText("F2")).toBeInTheDocument();
    });
  });

  describe("Hex locations", () => {
    test("hex code is displayed for units", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Test Unit",
            command: "1",
            hexLocation: "S5510",
          }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("S5510")).toBeInTheDocument();
    });

    test("location name is extracted from hex parenthetical", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Test Unit",
            command: "1",
            hexLocation: "S5510 (Yorktown)",
          }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("S5510")).toBeInTheDocument();
      expect(screen.getByText("(Yorktown)")).toBeInTheDocument();
    });
  });

  describe("Manpower values", () => {
    test("manpower value is displayed for units", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Strong Unit",
            command: "1",
            manpowerValue: "12",
          }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      expect(screen.getByText("12")).toBeInTheDocument();
    });

    test("dash manpower value is not displayed", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({
            name: "Leader Unit",
            command: "1",
            manpowerValue: "-",
          }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // The mp element should exist but not show "-"
      const unitRow = document.querySelector(".unit-row");
      const mpElement = unitRow?.querySelector(".mp");
      expect(mpElement?.textContent?.trim()).toBe("");
    });
  });

  describe("Variant rendering", () => {
    test("flow variant applies correct class", () => {
      const scenario = createScenario({
        confederateUnits: [createUnit({ name: "Test Unit", command: "1" })],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      const rosterSheet = document.querySelector(".roster-sheet");
      expect(rosterSheet).toHaveClass("flow");
    });

    test("hierarchical variant applies correct class", () => {
      const scenario = createScenario({
        confederateUnits: [createUnit({ name: "Test Unit", command: "1" })],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="hierarchical"
        />
      );

      const rosterSheet = document.querySelector(".roster-sheet");
      expect(rosterSheet).toHaveClass("hierarchical");
    });
  });

  describe("Unit sorting", () => {
    test("cavalry units appear after infantry units", () => {
      const scenario = createScenario({
        confederateUnits: [
          createLeader({ name: "Stuart", command: "Cav", size: "Corps" }),
          createUnit({ name: "Cavalry Brigade", command: "Cav", type: "Cav" }),
          createLeader({ name: "Longstreet", command: "1", size: "Corps" }),
          createUnit({ name: "Infantry Brigade", command: "1", type: "Inf" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Get all command groups
      const commandGroups = document.querySelectorAll(".command-group");
      const groupTitles = Array.from(commandGroups).map(
        (group) => group.querySelector(".group-title")?.textContent || ""
      );

      // Infantry (command "1") should come before Cavalry (command "Cav")
      const infIndex = groupTitles.findIndex((title) => title.includes("1 —"));
      const cavIndex = groupTitles.findIndex((title) => title.includes("Cav —"));
      
      expect(infIndex).toBeGreaterThanOrEqual(0);
      expect(cavIndex).toBeGreaterThanOrEqual(0);
      expect(infIndex).toBeLessThan(cavIndex);
    });

    test("units with leaders appear before units without leaders", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({ name: "Independent Unit", command: "Ind", type: "Inf" }),
          createLeader({ name: "Longstreet", command: "1", size: "Corps" }),
          createUnit({ name: "Led Unit", command: "1", type: "Inf" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Get all command groups
      const commandGroups = document.querySelectorAll(".command-group");
      const groupTitles = Array.from(commandGroups).map(
        (group) => group.querySelector(".group-title")?.textContent || ""
      );

      // Group with leader (command "1") should come before group without leader (command "Ind")
      const ledIndex = groupTitles.findIndex((title) => title.includes("1 —"));
      const unleadedIndex = groupTitles.findIndex((title) => title.includes("Ind"));
      
      expect(ledIndex).toBeGreaterThanOrEqual(0);
      expect(unleadedIndex).toBeGreaterThanOrEqual(0);
      expect(ledIndex).toBeLessThan(unleadedIndex);
    });

    test("cavalry without leaders still appear at the end", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({ name: "Independent Cavalry", command: "CavInd", type: "Cav" }),
          createUnit({ name: "Independent Infantry", command: "InfInd", type: "Inf" }),
          createLeader({ name: "Longstreet", command: "1", size: "Corps" }),
          createUnit({ name: "Led Infantry", command: "1", type: "Inf" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Get all command groups
      const commandGroups = document.querySelectorAll(".command-group");
      const groupTitles = Array.from(commandGroups).map(
        (group) => group.querySelector(".group-title")?.textContent || ""
      );

      // Infantry groups should come before cavalry groups, regardless of leader status
      const ledInfIndex = groupTitles.findIndex((title) => title.includes("1 —"));
      const unleadedInfIndex = groupTitles.findIndex((title) => title.includes("InfInd"));
      const unleadedCavIndex = groupTitles.findIndex((title) => title.includes("CavInd"));
      
      expect(ledInfIndex).toBeGreaterThanOrEqual(0);
      expect(unleadedInfIndex).toBeGreaterThanOrEqual(0);
      expect(unleadedCavIndex).toBeGreaterThanOrEqual(0);
      
      // Both infantry groups should come before cavalry
      expect(ledInfIndex).toBeLessThan(unleadedCavIndex);
      expect(unleadedInfIndex).toBeLessThan(unleadedCavIndex);
    });

    test("led infantry comes first, then led cavalry, then unleaded infantry, then unleaded cavalry", () => {
      const scenario = createScenario({
        confederateUnits: [
          createUnit({ name: "Independent Cavalry", command: "CavInd", type: "Cav" }),
          createLeader({ name: "Stuart", command: "Cav", size: "Corps" }),
          createUnit({ name: "Led Cavalry", command: "Cav", type: "Cav" }),
          createUnit({ name: "Independent Infantry", command: "InfInd", type: "Inf" }),
          createLeader({ name: "Longstreet", command: "1", size: "Corps" }),
          createUnit({ name: "Led Infantry", command: "1", type: "Inf" }),
        ],
      });

      render(
        <RosterSheet
          scenario={scenario}
          gameName="Test Game"
          showImages={false}
          variant="flow"
        />
      );

      // Get all command groups
      const commandGroups = document.querySelectorAll(".command-group");
      const groupTitles = Array.from(commandGroups).map(
        (group) => group.querySelector(".group-title")?.textContent || ""
      );

      const ledInfIndex = groupTitles.findIndex((title) => title.includes("1 —"));
      const unleadedInfIndex = groupTitles.findIndex((title) => title.includes("InfInd"));
      const ledCavIndex = groupTitles.findIndex((title) => title.includes("Cav —"));
      const unleadedCavIndex = groupTitles.findIndex((title) => title.includes("CavInd"));
      
      expect(ledInfIndex).toBeGreaterThanOrEqual(0);
      expect(unleadedInfIndex).toBeGreaterThanOrEqual(0);
      expect(ledCavIndex).toBeGreaterThanOrEqual(0);
      expect(unleadedCavIndex).toBeGreaterThanOrEqual(0);
      
      // Order should be: led infantry < led cavalry < unleaded infantry < unleaded cavalry
      // (leader presence is primary sort, then cavalry status within each)
      expect(ledInfIndex).toBeLessThan(ledCavIndex);
      expect(ledCavIndex).toBeLessThan(unleadedInfIndex);
      expect(unleadedInfIndex).toBeLessThan(unleadedCavIndex);
    });
  });
});
