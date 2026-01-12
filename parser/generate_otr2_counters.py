#!/usr/bin/env python3
"""
Generate composite counter images for OTR2.

OTR2 uses a composite counter system similar to HCR:
- Leader images are dedicated files (Lee.jpg, McClelland.jpg, etc.)
- Unit counters use background templates with manpower overlay and text labels

This script:
1. Parses buildFile.xml to extract unit-to-background mappings
2. For leaders: copies the image directly
3. For units: composites background + text overlay

Usage:
    uv run python generate_otr2_counters.py /path/to/OTR2.vmod
    uv run python generate_otr2_counters.py /tmp/otr2_vmod  # if already extracted
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
    # Handle Grifffith typo
    name = name.replace('Grifffith', 'Griffith')
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
    
    # Handle space variations: "AP Hill" vs "AP-Hill"
    if ' ' in name and '-' not in name:
        variants.append(name.replace(' ', '-'))
    if '-' in name and ' ' not in name:
        variants.append(name.replace('-', ' '))
    
    # Handle missing spaces: "4PA" -> "4 PA", "8IL" -> "8 IL"
    no_space_match = re.match(r'^(\d+)([A-Z]{2,})$', name)
    if no_space_match:
        variants.append(f"{no_space_match.group(1)} {no_space_match.group(2)}")
    
    # Handle DH Hill vs DH-Hill vs D.H. Hill
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[2:].strip()
        variants.append(f"{name[0]}.{name[1]}. {base}")
        variants.append(f"{name[0]}{name[1]}-{base}")
    
    # Handle "DR Jones" variations
    if name.startswith("DR "):
        variants.append("D.R. " + name[3:])
        variants.append("DR-" + name[3:])
    
    # Handle McLaws-B vs McLaws - B
    if 'McLaws-B' in name or 'McLaws - B' in name:
        variants.extend(['McLaws-B', 'McLaws - B'])
    if 'McLaws-C' in name or 'McLaws - C' in name:
        variants.extend(['McLaws-C', 'McLaws - C'])
    
    # Handle DR Jones-B vs DR Jones - B
    if 'Jones-B' in name or 'Jones - B' in name:
        variants.extend(['DR Jones-B', 'DR Jones - B'])
    if 'Jones-A' in name or 'Jones - A' in name:
        variants.extend(['DR Jones-A', 'DR Jones - A'])
    
    # Handle Grifffith typo
    if 'Griffith' in name:
        variants.append(name.replace('Griffith', 'Grifffith'))
    if 'Grifffith' in name:
        variants.append(name.replace('Grifffith', 'Griffith'))
    
    # Handle "Art Res-1" -> "Art Res 1"
    if 'Art Res-' in name:
        variants.append(name.replace('Art Res-', 'Art Res '))
    if 'Art Res ' in name and '-' not in name:
        variants.append(name.replace('Art Res ', 'Art Res-'))
    
    # Handle "1 NY Mrif" -> "1 NY MRif"
    if 'Mrif' in name:
        variants.append(name.replace('Mrif', 'MRif'))
    if 'MRif' in name:
        variants.append(name.replace('MRif', 'Mrif'))
    
    return list(set(variants))


def extract_unit_mappings(buildfile_path: Path) -> dict:
    """
    Parse buildFile.xml to extract unit name to background image mappings.
    
    Returns dict with structure:
    {
        "Union": {"UnitName": {"image": "USA_I_24.jpg", "type": "Infantry"}, ...},
        "Confederate": {"UnitName": {"image": "CSA_M_20.jpg", "type": "Infantry"}, ...},
        "Leaders": {
            "Union": {"McClellan": "McClelland.jpg", ...},
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
    
    # Pattern to extract: piece;;;IMAGE.jpg;NAME/
    piece_pattern = r'piece;;;([A-Za-z0-9_-]+\.(?:jpg|gif));([^/]+)/'
    
    for match in re.finditer(piece_pattern, content):
        image_file = match.group(1)
        unit_name = match.group(2).strip()
        
        # Skip markers and non-unit items
        if any(skip in unit_name for skip in ['VP', 'Ammu', 'Bridge', 'Wagon', 
                'Command', 'Ope', 'Mov', 'Track', 'CP', 'Paralysis']):
            continue
        if any(skip in image_file for skip in ['VP', 'Ammu', 'Control', 'Rv.', 
                'Ope.', 'Wagon', 'CP.']):
            continue
        
        # Determine side from image prefix
        if image_file.startswith('USA_'):
            side = 'Union'
            mappings[side][unit_name] = {'image': image_file, 'type': 'Unit'}
        elif image_file.startswith('CSA_'):
            side = 'Confederate'
            mappings[side][unit_name] = {'image': image_file, 'type': 'Unit'}
        elif image_file in ['Lee.jpg', 'Jackson.jpg', 'Johnston.jpg', 'Stuart.jpg', 
                           'Longstreet.jpg', 'Magruder.jpg', 'Smith.jpg', 
                           'AP-Hill.jpg', 'DH-Hill.jpg', 'DR-Jones.jpg']:
            mappings['Leaders']['Confederate'][unit_name] = image_file
        elif image_file in ['McClelland.jpg', 'Franklin.jpg', 'Heintzelman.jpg',
                           'Keyes.jpg', 'McDowell.jpg', 'Porter.jpg', 
                           'Sumner.jpg', 'Burnside.jpg']:
            mappings['Leaders']['Union'][unit_name] = image_file
    
    return mappings


def generate_counter_image(
    background_path: Path,
    unit_name: str,
    output_path: Path,
    font_size: int = 14
):
    """
    Generate a composite counter image with unit name overlaid on background.
    
    OTR2 counters have:
    - Background image with corps colors and strength/quality
    - Unit name at top center
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
    parser = argparse.ArgumentParser(description='Generate composite counter images for OTR2')
    parser.add_argument('source', help='Path to .vmod file or extracted directory')
    parser.add_argument('--output', '-o', help='Output directory (default: web/public/images/counters/otr2)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show mappings without generating images')
    parser.add_argument('--leaders-only', action='store_true', help='Only copy leader images (no composite generation)')
    parser.add_argument('--no-text', action='store_true', help='Copy background images without text overlay (for HTML text rendering)')
    
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
            # Look for extracted module in subdirectory
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
    parsed_file = Path(__file__).parent / 'parsed' / 'otr2_parsed.json'
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
        output_dir = Path(__file__).parent.parent / 'web' / 'public' / 'images' / 'counters' / 'otr2'
    
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
    
    # Also add mappings for combined regiments (e.g., "11/91 PA" -> match prefix "11\/")
    # These use truncated names in VASSAL like "11\/" or "3\/"
    combined_regiment_bg = {
        'Union': 'USA_Ind_00.jpg',  # Default background for Union combined regiments
        'Confederate': 'CSA_Ind_10.jpg'  # Default background for CSA combined regiments
    }
    
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
                # Try fallback for combined regiments like "11/91 PA"
                # These use a generic background image
                if '/' in parsed_name:
                    fallback_bg = combined_regiment_bg.get(side)
                    if fallback_bg and (images_dir / fallback_bg).exists():
                        vassal_info = {'image': fallback_bg, 'type': 'CombinedRegiment'}
            
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
            elif args.no_text:
                # Copy background without text overlay (for HTML text rendering)
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "").replace('/', '-')
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                shutil.copy2(src, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Copied (no text): {parsed_name} -> {output_file}")
            else:
                # Generate composite with unit name overlaid
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "").replace('/', '-')
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                generate_counter_image(src, parsed_name, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Generated: {parsed_name} -> {output_file}")
    
    # Save image mapping
    mapping_file = Path(__file__).parent / 'image_mappings' / 'otr2_images.json'
    mapping_file.parent.mkdir(exist_ok=True)
    
    # Organize mapping
    matched = {}
    matched_with_ext = {}
    
    for key, filename in image_map.items():
        base = Path(filename).stem
        matched[key] = base
        matched_with_ext[key] = filename
    
    mapping_data = {
        'game': 'otr2',
        'counterType': 'template',
        'matched': matched,
        'matched_with_ext': matched_with_ext,
        'unmatched': unmatched,
        'unused_images': [],
        'note': 'Generated by generate_otr2_counters.py'
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
