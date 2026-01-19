# Agent Instructions

Operational guide for working on this codebase.

## Pre-flight Checks

Before diving in, verify:

- **Dev server running?** If yes, don't restart it—Vite HMR handles changes automatically
- **Right directory?** Parser commands need `cd parser` first
- **Parser changes?** You'll need to regenerate data afterward (`make` or `make {game}`)

## Critical Rules

### Python: Always use `uv run`

```bash
# ✅ Correct
uv run python script.py
uv run python -c "print('hello')"

# ❌ Wrong - will use system Python
python3 script.py
pip install something
```

### Complex Python: Use create_file tool

Terminal buffering corrupts heredocs and complex quoting. Always:

1. Use `create_file` tool to write a `.py` file
2. Run it with `uv run python script.py`
3. Delete when done

```bash
# ❌ These WILL fail
cat > temp.py << 'EOF'           # Heredoc - gets garbled
echo 'import json...' > temp.py  # Quoting nightmare
uv run python -c "data['key']"   # Nested quotes break
```

## Commands

```bash
# Build (most common)
make              # Build all web JSON
make gtc2         # Build single game
make dev          # Dev server (localhost:5173)
make build        # Production build
make test         # Run all tests

# Parser
cd parser && uv run python pipeline/parse_raw_tables.py --all
cd parser && uv run python pipeline/convert_to_web.py

# LLM eval
make snapshots                              # Generate DOM snapshots
make llm-eval                               # Run LLM evaluation
make llm-eval-single GAME=gtc2 SCENARIO=1   # Single scenario
```

## Dev Server

**When the dev server is running, do NOT restart it or run `make build`.**

Vite HMR handles `.tsx`, `.ts`, and `.css` changes automatically.

## File Locations

| To change...                            | Edit...                                             |
| --------------------------------------- | --------------------------------------------------- |
| Unit card layout/styling                | `web/src/components/UnitCard.tsx` + `.css`          |
| Grid layout, footnotes, conventions key | `web/src/components/RosterSheet.tsx` + `.css`       |
| Game/scenario selection                 | `web/src/App.tsx`                                   |
| TypeScript types                        | `web/src/types.ts`                                  |
| Raw PDF extraction                      | `parser/pipeline/raw_table_extractor.py`            |
| Column mappings & game config           | `parser/game_configs.json`                          |
| Raw table → unit parsing                | `parser/pipeline/parse_raw_tables.py`               |
| Parsed → web JSON transform             | `parser/pipeline/convert_to_web.py`                 |
| Games list                              | `GAMES` list in `parser/pipeline/convert_to_web.py` |
| DOM snapshot generator                  | `web/scripts/generate-snapshots.test.tsx`           |
| LLM eval orchestrator                   | `web/scripts/llm-eval.ts`                           |
| LLM eval prompt template                | `web/scripts/eval-prompt.txt`                       |

## Data Flow

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json
```

### PDF and VASSAL Module Paths

Configure in `parser/.env`. See [parser/.env.example](parser/.env.example) for variable names.

## Architecture

**Parser** (`parser/`)

- `pipeline/` - Three-stage extraction pipeline (raw → parsed → web)
- `game_configs.json` - Column mappings per game/table
- `utils/` - Inspection and debugging utilities
- `image_extraction/` - Counter images from VASSAL modules

**Web** (`web/`)

- `App.tsx` - Game/scenario selection
- `RosterSheet.tsx` - Grid of UnitCards, footnotes, conventions
- `UnitCard.tsx` - Single unit display
- `types.ts` - TypeScript interfaces

## Implementation Details

### UnitCard display logic

- Leaders (type="Ldr") excluded from roster grid
- Leader names on units: `[bracketed]` = same hex, plain = different hex
- Starting fatigue: parsed from footnotes matching "Fatigue Level X"
- Location names: from hex parentheticals like "S5510 (Yorktown)"

### Parser details

- Special units (Gunboat, Wagon Train, Naval Battery) → `unit_type="Special"`
- Footnote symbols: \*, ^, †, ‡, §, $, +
- Column layouts configured per-game in `game_configs.json`

### JSON Structure Quick Reference (for jq)

**CRITICAL**: Parsed and web JSON have **different structures**:

| Aspect          | Parsed JSON (`parsed/*.json`)      | Web JSON (`web/public/data/*.json`) |
| --------------- | ---------------------------------- | ----------------------------------- |
| Root structure  | Array `[...]`                      | Object `{scenarios: [...]}`         |
| Access scenario | `.[1]` (0-indexed)                 | `.scenarios[1]` (0-indexed)         |
| Field naming    | `snake_case`                       | `camelCase`                         |
| Unit name field | `unit_leader`                      | `name`                              |
| Units arrays    | `confederate_units`, `union_units` | `confederateUnits`, `unionUnits`    |
| Hex location    | `hex_location`                     | `hexLocation`                       |

**Common jq patterns:**

```bash
# Parsed JSON - scenario 2 union units containing "Wagon"
cat parsed/hsn_parsed.json | jq '.[1].union_units[] | select(.unit_leader | contains("Wagon"))'

# Web JSON - same query
cat web/public/data/hsn.json | jq '.scenarios[1].unionUnits[] | select(.name | contains("Wagon"))'
```

## Validation

Validate changes by:

1. `make build` (catches TypeScript errors)
2. `make test` (runs parser + web unit tests)
3. Visual inspection in browser
4. Check parsed JSON output for parser changes
5. Use `utils/inspect_raw.py`, `utils/inspect_parsed.py`, or `utils/compare_data.py` to verify data
6. `make snapshots && make llm-eval` for LLM-powered integration testing (compares raw PDF data to rendered DOM)

## Skills (Task-Specific Guidance)

These skills are loaded conditionally based on the task. Reference them for detailed workflows:

| Skill                                                                  | When to use                                                       |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [parse-new-game](.github/skills/parse-new-game/SKILL.md)               | Adding a new GCACW game to the system                             |
| [data-structures](.github/skills/data-structures/SKILL.md)             | Understanding JSON schemas, field mappings, debugging data issues |
| [regenerate-data](.github/skills/regenerate-data/SKILL.md)             | Refreshing data after parser changes                              |
| [debug-pdf-extraction](.github/skills/debug-pdf-extraction/SKILL.md)   | Fixing garbled text or missing units from PDF                     |
| [extract-vassal-images](.github/skills/extract-vassal-images/SKILL.md) | Adding counter images from VASSAL modules                         |
| [troubleshooting](.github/skills/troubleshooting/SKILL.md)             | Diagnosing bugs, fixing test failures, common mistakes            |
