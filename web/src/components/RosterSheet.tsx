import type { Scenario, Unit } from "../types";
import { UnitCard } from "./UnitCard";
import "./RosterSheet.css";

interface RosterSheetProps {
  scenario: Scenario;
  gameName: string;
}

// Determine starting fatigue from footnotes - looks for "Fatigue Level X" pattern
function getStartingFatigue(unit: Unit, footnotes: Record<string, string>): string | undefined {
  for (const note of unit.notes) {
    const footnoteText = footnotes[note];
    if (footnoteText) {
      const fatigueMatch = footnoteText.match(/Fatigue Level (\d)/i);
      if (fatigueMatch) {
        return `F${fatigueMatch[1]}`;
      }
    }
  }
  return undefined;
}

// Calculate how many units fit per row (approximately 4 cards across letter page)
const UNITS_PER_ROW = 4;

// Pad array to fill rows completely
function padToFillRows<T>(items: T[], unitsPerRow: number): (T | null)[] {
  const remainder = items.length % unitsPerRow;
  if (remainder === 0) return items;
  const padding = unitsPerRow - remainder;
  return [...items, ...Array(padding).fill(null)];
}

// Render footnotes legend
function FootnotesLegend({ footnotes }: { footnotes: Record<string, string> }) {
  const entries = Object.entries(footnotes);
  if (entries.length === 0) return null;
  
  return (
    <div className="roster-sheet__footnotes">
      {entries.map(([symbol, text]) => (
        <div key={symbol} className="roster-sheet__footnote">
          <span className="roster-sheet__footnote-symbol">{symbol}</span>
          <span className="roster-sheet__footnote-text">{text}</span>
        </div>
      ))}
    </div>
  );
}

// Build a map from command code to leader name
function buildLeaderMap(units: Unit[]): Record<string, string> {
  const leaderMap: Record<string, string> = {};
  for (const unit of units) {
    if (unit.type === "Ldr" && unit.command !== "-") {
      leaderMap[unit.command] = unit.name;
    }
  }
  return leaderMap;
}

// Get leader name for a unit (skip if unit is itself a leader)
function getLeaderName(unit: Unit, leaderMap: Record<string, string>): string | undefined {
  if (unit.type === "Ldr") return undefined;
  if (unit.command === "-") return undefined;
  return leaderMap[unit.command];
}

// Get army leaders only
function getArmyLeaders(units: Unit[]): string {
  const armyLeaders = units.filter(u => u.type === "Ldr" && u.size === "Army");
  if (armyLeaders.length === 0) return "";
  return armyLeaders.map(l => l.name).join(", ");
}

export function RosterSheet({ scenario, gameName }: RosterSheetProps) {
  // Filter out leaders from unit cards
  const combatUnits = (units: Unit[]) => units.filter(u => u.type !== "Ldr");
  
  const confederateCombatUnits = combatUnits(scenario.confederateUnits);
  const unionCombatUnits = combatUnits(scenario.unionUnits);
  
  const paddedConfederate = padToFillRows(confederateCombatUnits, UNITS_PER_ROW);
  const paddedUnion = padToFillRows(unionCombatUnits, UNITS_PER_ROW);
  
  // Build leader maps for each side (still need all units for this)
  const confederateLeaders = buildLeaderMap(scenario.confederateUnits);
  const unionLeaders = buildLeaderMap(scenario.unionUnits);
  
  // Get army leader summaries
  const confederateArmyLeader = getArmyLeaders(scenario.confederateUnits);
  const unionArmyLeader = getArmyLeaders(scenario.unionUnits);

  return (
    <div className="roster-sheet">
      <header className="roster-sheet__header">
        <h1 className="roster-sheet__title">{gameName}</h1>
        <h2 className="roster-sheet__scenario">
          Scenario {scenario.number}: {scenario.name}
        </h2>
        <p className="roster-sheet__length">{scenario.gameLength}</p>
      </header>

      <section className="roster-sheet__section">
        <h3 className="roster-sheet__section-title">
          Confederate
          {confederateArmyLeader && <span className="roster-sheet__army-leader"> — Army Leader: {confederateArmyLeader}</span>}
        </h3>
        <div className="roster-sheet__units">
          {paddedConfederate.map((unit, index) => (
            <UnitCard
              key={`csa-${index}`}
              unit={unit ?? undefined}
              side="confederate"
              empty={!unit}
              startingFatigue={unit ? getStartingFatigue(unit, scenario.confederateFootnotes) : undefined}
              leaderName={unit ? getLeaderName(unit, confederateLeaders) : undefined}
            />
          ))}
        </div>
        <FootnotesLegend footnotes={scenario.confederateFootnotes} />
      </section>

      <section className="roster-sheet__section">
        <h3 className="roster-sheet__section-title">
          Union
          {unionArmyLeader && <span className="roster-sheet__army-leader"> — Army Leader: {unionArmyLeader}</span>}
        </h3>
        <div className="roster-sheet__units">
          {paddedUnion.map((unit, index) => (
            <UnitCard
              key={`usa-${index}`}
              unit={unit ?? undefined}
              side="union"
              empty={!unit}
              startingFatigue={unit ? getStartingFatigue(unit, scenario.unionFootnotes) : undefined}
              leaderName={unit ? getLeaderName(unit, unionLeaders) : undefined}
            />
          ))}
        </div>
        <FootnotesLegend footnotes={scenario.unionFootnotes} />
      </section>
    </div>
  );
}
