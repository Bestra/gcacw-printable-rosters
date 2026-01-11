import type { Unit } from "../types";
import { parseHexLocation } from "../hexLocationConfig";
import { getTableAbbreviation } from "../tableNameConfig";
import { getUnitImage } from "../data/imageMap";
import "./UnitCard.css";

interface UnitCardProps {
  unit?: Unit;
  side?: "confederate" | "union";
  empty?: boolean;
  startingFatigue?: string;
  leaderName?: string;
  gameId?: string;
}

export function UnitCard({ unit, side, empty, startingFatigue, leaderName, gameId }: UnitCardProps) {
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
  
  // Get table abbreviation (null for default setup tables)
  const tableAbbrev = getTableAbbreviation(unit.tableName);
  
  // Format manpower display
  const mpDisplay = unit.manpowerValue !== "-" ? unit.manpowerValue : "";
  
  // Look up unit counter image
  const imageFilename = gameId && side ? getUnitImage(gameId, side, unit.name) : undefined;
  const imagePath = imageFilename ? `${import.meta.env.BASE_URL}images/counters/${gameId}/${imageFilename}` : undefined;

  return (
    <div className={`unit-card unit-card--${side}`}>
      <div className="unit-card__header">
        <span className="unit-card__name">{unit.name}</span>
        {unit.command !== "-" && <span className="unit-card__command">{unit.command}</span>}
      </div>
      <div className="unit-card__counters">
        <div className="unit-card__counter-box unit-card__counter-box--counter">
          {imagePath ? (
            <img 
              src={imagePath} 
              alt={unit.name} 
              className="unit-card__counter-image"
            />
          ) : (
            <span className="unit-card__counter-text">{unit.name}</span>
          )}
        </div>
        <div className="unit-card__counter-box unit-card__counter-box--info">
          <span className="unit-card__leader">{leaderName ?? "\u00A0"}</span>
          <span className="unit-card__mp">{mpDisplay || "\u00A0"}</span>
        </div>
        <div className="unit-card__counter-box unit-card__counter-box--info">
          {startingFatigue && <span className="unit-card__fatigue">{startingFatigue}</span>}
          <div className="unit-card__setup-info">
            <span className="unit-card__hex">{hexCode}</span>
            {locationName && <span className="unit-card__location">{locationName}</span>}
            {tableAbbrev && <span className="unit-card__table">{tableAbbrev}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
