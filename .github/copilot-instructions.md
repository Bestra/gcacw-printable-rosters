# Copilot Instructions

Operational guide for working on this codebase.

## Python

- Always use `uv` to run Python scripts, never bare `python` or `pip`.

## Commands

```bash
# Web app
cd web && npm run dev      # Dev server at localhost:5173
cd web && npm run build    # Build to web/dist/

# Parser (always use uv, never bare python/pip)
cd parser && uv run python scenario_parser.py ../data/SomeGame.pdf [game_id]
cd parser && uv run python convert_to_web.py
```

## File Locations

| To change...                            | Edit...                                                  |
| --------------------------------------- | -------------------------------------------------------- |
| Unit card layout/styling                | `web/src/components/UnitCard.tsx` + `.css`               |
| Grid layout, footnotes, conventions key | `web/src/components/RosterSheet.tsx` + `.css`            |
| Game/scenario selection                 | `web/src/App.tsx`                                        |
| TypeScript types                        | `web/src/types.ts`                                       |
| PDF parsing logic                       | `parser/scenario_parser.py`                              |
| Parser → web JSON transform             | `parser/convert_to_web.py`                               |
| Scenario names for a game               | `SCENARIO_NAMES` dict in `scenario_parser.py` (~line 40) |
| Games list                              | `GAMES` list in `convert_to_web.py`                      |

## Data Flow

```
PDF → scenario_parser.py → {game_id}_scenarios.json (snake_case)
                         ↓
                   convert_to_web.py
                         ↓
              web/public/data/{game_id}.json (camelCase)
                         ↓
                   Web app fetches at runtime
```

## Architecture

**Parser** (`parser/`)

- `scenario_parser.py` - Extracts units from PDF tables using pdfplumber
- `convert_to_web.py` - Transforms snake_case → camelCase for web
- Outputs: `{game_id}_scenarios.json`, `web/public/data/{game_id}.json`

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

### Parser quirks

- Handles `(cntd)` continuation tables across pages
- Special units (Gunboat, Wagon Train, Naval Battery) parsed with `unit_type="Special"`
- Footnote symbols: \*, ^, †, ‡, §, $, +
- Scenario names are hardcoded per-game in `SCENARIO_NAMES` dict

### Adding a new game

1. **Verify scenario names from the PDF first.** Run this to see what the parser finds:

   ```bash
   cd parser && uv run python -c '
   import pdfplumber, re
   with pdfplumber.open("../data/NewGame.pdf") as pdf:
       for i, page in enumerate(pdf.pages[3:], start=4):
           text = page.extract_text() or ""
           for line in text.split("\n")[:15]:
               if re.search(r"scenario\s+\d+:", line, re.IGNORECASE):
                   print(f"Page {i}: {line.strip()[:80]}")
   '
   ```

   PDF extraction is unreliable—scenario titles often merge with adjacent text. Cross-reference against the actual PDF to get correct names.

2. Add scenario names to `SCENARIO_NAMES` in `scenario_parser.py`
3. Add game config to `GAMES` in `convert_to_web.py`
4. Run: `uv run python scenario_parser.py ../data/NewGame.pdf newgame`
5. Run: `uv run python convert_to_web.py`

## Validation

No automated tests. Validate changes by:

1. `npm run build` in web/ (catches TypeScript errors)
2. Visual inspection in browser
3. Check parsed JSON output for parser changes
