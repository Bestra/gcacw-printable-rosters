---
name: parse-new-game
description: Parse a new GCACW game PDF to extract scenario data. Use when adding a new game to the roster generator, extracting units from PDF tables, or setting up scenario names.
---

# Parse New Game

This skill guides the process of adding a new game from the Great Campaigns of the American Civil War series to the roster generator.

## Prerequisites

- PDF rulebook in `data/` directory (e.g., `data/NewGame_Rules.pdf`)
- Python environment with pdfplumber (managed by uv)

## Step 1: Extract Raw Tables

Run the raw table extractor to capture table structure from the PDF:

```bash
cd parser && uv run python raw_table_extractor.py ../data/NewGame.pdf newgame
```

This creates `raw/newgame_raw_tables.json` containing all scenario tables with:

- Scenario names and page ranges
- Confederate and Union tables
- Raw row tokens (not yet parsed)
- Footnote annotations

Review the output to verify scenarios were detected correctly.

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

Edit `parser/convert_to_web.py` and add to the `GAMES` list:

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
cd parser && uv run python parse_raw_tables.py newgame
```

This creates `parsed/newgame_parsed.json` with structured unit data.

Review the output for:

- Correct scenario count
- Reasonable unit counts per scenario
- Footnotes captured correctly

## Step 6: Generate Web Data

```bash
cd parser && uv run python convert_to_web.py
```

This creates `web/public/data/newgame.json` and updates `games.json`.

## Step 7: Validate

1. Run `cd web && npm run build` to catch TypeScript errors
2. Run `cd web && npm run dev` and visually inspect the new game
3. Check that all scenarios appear in the dropdown
4. Spot-check unit data against the PDF

## Step 8: Extract Counter Images (Optional)

If you have a VASSAL module (.vmod) for the game, you can extract counter images for display in the web app. See the **extract-vassal-images** skill for detailed instructions.

Quick start:

```bash
# Detect the counter type
cd parser && uv run python detect_counter_type.py /path/to/GAME.vmod

# Then run the appropriate extractor based on the detected type
```

## Common Issues

- **"Game not found" error**: Missing slug mapping in `web/src/utils/slugs.ts`
- **Wrong column parsing**: Check `game_configs.json` for table pattern overrides
- **Zero units parsed**: Check if the PDF table format differs from expected; may need to re-extract raw tables
- **Missing scenarios**: Check raw tables JSON to see if scenario headers were detected
