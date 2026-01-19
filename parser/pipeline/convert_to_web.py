#!/usr/bin/env python3
"""Convert parsed scenario data to web-friendly JSON format.

Reads from parsed/{game}_parsed.json (output of parse_raw_tables.py)
and writes to web/public/data/{game}.json
"""

import json
import re
from pathlib import Path


# Game configurations - now using parsed/ directory output
GAMES = [
    {"id": "otr2", "name": "On To Richmond!"},
    {"id": "gtc2", "name": "Grant Takes Command"},
    {"id": "hsn", "name": "Hood Strikes North"},
    {"id": "hcr", "name": "Here Come the Rebels!"},
    {"id": "rtg2", "name": "Roads to Gettysburg 2"},
    {"id": "rwh", "name": "Rebels in the White House"},
    {"id": "tom", "name": "Thunder on the Mississippi"},
    {"id": "tpc", "name": "The Petersburg Campaign"},
    {"id": "aga", "name": "All Green Alike"},
    {"id": "sjw", "name": "Stonewall Jackson's Way"},
]


def load_hex_config():
    """Load hex location config for validation."""
    config_path = Path(__file__).parent.parent / "utils" / "hex_location_config.json"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return json.load(f)


def validate_hex_location(hex_loc: str, config: dict) -> tuple[bool, str | None]:
    """Check if a hex location matches known patterns.
    
    Returns (is_valid, reason) where reason explains why it's unrecognized.
    """
    if not hex_loc or not hex_loc.strip():
        return True, None  # Empty is fine
    
    hex_loc = hex_loc.strip()
    
    # Check known unparseable strings (these are expected)
    for unparseable in config.get("knownUnparseable", []):
        if unparseable.lower() in hex_loc.lower():
            return True, None
    
    # Check special locations
    for pattern in config.get("specialLocations", {}):
        if hex_loc.lower() == pattern.lower():
            return True, None
    
    # Try each pattern
    for pattern_config in config.get("patterns", []):
        flags = 0 if pattern_config.get("type") == "hex" else re.IGNORECASE
        try:
            regex = re.compile(pattern_config["regex"], flags)
            if regex.match(hex_loc):
                return True, None
        except re.error:
            continue
    
    # Check if it looks like a hex code we don't recognize
    # Pattern: optional prefix + letter + 4 digits
    hex_match = re.match(r'^([A-Z]+)\s+([A-Z])(\d{4})', hex_loc)
    if hex_match:
        prefix = hex_match.group(1)
        letter = hex_match.group(2)
        known_prefixes = config.get("gameMapPrefixes", [])
        # Extract known hex letters from first pattern's regex
        first_pattern = config.get("patterns", [{}])[0].get("regex", "")
        known_letters_match = re.search(r'\[([A-Z]+)\]', first_pattern)
        known_letters = known_letters_match.group(1) if known_letters_match else "NSM"
        
        if prefix not in known_prefixes:
            return False, f"Unknown map prefix '{prefix}' (known: {known_prefixes})"
        if letter not in known_letters:
            return False, f"Unknown hex letter '{letter}' (known: {known_letters})"
    
    # Fallback: if it starts with a known prefix or looks like plain hex, it might be okay
    # but flag anything else as potentially unrecognized
    if re.match(r'^[A-Z]\d{4}', hex_loc):
        return True, None  # Plain hex like N4321
    
    return False, "No pattern matched"


def convert_unit(unit: dict) -> dict:
    """Convert a unit from parser format to web format."""
    result = {
        "name": unit["unit_leader"],
        "size": unit["size"],
        "command": unit["command"],
        "type": unit["unit_type"],
        "manpowerValue": unit["manpower_value"],
        "hexLocation": unit["hex_location"],
        "notes": unit["notes"],
    }
    # Include reinforcement set if present
    if unit.get("reinforcement_set"):
        result["reinforcementSet"] = unit["reinforcement_set"]
    # Include table name if present
    if unit.get("table_name"):
        result["tableName"] = unit["table_name"]
    return result


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
        "confederateFootnotes": scenario.get("confederate_footnotes", {}),
        "unionFootnotes": scenario.get("union_footnotes", {}),
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
    parser_dir = Path(__file__).parent.parent  # Go up from pipeline/ to parser/
    parsed_dir = parser_dir / "parsed"
    web_data_dir = parser_dir.parent / "web" / "public" / "data"

    # Ensure output directory exists
    web_data_dir.mkdir(parents=True, exist_ok=True)

    # Load hex config for validation
    hex_config = load_hex_config()
    if not hex_config:
        print("Warning: Could not load hex_location_config.json, skipping hex validation")
    
    # Track unrecognized hex patterns across all games
    all_unrecognized = []

    # Create games index
    games_index = {"games": []}

    for game in GAMES:
        game_id = game["id"]
        parser_output = parsed_dir / f"{game_id}_parsed.json"
        web_output = web_data_dir / f"{game_id}.json"

        if not parser_output.exists():
            print(f"Skipping {game['name']}: {parser_output} not found")
            continue

        # Load parser output
        with open(parser_output) as f:
            scenarios = json.load(f)

        # Convert to web format
        game_data = convert_game_data(scenarios, game_id, game["name"])
        
        # Validate hex locations if config is available
        if hex_config:
            game_unrecognized = []
            for scenario in game_data["scenarios"]:
                for unit in scenario["confederateUnits"] + scenario["unionUnits"]:
                    hex_loc = unit.get("hexLocation", "")
                    is_valid, reason = validate_hex_location(hex_loc, hex_config)
                    if not is_valid:
                        game_unrecognized.append({
                            "game": game_id,
                            "scenario": scenario["number"],
                            "unit": unit["name"],
                            "hex": hex_loc,
                            "reason": reason,
                        })
            if game_unrecognized:
                all_unrecognized.extend(game_unrecognized)

        # Write web output
        with open(web_output, "w") as f:
            json.dump(game_data, f, indent=2)

        print(f"Converted {len(scenarios)} scenarios to {web_output}")
        print(f"  Confederate units: {sum(len(s['confederateUnits']) for s in game_data['scenarios'])}")
        print(f"  Union units: {sum(len(s['unionUnits']) for s in game_data['scenarios'])}")

        # Add to games index
        games_index["games"].append({
            "id": game_id,
            "name": game["name"],
            "file": f"{game_id}.json",
        })

    # Report unrecognized hex patterns
    if all_unrecognized:
        print(f"\n⚠️  Found {len(all_unrecognized)} unrecognized hex location patterns:")
        # Group by reason for cleaner output
        by_reason: dict[str, list] = {}
        for item in all_unrecognized:
            reason = item["reason"] or "Unknown"
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(item)
        
        for reason, items in by_reason.items():
            print(f"\n  {reason}:")
            # Show up to 5 examples per reason
            for item in items[:5]:
                print(f"    - {item['game']} S{item['scenario']}: {item['unit']} at '{item['hex']}'")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")
        
        print(f"\n  → Update parser/utils/hex_location_config.json to fix")

    # Write games index
    games_index_path = web_data_dir / "games.json"
    with open(games_index_path, "w") as f:
        json.dump(games_index, f, indent=2)
    print(f"\nWrote games index to {games_index_path}")


if __name__ == "__main__":
    main()
