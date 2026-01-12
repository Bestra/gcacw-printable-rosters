# GCACW Parser Data Structures

This document describes the data structures used throughout the GCACW scenario parser pipeline.

## Pipeline Overview

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json (snake_case)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json (snake_case)
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json (camelCase)
                                       ↓
                              Web app fetches at runtime
```

## Stage 1: Raw Tables (`raw/{game}_raw_tables.json`)

Output from `raw_table_extractor.py`. Preserves PDF extraction artifacts and table structure.

### File Structure
```json
[
  {
    "scenario_number": 1,
    "scenario_name": "The Battle of the Wilderness",
    "start_page": 4,
    "end_page": 6,
    "advanced_game_rules_page": null,
    "confederate_tables": [...],
    "union_tables": [...]
  }
]
```

### `RawScenarioTables` (Top Level)
| Field | Type | Description |
|-------|------|-------------|
| `scenario_number` | int | Scenario number from PDF (1-indexed) |
| `scenario_name` | string | Scenario name from PDF or config |
| `start_page` | int | First page of scenario (1-indexed) |
| `end_page` | int | Last page of scenario (1-indexed) |
| `advanced_game_rules_page` | int \| null | Page where Advanced Game rules start |
| `confederate_tables` | RawTable[] | List of Confederate setup tables |
| `union_tables` | RawTable[] | List of Union setup tables |

### `RawTable`
Each table represents a setup table, reinforcement track, or increment table from the PDF.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Table header (e.g., "Confederate Set-Up", "First Increment") |
| `page_numbers` | int[] | Pages where table appears (1-indexed) |
| `header_row` | string[] | Column headers from PDF |
| `rows` | string[][] | Raw table data, each row is a list of cell values |
| `annotations` | dict | Footnote symbols → explanations |

#### Example `RawTable`
```json
{
  "name": "Confederate Set-Up",
  "page_numbers": [5],
  "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
  "rows": [
    ["WH", "Lee", "Div", "WL", "Ldr", "—", "N0811"],
    ["Chambliss", "Brig", "WL", "Cav", "2*", "N0811"],
    ["Anderson", "Div", "III", "Inf", "15", "N1012"]
  ],
  "annotations": {
    "*": "Chambliss, Ramseur, and Steuart start under Fort-Complete markers"
  }
}
```

### Key Characteristics
- **Preserves PDF artifacts**: Row values exactly as extracted from PDF
- **Multiple tokens per cell**: Unit names may span multiple array elements
- **No semantic parsing**: Size, command, type are not yet identified
- **Footnote symbols preserved**: Appear in values like `"2*"`, `"3†"`
- **Multi-page tables**: `page_numbers` tracks continuation across pages

---

## Stage 2: Parsed Units (`parsed/{game}_parsed.json`)

Output from `parse_raw_tables.py`. Converts raw rows into structured unit data.

### File Structure
```json
[
  {
    "number": 1,
    "name": "The Battle of the Wilderness",
    "start_page": 4,
    "confederate_units": [...],
    "union_units": [...],
    "confederate_footnotes": {...},
    "union_footnotes": {...},
    "notes": "",
    "map_info": "",
    "game_length": "",
    "special_rules": []
  }
]
```

### `ParsedScenario`
| Field | Type | Description |
|-------|------|-------------|
| `number` | int | Scenario number |
| `name` | string | Scenario name |
| `start_page` | int | First page of scenario |
| `confederate_units` | Unit[] | All Confederate units |
| `union_units` | Unit[] | All Union units |
| `confederate_footnotes` | dict | CSA footnote symbols → explanations |
| `union_footnotes` | dict | USA footnote symbols → explanations |
| `notes` | string | Additional scenario notes (currently unused) |
| `map_info` | string | Map configuration info (currently unused) |
| `game_length` | string | Game length info (currently unused) |
| `special_rules` | string[] | Special rules list (currently unused) |

### `Unit`
Represents a single parsed unit or leader.

| Field | Type | Description |
|-------|------|-------------|
| `unit_leader` | string | Unit or leader name (e.g., "Chambliss", "WH Lee") |
| `size` | string | Unit size (Army, Corps, Div, Brig, Regt, or "-" for leaders/special) |
| `command` | string | Command designation (e.g., "WL", "III", "K-I") |
| `unit_type` | string | Type: `Ldr`, `Inf`, `Cav`, `Art`, or `Special` |
| `manpower_value` | string | Manpower value with footnote symbols (e.g., "2*", "15", "—") |
| `hex_location` | string | Hex location(s), may include place names |
| `side` | string | "Confederate" or "Union" |
| `notes` | string[] | List of footnote symbols that apply to this unit |
| `turn` | string \| null | Reinforcement turn (HCR only) |
| `reinforcement_set` | string \| null | Set number (RTG2/HSN campaigns) |
| `table_name` | string \| null | Source table name (for multi-increment scenarios) |

#### Example Standard Unit
```json
{
  "unit_leader": "Chambliss",
  "size": "Brig",
  "command": "WL",
  "unit_type": "Cav",
  "manpower_value": "2*",
  "hex_location": "N0811",
  "side": "Confederate",
  "notes": ["*"],
  "turn": null,
  "reinforcement_set": null,
  "table_name": null
}
```

#### Example Leader Unit
```json
{
  "unit_leader": "Longstreet",
  "size": "Corps",
  "command": "I",
  "unit_type": "Ldr",
  "manpower_value": "—",
  "hex_location": "N1221 (Brock's Bridge)",
  "side": "Confederate",
  "notes": [],
  "turn": null,
  "reinforcement_set": null,
  "table_name": null
}
```

#### Example Special Unit (Gunboat)
```json
{
  "unit_leader": "Gunboat #2",
  "size": "-",
  "command": "-",
  "unit_type": "Special",
  "manpower_value": "-",
  "hex_location": "Reinforcement Display",
  "side": "Union",
  "notes": [],
  "turn": null,
  "reinforcement_set": null,
  "table_name": null
}
```

### Key Characteristics
- **Structured parsing**: Unit name, size, type, etc. are identified and separated
- **Footnote extraction**: Symbols removed from values, stored in `notes[]`
- **Snake_case naming**: Field names use underscores
- **Deduplicated leaders**: Leaders appearing in multiple tables are deduplicated by (name, hex)
- **Side assignment**: Each unit tagged with "Confederate" or "Union"
- **Special units**: Gunboats, Wagon Trains, Naval Batteries have `unit_type="Special"`

---

## Stage 3: Web JSON (`web/public/data/{game}.json`)

Output from `convert_to_web.py`. Frontend-ready format with camelCase naming.

### File Structure
```json
{
  "id": "gtc2",
  "name": "Grant Takes Command",
  "scenarios": [...]
}
```

### `GameData` (Top Level)
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Game identifier (e.g., "gtc2", "otr2") |
| `name` | string | Full game name |
| `scenarios` | Scenario[] | Array of scenarios |

### `Scenario`
| Field | Type | Description |
|-------|------|-------------|
| `number` | int | Scenario number |
| `name` | string | Scenario name |
| `confederateFootnotes` | Record<string, string> | CSA footnotes |
| `unionFootnotes` | Record<string, string> | USA footnotes |
| `confederateUnits` | Unit[] | CSA units (excluding gunboats) |
| `unionUnits` | Unit[] | USA units (excluding gunboats) |
| `confederateGunboats` | Gunboat[] | CSA gunboats/special units |
| `unionGunboats` | Gunboat[] | USA gunboats/special units |

### `Unit`
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unit or leader name |
| `size` | string | Unit size |
| `command` | string | Command designation |
| `type` | string | Unit type (Ldr, Inf, Cav, Art) |
| `manpowerValue` | string | Manpower with symbols |
| `hexLocation` | string | Hex location(s) |
| `notes` | string[] | Footnote symbols |
| `reinforcementSet?` | string | Optional: Set number |
| `tableName?` | string | Optional: Source table |

### `Gunboat`
Simplified structure for special units (gunboats, wagon trains, naval batteries).

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unit name |
| `location` | string | Hex or display location |

#### Example Web Unit
```json
{
  "name": "Chambliss",
  "size": "Brig",
  "command": "WL",
  "type": "Cav",
  "manpowerValue": "2*",
  "hexLocation": "N0811",
  "notes": ["*"]
}
```

#### Example Web Gunboat
```json
{
  "name": "Gunboat #2",
  "location": "Reinforcement Display"
}
```

### Key Characteristics
- **CamelCase naming**: All field names use camelCase for JavaScript/TypeScript
- **Separated gunboats**: Special units separated into `confederateGunboats` / `unionGunboats`
- **Game metadata**: Includes game ID and full name
- **Type-safe**: Matches TypeScript interfaces in `web/src/types.ts`

---

## TypeScript Interfaces (`web/src/types.ts`)

Frontend type definitions that match the web JSON structure:

```typescript
export interface Unit {
  name: string;
  size: string;
  command: string;
  type: string;
  manpowerValue: string;
  hexLocation: string;
  notes: string[];
  reinforcementSet?: string;
  tableName?: string;
}

export interface Gunboat {
  name: string;
  location: string;
}

export interface Scenario {
  number: number;
  name: string;
  confederateFootnotes: Record<string, string>;
  unionFootnotes: Record<string, string>;
  confederateUnits: Unit[];
  unionUnits: Unit[];
  confederateGunboats: Gunboat[];
  unionGunboats: Gunboat[];
}

export interface GameData {
  id: string;
  name: string;
  scenarios: Scenario[];
}
```

---

## Field Naming Conventions

### Across Pipeline Stages

| Concept | Raw Tables | Parsed | Web JSON |
|---------|-----------|--------|----------|
| Unit name | `values[0...n]` | `unit_leader` | `name` |
| Manpower | `values[n]` | `manpower_value` | `manpowerValue` |
| Hex | `values[n]` | `hex_location` | `hexLocation` |
| Type | `values[n]` | `unit_type` | `type` |
| Footnotes | Embedded in values | `notes[]` | `notes[]` |
| Footnote text | `annotations{}` | `confederate_footnotes` / `union_footnotes` | `confederateFootnotes` / `unionFootnotes` |

---

## Common Patterns and Edge Cases

### Unit Types
- **Leaders** (`Ldr`): Size indicates command level (Corps, Army, Div), no manpower
- **Infantry** (`Inf`): Most common, includes brigades, divisions, regiments
- **Cavalry** (`Cav`): Mobile units
- **Artillery** (`Art`): Rare in setup tables
- **Special**: Gunboats, Wagon Trains, Naval Batteries (converted to `Gunboat[]` in web)

### Size Hierarchy
`Army` > `Corps` > `Demi-Div` (or `D-Div`) > `Div` > `Brig` > `Regt`

### Hex Locations
- Standard hex: `N0811`, `S5510`
- With place name: `N1221 (Brock's Bridge)`
- Multiple hexes: `N0811 or N0812`
- Special locations: `Reinforcement Display`, `River Box`, `Baltimore/DC`

### Footnote Symbols
Standard symbols: `*`, `^`, `†`, `‡`, `§`, `$`, `+`, `#`, `&`

### Manpower Values
- Numbers: `2`, `15`, `10`
- With fatigue: `2*`, `3†`
- Leaders/special: `—` or `-`

### Command Designations
- Corps: `I`, `II`, `III`, `V`, `VI`, `IX`, `XI`, `XII`
- Division: `K-I`, `F-I`, `A-II`, `WL` (W.H. Lee)
- Special: Single letter or abbreviation

---

## Data Flow Example

### Raw Table Row
```json
["Chambliss", "Brig", "WL", "Cav", "2*", "N0811"]
```

### Parsed Unit
```json
{
  "unit_leader": "Chambliss",
  "size": "Brig",
  "command": "WL",
  "unit_type": "Cav",
  "manpower_value": "2*",
  "hex_location": "N0811",
  "side": "Confederate",
  "notes": ["*"],
  "turn": null,
  "reinforcement_set": null,
  "table_name": null
}
```

### Web JSON Unit
```json
{
  "name": "Chambliss",
  "size": "Brig",
  "command": "WL",
  "type": "Cav",
  "manpowerValue": "2*",
  "hexLocation": "N0811",
  "notes": ["*"]
}
```

---

## Debugging Tips

### Inspecting Data at Each Stage

```bash
# Check raw tables
uv run python parser/inspect_raw.py gtc2

# Check parsed data
uv run python parser/inspect_parsed.py gtc2

# Compare raw vs parsed for a scenario
uv run python parser/compare_data.py gtc2 1

# View web JSON (just use cat or jq)
cat web/public/data/gtc2.json | jq '.scenarios[0]'
```

### Common Issues

1. **Missing units in parsed data**: Check raw table extraction - unit may not have been recognized
2. **Wrong unit attributes**: Check column configuration in `game_configs.json`
3. **Footnotes not matching**: Check if symbol is in `footnote_symbols` list in config
4. **Hex location wrong**: Check if location spans multiple tokens in raw data
5. **Leaders appearing in wrong table**: Check side determination logic in raw extractor

---

## Related Files

- [game_configs.json](../../parser/game_configs.json) - Column mappings and parsing rules
- [raw_table_extractor.py](../../parser/raw_table_extractor.py) - Stage 1: PDF → raw tables
- [parse_raw_tables.py](../../parser/parse_raw_tables.py) - Stage 2: raw → parsed
- [convert_to_web.py](../../parser/convert_to_web.py) - Stage 3: parsed → web JSON
- [types.ts](../../web/src/types.ts) - TypeScript interfaces for web app
