# Copilot Instructions

Operational guide for working on this codebase.

## Python

**CRITICAL: Always use `uv run python` to execute Python. Never use bare `python`, `python3`, or `pip`.**

Examples:

- ✅ `cd parser && uv run python script.py`
- ✅ `uv run python -c "print('hello')"`
- ❌ `python3 script.py`
- ❌ `python -c "..."`

## Commands

```bash
# Web app
cd web && npm run dev      # Dev server at localhost:5173
cd web && npm run build    # Build to web/dist/

# Parser (always use uv, never bare python/pip)
cd parser && uv run python parse_raw_tables.py --all   # Parse all games
cd parser && uv run python convert_to_web.py           # Generate web JSON
```

## File Locations

| To change...                            | Edit...                                       |
| --------------------------------------- | --------------------------------------------- |
| Unit card layout/styling                | `web/src/components/UnitCard.tsx` + `.css`    |
| Grid layout, footnotes, conventions key | `web/src/components/RosterSheet.tsx` + `.css` |
| Game/scenario selection                 | `web/src/App.tsx`                             |
| TypeScript types                        | `web/src/types.ts`                            |
| Raw PDF extraction                      | `parser/raw_table_extractor.py`               |
| Column mappings & game config           | `parser/game_configs.json`                    |
| Raw table → unit parsing                | `parser/parse_raw_tables.py`                  |
| Parsed → web JSON transform             | `parser/convert_to_web.py`                    |
| Games list                              | `GAMES` list in `convert_to_web.py`           |

## Data Flow

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json
                                       ↓
                              Web app fetches at runtime
```

## Architecture

**Parser** (`parser/`)

- `raw_table_extractor.py` - Extracts raw table structure from PDFs
- `game_configs.json` - Data-driven column mappings per game/table
- `parse_raw_tables.py` - Parses raw tables into structured units
- `convert_to_web.py` - Transforms snake_case → camelCase for web
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

1. Extract raw tables: `uv run python raw_table_extractor.py ../data/NewGame.pdf newgame`
2. Add column config to `game_configs.json` if needed
3. Add game to `GAMES` list in `convert_to_web.py`
4. Add URL slug mapping in `web/src/utils/slugs.ts`
5. Parse: `uv run python parse_raw_tables.py newgame`
6. Convert: `uv run python convert_to_web.py`

## Validation

No automated tests. Validate changes by:

1. `npm run build` in web/ (catches TypeScript errors)
2. Visual inspection in browser
3. Check parsed JSON output for parser changes
