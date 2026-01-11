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

export function RosterSheet({ scenario, gameName }: RosterSheetProps) {
  const paddedConfederate = padToFillRows(scenario.confederateUnits, UNITS_PER_ROW);
  const paddedUnion = padToFillRows(scenario.unionUnits, UNITS_PER_ROW);

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
        <h3 className="roster-sheet__section-title">Confederate</h3>
        <div className="roster-sheet__units">
          {paddedConfederate.map((unit, index) => (
            <UnitCard
              key={`csa-${index}`}
              unit={unit ?? undefined}
              side="confederate"
              empty={!unit}
              startingFatigue={unit ? getStartingFatigue(unit, scenario.confederateFootnotes) : undefined}
            />
          ))}
        </div>
        <FootnotesLegend footnotes={scenario.confederateFootnotes} />
      </section>

      <section className="roster-sheet__section">
        <h3 className="roster-sheet__section-title">Union</h3>
        <div className="roster-sheet__units">
          {paddedUnion.map((unit, index) => (
            <UnitCard
              key={`usa-${index}`}
              unit={unit ?? undefined}
              side="union"
              empty={!unit}
              startingFatigue={unit ? getStartingFatigue(unit, scenario.unionFootnotes) : undefined}
            />
          ))}
        </div>
        <FootnotesLegend footnotes={scenario.unionFootnotes} />
      </section>
    </div>
  );
}
