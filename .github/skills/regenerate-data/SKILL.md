---
name: regenerate-data
description: Regenerate web JSON data after parser changes. Use after modifying parse_raw_tables.py, game_configs.json, or convert_to_web.py, or when data needs refreshing.
---

# Regenerate Data

Run the parser and converter to refresh all game data after making changes.

## Quick Regenerate (All Games)

```bash
cd parser
uv run python pipeline/parse_raw_tables.py --all
uv run python pipeline/convert_to_web.py
```

## Single Game

```bash
cd parser
uv run python pipeline/parse_raw_tables.py <game_id>
uv run python pipeline/convert_to_web.py
```

## Re-extract from PDF (if raw tables need updating)

```bash
cd parser
uv run python pipeline/raw_table_extractor.py <game_id>  # Uses {GAME_ID}_RULES_PATH from .env
uv run python pipeline/parse_raw_tables.py <game_id>
uv run python pipeline/convert_to_web.py
```

## Validate

After regenerating:

1. Check parser output for reasonable unit counts
2. Run `make build` to catch any type errors
3. Visually inspect in browser with `make dev` if needed

## Data Flow

```
PDF → pipeline/raw_table_extractor.py → raw/{game}_raw_tables.json
                                       ↓
                              game_configs.json (column mappings)
                                       ↓
                              pipeline/parse_raw_tables.py → parsed/{game}_parsed.json
                                       ↓
                              pipeline/convert_to_web.py → web/public/data/{game}.json
```
