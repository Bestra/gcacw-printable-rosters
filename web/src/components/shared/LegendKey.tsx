import type { Unit } from "../../types";
import { getTableAbbreviation } from "../../tableNameConfig";
import "./LegendKey.css";

// Abbreviation definitions: [pattern to match, abbreviation shown, full name]
const ABBREVIATION_DEFINITIONS: { pattern: RegExp; abbrev: string; full: string }[] = [
  { pattern: /^Inc \d$/, abbrev: "Inc 1-4", full: "Army of the Potomac Increment" },
  { pattern: /^Rich$/, abbrev: "Rich", full: "Richmond Garrison Track" },
  { pattern: /^Balt$/, abbrev: "Balt", full: "Baltimore/DC Reinforcement Track" },
  { pattern: /^PA Mil$/, abbrev: "PA Mil", full: "Pennsylvania Militia" },
  { pattern: /^WV$/, abbrev: "WV", full: "West Virginia Reinforcement Track" },
  { pattern: /^Stuart$/, abbrev: "Stuart", full: "Placed Upon Stuart's Arrival" },
  { pattern: /^Reinf$/, abbrev: "Reinf", full: "Confederate Reinforcement Track" },
];

function getAbbreviations(units: Unit[]): { abbrev: string; full: string }[] {
  const usedAbbrevs = new Set<string>();
  
  for (const unit of units) {
    const tableAbbrev = getTableAbbreviation(unit.tableName);
    if (tableAbbrev) {
      usedAbbrevs.add(tableAbbrev);
    }
    if (unit.reinforcementSet) {
      usedAbbrevs.add("Set");
    }
  }
  
  const matchedDefs: { abbrev: string; full: string }[] = [];
  const seen = new Set<string>();
  
  if (usedAbbrevs.has("Set")) {
    matchedDefs.push({ abbrev: "Set 1-4", full: "Reinforcement Set" });
    seen.add("Set 1-4");
  }
  
  for (const abbrev of usedAbbrevs) {
    for (const def of ABBREVIATION_DEFINITIONS) {
      if (def.pattern.test(abbrev) && !seen.has(def.abbrev)) {
        matchedDefs.push({ abbrev: def.abbrev, full: def.full });
        seen.add(def.abbrev);
      }
    }
  }
  
  return matchedDefs;
}

interface LegendKeyProps {
  footnotes: Record<string, string>;
  units: Unit[];
  className?: string;
}

export function LegendKey({ footnotes, units, className = "" }: LegendKeyProps) {
  const footnoteEntries = Object.entries(footnotes);
  const abbreviations = getAbbreviations(units);
  
  if (footnoteEntries.length === 0 && abbreviations.length === 0) {
    return null;
  }
  
  return (
    <div className={`legend-key ${className}`}>
      {footnoteEntries.length > 0 && (
        <div className="legend-key__section legend-key__footnotes">
          {footnoteEntries.map(([symbol, text]) => (
            <span key={symbol} className="legend-key__item">
              <span className="legend-key__symbol">{symbol}</span>
              <span className="legend-key__text">{text}</span>
            </span>
          ))}
        </div>
      )}
      
      {abbreviations.length > 0 && (
        <div className="legend-key__section legend-key__abbreviations">
          <span className="legend-key__title">Key:</span>
          {abbreviations.map(({ abbrev, full }) => (
            <span key={abbrev} className="legend-key__item">
              <span className="legend-key__abbrev">{abbrev}</span>
              <span className="legend-key__equals">=</span>
              <span className="legend-key__text">{full}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
