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
import { getUnitImage } from "../data/imageMap";
import { FootnotesLegend } from "./shared/FootnotesLegend";
import { GunboatsList } from "./shared/GunboatsList";
import "./HierarchicalRosterSheet.css";

interface HierarchicalRosterSheetProps {
  scenario: Scenario;
  gameName: string;
  gameId?: string;
}

// Maximum units per column before splitting into multiple columns
const MAX_UNITS_PER_COLUMN = 8;

// Compact unit row for hierarchical display
function UnitRow({ 
  unit, 
  footnotes,
  leaderName,
  gameId,
  side,
}: { 
  unit: Unit;
  footnotes: Record<string, string>;
  leaderName?: string;
  gameId?: string;
  side?: "confederate" | "union";
}) {
  const { hexCode, locationName } = parseHexLocation(unit.hexLocation);
  const fatigue = getStartingFatigue(unit, footnotes);
  const notes = getNoteSymbols(unit);
  const mpDisplay = unit.manpowerValue !== "-" ? unit.manpowerValue : "";
  const tableAbbrev = getTableAbbreviation(unit.tableName);
  
  // Look up unit counter image
  const imageFilename = gameId && side ? getUnitImage(gameId, side, unit.name) : undefined;
  const imagePath = imageFilename ? `${import.meta.env.BASE_URL}images/counters/${gameId}/${imageFilename}` : undefined;
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !unit.reinforcementSet || !unit.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="hier-unit-row">
      <div className="hier-unit-row__setup">
        {showHexLocation && (
          <>
            <span className="hier-unit-row__hex">{hexCode}</span>
            {locationName && <span className="hier-unit-row__location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="hier-unit-row__table">{tableAbbrev}</span>}
        {unit.reinforcementSet && (
          <span className="hier-unit-row__reinforcement">Reinf Set {unit.reinforcementSet}</span>
        )}
        {leaderName && <span className="hier-unit-row__leader">{leaderName}</span>}
      </div>
      <div className="hier-unit-row__counters">
        {/* Box 1: Unit counter image or name */}
        <div className={`hier-unit-row__counter-box hier-unit-row__counter-box--name${imagePath ? ' hier-unit-row__counter-box--has-image' : ''}`}>
          {imagePath ? (
            <img 
              src={imagePath} 
              alt={unit.name} 
              className="hier-unit-row__counter-image"
            />
          ) : (
            <span className="hier-unit-row__name">{unit.name}</span>
          )}
          {notes && <span className="hier-unit-row__notes">{notes}</span>}
        </div>
        {/* Box 2: Fortification */}
        <div className="hier-unit-row__counter-box" />
        {/* Box 3: Manpower */}
        <div className="hier-unit-row__counter-box hier-unit-row__counter-box--info">
          <span className="hier-unit-row__mp">{mpDisplay || "\u00A0"}</span>
        </div>
        {/* Box 4: Fatigue */}
        <div className="hier-unit-row__counter-box hier-unit-row__counter-box--info">
          {fatigue && <span className="hier-unit-row__fatigue">{fatigue}</span>}
        </div>
      </div>
    </div>
  );
}

// Leader header for command group
function LeaderHeader({ 
  leader, 
  footnotes,
  gameId,
  side,
}: { 
  leader: Unit;
  footnotes: Record<string, string>;
  gameId?: string;
  side?: "confederate" | "union";
}) {
  const { hexCode, locationName } = parseHexLocation(leader.hexLocation);
  const fatigue = getStartingFatigue(leader, footnotes);
  const notes = getNoteSymbols(leader);
  const tableAbbrev = getTableAbbreviation(leader.tableName);
  
  // Look up leader counter image
  const imageFilename = gameId && side ? getUnitImage(gameId, side, leader.name) : undefined;
  const imagePath = imageFilename ? `${import.meta.env.BASE_URL}images/counters/${gameId}/${imageFilename}` : undefined;
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !leader.reinforcementSet || !leader.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="hier-leader-header">
      <div className="hier-leader-header__counter">
        <div className={`hier-leader-header__counter-box${imagePath ? ' hier-leader-header__counter-box--has-image' : ''}`}>
          {imagePath ? (
            <img 
              src={imagePath} 
              alt={leader.name} 
              className="hier-leader-header__counter-image"
            />
          ) : (
            <span className="hier-leader-header__name">{leader.name}</span>
          )}
          {notes && <span className="hier-leader-header__notes">{notes}</span>}
        </div>
      </div>
      <div className="hier-leader-header__setup">
        {showHexLocation && (
          <>
            <span className="hier-leader-header__hex">{hexCode}</span>
            {locationName && <span className="hier-leader-header__location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="hier-leader-header__table">{tableAbbrev}</span>}
        {leader.reinforcementSet && (
          <span className="hier-leader-header__reinforcement">Reinf Set {leader.reinforcementSet}</span>
        )}
        {fatigue && <span className="hier-leader-header__fatigue">{fatigue}</span>}
      </div>
    </div>
  );
}

// Command group section
function CommandGroupSection({ 
  group, 
  footnotes,
  side,
  gameId,
  isSubgroup = false,
}: { 
  group: CommandGroup;
  footnotes: Record<string, string>;
  side: "confederate" | "union";
  gameId?: string;
  isSubgroup?: boolean;
}) {
  const hasSubgroups = group.subgroups.length > 0;
  const isContinuation = group.columnIndex && group.columnIndex > 1;
  
  // Build the title with continuation indicator if needed
  let titleText = group.displayName;
  if (isContinuation) {
    titleText = `${group.displayName} (cont.)`;
  }
  
  return (
    <div className={`hier-command-group hier-command-group--${side} ${isSubgroup ? 'hier-command-group--subgroup' : ''} ${hasSubgroups ? 'hier-command-group--has-subgroups' : ''}`}>
      <h4 className={`hier-command-group__title ${isSubgroup ? 'hier-command-group__title--subgroup' : ''}`}>
        {titleText}
        {group.size && !isContinuation && <span className="hier-command-group__size"> ({group.size})</span>}
      </h4>
      
      {group.leader && (
        <LeaderHeader leader={group.leader} footnotes={footnotes} gameId={gameId} side={side} />
      )}
      
      {/* Direct units for this command */}
      {group.units.length > 0 && (
        <div className="hier-command-group__units">
          {group.units.map((unit, idx) => (
            <UnitRow 
              key={`${unit.name}-${idx}`}
              unit={unit}
              footnotes={footnotes}
              gameId={gameId}
              side={side}
            />
          ))}
        </div>
      )}
      
      {/* Subgroups (e.g., Divisions under a Corps) */}
      {group.subgroups.length > 0 && (
        <div className="hier-command-group__subgroups">
          {group.subgroups.map((subgroup, idx) => (
            <CommandGroupSection
              key={`${subgroup.commandCode}-${idx}`}
              group={subgroup}
              footnotes={footnotes}
              side={side}
              gameId={gameId}
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
}: {
  title: string;
  units: Unit[];
  footnotes: Record<string, string>;
  gunboats: import("../types").Gunboat[];
  side: "confederate" | "union";
  gameId?: string;
}) {
  const armyLeader = getArmyLeader(units);
  const hierarchy = buildCommandHierarchy(units);
  
  // Separate groups with subgroups (Corps with divisions) from flat groups
  const nestedGroups = hierarchy.filter(g => g.subgroups.length > 0);
  const flatGroups = hierarchy.filter(g => g.subgroups.length === 0);
  
  // Split large groups into multiple columns
  const splitFlatGroups = splitLargeGroups(flatGroups, MAX_UNITS_PER_COLUMN);
  const splitNestedGroups = splitLargeGroups(nestedGroups, MAX_UNITS_PER_COLUMN);
  
  return (
    <section className={`hier-army-section hier-army-section--${side}`}>
      <div className="hier-army-section__header">
        <h3 className="hier-army-section__title">{title}</h3>
        {armyLeader && (
          <LeaderHeader leader={armyLeader} footnotes={footnotes} gameId={gameId} side={side} />
        )}
      </div>
      
      {/* Flat groups in 3-column grid */}
      {splitFlatGroups.length > 0 && (
        <div className="hier-army-section__groups">
          {splitFlatGroups.map((group, idx) => (
            <CommandGroupSection 
              key={`${group.commandCode}-${group.columnIndex || 0}-${idx}`}
              group={group}
              footnotes={footnotes}
              side={side}
              gameId={gameId}
            />
          ))}
        </div>
      )}
      
      {/* Nested groups (Corps with divisions) - full width, each with its own 3-column grid */}
      {splitNestedGroups.map((group, idx) => (
        <CommandGroupSection 
          key={`${group.commandCode}-${group.columnIndex || 0}-${idx}`}
          group={group}
          footnotes={footnotes}
          side={side}
          gameId={gameId}
        />
      ))}
      
      <GunboatsList gunboats={gunboats} />
      <FootnotesLegend footnotes={footnotes} />
    </section>
  );
}

export function HierarchicalRosterSheet({ scenario, gameName, gameId }: HierarchicalRosterSheetProps) {
  return (
    <div className="hier-roster-sheet">
      <header className="hier-roster-sheet__header">
        {gameName} — Scenario {scenario.number}: {scenario.name}
      </header>
      
      <div className="hier-roster-sheet__armies">
        <ArmySection
          title="Confederate"
          units={scenario.confederateUnits}
          footnotes={scenario.confederateFootnotes}
          gunboats={scenario.confederateGunboats}
          side="confederate"
          gameId={gameId}
        />
        
        <ArmySection
          title="Union"
          units={scenario.unionUnits}
          footnotes={scenario.unionFootnotes}
          gunboats={scenario.unionGunboats}
          side="union"
          gameId={gameId}
        />
      </div>
    </div>
  );
}
