import type { Unit } from "../types";
import "./UnitCard.css";

interface UnitCardProps {
  unit?: Unit;
  side?: "confederate" | "union";
  empty?: boolean;
  startingFatigue?: string;
}

export function UnitCard({ unit, side, empty, startingFatigue }: UnitCardProps) {
  if (empty || !unit) {
    return (
      <div className="unit-card unit-card--empty">
        <div className="unit-card__header">
          <span className="unit-card__name">&nbsp;</span>
        </div>
        <div className="unit-card__counters">
          <div className="unit-card__counter-box" />
          <div className="unit-card__counter-box" />
          <div className="unit-card__counter-box" />
        </div>
      </div>
    );
  }

  // Extract just the hex code from locations like "S5510 (Yorktown)"
  const hexMatch = unit.hexLocation.match(/^([NS]\d{4})/);
  const hexCode = hexMatch ? hexMatch[1] : unit.hexLocation.split(" ")[0];
  
  // Format manpower display
  const mpDisplay = unit.manpowerValue !== "-" ? unit.manpowerValue : "";

  return (
    <div className={`unit-card unit-card--${side}`}>
      <div className="unit-card__header">
        <span className="unit-card__name">{unit.name}</span>
        {unit.command !== "-" && <span className="unit-card__command">{unit.command}</span>}
      </div>
      <div className="unit-card__counters">
        <div className="unit-card__counter-box" />
        <div className="unit-card__counter-box unit-card__counter-box--info">
          {mpDisplay && <span className="unit-card__mp">{mpDisplay}</span>}
          <span className="unit-card__hex">{hexCode}</span>
        </div>
        <div className="unit-card__counter-box unit-card__counter-box--info">
          {startingFatigue && <span className="unit-card__fatigue">{startingFatigue}</span>}
        </div>
      </div>
    </div>
  );
}
