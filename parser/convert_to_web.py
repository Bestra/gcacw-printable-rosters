#!/usr/bin/env python3
"""Convert parser output to web-friendly JSON format."""

import json
from pathlib import Path


# Game configurations
GAMES = [
    {
        "id": "otr2",
        "name": "On To Richmond!",
        "parser_output": "all_scenarios.json",
        "web_output": "otr2.json",
    },
    {
        "id": "gtc2",
        "name": "Grant Takes Command",
        "parser_output": "gtc2_scenarios.json",
        "web_output": "gtc2.json",
    },
    {
        "id": "hsn",
        "name": "Hood Strikes North",
        "parser_output": "hsn_scenarios.json",
        "web_output": "hsn.json",
    },
    {
        "id": "hcr",
        "name": "Here Come the Rebels!",
        "parser_output": "hcr_scenarios.json",
        "web_output": "hcr.json",
    },
]


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


def is_gunboat(unit: dict) -> bool:
    """Check if a unit is a gunboat."""
    name = unit.get("unit_leader", "")
    return name.startswith("Gunboat") or name.startswith("(Gunboat")


def convert_gunboat(unit: dict) -> dict:
    """Convert a gunboat unit to a simple text representation."""
    name = unit["unit_leader"]
    location = unit["hex_location"]
    return {
        "name": name,
        "location": location,
    }


def convert_scenario(scenario: dict) -> dict:
    """Convert a scenario from parser format to web format."""
    # Separate gunboats from regular units
    csa_units = [u for u in scenario["confederate_units"] if not is_gunboat(u)]
    csa_gunboats = [u for u in scenario["confederate_units"] if is_gunboat(u)]
    usa_units = [u for u in scenario["union_units"] if not is_gunboat(u)]
    usa_gunboats = [u for u in scenario["union_units"] if is_gunboat(u)]
    
    return {
        "number": scenario["number"],
        "name": scenario["name"],
        "gameLength": scenario["game_length"],
        "mapInfo": scenario["map_info"],
        "confederateFootnotes": scenario["confederate_footnotes"],
        "unionFootnotes": scenario["union_footnotes"],
        "confederateUnits": [convert_unit(u) for u in csa_units],
        "unionUnits": [convert_unit(u) for u in usa_units],
        "confederateGunboats": [convert_gunboat(u) for u in csa_gunboats],
        "unionGunboats": [convert_gunboat(u) for u in usa_gunboats],
    }


def convert_game_data(scenarios: list, game_id: str, game_name: str) -> dict:
    """Convert full parser output to web format."""
    return {
        "id": game_id,
        "name": game_name,
        "scenarios": [convert_scenario(s) for s in scenarios],
    }


def main():
    parser_dir = Path(__file__).parent
    web_data_dir = Path(__file__).parent.parent / "web" / "public" / "data"

    # Ensure output directory exists
    web_data_dir.mkdir(parents=True, exist_ok=True)

    # Create games index
    games_index = {"games": []}

    for game in GAMES:
        parser_output = parser_dir / game["parser_output"]
        web_output = web_data_dir / game["web_output"]

        if not parser_output.exists():
            print(f"Skipping {game['name']}: {parser_output} not found")
            continue

        # Load parser output
        with open(parser_output) as f:
            scenarios = json.load(f)

        # Convert to web format
        game_data = convert_game_data(scenarios, game["id"], game["name"])

        # Write web output
        with open(web_output, "w") as f:
            json.dump(game_data, f, indent=2)

        print(f"Converted {len(scenarios)} scenarios to {web_output}")
        print(f"  Confederate units: {sum(len(s['confederateUnits']) for s in game_data['scenarios'])}")
        print(f"  Union units: {sum(len(s['unionUnits']) for s in game_data['scenarios'])}")

        # Add to games index
        games_index["games"].append({
            "id": game["id"],
            "name": game["name"],
            "file": game["web_output"],
        })

    # Write games index
    games_index_path = web_data_dir / "games.json"
    with open(games_index_path, "w") as f:
        json.dump(games_index, f, indent=2)
    print(f"\nWrote games index to {games_index_path}")


if __name__ == "__main__":
    main()
