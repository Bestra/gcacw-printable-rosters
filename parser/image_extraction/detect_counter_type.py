#!/usr/bin/env python3
"""
Detect the counter structure type in a VASSAL module.

Counter types:
1. INDIVIDUAL - Each unit has a dedicated pre-rendered image with the unit name on it
                Example: RTG2 has Union_Hooker.jpg, CSA_Lee.jpg
                
2. TEMPLATE_COMPOSITE - Units use generic background images based on corps/type,
                        with unit names overlaid via VASSAL's label mechanism
                        Example: HCR uses I-P-2-4.jpg (corps I, position 2-4)
                        Example: OTR2 uses USA_I_24.jpg, CSA_M_20.jpg
                        Example: GTC2 uses UII_2_3.jpg, CIII_3_4.jpg
                        
3. HYBRID - Leaders have individual images, units use templates
            Example: Most games have dedicated leader portraits

Usage:
    uv run python detect_counter_type.py /path/to/game.vmod
    uv run python detect_counter_type.py /path/to/extracted_vmod/
"""

import argparse
import re
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


def extract_pieces_from_buildfile(buildfile_path: Path) -> list[dict]:
    """
    Extract piece definitions from buildFile.xml.
    
    Returns list of dicts with:
    - entry_name: The unit name from entryName attribute
    - image: The image filename
    - prototype: The prototype type (Leader, USA Infantry Division, etc.)
    - has_label: Whether it uses a label/text overlay
    """
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    pieces = []
    
    # Pattern to find PieceSlot definitions
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        # Extract image filename
        image_match = re.search(r'piece;;;([^;]+\.(jpg|gif|png));', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Extract prototype
        prototype_match = re.search(r'prototype;([^\\\s]+)', slot_content)
        prototype = prototype_match.group(1) if prototype_match else 'Unknown'
        
        # Check for label/text overlay
        has_label = 'label;;;' in slot_content or 'TextLabel;' in slot_content
        
        pieces.append({
            'entry_name': entry_name,
            'image': image_file,
            'prototype': prototype,
            'has_label': has_label
        })
    
    return pieces


def analyze_image_patterns(pieces: list[dict]) -> dict:
    """
    Analyze image naming patterns to determine counter type.
    """
    # Separate leaders from units
    leaders = [p for p in pieces if 'Leader' in p['prototype']]
    units = [p for p in pieces if 'Leader' not in p['prototype']]
    
    # Analyze unit images
    unit_images = [p['image'] for p in units]
    leader_images = [p['image'] for p in leaders]
    
    # Check if unit names appear in their image filenames
    name_in_image_count = 0
    name_not_in_image_count = 0
    
    for p in units:
        name = p['entry_name'].lower().replace(' ', '').replace('-', '')
        image = p['image'].lower().replace(' ', '').replace('-', '').replace('_', '')
        
        # Check if a significant part of the name appears in the image
        if len(name) >= 3 and name[:min(4, len(name))] in image:
            name_in_image_count += 1
        else:
            name_not_in_image_count += 1
    
    # Analyze image patterns
    image_patterns = Counter()
    for img in unit_images:
        # Strip extension
        base = Path(img).stem
        
        # Common template patterns
        if re.match(r'^[UC]?[IVXLC]+[-_]\d+[-_]\d+$', base, re.IGNORECASE):
            # Roman numeral corps + numbers: II-P-1-0, CII_3_3
            image_patterns['corps_template'] += 1
        elif re.match(r'^(USA|CSA)[-_][A-Z][-_]\d+$', base, re.IGNORECASE):
            # Side prefix + type: USA_I_24, CSA_M_20
            image_patterns['side_type_template'] += 1
        elif re.match(r'^[UC](II|III|IV|IX|V|VI|VII|VIII|X|XI|XII|XVIII)[-_]\d+[-_]\d+$', base, re.IGNORECASE):
            # Side initial + corps: UII_2_3, CIII_3_4
            image_patterns['side_corps_template'] += 1
        elif re.match(r'^[A-Z][-_][A-Z][-_]\d+[-_]\d+$', base, re.IGNORECASE):
            # Generic template: I-P-2-4
            image_patterns['generic_template'] += 1
        else:
            image_patterns['individual'] += 1
    
    # Check if units use labels (text overlay)
    units_with_labels = sum(1 for p in units if p['has_label'])
    units_without_labels = len(units) - units_with_labels
    
    # Check if multiple units share the same image
    image_counts = Counter(p['image'] for p in units)
    shared_images = sum(1 for img, count in image_counts.items() if count > 1)
    unique_images = sum(1 for img, count in image_counts.items() if count == 1)
    
    return {
        'total_pieces': len(pieces),
        'leaders': len(leaders),
        'units': len(units),
        'name_in_image': name_in_image_count,
        'name_not_in_image': name_not_in_image_count,
        'image_patterns': dict(image_patterns),
        'units_with_labels': units_with_labels,
        'units_without_labels': units_without_labels,
        'shared_images': shared_images,
        'unique_images': unique_images,
        'unique_unit_images': len(set(unit_images)),
        'unique_leader_images': len(set(leader_images)),
    }


def detect_counter_type(analysis: dict) -> tuple[str, str]:
    """
    Determine the counter type based on analysis.
    
    Returns (type, explanation)
    """
    units = analysis['units']
    if units == 0:
        return ('UNKNOWN', 'No units found in module')
    
    # Key indicators:
    # 1. If most units have labels AND share images -> TEMPLATE_COMPOSITE
    # 2. If most units have unique images with name in filename -> INDIVIDUAL
    # 3. If units share images but no labels -> probably still TEMPLATE (VASSAL may handle differently)
    
    label_ratio = analysis['units_with_labels'] / units if units > 0 else 0
    shared_ratio = analysis['shared_images'] / analysis['unique_unit_images'] if analysis['unique_unit_images'] > 0 else 0
    name_in_image_ratio = analysis['name_in_image'] / units if units > 0 else 0
    
    template_patterns = sum(
        analysis['image_patterns'].get(k, 0) 
        for k in ['corps_template', 'side_type_template', 'side_corps_template', 'generic_template']
    )
    template_ratio = template_patterns / units if units > 0 else 0
    
    reasons = []
    
    if template_ratio > 0.5:
        reasons.append(f"Template-style image patterns: {template_ratio:.0%}")
    if label_ratio > 0.5:
        reasons.append(f"Units use text labels: {label_ratio:.0%}")
    if shared_ratio > 0.3:
        reasons.append(f"Images shared between units: {shared_ratio:.0%}")
    if name_in_image_ratio > 0.5:
        reasons.append(f"Unit names in image filenames: {name_in_image_ratio:.0%}")
    
    # Decision logic
    if template_ratio > 0.5 or (label_ratio > 0.5 and shared_ratio > 0.3):
        counter_type = 'TEMPLATE_COMPOSITE'
        explanation = "Units use generic background images with text overlays. " + "; ".join(reasons)
    elif name_in_image_ratio > 0.6 and analysis['unique_unit_images'] > units * 0.8:
        counter_type = 'INDIVIDUAL'
        explanation = "Each unit has a dedicated pre-rendered image. " + "; ".join(reasons)
    elif label_ratio > 0.3 and shared_ratio > 0.2:
        counter_type = 'TEMPLATE_COMPOSITE'
        explanation = "Likely template-based with text overlays. " + "; ".join(reasons)
    else:
        counter_type = 'HYBRID'
        explanation = "Mixed counter types detected. " + "; ".join(reasons)
    
    return (counter_type, explanation)


def analyze_vmod(source: Path) -> dict:
    """
    Analyze a VMOD file or extracted directory.
    """
    # Find or extract the module
    if source.is_file() and source.suffix.lower() == '.vmod':
        temp_dir = Path(tempfile.mkdtemp())
        print(f"Extracting {source.name}...")
        with zipfile.ZipFile(source, 'r') as z:
            z.extractall(temp_dir)
        module_dir = temp_dir
        cleanup = True
    elif source.is_dir():
        module_dir = source
        cleanup = False
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
    
    # Extract pieces
    pieces = extract_pieces_from_buildfile(buildfile)
    
    # List actual images
    actual_images = []
    if images_dir.exists():
        actual_images = [f.name for f in images_dir.iterdir() if f.suffix.lower() in ['.jpg', '.gif', '.png']]
    
    # Analyze patterns
    analysis = analyze_image_patterns(pieces)
    analysis['actual_image_count'] = len(actual_images)
    
    # Detect type
    counter_type, explanation = detect_counter_type(analysis)
    analysis['counter_type'] = counter_type
    analysis['explanation'] = explanation
    
    # Sample pieces for debugging
    analysis['sample_leaders'] = [
        {'name': p['entry_name'], 'image': p['image']} 
        for p in pieces if 'Leader' in p['prototype']
    ][:5]
    analysis['sample_units'] = [
        {'name': p['entry_name'], 'image': p['image'], 'has_label': p['has_label']} 
        for p in pieces if 'Leader' not in p['prototype']
    ][:10]
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description='Detect counter type in VASSAL module')
    parser.add_argument('source', nargs='?', help='Path to .vmod file or extracted directory')
    parser.add_argument('--all', '-a', action='store_true', help='Analyze all .vmod files in a directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed analysis')
    
    args = parser.parse_args()
    
    if args.all:
        # Find all .vmod files
        if args.source:
            search_dir = Path(args.source).expanduser()
        else:
            search_dir = Path('/Users/bestra/Documents/vasl/gcacw')
        
        vmod_files = list(search_dir.glob('*.vmod'))
        if not vmod_files:
            print(f"No .vmod files found in {search_dir}")
            return
        
        print(f"Analyzing {len(vmod_files)} VMOD files...\n")
        print("=" * 80)
        
        for vmod in sorted(vmod_files):
            try:
                analysis = analyze_vmod(vmod)
                print(f"\n{vmod.name}")
                print("-" * 40)
                print(f"  Type: {analysis['counter_type']}")
                print(f"  {analysis['explanation']}")
                print(f"  Units: {analysis['units']}, Leaders: {analysis['leaders']}")
                print(f"  Unique unit images: {analysis['unique_unit_images']}")
                print(f"  Image patterns: {analysis['image_patterns']}")
                
                if args.verbose:
                    print(f"\n  Sample leaders:")
                    for s in analysis['sample_leaders']:
                        print(f"    {s['name']}: {s['image']}")
                    print(f"\n  Sample units:")
                    for s in analysis['sample_units']:
                        label = " [LABEL]" if s['has_label'] else ""
                        print(f"    {s['name']}: {s['image']}{label}")
            except Exception as e:
                print(f"\n{vmod.name}: ERROR - {e}")
        
        print("\n" + "=" * 80)
    
    elif args.source:
        source = Path(args.source).expanduser()
        analysis = analyze_vmod(source)
        
        print(f"\n=== Counter Type Detection: {source.name} ===\n")
        print(f"Type: {analysis['counter_type']}")
        print(f"Explanation: {analysis['explanation']}")
        print(f"\n--- Statistics ---")
        print(f"Total pieces: {analysis['total_pieces']}")
        print(f"Leaders: {analysis['leaders']}")
        print(f"Units: {analysis['units']}")
        print(f"Units with labels: {analysis['units_with_labels']}")
        print(f"Unique unit images: {analysis['unique_unit_images']}")
        print(f"Shared images: {analysis['shared_images']}")
        print(f"Actual images in module: {analysis['actual_image_count']}")
        print(f"\nImage patterns: {analysis['image_patterns']}")
        
        print(f"\n--- Sample Leaders ---")
        for s in analysis['sample_leaders']:
            print(f"  {s['name']}: {s['image']}")
        
        print(f"\n--- Sample Units ---")
        for s in analysis['sample_units']:
            label = " [LABEL]" if s['has_label'] else ""
            print(f"  {s['name']}: {s['image']}{label}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
