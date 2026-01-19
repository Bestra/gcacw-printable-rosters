#!/usr/bin/env python
"""
Parse raw table rows into structured unit data using data-driven configuration.

This parser reads {game}_raw_tables.json files and converts them to structured
unit data compatible with the web app.

Usage:
    uv run python pipeline/parse_raw_tables.py otr2
    uv run python pipeline/parse_raw_tables.py --all
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Directory containing this script's parent (the parser directory)
PARSER_DIR = Path(__file__).parent.parent


@dataclass
class Unit:
    """Represents a parsed unit."""
    unit_leader: str
    size: str
    command: str
    unit_type: str
    manpower_value: str
    hex_location: str
    side: str
    notes: list = field(default_factory=list)
    # Optional fields for special tables
    turn: Optional[str] = None  # HCR reinforcement turn
    reinforcement_set: Optional[str] = None  # RTG2/HSN set number
    table_name: Optional[str] = None  # Source table name (e.g., "First Increment")


@dataclass
class ParsedScenario:
    """Represents a parsed scenario."""
    number: int
    name: str
    start_page: int
    confederate_units: list = field(default_factory=list)
    union_units: list = field(default_factory=list)
    confederate_footnotes: dict = field(default_factory=dict)
    union_footnotes: dict = field(default_factory=dict)
    # Metadata preserved from raw tables
    notes: str = ""
    map_info: str = ""
    game_length: str = ""
    special_rules: list = field(default_factory=list)


class RawTableParser:
    """Data-driven parser for raw table rows."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.config = self._load_config()
        self.unknown_symbols: set[str] = set()  # Track symbols we don't recognize
        
    def _load_config(self) -> dict:
        """Load game configuration."""
        config_path = PARSER_DIR / "game_configs.json"
        with open(config_path) as f:
            all_configs = json.load(f)
        
        # Merge defaults with game-specific config
        defaults = all_configs.get("defaults", {})
        game_config = all_configs.get(self.game_id, {})
        
        return {
            "columns": game_config.get("columns", defaults.get("columns", [])),
            "valid_sizes": defaults.get("valid_sizes", []),
            "valid_types": defaults.get("valid_types", []),
            "footnote_symbols": defaults.get("footnote_symbols", []),
            "special_unit_patterns": defaults.get("special_unit_patterns", []),
            "table_patterns": game_config.get("table_patterns", {}),
            "scenarios": game_config.get("scenarios", {}),
            "shared_scenarios": game_config.get("shared_scenarios", {}),
        }
    
    def _get_table_config(self, table_name: str, scenario_num: int) -> dict:
        """Get configuration for a specific table, with scenario overrides."""
        # Check scenario-specific overrides first
        scenario_config = self.config.get("scenarios", {}).get(str(scenario_num), {})
        table_overrides = scenario_config.get("table_overrides", {})
        if table_name in table_overrides:
            return table_overrides[table_name]
        
        # Check table name patterns
        for pattern, pattern_config in self.config.get("table_patterns", {}).items():
            if re.search(pattern, table_name, re.IGNORECASE):
                return pattern_config
        
        # Return defaults
        return {"columns": self.config.get("columns", [])}
    
    def _detect_columns_from_header(self, header_row: list) -> list:
        """Detect column layout from header row."""
        if not header_row:
            return self.config.get("columns", [])
        
        columns = []
        i = 0
        while i < len(header_row):
            token = header_row[i].lower()
            
            if "unit/leader" in token:
                columns.append("name")
            elif token == "turn":
                columns.append("turn")
            elif token == "set":
                columns.append("set")
            elif token == "#":
                # Part of "Set #" - skip
                pass
            elif token == "size":
                columns.append("size")
            elif token == "command":
                columns.append("command")
            elif token == "type":
                columns.append("type")
            elif "manpower" in token:
                columns.append("manpower")
            elif token == "hex" or token == "entry":
                columns.append("hex")
            elif "reinforcement" in token and "set" in token:
                columns.append("set")
            # Skip tokens that are part of multi-word headers
            elif token in ["value", "hexes", "area", "(see", "notes)", "alternative"]:
                pass
            
            i += 1
        
        return columns if columns else self.config.get("columns", [])
    
    def _extract_footnotes(self, value: str) -> tuple[str, list]:
        """Extract footnote symbols from a value. Returns (clean_value, [symbols])."""
        symbols = []
        clean = value
        known_symbols = self.config.get("footnote_symbols", [])
        
        # First pass: extract known symbols
        for sym in known_symbols:
            if sym in clean:
                symbols.append(sym)
                clean = clean.replace(sym, "")
        
        # Second pass: check for any remaining non-alphanumeric characters that might be unknown symbols
        # This catches symbols embedded in values like "3†" or "Longstreet*"
        for char in value:
            if char not in known_symbols and not char.isalnum() and not char.isspace() and char not in [',', '.', '-', '/', '(', ')', '[', ']']:
                self.unknown_symbols.add(char)
        
        return clean.strip(), symbols
    
    def _is_special_unit(self, tokens: list) -> bool:
        """Check if row represents a special unit (Gunboat, Wagon Train, etc.)."""
        if not tokens:
            return False
        first = tokens[0]
        for pattern in self.config.get("special_unit_patterns", []):
            if re.match(pattern, first, re.IGNORECASE):
                return True
        # Check for two-word patterns like "Naval Battery", "Wagon Train"
        if len(tokens) >= 2:
            combined = f"{tokens[0]} {tokens[1]}"
            if re.match(r"^Naval Battery|^Wagon Train", combined, re.IGNORECASE):
                return True
        return False
    
    def _parse_special_unit(self, tokens: list, side: str, table_name: str = "") -> Optional[Unit]:
        """Parse a special unit row (Gunboat, Wagon Train, Naval Battery)."""
        if not tokens:
            return None
        
        # Determine unit name
        if re.match(r"^Gunboat", tokens[0], re.IGNORECASE):
            unit_name = tokens[0]
            remaining = tokens[1:]
        elif len(tokens) >= 2 and re.match(r"^Naval|^Wagon", tokens[0], re.IGNORECASE):
            unit_name = f"{tokens[0]} {tokens[1]}"
            remaining = tokens[2:]
        else:
            return None
        
        # Find hex location - skip dashes and look for hex pattern or keywords
        hex_tokens = []
        for i, t in enumerate(remaining):
            if t == "-" or t == "—":
                continue
            if re.match(r"^[NS]\d{4}", t) or t.lower() in ["box", "river", "display", "reinforcement"]:
                hex_tokens = remaining[i:]
                break
        
        hex_location = " ".join(hex_tokens) if hex_tokens else ""
        
        # Sanity check
        if len(hex_location) > 60:
            hex_location = ""
        
        return Unit(
            unit_leader=unit_name,
            size="-",
            command="-",
            unit_type="Special",
            manpower_value="-",
            hex_location=hex_location,
            side=side,
            notes=[],
            table_name=table_name
        )
    
    def _find_size_index(self, tokens: list) -> tuple[Optional[int], Optional[str]]:
        """Find the index of the size token. Returns (index, normalized_size)."""
        valid_sizes = self.config.get("valid_sizes", [])
        
        for i, token in enumerate(tokens):
            # Clean footnote symbols for matching
            clean_token, _ = self._extract_footnotes(token)
            
            # Check for exact match
            if clean_token in valid_sizes:
                # Normalize D-Div to Demi-Div
                normalized = "Demi-Div" if clean_token == "D-Div" else clean_token
                return i, normalized
        
        return None, None
    
    def _parse_standard_unit(self, tokens: list, side: str, columns: list, 
                             table_name: str) -> Optional[Unit]:
        """Parse a standard unit row based on column configuration."""
        if len(tokens) < 4:
            return None
        
        # Find size token - this anchors our parsing
        size_idx, size_value = self._find_size_index(tokens)
        if size_idx is None:
            return None
        
        # Determine column layout
        # If columns has "turn" at start, first token is turn
        # If columns has "set" before size, we need to account for it
        
        turn_value = None
        set_value = None
        name_start = 0
        name_end = size_idx
        
        # Handle leading "turn" column (HCR)
        if columns and columns[0] == "turn":
            turn_value = tokens[0]
            name_start = 1
            # Recalculate size index relative to name
            size_idx, size_value = self._find_size_index(tokens[1:])
            if size_idx is not None:
                size_idx += 1  # Adjust for turn column
                name_end = size_idx
            else:
                return None
        
        # Handle "set" column before size (HSN variant)
        # If the token before size is a single digit, it might be a set number
        if "set" in columns and size_idx > name_start:
            potential_set = tokens[size_idx - 1]
            if re.match(r"^\d$", potential_set):
                set_value = potential_set
                name_end = size_idx - 1
        
        # Extract name tokens
        name_tokens = tokens[name_start:name_end]
        if not name_tokens:
            return None
        
        unit_name = " ".join(name_tokens)
        unit_name, name_notes = self._extract_footnotes(unit_name)
        
        # Tokens after size: command, type, manpower, hex...
        remaining = tokens[size_idx + 1:]
        
        if len(remaining) < 3:
            return None
        
        command = remaining[0]
        unit_type = remaining[1]
        manpower = remaining[2]
        
        # Validate unit type
        if unit_type not in self.config.get("valid_types", []):
            return None
        
        # Extract manpower footnotes
        manpower_clean, manpower_notes = self._extract_footnotes(manpower)
        
        # Remaining tokens are hex location (and possibly trailing set number)
        hex_tokens = remaining[3:]
        
        # Check for trailing reinforcement set number
        if hex_tokens and "set" in columns:
            last = hex_tokens[-1]
            if re.match(r"^\d$", last):
                set_value = last
                hex_tokens = hex_tokens[:-1]
        
        hex_location = " ".join(hex_tokens)
        
        # Combine all footnote markers
        all_notes = list(set(name_notes + manpower_notes))
        
        return Unit(
            unit_leader=unit_name,
            size=size_value,
            command=command,
            unit_type=unit_type,
            manpower_value=manpower,  # Keep original with symbols for display
            hex_location=hex_location,
            side=side,
            notes=sorted(all_notes),
            turn=turn_value,
            reinforcement_set=set_value,
            table_name=table_name
        )
    
    def parse_row(self, tokens: list, side: str, columns: list, 
                  table_name: str) -> Optional[Unit]:
        """Parse a single row into a Unit."""
        if not tokens:
            return None
        
        # Check for special units first
        if self._is_special_unit(tokens):
            return self._parse_special_unit(tokens, side, table_name)
        
        # Parse as standard unit
        return self._parse_standard_unit(tokens, side, columns, table_name)
    
    def parse_table(self, table: dict, side: str, scenario_num: int) -> list[Unit]:
        """Parse all rows in a table."""
        table_name = table.get("name", "")
        header_row = table.get("header_row", [])
        rows = table.get("rows", [])
        
        # Get column configuration
        table_config = self._get_table_config(table_name, scenario_num)
        
        # Detect columns from header if available
        columns = self._detect_columns_from_header(header_row)
        if not columns:
            columns = table_config.get("columns", self.config.get("columns", []))
        
        units = []
        for row in rows:
            unit = self.parse_row(row, side, columns, table_name)
            if unit:
                units.append(unit)
        
        return units
    
    def deduplicate_leaders(self, units: list[Unit]) -> list[Unit]:
        """
        Deduplicate leader units that appear in multiple setup tables.
        Keeps unique combinations of (unit_leader, hex_location) for leaders.
        Non-leader units are kept as-is.
        """
        leaders = []
        non_leaders = []
        seen_leaders = set()
        
        for unit in units:
            if unit.unit_type == "Ldr":
                # Create a key from leader name and hex
                key = (unit.unit_leader, unit.hex_location)
                if key not in seen_leaders:
                    leaders.append(unit)
                    seen_leaders.add(key)
            else:
                non_leaders.append(unit)
        
        return leaders + non_leaders
    
    def parse_scenario(self, raw_scenario: dict) -> ParsedScenario:
        """Parse a raw scenario into structured data."""
        scenario = ParsedScenario(
            number=raw_scenario["scenario_number"],
            name=raw_scenario["scenario_name"],
            start_page=raw_scenario["start_page"]
        )
        
        # Parse Confederate tables
        for table in raw_scenario.get("confederate_tables", []):
            units = self.parse_table(table, "Confederate", scenario.number)
            scenario.confederate_units.extend(units)
            # Collect footnotes
            for sym, text in table.get("annotations", {}).items():
                scenario.confederate_footnotes[sym] = text
        
        # Deduplicate Confederate leaders (for scenarios with multiple setup tables)
        scenario.confederate_units = self.deduplicate_leaders(scenario.confederate_units)
        
        # Parse Union tables
        for table in raw_scenario.get("union_tables", []):
            units = self.parse_table(table, "Union", scenario.number)
            scenario.union_units.extend(units)
            # Collect footnotes
            for sym, text in table.get("annotations", {}).items():
                scenario.union_footnotes[sym] = text
        
        # Deduplicate Union leaders (for scenarios with multiple setup tables)
        scenario.union_units = self.deduplicate_leaders(scenario.union_units)
        
        return scenario
    
    def parse_file(self, filepath: str) -> list[ParsedScenario]:
        """Parse a raw tables file."""
        with open(filepath) as f:
            raw_scenarios = json.load(f)
        
        scenarios = [self.parse_scenario(s) for s in raw_scenarios]
        
        # Handle shared scenarios (scenarios that use another scenario's setup)
        shared_scenarios = self.config.get("shared_scenarios", {})
        if shared_scenarios:
            # Build lookup by scenario number
            scenario_by_num = {s.number: s for s in scenarios}
            
            for target_str, source_num in shared_scenarios.items():
                if target_str.startswith("_"):  # Skip comments
                    continue
                target_num = int(target_str)
                target = scenario_by_num.get(target_num)
                source = scenario_by_num.get(source_num)
                
                if target and source and not target.confederate_units and not target.union_units:
                    # Copy units and footnotes from source to target
                    target.confederate_units = source.confederate_units.copy()
                    target.union_units = source.union_units.copy()
                    target.confederate_footnotes = source.confederate_footnotes.copy()
                    target.union_footnotes = source.union_footnotes.copy()
        
        return scenarios


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python pipeline/parse_raw_tables.py <game_id>")
        print("       uv run python pipeline/parse_raw_tables.py --all")
        sys.exit(1)
    
    # Ensure output directory exists
    parsed_dir = PARSER_DIR / "parsed"
    raw_dir = PARSER_DIR / "raw"
    parsed_dir.mkdir(exist_ok=True)
    
    games = ["otr2", "rtg2", "gtc2", "hcr", "hsn", "rwh"] if sys.argv[1] == "--all" else [sys.argv[1]]
    
    for game_id in games:
        input_file = raw_dir / f"{game_id}_raw_tables.json"
        output_file = parsed_dir / f"{game_id}_parsed.json"
        
        print(f"\nParsing {input_file}...")
        parser = RawTableParser(game_id)
        
        try:
            scenarios = parser.parse_file(str(input_file))
        except FileNotFoundError:
            print(f"  Error: {input_file} not found")
            continue
        
        print(f"  Parsed {len(scenarios)} scenarios")
        
        # Summary
        for s in scenarios:
            print(f"    Scenario {s.number}: {s.name}")
            print(f"      Confederate: {len(s.confederate_units)} units, {len(s.confederate_footnotes)} footnotes")
            print(f"      Union: {len(s.union_units)} units, {len(s.union_footnotes)} footnotes")
        
        # Export
        with open(output_file, "w") as f:
            json.dump([asdict(s) for s in scenarios], f, indent=2)
        print(f"  Exported to {output_file}")
        
        # Report any unknown footnote symbols
        if parser.unknown_symbols:
            print(f"  ⚠️  WARNING: Found unknown footnote symbols: {sorted(parser.unknown_symbols)}")
            print("     These symbols are not in game_configs.json footnote_symbols and may not be parsed correctly.")
            print("     Consider adding them to the defaults.footnote_symbols array.")


if __name__ == "__main__":
    main()
