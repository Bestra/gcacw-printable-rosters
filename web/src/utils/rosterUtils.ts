import type { Unit } from "../types";

// Command group with leader and subordinate units
export interface CommandGroup {
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

// Determine starting fatigue from footnotes - looks for "Fatigue Level X" pattern
export function getStartingFatigue(unit: Unit, footnotes: Record<string, string>): string | undefined {
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
export function getNoteSymbols(unit: Unit): string {
  return unit.notes.join("");
}

// Check if a command is subordinate to another (e.g., C-Cav is subordinate to Cav)
export function isSubordinateCommand(childCmd: string, parentCmd: string): boolean {
  return childCmd.includes(`-${parentCmd}`) || childCmd.endsWith(`-${parentCmd}`);
}

// Get army-level leader
export function getArmyLeader(units: Unit[]): Unit | null {
  return units.find(u => u.type === "Ldr" && (u.size === "Army" || u.size === "District")) ?? null;
}

// Build command hierarchy from units
export function buildCommandHierarchy(units: Unit[]): CommandGroup[] {
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
export function splitGroupIntoColumns(group: CommandGroup, maxUnitsPerColumn: number): CommandGroup[] {
  const unitCount = group.units.length;
  
  // Don't split small groups
  if (unitCount <= maxUnitsPerColumn) {
    return [group];
  }
  
  // Calculate number of columns needed
  const numColumns = Math.ceil(unitCount / maxUnitsPerColumn);
  
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
export function splitLargeGroups(groups: CommandGroup[], maxUnitsPerColumn: number): CommandGroup[] {
  const result: CommandGroup[] = [];
  
  for (const group of groups) {
    // First, split the group's own units if needed
    const splitMain = splitGroupIntoColumns(group, maxUnitsPerColumn);
    
    // For groups with subgroups, also split those
    if (group.subgroups.length > 0) {
      const splitSubgroups: CommandGroup[] = [];
      for (const subgroup of group.subgroups) {
        splitSubgroups.push(...splitGroupIntoColumns(subgroup, maxUnitsPerColumn));
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
