---
name: parse-new-game
description: Parse a new GCACW game PDF to extract scenario data. Use when adding a new game to the roster generator, extracting units from PDF tables, or setting up scenario names.
---

# Parse New Game

This skill guides the process of adding a new game from the Great Campaigns of the American Civil War series to the roster generator.

## Prerequisites

- PDF rulebook in `data/` directory (e.g., `data/NewGame_Rules.pdf`)
- Python environment with pdfplumber (managed by uv)

## Step 1: Discover Scenario Names

PDF text extraction is unreliable—scenario titles often merge with adjacent text due to multi-column layouts. Run this to see what the parser finds:

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

**CRITICAL**: Cross-reference the output against the actual PDF. The extracted text will have:

- Weird capitalization (from small caps fonts)
- Extra text merged from adjacent columns
- Missing or corrupted characters

Manually verify each scenario name by looking at the PDF.

## Step 2: Add Scenario Names

Edit `parser/scenario_parser.py` and add entries to the `SCENARIO_NAMES` dict (~line 40):

```python
SCENARIO_NAMES = {
    # ... existing games ...
    "newgame": {
        1: "Scenario One Name",
        2: "Scenario Two Name",
        # etc.
    },
}
```

## Step 3: Add Game Config

Edit `parser/convert_to_web.py` and add to the `GAMES` list:

```python
GAMES = [
    # ... existing games ...
    {
        "id": "newgame",
        "name": "Full Game Name",
        "parser_output": "newgame_scenarios.json",
        "web_output": "newgame.json",
    },
]
```

## Step 4: Run Parser

```bash
cd parser && uv run python scenario_parser.py ../data/NewGame.pdf newgame
```

Review the output for:

- Correct scenario count
- Reasonable unit counts per scenario
- Game length format (should be like "X turns; Month Day to Month Day, Year.")

## Step 5: Generate Web Data

```bash
cd parser && uv run python convert_to_web.py
```

This creates `web/public/data/newgame.json` and updates `games.json`.

## Step 6: Validate

1. Run `cd web && npm run build` to catch TypeScript errors
2. Run `cd web && npm run dev` and visually inspect the new game
3. Check that all scenarios appear in the dropdown
4. Spot-check unit data against the PDF

## Common Issues

- **Zero units parsed**: Check if the PDF table format differs from expected
- **Wrong game length text**: The `_extract_game_length` regex may need adjustment
- **Missing scenarios**: Check if scenario headers are on unusual pages or have different formatting
