# Raw Table Extractor

## Current State (Jan 2026)

**Status: Fully Integrated** - All games extracted, parsed, and feeding the web app.

| Game | Raw Tables                 | Parsed Units              | Web Output                  | Status  |
| ---- | -------------------------- | ------------------------- | --------------------------- | ------- |
| OTR2 | `raw/otr2_raw_tables.json` | `parsed/otr2_parsed.json` | `web/public/data/otr2.json` | ✅ Live |
| RTG2 | `raw/rtg2_raw_tables.json` | `parsed/rtg2_parsed.json` | `web/public/data/rtg2.json` | ✅ Live |
| GTC2 | `raw/gtc2_raw_tables.json` | `parsed/gtc2_parsed.json` | `web/public/data/gtc2.json` | ✅ Live |
| HCR  | `raw/hcr_raw_tables.json`  | `parsed/hcr_parsed.json`  | `web/public/data/hcr.json`  | ✅ Live |
| HSN  | `raw/hsn_raw_tables.json`  | `parsed/hsn_parsed.json`  | `web/public/data/hsn.json`  | ✅ Live |
| RTW  | `raw/rtw_raw_tables.json`  | `parsed/rtw_parsed.json`  | `web/public/data/rtw.json`  | ✅ Live |

---

## Architecture

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json
```

**Phase 1**: Extract raw table structure from PDFs (preserves tokens for verification)
**Phase 2**: Parse raw tables into structured units using data-driven config

---

## File Locations

- **PDFs**: `data/{GAME}_Rules.pdf` (e.g., `data/RTG2_Rules.pdf`)
- **Raw tables**: `parser/raw/{game}_raw_tables.json`
- **Game configs**: `parser/game_configs.json`
- **Parsed units**: `parser/parsed/{game}_parsed.json`

## Usage

```bash
cd parser

# Extract raw tables from PDF (Phase 1 - already done)
uv run python raw_table_extractor.py ../data/RTG2_Rules.pdf rtg2

# Parse raw tables into units (Phase 2)
uv run python parse_raw_tables.py otr2      # Single game
uv run python parse_raw_tables.py --all     # All games
```

## How to Verify a Scenario

For each scenario, check the `raw/{game}_raw_tables.json` file:

1. **Tables found**: Are all expected tables present? (Set-Up, Reinforcements, etc.)
2. **Table names**: Are names correct, not corrupted with extra text?
3. **Row counts**: Do row counts seem reasonable for the scenario?
4. **Annotations**: Are footnote symbols (\*, ^, †) captured with their text?

Quick check script:

```bash
cd parser && uv run python -c "
import json
with open('raw/{game}_raw_tables.json') as f:
    data = json.load(f)
for s in data:
    print(f\"Scenario {s['scenario_number']}: {s['scenario_name']}\")
    print(f\"  CSA tables: {len(s['confederate_tables'])}\")
    print(f\"  Union tables: {len(s['union_tables'])}\")
"
```

## Output Format

Each scenario contains:

- **Table names** (e.g., "Union Set-Up", "Army Of The Potomac First Increment")
- **Page numbers** where each table appears
- **Raw row values** as token arrays (not yet parsed into unit fields)
- **Annotations/footnotes** per table
- **Per-side groupings** (Confederate tables vs Union tables)

```json
{
  "scenario_number": 10,
  "scenario_name": "The Gettysburg Campaign",
  "start_page": 77,
  "end_page": 95,
  "confederate_tables": [
    {
      "name": "Confederate Set-Up",
      "page_numbers": [81],
      "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
      "rows": [
        ["A.", "Jenkins", "Brig", "Cav", "Cav", "3", "S0608", "(Middleburg)"],
        ...
      ],
      "annotations": {}
    },
    {
      "name": "Placed Upon Stuart's Arrival",
      "page_numbers": [81],
      "rows": [...],
      "annotations": {"^": "May delay entry (see advanced rule 7.0)"}
    }
  ],
  "union_tables": [...]
}
```

---

## Verification Status

### Legend

- ✅ Verified correct
- ⚠️ Has known issues (see notes)
- ❌ Not yet extracted
- ⬜ Not yet checked

### OTR2 (On to Richmond 2nd Ed) - 9 scenarios

| #   | Scenario               | Status | Notes                                             |
| --- | ---------------------- | ------ | ------------------------------------------------- |
| 1   | The Warwick Line       | ✅     | 15 CSA rows, 15 Union rows                        |
| 2   | Johnston's Retreat     | ✅     | 20 CSA rows, 20 Union rows                        |
| 3   | The Gates of Richmond  | ✅     | 36 CSA rows, 35 Union rows                        |
| 4   | Seven Pines            | ✅     | 15 CSA rows, 11 Union rows                        |
| 5   | Stuart's Ride          | ✅     | 3 CSA rows, 8 Union rows                          |
| 6   | The Seven Days         | ✅     | 38 CSA rows, 38 Union rows                        |
| 7   | Gaines Mill            | ✅     | 19 CSA rows, 17 Union rows                        |
| 8   | Retreat to the James   | ✅     | 25 CSA rows, 27 Union rows                        |
| 9   | The Peninsula Campaign | ✅     | 4 CSA tables (172 rows), 4 Union tables (98 rows) |

### RTG2 (Roads to Gettysburg 2nd Ed) - 10 scenarios

| #   | Scenario                       | Status | Notes                                             |
| --- | ------------------------------ | ------ | ------------------------------------------------- |
| 1   | Meade Moves North              | ⬜     |                                                   |
| 2   | Stuart Rides North             | ⬜     |                                                   |
| 3   | Confederate High Tide          | ⬜     |                                                   |
| 4   | First Day at Gettysburg        | ⬜     |                                                   |
| 5   | Battle of Gettysburg           | ⬜     |                                                   |
| 6   | The Pipe Creek Plan            | ⬜     |                                                   |
| 7   | The Battle Continues           | ⬜     |                                                   |
| 8   | The Wagoneer's Fight           | ⬜     |                                                   |
| 9   | The Battle that Never Happened | ⬜     |                                                   |
| 10  | The Gettysburg Campaign        | ✅     | 4 CSA tables, 7 Union tables, annotations correct |

### GTC2 (Grant Takes Command 2nd Ed) - 12 scenarios

| #   | Scenario                     | Status | Notes                      |
| --- | ---------------------------- | ------ | -------------------------- |
| 1   | The Battle of the Wilderness | ✅     | 23 CSA rows, 33 Union rows |
| 2   | Grant Crosses the Rapidan    | ✅     | 26 CSA rows, 43 Union rows |
| 3   | Race for Spotsylvania        | ✅     | 10 CSA rows, 12 Union rows |
| 4   | Bloody Spotsylvania          | ✅     | 23 CSA rows, 32 Union rows |
| 5   | Sheridan Rides South         | ✅     | 10 CSA rows, 11 Union rows |
| 6   | Strike Them a Blow!          | ✅     | 22 CSA rows, 23 Union rows |
| 7   | Bethesda Church              | ✅     | 25 CSA rows, 33 Union rows |
| 8   | Trevilian Station            | ✅     | 7 CSA rows, 8 Union rows   |
| 9   | The Overland Campaign        | ✅     | 60 CSA rows, 65 Union rows |
| 10  | Marching to Cold Harbor      | ✅     | 43 CSA rows, 58 Union rows |
| 11  | Grant's 1864 Offensive       | ✅     | 65 CSA rows, 66 Union rows |
| 12  | If It Takes All Summer       | ✅     | 51 CSA rows, 61 Union rows |

### HCR (Here Come the Rebels) - 8 scenarios

| #   | Scenario                     | Status | Notes                      |
| --- | ---------------------------- | ------ | -------------------------- |
| 1   | South Mountain               | ✅     | 9 CSA rows, 10 Union rows  |
| 2   | Harpers Ferry – Crampton Gap | ✅     | 14 CSA rows, 12 Union rows |
| 3   | McClellan's Opportunity      | ✅     | 22 CSA rows, 30 Union rows |
| 4   | Three Cigars                 | ✅     | 24 CSA rows, 39 Union rows |
| 5   | The Baltimore Raid           | ✅     | 4 CSA rows, 11 Union rows  |
| 6   | The Battle for Washington    | ✅     | 17 CSA rows, 20 Union rows |
| 7   | From Frederick to Sharpsburg | ✅     | 20 CSA rows, 39 Union rows |
| 8   | The Maryland Campaign        | ✅     | 18 CSA rows, 61 Union rows |

### HSN (Hood Strikes North) - 8 scenarios

| #   | Scenario                    | Status | Notes                      |
| --- | --------------------------- | ------ | -------------------------- |
| 2   | The Race for Columbia       | ✅     | 23 CSA rows, 26 Union rows |
| 3   | A Great Chance Was Lost     | ✅     | 23 CSA rows, 21 Union rows |
| 4   | We Will Make the Fight      | ✅     | 23 CSA rows, 22 Union rows |
| 5   | The Enemy Was Badly Whipped | ✅     | 8 CSA rows, 7 Union rows   |
| 6   | The Battle of Nashville     | ✅     | 16 CSA rows, 26 Union rows |
| 7   | Hood's Retreat              | ✅     | 21 CSA rows, 15 Union rows |
| 8   | That Devil Forrest          | ✅     | 10 CSA rows, 11 Union rows |
| 9   | Hood Strikes North          | ✅     | 32 CSA rows, 49 Union rows |

### RTW (Rally 'Round the Flag) - 4 scenarios

| #   | Scenario                      | Status | Notes                      |
| --- | ----------------------------- | ------ | -------------------------- |
| 1   | Monocacy                      | ✅     | 6 CSA rows, 6 Union rows   |
| 2   | Fort Stevens                  | ✅     | 8 CSA rows, 9 Union rows   |
| 3   | The Retreat From Washington   | ✅     | 10 CSA rows, 27 Union rows |
| 4   | From Winchester to Washington | ✅     | 12 CSA rows, 40 Union rows |

---

## Known Issues & Fixes (Resolved)

### Issue: Scenario header not detected (FIXED)

**Example:** OTR2 Scenario 1 - header on same line as section title

**Fix applied:** Skip TOC-style lines with multiple dots (`.....`) rather than skipping entire pages containing "basic game scenarios".

### Issue: Table name picks up extra text (FIXED)

**Example:** OTR2 Scenario 3 - "Confederate Set-Up 1 Or Less Confederate Decisive Victory"

**Fix applied:** `_clean_header()` now truncates at victory condition patterns like "1 or less", "decisive victory", etc.

### Issue: "Advanced Game" text in rules causes early stop (FIXED)

**Example:** GTC2 Scenario 4 - "Advanced Game rules (see 17.2) apply in this scenario" was triggering section stop

**Fix applied:** Exclude lines containing "(see" or "apply" from advanced game section detection.

### Issue: PDF typo "Unon" for "Union" (FIXED)

**Example:** GTC2 Scenario 5 - "Unon set-Up" table header

**Fix applied:** Added "unon" to pattern matching and cleanup.

---

## Data-Driven Unit Parser (Phase 2)

The unit parser uses a configuration-based approach to handle game-specific column layouts.

### Configuration Hierarchy

1. **Defaults** - Standard column layout for most tables
2. **Table patterns** - Regex-matched overrides for special tables (reinforcement tracks, etc.)
3. **Scenario overrides** - Specific table configs for individual scenarios

Example from `game_configs.json`:

```json
{
  "defaults": {
    "columns": ["name", "size", "command", "type", "manpower", "hex"]
  },
  "hcr": {
    "table_patterns": {
      ".*Scenario 7.*|.*Scenario 8.*": {
        "columns": [
          "turn",
          "name",
          "size",
          "command",
          "type",
          "manpower",
          "hex"
        ]
      }
    }
  },
  "rtg2": {
    "table_patterns": {
      ".*Reinforcement Track|.*Garrison Track": {
        "columns": ["name", "size", "command", "type", "manpower", "hex", "set"]
      }
    }
  }
}
```

### Parsed Unit Fields

| Field               | Description                                    |
| ------------------- | ---------------------------------------------- |
| `unit_leader`       | Unit/leader name (cleaned of footnote symbols) |
| `size`              | Army, Corps, Div, Brig, Regt, etc.             |
| `command`           | Command designation (e.g., "III", "Cav", "M")  |
| `unit_type`         | Ldr, Inf, Cav, Art, Special                    |
| `manpower_value`    | MP value (may contain footnote symbols)        |
| `hex_location`      | Hex ID and location name                       |
| `side`              | Confederate or Union                           |
| `notes`             | List of footnote symbols attached to this unit |
| `turn`              | (Optional) Arrival turn for reinforcements     |
| `reinforcement_set` | (Optional) Reinforcement set number            |

---

## Next Steps

Phase 2 integration is complete. The pipeline is now:

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json
```

### Regenerating Data

To regenerate all web data from parsed files:

```bash
cd parser && uv run python convert_to_web.py
```

To re-parse raw tables (if column configs change):

```bash
cd parser && uv run python parse_raw_tables.py --all
cd parser && uv run python convert_to_web.py
```

### Remaining Improvements (Optional)

1. **Add table metadata** - Preserve table name (e.g., "Reinforcement Track") in parsed output for UI grouping
2. **Handle HCR scenarios 7/8 turn display** - Turn field needs to be shown in roster UI
