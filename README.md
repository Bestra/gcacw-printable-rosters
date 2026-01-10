# GCACW Scenario Parser

A Python tool for parsing scenario setup tables from Great Campaigns of the American Civil War (GCACW) game PDFs.

## Features

- Extracts scenario metadata (name, game length, map, notes, special rules)
- Parses Confederate and Union unit setup tables
- Handles multi-word unit names (e.g., "RH Anderson", "Art Res-1")
- Captures footnote symbols (*, ^, †) and their explanations
- Exports to CSV and JSON formats

## Installation

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

## Usage

```bash
uv run python scenario_parser.py
```

This will:
1. Parse `OTR2_Rules.pdf` in the current directory
2. Output a summary of all scenarios
3. Export `all_scenarios_units.csv` - flat CSV of all units
4. Export `all_scenarios.json` - full structured data

### As a Library

```python
from scenario_parser import ScenarioParser

parser = ScenarioParser("OTR2_Rules.pdf")
scenarios = parser.parse()

# Get DataFrame of all units
df = parser.to_dataframe()

# Get JSON string
json_data = parser.to_json()

# Access individual scenarios
for scenario in scenarios:
    print(f"{scenario.name}: {len(scenario.confederate_units)} CSA, {len(scenario.union_units)} USA")
```

## Data Structure

### Scenario
- `number`: Scenario number (1-9)
- `name`: Scenario title
- `start_page`: PDF page number
- `notes`: Scenario description/notes
- `map_info`: Which maps to use
- `game_length`: Duration and dates
- `special_rules`: List of special rules
- `footnotes`: Dict mapping symbols to explanations
- `confederate_units`: List of Unit objects
- `union_units`: List of Unit objects

### Unit
- `unit_leader`: Unit name or leader name
- `size`: Army, Corps, Div, Demi-Div, Brig, Regt
- `command`: Command affiliation (e.g., "M", "ANV", "III")
- `unit_type`: Ldr, Inf, Cav, Art
- `manpower_value`: Strength value (may include markers like *)
- `hex_location`: Starting hex or placement instructions
- `side`: "Confederate" or "Union"
- `notes`: List of footnote markers that apply to this unit

## Supported PDFs

Currently configured for **On To Richmond! (OTR2)** but can be adapted for other GCACW titles.

## Output Example

```
Found 9 scenarios

Scenario 1: The Warwick Line
  Start page: 4
  Game length: 3 turns; April 5 to April 7, 1862.
  Confederate units: 15
  Union units: 15
  Footnotes: {'*': 'Sedgwick is part of Heintzelman's III Corps'}
```

## License

MIT
