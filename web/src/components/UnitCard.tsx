import type { Unit } from "../types";
import { parseHexLocation } from "../hexLocationConfig";
import "./UnitCard.css";

interface UnitCardProps {
  unit?: Unit;
  side?: "confederate" | "union";
  empty?: boolean;
  startingFatigue?: string;
  leaderName?: string;
}

export function UnitCard({ unit, side, empty, startingFatigue, leaderName }: UnitCardProps) {
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

  // Parse hex location using shared config
  const { hexCode, locationName } = parseHexLocation(unit.hexLocation);
  
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
          <span className="unit-card__leader">{leaderName ?? "\u00A0"}</span>
          <span className="unit-card__mp">{mpDisplay || "\u00A0"}</span>
        </div>
        <div className="unit-card__counter-box unit-card__counter-box--info">
          {startingFatigue && <span className="unit-card__fatigue">{startingFatigue}</span>}
          <div className="unit-card__setup-info">
            <span className="unit-card__hex">{hexCode}</span>
            {locationName && <span className="unit-card__location">{locationName}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
