#!/usr/bin/env python3
"""
Inspect parsed unit data from {game}_parsed.json

Quick utility to view structured parsed data, useful for verifying unit parsing.

Usage:
    uv run python inspect_parsed.py <game_id> [options]
    
Examples:
    uv run python inspect_parsed.py gtc2
    uv run python inspect_parsed.py gtc2 --scenario 1
    uv run python inspect_parsed.py otr2 --list-scenarios
    uv run python inspect_parsed.py gtc2 --scenario 1 --side Confederate
    uv run python inspect_parsed.py gtc2 --scenario 1 --filter Longstreet
    uv run python inspect_parsed.py hsn --scenario 1 --leaders-only
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional


def load_parsed_data(game_id: str) -> list:
    """Load parsed scenario data for a game."""
    parsed_file = Path(__file__).parent.parent / "parsed" / f"{game_id}_parsed.json"
    if not parsed_file.exists():
        print(f"Error: {parsed_file} not found")
        print(f"Run: make reparse-{game_id}")
        sys.exit(1)
    
    with open(parsed_file) as f:
        return json.load(f)


def list_scenarios(data: list):
    """List all scenarios in the data."""
    print(f"\n{'='*70}")
    print(f"Found {len(data)} scenarios\n")
    
    for scenario in data:
        num = scenario['number']
        name = scenario['name']
        page = scenario['start_page']
        
        csa_units = len(scenario.get('confederate_units', []))
        usa_units = len(scenario.get('union_units', []))
        csa_notes = len(scenario.get('confederate_footnotes', {}))
        usa_notes = len(scenario.get('union_footnotes', {}))
        
        print(f"Scenario {num}: {name} (page {page})")
        print(f"  Confederate: {csa_units} units, {csa_notes} footnotes")
        print(f"  Union: {usa_units} units, {usa_notes} footnotes")


def show_scenario_detail(scenario: dict, side_filter: Optional[str] = None,
                         name_filter: Optional[str] = None, leaders_only: bool = False,
                         show_footnotes: bool = True):
    """Show detailed info for a single scenario."""
    num = scenario['number']
    name = scenario['name']
    page = scenario['start_page']
    
    print(f"\n{'='*70}")
    print(f"Scenario {num}: {name} (page {page})")
    print(f"{'='*70}\n")
    
    # Confederate units
    if side_filter is None or side_filter.lower() == 'confederate':
        csa_units = scenario.get('confederate_units', [])
        if csa_units:
            print("CONFEDERATE UNITS:\n")
            show_units(csa_units, name_filter, leaders_only)
            
            if show_footnotes:
                csa_footnotes = scenario.get('confederate_footnotes', {})
                if csa_footnotes:
                    print("\nConfederate Footnotes:")
                    for symbol, text in csa_footnotes.items():
                        print(f"  {symbol} = {text}")
    
    # Union units
    if side_filter is None or side_filter.lower() == 'union':
        usa_units = scenario.get('union_units', [])
        if usa_units:
            print("\n\nUNION UNITS:\n")
            show_units(usa_units, name_filter, leaders_only)
            
            if show_footnotes:
                usa_footnotes = scenario.get('union_footnotes', {})
                if usa_footnotes:
                    print("\nUnion Footnotes:")
                    for symbol, text in usa_footnotes.items():
                        print(f"  {symbol} = {text}")


def show_units(units: list, name_filter: Optional[str] = None, leaders_only: bool = False):
    """Display units in a readable format."""
    filtered = units
    
    # Apply name filter
    if name_filter:
        filtered = [u for u in filtered if name_filter.lower() in u['unit_leader'].lower()]
    
    # Apply leaders filter
    if leaders_only:
        filtered = [u for u in filtered if u['unit_type'] == 'Ldr']
    
    if not filtered:
        print("  (No units match the filter)")
        return
    
    # Group by type for better readability
    leaders = [u for u in filtered if u['unit_type'] == 'Ldr']
    infantry = [u for u in filtered if u['unit_type'] == 'Inf']
    cavalry = [u for u in filtered if u['unit_type'] == 'Cav']
    artillery = [u for u in filtered if u['unit_type'] == 'Art']
    special = [u for u in filtered if u['unit_type'] == 'Special']
    
    if leaders:
        print(f"  Leaders ({len(leaders)}):")
        for unit in leaders:
            show_unit(unit, indent=4)
    
    if infantry:
        print(f"\n  Infantry ({len(infantry)}):")
        for unit in infantry:
            show_unit(unit, indent=4)
    
    if cavalry:
        print(f"\n  Cavalry ({len(cavalry)}):")
        for unit in cavalry:
            show_unit(unit, indent=4)
    
    if artillery:
        print(f"\n  Artillery ({len(artillery)}):")
        for unit in artillery:
            show_unit(unit, indent=4)
    
    if special:
        print(f"\n  Special ({len(special)}):")
        for unit in special:
            show_unit(unit, indent=4)
    
    print(f"\n  Total: {len(filtered)} units")


def show_unit(unit: dict, indent: int = 0):
    """Display a single unit."""
    prefix = ' ' * indent
    name = unit['unit_leader']
    size = unit['size']
    cmd = unit['command']
    utype = unit['unit_type']
    mp = unit['manpower_value']
    hex_loc = unit['hex_location']
    notes = unit.get('notes', [])
    turn = unit.get('turn')
    rset = unit.get('reinforcement_set')
    table = unit.get('table_name')
    
    # Build info line
    info = f"{size:8} {cmd:6} {utype:4} MP:{mp:4}"
    
    # Add optional fields
    extras = []
    if turn:
        extras.append(f"Turn:{turn}")
    if rset:
        extras.append(f"Set:{rset}")
    if table:
        extras.append(f"Table:{table}")
    if notes:
        extras.append(f"Notes:{','.join(notes)}")
    
    if extras:
        info += "  " + " ".join(extras)
    
    print(f"{prefix}{name:25} {info}")
    if hex_loc:
        print(f"{prefix}{'':25} @ {hex_loc}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect parsed unit data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python inspect_parsed.py gtc2
  uv run python inspect_parsed.py gtc2 --scenario 1
  uv run python inspect_parsed.py gtc2 --list-scenarios
  uv run python inspect_parsed.py otr2 --scenario 9 --side Union
  uv run python inspect_parsed.py gtc2 --scenario 1 --filter Longstreet
  uv run python inspect_parsed.py hsn --scenario 1 --leaders-only
        """
    )
    
    parser.add_argument('game_id', help='Game ID (gtc2, otr2, hcr, etc.)')
    parser.add_argument('--scenario', '-s', type=int, help='Show details for specific scenario number')
    parser.add_argument('--list-scenarios', '-l', action='store_true', help='List all scenarios')
    parser.add_argument('--side', choices=['Confederate', 'Union'], help='Show only one side')
    parser.add_argument('--filter', '-f', help='Filter units by name (case-insensitive)')
    parser.add_argument('--leaders-only', action='store_true', help='Show only leader units')
    parser.add_argument('--no-footnotes', action='store_true', help='Hide footnote details')
    
    args = parser.parse_args()
    
    # Load data
    data = load_parsed_data(args.game_id)
    
    if not data:
        print(f"No scenarios found in parsed data for {args.game_id}")
        sys.exit(1)
    
    # List scenarios mode
    if args.list_scenarios:
        list_scenarios(data)
        return
    
    # Show specific scenario
    if args.scenario:
        scenario = next((s for s in data if s['number'] == args.scenario), None)
        if not scenario:
            print(f"Error: Scenario {args.scenario} not found")
            print(f"Available scenarios: {', '.join(str(s['number']) for s in data)}")
            sys.exit(1)
        
        show_scenario_detail(
            scenario, 
            args.side, 
            args.filter, 
            args.leaders_only,
            not args.no_footnotes
        )
        return
    
    # Default: list all scenarios
    list_scenarios(data)
    print("\nUse --scenario <N> to see details for a specific scenario")
    print("Use --help for more options")


if __name__ == '__main__':
    main()
