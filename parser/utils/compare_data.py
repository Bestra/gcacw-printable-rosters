#!/usr/bin/env python3
"""
Compare raw vs parsed data for debugging

Shows side-by-side comparison of raw table rows and parsed units to help
debug parsing issues.

Usage:
    uv run python compare_data.py <game_id> <scenario_number> [options]
    
Examples:
    uv run python compare_data.py gtc2 1
    uv run python compare_data.py gtc2 1 --side Confederate
    uv run python compare_data.py gtc2 1 --table "Confederate Set-Up"
    uv run python compare_data.py otr2 9 --row 5
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional


def load_data(game_id: str):
    """Load both raw and parsed data."""
    parser_dir = Path(__file__).parent
    
    raw_file = parser_dir / "raw" / f"{game_id}_raw_tables.json"
    parsed_file = parser_dir / "parsed" / f"{game_id}_parsed.json"
    
    if not raw_file.exists():
        print(f"Error: {raw_file} not found")
        sys.exit(1)
    
    if not parsed_file.exists():
        print(f"Error: {parsed_file} not found")
        sys.exit(1)
    
    with open(raw_file) as f:
        raw_data = json.load(f)
    
    with open(parsed_file) as f:
        parsed_data = json.load(f)
    
    return raw_data, parsed_data


def compare_scenario(raw_scenario: dict, parsed_scenario: dict, 
                     side_filter: Optional[str] = None,
                     table_filter: Optional[str] = None,
                     row_number: Optional[int] = None):
    """Compare raw and parsed data for a scenario."""
    num = raw_scenario['scenario_number']
    name = raw_scenario['scenario_name']
    
    print(f"\n{'='*80}")
    print(f"Scenario {num}: {name}")
    print(f"{'='*80}\n")
    
    # Compare Confederate data
    if side_filter is None or side_filter.lower() == 'confederate':
        print("CONFEDERATE DATA:\n")
        compare_side(
            raw_scenario.get('confederate_tables', []),
            parsed_scenario.get('confederate_units', []),
            'Confederate',
            table_filter,
            row_number
        )
    
    # Compare Union data
    if side_filter is None or side_filter.lower() == 'union':
        print("\n\nUNION DATA:\n")
        compare_side(
            raw_scenario.get('union_tables', []),
            parsed_scenario.get('union_units', []),
            'Union',
            table_filter,
            row_number
        )


def compare_side(raw_tables: list, parsed_units: list, side: str,
                 table_filter: Optional[str] = None,
                 row_number: Optional[int] = None):
    """Compare raw tables and parsed units for one side."""
    for table in raw_tables:
        table_name = table['name']
        
        # Apply table filter
        if table_filter and table_filter.lower() not in table_name.lower():
            continue
        
        print(f"Table: {table_name}")
        print(f"  Pages: {', '.join(map(str, table['page_numbers']))}")
        
        header = table.get('header_row', [])
        rows = table.get('rows', [])
        
        if header:
            print(f"  Header: {' | '.join(header)}\n")
        
        # Match parsed units to this table
        table_units = [u for u in parsed_units if u.get('table_name') == table_name]
        if not table_units:
            # If no table_name, try to match all units (for games without table_name)
            table_units = parsed_units
        
        print(f"  Raw rows: {len(rows)}")
        print(f"  Parsed units: {len(table_units)}\n")
        
        # Show row-by-row comparison
        if row_number is not None:
            # Show specific row
            if 1 <= row_number <= len(rows):
                show_row_comparison(rows[row_number - 1], row_number, table_units)
            else:
                print(f"  Error: Row {row_number} not found (table has {len(rows)} rows)")
        else:
            # Show all rows
            for i, row in enumerate(rows, 1):
                show_row_comparison(row, i, table_units)
        
        # Show any annotations
        annotations = table.get('annotations', {})
        if annotations:
            print(f"\n  Footnotes:")
            for symbol, text in annotations.items():
                print(f"    {symbol} = {text}")
        
        print()


def show_row_comparison(raw_row: list, row_num: int, parsed_units: list):
    """Show comparison between a raw row and matching parsed unit."""
    print(f"  [{row_num}] Raw: {' | '.join(raw_row)}")
    
    # Try to find matching parsed unit
    # Match by name (first tokens usually)
    name_tokens = raw_row[:3]  # First few tokens are usually the name
    
    matches = []
    for unit in parsed_units:
        unit_name = unit['unit_leader']
        # Check if any name token appears in the unit name
        if any(token.lower() in unit_name.lower() for token in name_tokens if token):
            matches.append(unit)
    
    if matches:
        # Show the best match (first one, or closest name match)
        unit = matches[0]
        print(f"      ↓")
        print(f"      Parsed: {unit['unit_leader']:20} | "
              f"{unit['size']:8} | {unit['command']:6} | "
              f"{unit['unit_type']:4} | MP:{unit['manpower_value']:4} | "
              f"@ {unit['hex_location']}")
        if unit.get('notes'):
            print(f"              Notes: {', '.join(unit['notes'])}")
    else:
        print(f"      ⚠ No matching parsed unit found")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare raw vs parsed data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python compare_data.py gtc2 1
  uv run python compare_data.py gtc2 1 --side Confederate
  uv run python compare_data.py gtc2 1 --table "Confederate Set-Up"
  uv run python compare_data.py otr2 9 --row 5
  uv run python compare_data.py hcr 1 --side Union --table "Turn 5"
        """
    )
    
    parser.add_argument('game_id', help='Game ID (gtc2, otr2, hcr, etc.)')
    parser.add_argument('scenario', type=int, help='Scenario number to compare')
    parser.add_argument('--side', choices=['Confederate', 'Union'], help='Compare only one side')
    parser.add_argument('--table', '-t', help='Filter to specific table name')
    parser.add_argument('--row', '-r', type=int, help='Show only specific row number')
    
    args = parser.parse_args()
    
    # Load data
    raw_data, parsed_data = load_data(args.game_id)
    
    # Find matching scenarios
    raw_scenario = next((s for s in raw_data if s['scenario_number'] == args.scenario), None)
    parsed_scenario = next((s for s in parsed_data if s['number'] == args.scenario), None)
    
    if not raw_scenario:
        print(f"Error: Scenario {args.scenario} not found in raw data")
        sys.exit(1)
    
    if not parsed_scenario:
        print(f"Error: Scenario {args.scenario} not found in parsed data")
        sys.exit(1)
    
    # Compare
    compare_scenario(
        raw_scenario, 
        parsed_scenario, 
        args.side,
        args.table,
        args.row
    )


if __name__ == '__main__':
    main()
