#!/usr/bin/env python3
"""
Validate counter image setup for a game.

Checks:
- Image mapping JSON exists and is valid
- Counter images directory exists and has images
- All mapped images actually exist in the counters directory
- imageMap.ts is properly configured
- No broken references

Usage:
    uv run python validate_game_images.py GAME_ID

Examples:
    uv run python validate_game_images.py hsn
    uv run python validate_game_images.py --all  # Check all games
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def validate_game(game_id: str) -> Tuple[bool, List[str]]:
    """Validate image setup for a game. Returns (success, errors)."""
    errors = []
    warnings = []
    
    # Check mapping JSON
    mapping_file = Path(__file__).parent / 'image_mappings' / f'{game_id}_images.json'
    if not mapping_file.exists():
        errors.append(f"Missing mapping file: {mapping_file}")
        return False, errors
    
    try:
        with open(mapping_file) as f:
            mapping = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {mapping_file}: {e}")
        return False, errors
    
    matched = mapping.get('matched_with_ext', {})
    unmatched = mapping.get('unmatched', [])
    counter_type = mapping.get('counterType', 'unknown')
    
    print(f"\n=== {game_id.upper()} ===")
    print(f"Mapping: {mapping_file.name}")
    print(f"Matched: {len(matched)} units")
    print(f"Unmatched: {len(unmatched)} units")
    print(f"Counter type: {counter_type}")
    
    if len(unmatched) > 0:
        warnings.append(f"{len(unmatched)} unmatched units")
        if len(unmatched) <= 10:
            print(f"\nUnmatched units:")
            for u in unmatched:
                print(f"  - {u}")
    
    # Check web data copy
    web_data_file = Path(__file__).parent.parent / 'web' / 'src' / 'data' / f'{game_id}_images.json'
    if not web_data_file.exists():
        errors.append(f"Missing web data file: {web_data_file}")
    else:
        print(f"✓ Web data: {web_data_file.name}")
    
    # Check counters directory
    counters_dir = Path(__file__).parent.parent / 'web' / 'public' / 'images' / 'counters' / game_id
    if not counters_dir.exists():
        errors.append(f"Missing counters directory: {counters_dir}")
    else:
        image_files = list(counters_dir.glob('*.jpg')) + list(counters_dir.glob('*.png'))
        print(f"✓ Images: {len(image_files)} files in {counters_dir.name}/")
        
        # Check for broken references
        existing_files = {f.name for f in image_files}
        missing = []
        for key, filename in matched.items():
            if filename not in existing_files:
                missing.append(f"{key} → {filename}")
        
        if missing:
            errors.append(f"{len(missing)} mapped images don't exist in {counters_dir}")
            if len(missing) <= 5:
                print(f"\nMissing images:")
                for m in missing:
                    print(f"  - {m}")
    
    # Check imageMap.ts
    image_map_ts = Path(__file__).parent.parent / 'web' / 'src' / 'data' / 'imageMap.ts'
    if image_map_ts.exists():
        content = image_map_ts.read_text()
        
        if f'import {game_id}Data from' not in content:
            errors.append(f"imageMap.ts missing import for {game_id}")
        else:
            print(f"✓ imageMap.ts: import registered")
        
        if f'{game_id}: {game_id}Data.matched_with_ext' not in content:
            errors.append(f"imageMap.ts missing {game_id} in imageMap object")
        else:
            print(f"✓ imageMap.ts: imageMap entry registered")
        
        if f'{game_id}:' not in content or 'counterTypeMap' not in content:
            errors.append(f"imageMap.ts missing {game_id} in counterTypeMap")
        else:
            print(f"✓ imageMap.ts: counterTypeMap entry registered")
    else:
        errors.append(f"imageMap.ts not found at {image_map_ts}")
    
    # Summary
    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
    
    if not errors:
        print(f"\n✅ {game_id.upper()} validation passed")
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description='Validate counter image setup for a game'
    )
    parser.add_argument('game_id', nargs='?', help='Game ID (e.g., hsn, rtw)')
    parser.add_argument('--all', action='store_true', help='Validate all games')
    
    args = parser.parse_args()
    
    if args.all:
        # Find all games with mappings
        mapping_dir = Path(__file__).parent / 'image_mappings'
        games = sorted([f.stem.replace('_images', '') for f in mapping_dir.glob('*_images.json')])
        
        print(f"=== Validating {len(games)} games ===")
        
        results = {}
        for game_id in games:
            success, errors = validate_game(game_id)
            results[game_id] = success
        
        print(f"\n=== Summary ===")
        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed
        print(f"Passed: {passed}/{len(results)}")
        if failed > 0:
            print(f"Failed: {failed}")
            for game_id, success in results.items():
                if not success:
                    print(f"  - {game_id}")
        
        return 0 if failed == 0 else 1
    
    elif args.game_id:
        success, errors = validate_game(args.game_id.lower())
        return 0 if success else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit(main())
