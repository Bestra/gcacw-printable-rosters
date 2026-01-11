# GCACW Scenario Parser & Roster Generator

Tools for parsing scenario setup tables from Great Campaigns of the American Civil War (GCACW) game PDFs and generating printable roster sheets.

## Overview

This project has two parts:

1. **Parser** (`parser/`) - Python tool that extracts unit data from PDF rulebooks
2. **Web App** (`web/`) - React app that generates printable roster sheets

The roster sheets provide a place to track each unit's fortifications, manpower, and fatigue markers during play, reducing counter stacking on the game map.

## Quick Start

### Run the Web App

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173 to view roster sheets. Use `Cmd+P` / `Ctrl+P` to print.

### Parse a New PDF

```bash
cd parser
uv run python scenario_parser.py ../data/YourGame.pdf
uv run python convert_to_web.py
```

## Project Structure

```
gcacw-scenario-parser/
├── parser/                     # Python PDF parser
│   ├── scenario_parser.py      # Main parser class
│   ├── convert_to_web.py       # Convert to web JSON format
│   ├── all_scenarios.json      # Raw parser output
│   └── all_scenarios_units.csv # Flat CSV export
├── web/                        # React web app
│   ├── src/
│   │   ├── components/         # React components
│   │   └── types.ts            # TypeScript interfaces
│   └── public/data/
│       └── otr2.json           # Web-formatted game data
├── data/                       # Source PDFs (gitignored)
└── .github/workflows/
    └── deploy.yml              # GitHub Pages deployment
```

## Parser

### Installation

Requires Python 3.14+ and [uv](https://github.com/astral-sh/uv):

```bash
cd parser
uv sync
```

### Usage

```bash
# Parse a PDF
uv run python scenario_parser.py ../data/OTR2_Rules.pdf

# Convert to web format
uv run python convert_to_web.py
```

Output files:

- `all_scenarios.json` - Full structured data
- `all_scenarios_units.csv` - Flat CSV of all units
- `../web/public/data/otr2.json` - Web-formatted JSON

### As a Library

```python
from scenario_parser import ScenarioParser

parser = ScenarioParser("OTR2_Rules.pdf")
scenarios = parser.parse()

for scenario in scenarios:
    print(f"{scenario.name}: {len(scenario.confederate_units)} CSA, {len(scenario.union_units)} USA")
```

### Data Structure

**Scenario:**

- `number`, `name`, `start_page`
- `game_length`, `map_info`, `notes`
- `special_rules` (list)
- `footnotes` (dict: symbol → explanation)
- `confederate_units`, `union_units` (lists)

**Unit:**

- `unit_leader` - Name or leader
- `size` - Army, Corps, Div, Demi-Div, Brig, Regt
- `command` - Affiliation (e.g., "M", "ANV", "III")
- `unit_type` - Ldr, Inf, Cav, Art
- `manpower_value` - Strength (may include \* for footnotes)
- `hex_location` - Starting hex
- `notes` - Footnote markers

## Web App

### Installation

```bash
cd web
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

Output goes to `web/dist/`.

### Deployment

Push to `main` branch triggers GitHub Actions deployment to GitHub Pages.

To enable:

1. Go to repo Settings → Pages
2. Set Source to "GitHub Actions"

## Roster Sheet Layout

Each unit card shows:

- **Header**: Unit name and command
- **Box 1**: Space for fortification marker
- **Box 2**: Starting manpower and hex location
- **Box 3**: Starting fatigue (if non-standard)

Counter boxes are 0.55" (14mm) to fit GCACW 1/2" counters.

## Supported Games

- ✅ On To Richmond! (OTR2) - 9 scenarios, 604 units
- ⬜ Stonewall Jackson's Way
- ⬜ Here Come the Rebels
- ⬜ Roads to Gettysburg
- ⬜ Grant Takes Command

## License

MIT
