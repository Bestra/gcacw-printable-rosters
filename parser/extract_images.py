#!/usr/bin/env python3
"""
Extract unit counter images from VASSAL modules (.vmod files).

This script:
1. Extracts images from a VASSAL module (which is a ZIP file)
2. Maps unit names from parsed game data to image filenames
3. Copies matched images to the web public directory

Usage:
    uv run python extract_images.py rtg2 /path/to/RTGII.vmod
    uv run python extract_images.py rtg2 /path/to/extracted/images/  # if already extracted
"""

import argparse
import json
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageMatch:
    """Represents a mapping between a unit and its image file."""
    unit_leader: str
    side: str  # 'Confederate' or 'Union'
    image_filename: str
    matched: bool = False


# ============================================================================
# Game-specific extractors
# ============================================================================

class GameExtractor:
    """Base class for game-specific image extraction."""
    
    def get_available_images(self, images_dir: Path) -> dict[str, Path]:
        """Get available images for this game. Override in subclasses."""
        raise NotImplementedError
    
    def find_image_match(self, unit_leader: str, side: str, unit_type: str, available_set: set[str]) -> str | None:
        """Find matching image for a unit. Override in subclasses."""
        raise NotImplementedError


class RTG2Extractor(GameExtractor):
    """Extractor for RTG2 and similar games (OTR2, GTC2, HSN, RTW) using C_/U_ prefix convention."""
    
    def normalize_unit_name(self, name: str) -> str:
        """
        Normalize a unit name for matching against VASSAL image filenames.
        
        Transformations observed:
        - "F. Lee" -> "F-Lee" (space and period -> hyphen)
        - "A. Jenkins" -> "A-Jenkins"
        - "J. Smith" -> "JSmith" (some variations)
        - "JI Gregg" -> "JI-Greg" (note: might be typo in VASSAL)
        - "Art Res-1" -> "Art1"
        - "1 NY/12 PA" -> "1-NY-12-PA"
        - "17 VA" -> "17VA" (space removed)
        """
        # Remove periods
        name = name.replace('.', '')
        
        # Handle special cases for artillery reserves
        if name.startswith('Art Res-'):
            num = name.split('-')[-1]
            return f"Art{num}"
        
        # Handle wagon train and other special units
        if name.lower() in ['wagon train']:
            return None  # No image expected
        
        # Replace slashes with hyphens
        name = name.replace('/', '-')
        
        # Replace spaces with hyphens
        return name.replace(' ', '-')
    def get_alternate_names(self, name: str) -> list[str]:
        """Generate alternate name variations to try matching."""
        variations = []
        
        base = self.normalize_unit_name(name)
        if base is None:
            return []
        
        variations.append(base)
        
        # Try without hyphens
        variations.append(base.replace('-', ''))
        
        # Try with underscores
        variations.append(base.replace('-', '_'))
        
        # Handle initials - "JI Gregg" might be "JI-Greg" (single g)
        if 'Gregg' in base:
            variations.append(base.replace('Gregg', 'Greg'))
        
        # Handle Fessenden vs Fessendon
        if 'Fessendon' in base:
            variations.append(base.replace('Fessendon', 'Fessenden'))
        
        # Handle Sykes typo in VASSAL (Siykes)
        if 'Sykes' in base:
            variations.append(base.replace('Sykes', 'Siykes'))
        
        # Handle "DM Gregg" -> "Gregg" (strip leading initials for leaders)
        if re.match(r'^[A-Z]{1,2}[-\s]', name):
            stripped = re.sub(r'^[A-Z]{1,2}[-\s]', '', name)
            stripped_norm = self.normalize_unit_name(stripped)
            if stripped_norm:
                variations.append(stripped_norm)
                if 'Gregg' in stripped_norm:
                    variations.append(stripped_norm.replace('Gregg', 'Greg'))
        
        return variations
        extensions = ('.jpg', '.gif')
        
        for f in images_dir.iterdir():
            if f.suffix.lower() in extensions and f.name.startswith(prefixes):
                # Skip _d depleted versions
                if '_d.' in f.name:
                    continue
                base_name = f.stem
                # Prefer .jpg over .gif if both exist
                if base_name not in images or f.suffix.lower() == '.jpg':
                    images[base_name] = f
        return images
    
    def find_image_match(self, unit_leader: str, side: str, unit_type: str, available_set: set[str]) -> str | None:
        """Find matching image using C_/U_ prefix convention."""
        # Determine prefix based on side and unit type
        if unit_type == 'Ldr':
            prefix = 'CL_' if side == 'Confederate' else 'UL_'
        else:
            prefix = 'C_' if side == 'Confederate' else 'U_'
        
        for variation in self.get_alternate_names(unit_leader):
            candidate = f"{prefix}{variation}"
            if candidate in available_set:
                return candidate
        
        # For leaders, also try with command suffix (e.g., MeadeAP)
        if unit_type == 'Ldr':
            for variation in self.get_alternate_names(unit_leader):
                for suffix in ['AP', 'ANV', 'I', 'II', 'III', 'IV', 'V', 'VI', 'XI', 'XII', 'Cav', '1st', '2nd', '3rd']:
                    candidate = f"{prefix}{variation}{suffix}"
                    if candidate in available_set:
                        return candidate
        
        return None


class HCRExtractor(GameExtractor):
    """Extractor for HCR using plain name convention (no prefixes)."""
    
    def normalize_unit_name(self, name: str) -> str:
        """
        Normalize unit name for HCR.
        
        HCR uses plain names like "Lee", "Jackson", "McClellan", etc.
        Some have suffixes like "burnside_a".
        """
        # Remove periods
        name = name.replace('.', '')
        
        # Handle special units with no images
        if name.lower() in ['wagon train']:
            return None
        
        return name
    
    def get_alternate_names(self, name: str) -> list[str]:
        """Generate alternate name variations for HCR."""
        variations = []
        
        base = self.normalize_unit_name(name)
        if base is None:
            return []
        
        # Try as-is
        variations.append(base)
        
        # Try lowercase
        variations.append(base.lower())
        
        # Try with first letter uppercase, rest lowercase
        variations.append(base.capitalize())
        
        # For names with periods like "D.H. Hill-A" -> try "DHHill-A"
        if '.' in name:
            no_periods = name.replace('. ', '').replace('.', '')
            variations.append(no_periods)
            variations.append(no_periods.lower())
        
        # Try with underscores: "Burnside-A" -> "burnside_a"
        if '-' in base:
            with_underscore = base.replace('-', '_').lower()
            variations.append(with_underscore)
        
        # Strip leading initials: "A.P. Hill" -> "Hill"
        if re.match(r'^[A-Z]\.', name):
            stripped = re.sub(r'^[A-Z]\.\s*', '', name)
            if stripped:
                variations.append(stripped)
                variations.append(stripped.capitalize())
        
        # Strip two-letter initials: "D.H. Hill" -> "Hill"
        if re.match(r'^[A-Z]\.[A-Z]\.', name):
            stripped = re.sub(r'^[A-Z]\.[A-Z]\.\s*', '', name)
            if stripped:
                variations.append(stripped)
                variations.append(stripped.capitalize())
        
        # Strip initials with space: "D.R. Jones" -> "Jones"
        match = re.match(r'^([A-Z]\.)+\s+(.+)$', name)
        if match:
            last_name = match.group(2)
            variations.append(last_name)
            variations.append(last_name.capitalize())
        
        return variations
    
    def get_available_images(self, images_dir: Path) -> dict[str, Path]:
        """Get available images for HCR (no prefix requirement)."""
        images = {}
        extensions = ('.jpg', '.gif')
        
        # Exclude known non-unit image patterns
        exclude_patterns = [
            'Fort', 'Balt', 'Boton', 'VP', 'Marker', 'Ammu', 'Ace', 'Chart',
            'Control', 'CSA', 'USA', 'Destroyed', 'END', 'Falls', 'FORRAJEO',
            'Gasme', 'HCR', 'Indestructible', 'Inteli', 'Detroyed', 'Cigars',
            'Commitmen', 'DC-N', 'PA-N', 'RR-N', 'RR_', 'Shen-N', 'Map-',
            'mmm-', 'Nigth-', 'OOA', 'Rain', 'Slow-', 'Snake', 'Start',
            'Surrender', 'Time-', 'LEADER-master', 'Miayor-', 'Miinor-',
            'pleasontonL', 'PleasontonLd',  # These are duplicates
            # Corps designation counters (strength/quality)
            re.compile(r'^[A-Z]+-\d+-\d+'),  # e.g., "J-2-0", "L-3-1"
            re.compile(r'^[IVX]+-P-'),  # e.g., "I-P-1-0", "XII-P-2-3"
            re.compile(r'^[A-Z]+Sub-'),  # e.g., "JSub-2-0", "LLSub-J"
            re.compile(r'^T\d+$'),  # e.g., "T0", "T1"
            re.compile(r'^S_\d+_\d+$'),  # e.g., "S_2_1"
        ]
        
        for f in images_dir.iterdir():
            if f.suffix.lower() not in extensions:
                continue
            
            # Skip depleted versions
            if '_d.' in f.name:
                continue
            
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if isinstance(pattern, re.Pattern):
                    if pattern.match(f.name):
                        should_exclude = True
                        break
                elif pattern in f.name:
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            base_name = f.stem
            # Prefer .jpg over .gif if both exist
            if base_name not in images or f.suffix.lower() == '.jpg':
                images[base_name] = f
        
        return images
    
    def find_image_match(self, unit_leader: str, side: str, unit_type: str, available_set: set[str]) -> str | None:
        """Find matching image using plain name convention."""
        for variation in self.get_alternate_names(unit_leader):
            if variation in available_set:
                return variation
        
        return None


def get_extractor(game: str) -> GameExtractor:
    """Get the appropriate extractor for a game."""
    if game.lower() == 'hcr':
        return HCRExtractor()
    else:
        # Default to RTG2-style for other games
        return RTG2Extractor()


def load_parsed_units(game: str) -> tuple[dict[str, str], dict[str, str]]:
    """
    Load unique unit leaders from a parsed game file.
    
    Returns:
        Tuple of (confederate_units, union_units) dicts mapping unit_leader -> unit_type
    """
    parsed_file = Path(__file__).parent / 'parsed' / f'{game}_parsed.json'
    
    with open(parsed_file) as f:
        data = json.load(f)
    
    confederate = {}
    union = {}
    
    for scenario in data:
        for unit in scenario.get('confederate_units', []):
            name = unit['unit_leader']
            utype = unit.get('unit_type', 'Inf')
            # Keep the first type we encounter (or Ldr takes priority)
            if name not in confederate or utype == 'Ldr':
                confederate[name] = utype
        for unit in scenario.get('union_units', []):
            name = unit['unit_leader']
            utype = unit.get('unit_type', 'Inf')
            if name not in union or utype == 'Ldr':
                union[name] = utype
    
    return confederate, union


def find_images_directory(source: Path, game: str) -> Path:
    """
    Find the images directory from a source path.
    
    Handles:
    - Direct path to images directory
    - Path to extracted VMOD directory (with images subdirectory)
    - Path to directory containing .vmod files (searches for matching game)
    - Path to .vmod file directly
    """
    # If it's a .vmod file, extract it
    if source.is_file() and source.suffix.lower() == '.vmod':
        temp_dir = Path(tempfile.mkdtemp())
        print(f"Extracting {source}...")
        return extract_vmod(source, temp_dir)
    
    # If source/images exists, use it
    if (source / 'images').is_dir():
        return source / 'images'
    
    # If source itself is an images directory
    if source.name == 'images' and source.is_dir():
        return source
    
    # Look for .vmod files or extracted directories in source
    if source.is_dir():
        # Map game codes to possible VMOD naming patterns
        game_patterns = {
            'rtg2': ['RTGII', 'RTG2', 'RtG'],
            'otr2': ['OTRII', 'OTR2', 'OtR'],
            'gtc2': ['GTCII', 'GTC2', 'GtC'],
            'hcr': ['HCR', 'HctR'],
            'hsn': ['HSN'],
            'rtw': ['RTW', 'RitWH'],
        }
        
        patterns = game_patterns.get(game.lower(), [game.upper()])
        
        # First look for extracted directories (directories with 'images' subdirectory)
        for item in source.iterdir():
            if item.is_dir():
                for pattern in patterns:
                    if pattern.lower() in item.name.lower():
                        if (item / 'images').is_dir():
                            return item / 'images'
        
        # Then look for .vmod files
        for item in source.iterdir():
            if item.suffix.lower() == '.vmod':
                for pattern in patterns:
                    if pattern.lower() in item.name.lower():
                        temp_dir = Path(tempfile.mkdtemp())
                        print(f"Extracting {item}...")
                        return extract_vmod(item, temp_dir)
    
    raise ValueError(f"Could not find images directory or VMOD file for {game} in {source}")


def extract_vmod(vmod_path: Path, temp_dir: Path) -> Path:
    """Extract a .vmod file and return the path to the images directory."""
    with zipfile.ZipFile(vmod_path, 'r') as z:
        z.extractall(temp_dir)
    
    images_dir = temp_dir / 'images'
    if not images_dir.exists():
        raise ValueError(f"No 'images' directory found in {vmod_path}")
    
    return images_dir


def get_available_images(images_dir: Path, game: str) -> dict[str, Path]:
    """Get a dict of available images using game-specific extractor."""
    extractor = get_extractor(game)
    return extractor.get_available_images(images_dir)


def build_mapping(game: str, images_dir: Path) -> dict:
    """
    Build a mapping of unit names to image filenames.
    
    Returns a dict with:
    - matched: dict mapping unit_leader to image basename
    - unmatched: list of unit_leader names without matches
    - unused_images: list of images not matched to any unit
    """
    extractor = get_extractor(game)
    confederate_units, union_units = load_parsed_units(game)
    available_images = get_available_images(images_dir, game)
    available_set = set(available_images.keys())
    
    matched = {}
    matched_with_ext = {}  # Include file extension for web use
    unmatched = []
    used_images = set()
    
    # Match Confederate units
    for unit, unit_type in sorted(confederate_units.items()):
        img = extractor.find_image_match(unit, 'Confederate', unit_type, available_set)
        if img:
            matched[f"C:{unit}"] = img
            # Get the actual filename with extension
            img_path = available_images[img]
            matched_with_ext[f"C:{unit}"] = img_path.name
            used_images.add(img)
        else:
            unmatched.append(f"Confederate ({unit_type}): {unit}")
    
    # Match Union units
    for unit, unit_type in sorted(union_units.items()):
        img = extractor.find_image_match(unit, 'Union', unit_type, available_set)
        if img:
            matched[f"U:{unit}"] = img
            # Get the actual filename with extension
            img_path = available_images[img]
            matched_with_ext[f"U:{unit}"] = img_path.name
            used_images.add(img)
        else:
            unmatched.append(f"Union ({unit_type}): {unit}")
    
    # Find unused images (excluding markers, VPs, etc.)
    unused = []
    for img_name in sorted(available_set - used_images):
        # Skip known non-unit images
        if any(x in img_name for x in ['Sub', 'VP', 'Losses', 'Corp', 'Minor', 'WH-Lee', 'Shen']):
            continue
        unused.append(img_name)
    
    return {
        'matched': matched,
        'matched_with_ext': matched_with_ext,
        'unmatched': unmatched,
        'unused_images': unused,
        'image_paths': available_images
    }


def copy_images(mapping: dict, output_dir: Path, include_depleted: bool = False):
    """
    Copy matched images to the output directory.
    
    Args:
        mapping: Result from build_mapping()
        output_dir: Directory to copy images to
        include_depleted: Whether to also copy _d.gif depleted images
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_paths = mapping['image_paths']
    copied = 0
    
    for unit_key, img_name in mapping['matched'].items():
        if img_name in image_paths:
            src = image_paths[img_name]
            dst = output_dir / src.name
            shutil.copy2(src, dst)
            copied += 1
            
            # Also copy depleted version if requested
            if include_depleted:
                depleted_name = f"{img_name}_d.gif"
                depleted_src = src.parent / depleted_name
                if depleted_src.exists():
                    shutil.copy2(depleted_src, output_dir / depleted_name)
    
    return copied


def generate_typescript_map(game: str, matched_with_ext: dict, ts_file: Path):
    """
    Generate or update the TypeScript image mapping file.
    
    The file exports a nested object: { game: { "side:unitName": "filename.jpg" } }
    """
    # Read existing file if it exists
    existing_data = {}
    if ts_file.exists():
        content = ts_file.read_text()
        # Try to extract existing data - simple regex approach
        import re
        # Match the imageMap object definition
        match = re.search(r'export const imageMap[^=]*=\s*(\{[\s\S]*?\n\};)', content)
        if match:
            # We'll just regenerate the whole file to be safe
            pass
    
    # Build the new data
    existing_data[game] = matched_with_ext
    
    # Generate TypeScript content
    lines = [
        '// Auto-generated by extract_images.py - DO NOT EDIT MANUALLY',
        '// Maps unit keys ("C:UnitName" or "U:UnitName") to image filenames',
        '',
        'export type ImageMap = Record<string, Record<string, string>>;',
        '',
        'export const imageMap: ImageMap = {',
    ]
    
    for game_code in sorted(existing_data.keys()):
        game_data = existing_data[game_code]
        lines.append(f'  {game_code}: {{')
        for unit_key in sorted(game_data.keys()):
            filename = game_data[unit_key]
            # Escape quotes in keys
            safe_key = unit_key.replace('"', '\\"')
            lines.append(f'    "{safe_key}": "{filename}",')
        lines.append('  },')
    
    lines.append('};')
    lines.append('')
    lines.append('/**')
    lines.append(' * Get the image filename for a unit.')
    lines.append(' * @param game - Game code (e.g., "rtg2")')
    lines.append(' * @param side - "confederate" or "union"')
    lines.append(' * @param unitName - The unit leader/name field')
    lines.append(' * @returns The image filename or undefined if not found')
    lines.append(' */')
    lines.append('export function getUnitImage(game: string, side: "confederate" | "union", unitName: string): string | undefined {')
    lines.append('  const gameMap = imageMap[game];')
    lines.append('  if (!gameMap) return undefined;')
    lines.append('  const prefix = side === "confederate" ? "C" : "U";')
    lines.append('  return gameMap[`${prefix}:${unitName}`];')
    lines.append('}')
    lines.append('')
    
    ts_file.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Extract unit images from VASSAL modules')
    parser.add_argument('game', help='Game code (e.g., rtg2, otr2)')
    parser.add_argument('source', help='Path to .vmod file, extracted directory, or directory containing VMOD files')
    parser.add_argument('--output', '-o', help='Output directory (default: web/public/images/counters/<game>)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show mapping without copying files')
    parser.add_argument('--include-depleted', '-d', action='store_true', help='Also copy depleted/exhausted images')
    
    args = parser.parse_args()
    
    source = Path(args.source).expanduser()  # Handle ~ in paths
    
    # Find the images directory using smart detection
    images_dir = find_images_directory(source, args.game)
    print(f"Using images from: {images_dir}")
    
    mapping = build_mapping(args.game, images_dir)
    
    # Print results
    print(f"\n=== Mapping Results for {args.game} ===\n")
    print(f"Matched: {len(mapping['matched'])} units")
    print(f"Unmatched: {len(mapping['unmatched'])} units")
    print(f"Unused images: {len(mapping['unused_images'])} images")
    
    if mapping['unmatched']:
        print("\n--- Unmatched Units ---")
        for u in mapping['unmatched']:
            print(f"  {u}")
    
    if mapping['unused_images']:
        print("\n--- Unused Images ---")
        for img in mapping['unused_images']:
            print(f"  {img}")
    
    # Save mapping to JSON
    mapping_file = Path(__file__).parent / 'image_mappings' / f'{args.game}_images.json'
    mapping_file.parent.mkdir(exist_ok=True)
    
    # Create a clean mapping dict for JSON (without Path objects)
    clean_mapping = {
        'game': args.game,
        'matched': mapping['matched'],
        'matched_with_ext': mapping['matched_with_ext'],
        'unmatched': mapping['unmatched'],
        'unused_images': mapping['unused_images']
    }
    
    with open(mapping_file, 'w') as f:
        json.dump(clean_mapping, f, indent=2)
    print(f"\nMapping saved to: {mapping_file}")
    
    # Also generate a TypeScript file for the web app
    ts_file = Path(__file__).parent.parent / 'web' / 'src' / 'data' / 'imageMap.ts'
    ts_file.parent.mkdir(exist_ok=True)
    generate_typescript_map(args.game, mapping['matched_with_ext'], ts_file)
    print(f"TypeScript map updated: {ts_file}")
    
    if not args.dry_run:
        # Determine output directory
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = Path(__file__).parent.parent / 'web' / 'public' / 'images' / 'counters' / args.game
        
        copied = copy_images(mapping, output_dir, args.include_depleted)
        print(f"\nCopied {copied} images to: {output_dir}")


if __name__ == '__main__':
    main()
