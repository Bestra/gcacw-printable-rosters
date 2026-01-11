#!/usr/bin/env python3
"""Convert parser output to web-friendly JSON format."""

import json
from pathlib import Path


def convert_unit(unit: dict) -> dict:
    """Convert a unit from parser format to web format."""
    return {
        "name": unit["unit_leader"],
        "size": unit["size"],
        "command": unit["command"],
        "type": unit["unit_type"],
        "manpowerValue": unit["manpower_value"],
        "hexLocation": unit["hex_location"],
        "notes": unit["notes"],
    }


def convert_scenario(scenario: dict) -> dict:
    """Convert a scenario from parser format to web format."""
    return {
        "number": scenario["number"],
        "name": scenario["name"],
        "gameLength": scenario["game_length"],
        "mapInfo": scenario["map_info"],
        "footnotes": scenario["footnotes"],
        "confederateUnits": [convert_unit(u) for u in scenario["confederate_units"]],
        "unionUnits": [convert_unit(u) for u in scenario["union_units"]],
    }


def convert_game_data(scenarios: list, game_id: str, game_name: str) -> dict:
    """Convert full parser output to web format."""
    return {
        "id": game_id,
        "name": game_name,
        "scenarios": [convert_scenario(s) for s in scenarios],
    }


def main():
    parser_output = Path(__file__).parent / "all_scenarios.json"
    web_output = Path(__file__).parent.parent / "web" / "public" / "data" / "otr2.json"

    # Ensure output directory exists
    web_output.parent.mkdir(parents=True, exist_ok=True)

    # Load parser output
    with open(parser_output) as f:
        scenarios = json.load(f)

    # Convert to web format
    game_data = convert_game_data(scenarios, "otr2", "On To Richmond!")

    # Write web output
    with open(web_output, "w") as f:
        json.dump(game_data, f, indent=2)

    print(f"Converted {len(scenarios)} scenarios to {web_output}")
    print(f"Total Confederate units: {sum(len(s['confederateUnits']) for s in game_data['scenarios'])}")
    print(f"Total Union units: {sum(len(s['unionUnits']) for s in game_data['scenarios'])}")


if __name__ == "__main__":
    main()
