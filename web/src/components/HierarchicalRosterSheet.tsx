import type { Gunboat, Scenario, Unit } from "../types";
import { parseHexLocation } from "../hexLocationConfig";
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
  
  // Build groups - start with known leaders (to maintain hierarchy order)
  const groups: CommandGroup[] = [];
  const processedCommands = new Set<string>();
  
  // First add leader-based groups (Corps, Div leaders)
  const sortedLeaders = [...leaders].sort((a, b) => {
    // Sort by size priority: Army > District > Corps > Div > Brig
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
  
  for (const leader of sortedLeaders) {
    const cmd = leader.command;
    if (cmd === "-" || cmd === "—") continue;
    
    // Skip army/district leaders as they don't have direct units
    if (leader.size === "Army" || leader.size === "District") continue;
    
    processedCommands.add(cmd);
    
    // Get units for this command or commands that are subordinate
    const directUnits = unitsByCommand[cmd] || [];
    
    // Also look for sub-commands (e.g., P-I is subordinate to I)
    // This handles div-level commands under corps
    const subordinateUnits: Unit[] = [];
    for (const [otherCmd, otherUnits] of Object.entries(unitsByCommand)) {
      if (otherCmd.includes(`-${cmd}`) || otherCmd.endsWith(`-${cmd}`)) {
        subordinateUnits.push(...otherUnits);
        processedCommands.add(otherCmd);
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
    });
  }
  
  return groups;
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
  
  return (
    <div className="hier-leader-header">
      <div className="hier-leader-header__setup">
        <span className="hier-leader-header__hex">{hexCode}</span>
        {locationName && <span className="hier-leader-header__location">({locationName})</span>}
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
}: { 
  group: CommandGroup;
  footnotes: Record<string, string>;
  side: "confederate" | "union";
}) {
  return (
    <div className={`hier-command-group hier-command-group--${side}`}>
      <h4 className="hier-command-group__title">
        {group.displayName}
        {group.size && <span className="hier-command-group__size"> ({group.size})</span>}
      </h4>
      
      {group.leader && (
        <LeaderHeader leader={group.leader} footnotes={footnotes} />
      )}
      
      <div className="hier-command-group__units">
        {group.units.map((unit, idx) => (
          <UnitRow 
            key={`${unit.name}-${idx}`}
            unit={unit}
            footnotes={footnotes}
          />
        ))}
      </div>
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
  
  return (
    <section className={`hier-army-section hier-army-section--${side}`}>
      <h3 className="hier-army-section__title">{title}</h3>
      
      {armyLeader && (
        <div className="hier-army-section__army-leader">
          <LeaderHeader leader={armyLeader} footnotes={footnotes} />
        </div>
      )}
      
      <div className="hier-army-section__groups">
        {hierarchy.map((group, idx) => (
          <CommandGroupSection 
            key={`${group.commandCode}-${idx}`}
            group={group}
            footnotes={footnotes}
            side={side}
          />
        ))}
      </div>
      
      <GunboatsList gunboats={gunboats} />
      <FootnotesLegend footnotes={footnotes} />
    </section>
  );
}

export function HierarchicalRosterSheet({ scenario, gameName }: HierarchicalRosterSheetProps) {
  return (
    <div className="hier-roster-sheet">
      <header className="hier-roster-sheet__header">
        <h1 className="hier-roster-sheet__title">{gameName}</h1>
        <h2 className="hier-roster-sheet__scenario">
          Scenario {scenario.number}: {scenario.name}
        </h2>
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
