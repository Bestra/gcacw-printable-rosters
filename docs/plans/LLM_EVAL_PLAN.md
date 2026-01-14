# LLM-Powered Raw-to-DOM Integration Test

Build an offline integration test with a two-phase workflow: (1) generate and persist DOM snapshots, (2) run LLM evaluation against saved snapshots. Snapshots are committed for regression tracking. Evaluator warns if snapshots are stale.

## Status: ✅ Complete (January 2026)

## Overview

Use `copilot --model claude-haiku-4.5 -p "<prompt>" -s` to evaluate whether raw table data from PDFs correctly renders in the DOM. Supports full suite or single scenario evaluation, outputs JSON findings.

## Implementation

### 1. DOM Snapshot Generator (`web/scripts/generate-snapshots.test.tsx`)

- Renders `RosterSheet` for each game/scenario using vitest + React Testing Library
- Extracts structured JSON from rendered DOM: units, leaders, footnotes, command groups
- Writes to `web/snapshots/{game}/scenario-{num}.json`
- Run via: `npm run snapshots` or `make snapshots`

### 2. Raw Table Extractor (`web/scripts/extract-raw-json.ts`)

- Reads `parser/raw/{game}_raw_tables.json` and returns scenario tables as structured JSON
- Used by orchestrator at eval time (raw files already persisted in repo)

### 3. Prompt Template (`web/scripts/eval-prompt.txt`)

- Instructions for comparing raw tables to DOM output
- Requests structured response with pass/fail, issues, missing/extra units, summary

### 4. Evaluation Orchestrator (`web/scripts/llm-eval.ts`)

- Reads DOM from `web/snapshots/`, raw from `parser/raw/`
- **Freshness check**: Compares snapshot mtime vs `web/public/data/{game}.json` mtime; warns if snapshot is older
- CLI: `--game <id> --scenario <num>` (single) or `--all` (full suite)
- Spawns `copilot --model claude-haiku-4.5 -p "$PROMPT" -s`
- On malformed response: logs raw output, marks `"error": true`, continues
- Writes to `web/eval-results/{game}-s{scenario}.json` or `web/eval-results/YYYY-MM-DD-full.json`

### 5. npm Scripts (`web/package.json`)

```json
{
  "snapshots": "vitest run scripts/generate-snapshots.test.tsx",
  "snapshots:game": "SNAPSHOT_GAME=$npm_config_game vitest run scripts/generate-snapshots.test.tsx",
  "llm-eval": "npx tsx scripts/llm-eval.ts --all",
  "llm-eval:single": "npx tsx scripts/llm-eval.ts"
}
```

### 6. Makefile Targets

```makefile
make snapshots                              # Regenerate all DOM snapshots
make snapshots-game GAME=gtc2               # Snapshots for one game
make snapshots-single GAME=gtc2 SCENARIO=1  # Single snapshot
make llm-eval                               # Run full LLM evaluation
make llm-eval-single GAME=gtc2 SCENARIO=1   # Single scenario eval
```

### 7. Gitignore

Only `.eval-prompt-temp.txt` is gitignored (temporary file during evaluation). Eval results are committed for tracking.

## File Structure

```
web/
  scripts/
    generate-snapshots.test.tsx  # Vitest-based DOM snapshot generator
    extract-raw-json.ts          # Raw table extraction helper
    llm-eval.ts                  # Orchestrator with freshness check
    eval-prompt.txt              # Prompt template
  snapshots/                     # Committed DOM snapshots
    gtc2/
      scenario-1.json
      scenario-2.json
    ...
  eval-results/                  # Committed LLM evaluation results
    gtc2-s1.json                 # Per-scenario results
    2026-01-13-full.json         # Full suite run results
```

## Usage

```bash
# Generate snapshots for all games (run after data changes)
make snapshots

# Generate snapshots for a single game
make snapshots-game GAME=gtc2

# Generate snapshot for a single scenario
make snapshots-single GAME=gtc2 SCENARIO=1

# Run LLM evaluation across all scenarios
make llm-eval

# Evaluate a single scenario
make llm-eval-single GAME=gtc2 SCENARIO=1
```

## Example Output

```json
{
  "gameId": "gtc2",
  "scenarioNumber": 1,
  "snapshotStale": false,
  "result": {
    "pass": false,
    "unitCountMatch": {
      "raw": { "confederate": 23, "union": 33 },
      "dom": { "confederate": 22, "union": 32 },
      "matches": false
    },
    "issues": [
      {
        "side": "confederate",
        "unit": "Stuart",
        "field": "leader_missing",
        "severity": "critical"
      }
    ],
    "summary": "Two cavalry corps leaders missing from DOM..."
  }
}
```

## Design Decisions

- **Commit snapshots**: Small JSON files serve as regression baselines and enable CI diffing
- **Vitest-based generator**: Leverages existing test infrastructure for CSS handling and jsdom
- **Timestamp freshness check**: Warns if snapshots are older than source data files
- **Haiku model**: Cost-effective for structured comparison tasks (~$0.10-0.50 per full run)
- **Error handling**: Log malformed LLM responses and continue; manual review for edge cases
- **Decoupled workflow**: Snapshot generation is separate from evaluation, enabling prompt iteration without re-rendering
