#!/usr/bin/env python3
"""
Generate composite counter images for GTC2.

GTC2 uses a TEMPLATE_COMPOSITE counter system:
- Leader images are dedicated files (Grant.jpg, Lee.jpg, etc.)
- Unit counters use background templates with text labels

This script:
1. Parses buildFile.xml to extract unit-to-background mappings
2. For leaders: copies the image directly
3. For units: composites background + text overlay

Usage:
    uv run python generate_gtc2_counters.py /path/to/GTC2.vmod
    uv run python generate_gtc2_counters.py /tmp/gtc2_vmod  # if already extracted
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
    # Remove extra spaces
    name = ' '.join(name.split())
    # Remove " - " style suffixes and convert to "-" style
    name = re.sub(r'\s+-\s+([A-Z])$', r'-\1', name)
    # Handle escaped slashes from VASSAL
    name = name.replace('\\/', '/')
    return name


def get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching."""
    variants = [name]
    
    # Add normalized version
    normalized = normalize_name(name)
    if normalized != name:
        variants.append(normalized)
    
    # Handle " - A" vs "-A" style suffixes
    if ' - ' in name:
        variants.append(name.replace(' - ', '-'))
    if re.search(r'-[A-Z]$', name):
        variants.append(re.sub(r'-([A-Z])$', r' - \1', name))
    
    # Handle (B) vs -B suffix style (VASSAL uses parentheses, parsed uses hyphen)
    paren_match = re.search(r'\s*\(([A-Z])\)$', name)
    if paren_match:
        base = re.sub(r'\s*\([A-Z]\)$', '', name)
        variants.append(f"{base}-{paren_match.group(1)}")
    hyphen_match = re.search(r'-([A-Z])$', name)
    if hyphen_match:
        base = re.sub(r'-[A-Z]$', '', name)
        variants.append(f"{base} ({hyphen_match.group(1)})")
        variants.append(base)  # Also try without suffix
    
    # Handle space variations: "AP Hill" vs "AP-Hill"
    if ' ' in name and '-' not in name:
        variants.append(name.replace(' ', '-'))
    if '-' in name and ' ' not in name:
        variants.append(name.replace('-', ' '))
    
    # Handle "WH Lee" vs "WHLee" vs "WH-Lee"
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[2:].strip()
        variants.append(f"{name[0]}{name[1]}{base}")
        variants.append(f"{name[0]}{name[1]}-{base}")
    if re.match(r'^[A-Z]{2}[A-Z]', name) and ' ' not in name[:4]:
        # WHLee -> WH Lee
        variants.append(f"{name[0]}{name[1]} {name[2:]}")
    
    # Handle "DM Gregg" vs "DM-Gregg"
    if re.match(r'^[A-Z]{2}\s', name):
        variants.append(name.replace(' ', '-', 1))
    
    # Handle "E Johnson" vs "E-Johnson" vs "EJohnson"
    if re.match(r'^[A-Z]\s', name):
        base = name[2:]
        variants.append(f"{name[0]}-{base}")
        variants.append(f"{name[0]}{base}")
    
    # Handle "BR Johnson" vs "BR-Johnson" vs "B R Johnson"
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[3:]
        variants.append(f"{name[:2]}-{base}")
        variants.append(f"{name[0]} {name[1]} {base}")  # "BR Johnson" -> "B R Johnson"
    if re.match(r'^[A-Z]\s[A-Z]\s', name):
        # "B R Johnson" -> "BR Johnson"
        variants.append(f"{name[0]}{name[2]}{name[3:]}")
    
    # Handle Wilcox vs Willcox
    if 'Wilcox' in name:
        variants.append(name.replace('Wilcox', 'Willcox'))
    if 'Willcox' in name:
        variants.append(name.replace('Willcox', 'Wilcox'))
    
    # Handle escaped slashes: "1VA \/ 11VA" -> "1VA / 11VA" -> "1 VA/11 VA"
    if '\\/' in name:
        variants.append(name.replace('\\/', '/'))
    if '/' in name:
        variants.append(name.replace('/', '\\/'))
        # Also handle space variations around slash: "1VA / 11VA" vs "1 VA/11 VA"
        variants.append(name.replace(' / ', '/'))
        variants.append(name.replace('/', ' / '))
        # Handle "1VA/11VA" vs "1 VA/11 VA"
        no_space = re.sub(r'(\d)([A-Z]{2})', r'\1 \2', name)  # Add space after number
        if no_space != name:
            variants.append(no_space)
    
    # Handle "Art Res-1" vs "Art Res 1"
    if 'Art Res-' in name:
        variants.append(name.replace('Art Res-', 'Art Res '))
    if 'Art Res ' in name and '-' not in name:
        variants.append(name.replace('Art Res ', 'Art Res-'))
    
    # Handle "Torbert" vs "Tobert" typo
    if 'Torbert' in name:
        variants.append(name.replace('Torbert', 'Tobert'))
    if 'Tobert' in name:
        variants.append(name.replace('Tobert', 'Torbert'))
    
    # Handle "Warren" vs "Warren-A" vs "Warrent"
    if 'Warren' in name:
        variants.append(name.replace('Warren', 'Warrent'))
    if 'Warrent' in name:
        variants.append(name.replace('Warrent', 'Warren'))
    
    # Handle "Hill" -> "AP HIll" or "A.P. Hill"
    if name == 'Hill':
        variants.extend(['AP Hill', 'AP HIll', 'A.P. Hill', 'APHill'])
    if 'AP Hill' in name or 'AP HIll' in name:
        variants.append('Hill')
        variants.append(name.replace('AP Hill', 'AP HIll'))
        variants.append(name.replace('AP HIll', 'AP Hill'))
    
    # Handle "VA Militia" vs "VA Mil"
    if 'Militia' in name:
        variants.append(name.replace('Militia', 'Mil'))
    if 'VA Mil' in name and 'Militia' not in name:
        variants.append(name.replace('VA Mil', 'VA Militia'))
    
    # Handle "Washington Art." vs "Wash Art"
    if 'Washington Art' in name:
        variants.append(name.replace('Washington Art', 'Wash Art').replace('.', ''))
    if 'Wash Art' in name:
        variants.append(name.replace('Wash Art', 'Washington Art'))
        variants.append(name.replace('Wash Art', 'Washington Art.'))
    
    # Handle "Schoonmaker" vs "Schoonmkr" (VASSAL abbreviation)
    if 'Schoonmaker' in name:
        variants.append(name.replace('Schoonmaker', 'Schoonmkr'))
    if 'Schoonmkr' in name:
        variants.append(name.replace('Schoonmkr', 'Schoonmaker'))
    
    return list(set(variants))


def extract_unit_mappings(buildfile_path: Path) -> dict:
    """
    Parse buildFile.xml to extract unit name to background image mappings.
    
    Returns dict with structure:
    {
        "Union": {"UnitName": {"image": "UV_2_2.jpg", "type": "Infantry Division"}, ...},
        "Confederate": {"UnitName": {"image": "CIII_3_3.jpg", "type": "Infantry Division"}, ...},
        "Leaders": {
            "Union": {"Grant": "Grant.jpg", ...},
            "Confederate": {"Lee": "Lee.jpg", ...}
        }
    }
    """
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    # Pattern to find PieceSlot definitions
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        # Extract the image filename: piece;;;IMAGE.jpg;NAME/
        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Skip markers and non-unit items
        if any(skip in entry_name.lower() for skip in ['vp', 'ammu', 'bridge', 'wagon', 
                'command', 'control', 'track', 'paralysis', 'game-turn', 'cycle', 'defeat',
                'supply', 'event', 'rain', 'heat', 'posture', 'mov', 'ope']):
            continue
        if any(skip in image_file.lower() for skip in ['vp', 'ammu', 'control', 'wagon',
                'cp.', 'ctrl', 'bridge', 'losses', 'rr_', 'rr-', 'strong', 'weak', 'init',
                'forces', 'display', 'chart', 'replacement', 'damage', 'destroyed',
                'transport', 'start', 'end', 'map', 'tt-', 'strategic']):
            continue
        
        # Determine if it's a leader or unit
        if 'prototype;Leader' in slot_content:
            # Determine side from image name or context
            # GTC2 leaders: Grant, Lee, Hancock, Longstreet, etc.
            union_leaders = ['Grant', 'Hancock', 'Burnside', 'Butler', 'Crook', 'Sheridan',
                           'Wright', 'Warren', 'Sedgwick', 'Smith', 'Sigel', 'Hunter',
                           'Merritt', 'Averell', 'Kautz', 'Gillmore', 'Griffin', 'Humphreys',
                           'Terry', 'Torbert', 'Martindale', 'Wilson', 'Wilcox', 'DM Gregg',
                           'Upton', 'Merrit']
            csa_leaders = ['Lee', 'Longstreet', 'Ewell', 'Stuart', 'Anderson', 'Early',
                          'Hampton', 'Beauregard', 'Breckinridge', 'Hoke', 'Pickett',
                          'AP Hill', 'APHill', 'A.P. Hill', 'F Lee', 'WH Lee', 'WHLee',
                          'E Johnson', 'BR Johnson', 'WE Jones']
            
            if any(leader in entry_name for leader in union_leaders):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif any(leader in entry_name for leader in csa_leaders):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
            else:
                # Default guess based on common patterns
                if 'CL-' in image_file:
                    mappings["Leaders"]["Confederate"][entry_name] = image_file
                else:
                    # Check buildfile context for USA/CSA
                    mappings["Leaders"]["Union"][entry_name] = image_file
        else:
            # It's a unit - extract type from prototype
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
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
    font_size: int = 14
):
    """
    Generate a composite counter image with unit name overlaid on background.
    """
    if not HAS_PIL:
        shutil.copy2(background_path, output_path)
        return
    
    # Load background
    bg = Image.open(background_path).convert('RGBA')
    
    # Create drawing context
    draw = ImageDraw.Draw(bg)
    
    # Try to load a font, fall back to default
    font = None
    for font_name in [
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Geneva.ttf',
        'Arial.ttf', 
        'Helvetica.ttf', 
        'DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ]:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except (OSError, IOError):
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # Calculate text position (centered near top of counter)
    bbox = draw.textbbox((0, 0), unit_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center horizontally, place near top with small margin
    x = (bg.width - text_width) // 2
    y = 3  # Small top margin
    
    # Draw text with black color
    draw.text((x, y), unit_name, fill=(0, 0, 0, 255), font=font)
    
    # Convert to RGB for JPEG output
    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
        bg = bg.convert('RGB')
    
    bg.save(output_path, quality=95)


def main():
    parser = argparse.ArgumentParser(description='Generate composite counter images for GTC2')
    parser.add_argument('source', help='Path to .vmod file or extracted directory')
    parser.add_argument('--output', '-o', help='Output directory (default: web/public/images/counters/gtc2)')
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
        if not (source / 'buildFile.xml').exists():
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
    parsed_file = Path(__file__).parent / 'parsed' / 'gtc2_parsed.json'
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
        
        print("\n--- Sample Union Units ---")
        for name, info in list(sorted(mappings['Union'].items()))[:20]:
            print(f"  {name}: {info['image']}")
        
        print("\n--- Sample Confederate Units ---")
        for name, info in list(sorted(mappings['Confederate'].items()))[:20]:
            print(f"  {name}: {info['image']}")
        
        return
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / 'web' / 'public' / 'images' / 'counters' / 'gtc2'
    
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
            # Skip special units that won't have images
            if any(skip in parsed_name for skip in ['Wagon Train', 'Gunboat', 'Naval Battery']):
                continue
            
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
                if not dst.exists():
                    shutil.copy2(src, dst)
                image_map[f"{prefix}:{parsed_name}"] = img_file
                print(f"  Copied: {parsed_name} -> {img_file}")
            elif args.leaders_only:
                continue
            else:
                # Generate composite with unit name overlaid
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "").replace('/', '-')
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                generate_counter_image(src, parsed_name, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Generated: {parsed_name} -> {output_file}")
    
    # Save image mapping
    mapping_file = Path(__file__).parent / 'image_mappings' / 'gtc2_images.json'
    mapping_file.parent.mkdir(exist_ok=True)
    
    # Organize mapping
    matched = {}
    matched_with_ext = {}
    
    for key, filename in image_map.items():
        base = Path(filename).stem
        matched[key] = base
        matched_with_ext[key] = filename
    
    mapping_data = {
        'game': 'gtc2',
        'matched': matched,
        'matched_with_ext': matched_with_ext,
        'unmatched': unmatched,
        'unused_images': [],
        'note': 'Generated by generate_gtc2_counters.py'
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
