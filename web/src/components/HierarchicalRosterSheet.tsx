import type { Gunboat, Scenario, Unit } from "../types";
import { parseHexLocation } from "../hexLocationConfig";
import { getTableAbbreviation } from "../tableNameConfig";
import "./HierarchicalRosterSheet.css";

interface HierarchicalRosterSheetProps {
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

// Get note symbols for display (excluding fatigue)
function getNoteSymbols(unit: Unit): string {
  return unit.notes.join("");
}

// Command group with leader and subordinate units
interface CommandGroup {
  leader: Unit | null;
  commandCode: string;
  displayName: string;
  size: string;
  units: Unit[];
  subgroups: CommandGroup[]; // Nested groups for Corps -> Div hierarchy
  parentCommand?: string; // Track which Corps this Div belongs to
  columnIndex?: number; // For multi-column splits (1, 2, 3...)
  totalColumns?: number; // Total number of columns for this command
}

// Maximum units per column before splitting into multiple columns
const MAX_UNITS_PER_COLUMN = 8;

// Check if a command is subordinate to another (e.g., C-Cav is subordinate to Cav)
function isSubordinateCommand(childCmd: string, parentCmd: string): boolean {
  return childCmd.includes(`-${parentCmd}`) || childCmd.endsWith(`-${parentCmd}`);
}

// Build command hierarchy from units
function buildCommandHierarchy(units: Unit[]): CommandGroup[] {
  const leaders = units.filter(u => u.type === "Ldr");
  const combatUnits = units.filter(u => u.type !== "Ldr");
  
  // Map from command code to leader
  const leaderByCommand: Record<string, Unit> = {};
  for (const leader of leaders) {
    if (leader.command !== "-" && leader.command !== "—") {
      leaderByCommand[leader.command] = leader;
    }
  }
  
  // Group units by their command code
  const unitsByCommand: Record<string, Unit[]> = {};
  for (const unit of combatUnits) {
    const cmd = unit.command || "-";
    if (!unitsByCommand[cmd]) {
      unitsByCommand[cmd] = [];
    }
    unitsByCommand[cmd].push(unit);
  }
  
  // Sort leaders by size priority
  const sortedLeaders = [...leaders].sort((a, b) => {
    const sizePriority: Record<string, number> = {
      "Army": 0,
      "District": 1,
      "Corps": 2,
      "Div": 3,
      "Brig": 4,
    };
    const aP = sizePriority[a.size] ?? 5;
    const bP = sizePriority[b.size] ?? 5;
    if (aP !== bP) return aP - bP;
    return a.name.localeCompare(b.name);
  });
  
  // Identify Corps leaders and their subordinate Div commands
  const corpsLeaders = sortedLeaders.filter(l => l.size === "Corps");
  const divLeaders = sortedLeaders.filter(l => l.size === "Div");
  
  // Map Div commands to their parent Corps command
  const divToCorps: Record<string, string> = {};
  for (const corpsLeader of corpsLeaders) {
    const corpsCmd = corpsLeader.command;
    for (const divLeader of divLeaders) {
      const divCmd = divLeader.command;
      if (isSubordinateCommand(divCmd, corpsCmd)) {
        divToCorps[divCmd] = corpsCmd;
      }
    }
  }
  
  // Build groups
  const groups: CommandGroup[] = [];
  const processedCommands = new Set<string>();
  
  for (const leader of sortedLeaders) {
    const cmd = leader.command;
    if (cmd === "-" || cmd === "—") continue;
    
    // Skip army/district leaders as they don't have direct units
    if (leader.size === "Army" || leader.size === "District") continue;
    
    // Skip if already processed (as subgroup of a Corps)
    if (processedCommands.has(cmd)) continue;
    
    processedCommands.add(cmd);
    
    // For Corps leaders: check if they have subordinate Div leaders
    if (leader.size === "Corps") {
      const subordinateDivCmds = Object.entries(divToCorps)
        .filter(([, corpsCmd]) => corpsCmd === cmd)
        .map(([divCmd]) => divCmd);
      
      if (subordinateDivCmds.length > 0) {
        // Corps has subordinate divisions with their own leaders
        // Build subgroups for each division
        const subgroups: CommandGroup[] = [];
        
        for (const divCmd of subordinateDivCmds) {
          const divLeader = leaderByCommand[divCmd];
          if (!divLeader) continue;
          
          processedCommands.add(divCmd);
          
          const divUnits = unitsByCommand[divCmd] || [];
          if (divUnits.length > 0 || divLeader) {
            subgroups.push({
              leader: divLeader,
              commandCode: divCmd,
              displayName: `${divCmd} — ${divLeader.name}`,
              size: divLeader.size,
              units: divUnits,
              subgroups: [],
              parentCommand: cmd,
            });
          }
        }
        
        // Corps direct units (if any)
        const corpsDirectUnits = unitsByCommand[cmd] || [];
        
        groups.push({
          leader,
          commandCode: cmd,
          displayName: `${cmd} — ${leader.name}`,
          size: leader.size,
          units: corpsDirectUnits,
          subgroups,
        });
        continue;
      }
    }
    
    // For Div leaders that are subordinate to a Corps: skip (handled by Corps)
    if (leader.size === "Div" && divToCorps[cmd]) {
      continue;
    }
    
    // Standard processing: direct units + subordinate units without their own leader
    const directUnits = unitsByCommand[cmd] || [];
    
    const subordinateUnits: Unit[] = [];
    for (const [otherCmd, otherUnits] of Object.entries(unitsByCommand)) {
      if (isSubordinateCommand(otherCmd, cmd)) {
        const hasOwnLeader = leaderByCommand[otherCmd] !== undefined;
        if (!hasOwnLeader) {
          subordinateUnits.push(...otherUnits);
          processedCommands.add(otherCmd);
        }
      }
    }
    
    const allUnits = [...directUnits, ...subordinateUnits];
    if (allUnits.length > 0) {
      groups.push({
        leader,
        commandCode: cmd,
        displayName: `${cmd} — ${leader.name}`,
        size: leader.size,
        units: allUnits,
        subgroups: [],
      });
    }
  }
  
  // Add groups for commands without leaders
  for (const [cmd, cmdUnits] of Object.entries(unitsByCommand)) {
    if (processedCommands.has(cmd)) continue;
    if (cmdUnits.length === 0) continue;
    
    groups.push({
      leader: null,
      commandCode: cmd,
      displayName: cmd === "-" || cmd === "—" ? "Independent" : cmd,
      size: "",
      units: cmdUnits,
      subgroups: [],
    });
  }
  
  return groups;
}

// Split a single group with many units into multiple column groups
function splitGroupIntoColumns(group: CommandGroup): CommandGroup[] {
  const unitCount = group.units.length;
  
  // Don't split small groups
  if (unitCount <= MAX_UNITS_PER_COLUMN) {
    return [group];
  }
  
  // Calculate number of columns needed
  const numColumns = Math.ceil(unitCount / MAX_UNITS_PER_COLUMN);
  
  // Split units evenly across columns
  const unitsPerColumn = Math.ceil(unitCount / numColumns);
  
  const splitGroups: CommandGroup[] = [];
  for (let i = 0; i < numColumns; i++) {
    const startIdx = i * unitsPerColumn;
    const endIdx = Math.min(startIdx + unitsPerColumn, unitCount);
    const columnUnits = group.units.slice(startIdx, endIdx);
    
    splitGroups.push({
      ...group,
      units: columnUnits,
      // Only show leader in first column
      leader: i === 0 ? group.leader : null,
      columnIndex: i + 1,
      totalColumns: numColumns,
    });
  }
  
  return splitGroups;
}

// Split all groups that exceed the column limit
function splitLargeGroups(groups: CommandGroup[]): CommandGroup[] {
  const result: CommandGroup[] = [];
  
  for (const group of groups) {
    // First, split the group's own units if needed
    const splitMain = splitGroupIntoColumns(group);
    
    // For groups with subgroups, also split those
    if (group.subgroups.length > 0) {
      const splitSubgroups: CommandGroup[] = [];
      for (const subgroup of group.subgroups) {
        splitSubgroups.push(...splitGroupIntoColumns(subgroup));
      }
      
      // Add the main group (first split) with split subgroups
      splitMain[0] = {
        ...splitMain[0],
        subgroups: splitSubgroups,
      };
      
      // Subsequent splits don't have subgroups
      for (let i = 1; i < splitMain.length; i++) {
        splitMain[i] = {
          ...splitMain[i],
          subgroups: [],
        };
      }
    }
    
    result.push(...splitMain);
  }
  
  return result;
}

// Get army-level leader
function getArmyLeader(units: Unit[]): Unit | null {
  return units.find(u => u.type === "Ldr" && (u.size === "Army" || u.size === "District")) ?? null;
}

// Compact unit row for hierarchical display
function UnitRow({ 
  unit, 
  footnotes,
  leaderName,
}: { 
  unit: Unit;
  footnotes: Record<string, string>;
  leaderName?: string;
}) {
  const { hexCode, locationName } = parseHexLocation(unit.hexLocation);
  const fatigue = getStartingFatigue(unit, footnotes);
  const notes = getNoteSymbols(unit);
  const mpDisplay = unit.manpowerValue !== "-" ? unit.manpowerValue : "";
  const tableAbbrev = getTableAbbreviation(unit.tableName);
  
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
        {/* Box 1: Unit name (what it looks like on the board) */}
        <div className="hier-unit-row__counter-box hier-unit-row__counter-box--name">
          <span className="hier-unit-row__name">{unit.name}</span>
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
  footnotes 
}: { 
  leader: Unit;
  footnotes: Record<string, string>;
}) {
  const { hexCode, locationName } = parseHexLocation(leader.hexLocation);
  const fatigue = getStartingFatigue(leader, footnotes);
  const notes = getNoteSymbols(leader);
  const tableAbbrev = getTableAbbreviation(leader.tableName);
  
  // Don't show hex location if it's just a "See rule" reference and we have reinforcement set
  const showHexLocation = !leader.reinforcementSet || !leader.hexLocation.toLowerCase().startsWith("see");
  
  return (
    <div className="hier-leader-header">
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
      <div className="hier-leader-header__counter">
        <div className="hier-leader-header__counter-box">
          <span className="hier-leader-header__name">{leader.name}</span>
          {notes && <span className="hier-leader-header__notes">{notes}</span>}
        </div>
      </div>
    </div>
  );
}

// Command group section
function CommandGroupSection({ 
  group, 
  footnotes,
  side,
  isSubgroup = false,
}: { 
  group: CommandGroup;
  footnotes: Record<string, string>;
  side: "confederate" | "union";
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
        <LeaderHeader leader={group.leader} footnotes={footnotes} />
      )}
      
      {/* Direct units for this command */}
      {group.units.length > 0 && (
        <div className="hier-command-group__units">
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
        <div className="hier-command-group__subgroups">
          {group.subgroups.map((subgroup, idx) => (
            <CommandGroupSection
              key={`${subgroup.commandCode}-${idx}`}
              group={subgroup}
              footnotes={footnotes}
              side={side}
              isSubgroup={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Footnotes legend
function FootnotesLegend({ footnotes }: { footnotes: Record<string, string> }) {
  const entries = Object.entries(footnotes);
  if (entries.length === 0) return null;
  
  return (
    <div className="hier-footnotes">
      {entries.map(([symbol, text]) => (
        <div key={symbol} className="hier-footnotes__item">
          <span className="hier-footnotes__symbol">{symbol}</span>
          <span className="hier-footnotes__text">{text}</span>
        </div>
      ))}
    </div>
  );
}

// Display gunboats
function GunboatsList({ gunboats }: { gunboats: Gunboat[] }) {
  if (gunboats.length === 0) return null;
  
  return (
    <div className="hier-gunboats">
      <h4 className="hier-gunboats__title">Gunboats</h4>
      <ul className="hier-gunboats__list">
        {gunboats.map((gunboat, index) => (
          <li key={index} className="hier-gunboats__item">
            <span className="hier-gunboats__name">{gunboat.name}</span>
            {gunboat.location && (
              <span className="hier-gunboats__location"> — {gunboat.location}</span>
            )}
          </li>
        ))}
      </ul>
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
}: {
  title: string;
  units: Unit[];
  footnotes: Record<string, string>;
  gunboats: Gunboat[];
  side: "confederate" | "union";
}) {
  const armyLeader = getArmyLeader(units);
  const hierarchy = buildCommandHierarchy(units);
  
  // Separate groups with subgroups (Corps with divisions) from flat groups
  const nestedGroups = hierarchy.filter(g => g.subgroups.length > 0);
  const flatGroups = hierarchy.filter(g => g.subgroups.length === 0);
  
  // Split large groups into multiple columns
  const splitFlatGroups = splitLargeGroups(flatGroups);
  const splitNestedGroups = splitLargeGroups(nestedGroups);
  
  return (
    <section className={`hier-army-section hier-army-section--${side}`}>
      <div className="hier-army-section__header">
        <h3 className="hier-army-section__title">{title}</h3>
        {armyLeader && (
          <LeaderHeader leader={armyLeader} footnotes={footnotes} />
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
        />
      ))}
      
      <GunboatsList gunboats={gunboats} />
      <FootnotesLegend footnotes={footnotes} />
    </section>
  );
}

export function HierarchicalRosterSheet({ scenario, gameName }: HierarchicalRosterSheetProps) {
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
        />
        
        <ArmySection
          title="Union"
          units={scenario.unionUnits}
          footnotes={scenario.unionFootnotes}
          gunboats={scenario.unionGunboats}
          side="union"
        />
      </div>
    </div>
  );
}
