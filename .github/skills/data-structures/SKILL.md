---
name: data-structures
description: Understand data structures in the GCACW parser pipeline (raw tables, parsed units, web JSON). Use when debugging data issues, understanding field mappings between stages, checking column configurations, or investigating why units are missing or malformed. Includes inspection utilities (inspect_raw.py, inspect_parsed.py, compare_data.py). Essential for work involving raw_table_extractor.py, parse_raw_tables.py, convert_to_web.py, or game_configs.json.
---

# Data Structures

Documentation for the three-stage data pipeline used by the GCACW scenario parser.

## Pipeline Overview

```
PDF → raw_table_extractor.py → raw/{game}_raw_tables.json (snake_case)
                                       ↓
                              parse_raw_tables.py → parsed/{game}_parsed.json (snake_case)
                                       ↓
                              convert_to_web.py → web/public/data/{game}.json (camelCase)
```

## When to Use This Skill

Use this skill when:

- Debugging missing or malformed units in any stage
- Understanding field mappings between pipeline stages
- Investigating column configuration issues in `game_configs.json`
- Comparing data between stages to isolate parsing problems
- Working with raw table extraction, parsing, or web conversion

## Quick Reference

### Stage 1: Raw Tables

**File**: `raw/{game}_raw_tables.json`  
**Source**: `raw_table_extractor.py`

Structure preserves PDF extraction exactly as read:

- Array of scenarios, each with `confederate_tables` and `union_tables`
- Each table has `header_row`, `rows[][]`, and `annotations{}`
- Values are raw strings from PDF, may span multiple tokens
- Footnote symbols embedded in cell values (e.g., `"2*"`)

### Stage 2: Parsed Units

**File**: `parsed/{game}_parsed.json`  
**Source**: `parse_raw_tables.py`

Structured unit objects with semantic fields:

- `unit_leader`, `size`, `command`, `unit_type`, `manpower_value`, `hex_location`
- Footnote symbols extracted to `notes[]` array
- Side assignment: `"Confederate"` or `"Union"`
- Optional: `turn`, `reinforcement_set`, `table_name`

### Stage 3: Web JSON

**File**: `web/public/data/{game}.json`  
**Source**: `convert_to_web.py`

Frontend-ready format:

- CamelCase field names (`hexLocation`, `manpowerValue`)
- Gunboats/special units separated into `confederateGunboats` / `unionGunboats`
- Matches TypeScript interfaces in `web/src/types.ts`

## Inspection Tools

Three utility scripts help debug data at each stage:

```bash
# View raw table data
cd parser && uv run python utils/inspect_raw.py <game_id>
cd parser && uv run python utils/inspect_raw.py <game_id> --scenario 1 --table "Confederate Set-Up"

# View parsed units
cd parser && uv run python utils/inspect_parsed.py <game_id>
cd parser && uv run python utils/inspect_parsed.py <game_id> --scenario 1 --side Confederate

# Compare raw vs parsed (for debugging parsing issues)
cd parser && uv run python utils/compare_data.py <game_id> <scenario>
cd parser && uv run python utils/compare_data.py <game_id> <scenario> --side Union --table "Union Set-Up"
```

All scripts support `--help` for detailed usage.

## Common Debugging Patterns

### Missing Units in Parsed Data

1. Check raw extraction: `uv run python inspect_raw.py <game> --scenario N`
2. Look for the missing unit in raw table rows
3. If present in raw but missing in parsed, check column config in `game_configs.json`
4. If absent from raw, check PDF extraction with `utils/diagnose_pdf.py`

### Wrong Unit Attributes

1. Compare raw vs parsed: `uv run python compare_data.py <game> <scenario>`
2. Check column configuration in `game_configs.json`
3. Verify column mappings match the raw `header_row`

### Footnotes Not Matching

1. Check if symbol is in `footnote_symbols` list in config
2. Verify annotations dict in raw tables contains the symbol
3. Check parser's footnote extraction logic

### Field Naming Across Stages

| Concept   | Raw             | Parsed           | Web JSON        |
| --------- | --------------- | ---------------- | --------------- |
| Unit name | `values[0...n]` | `unit_leader`    | `name`          |
| Manpower  | `values[n]`     | `manpower_value` | `manpowerValue` |
| Hex       | `values[n]`     | `hex_location`   | `hexLocation`   |
| Type      | `values[n]`     | `unit_type`      | `type`          |

## Detailed Documentation

**For complete structure details, examples, and edge cases**, see [references/structures.md](references/structures.md).

That file contains:

- Full JSON schemas for each stage
- Field-by-field descriptions
- TypeScript interface definitions
- Data flow examples
- Unit type explanations (Ldr, Inf, Cav, Art, Special)
- Size hierarchy (Army > Corps > Div > Brig > Regt)
- Hex location formats
- Footnote symbol reference
- Common patterns and edge cases

## Related Files

- [game_configs.json](../../../parser/game_configs.json) - Column mappings and parsing rules
- [raw_table_extractor.py](../../../parser/pipeline/raw_table_extractor.py) - Stage 1: PDF → raw
- [parse_raw_tables.py](../../../parser/pipeline/parse_raw_tables.py) - Stage 2: raw → parsed
- [convert_to_web.py](../../../parser/pipeline/convert_to_web.py) - Stage 3: parsed → web
- [types.ts](../../../web/src/types.ts) - TypeScript interfaces
