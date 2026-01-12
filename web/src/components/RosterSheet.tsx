import type { Scenario, Unit } from "../types";
import { parseHexLocation } from "../hexLocationConfig";
import { getTableAbbreviation } from "../tableNameConfig";
import {
  type CommandGroup,
  getStartingFatigue,
  getNoteSymbols,
  getArmyLeader,
  buildCommandHierarchy,
  splitLargeGroups,
} from "../utils/rosterUtils";
import { getUnitImage, getCounterType } from "../data/imageMap";
import { RosterProvider, useRoster } from "../context/RosterContext";
import { GunboatsList } from "./shared/GunboatsList";
import { LegendKey } from "./shared/LegendKey";
import "./RosterSheet.css";

export type RosterVariant = "flow" | "hierarchical";

interface RosterSheetProps {
  scenario: Scenario;
  gameName: string;
  gameId?: string;
  showImages: boolean;
  variant: RosterVariant;
}

// Maximum units per column before splitting into multiple columns
const MAX_UNITS_PER_COLUMN = 6;

// Compact unit row
function UnitRow({ 
  unit, 
  footnotes,
}: { 
  unit: Unit;
  footnotes: Record<string, string>;
}) {
  const { gameId, side, showImages } = useRoster();
  const { hexCode, locationName } = parseHexLocation(unit.hexLocation);
  const fatigue = getStartingFatigue(unit, footnotes);
  const notes = getNoteSymbols(unit);
  const mpDisplay = unit.manpowerValue !== "-" ? unit.manpowerValue : "";
  const tableAbbrev = getTableAbbreviation(unit.tableName);
  
  // Look up unit counter image
  const imageFilename = gameId && showImages ? getUnitImage(gameId, side, unit.name) : undefined;
  const imagePath = imageFilename ? `${import.meta.env.BASE_URL}images/counters/${gameId}/${imageFilename}` : undefined;
  
  // Check if this game uses template counters (needs HTML text overlay)
  const counterType = gameId ? getCounterType(gameId) : 'individual';
  const needsTextOverlay = counterType === 'template' && imagePath;
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !unit.reinforcementSet || !unit.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="unit-row">
      <div className="setup-info">
        {showHexLocation && (
          <>
            <span className="hex">{hexCode}</span>
            {locationName && <span className="location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="table-abbrev">{tableAbbrev}</span>}
        {unit.reinforcementSet && (
          <span className="reinforcement">Set {unit.reinforcementSet}</span>
        )}
      </div>
      <div className="counter-boxes">
        {/* Box 1: Unit counter image or name */}
        <div className={`counter-box name-box${imagePath ? ' has-image' : ''}`}>
          {imagePath ? (
            needsTextOverlay ? (
              <div className="counter-composite">
                <img src={imagePath} alt={unit.name} className="counter-image" />
                <span className="counter-overlay">{unit.name}</span>
              </div>
            ) : (
              <img src={imagePath} alt={unit.name} className="counter-image" />
            )
          ) : (
            <span className="name">{unit.name}</span>
          )}
        </div>
        {/* Box 2: Annotations/Fortification */}
        <div className="counter-box annotations-box">
          {notes && <span className="notes">{notes}</span>}
        </div>
        {/* Box 3: Manpower */}
        <div className="counter-box info-box">
          <span className="mp">{mpDisplay || "\u00A0"}</span>
        </div>
        {/* Box 4: Fatigue */}
        <div className="counter-box info-box">
          {fatigue && <span className="fatigue">{fatigue}</span>}
        </div>
      </div>
    </div>
  );
}

// Leader header for command group
function LeaderHeader({ 
  leader, 
  footnotes,
}: { 
  leader: Unit;
  footnotes: Record<string, string>;
}) {
  const { gameId, side, showImages } = useRoster();
  const { hexCode, locationName } = parseHexLocation(leader.hexLocation);
  const fatigue = getStartingFatigue(leader, footnotes);
  const notes = getNoteSymbols(leader);
  const tableAbbrev = getTableAbbreviation(leader.tableName);
  
  // Look up leader counter image
  const imageFilename = gameId && showImages ? getUnitImage(gameId, side, leader.name) : undefined;
  const imagePath = imageFilename ? `${import.meta.env.BASE_URL}images/counters/${gameId}/${imageFilename}` : undefined;
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !leader.reinforcementSet || !leader.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="leader-header">
      <div className="leader-counter">
        <div className={`counter-box${imagePath ? ' has-image' : ''}`}>
          {imagePath ? (
            <img src={imagePath} alt={leader.name} className="counter-image" />
          ) : (
            <span className="name">{leader.name}</span>
          )}
        </div>
        {notes && (
          <div className="annotations-box">
            <span className="notes">{notes}</span>
          </div>
        )}
      </div>
      <div className="setup-info">
        {showHexLocation && (
          <>
            <span className="hex">{hexCode}</span>
            {locationName && <span className="location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="table-abbrev">{tableAbbrev}</span>}
        {leader.reinforcementSet && (
          <span className="reinforcement">Set {leader.reinforcementSet}</span>
        )}
        {fatigue && <span className="fatigue">{fatigue}</span>}
      </div>
    </div>
  );
}

// Command group section
function CommandGroupSection({ 
  group, 
  footnotes,
  isSubgroup = false,
}: { 
  group: CommandGroup;
  footnotes: Record<string, string>;
  isSubgroup?: boolean;
}) {
  const { side } = useRoster();
  const hasSubgroups = group.subgroups.length > 0;
  const isContinuation = group.columnIndex && group.columnIndex > 1;
  
  // Build the title with continuation indicator if needed
  let titleText = group.displayName;
  if (isContinuation) {
    titleText = `${group.displayName} (cont.)`;
  }
  
  const groupClasses = [
    "command-group",
    side,
    isSubgroup ? "subgroup" : "",
    hasSubgroups ? "has-subgroups" : "",
  ].filter(Boolean).join(" ");
  
  return (
    <div className={groupClasses}>
      <h4 className={`group-title${isSubgroup ? ' subgroup-title' : ''}`}>
        {titleText}
        {group.size && !isContinuation && <span className="group-size"> ({group.size})</span>}
      </h4>
      
      {group.leader && (
        <LeaderHeader leader={group.leader} footnotes={footnotes} />
      )}
      
      {/* Direct units for this command */}
      {group.units.length > 0 && (
        <div className="units-list">
          {group.units.map((unit, idx) => (
            <UnitRow 
              key={`${unit.name}-${idx}`}
              unit={unit}
              footnotes={footnotes}
            />
          ))}
        </div>
      )}
      
      {/* Subgroups (e.g., Divisions under a Corps) */}
      {group.subgroups.length > 0 && (
        <div className="subgroups">
          {group.subgroups.map((subgroup, idx) => (
            <CommandGroupSection
              key={`${subgroup.commandCode}-${idx}`}
              group={subgroup}
              footnotes={footnotes}
              isSubgroup={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Army side section
function ArmySection({
  title,
  units,
  footnotes,
  gunboats,
  side,
  gameId,
  showImages,
  variant,
}: {
  title: string;
  units: Unit[];
  footnotes: Record<string, string>;
  gunboats: import("../types").Gunboat[];
  side: "confederate" | "union";
  gameId?: string;
  showImages: boolean;
  variant: RosterVariant;
}) {
  const armyLeader = getArmyLeader(units);
  const hierarchy = buildCommandHierarchy(units);
  
  // Split large groups into multiple columns
  const splitGroups = splitLargeGroups(hierarchy, MAX_UNITS_PER_COLUMN);
  
  // For hierarchical variant, separate nested from flat groups
  const nestedGroups = variant === "hierarchical" 
    ? splitGroups.filter(g => g.subgroups.length > 0) 
    : [];
  const flatGroups = variant === "hierarchical"
    ? splitGroups.filter(g => g.subgroups.length === 0)
    : splitGroups;
  
  return (
    <RosterProvider gameId={gameId} side={side} showImages={showImages}>
      <section className={`army-section ${side}`}>
        <div className="army-header">
          <h3 className="army-title">{title}</h3>
          {armyLeader && (
            <LeaderHeader leader={armyLeader} footnotes={footnotes} />
          )}
        </div>
        
        {/* Groups container - uses CSS columns (flow) or grid (hierarchical) */}
        {flatGroups.length > 0 && (
          <div className="groups-container">
            {flatGroups.map((group, idx) => (
              <CommandGroupSection 
                key={`${group.commandCode}-${group.columnIndex || 0}-${idx}`}
                group={group}
                footnotes={footnotes}
              />
            ))}
          </div>
        )}
        
        {/* Nested groups rendered separately for hierarchical variant */}
        {nestedGroups.map((group, idx) => (
          <CommandGroupSection 
            key={`${group.commandCode}-${group.columnIndex || 0}-${idx}`}
            group={group}
            footnotes={footnotes}
          />
        ))}
        
        <GunboatsList gunboats={gunboats} />
        <LegendKey footnotes={footnotes} units={units} />
      </section>
    </RosterProvider>
  );
}

export function RosterSheet({ scenario, gameName, gameId, showImages, variant }: RosterSheetProps) {
  return (
    <div className={`roster-sheet ${variant}`}>
      <header className="roster-header">
        {gameName} — Scenario {scenario.number}: {scenario.name}
      </header>
      
      <div className="armies">
        <ArmySection
          title="Confederate"
          units={scenario.confederateUnits}
          footnotes={scenario.confederateFootnotes}
          gunboats={scenario.confederateGunboats}
          side="confederate"
          gameId={gameId}
          showImages={showImages}
          variant={variant}
        />
        
        <ArmySection
          title="Union"
          units={scenario.unionUnits}
          footnotes={scenario.unionFootnotes}
          gunboats={scenario.unionGunboats}
          side="union"
          gameId={gameId}
          showImages={showImages}
          variant={variant}
        />
      </div>
    </div>
  );
}
