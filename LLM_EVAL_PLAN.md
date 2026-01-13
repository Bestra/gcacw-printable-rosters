# LLM-Powered Raw-to-DOM Integration Test

Build an offline integration test with a two-phase workflow: (1) generate and persist DOM snapshots, (2) run LLM evaluation against saved snapshots. Snapshots are committed for regression tracking. Evaluator warns if snapshots are stale.

## Overview

Use `copilot --model claude-haiku-4.5 -p "<prompt>" -s` to evaluate whether raw table data from PDFs correctly renders in the DOM. Supports full suite or single scenario evaluation, outputs JSON findings.

## Implementation Steps

### 1. DOM Snapshot Generator (`web/scripts/generate-snapshots.ts`)

- Renders `RosterSheet` for each game/scenario using jsdom + React Testing Library
- Extracts structured JSON: `{ generatedAt: ISO timestamp, units: [...], footnotes: {...}, leaders: [...] }`
- Writes to `web/snapshots/{game}/scenario-{num}.json`
- CLI: `--game <id>` (one game), `--all` (all games), or `--game <id> --scenario <num>` (single)

### 2. Raw Table Extractor (`web/scripts/extract-raw-json.ts`)

- Reads `parser/raw/{game}_raw_tables.json` and returns scenario tables as structured JSON
- Used by orchestrator at eval time (raw files already persisted in repo)

### 3. Prompt Template (`web/scripts/eval-prompt.txt`)

- Instructions for comparing raw tables to DOM output
- Requests structured response:
  ```json
  {
    "pass": boolean,
    "issues": [{ "unit": "...", "field": "...", "expected": "...", "actual": "..." }],
    "summary": "..."
  }
  ```

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
  "snapshots": "npx tsx scripts/generate-snapshots.ts --all",
  "snapshots:single": "npx tsx scripts/generate-snapshots.ts",
  "llm-eval": "npx tsx scripts/llm-eval.ts --all",
  "llm-eval:single": "npx tsx scripts/llm-eval.ts"
}
```

### 6. Makefile Targets

```makefile
make snapshots                              # Regenerate all DOM snapshots
make snapshots-single GAME=gtc2 SCENARIO=1  # Single snapshot
make llm-eval                               # Run full LLM evaluation
make llm-eval-single GAME=gtc2 SCENARIO=1   # Single scenario eval
```

### 7. Gitignore

Add `web/eval-results/` to `.gitignore` (evaluation outputs are ephemeral, not committed).

## File Structure

```
web/
  scripts/
    generate-snapshots.ts  # Render → JSON snapshots
    extract-raw-json.ts    # Raw table extraction helper
    llm-eval.ts            # Orchestrator with freshness check
    eval-prompt.txt        # Prompt template
  snapshots/               # Committed DOM snapshots
    gtc2/
      scenario-1.json
      scenario-2.json
    ...
  eval-results/            # Gitignored LLM outputs
```

## Usage

```bash
# Generate snapshots for all games (run after data changes)
make snapshots

# Generate snapshot for a single scenario
make snapshots-single GAME=gtc2 SCENARIO=1

# Run LLM evaluation across all scenarios
make llm-eval

# Evaluate a single scenario
make llm-eval-single GAME=gtc2 SCENARIO=1
```

## Design Decisions

- **Commit snapshots**: Small JSON files serve as regression baselines and enable CI diffing
- **Timestamp freshness check**: Warns if snapshots are older than source data files
- **Haiku model**: Cost-effective for structured comparison tasks (~$0.10-0.50 per full run)
- **Error handling**: Log malformed LLM responses and continue; manual review for edge cases
- **Decoupled workflow**: Snapshot generation is separate from evaluation, enabling prompt iteration without re-rendering
