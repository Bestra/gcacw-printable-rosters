"""
Hex location parsing and normalization.
Uses hex_location_config.json as the source of truth for patterns and abbreviations.
"""

import json
import re
from pathlib import Path
from typing import Optional, Tuple


# Load config on module import
_config_path = Path(__file__).parent / "hex_location_config.json"
with open(_config_path) as f:
    CONFIG = json.load(f)


def parse_hex_location(hex_location: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parse a hex location string into normalized components.
    
    Returns:
        (hex_code, location_name, warning)
        - hex_code: The primary display text (e.g., "GTC N2311", "May 5 Reinf.")
        - location_name: Optional secondary text (e.g., "Locust Grove")
        - warning: Optional warning if location seems malformed
    """
    if not hex_location or not hex_location.strip():
        return ("", None, "Empty hex location")
    
    hex_location = hex_location.strip()
    
    # Check for known unparseable strings (these are PDF parsing errors)
    for unparseable in CONFIG.get("knownUnparseable", []):
        if unparseable.lower() in hex_location.lower():
            return (hex_location[:20] + "...", None, f"Known unparseable: {hex_location[:50]}")
    
    # Check for exact match in special locations
    for pattern, result in CONFIG.get("specialLocations", {}).items():
        if hex_location.lower() == pattern.lower():
            return (result["hexCode"], result.get("locationName"), None)
    
    # Try each pattern in order
    for pattern_config in CONFIG.get("patterns", []):
        regex = pattern_config["regex"]
        match = re.match(regex, hex_location, re.IGNORECASE if pattern_config.get("type") != "hex" else 0)
        
        if match:
            pattern_type = pattern_config.get("type")
            
            if pattern_type == "hex":
                # Build hex code from groups
                groups = pattern_config.get("hexCodeGroups", [])
                hex_code = "".join(match.group(g) or "" for g in groups).strip()
                
                # Get location name
                loc_group = pattern_config.get("locationGroup")
                location_name = match.group(loc_group) if loc_group and match.group(loc_group) else None
                
                # Apply location abbreviations
                if location_name:
                    location_name = _apply_abbreviations(location_name)
                
                return (hex_code, location_name, None)
            
            elif pattern_type == "box":
                template = pattern_config.get("hexCodeTemplate", "{1} Box")
                hex_code = _apply_template(template, match)
                
                # Check for box abbreviations
                box_abbrevs = CONFIG.get("boxAbbreviations", {})
                hex_code = box_abbrevs.get(hex_code, hex_code)
                
                return (hex_code, None, None)
            
            elif pattern_type in ("dateReinforcement", "namedReinforcement"):
                template = pattern_config.get("hexCodeTemplate", "{1} Reinf.")
                hex_code = _apply_template(template, match)
                return (hex_code, None, None)
            
            elif pattern_type == "radius":
                template = pattern_config.get("hexCodeTemplate", "{1} hex radius")
                hex_code = _apply_template(template, match)
                
                loc_group = pattern_config.get("locationGroup")
                location_name = match.group(loc_group) if loc_group else None
                
                if location_name:
                    location_name = _apply_abbreviations(location_name)
                
                return (hex_code, location_name, None)
            
            elif pattern_type == "county":
                template = pattern_config.get("hexCodeTemplate", "In {1} Co.")
                hex_code = _apply_template(template, match)
                return (hex_code, None, None)
            
            else:
                # Generic pattern type - just apply template
                template = pattern_config.get("hexCodeTemplate", "{1}")
                hex_code = _apply_template(template, match)
                
                loc_group = pattern_config.get("locationGroup")
                location_name = match.group(loc_group) if loc_group else None
                
                if location_name:
                    location_name = _apply_abbreviations(location_name)
                
                return (hex_code, location_name, None)
    
    # Fallback: try to extract something useful
    # Check for parenthetical location
    paren_match = re.search(r'\(([^)]+)\)', hex_location)
    location_name = paren_match.group(1) if paren_match else None
    
    # Use first word as hex code
    first_word = hex_location.split()[0] if hex_location.split() else hex_location
    
    # Generate warning for unrecognized patterns (but not for simple words)
    warning = None
    if len(hex_location.split()) > 1 and not paren_match:
        warning = f"Unrecognized location pattern: {hex_location}"
    
    return (first_word, location_name, warning)


def _apply_template(template: str, match: re.Match) -> str:
    """Apply a template string with match group substitutions like {1}, {2}."""
    result = template
    for i in range(1, 10):
        placeholder = "{" + str(i) + "}"
        if placeholder in result:
            value = match.group(i) if i <= len(match.groups()) else ""
            result = result.replace(placeholder, value or "")
    return result.strip()


def _apply_abbreviations(text: str) -> str:
    """Apply location abbreviations from config."""
    for full, abbrev in CONFIG.get("locationAbbreviations", {}).items():
        text = re.sub(re.escape(full), abbrev, text, flags=re.IGNORECASE)
    return text


def validate_hex_locations(scenarios: list) -> list:
    """
    Validate all hex locations in a list of scenarios.
    Returns a list of warnings for review.
    """
    warnings = []
    
    for scenario in scenarios:
        scenario_num = scenario.get("number", "?")
        
        for side in ["confederate_units", "union_units"]:
            for unit in scenario.get(side, []):
                hex_loc = unit.get("hex_location", "")
                _, _, warning = parse_hex_location(hex_loc)
                
                if warning:
                    warnings.append({
                        "scenario": scenario_num,
                        "unit": unit.get("unit_leader", "?"),
                        "hex_location": hex_loc,
                        "warning": warning,
                    })
    
    return warnings


if __name__ == "__main__":
    # Test the parser with sample locations
    test_cases = [
        "S5510 (Yorktown)",
        "GTC N2311 (Locust Grove)",
        "OTR N0307 (Fox)",
        "SIV M2229 (Dunkard Church)",
        "Winchester Box",
        "Bermuda Hundred Box",
        "Drewry's Bluff box",
        "May 5 Reinforcement",
        "May 7 reinforcement",
        "Special Reinforcement",
        "Union Reinforcement",
        "Upon CSA reorganization",
        "Within 12 hexes of Hanover Junction",
        "Within 5 hexes of Bowling Green (N4825)",
        "is only for use in the GTC Grand Campaigns (see Grand",
    ]
    
    print("Testing hex location parser:\n")
    for loc in test_cases:
        hex_code, location_name, warning = parse_hex_location(loc)
        print(f"Input:    {loc}")
        print(f"  hex:    {hex_code}")
        print(f"  loc:    {location_name or '(none)'}")
        if warning:
            print(f"  WARN:   {warning}")
        print()
