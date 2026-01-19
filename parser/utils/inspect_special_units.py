#!/usr/bin/env python3
"""
Utility to inspect special units (Wagon Train, Gunboat, Naval Battery) across games.

Usage:
    uv run python utils/inspect_special_units.py                    # All games
    uv run python utils/inspect_special_units.py hsn               # Single game
    uv run python utils/inspect_special_units.py hsn --scenario 2  # Single scenario
    uv run python utils/inspect_special_units.py --type wagon      # Filter by type
"""

import argparse
import json
import sys
from pathlib import Path


def load_parsed_data(game_id: str) -> list:
    """Load parsed JSON for a game."""
    parsed_path = Path(__file__).parent.parent / "parsed" / f"{game_id}_parsed.json"
    if not parsed_path.exists():
        return []
    with open(parsed_path) as f:
        return json.load(f)


def get_available_games() -> list[str]:
    """Get list of available games from parsed directory."""
    parsed_dir = Path(__file__).parent.parent / "parsed"
    return sorted([
        p.stem.replace("_parsed", "") 
        for p in parsed_dir.glob("*_parsed.json")
    ])


def filter_special_units(units: list, unit_type: str | None = None) -> list:
    """Filter units to only include special units."""
    special = []
    for u in units:
        name = u.get("unit_leader", "").lower()
        if u.get("unit_type") == "Special" or any(x in name for x in ["wagon train", "gunboat", "naval battery"]):
            if unit_type is None:
                special.append(u)
            elif unit_type.lower() == "wagon" and "wagon" in name:
                special.append(u)
            elif unit_type.lower() == "gunboat" and "gunboat" in name:
                special.append(u)
            elif unit_type.lower() == "naval" and "naval" in name:
                special.append(u)
    return special


def format_unit(unit: dict) -> str:
    """Format a unit for display."""
    name = unit.get("unit_leader", "?")
    hex_loc = unit.get("hex_location", "")
    side = unit.get("side", "?")
    table = unit.get("table_name", "")
    
    parts = [f"  {name:25}"]
    if hex_loc:
        parts.append(f"  Hex: {hex_loc:30}")
    else:
        parts.append(f"  Hex: {'<MISSING>':30}")
    parts.append(f"  Side: {side:12}")
    if table:
        parts.append(f"  Table: {table}")
    return "".join(parts)


def inspect_game(game_id: str, scenario_num: int | None = None, unit_type: str | None = None) -> dict:
    """Inspect special units in a game. Returns stats dict."""
    data = load_parsed_data(game_id)
    if not data:
        return {"error": f"No data for {game_id}"}
    
    stats = {
        "game": game_id,
        "total_special": 0,
        "missing_hex": 0,
        "scenarios": []
    }
    
    for scenario in data:
        if scenario_num is not None and scenario.get("number") != scenario_num:
            continue
        
        all_units = scenario.get("confederate_units", []) + scenario.get("union_units", [])
        special = filter_special_units(all_units, unit_type)
        
        if not special:
            continue
        
        scenario_stats = {
            "number": scenario.get("number"),
            "name": scenario.get("name"),
            "units": []
        }
        
        for u in special:
            stats["total_special"] += 1
            if not u.get("hex_location"):
                stats["missing_hex"] += 1
            scenario_stats["units"].append({
                "name": u.get("unit_leader"),
                "hex": u.get("hex_location"),
                "side": u.get("side"),
                "table": u.get("table_name"),
            })
        
        stats["scenarios"].append(scenario_stats)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Inspect special units across games")
    parser.add_argument("game", nargs="?", help="Game ID (e.g., hsn, otr2)")
    parser.add_argument("--scenario", "-s", type=int, help="Scenario number")
    parser.add_argument("--type", "-t", choices=["wagon", "gunboat", "naval"], 
                        help="Filter by unit type")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    games = [args.game] if args.game else get_available_games()
    
    all_stats = []
    total_special = 0
    total_missing = 0
    
    for game_id in games:
        stats = inspect_game(game_id, args.scenario, args.type)
        if "error" in stats:
            continue
        all_stats.append(stats)
        total_special += stats["total_special"]
        total_missing += stats["missing_hex"]
    
    if args.json:
        print(json.dumps(all_stats, indent=2))
        return
    
    # Pretty print
    for stats in all_stats:
        print(f"\n{'='*70}")
        print(f"Game: {stats['game'].upper()}")
        print(f"{'='*70}")
        
        if not stats["scenarios"]:
            print("  No special units found")
            continue
        
        for scenario in stats["scenarios"]:
            print(f"\nScenario {scenario['number']}: {scenario['name']}")
            for u in scenario["units"]:
                hex_display = u['hex'] if u['hex'] else '<MISSING>'
                mark = "⚠️ " if not u['hex'] else "   "
                print(f"  {mark}{u['name']:25} Hex: {hex_display:30} ({u['side']})")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total special units: {total_special}")
    if total_missing > 0:
        print(f"Missing hex locations: {total_missing} ⚠️")
    else:
        print(f"Missing hex locations: 0 ✓")


if __name__ == "__main__":
    main()
