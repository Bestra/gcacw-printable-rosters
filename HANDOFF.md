# Handoff: GCACW Scenario Parser

## What Was Built

A Python PDF parser that extracts unit setup tables from GCACW (Great Campaigns of the American Civil War) rulebook PDFs.

## Key Files

- `parser/scenario_parser.py` - Main parser with `ScenarioParser` class
- `parser/all_scenarios.json` - Parsed data from On To Richmond! (9 scenarios, 604 units)
- `parser/all_scenarios_units.csv` - Flat CSV export
- `PLAN.md` - Project roadmap for the web app

## Parser Details

**Usage:**
```bash
cd parser
uv run python scenario_parser.py ../data/OTR2_Rules.pdf
```

**Key parsing challenges solved:**
1. Tables span multiple pages with `(cntd)` continuation headers
2. Multi-word unit names like "RH Anderson", "Art Res-1", "DH Hill"
3. Special units (Gunboat, Wagon Train, Naval Battery) with `-` for size/type
4. Multiple footnote markers: `*`, `^`, `$`, `+`
5. Scenarios starting on same page where previous scenario's table ends

**Known scenario names are hardcoded** (line ~80 in scenario_parser.py) for OTR2:
```python
known_names = {
    1: "The Warwick Line",
    2: "Johnston's Retreat", 
    3: "The Gates of Richmond",
    ...
}
```
Other rulebooks will need their own name mappings.

## Next Steps (from PLAN.md)

1. **Convert JSON format** - Transform `all_scenarios.json` to simpler web-friendly schema
2. **Create web/ directory** - Vite + React scaffold
3. **UnitCard component** - Counter box at 0.55" (14mm) for 1/2" counters
4. **RosterSheet component** - Horizontal rows of UnitCards
5. **Print CSS** - `@media print` with exact sizing
6. **GitHub Pages deploy** - GitHub Actions workflow

## Data Schema for Web

The current JSON has nested dataclass structure. Simplify to:
```json
{
  "id": "otr2",
  "name": "On To Richmond!",
  "scenarios": [{
    "number": 1,
    "name": "The Warwick Line",
    "confederateUnits": [{ "name": "...", "size": "...", ... }],
    "unionUnits": [...]
  }]
}
```

## Print Layout

Target: US Letter, units in horizontal rows, counter boxes at 0.55" square.
Group by side (Confederate/Union), optionally by command.
