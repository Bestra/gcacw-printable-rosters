#!/usr/bin/env python3
"""
Generate composite counter images for HCR.

HCR uses a different counter system than RTG2 - instead of individual unit images,
it uses corps background templates with text overlays. This script:
1. Extracts the unit-to-corps-background mapping from buildFile.xml
2. Composites the background image with the unit name text
3. Saves the result as individual unit counter images

Usage:
    uv run python generate_hcr_counters.py /path/to/HCR.vmod
"""

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Run: uv add pillow")


def normalize_name(name: str) -> str:
    """Normalize a unit name for matching between VASSAL and parsed data."""
    # Remove spaces after periods: "A.P. Hill" -> "A.P.Hill"
    name = re.sub(r'\.(\s+)', '.', name)
    # Remove trailing suffixes like -A, -B
    name = re.sub(r'-[A-Z]$', '', name)
    return name


def get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching."""
    variants = [name]
    
    # Add normalized version
    normalized = normalize_name(name)
    if normalized != name:
        variants.append(normalized)
    
    # Add version with periods followed by space: "A.P.Hill" -> "A.P. Hill"
    spaced = re.sub(r'\.([A-Z])', r'. \1', name)
    if spaced != name:
        variants.append(spaced)
    
    # Add version without suffix
    no_suffix = re.sub(r'-[A-Z]$', '', name)
    if no_suffix != name:
        variants.append(no_suffix)
    
    # Add version with suffix variations
    for suffix in ['-A', '-B']:
        variants.append(name + suffix)
        variants.append(normalized + suffix)
    
    # Handle Heintzelman / Heitzelman typo
    if 'Heitz' in name:
        variants.append(name.replace('Heitz', 'Heintz'))
    if 'Heintz' in name:
        variants.append(name.replace('Heintz', 'Heitz'))
    
    # Handle Willcox / Wilcox
    if 'Wilcox' in name:
        variants.append(name.replace('Wilcox', 'Willcox'))
    if 'Willcox' in name:
        variants.append(name.replace('Willcox', 'Wilcox'))
    
    # Handle D'Utassy vs D'Utassy (curly apostrophe)
    if "'" in name:
        variants.append(name.replace("'", "'"))
    if "'" in name:
        variants.append(name.replace("'", "'"))
    
    # Handle F. Lee vs F.Lee
    if re.match(r'^[A-Z]\.\s', name):
        variants.append(re.sub(r'^([A-Z]\.)\s', r'\1', name))
    if re.match(r'^[A-Z]\.[A-Z]', name) and ' ' not in name[:4]:
        variants.append(re.sub(r'^([A-Z])\.', r'\1. ', name))
    
    return list(set(variants))


def extract_unit_mappings(buildfile_path: Path) -> dict:
    """
    Parse buildFile.xml to extract unit name to background image mappings.
    
    Returns dict with structure:
    {
        "Union": {
            "Doubleday": {"image": "I-P-2-4.jpg", "type": "Infantry Division"},
            ...
        },
        "Confederate": {
            "A.P.Hill": {"image": "J-3-4.jpg", "type": "Infantry Division"},
            ...
        },
        "Leaders": {
            "Union": {"Burnside-A": "burnside_a.jpg", ...},
            "Confederate": {"Jackson": "Jackson.jpg", ...}
        }
    }
    """
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    # Pattern to extract: entryName="UnitName" ... prototype;TYPE\ ... piece;;;IMAGE.jpg;UnitName/
    # Leaders have: prototype;Leader ... piece;;;IMAGE.jpg;NAME/
    # Units have: prototype;USA/CSA Infantry/Cavalry Division/Brigade/Regiment\ ... piece;;;IMAGE.jpg;NAME/
    
    # Find all PieceSlot definitions
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        # Extract the image filename: piece;;;IMAGE.jpg;NAME/
        image_match = re.search(r'piece;;;([^;]+);[^/]+/', slot_content)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Determine if it's a leader or unit
        if 'prototype;Leader' in slot_content:
            # It's a leader
            # Determine side from ListWidget context - look for nearby context
            # For now, check common patterns in the data
            if any(name in entry_name for name in ['Burnside', 'Cox', 'Franklin', 'Heitz', 'Hooker', 
                    'Mansfield', 'McClellan', 'Pleasonton', 'Porter', 'Reno', 'Sigel', 'Sumner']):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif any(name in entry_name for name in ['Jackson', 'Lee', 'Longstreet', 'Stuart']):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            # It's a unit - extract type
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment|Sub)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


def generate_counter_image(
    background_path: Path,
    unit_name: str,
    output_path: Path,
    font_size: int = 12
):
    """
    Generate a composite counter image with unit name overlaid on background.
    """
    if not HAS_PIL:
        # Just copy the background as-is
        shutil.copy2(background_path, output_path)
        return
    
    # Load background
    bg = Image.open(background_path).convert('RGBA')
    
    # Create drawing context
    draw = ImageDraw.Draw(bg)
    
    # Try to load a font, fall back to default
    try:
        # Try common system fonts
        for font_name in ['Arial.ttf', 'Helvetica.ttf', 'DejaVuSans.ttf', '/System/Library/Fonts/Helvetica.ttc']:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except (OSError, IOError):
                continue
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Calculate text position (centered at top of counter)
    # Get text bounding box
    bbox = draw.textbbox((0, 0), unit_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center horizontally, place at top with small margin
    x = (bg.width - text_width) // 2
    y = 4  # Small top margin
    
    # Draw text with black color
    draw.text((x, y), unit_name, fill=(0, 0, 0, 255), font=font)
    
    # Convert back to RGB for JPEG output
    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
        bg = bg.convert('RGB')
    
    bg.save(output_path, quality=95)


def main():
    parser = argparse.ArgumentParser(description='Generate composite counter images for HCR')
    parser.add_argument('source', help='Path to .vmod file or extracted directory')
    parser.add_argument('--output', '-o', help='Output directory (default: web/public/images/counters/hcr)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show mappings without generating images')
    parser.add_argument('--leaders-only', action='store_true', help='Only copy leader images (no composite generation)')
    
    args = parser.parse_args()
    
    source = Path(args.source).expanduser()
    
    # Find or extract the module
    if source.is_file() and source.suffix.lower() == '.vmod':
        temp_dir = Path(tempfile.mkdtemp())
        print(f"Extracting {source}...")
        with zipfile.ZipFile(source, 'r') as z:
            z.extractall(temp_dir)
        module_dir = temp_dir
    elif source.is_dir():
        module_dir = source
        if (source / 'images').is_dir() and (source / 'buildFile.xml').exists():
            pass  # Already extracted
        else:
            # Look for extracted module
            for item in source.iterdir():
                if item.is_dir() and (item / 'buildFile.xml').exists():
                    module_dir = item
                    break
    else:
        raise ValueError(f"Cannot find VMOD module at {source}")
    
    buildfile = module_dir / 'buildFile.xml'
    images_dir = module_dir / 'images'
    
    if not buildfile.exists():
        raise ValueError(f"buildFile.xml not found in {module_dir}")
    if not images_dir.exists():
        raise ValueError(f"images directory not found in {module_dir}")
    
    print(f"Parsing {buildfile}...")
    mappings = extract_unit_mappings(buildfile)
    
    # Load parsed data to get the actual unit names used in the web app
    parsed_file = Path(__file__).parent / 'parsed' / 'hcr_parsed.json'
    parsed_units = {'Union': {}, 'Confederate': {}}
    if parsed_file.exists():
        with open(parsed_file) as f:
            data = json.load(f)
        for scenario in data:
            for unit in scenario.get('confederate_units', []):
                name = unit['unit_leader']
                utype = unit.get('unit_type', 'Inf')
                if name not in parsed_units['Confederate'] or utype == 'Ldr':
                    parsed_units['Confederate'][name] = utype
            for unit in scenario.get('union_units', []):
                name = unit['unit_leader']
                utype = unit.get('unit_type', 'Inf')
                if name not in parsed_units['Union'] or utype == 'Ldr':
                    parsed_units['Union'][name] = utype
        print(f"Loaded {len(parsed_units['Union'])} Union and {len(parsed_units['Confederate'])} Confederate units from parsed data")
    
    print(f"\n=== VASSAL Unit Mappings ===")
    print(f"Union Leaders: {len(mappings['Leaders']['Union'])}")
    print(f"Confederate Leaders: {len(mappings['Leaders']['Confederate'])}")
    print(f"Union Units: {len(mappings['Union'])}")
    print(f"Confederate Units: {len(mappings['Confederate'])}")
    
    if args.dry_run:
        print("\n--- Union Leaders ---")
        for name, img in sorted(mappings['Leaders']['Union'].items()):
            print(f"  {name}: {img}")
        
        print("\n--- Confederate Leaders ---")
        for name, img in sorted(mappings['Leaders']['Confederate'].items()):
            print(f"  {name}: {img}")
        
        print("\n--- Union Units ---")
        for name, info in sorted(mappings['Union'].items()):
            print(f"  {name}: {info['image']} ({info['type']})")
        
        print("\n--- Confederate Units ---")
        for name, info in sorted(mappings['Confederate'].items()):
            print(f"  {name}: {info['image']} ({info['type']})")
        
        return
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / 'web' / 'public' / 'images' / 'counters' / 'hcr'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build a lookup from VASSAL names to image files
    vassal_lookup = {}
    for side in ['Union', 'Confederate']:
        for name, info in mappings.get(side, {}).items():
            for variant in get_name_variants(name):
                key = (side, variant)
                if key not in vassal_lookup:
                    vassal_lookup[key] = info
        for name, img in mappings['Leaders'].get(side, {}).items():
            for variant in get_name_variants(name):
                key = (side, variant)
                if key not in vassal_lookup:
                    vassal_lookup[key] = {'image': img, 'type': 'Leader'}
    
    # Build image mapping for web app using parsed unit names
    image_map = {}
    unmatched = []
    
    print("\n--- Generating Images ---")
    for side in ['Union', 'Confederate']:
        prefix = 'U' if side == 'Union' else 'C'
        for parsed_name, utype in sorted(parsed_units.get(side, {}).items()):
            # Try to find matching VASSAL unit
            vassal_info = None
            for variant in get_name_variants(parsed_name):
                key = (side, variant)
                if key in vassal_lookup:
                    vassal_info = vassal_lookup[key]
                    break
            
            if not vassal_info:
                unmatched.append(f"{side} ({utype}): {parsed_name}")
                continue
            
            img_file = vassal_info['image']
            src = images_dir / img_file
            
            if not src.exists():
                print(f"  Missing: {img_file} for {parsed_name}")
                unmatched.append(f"{side} ({utype}): {parsed_name} [missing: {img_file}]")
                continue
            
            # For leaders, just copy the image directly
            if vassal_info['type'] == 'Leader':
                dst = output_dir / img_file
                shutil.copy2(src, dst)
                image_map[f"{prefix}:{parsed_name}"] = img_file
                print(f"  Copied: {parsed_name} -> {img_file}")
            else:
                # Generate composite with unit name overlaid
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "")
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                generate_counter_image(src, parsed_name, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Generated: {parsed_name} -> {output_file}")
    
    # Save image mapping
    mapping_file = Path(__file__).parent / 'image_mappings' / 'hcr_images.json'
    mapping_file.parent.mkdir(exist_ok=True)
    
    # Organize mapping
    matched = {}
    matched_with_ext = {}
    
    for key, filename in image_map.items():
        base = Path(filename).stem
        matched[key] = base
        matched_with_ext[key] = filename
    
    mapping_data = {
        'game': 'hcr',
        'matched': matched,
        'matched_with_ext': matched_with_ext,
        'unmatched': unmatched,
        'unused_images': [],
        'note': 'Generated by generate_hcr_counters.py'
    }
    
    with open(mapping_file, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Matched: {len(image_map)} units")
    print(f"Unmatched: {len(unmatched)} units")
    if unmatched:
        print("\n--- Unmatched Units ---")
        for u in unmatched:
            print(f"  {u}")
    
    print(f"\nSaved mappings to {mapping_file}")
    print(f"Images saved to {output_dir}")


if __name__ == '__main__':
    main()
