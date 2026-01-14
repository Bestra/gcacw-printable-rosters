# Hybrid PDF Parsing Approach

## Overview

Instead of building a fully automated parser that handles all PDF edge cases, we use a **hybrid approach**:

1. **Automated extraction** - Use `raw_table_extractor.py` to dump raw table data from PDFs
2. **AI-assisted cleanup** - Review extracted data and manually correct parsing errors
3. **Validated output** - Produce clean, verified JSON ready for the web app

## Why This Works Better

| Challenge                              | Automated Parser         | Hybrid Approach                     |
| -------------------------------------- | ------------------------ | ----------------------------------- |
| Merged/garbled text                    | Endless regex edge cases | Visual review catches errors        |
| Multi-token names (e.g., "A. Jenkins") | Complex heuristics       | Human judgment                      |
| Table boundaries                       | Pattern matching fails   | Clear table structure in raw output |
| Footnote symbols                       | Inconsistent extraction  | Direct verification                 |
| New game PDFs                          | Each needs debugging     | Same process, just review           |

## Process

### Step 1: Extract Raw Tables

```bash
cd parser
uv run python raw_table_extractor.py game_id  # Uses {GAME_ID}_RULES_PATH from .env
```

This produces `raw/{game_id}_raw_tables.json` with:

- Scenario boundaries (start/end pages)
- Per-side table groupings
- Raw row tokens (not yet parsed into fields)
- Detected annotations/footnotes

### Step 2: Review & Correct

For each scenario:

1. **Check table names** - Are they correctly identified?
2. **Parse row tokens** - Map tokens to: unit_leader, size, command, unit_type, manpower_value, hex_location
3. **Handle multi-token values** - Names like "A. Jenkins" or "Art Res-1" or "17 VA"
4. **Verify annotations** - Match footnote symbols to correct explanations
5. **Special cases** - Reinforcement tracks, entry hexes with ranges ("S2134 to S3534")

### Step 3: Output Clean JSON

Produce `{game_id}_scenarios.json` with properly structured unit data:

```json
{
  "unit_leader": "A. Jenkins",
  "size": "Brig",
  "command": "Cav",
  "unit_type": "Cav",
  "manpower_value": "3",
  "hex_location": "S0608 (Middleburg)",
  "side": "Confederate",
  "notes": []
}
```

## Common Parsing Patterns

### Unit Name Patterns

| Raw Tokens                | Parsed unit_leader |
| ------------------------- | ------------------ |
| `["A.", "Jenkins"]`       | "A. Jenkins"       |
| `["17", "VA"]`            | "17 VA"            |
| `["Art", "Res-1"]`        | "Art Res-1"        |
| `["DM", "Gregg"]`         | "DM Gregg"         |
| `["F.", "Lee"]`           | "F. Lee"           |
| `["Wagon", "Train", "1"]` | "Wagon Train 1"    |

### Hex Location Patterns

| Raw Tokens                      | Parsed hex_location                |
| ------------------------------- | ---------------------------------- |
| `["S0608", "(Middleburg)"]`     | "S0608 (Middleburg)"               |
| `["S2134", "to", "S3534^"]`     | "S2134 to S3534" (with ^ footnote) |
| `["N4907", "(Camp", "Curtin)"]` | "N4907 (Camp Curtin)"              |

### Size/Command Detection

Standard sizes: Army, Corps, Div, Brig, Regt
Standard types: Ldr, Inf, Cav, Art
Commands: Roman numerals (I, II, III), abbreviations (AP, ANV, Cav, PA, DC, etc.)

## RTG2 Scenario 10: The Gettysburg Campaign

This is the advanced game scenario with multiple table types:

### Confederate Tables

1. **Confederate Set-Up** - Initial placement
2. **Placed Upon Stuart's Arrival** - Entry with Stuart (special timing)
3. **Confederate Reinforcement Track** - Reinforcement sets 1-4
4. **Richmond Garrison Track** - Reinforcement sets 1-4

### Union Tables

1. **Union Set-Up** - Initial placement (forts, militia)
2. **Army Of The Potomac First Increment** - Entry hex range
3. **Army Of The Potomac Second Increment** - Entry hex range
4. **Army Of The Potomac Third Increment** - Entry hex range
5. **West Virginia Reinforcement Track** - Reinforcement sets 1-3
6. **Baltimore/DC Reinforcement Track** - Reinforcement sets 1-6
7. **Pennsylvania Militia Reinforcement Track** - Reinforcement sets 1-6
