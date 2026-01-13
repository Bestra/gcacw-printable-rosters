#!/usr/bin/env python3
"""
Unified counter image generator for GCACW games.

Supports games that use TEMPLATE_COMPOSITE counter systems where:
- Leader images are dedicated files (Grant.jpg, Lee.jpg, etc.)
- Unit counters use background templates with text labels

Usage:
    uv run python generate_counters.py gtc2 /path/to/GTC2.vmod
    uv run python generate_counters.py hcr /path/to/HCR.vmod
    uv run python generate_counters.py otr2 /path/to/OTR2.vmod
"""

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Run: uv add pillow")


# =============================================================================
# Game-specific configurations
# =============================================================================

@dataclass
class GameConfig:
    """Configuration for a specific game's counter generation."""
    game_id: str
    union_leaders: list[str] = field(default_factory=list)
    csa_leaders: list[str] = field(default_factory=list)
    name_variants_fn: Callable[[str], list[str]] | None = None
    extract_mappings_fn: Callable[[Path], dict] | None = None
    skip_units: list[str] = field(default_factory=lambda: ['Wagon Train', 'Gunboat', 'Naval Battery'])
    # For combined regiments that need fallback backgrounds
    combined_regiment_bg: dict[str, str] = field(default_factory=dict)


def base_normalize_name(name: str) -> str:
    """Basic name normalization shared across games."""
    name = ' '.join(name.split())
    name = re.sub(r'\s+-\s+([A-Z])$', r'-\1', name)
    return name


def base_get_name_variants(name: str) -> list[str]:
    """Generate basic name variants for fuzzy matching."""
    variants = [name]
    
    normalized = base_normalize_name(name)
    if normalized != name:
        variants.append(normalized)
    
    # Handle " - A" vs "-A" style suffixes
    if ' - ' in name:
        variants.append(name.replace(' - ', '-'))
    if re.search(r'-[A-Z]$', name):
        variants.append(re.sub(r'-([A-Z])$', r' - \1', name))
        base = re.sub(r'-[A-Z]$', '', name)
        variants.append(base)
    
    # Handle space vs hyphen
    if ' ' in name and '-' not in name:
        variants.append(name.replace(' ', '-'))
    if '-' in name and ' ' not in name:
        variants.append(name.replace('-', ' '))
    
    return list(set(variants))


# -----------------------------------------------------------------------------
# GTC2 Configuration
# -----------------------------------------------------------------------------

def gtc2_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (GTC2-specific)."""
    variants = base_get_name_variants(name)
    
    # Handle (B) vs -B suffix style
    paren_match = re.search(r'\s*\(([A-Z])\)$', name)
    if paren_match:
        base = re.sub(r'\s*\([A-Z]\)$', '', name)
        variants.append(f"{base}-{paren_match.group(1)}")
    hyphen_match = re.search(r'-([A-Z])$', name)
    if hyphen_match:
        base = re.sub(r'-[A-Z]$', '', name)
        variants.append(f"{base} ({hyphen_match.group(1)})")
    
    # Handle "WH Lee" vs "WHLee" vs "WH-Lee"
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[2:].strip()
        variants.append(f"{name[0]}{name[1]}{base}")
        variants.append(f"{name[0]}{name[1]}-{base}")
    if re.match(r'^[A-Z]{2}[A-Z]', name) and ' ' not in name[:4]:
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
        variants.append(f"{name[0]} {name[1]} {base}")
    if re.match(r'^[A-Z]\s[A-Z]\s', name):
        variants.append(f"{name[0]}{name[2]}{name[3:]}")
    
    # Typo handling
    if 'Wilcox' in name:
        variants.append(name.replace('Wilcox', 'Willcox'))
    if 'Willcox' in name:
        variants.append(name.replace('Willcox', 'Wilcox'))
    if 'Torbert' in name:
        variants.append(name.replace('Torbert', 'Tobert'))
    if 'Tobert' in name:
        variants.append(name.replace('Tobert', 'Torbert'))
    if 'Warren' in name:
        variants.append(name.replace('Warren', 'Warrent'))
    if 'Warrent' in name:
        variants.append(name.replace('Warrent', 'Warren'))
    if 'Schoonmaker' in name:
        variants.append(name.replace('Schoonmaker', 'Schoonmkr'))
    if 'Schoonmkr' in name:
        variants.append(name.replace('Schoonmkr', 'Schoonmaker'))
    
    # Handle escaped slashes
    if '\\/' in name:
        variants.append(name.replace('\\/', '/'))
    if '/' in name:
        variants.append(name.replace('/', '\\/'))
        variants.append(name.replace(' / ', '/'))
        variants.append(name.replace('/', ' / '))
        no_space = re.sub(r'(\d)([A-Z]{2})', r'\1 \2', name)
        if no_space != name:
            variants.append(no_space)
    
    # Handle "Art Res-1" vs "Art Res 1"
    if 'Art Res-' in name:
        variants.append(name.replace('Art Res-', 'Art Res '))
    if 'Art Res ' in name and '-' not in name:
        variants.append(name.replace('Art Res ', 'Art Res-'))
    
    # Handle "Hill" -> "AP Hill"
    if name == 'Hill':
        variants.extend(['AP Hill', 'AP HIll', 'A.P. Hill', 'APHill'])
    if 'AP Hill' in name or 'AP HIll' in name:
        variants.append('Hill')
        variants.append(name.replace('AP Hill', 'AP HIll'))
        variants.append(name.replace('AP HIll', 'AP Hill'))
    
    # Handle militia/artillery abbreviations
    if 'Militia' in name:
        variants.append(name.replace('Militia', 'Mil'))
    if 'VA Mil' in name and 'Militia' not in name:
        variants.append(name.replace('VA Mil', 'VA Militia'))
    if 'Washington Art' in name:
        variants.append(name.replace('Washington Art', 'Wash Art').replace('.', ''))
    if 'Wash Art' in name:
        variants.append(name.replace('Wash Art', 'Washington Art'))
        variants.append(name.replace('Wash Art', 'Washington Art.'))
    
    return list(set(variants))


def gtc2_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for GTC2."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
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
        
        if 'prototype;Leader' in slot_content:
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
                if 'CL-' in image_file:
                    mappings["Leaders"]["Confederate"][entry_name] = image_file
                else:
                    mappings["Leaders"]["Union"][entry_name] = image_file
        else:
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


GTC2_CONFIG = GameConfig(
    game_id='gtc2',
    name_variants_fn=gtc2_get_name_variants,
    extract_mappings_fn=gtc2_extract_unit_mappings,
)


# -----------------------------------------------------------------------------
# HCR Configuration
# -----------------------------------------------------------------------------

def hcr_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (HCR-specific)."""
    variants = base_get_name_variants(name)
    
    # Add version with periods followed by space: "A.P.Hill" -> "A.P. Hill"
    spaced = re.sub(r'\.([A-Z])', r'. \1', name)
    if spaced != name:
        variants.append(spaced)
    
    # Add version with suffix variations
    for suffix in ['-A', '-B']:
        variants.append(name + suffix)
        variants.append(base_normalize_name(name) + suffix)
    
    # Typo handling
    if 'Heitz' in name:
        variants.append(name.replace('Heitz', 'Heintz'))
    if 'Heintz' in name:
        variants.append(name.replace('Heintz', 'Heitz'))
    if 'Wilcox' in name:
        variants.append(name.replace('Wilcox', 'Willcox'))
    if 'Willcox' in name:
        variants.append(name.replace('Willcox', 'Wilcox'))
    
    # Handle apostrophe variants
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


def hcr_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for HCR."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        image_match = re.search(r'piece;;;([^;]+);[^/]+/', slot_content)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        if 'prototype;Leader' in slot_content:
            if any(name in entry_name for name in ['Burnside', 'Cox', 'Franklin', 'Heitz', 'Hooker', 
                    'Mansfield', 'McClellan', 'Pleasonton', 'Porter', 'Reno', 'Sigel', 'Sumner']):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif any(name in entry_name for name in ['Jackson', 'Lee', 'Longstreet', 'Stuart']):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment|Sub)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


HCR_CONFIG = GameConfig(
    game_id='hcr',
    name_variants_fn=hcr_get_name_variants,
    extract_mappings_fn=hcr_extract_unit_mappings,
)


# -----------------------------------------------------------------------------
# OTR2 Configuration
# -----------------------------------------------------------------------------

def otr2_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (OTR2-specific)."""
    variants = base_get_name_variants(name)
    
    # Handle Grifffith typo
    if 'Griffith' in name:
        variants.append(name.replace('Griffith', 'Grifffith'))
    if 'Grifffith' in name:
        variants.append(name.replace('Grifffith', 'Griffith'))
    
    # Handle missing spaces: "4PA" -> "4 PA"
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


def otr2_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for OTR2."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    piece_pattern = r'piece;;;([A-Za-z0-9_-]+\.(?:jpg|gif));([^/]+)/'
    
    for match in re.finditer(piece_pattern, content):
        image_file = match.group(1)
        unit_name = match.group(2).strip()
        
        # Skip markers
        if any(skip in unit_name for skip in ['VP', 'Ammu', 'Bridge', 'Wagon', 
                'Command', 'Ope', 'Mov', 'Track', 'CP', 'Paralysis']):
            continue
        if any(skip in image_file for skip in ['VP', 'Ammu', 'Control', 'Rv.', 
                'Ope.', 'Wagon', 'CP.']):
            continue
        
        if image_file.startswith('USA_'):
            mappings['Union'][unit_name] = {'image': image_file, 'type': 'Unit'}
        elif image_file.startswith('CSA_'):
            mappings['Confederate'][unit_name] = {'image': image_file, 'type': 'Unit'}
        elif image_file in ['Lee.jpg', 'Jackson.jpg', 'Johnston.jpg', 'Stuart.jpg', 
                           'Longstreet.jpg', 'Magruder.jpg', 'Smith.jpg', 
                           'AP-Hill.jpg', 'DH-Hill.jpg', 'DR-Jones.jpg']:
            mappings['Leaders']['Confederate'][unit_name] = image_file
        elif image_file in ['McClelland.jpg', 'Franklin.jpg', 'Heintzelman.jpg',
                           'Keyes.jpg', 'McDowell.jpg', 'Porter.jpg', 
                           'Sumner.jpg', 'Burnside.jpg']:
            mappings['Leaders']['Union'][unit_name] = image_file
    
    return mappings


OTR2_CONFIG = GameConfig(
    game_id='otr2',
    name_variants_fn=otr2_get_name_variants,
    extract_mappings_fn=otr2_extract_unit_mappings,
    combined_regiment_bg={
        'Union': 'USA_Ind_00.jpg',
        'Confederate': 'CSA_Ind_10.jpg'
    }
)


# -----------------------------------------------------------------------------
# HSN Configuration
# -----------------------------------------------------------------------------

def hsn_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (HSN-specific)."""
    variants = base_get_name_variants(name)
    
    # Handle "J Miller" vs "J. Miller"
    if re.match(r'^[A-Z]\s', name):
        base = name[2:]
        variants.append(f"{name[0]}. {base}")
        variants.append(f"{name[0]}{base}")
    
    # Handle "O. Moore" vs "O More" vs "O'More"
    if 'Moore' in name or 'More' in name:
        base_name = name.replace('O. Moore', 'O').replace('O Moore', 'O').replace('O. More', 'O').replace('O More', 'O').strip()
        if not base_name or base_name == 'O':
            variants.extend(['O More', "O'More", 'O Moore', 'O. Moore'])
        else:
            # Has additional qualifiers like "O. Moore (something)"
            variants.extend([
                base_name + ' More',
                base_name + ' Moore', 
                base_name + '. More',
                base_name + '. Moore'
            ])
    
    # Handle "R Johnson" vs "R. Johnson" vs "RJohnson"
    if name == 'R Johnson' or name == 'RJohnson' or name == 'R. Johnson':
        variants.extend(['R Johnson', 'R. Johnson', 'RJohnson'])
    
    # Handle "A. Miller" vs "A Miller" with numbers
    if 'Miller' in name:
        # "A. Miller 15" -> "A Miller 15", "A. Miller", "A Miller"
        variants.append(name.replace('A. Miller', 'A Miller'))
        variants.append(name.replace('A Miller', 'A. Miller'))
        if ' ' in name and name.split()[-1].isdigit():
            base = ' '.join(name.split()[:-1])
            variants.append(base)
    
    # Handle number suffixes: "Cooper 12" -> "Cooper", "LaGrange 13" -> "LaGrange"
    if ' ' in name and name.split()[-1].isdigit():
        base = ' '.join(name.split()[:-1])
        variants.append(base)
    
    # Handle USCT qualifier: "Thompson (USCT)" -> "Thompson", "Thompson (USCT) 10" -> "Thompson"
    if '(USCT)' in name:
        base = name.replace('(USCT)', '').strip()
        variants.append(base)
        # Also handle with number: "Thompson (USCT) 10" -> "Thompson"
        if ' ' in base and base.split()[-1].isdigit():
            variants.append(' '.join(base.split()[:-1]))
    
    # Handle "Lowrey - A" vs "Lowrey" vs "Lowrey-A"
    if 'Lowrey' in name:
        variants.extend(['Lowrey', 'Lowrey - A', 'Lowrey-A'])
    
    # Handle "#" suffix: "Lyon#" -> "Lyon"
    if name.endswith('#'):
        variants.append(name[:-1])
    if not name.endswith('#') and 'Lyon' in name:
        variants.append(name + '#')
    
    # Handle "@" suffix for leaders (Breckinridge@)
    if name.endswith('@'):
        variants.append(name[:-1])
    if not name.endswith('@'):
        variants.append(name + '@')
    
    return list(set(variants))


def hsn_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for HSN."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Skip markers and non-unit items
        if any(skip in entry_name.lower() for skip in ['vp', 'wagon', 'control', 'track', 
                'paralysis', 'game-turn', 'cycle', 'supply', 'event', 'posture', 'mov', 'ope']):
            continue
        
        if 'prototype;Leader' in slot_content:
            # Union leaders have UL_ prefix, Confederate have CL_ prefix
            if image_file.startswith('UL_'):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif image_file.startswith('CL_') or image_file.startswith('Cl_'):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            # Determine side and type from prototypes
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


HSN_CONFIG = GameConfig(
    game_id='hsn',
    name_variants_fn=hsn_get_name_variants,
    extract_mappings_fn=hsn_extract_unit_mappings,
)

# -----------------------------------------------------------------------------
# RWH (Rebels in the White House) Configuration  
# -----------------------------------------------------------------------------

def rwh_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Extract unit->background mappings from RWH buildFile.xml."""
    with open(buildfile_path) as f:
        content = f.read()
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Skip markers and non-unit items
        if any(skip in entry_name.lower() for skip in ['vp', 'wagon', 'control', 'track', 
                'paralysis', 'game-turn', 'cycle', 'supply', 'event', 'posture', 'mov', 'ope']):
            continue
        
        # Determine if it's a leader based on image filename
        if image_file.startswith('USA-') and len(image_file.split('-')) == 2:
            # USA-Name.jpg pattern indicates a leader
            leader_name = image_file.replace('USA-', '').replace('.jpg', '')
            if leader_name[0].isupper() and leader_name not in ['USA', 'CSA']:
                mappings["Leaders"]["Union"][entry_name] = image_file
                continue
        elif image_file.startswith('CSA-') and len(image_file.split('-')) == 2:
            leader_name = image_file.replace('CSA-', '').replace('.jpg', '')
            if leader_name[0].isupper() and leader_name not in ['USA', 'CSA']:
                mappings["Leaders"]["Confederate"][entry_name] = image_file
                continue
        
        # Units have image patterns like USA-xix-10.jpg, USA-ap00.jpg, CSA-b-10.jpg
        if image_file.startswith('USA-'):
            mappings["Union"][entry_name] = {
                "image": image_file,
                "type": "Unit"
            }
        elif image_file.startswith('CSA-'):
            mappings["Confederate"][entry_name] = {
                "image": image_file,
                "type": "Unit"
            }
    
    return mappings


RWH_CONFIG = GameConfig(
    game_id='rwh',
    name_variants_fn=base_get_name_variants,
    extract_mappings_fn=rwh_extract_unit_mappings,
)


# -----------------------------------------------------------------------------
# TOM (Thunder on Marsh Run) Configuration
# -----------------------------------------------------------------------------

def tom_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (TOM-specific)."""
    variants = base_get_name_variants(name)
    
    # Handle "49/69 IN" vs "49 / 69 IN" vs "49/69 IN"
    if '/' in name:
        # Add versions with spaces around slash
        variants.append(re.sub(r'(\d+)/(\d+)', r'\1 / \2', name))
        # Add version without IN suffix
        base = re.sub(r'\s+IN$', '', name)
        if base != name:
            variants.append(base)
            variants.append(re.sub(r'(\d+)/(\d+)', r'\1 / \2', base))
    
    # Handle "(dmnt)" vs "Dmt" dismounted variants
    if '(dmnt)' in name.lower():
        # "1 MO (dmnt)" -> "1 MO Dmt"
        variants.append(re.sub(r'\s*\(dmnt\)', ' Dmt', name, flags=re.IGNORECASE))
    if 'dmt' in name.lower():
        # "1 MO Dmt" -> "1 MO (dmnt)"
        variants.append(re.sub(r'\s+dmt', ' (dmnt)', name, flags=re.IGNORECASE))
    
    # Handle "25/29 GA" style combined regiments
    if re.match(r'^\d+/\d+\s+[A-Z]{2}', name):
        variants.append(re.sub(r'(\d+)/(\d+)', r'\1 / \2', name))
    
    # Handle "AJ Smith" vs "AJ Smith - A" vs "AJ Smith-A"
    if 'AJ Smith' in name or 'A J Smith' in name:
        base = 'AJ Smith'
        variants.extend([base, 'A J Smith', 'A.J. Smith'])
        if '-A' in name or ' - A' in name:
            variants.extend([f'{base} - A', f'{base}-A', 'A J Smith - A', 'A J Smith-A'])
        if '-B' in name or ' - B' in name:
            variants.extend([f'{base} - B', f'{base}-B', 'A J Smith - B', 'A J Smith-B'])
    
    # Handle "AW Reynolds" vs "A W Reynolds" vs "A.W. Reynolds"
    if 'AW Reynolds' in name or 'A W Reynolds' in name:
        variants.extend(['AW Reynolds', 'A W Reynolds', 'A.W. Reynolds'])
    
    # Handle "WS Smith" vs "W S Smith" vs "W.S. Smith"
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[2:].strip()
        variants.append(f"{name[0]} {name[1]} {base}")
        variants.append(f"{name[0]}.{name[1]}. {base}")
    if re.match(r'^[A-Z]\s[A-Z]\s', name):
        base = name[4:].strip()
        variants.append(f"{name[0]}{name[2]} {base}")
        variants.append(f"{name[0]}.{name[2]}. {base}")
    
    return list(set(variants))


def tom_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for TOM."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Skip markers and non-unit items
        if any(skip in entry_name.lower() for skip in ['vp', 'wagon', 'control', 'track',
                'paralysis', 'game-turn', 'cycle', 'supply', 'event', 'posture', 'mov', 'ope',
                'ammunition', 'bridge', 'command']):
            continue
        if any(skip in image_file.lower() for skip in ['vp', 'control', 'wagon', 'cp.',
                'track', 'paralysis', 'ammu', 'event']):
            continue
        
        if 'prototype;Leader' in slot_content:
            # Union leaders have U- prefix, Confederate have C- prefix
            if image_file.startswith('U-'):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif image_file.startswith('C-'):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            # Determine side and type from prototypes
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


TOM_CONFIG = GameConfig(
    game_id='tom',
    name_variants_fn=tom_get_name_variants,
    extract_mappings_fn=tom_extract_unit_mappings,
)


# -----------------------------------------------------------------------------
# TPC (The Peninsula Campaign) Configuration
# -----------------------------------------------------------------------------

def tpc_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (TPC-specific)."""
    variants = base_get_name_variants(name)
    
    # Handle regiment numbers with slashes: "10/37 Clrd" vs "10 / 37 Clrd"
    if '/' in name:
        variants.append(re.sub(r'(\d+)/(\d+)', r'\1 / \2', name))
    
    # Handle "Clrd" vs "Colored"
    if 'Clrd' in name:
        variants.append(name.replace('Clrd', 'Colored'))
    if 'Colored' in name:
        variants.append(name.replace('Colored', 'Clrd'))
    
    # Handle initials: "AJ Smith" vs "A J Smith" vs "A.J. Smith"
    if re.match(r'^[A-Z]{2}\s', name):
        base = name[2:].strip()
        variants.append(f"{name[0]} {name[1]} {base}")
        variants.append(f"{name[0]}.{name[1]}. {base}")
    if re.match(r'^[A-Z]\s[A-Z]\s', name):
        base = name[4:].strip()
        variants.append(f"{name[0]}{name[2]} {base}")
        variants.append(f"{name[0]}.{name[2]}. {base}")
    
    # Handle "Birney II" vs "Birney - II" vs "Birney-II"
    if re.search(r'\s+(II|X|XVIII|XIX|XXIV|I|V|VI|IX)$', name):
        # "Birney II" -> "Birney - II", "Birney-II"
        variants.append(re.sub(r'\s+([IVX]+)$', r' - \1', name))
        variants.append(re.sub(r'\s+([IVX]+)$', r'-\1', name))
    if ' - ' in name and re.search(r'\s+-\s+(II|X|XVIII|XIX|XXIV|I|V|VI|IX)$', name):
        # "Birney - II" -> "Birney II", "Birney-II"
        variants.append(re.sub(r'\s+-\s+([IVX]+)$', r' \1', name))
        variants.append(re.sub(r'\s+-\s+([IVX]+)$', r'-\1', name))
    if '-' in name and not ' - ' in name and re.search(r'-([IVX]+)$', name):
        # "Birney-II" -> "Birney II", "Birney - II"
        variants.append(re.sub(r'-([IVX]+)$', r' \1', name))
        variants.append(re.sub(r'-([IVX]+)$', r' - \1', name))
    
    return list(set(variants))


def tpc_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for TPC."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')
    
    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }
    
    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'
    
    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)
        
        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)
        
        # Skip markers and non-unit items
        if any(skip in entry_name.lower() for skip in ['vp', 'wagon', 'control', 'track',
                'paralysis', 'game-turn', 'cycle', 'supply', 'event', 'posture', 'mov', 'ope',
                'ammunition', 'bridge', 'command', 'replacement']):
            continue
        if any(skip in image_file.lower() for skip in ['vp', 'control', 'wagon', 'cp.',
                'track', 'paralysis', 'ammu', 'event', 'replacement']):
            continue
        
        if 'prototype;Leader' in slot_content:
            # Determine side based on common leader names or image patterns
            union_leaders = ['Averell', 'Brooks', 'Burnside', 'Casey', 'Couch', 'Franklin',
                           'Heintzelman', 'Hooker', 'Keyes', 'Kearney', 'McClellan', 'McDowell',
                           'Porter', 'Richardson', 'Sedgwick', 'Slocum', 'Stoneman', 'Sumner',
                           'Sykes', 'Williams']
            csa_leaders = ['Anderson', 'AP Hill', 'DH Hill', 'Ewell', 'Hampton', 'Holmes',
                         'Huger', 'Jackson', 'Johnston', 'Lee', 'Longstreet', 'Magruder',
                         'Stuart', 'Whiting']
            
            if any(leader in entry_name for leader in union_leaders):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif any(leader in entry_name for leader in csa_leaders):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
            else:
                # Fall back to image file naming if available
                if image_file.startswith('U-') or image_file.startswith('UL'):
                    mappings["Leaders"]["Union"][entry_name] = image_file
                else:
                    mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            # Determine side and type from prototypes
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }
    
    return mappings


TPC_CONFIG = GameConfig(
    game_id='tpc',
    name_variants_fn=tpc_get_name_variants,
    extract_mappings_fn=tpc_extract_unit_mappings,
)


# -----------------------------------------------------------------------------
# Game registry
# -----------------------------------------------------------------------------

GAME_CONFIGS: dict[str, GameConfig] = {
    'gtc2': GTC2_CONFIG,
    'hcr': HCR_CONFIG,
    'otr2': OTR2_CONFIG,
    'hsn': HSN_CONFIG,
    'rwh': RWH_CONFIG,
    'tom': TOM_CONFIG,
    'tpc': TPC_CONFIG,
}


# =============================================================================
# Shared counter generation logic
# =============================================================================

def generate_counter_image(
    background_path: Path,
    unit_name: str,
    output_path: Path,
    font_size: int = 14
):
    """Generate a composite counter image with unit name overlaid on background."""
    if not HAS_PIL:
        shutil.copy2(background_path, output_path)
        return
    
    bg = Image.open(background_path).convert('RGBA')
    draw = ImageDraw.Draw(bg)
    
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
    
    bbox = draw.textbbox((0, 0), unit_name, font=font)
    text_width = bbox[2] - bbox[0]
    
    x = (bg.width - text_width) // 2
    y = 3
    
    draw.text((x, y), unit_name, fill=(0, 0, 0, 255), font=font)
    
    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
        bg = bg.convert('RGB')
    
    bg.save(output_path, quality=95)


def run_counter_generation(
    game_id: str,
    source: Path,
    output_dir: Path | None = None,
    dry_run: bool = False,
    leaders_only: bool = False,
    no_text: bool = False,
):
    """Main counter generation logic shared across all games."""
    
    config = GAME_CONFIGS.get(game_id)
    if not config:
        raise ValueError(f"Unknown game: {game_id}. Available: {list(GAME_CONFIGS.keys())}")
    
    get_name_variants = config.name_variants_fn or base_get_name_variants
    extract_unit_mappings = config.extract_mappings_fn
    
    if not extract_unit_mappings:
        raise ValueError(f"No extract_mappings_fn defined for {game_id}")
    
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
    
    # Load parsed data
    parsed_file = Path(__file__).parent.parent / 'parsed' / f'{game_id}_parsed.json'
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
    
    if dry_run:
        print("\n--- Union Leaders ---")
        for name, img in sorted(mappings['Leaders']['Union'].items()):
            print(f"  {name}: {img}")
        
        print("\n--- Confederate Leaders ---")
        for name, img in sorted(mappings['Leaders']['Confederate'].items()):
            print(f"  {name}: {img}")
        
        print("\n--- Sample Union Units ---")
        for name, info in list(sorted(mappings['Union'].items()))[:20]:
            img = info['image'] if isinstance(info, dict) else info
            print(f"  {name}: {img}")
        
        print("\n--- Sample Confederate Units ---")
        for name, info in list(sorted(mappings['Confederate'].items()))[:20]:
            img = info['image'] if isinstance(info, dict) else info
            print(f"  {name}: {img}")
        
        return
    
    # Determine output directory
    if output_dir is None:
        # Go up from parser/image_extraction/ to project root, then into web/
        output_dir = Path(__file__).parent.parent.parent / 'web' / 'public' / 'images' / 'counters' / game_id
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build lookup
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
    
    # Generate images
    image_map = {}
    unmatched = []
    
    print("\n--- Generating Images ---")
    for side in ['Union', 'Confederate']:
        prefix = 'U' if side == 'Union' else 'C'
        for parsed_name, utype in sorted(parsed_units.get(side, {}).items()):
            # Skip special units
            if any(skip in parsed_name for skip in config.skip_units):
                continue
            
            # Try to find matching VASSAL unit
            vassal_info = None
            for variant in get_name_variants(parsed_name):
                key = (side, variant)
                if key in vassal_lookup:
                    vassal_info = vassal_lookup[key]
                    break
            
            # Fallback for combined regiments
            if not vassal_info and '/' in parsed_name and config.combined_regiment_bg:
                fallback_bg = config.combined_regiment_bg.get(side)
                if fallback_bg and (images_dir / fallback_bg).exists():
                    vassal_info = {'image': fallback_bg, 'type': 'CombinedRegiment'}
            
            if not vassal_info:
                unmatched.append(f"{side} ({utype}): {parsed_name}")
                continue
            
            img_file = vassal_info['image'] if isinstance(vassal_info, dict) else vassal_info
            src = images_dir / img_file
            
            if not src.exists():
                print(f"  Missing: {img_file} for {parsed_name}")
                unmatched.append(f"{side} ({utype}): {parsed_name} [missing: {img_file}]")
                continue
            
            unit_type = vassal_info.get('type', 'Unit') if isinstance(vassal_info, dict) else 'Unit'
            
            if unit_type == 'Leader':
                dst = output_dir / img_file
                if not dst.exists():
                    shutil.copy2(src, dst)
                image_map[f"{prefix}:{parsed_name}"] = img_file
                print(f"  Copied: {parsed_name} -> {img_file}")
            elif leaders_only:
                continue
            elif no_text:
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "").replace('/', '-')
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                shutil.copy2(src, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Copied (no text): {parsed_name} -> {output_file}")
            else:
                safe_name = parsed_name.replace(' ', '_').replace('.', '').replace("'", "").replace('/', '-')
                output_file = f"{prefix}_{safe_name}.jpg"
                dst = output_dir / output_file
                
                generate_counter_image(src, parsed_name, dst)
                image_map[f"{prefix}:{parsed_name}"] = output_file
                print(f"  Generated: {parsed_name} -> {output_file}")
    
    # Save mapping
    mapping_file = Path(__file__).parent / 'image_mappings' / f'{game_id}_images.json'
    mapping_file.parent.mkdir(exist_ok=True)
    
    matched = {}
    matched_with_ext = {}
    for key, filename in image_map.items():
        base = Path(filename).stem
        matched[key] = base
        matched_with_ext[key] = filename
    
    mapping_data = {
        'game': game_id,
        'counterType': 'template',
        'matched': matched,
        'matched_with_ext': matched_with_ext,
        'unmatched': unmatched,
        'unused_images': [],
        'note': f'Generated by generate_counters.py for {game_id}'
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


def main():
    parser = argparse.ArgumentParser(description='Generate composite counter images for GCACW games')
    parser.add_argument('game', choices=list(GAME_CONFIGS.keys()), help='Game ID')
    parser.add_argument('source', help='Path to .vmod file or extracted directory')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show mappings without generating images')
    parser.add_argument('--leaders-only', action='store_true', help='Only copy leader images')
    parser.add_argument('--no-text', action='store_true', help='Copy backgrounds without text overlay')
    
    args = parser.parse_args()
    
    source = Path(args.source).expanduser()
    output_dir = Path(args.output) if args.output else None
    
    run_counter_generation(
        game_id=args.game,
        source=source,
        output_dir=output_dir,
        dry_run=args.dry_run,
        leaders_only=args.leaders_only,
        no_text=args.no_text,
    )


if __name__ == '__main__':
    main()
