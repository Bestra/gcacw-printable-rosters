---
name: regenerate-data
description: Regenerate web JSON data after parser changes. Use after modifying scenario_parser.py or convert_to_web.py, or when data needs refreshing.
---

# Regenerate Data

Run the parser and converter to refresh all game data after making changes.

## Quick Regenerate (All Games)

```bash
cd parser
uv run python scenario_parser.py ../data/OTR2_Rules.pdf otr2
uv run python scenario_parser.py ../data/GTC2_Rules.pdf gtc2
uv run python convert_to_web.py
```

## Single Game

```bash
cd parser
uv run python scenario_parser.py ../data/<GamePDF>.pdf <game_id>
uv run python convert_to_web.py
```

## Validate

After regenerating:

1. Check parser output for reasonable unit counts
2. Run `cd web && npm run build` to catch any type errors
3. Visually inspect in browser if needed

## Data Flow

```
PDF → scenario_parser.py → {game_id}_scenarios.json (snake_case)
                         ↓
                   convert_to_web.py
                         ↓
              web/public/data/{game_id}.json (camelCase)
```
