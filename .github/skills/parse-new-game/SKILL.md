---
name: parse-new-game
description: Parse a new GCACW game PDF to extract scenario data. Use when adding a new game to the roster generator, extracting units from PDF tables, or setting up scenario names.
---

# Parse New Game

This skill guides the process of adding a new game from the Great Campaigns of the American Civil War series to the roster generator.

## Prerequisites

- PDF rulebook accessible on your filesystem
- Python environment with pdfplumber (managed by uv)
- Environment variables configured in `parser/.env`

### Environment Variable Setup (Required)

Configure file paths using environment variables in `parser/.env`:

```bash
# Add to parser/.env
NEWGAME_RULES_PATH=~/Documents/vasl/gcacw/NewGame_Rules.pdf
NEWGAME_VASSAL_PATH=~/Documents/vasl/gcacw/NewGame.vmod  # Optional, for counter images
```

## Step 1: Extract Raw Tables

Run the raw table extractor to capture table structure from the PDF:

```bash
# Using environment variable (NEWGAME_RULES_PATH from parser/.env):
cd parser && uv run python pipeline/raw_table_extractor.py newgame

# Or via Makefile:
make extract-newgame
```

This creates `raw/newgame_raw_tables.json` containing all scenario tables with:

- Scenario names and page ranges (initially generic "Scenario 1", "Scenario 2", etc.)
- Confederate and Union tables
- Raw row tokens (not yet parsed)
- Footnote annotations

Review the output to verify scenarios were detected correctly.

## Step 1.5: Add Scenario Names (Required)

The initial extraction will use generic names like "Scenario 1", "Scenario 2", etc. You need to manually add the actual scenario names:

1. **Look up scenario names** from the PDF table of contents or scenario headers
2. **Edit `parser/pipeline/raw_table_extractor.py`** and add to the `SCENARIO_NAMES` dictionary:

```python
SCENARIO_NAMES = {
    # ... existing games ...
    "newgame": {
        1: "First Scenario Name",
        2: "Second Scenario Name",
        3: "Third Scenario Name",
        # ... etc
    },
}
```

3. **Re-extract raw tables** with the updated names:

```bash
cd parser && rm raw/newgame_raw_tables.json
cd parser && uv run python pipeline/raw_table_extractor.py newgame
```

**Why this is manual**: PDF text extraction quality varies significantly. Scenario names often run into other text on the same line, making reliable auto-extraction impractical. The semi-manual approach ensures correct names every time.

## Step 2: Check Column Structure

Examine the raw tables to understand the column layout. Most games use:

```
Unit/Leader | Size | Command | Type | Manpower | Hex
```

Some games have variations:

- **HCR Scenarios 7-8**: Have a leading "Turn" column
- **RTG2**: Has trailing "Set #" column for reinforcements
- **HSN**: Has "Set" column in some tables

If the game has non-standard columns, add a config entry to `game_configs.json`:

```json
{
  "newgame": {
    "table_patterns": {
      ".*Reinforcement.*": {
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
  }
}
```

## Step 3: Add Game Config

Edit `parser/pipeline/convert_to_web.py` and add to the `GAMES` list:

```python
GAMES = [
    # ... existing games ...
    {"id": "newgame", "name": "Full Game Name"},
]
```

## Step 4: Add URL Slug Mapping

Edit `web/src/utils/slugs.ts` and add the game to both slug mappings:

```typescript
const gameIdToSlug: Record<string, string> = {
  // ... existing games ...
  newgame: "NEWGAME", // URL-friendly slug (typically uppercase abbreviation)
};

const slugToGameId: Record<string, string> = {
  // ... existing games ...
  newgame: "newgame", // lowercase version maps back to game ID
};
```

**Note**: The `slugToGameId` key must be lowercase since lookups are case-insensitive.

## Step 5: Parse Raw Tables

```bash
cd parser && uv run python pipeline/parse_raw_tables.py newgame
```

This creates `parsed/newgame_parsed.json` with structured unit data.

Review the output for:

- Correct scenario count
- Reasonable unit counts per scenario
- Footnotes captured correctly

## Step 6: Generate Web Data

```bash
cd parser && uv run python pipeline/convert_to_web.py
```

This creates `web/public/data/newgame.json` and updates `games.json`.

## Step 7: Validate

1. Run `make build` to catch TypeScript errors
2. Run `make dev` and visually inspect the new game
3. Check that all scenarios appear in the dropdown
4. Spot-check unit data against the PDF

## Step 8: Extract Counter Images (Optional)

If you have a VASSAL module (.vmod) for the game, you can extract counter images for display in the web app. See the **extract-vassal-images** skill for detailed instructions.

Quick start:

```bash
# If NEWGAME_VASSAL_PATH is set in parser/.env:
cd parser && uv run python image_extraction/detect_counter_type.py

# Or with explicit path:
cd parser && uv run python image_extraction/detect_counter_type.py /path/to/GAME.vmod

# Then run the appropriate extractor based on the detected type
```

## Common Issues

- **"Game not found" error**: Missing slug mapping in `web/src/utils/slugs.ts`
- **Wrong column parsing**: Check `game_configs.json` for table pattern overrides
- **Zero units parsed**: Check if the PDF table format differs from expected; may need to re-extract raw tables
- **Missing scenarios**: Check raw tables JSON to see if scenario headers were detected
- **Hex codes show only map prefix** (e.g., "HCR" instead of "HCR W0330"): The hex location parser in `parser/utils/hex_location_config.json` needs to recognize the game's map prefix and hex letter format. Update:
  - `gameMapPrefixes` array: Add new map prefixes (e.g., "HCR", "GTC")
  - `patterns[0].regex`: Add new hex letters to the character class (e.g., `[NSMW]` for games using W-prefixed hexes)

  Then rebuild with `make build` to pick up the config changes.

  **Note:** `convert_to_web.py` automatically validates hex locations against the config and will warn about unrecognized patterns during conversion. Watch for warnings like "⚠️ Found X unrecognized hex location patterns" in the output.
