import type { Gunboat, Scenario, Unit } from "../types";
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

// Leader info including name and hex location
interface LeaderInfo {
  name: string;
  hexLocation: string;
}

// Build a map from command code to leader info
function buildLeaderMap(units: Unit[]): Record<string, LeaderInfo> {
  const leaderMap: Record<string, LeaderInfo> = {};
  for (const unit of units) {
    if (unit.type === "Ldr" && unit.command !== "-") {
      leaderMap[unit.command] = {
        name: unit.name,
        hexLocation: unit.hexLocation
      };
    }
  }
  return leaderMap;
}

// Get leader name for a unit (skip if unit is itself a leader)
// If leader shares the same hex as the unit, wrap name in brackets
function getLeaderName(unit: Unit, leaderMap: Record<string, LeaderInfo>): string | undefined {
  if (unit.type === "Ldr") return undefined;
  if (unit.command === "-") return undefined;
  const leaderInfo = leaderMap[unit.command];
  if (!leaderInfo) return undefined;
  
  // If leader is in the same hex, wrap in brackets
  if (leaderInfo.hexLocation === unit.hexLocation) {
    return `[${leaderInfo.name}]`;
  }
  return leaderInfo.name;
}

// Get army leaders with their hex locations
function getArmyLeaders(units: Unit[]): string {
  const armyLeaders = units.filter(u => u.type === "Ldr" && u.size === "Army");
  if (armyLeaders.length === 0) return "";
  return armyLeaders.map(l => `${l.name} (${l.hexLocation})`).join(", ");
}

// Get corps-level cavalry leaders (like Forrest) who need to stack with their command
function getCavLeaders(units: Unit[]): string {
  const cavLeaders = units.filter(u => 
    u.type === "Ldr" && u.size === "Corps" && u.command === "Cav"
  );
  if (cavLeaders.length === 0) return "";
  return cavLeaders.map(l => `${l.name} (${l.hexLocation})`).join(", ");
}

// Key explaining conventions shown on web but not in print
function ConventionsKey() {
  return (
    <div className="roster-sheet__key">
      <h4 className="roster-sheet__key-title">Key</h4>
      <dl className="roster-sheet__key-list">
        <div className="roster-sheet__key-item">
          <dt>[Leader Name]</dt>
          <dd>Leader starts in the same hex as this unit</dd>
        </div>
        <div className="roster-sheet__key-item">
          <dt>Leader Name</dt>
          <dd>Leader starts in a different hex</dd>
        </div>
        <div className="roster-sheet__key-item">
          <dt>Army Leader (hex)</dt>
          <dd>Army leader's starting hex shown in header</dd>
        </div>
        <div className="roster-sheet__key-item">
          <dt>Cav Leader (hex)</dt>
          <dd>Cavalry corps leader's starting hex shown in header</dd>
        </div>
        <div className="roster-sheet__key-item">
          <dt>F1, F2, etc.</dt>
          <dd>Starting fatigue level</dd>
        </div>
        <div className="roster-sheet__key-item">
          <dt>†, ‡, *, etc.</dt>
          <dd>See footnotes below each section</dd>
        </div>
      </dl>
    </div>
  );
}

// Display gunboats as a simple list
function GunboatsList({ gunboats }: { gunboats: Gunboat[] }) {
  if (gunboats.length === 0) return null;
  
  return (
    <div className="roster-sheet__gunboats">
      <h4 className="roster-sheet__gunboats-title">Gunboats</h4>
      <ul className="roster-sheet__gunboats-list">
        {gunboats.map((gunboat, index) => (
          <li key={index} className="roster-sheet__gunboat-item">
            <span className="roster-sheet__gunboat-name">{gunboat.name}</span>
            {gunboat.location && (
              <span className="roster-sheet__gunboat-location"> — {gunboat.location}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
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
  
  // Get cavalry leader summaries
  const confederateCavLeader = getCavLeaders(scenario.confederateUnits);
  const unionCavLeader = getCavLeaders(scenario.unionUnits);

  return (
    <div className="roster-sheet">
      <header className="roster-sheet__header">
        <h1 className="roster-sheet__title">{gameName}</h1>
        <h2 className="roster-sheet__scenario">
          Scenario {scenario.number}: {scenario.name}
        </h2>
        <p className="roster-sheet__length">{scenario.gameLength}</p>
        <ConventionsKey />
      </header>

      <section className="roster-sheet__section">
        <h3 className="roster-sheet__section-title">
          Confederate
          {confederateArmyLeader && <span className="roster-sheet__army-leader"> — Army Leader: {confederateArmyLeader}</span>}
          {confederateCavLeader && <span className="roster-sheet__cav-leader"> — Cav Leader: {confederateCavLeader}</span>}
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
        <GunboatsList gunboats={scenario.confederateGunboats} />
        <FootnotesLegend footnotes={scenario.confederateFootnotes} />
      </section>

      <section className="roster-sheet__section">
        <h3 className="roster-sheet__section-title">
          Union
          {unionArmyLeader && <span className="roster-sheet__army-leader"> — Army Leader: {unionArmyLeader}</span>}
          {unionCavLeader && <span className="roster-sheet__cav-leader"> — Cav Leader: {unionCavLeader}</span>}
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
        <GunboatsList gunboats={scenario.unionGunboats} />
        <FootnotesLegend footnotes={scenario.unionFootnotes} />
      </section>
    </div>
  );
}
