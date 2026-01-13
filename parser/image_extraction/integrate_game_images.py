#!/usr/bin/env python3
"""
Post-extraction integration script for VASSAL counter images.

After running generate_counters.py or extract_images.py, this script:
1. Copies the image mapping JSON to web/src/data/
2. Updates web/src/data/imageMap.ts to import and register the game
3. Validates the setup

Usage:
    uv run python integrate_game_images.py GAME_ID [--dry-run]

Examples:
    uv run python integrate_game_images.py hsn
    uv run python integrate_game_images.py rwh --dry-run
"""

import argparse
import json
import re
import shutil
from pathlib import Path


def get_counter_type(game_id: str, mapping_file: Path) -> str:
    """Determine counter type from mapping JSON."""
    with open(mapping_file) as f:
        data = json.load(f)
    return data.get('counterType', 'template')


def update_image_map_ts(game_id: str, counter_type: str, dry_run: bool = False) -> bool:
    """Update imageMap.ts to include the new game."""
    # Go up from parser/image_extraction/ to project root, then into web/
    image_map_path = Path(__file__).parent.parent.parent / 'web' / 'src' / 'data' / 'imageMap.ts'
    
    if not image_map_path.exists():
        print(f"❌ Error: {image_map_path} not found")
        return False
    
    content = image_map_path.read_text()
    
    # Check if already registered
    if f'import {game_id}Data from' in content:
        print(f"✓ {game_id} already registered in imageMap.ts")
        return True
    
    # Add import
    import_pattern = r'(import \w+Data from "[^"]+";)\n'
    matches = list(re.finditer(import_pattern, content))
    if not matches:
        print(f"❌ Could not find import section in imageMap.ts")
        return False
    
    last_import = matches[-1]
    new_import = f'import {game_id}Data from "./{game_id}_images.json";\n'
    
    # Add to imageMap object
    image_map_pattern = r'export const imageMap: ImageMap = \{([^}]+)\};'
    image_map_match = re.search(image_map_pattern, content, re.DOTALL)
    if not image_map_match:
        print(f"❌ Could not find imageMap object")
        return False
    
    new_entry = f'  {game_id}: {game_id}Data.matched_with_ext,\n'
    
    # Add to counterTypeMap
    counter_type_pattern = r'export const counterTypeMap: Record<string, CounterType> = \{([^}]+)\};'
    counter_type_match = re.search(counter_type_pattern, content, re.DOTALL)
    if not counter_type_match:
        print(f"❌ Could not find counterTypeMap object")
        return False
    
    new_counter_type = f'  {game_id}: ({game_id}Data as {{ counterType?: CounterType }}).counterType ?? \'{counter_type}\',\n'
    
    if dry_run:
        print(f"\n--- Dry Run: Would update imageMap.ts ---")
        print(f"Add import: {new_import.strip()}")
        print(f"Add to imageMap: {new_entry.strip()}")
        print(f"Add to counterTypeMap: {new_counter_type.strip()}")
        return True
    
    # Apply changes
    new_content = content[:last_import.end()] + new_import + content[last_import.end():]
    
    # Add to imageMap
    image_map_start = image_map_match.start(1)
    image_map_end = image_map_match.end(1)
    new_content = (
        new_content[:image_map_start] + 
        new_content[image_map_start:image_map_end].rstrip() + '\n' + new_entry +
        new_content[image_map_end:]
    )
    
    # Re-find counterTypeMap after first replacement
    counter_type_match = re.search(counter_type_pattern, new_content, re.DOTALL)
    if counter_type_match:
        counter_type_start = counter_type_match.start(1)
        counter_type_end = counter_type_match.end(1)
        new_content = (
            new_content[:counter_type_start] + 
            new_content[counter_type_start:counter_type_end].rstrip() + '\n' + new_counter_type +
            new_content[counter_type_end:]
        )
    
    image_map_path.write_text(new_content)
    print(f"✓ Updated imageMap.ts")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Integrate extracted counter images into the web app'
    )
    parser.add_argument('game_id', help='Game ID (e.g., hsn, rwh)')
    parser.add_argument('--dry-run', '-n', action='store_true', 
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    game_id = args.game_id.lower()
    
    print(f"=== Integrating {game_id.upper()} Counter Images ===\n")
    
    # Check source files
    mapping_file = Path(__file__).parent / 'image_mappings' / f'{game_id}_images.json'
    if not mapping_file.exists():
        print(f"❌ Error: {mapping_file} not found")
        print(f"   Run generate_counters.py or extract_images.py first")
        return 1
    
    # Go up from parser/image_extraction/ to project root, then into web/
    web_data_dir = Path(__file__).parent.parent.parent / 'web' / 'src' / 'data'
    web_counters_dir = Path(__file__).parent.parent.parent / 'web' / 'public' / 'images' / 'counters' / game_id
    
    if not web_counters_dir.exists() or not list(web_counters_dir.glob('*.jpg')):
        print(f"⚠️  Warning: No counter images found in {web_counters_dir}")
        print(f"   Run generate_counters.py or extract_images.py first")
    
    # Load and validate mapping
    with open(mapping_file) as f:
        mapping = json.load(f)
    
    matched = len(mapping.get('matched', {}))
    unmatched = len(mapping.get('unmatched', []))
    counter_type = get_counter_type(game_id, mapping_file)
    
    print(f"Source: {mapping_file}")
    print(f"Matched units: {matched}")
    print(f"Unmatched units: {unmatched}")
    print(f"Counter type: {counter_type}")
    
    if args.dry_run:
        print(f"\n--- Dry Run Mode ---")
    
    # Step 1: Copy JSON to web/src/data/
    dest_json = web_data_dir / f'{game_id}_images.json'
    if dest_json.exists():
        print(f"\n✓ {dest_json.name} already exists")
    else:
        if args.dry_run:
            print(f"\nWould copy: {mapping_file.name} -> {dest_json}")
        else:
            shutil.copy2(mapping_file, dest_json)
            print(f"\n✓ Copied {mapping_file.name} to web/src/data/")
    
    # Step 2: Update imageMap.ts
    print()
    if not update_image_map_ts(game_id, counter_type, args.dry_run):
        return 1
    
    # Step 3: Validate
    if not args.dry_run:
        print(f"\n=== Validation ===")
        print(f"✓ {dest_json.name} exists")
        print(f"✓ imageMap.ts updated")
        
        if web_counters_dir.exists():
            image_count = len(list(web_counters_dir.glob('*.jpg')))
            print(f"✓ {image_count} counter images in {web_counters_dir.name}/")
        
        print(f"\n🎉 Integration complete!")
        print(f"\nNext steps:")
        print(f"  1. cd web && npm run build")
        print(f"  2. Verify {game_id} counters display correctly in the app")
    else:
        print(f"\n--- Dry run complete. Use without --dry-run to apply changes. ---")
    
    return 0


if __name__ == '__main__':
    exit(main())
