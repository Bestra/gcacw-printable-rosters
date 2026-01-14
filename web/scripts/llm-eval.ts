/**
 * LLM Evaluation Orchestrator
 *
 * Compares DOM snapshots against raw table data using an LLM to identify
 * parsing discrepancies. Uses GitHub Copilot CLI for evaluation.
 *
 * Usage:
 *   npx tsx scripts/llm-eval.ts --all
 *   npx tsx scripts/llm-eval.ts --game gtc2 --scenario 1
 */

import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  existsSync,
  statSync,
  readdirSync,
  unlinkSync,
} from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import { extractRawScenarioData, type ExtractedRawData } from "./extract-raw-json.js";

// ES module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Truncation limit for raw LLM output in error cases
const MAX_RAW_OUTPUT_LENGTH = 2000;

// ============================================================================
// Types
// ============================================================================

interface EvalIssue {
  side: "confederate" | "union";
  unit: string;
  field: string;
  expected: string;
  actual: string;
  severity: "critical" | "minor";
}

interface MissingUnit {
  side: "confederate" | "union";
  rawRow: string[];
  tableName: string;
}

interface ExtraUnit {
  side: "confederate" | "union";
  unitName: string;
}

interface EvalResult {
  pass: boolean;
  unitCountMatch?: {
    raw: { confederate: number; union: number };
    dom: { confederate: number; union: number };
    matches: boolean;
  };
  issues: EvalIssue[];
  missingUnits: MissingUnit[];
  extraUnits: ExtraUnit[];
  summary: string;
  error?: boolean;
  rawOutput?: string;
}

interface ScenarioEvalOutput {
  gameId: string;
  scenarioNumber: number;
  evaluatedAt: string;
  evaluationDurationMs: number;
  snapshotGeneratedAt: string;
  snapshotStale: boolean;
  result: EvalResult;
}

interface FullSuiteOutput {
  evaluatedAt: string;
  totalScenarios: number;
  passed: number;
  failed: number;
  errors: number;
  scenarios: ScenarioEvalOutput[];
}

// ============================================================================
// Snapshot & Data Loading
// ============================================================================

function getSnapshotPath(gameId: string, scenarioNumber: number): string {
  return path.join(
    __dirname,
    "..",
    "snapshots",
    gameId,
    `scenario-${scenarioNumber}.json`
  );
}

function getWebDataPath(gameId: string): string {
  return path.join(__dirname, "..", "public", "data", `${gameId}.json`);
}

function loadSnapshot(
  gameId: string,
  scenarioNumber: number
): { snapshot: unknown; generatedAt: string } | null {
  const snapshotPath = getSnapshotPath(gameId, scenarioNumber);
  if (!existsSync(snapshotPath)) {
    return null;
  }
  const content = readFileSync(snapshotPath, "utf-8");
  const snapshot = JSON.parse(content);
  return { snapshot, generatedAt: snapshot.generatedAt };
}

function loadGamesIndex(): { games: Array<{ id: string; name: string }> } {
  const gamesPath = path.join(__dirname, "..", "public", "data", "games.json");
  const content = readFileSync(gamesPath, "utf-8");
  return JSON.parse(content);
}

function getScenarioNumbersForGame(gameId: string): number[] {
  const snapshotsDir = path.join(__dirname, "..", "snapshots", gameId);
  if (!existsSync(snapshotsDir)) {
    return [];
  }
  const files = readdirSync(snapshotsDir);
  return files
    .filter((f) => f.startsWith("scenario-") && f.endsWith(".json"))
    .map((f) => parseInt(f.replace("scenario-", "").replace(".json", ""), 10))
    .sort((a, b) => a - b);
}

// ============================================================================
// Freshness Check
// ============================================================================

function checkSnapshotFreshness(
  gameId: string,
  scenarioNumber: number
): { isStale: boolean; snapshotTime: Date | null; dataTime: Date | null } {
  const snapshotPath = getSnapshotPath(gameId, scenarioNumber);
  const webDataPath = getWebDataPath(gameId);

  if (!existsSync(snapshotPath)) {
    return { isStale: true, snapshotTime: null, dataTime: null };
  }

  const snapshotStat = statSync(snapshotPath);
  const dataStat = statSync(webDataPath);

  return {
    isStale: snapshotStat.mtime < dataStat.mtime,
    snapshotTime: snapshotStat.mtime,
    dataTime: dataStat.mtime,
  };
}

// ============================================================================
// Prompt Building
// ============================================================================

function loadPromptTemplate(): string {
  const promptPath = path.join(__dirname, "eval-prompt.txt");
  return readFileSync(promptPath, "utf-8");
}

function buildEvalPrompt(
  rawData: ExtractedRawData,
  snapshot: unknown
): string {
  const template = loadPromptTemplate();

  const dataSection = `
## RAW TABLE DATA

\`\`\`json
${JSON.stringify(rawData, null, 2)}
\`\`\`

## DOM SNAPSHOT

\`\`\`json
${JSON.stringify(snapshot, null, 2)}
\`\`\`
`;

  return template + "\n\n" + dataSection;
}

// ============================================================================
// LLM Evaluation
// ============================================================================

function ensurePromptsDir(): void {
  const dir = path.join(__dirname, "..", "eval-prompts");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function savePromptToFile(
  gameId: string,
  scenarioNumber: number,
  prompt: string
): string {
  ensurePromptsDir();
  const filename = `${gameId}-s${scenarioNumber}.txt`;
  const promptPath = path.join(__dirname, "..", "eval-prompts", filename);
  writeFileSync(promptPath, prompt);
  return promptPath;
}

async function runLLMEvaluation(promptPath: string): Promise<EvalResult> {
  return new Promise((resolve) => {
    try {
      // Use copilot CLI with the prompt file
      const result = execSync(
        `cat "${promptPath}" | copilot --model claude-haiku-4.5 -s`,
        {
          encoding: "utf-8",
          maxBuffer: 10 * 1024 * 1024, // 10MB buffer
          timeout: 120000, // 2 minute timeout
        }
      );

      // Try to parse JSON from the response
      // The response might have text before/after the JSON
      const jsonMatch = result.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          const parsed = JSON.parse(jsonMatch[0]);
          resolve({
            pass: parsed.pass ?? false,
            unitCountMatch: parsed.unitCountMatch,
            issues: parsed.issues ?? [],
            missingUnits: parsed.missingUnits ?? [],
            extraUnits: parsed.extraUnits ?? [],
            summary: parsed.summary ?? "No summary provided",
          });
          return;
        } catch {
          // JSON parse failed
        }
      }

      // Could not parse JSON
      resolve({
        pass: false,
        issues: [],
        missingUnits: [],
        extraUnits: [],
        summary: "Could not parse LLM response as JSON",
        error: true,
        rawOutput: result.substring(0, MAX_RAW_OUTPUT_LENGTH),
      });
    } catch (err) {
      const error = err as Error;
      resolve({
        pass: false,
        issues: [],
        missingUnits: [],
        extraUnits: [],
        summary: `LLM evaluation failed: ${error.message}`,
        error: true,
      });
    }
  });
}

// ============================================================================
// Evaluation Execution
// ============================================================================

async function evaluateScenario(
  gameId: string,
  scenarioNumber: number
): Promise<ScenarioEvalOutput> {
  console.log(`  Evaluating ${gameId} scenario ${scenarioNumber}...`);
  const startTime = Date.now();

  // Check freshness
  const freshness = checkSnapshotFreshness(gameId, scenarioNumber);
  if (freshness.isStale) {
    console.log(`    ⚠ Snapshot is stale (older than web data)`);
  }

  // Load snapshot
  const snapshotData = loadSnapshot(gameId, scenarioNumber);
  if (!snapshotData) {
    return {
      gameId,
      scenarioNumber,
      evaluatedAt: new Date().toISOString(),
      evaluationDurationMs: Date.now() - startTime,
      snapshotGeneratedAt: "",
      snapshotStale: true,
      result: {
        pass: false,
        issues: [],
        missingUnits: [],
        extraUnits: [],
        summary: "Snapshot not found - run generate-snapshots first",
        error: true,
      },
    };
  }

  // Load raw data
  const rawData = extractRawScenarioData(gameId, scenarioNumber);
  if (!rawData) {
    return {
      gameId,
      scenarioNumber,
      evaluatedAt: new Date().toISOString(),
      evaluationDurationMs: Date.now() - startTime,
      snapshotGeneratedAt: snapshotData.generatedAt,
      snapshotStale: freshness.isStale,
      result: {
        pass: false,
        issues: [],
        missingUnits: [],
        extraUnits: [],
        summary: "Raw table data not found",
        error: true,
      },
    };
  }

  // Build prompt, save it, and run evaluation
  const prompt = buildEvalPrompt(rawData, snapshotData.snapshot);
  const promptPath = savePromptToFile(gameId, scenarioNumber, prompt);
  const result = await runLLMEvaluation(promptPath);

  const durationMs = Date.now() - startTime;
  const status = result.error ? "⚠" : result.pass ? "✓" : "✗";
  console.log(`    ${status} ${result.summary} (${(durationMs / 1000).toFixed(1)}s)`);

  return {
    gameId,
    scenarioNumber,
    evaluatedAt: new Date().toISOString(),
    evaluationDurationMs: durationMs,
    snapshotGeneratedAt: snapshotData.generatedAt,
    snapshotStale: freshness.isStale,
    result,
  };
}

async function evaluateGame(gameId: string): Promise<ScenarioEvalOutput[]> {
  console.log(`\nEvaluating ${gameId}...`);
  const scenarioNumbers = getScenarioNumbersForGame(gameId);

  if (scenarioNumbers.length === 0) {
    console.log(`  No snapshots found for ${gameId}`);
    return [];
  }

  const results: ScenarioEvalOutput[] = [];
  for (const num of scenarioNumbers) {
    const result = await evaluateScenario(gameId, num);
    results.push(result);
  }

  return results;
}

async function evaluateAll(): Promise<FullSuiteOutput> {
  const gamesIndex = loadGamesIndex();
  const allResults: ScenarioEvalOutput[] = [];

  for (const game of gamesIndex.games) {
    const gameResults = await evaluateGame(game.id);
    allResults.push(...gameResults);
  }

  const passed = allResults.filter((r) => r.result.pass && !r.result.error).length;
  const errors = allResults.filter((r) => r.result.error).length;
  const failed = allResults.length - passed - errors;

  return {
    evaluatedAt: new Date().toISOString(),
    totalScenarios: allResults.length,
    passed,
    failed,
    errors,
    scenarios: allResults,
  };
}

// ============================================================================
// Output
// ============================================================================

function ensureResultsDir(): void {
  const dir = path.join(__dirname, "..", "eval-results");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function writeScenarioResult(result: ScenarioEvalOutput): void {
  ensureResultsDir();
  const filename = `${result.gameId}-s${result.scenarioNumber}.json`;
  const resultPath = path.join(__dirname, "..", "eval-results", filename);
  writeFileSync(resultPath, JSON.stringify(result, null, 2));
  console.log(`    Wrote ${resultPath}`);
}

function writeFullSuiteResult(result: FullSuiteOutput): void {
  ensureResultsDir();
  const date = new Date().toISOString().split("T")[0];
  const filename = `${date}-full.json`;
  const resultPath = path.join(__dirname, "..", "eval-results", filename);
  writeFileSync(resultPath, JSON.stringify(result, null, 2));
  console.log(`\nWrote full suite results to ${resultPath}`);
}

// ============================================================================
// CLI
// ============================================================================

function parseArgs(): { all: boolean; game?: string; scenario?: number } {
  const args = process.argv.slice(2);
  const result: { all: boolean; game?: string; scenario?: number } = {
    all: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--all") {
      result.all = true;
    } else if (arg === "--game" && args[i + 1]) {
      result.game = args[++i];
    } else if (arg === "--scenario" && args[i + 1]) {
      result.scenario = parseInt(args[++i], 10);
    }
  }

  return result;
}

async function main(): Promise<void> {
  const args = parseArgs();

  if (args.all) {
    console.log("Running LLM evaluation for all games...");
    const result = await evaluateAll();
    writeFullSuiteResult(result);

    console.log("\n=== Summary ===");
    console.log(`Total: ${result.totalScenarios}`);
    console.log(`Passed: ${result.passed}`);
    console.log(`Failed: ${result.failed}`);
    console.log(`Errors: ${result.errors}`);
  } else if (args.game && args.scenario) {
    const result = await evaluateScenario(args.game, args.scenario);
    writeScenarioResult(result);
  } else if (args.game) {
    const results = await evaluateGame(args.game);
    for (const result of results) {
      writeScenarioResult(result);
    }
  } else {
    console.log("Usage:");
    console.log("  npx tsx scripts/llm-eval.ts --all");
    console.log("  npx tsx scripts/llm-eval.ts --game <id>");
    console.log("  npx tsx scripts/llm-eval.ts --game <id> --scenario <num>");
    process.exit(1);
  }

  console.log("\n✓ LLM evaluation complete");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
