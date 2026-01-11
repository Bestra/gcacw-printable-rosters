import type { Unit } from "../../types";
import { getTableAbbreviation } from "../../tableNameConfig";
import "./AbbreviationsKey.css";

// Abbreviation definitions: [pattern to match, abbreviation shown, full name]
// Pattern can match either the abbreviation output or part of the table name
const ABBREVIATION_DEFINITIONS: { pattern: RegExp; abbrev: string; full: string }[] = [
  { pattern: /^Inc \d$/, abbrev: "Inc 1-4", full: "Army of the Potomac Increment" },
  { pattern: /^Rich$/, abbrev: "Rich", full: "Richmond Garrison Track" },
  { pattern: /^Balt$/, abbrev: "Balt", full: "Baltimore/DC Reinforcement Track" },
  { pattern: /^PA Mil$/, abbrev: "PA Mil", full: "Pennsylvania Militia" },
  { pattern: /^WV$/, abbrev: "WV", full: "West Virginia Reinforcement Track" },
  { pattern: /^Stuart$/, abbrev: "Stuart", full: "Placed Upon Stuart's Arrival" },
  { pattern: /^Reinf$/, abbrev: "Reinf", full: "Confederate Reinforcement Track" },
];

interface AbbreviationsKeyProps {
  units: Unit[];
  className?: string;
}

export function AbbreviationsKey({ units, className = "" }: AbbreviationsKeyProps) {
  // Collect all abbreviations used by these units
  const usedAbbrevs = new Set<string>();
  
  for (const unit of units) {
    // Check table name abbreviation
    const tableAbbrev = getTableAbbreviation(unit.tableName);
    if (tableAbbrev) {
      usedAbbrevs.add(tableAbbrev);
    }
    
    // Check reinforcement set
    if (unit.reinforcementSet) {
      usedAbbrevs.add("Set");
    }
  }
  
  // Find which definitions match the used abbreviations
  const matchedDefs: { abbrev: string; full: string }[] = [];
  const seen = new Set<string>();
  
  // Check for reinforcement sets first
  if (usedAbbrevs.has("Set")) {
    matchedDefs.push({ abbrev: "Set 1-4", full: "Reinforcement Set" });
    seen.add("Set 1-4");
  }
  
  // Check other abbreviations
  for (const abbrev of usedAbbrevs) {
    for (const def of ABBREVIATION_DEFINITIONS) {
      if (def.pattern.test(abbrev) && !seen.has(def.abbrev)) {
        matchedDefs.push({ abbrev: def.abbrev, full: def.full });
        seen.add(def.abbrev);
      }
    }
  }
  
  if (matchedDefs.length === 0) return null;
  
  return (
    <div className={`abbreviations-key ${className}`}>
      <span className="abbreviations-key__title">Key:</span>
      {matchedDefs.map(({ abbrev, full }) => (
        <span key={abbrev} className="abbreviations-key__item">
          <span className="abbreviations-key__abbrev">{abbrev}</span>
          <span className="abbreviations-key__equals">=</span>
          <span className="abbreviations-key__full">{full}</span>
        </span>
      ))}
    </div>
  );
}
