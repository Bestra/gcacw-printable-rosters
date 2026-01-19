````skill
---
name: troubleshooting
description: Diagnose and fix common issues in the GCACW parser and web app. Use when something isn't working as expected, tests are failing, data looks wrong, or the user reports a bug.
---

# Troubleshooting

Common issues, their causes, and how to fix them.

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| "Module not found" in Python | Forgot `uv run` | Use `uv run python ...` |
| Web shows stale data | Didn't regenerate after parser change | `make {game}` or `make` |
| TypeScript errors after parser change | Web JSON structure changed | Update `web/src/types.ts` |
| Test fails with "Cannot find module" | Missing npm install | `cd web && npm install` |
| jq returns nothing | Wrong JSON structure (parsed vs web) | See JSON structure table below |
| "Game not found" in browser | Missing slug mapping | Add to `web/src/utils/slugs.ts` |
| Units missing from roster | Parsing skipped them | Use `inspect_parsed.py` to debug |
| Wrong unit attributes | Column mapping mismatch | Check `game_configs.json` |
| Garbled text from PDF | PDF extraction issue | See debug-pdf-extraction skill |

## Decision Trees

### "Fix a parsing bug"

1. Identify affected game(s) and scenario(s)
2. Check raw extraction:
   ```bash
   cd parser && uv run python utils/inspect_raw.py GAME --scenario N
````

- If data is wrong/missing here → Problem is in `raw_table_extractor.py` or PDF
- If data looks correct → Continue to step 3

3. Check parsed output:
   ```bash
   cd parser && uv run python utils/inspect_parsed.py GAME --scenario N
   ```

   - If data is wrong/missing here → Problem is in `parse_raw_tables.py` or `game_configs.json`
   - If data looks correct → Problem is in `convert_to_web.py` or frontend
4. After fixing, regenerate: `make GAME`
5. Validate: visual check + `make test`

### "Web app shows wrong data"

1. Check web JSON directly:
   ```bash
   cat web/public/data/GAME.json | jq '.scenarios[N-1].unionUnits | length'
   ```
2. Compare to parsed JSON:
   ```bash
   cat parser/parsed/GAME_parsed.json | jq '.[N-1].union_units | length'
   ```
3. If counts differ → Problem in `convert_to_web.py`
4. If counts match but data wrong → Check specific fields in both files

### "Unit images not showing"

1. Check image mapping exists:
   ```bash
   cat web/src/data/GAME_images.json | jq '.matched["SIDE:UnitName"]'
   ```
2. Check image file exists:
   ```bash
   ls web/public/images/counters/GAME/ | grep -i "unitname"
   ```
3. If mapping missing → Re-run image extraction (see extract-vassal-images skill)
4. If file missing → Check VASSAL module for the image

## Post-Change Verification

What to check after modifying each area:

| Changed               | Verify with                                             |
| --------------------- | ------------------------------------------------------- |
| `parse_raw_tables.py` | `make test`, `utils/inspect_parsed.py`, regenerate data |
| `game_configs.json`   | `make {affected-game}`, inspect parsed output           |
| `convert_to_web.py`   | `make`, check web JSON structure                        |
| `UnitCard.tsx`        | Visual check in browser, `make snapshots`               |
| `RosterSheet.tsx`     | Visual check, `make snapshots`                          |
| `types.ts`            | `make build` (TypeScript catches mismatches)            |
| `App.tsx`             | Visual check, game/scenario selection works             |

## Running Tests

```bash
# Parser tests
cd parser && uv run pytest                                    # All
cd parser && uv run pytest tests/test_parse_raw_tables.py     # Specific file
cd parser && uv run pytest -k "test_name"                     # By name pattern

# Web tests
cd web && npm test                                            # All
cd web && npm test -- path/to/test.test.tsx                   # Specific file
cd web && npm test -- -t "test name"                          # By name pattern
```

## JSON Structure Quick Reference

**CRITICAL**: Parsed and web JSON have different structures:

| Aspect            | Parsed (`parsed/*.json`) | Web (`web/public/data/*.json`) |
| ----------------- | ------------------------ | ------------------------------ |
| Root              | Array `[...]`            | Object `{scenarios: [...]}`    |
| Access scenario 2 | `.[1]`                   | `.scenarios[1]`                |
| Field naming      | `snake_case`             | `camelCase`                    |
| Unit name         | `unit_leader`            | `name`                         |
| Units arrays      | `confederate_units`      | `confederateUnits`             |

## Common jq Patterns

```bash
# Parsed: scenario 2 confederate units
cat parsed/gtc2_parsed.json | jq '.[1].confederate_units'

# Web: scenario 2 confederate units
cat web/public/data/gtc2.json | jq '.scenarios[1].confederateUnits'

# Count units
jq '.[1].union_units | length' parsed/gtc2_parsed.json
jq '.scenarios[1].unionUnits | length' web/public/data/gtc2.json

# Find unit by name
jq '.[1].union_units[] | select(.unit_leader | contains("Meade"))' parsed/gtc2_parsed.json
```

## Generated Files (Do NOT Edit)

These files are generated by the pipeline. Edit the source instead:

| File                           | Regenerate with                                      |
| ------------------------------ | ---------------------------------------------------- |
| `parser/raw/*.json`            | `uv run python pipeline/raw_table_extractor.py GAME` |
| `parser/parsed/*.json`         | `uv run python pipeline/parse_raw_tables.py GAME`    |
| `web/public/data/*.json`       | `uv run python pipeline/convert_to_web.py`           |
| `parser/image_mappings/*.json` | Image extraction scripts                             |

## Related Skills

- **data-structures**: Full JSON schemas and field mappings
- **debug-pdf-extraction**: PDF text extraction issues
- **regenerate-data**: Refreshing data after changes

```

```
