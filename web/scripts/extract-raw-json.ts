/**
 * Raw Table JSON Extractor
 *
 * Reads raw table data from parser/raw/{game}_raw_tables.json and returns
 * scenario tables as structured JSON for LLM evaluation.
 *
 * This is a helper module used by the LLM evaluation orchestrator.
 */

import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

// ES module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// Types
// ============================================================================

interface RawTableRow {
  [index: number]: string;
}

interface RawTable {
  name: string;
  page_numbers: number[];
  header_row: string[];
  rows: string[][];
}

interface RawScenario {
  scenario_number: number;
  scenario_name: string;
  start_page: number;
  end_page: number;
  confederate_tables: RawTable[];
  union_tables: RawTable[];
  confederate_footnotes?: Record<string, string>;
  union_footnotes?: Record<string, string>;
}

export interface ExtractedRawData {
  gameId: string;
  scenarioNumber: number;
  scenarioName: string;
  confederate: {
    tables: RawTable[];
    footnotes: Record<string, string>;
  };
  union: {
    tables: RawTable[];
    footnotes: Record<string, string>;
  };
}

// ============================================================================
// Raw Data Loading
// ============================================================================

function getRawTablesPath(gameId: string): string {
  return path.join(
    __dirname,
    "..",
    "..",
    "parser",
    "raw",
    `${gameId}_raw_tables.json`
  );
}

export function loadRawTables(gameId: string): RawScenario[] {
  const rawPath = getRawTablesPath(gameId);
  const content = readFileSync(rawPath, "utf-8");
  return JSON.parse(content);
}

export function extractRawScenarioData(
  gameId: string,
  scenarioNumber: number
): ExtractedRawData | null {
  const rawScenarios = loadRawTables(gameId);
  const scenario = rawScenarios.find(
    (s) => s.scenario_number === scenarioNumber
  );

  if (!scenario) {
    return null;
  }

  return {
    gameId,
    scenarioNumber: scenario.scenario_number,
    scenarioName: scenario.scenario_name,
    confederate: {
      tables: scenario.confederate_tables,
      footnotes: scenario.confederate_footnotes || {},
    },
    union: {
      tables: scenario.union_tables,
      footnotes: scenario.union_footnotes || {},
    },
  };
}

/**
 * Flatten raw tables into a simple list of units for easier comparison
 */
export function flattenRawTables(
  tables: RawTable[]
): Array<{ tableName: string; row: string[] }> {
  const result: Array<{ tableName: string; row: string[] }> = [];

  for (const table of tables) {
    for (const row of table.rows) {
      result.push({
        tableName: table.name,
        row,
      });
    }
  }

  return result;
}
