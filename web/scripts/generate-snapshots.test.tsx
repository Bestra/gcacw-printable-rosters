/**
 * DOM Snapshot Generator
 *
 * Renders RosterSheet for each game/scenario using vitest + React Testing Library
 * and extracts structured JSON snapshots from the rendered DOM.
 *
 * Run with vitest: npx vitest run scripts/generate-snapshots.test.ts
 * 
 * This is structured as a test file to leverage vitest's CSS handling
 * and jsdom environment.
 */

import { describe, test, expect } from "vitest";
import { render } from "@testing-library/react";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { RosterSheet } from "../src/components/RosterSheet";
import type { GameData, Scenario } from "../src/types";

// ES module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// Types
// ============================================================================

interface SnapshotUnit {
  name: string;
  hex: string;
  location?: string;
  manpower?: string;
  fatigue?: string;
  notes?: string;
  reinforcementSet?: string;
  tableAbbrev?: string;
}

interface SnapshotLeader {
  name: string;
  hex: string;
  location?: string;
  notes?: string;
  fatigue?: string;
}

interface SnapshotCommandGroup {
  title: string;
  leader?: SnapshotLeader;
  units: SnapshotUnit[];
  subgroups: SnapshotCommandGroup[];
}

interface SnapshotGunboat {
  name: string;
  location: string;
}

interface SideSnapshot {
  armyLeader?: SnapshotLeader;
  commandGroups: SnapshotCommandGroup[];
  gunboats: SnapshotGunboat[];
  footnotes: Record<string, string>;
  unitCount: number;
  leaderCount: number;
}

interface ScenarioSnapshot {
  generatedAt: string;
  gameId: string;
  gameName: string;
  scenarioNumber: number;
  scenarioName: string;
  confederate: SideSnapshot;
  union: SideSnapshot;
}

// ============================================================================
// Data Loading
// ============================================================================

function loadGameData(gameId: string): GameData {
  const dataPath = path.join(__dirname, "..", "public", "data", `${gameId}.json`);
  const content = readFileSync(dataPath, "utf-8");
  return JSON.parse(content);
}

function loadGamesIndex(): { games: Array<{ id: string; name: string }> } {
  const gamesPath = path.join(__dirname, "..", "public", "data", "games.json");
  const content = readFileSync(gamesPath, "utf-8");
  return JSON.parse(content);
}

// ============================================================================
// DOM Extraction
// ============================================================================

function extractLeaderFromElement(el: Element): SnapshotLeader | undefined {
  const nameEl = el.querySelector(".name, .counter-image");
  const name = nameEl?.textContent?.trim() || nameEl?.getAttribute("alt") || "";
  
  if (!name) return undefined;
  
  const hexEl = el.querySelector(".hex");
  const locationEl = el.querySelector(".location");
  const notesEl = el.querySelector(".notes");
  const fatigueEl = el.querySelector(".fatigue");
  
  const leader: SnapshotLeader = {
    name,
    hex: hexEl?.textContent?.trim() || "",
  };
  
  if (locationEl?.textContent) {
    leader.location = locationEl.textContent.trim().replace(/[()]/g, "");
  }
  if (notesEl?.textContent?.trim()) {
    leader.notes = notesEl.textContent.trim();
  }
  if (fatigueEl?.textContent?.trim()) {
    leader.fatigue = fatigueEl.textContent.trim();
  }
  
  return leader;
}

function extractUnitFromRow(row: Element): SnapshotUnit {
  const nameEl = row.querySelector(".name, .counter-image");
  const name = nameEl?.textContent?.trim() || nameEl?.getAttribute("alt") || "";
  
  const hexEl = row.querySelector(".hex");
  const locationEl = row.querySelector(".location");
  const mpEl = row.querySelector(".mp");
  const fatigueEl = row.querySelector(".fatigue");
  const notesEl = row.querySelector(".notes");
  const reinforcementEl = row.querySelector(".reinforcement");
  const tableAbbrevEl = row.querySelector(".table-abbrev");
  
  const unit: SnapshotUnit = {
    name,
    hex: hexEl?.textContent?.trim() || "",
  };
  
  if (locationEl?.textContent) {
    unit.location = locationEl.textContent.trim().replace(/[()]/g, "");
  }
  if (mpEl?.textContent?.trim()) {
    unit.manpower = mpEl.textContent.trim();
  }
  if (fatigueEl?.textContent?.trim()) {
    unit.fatigue = fatigueEl.textContent.trim();
  }
  if (notesEl?.textContent?.trim()) {
    unit.notes = notesEl.textContent.trim();
  }
  if (reinforcementEl?.textContent?.trim()) {
    unit.reinforcementSet = reinforcementEl.textContent.trim().replace(/^Set\s+/, "");
  }
  if (tableAbbrevEl?.textContent?.trim()) {
    unit.tableAbbrev = tableAbbrevEl.textContent.trim();
  }
  
  return unit;
}

function extractCommandGroup(groupEl: Element): SnapshotCommandGroup {
  const titleEl = groupEl.querySelector(".group-title");
  const title = titleEl?.textContent?.trim() || "Unknown";
  
  // Extract leader if present - use direct child selector carefully
  const leaderHeaders = groupEl.querySelectorAll(".leader-header");
  let leader: SnapshotLeader | undefined;
  for (const lh of leaderHeaders) {
    // Check if this leader-header is a direct child (not in a subgroup)
    if (lh.parentElement === groupEl) {
      leader = extractLeaderFromElement(lh);
      break;
    }
  }
  
  // Extract direct units - find units-list that is a direct child
  const unitsLists = groupEl.querySelectorAll(".units-list");
  const units: SnapshotUnit[] = [];
  for (const ul of unitsLists) {
    if (ul.parentElement === groupEl) {
      const unitRows = ul.querySelectorAll(".unit-row");
      for (const row of unitRows) {
        units.push(extractUnitFromRow(row));
      }
      break;
    }
  }
  
  // Extract subgroups recursively - find subgroups container that is direct child
  const subgroupsContainers = groupEl.querySelectorAll(".subgroups");
  const subgroups: SnapshotCommandGroup[] = [];
  for (const sc of subgroupsContainers) {
    if (sc.parentElement === groupEl) {
      const subgroupEls = sc.querySelectorAll(":scope > .command-group");
      for (const sg of subgroupEls) {
        subgroups.push(extractCommandGroup(sg));
      }
      break;
    }
  }
  
  return { title, leader, units, subgroups };
}

function extractFootnotes(sectionEl: Element): Record<string, string> {
  const footnotes: Record<string, string> = {};
  const footnoteItems = sectionEl.querySelectorAll(".legend-key__footnotes .legend-item");
  
  for (const item of footnoteItems) {
    const symbolEl = item.querySelector(".legend-symbol");
    const textEl = item.querySelector(".legend-text");
    if (symbolEl && textEl) {
      const symbol = symbolEl.textContent?.trim() || "";
      const text = textEl.textContent?.trim() || "";
      if (symbol && text) {
        footnotes[symbol] = text;
      }
    }
  }
  
  return footnotes;
}

function extractGunboats(sectionEl: Element): SnapshotGunboat[] {
  const gunboats: SnapshotGunboat[] = [];
  const gunboatItems = sectionEl.querySelectorAll(".gunboats-list .gunboat-item");
  
  for (const item of gunboatItems) {
    const nameEl = item.querySelector(".gunboat-name");
    const locationEl = item.querySelector(".gunboat-location");
    if (nameEl && locationEl) {
      gunboats.push({
        name: nameEl.textContent?.trim() || "",
        location: locationEl.textContent?.trim() || "",
      });
    }
  }
  
  return gunboats;
}

function extractSideSnapshot(sectionEl: Element): SideSnapshot {
  // Extract army leader from army header
  const armyHeader = sectionEl.querySelector(".army-header .leader-header");
  const armyLeader = armyHeader ? extractLeaderFromElement(armyHeader) : undefined;
  
  // Extract command groups from groups container
  const groupsContainer = sectionEl.querySelector(".groups-container");
  const groupEls = groupsContainer?.querySelectorAll(":scope > .command-group") || [];
  const commandGroups = Array.from(groupEls).map(extractCommandGroup);
  
  // Also check for top-level command groups (nested/hierarchical ones outside groups-container)
  const allTopLevel = sectionEl.querySelectorAll(":scope > .command-group");
  for (const groupEl of allTopLevel) {
    commandGroups.push(extractCommandGroup(groupEl));
  }
  
  // Extract footnotes and gunboats
  const footnotes = extractFootnotes(sectionEl);
  const gunboats = extractGunboats(sectionEl);
  
  // Count units and leaders
  let unitCount = 0;
  let leaderCount = armyLeader ? 1 : 0;
  
  function countInGroup(group: SnapshotCommandGroup) {
    unitCount += group.units.length;
    if (group.leader) leaderCount++;
    for (const sub of group.subgroups) {
      countInGroup(sub);
    }
  }
  
  for (const group of commandGroups) {
    countInGroup(group);
  }
  
  return {
    armyLeader,
    commandGroups,
    gunboats,
    footnotes,
    unitCount,
    leaderCount,
  };
}

function extractScenarioSnapshot(
  container: HTMLElement,
  gameData: GameData,
  scenario: Scenario
): ScenarioSnapshot {
  const confederateSection = container.querySelector(".army-section.confederate");
  const unionSection = container.querySelector(".army-section.union");
  
  return {
    generatedAt: new Date().toISOString(),
    gameId: gameData.id,
    gameName: gameData.name,
    scenarioNumber: scenario.number,
    scenarioName: scenario.name,
    confederate: confederateSection 
      ? extractSideSnapshot(confederateSection) 
      : { commandGroups: [], gunboats: [], footnotes: {}, unitCount: 0, leaderCount: 0 },
    union: unionSection 
      ? extractSideSnapshot(unionSection)
      : { commandGroups: [], gunboats: [], footnotes: {}, unitCount: 0, leaderCount: 0 },
  };
}

// ============================================================================
// Snapshot File Management
// ============================================================================

function getSnapshotPath(gameId: string, scenarioNumber: number): string {
  return path.join(__dirname, "..", "snapshots", gameId, `scenario-${scenarioNumber}.json`);
}

function ensureSnapshotDir(gameId: string): void {
  const dir = path.join(__dirname, "..", "snapshots", gameId);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function writeSnapshot(gameId: string, scenarioNumber: number, snapshot: ScenarioSnapshot): void {
  ensureSnapshotDir(gameId);
  const snapshotPath = getSnapshotPath(gameId, scenarioNumber);
  writeFileSync(snapshotPath, JSON.stringify(snapshot, null, 2));
}

// ============================================================================
// Test-based Generator
// ============================================================================

// Get filter from environment variables
const targetGame = process.env.SNAPSHOT_GAME;
const targetScenario = process.env.SNAPSHOT_SCENARIO ? parseInt(process.env.SNAPSHOT_SCENARIO, 10) : undefined;

const gamesIndex = loadGamesIndex();
const gamesToProcess = targetGame 
  ? gamesIndex.games.filter(g => g.id === targetGame)
  : gamesIndex.games;

describe("DOM Snapshot Generator", () => {
  for (const gameInfo of gamesToProcess) {
    describe(gameInfo.name, () => {
      const gameData = loadGameData(gameInfo.id);
      const scenarios = targetScenario
        ? gameData.scenarios.filter(s => s.number === targetScenario)
        : gameData.scenarios;

      for (const scenario of scenarios) {
        test(`Scenario ${scenario.number}: ${scenario.name}`, () => {
          const { container } = render(
            <RosterSheet
              scenario={scenario}
              gameName={gameData.name}
              gameId={gameData.id}
              showImages={false}
              variant="flow"
            />
          );

          const snapshot = extractScenarioSnapshot(container, gameData, scenario);
          writeSnapshot(gameData.id, scenario.number, snapshot);
          
          // Basic validation
          expect(snapshot.confederate.unitCount + snapshot.confederate.leaderCount).toBeGreaterThan(0);
          expect(snapshot.union.unitCount + snapshot.union.leaderCount).toBeGreaterThan(0);
        });
      }
    });
  }
});
