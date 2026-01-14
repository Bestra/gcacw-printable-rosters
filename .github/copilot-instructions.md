# Copilot Instructions

Operational guide for working on this codebase.

Do not use CLAUDE.md, as it won't be included in every prompt like this file is.

## Python

**CRITICAL: Always use `uv run python` to execute Python. Never use bare `python`, `python3`, or `pip`.**

**CRITICAL: Avoid shell quoting issues with complex Python code:**

- ✅ Use `create_file` tool to create a `.py` file, then run it with `uv run python script.py`
- ✅ `uv run python -c "print('hello')"` (simple one-liners only)
- ❌ NEVER use `uv run python -c` with complex Python code containing nested quotes
- ❌ NEVER use heredoc (`cat > file.py << 'EOF'`) - terminal buffering corrupts the output

**Why heredocs fail:** Terminal output is captured in chunks and heredoc content gets garbled, duplicated, or truncated. Always use `create_file` tool instead.

Examples:

- ✅ `create_file` tool → `uv run python script.py`
- ✅ `uv run python -c "print('hello')"` (simple one-liners only)
- ❌ `python3 script.py` (wrong Python)
- ❌ `cat > temp.py << 'EOF'` (heredoc - will fail)
- ❌ `echo 'import json...' > temp.py` (quoting nightmare)
- ❌ `uv run python -c "import json; data['key']..."` (nested quotes will fail)

## Commands

```bash
# Build pipeline (preferred)
make              # Build all web JSON files
make gtc2         # Build a single game
make reparse-otr2 # Force rebuild a game
make dev          # Start dev server (localhost:5173)
make build        # Production build

# Parser (always use uv, never bare python/pip)
cd parser && uv run python pipeline/parse_raw_tables.py --all   # Parse all games
cd parser && uv run python pipeline/convert_to_web.py           # Generate web JSON

# LLM evaluation (DOM snapshot testing)
make snapshots                              # Generate DOM snapshots for all games
make snapshots-game GAME=gtc2               # Snapshots for one game
make snapshots-single GAME=gtc2 SCENARIO=1  # Single snapshot
make llm-eval                               # Run LLM evaluation (all scenarios)
make llm-eval-single GAME=gtc2 SCENARIO=1   # Single scenario eval
```

## Dev Server

**When the dev server is running, do NOT restart it or run `make build`.**

Vite provides hot module replacement (HMR) - changes to `.tsx`, `.ts`, and `.css` files are automatically reflected in the browser without any action needed. Just edit the file and save.

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
PDF → pipeline/raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              pipeline/parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              pipeline/convert_to_web.py → web/public/data/{game}.json
                                       ↓
                              Web app fetches at runtime
```

## Architecture

**Parser** (`parser/`)

- `pipeline/raw_table_extractor.py` - Extracts raw table structure from PDFs
- `game_configs.json` - Data-driven column mappings per game/table
- `pipeline/parse_raw_tables.py` - Parses raw tables into structured units
- `pipeline/convert_to_web.py` - Transforms snake_case → camelCase for web
- `utils/` - Inspection and debugging utilities
- `image_extraction/` - Counter image extraction from VASSAL modules
- `raw/` - Raw table JSON files (preserved for debugging)
- `parsed/` - Structured unit data per game

**Web** (`web/`)

- `App.tsx` - Loads games.json, then game data, manages selection state
- `RosterSheet.tsx` - Grid of UnitCards, footnotes legend, conventions key
- `UnitCard.tsx` - Single unit with 3 counter boxes
- `types.ts` - TypeScript interfaces (Unit, Scenario, GameData)

## Implementation Details

### UnitCard display logic

- Leaders (type="Ldr") excluded from roster grid
- Leader names shown on subordinate units: `[bracketed]` = same hex, plain = different hex
- Starting fatigue: parsed from footnotes matching "Fatigue Level X"
- Location names: extracted from hex parentheticals like "S5510 (Yorktown)"

### Parser details

- Special units (Gunboat, Wagon Train, Naval Battery) parsed with `unit_type="Special"`
- Footnote symbols: \*, ^, †, ‡, §, $, +
- Column layouts are configured per-game in `game_configs.json`

### Adding a new game

See `parser/RAW_TABLE_EXTRACTOR.md` for detailed instructions.

Quick summary:

1. Extract raw tables: `make extract-newgame` (or manually run pipeline/raw_table_extractor.py)
2. Add column config to `game_configs.json` if needed
3. Add game to `GAMES` list in `pipeline/convert_to_web.py`
4. Add game to `ALL_GAMES` in `Makefile`
5. Add URL slug mapping in `web/src/utils/slugs.ts`
6. Build: `make newgame`

## Data Inspection Utilities

Utility scripts for debugging and inspecting data at each pipeline stage:

```bash
# Inspect raw table data (from PDF extraction)
cd parser && uv run python utils/inspect_raw.py gtc2
cd parser && uv run python utils/inspect_raw.py gtc2 --scenario 1
cd parser && uv run python utils/inspect_raw.py gtc2 --scenario 1 --table "Confederate Set-Up"

# Inspect parsed unit data (after parse_raw_tables.py)
cd parser && uv run python utils/inspect_parsed.py gtc2
cd parser && uv run python utils/inspect_parsed.py gtc2 --scenario 1
cd parser && uv run python utils/inspect_parsed.py gtc2 --scenario 1 --side Confederate
cd parser && uv run python utils/inspect_parsed.py gtc2 --scenario 1 --filter Longstreet

# Compare raw vs parsed data (for debugging parsing issues)
cd parser && uv run python utils/compare_data.py gtc2 1
cd parser && uv run python utils/compare_data.py gtc2 1 --side Union
cd parser && uv run python utils/compare_data.py gtc2 1 --table "Union Set-Up" --row 5
```

All scripts support `--help` for full usage details.

**Data structure documentation**: See the [data-structures skill](.github/skills/data-structures/SKILL.md) for detailed information about raw, parsed, and web JSON structures.

## Validation

Validate changes by:

1. `make build` (catches TypeScript errors)
2. `make test` (runs parser + web unit tests)
3. Visual inspection in browser
4. Check parsed JSON output for parser changes
5. Use `utils/inspect_raw.py`, `utils/inspect_parsed.py`, or `utils/compare_data.py` to verify data
6. `make snapshots && make llm-eval` for LLM-powered integration testing (compares raw PDF data to rendered DOM)
