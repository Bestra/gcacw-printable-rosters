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
import { RosterProvider, useRoster } from "../context/RosterContext";
import { FootnotesLegend } from "./shared/FootnotesLegend";
import { GunboatsList } from "./shared/GunboatsList";
import "./FlowRosterSheet.css";

interface FlowRosterSheetProps {
  scenario: Scenario;
  gameName: string;
  gameId?: string;
  showImages: boolean;
}

// Maximum units per column before splitting into multiple columns
const MAX_UNITS_PER_COLUMN = 6;

// Compact unit row for flow display
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
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !unit.reinforcementSet || !unit.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="flow-unit-row">
      <div className="flow-unit-row__setup">
        {showHexLocation && (
          <>
            <span className="flow-unit-row__hex">{hexCode}</span>
            {locationName && <span className="flow-unit-row__location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="flow-unit-row__table">{tableAbbrev}</span>}
        {unit.reinforcementSet && (
          <span className="flow-unit-row__reinforcement">Reinf Set {unit.reinforcementSet}</span>
        )}
      </div>
      <div className="flow-unit-row__counters">
        {/* Box 1: Unit counter image or name */}
        <div className={`flow-unit-row__counter-box flow-unit-row__counter-box--name${imagePath ? ' flow-unit-row__counter-box--has-image' : ''}`}>
          {imagePath ? (
            <img 
              src={imagePath} 
              alt={unit.name} 
              className="flow-unit-row__counter-image"
            />
          ) : (
            <span className="flow-unit-row__name">{unit.name}</span>
          )}
          {notes && <span className="flow-unit-row__notes">{notes}</span>}
        </div>
        {/* Box 2: Fortification */}
        <div className="flow-unit-row__counter-box" />
        {/* Box 3: Manpower */}
        <div className="flow-unit-row__counter-box flow-unit-row__counter-box--info">
          <span className="flow-unit-row__mp">{mpDisplay || "\u00A0"}</span>
        </div>
        {/* Box 4: Fatigue */}
        <div className="flow-unit-row__counter-box flow-unit-row__counter-box--info">
          {fatigue && <span className="flow-unit-row__fatigue">{fatigue}</span>}
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
    <div className="flow-leader-header">
      <div className="flow-leader-header__counter">
        <div className={`flow-leader-header__counter-box${imagePath ? ' flow-leader-header__counter-box--has-image' : ''}`}>
          {imagePath ? (
            <img 
              src={imagePath} 
              alt={leader.name} 
              className="flow-leader-header__counter-image"
            />
          ) : (
            <span className="flow-leader-header__name">{leader.name}</span>
          )}
          {notes && <span className="flow-leader-header__notes">{notes}</span>}
        </div>
      </div>
      <div className="flow-leader-header__setup">
        {showHexLocation && (
          <>
            <span className="flow-leader-header__hex">{hexCode}</span>
            {locationName && <span className="flow-leader-header__location">({locationName})</span>}
          </>
        )}
        {tableAbbrev && <span className="flow-leader-header__table">{tableAbbrev}</span>}
        {leader.reinforcementSet && (
          <span className="flow-leader-header__reinforcement">Reinf Set {leader.reinforcementSet}</span>
        )}
        {fatigue && <span className="flow-leader-header__fatigue">{fatigue}</span>}
      </div>
    </div>
  );
}

// Command group section - designed to flow in columns
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
  const isContinuation = group.columnIndex && group.columnIndex > 1;
  
  // Build the title with continuation indicator if needed
  let titleText = group.displayName;
  if (isContinuation) {
    titleText = `${group.displayName} (cont.)`;
  }
  
  return (
    <div className={`flow-command-group flow-command-group--${side} ${isSubgroup ? 'flow-command-group--subgroup' : ''}`}>
      <h4 className={`flow-command-group__title ${isSubgroup ? 'flow-command-group__title--subgroup' : ''}`}>
        {titleText}
        {group.size && !isContinuation && <span className="flow-command-group__size"> ({group.size})</span>}
      </h4>
      
      {group.leader && (
        <LeaderHeader leader={group.leader} footnotes={footnotes} />
      )}
      
      {/* Direct units for this command */}
      {group.units.length > 0 && (
        <div className="flow-command-group__units">
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
        <div className="flow-command-group__subgroups">
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

// Army side section with CSS multi-column flow
function ArmySection({
  title,
  units,
  footnotes,
  gunboats,
  side,
  gameId,
  showImages,
}: {
  title: string;
  units: Unit[];
  footnotes: Record<string, string>;
  gunboats: import("../types").Gunboat[];
  side: "confederate" | "union";
  gameId?: string;
  showImages: boolean;
}) {
  const armyLeader = getArmyLeader(units);
  const hierarchy = buildCommandHierarchy(units);
  
  // Split large groups into multiple columns
  const splitGroups = splitLargeGroups(hierarchy, MAX_UNITS_PER_COLUMN);
  
  return (
    <RosterProvider gameId={gameId} side={side} showImages={showImages}>
      <section className={`flow-army-section flow-army-section--${side}`}>
        <div className="flow-army-section__header">
          <h3 className="flow-army-section__title">{title}</h3>
          {armyLeader && (
            <LeaderHeader leader={armyLeader} footnotes={footnotes} />
          )}
        </div>
        
        {/* Multi-column flow container */}
        <div className="flow-army-section__columns">
          {splitGroups.map((group, idx) => (
            <CommandGroupSection 
              key={`${group.commandCode}-${group.columnIndex || 0}-${idx}`}
              group={group}
              footnotes={footnotes}
            />
          ))}
        </div>
        
        <GunboatsList gunboats={gunboats} />
        <FootnotesLegend footnotes={footnotes} />
      </section>
    </RosterProvider>
  );
}

export function FlowRosterSheet({ scenario, gameName, gameId, showImages }: FlowRosterSheetProps) {
  return (
    <div className="flow-roster-sheet">
      <header className="flow-roster-sheet__header">
        {gameName} — Scenario {scenario.number}: {scenario.name}
      </header>
      
      <div className="flow-roster-sheet__armies">
        <ArmySection
          title="Confederate"
          units={scenario.confederateUnits}
          footnotes={scenario.confederateFootnotes}
          gunboats={scenario.confederateGunboats}
          side="confederate"
          gameId={gameId}
          showImages={showImages}
        />
        
        <ArmySection
          title="Union"
          units={scenario.unionUnits}
          footnotes={scenario.unionFootnotes}
          gunboats={scenario.unionGunboats}
          side="union"
          gameId={gameId}
          showImages={showImages}
        />
      </div>
    </div>
  );
}
