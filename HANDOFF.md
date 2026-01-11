# Handoff: GCACW Scenario Parser

## Current State

Working web app that generates printable roster sheets from parsed PDF data.

## Quick Commands

```bash
# Run web app
cd web && npm run dev

# Parse PDF and convert to web format
cd parser && uv run python scenario_parser.py ../data/OTR2_Rules.pdf
cd parser && uv run python convert_to_web.py
```

## Key Files

### Parser (`parser/`)

- `scenario_parser.py` - Main PDF parser class
- `convert_to_web.py` - Transforms parser JSON → web JSON
- `all_scenarios.json` - Raw parser output (604 units)
- `pyproject.toml` - Python deps (pdfplumber, pandas)

### Web App (`web/`)

- `src/App.tsx` - Main app, loads JSON, scenario selector
- `src/components/UnitCard.tsx` - Single unit with 3 counter boxes
- `src/components/RosterSheet.tsx` - Grid of units, pads rows with empties
- `src/types.ts` - TypeScript interfaces
- `public/data/otr2.json` - Game data for On To Richmond!

### Deployment

- `.github/workflows/deploy.yml` - Auto-deploy to GitHub Pages on push to main

## Roster Card Layout

```
┌─────────────────────────────┐
│ Unit Name           Command │
├─────────┬─────────┬─────────┤
│         │   MP    │   F1    │  ← Fatigue only if non-standard
│  Fort   │   Hex   │ Fatigue │
│         │         │         │
└─────────┴─────────┴─────────┘
```

- Box 1: Fortifications marker
- Box 2: Manpower + starting hex (printed small at bottom)
- Box 3: Starting fatigue (e.g., "F1") if specified in footnotes

## Parser Notes

**Hardcoded scenario names** (line ~80 in scenario_parser.py):

```python
known_names = {
    1: "The Warwick Line",
    2: "Johnston's Retreat",
    ...
}
```

Other GCACW titles need their own mappings.

**Fatigue detection**: Parses footnotes for "Fatigue Level X" pattern.

## Next Steps

1. Add more GCACW titles (SJW, HCTR, etc.)
2. Group units by command within each side
3. Add print button to UI
4. Consider page break handling for large scenarios
