#!/usr/bin/env python3
"""
Inspect raw table data from {game}_raw_tables.json

Quick utility to view raw extracted data, useful for debugging PDF extraction issues.

Usage:
    uv run python inspect_raw.py <game_id> [options]
    
Examples:
    uv run python inspect_raw.py gtc2
    uv run python inspect_raw.py gtc2 --scenario 1
    uv run python inspect_raw.py otr2 --list-scenarios
    uv run python inspect_raw.py gtc2 --scenario 1 --table "Confederate Set-Up"
    uv run python inspect_raw.py gtc2 --scenario 1 --rows 5
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional


def load_raw_data(game_id: str) -> list:
    """Load raw table data for a game."""
    raw_file = Path(__file__).parent / "raw" / f"{game_id}_raw_tables.json"
    if not raw_file.exists():
        print(f"Error: {raw_file} not found")
        print(f"Run: make extract-{game_id}")
        sys.exit(1)
    
    with open(raw_file) as f:
        return json.load(f)


def list_scenarios(data: list):
    """List all scenarios in the data."""
    print(f"\n{'='*70}")
    print(f"Found {len(data)} scenarios\n")
    
    for scenario in data:
        num = scenario['scenario_number']
        name = scenario['scenario_name']
        start = scenario['start_page']
        end = scenario['end_page']
        adv = scenario.get('advanced_game_rules_page')
        
        csa_tables = len(scenario.get('confederate_tables', []))
        usa_tables = len(scenario.get('union_tables', []))
        
        print(f"Scenario {num}: {name}")
        print(f"  Pages: {start}-{end}" + (f" (adv rules: {adv})" if adv else ""))
        print(f"  Confederate tables: {csa_tables}, Union tables: {usa_tables}")


def show_scenario_detail(scenario: dict, table_filter: Optional[str] = None, 
                         max_rows: Optional[int] = None):
    """Show detailed info for a single scenario."""
    num = scenario['scenario_number']
    name = scenario['scenario_name']
    start = scenario['start_page']
    end = scenario['end_page']
    adv = scenario.get('advanced_game_rules_page')
    
    print(f"\n{'='*70}")
    print(f"Scenario {num}: {name}")
    print(f"Pages: {start}-{end}" + (f" (Advanced Game rules: page {adv})" if adv else ""))
    print(f"{'='*70}\n")
    
    # Confederate tables
    csa_tables = scenario.get('confederate_tables', [])
    if csa_tables:
        print("CONFEDERATE TABLES:\n")
        for table in csa_tables:
            if table_filter and table_filter.lower() not in table['name'].lower():
                continue
            show_table(table, max_rows)
    
    # Union tables
    usa_tables = scenario.get('union_tables', [])
    if usa_tables:
        print("\nUNION TABLES:\n")
        for table in usa_tables:
            if table_filter and table_filter.lower() not in table['name'].lower():
                continue
            show_table(table, max_rows)


def show_table(table: dict, max_rows: Optional[int] = None):
    """Display a single table with headers, rows, and annotations."""
    name = table['name']
    pages = ', '.join(map(str, table['page_numbers']))
    header = table.get('header_row', [])
    rows = table.get('rows', [])
    annotations = table.get('annotations', {})
    
    print(f"Table: {name}")
    print(f"  Pages: {pages}")
    print(f"  Rows: {len(rows)}")
    
    # Show header
    if header:
        print(f"\n  Header: {' | '.join(header)}")
    
    # Show sample rows
    if rows:
        display_rows = rows[:max_rows] if max_rows else rows
        print(f"\n  Data rows ({len(display_rows)} of {len(rows)} shown):")
        for i, row in enumerate(display_rows, 1):
            row_str = ' | '.join(row)
            # Truncate very long rows
            if len(row_str) > 100:
                row_str = row_str[:97] + "..."
            print(f"    [{i}] {row_str}")
        
        if max_rows and len(rows) > max_rows:
            print(f"    ... ({len(rows) - max_rows} more rows)")
    
    # Show annotations
    if annotations:
        print(f"\n  Footnotes:")
        for symbol, text in annotations.items():
            print(f"    {symbol} = {text}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect raw table data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python inspect_raw.py gtc2
  uv run python inspect_raw.py gtc2 --scenario 1
  uv run python inspect_raw.py gtc2 --list-scenarios
  uv run python inspect_raw.py otr2 --scenario 9 --table "Union Set-Up"
  uv run python inspect_raw.py gtc2 --scenario 1 --rows 10
        """
    )
    
    parser.add_argument('game_id', help='Game ID (gtc2, otr2, hcr, etc.)')
    parser.add_argument('--scenario', '-s', type=int, help='Show details for specific scenario number')
    parser.add_argument('--list-scenarios', '-l', action='store_true', help='List all scenarios')
    parser.add_argument('--table', '-t', help='Filter to tables matching this name (case-insensitive)')
    parser.add_argument('--rows', '-r', type=int, help='Limit number of rows shown per table')
    
    args = parser.parse_args()
    
    # Load data
    data = load_raw_data(args.game_id)
    
    if not data:
        print(f"No scenarios found in raw data for {args.game_id}")
        sys.exit(1)
    
    # List scenarios mode
    if args.list_scenarios:
        list_scenarios(data)
        return
    
    # Show specific scenario
    if args.scenario:
        scenario = next((s for s in data if s['scenario_number'] == args.scenario), None)
        if not scenario:
            print(f"Error: Scenario {args.scenario} not found")
            print(f"Available scenarios: {', '.join(str(s['scenario_number']) for s in data)}")
            sys.exit(1)
        
        show_scenario_detail(scenario, args.table, args.rows)
        return
    
    # Default: list all scenarios
    list_scenarios(data)
    print("\nUse --scenario <N> to see details for a specific scenario")
    print("Use --help for more options")


if __name__ == '__main__':
    main()
