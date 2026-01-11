"""
GCACW Scenario Parser
Parses PDF scenario documents from Great Campaigns of the American Civil War series.
Extracts scenario metadata and unit setup tables.
"""

import pdfplumber
import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Unit:
    """Represents a military unit in a scenario setup."""
    unit_leader: str
    size: str
    command: str
    unit_type: str
    manpower_value: str
    hex_location: str
    side: str  # 'Confederate' or 'Union'
    notes: list = field(default_factory=list)  # Footnote markers like *, ^


@dataclass 
class Scenario:
    """Represents a complete scenario with metadata and units."""
    number: int
    name: str
    start_page: int
    notes: str = ""
    map_info: str = ""
    game_length: str = ""
    special_rules: list = field(default_factory=list)
    confederate_footnotes: dict = field(default_factory=dict)  # Maps symbols to explanations for Confederate setup
    union_footnotes: dict = field(default_factory=dict)  # Maps symbols to explanations for Union setup
    confederate_units: list = field(default_factory=list)
    union_units: list = field(default_factory=list)


class ScenarioParser:
    """Parser for GCACW scenario PDFs."""
    
    # Valid unit sizes - order matters for matching (D-Div is abbreviation for Demi-Div)
    VALID_SIZES = ['Army', 'Corps', 'Demi-Div', 'D-Div', 'Div', 'Brig', 'Regt']
    VALID_TYPES = ['Ldr', 'Inf', 'Cav', 'Art']
    
    # Page ranges for games that share a PDF (1-indexed, inclusive)
    # Format: (start_page, end_page) or None to parse entire PDF
    # RTG2_Rules.pdf contains three games: HCR, RTG2, and RTW
    PAGE_RANGES = {
        "hcr": (1, 44),    # Here Come the Rebels! scenarios
        "rtg2": (45, 95),  # Roads to Gettysburg 2 scenarios
        "rtw": (96, 116),  # RTW scenarios 1-4 (scenario 5 starts on 117)
    }
    
    # Known scenario names by game
    SCENARIO_NAMES = {
        "otr2": {
            1: "The Warwick Line",
            2: "Johnston's Retreat", 
            3: "The Gates of Richmond",
            4: "Seven Pines",
            5: "Stuart's Ride",
            6: "The Seven Days",
            7: "Gaines Mill",
            8: "Retreat to the James",
            9: "The Peninsula Campaign",
        },
        "gtc2": {
            1: "The Battle of the Wilderness",
            2: "Grant Crosses the Rapidan",
            3: "Race for Spotsylvania",
            4: "Bloody Spotsylvania",
            5: "Sheridan Rides South",
            6: "Strike Them a Blow!",
            7: "Bethesda Church",
            8: "Trevilian Station",
            9: "The Overland Campaign",
            10: "Marching to Cold Harbor",
            11: "Grant's 1864 Offensive",
            12: "If It Takes All Summer",
        },
        "hsn": {
            1: "Here Come the Rebels!",
            2: "The Race for Columbia",
            3: "A Great Chance Was Lost",
            4: "We Will Make the Fight",
            5: "The Enemy Was Badly Whipped",
            6: "The Battle of Nashville",
            7: "Hood's Retreat",
            8: "That Devil Forrest",
            9: "Hood Strikes North",
        },
        "hcr": {
            1: "South Mountain",
            2: "Harpers Ferry – Crampton Gap",
            3: "McClellan's Opportunity",
            4: "Three Cigars",
            5: "The Baltimore Raid",
            6: "The Battle for Washington",
            7: "From Frederick to Sharpsburg",
            8: "The Maryland Campaign",
        },
        "rtg2": {
            1: "Meade Moves North",
            2: "Stuart Rides North",
            3: "Confederate High Tide",
            4: "First Day at Gettysburg",
            5: "Battle of Gettysburg",
            6: "The Pipe Creek Plan",
            7: "The Battle Continues",
            8: "The Wagoneer's Fight",
            9: "The Battle that Never Happened",
            10: "The Gettysburg Campaign",
        },
        # RTW: Scenario 5 (Early's Raid) omitted - unit setup references Scenario 4 instead of listing units
        "rtw": {
            1: "Monocacy",
            2: "Fort Stevens",
            3: "The Retreat From Washington",
            4: "From Winchester to Washington",
        },
    }
    
    def __init__(self, pdf_path: str, game_id: str = "otr2", start_page: int = None, end_page: int = None):
        self.pdf_path = pdf_path
        self.game_id = game_id
        self.scenarios: list[Scenario] = []
        
        # Use provided page range, or look up from PAGE_RANGES, or use entire PDF
        if start_page is not None:
            self.start_page = start_page - 1  # Convert to 0-indexed
            self.end_page = end_page if end_page else None  # Will be set to len(pdf.pages) later
        elif game_id in self.PAGE_RANGES:
            range_start, range_end = self.PAGE_RANGES[game_id]
            self.start_page = range_start - 1  # Convert to 0-indexed
            self.end_page = range_end
        else:
            self.start_page = 0
            self.end_page = None  # Will be set to len(pdf.pages) later
        
    def parse(self) -> list[Scenario]:
        """Parse the PDF and extract all scenarios within the page range."""
        with pdfplumber.open(self.pdf_path) as pdf:
            # Set end_page if not already set
            if self.end_page is None:
                self.end_page = len(pdf.pages)
            
            # First pass: find all scenario start pages
            scenario_pages = self._find_scenario_pages(pdf)
            
            # Second pass: parse each scenario
            for i, (page_num, scenario_num, scenario_name) in enumerate(scenario_pages):
                # Determine end page (start of next scenario or end of range)
                if i + 1 < len(scenario_pages):
                    end_page = scenario_pages[i + 1][0]
                else:
                    end_page = self.end_page
                
                scenario = self._parse_scenario(pdf, page_num, end_page, scenario_num, scenario_name)
                self.scenarios.append(scenario)
        
        return self.scenarios
    
    def _find_scenario_pages(self, pdf) -> list[tuple[int, int, str]]:
        """Find all scenario header pages. Returns [(page_num, scenario_num, name), ...]"""
        # Pattern to find scenario number
        scenario_pattern = re.compile(r'scenario\s+(\d+):', re.IGNORECASE)
        
        # Known scenario names from TOC for validation/cleanup
        known_names = self.SCENARIO_NAMES.get(self.game_id, {})
        
        results = []
        seen_scenarios = set()  # Avoid duplicates
        
        # Only scan within the configured page range
        for i in range(self.start_page, self.end_page):
            if i >= len(pdf.pages):
                break
            page = pdf.pages[i]
            text = page.extract_text()
            if not text:
                continue
            
            # Skip table of contents pages (only if we're starting from the beginning)
            if self.start_page == 0 and i < 3:
                continue
            
            # Also skip pages that contain TOC markers like "Table of Contents" or "Basic Game Scenarios"
            # (RTG2 has its TOC on page 45)
            text_lower = text.lower()
            if 'table of contents' in text_lower or 'basic game scenarios' in text_lower:
                continue
                
            for line in text.split('\n'):
                match = scenario_pattern.search(line)
                if match:
                    scenario_num = int(match.group(1))
                    # Skip if we've already seen this scenario
                    if scenario_num in seen_scenarios:
                        continue
                    seen_scenarios.add(scenario_num)
                    
                    # Use known name
                    scenario_name = known_names.get(scenario_num, f"Scenario {scenario_num}")
                    results.append((i, scenario_num, scenario_name))
                    break  # Only first match per page
        
        return results
    
    def _parse_scenario(self, pdf, start_page: int, end_page: int, 
                        scenario_num: int, scenario_name: str) -> Scenario:
        """Parse a single scenario from the given page range."""
        scenario = Scenario(
            number=scenario_num,
            name=scenario_name,
            start_page=start_page + 1  # Convert to 1-indexed
        )
        
        # Collect all text from scenario pages
        # Include one extra page to catch continuation tables
        confederate_footnotes = {}
        union_footnotes = {}
        current_side = None  # Track side across pages
        
        # Extend parsing to include the "end_page" to catch continuations
        actual_end = min(end_page + 1, len(pdf.pages))
        
        for page_idx in range(start_page, actual_end):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue
            
            # Extract metadata from first scenario page
            if page_idx == start_page:
                scenario.notes = self._extract_notes(text)
                scenario.map_info = self._extract_map_info(text)
                scenario.game_length = self._extract_game_length(text)
                scenario.special_rules = self._extract_special_rules(text)
            
            # Extract units
            lines = text.split('\n')
            stop_parsing = False
            
            # On the start page, we need to find the scenario header first
            # and only process lines AFTER it to avoid picking up previous scenario's tables
            found_scenario_header_on_start_page = False
            if page_idx == start_page:
                # We'll set this to True once we find our scenario header
                found_scenario_header_on_start_page = False
            else:
                # On subsequent pages, we're already past the header
                found_scenario_header_on_start_page = True
            
            for line in lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # On the start page, look for our scenario header before processing anything
                if page_idx == start_page and not found_scenario_header_on_start_page:
                    scenario_match = re.search(rf'scenario\s+{scenario_num}:', line_lower)
                    if scenario_match:
                        found_scenario_header_on_start_page = True
                    # Skip all lines until we find our scenario header
                    continue
                
                # Stop if we hit the next scenario header
                scenario_match = re.search(r'scenario\s+(\d+):', line_lower)
                if scenario_match:
                    next_scenario_num = int(scenario_match.group(1))
                    if next_scenario_num != scenario_num:
                        stop_parsing = True
                        break
                
                # Stop if we hit Advanced Game Rules SECTION HEADER - but not just
                # references to advanced game rules within scenario text.
                # The actual section header is a line that STARTS with the section indicator,
                # like "1.0 advanced Game sequence of play" or "advanced Game Rules" as a title.
                # Skip lines that just mention "Advanced Game" in the middle of other text.
                is_advanced_game_section_header = (
                    # Numbered section header like "1.0 advanced Game sequence of play"
                    re.match(r'^\d+\.\d*\s+advanced\s+game', line_lower) or
                    # Line starts with "advanced game rules" as a title
                    re.match(r'^advanced\s+game\s+rules\b', line_lower) or
                    # The intro line for the advanced rules section (but must start with it)
                    re.match(r'^the following rules are used only in advanced game', line_lower)
                )
                if is_advanced_game_section_header:
                    # Only stop if we haven't started collecting units
                    if not scenario.confederate_units and not scenario.union_units:
                        stop_parsing = True
                        break
                
                # Detect section headers (including continuations like "cntd")
                # But IGNORE continuations "(cntd)" as they belong to previous scenario
                if 'confederate set-up' in line_lower:
                    if '(cntd)' in line_lower or 'cntd' in line_lower:
                        # This is a continuation of a PREVIOUS scenario's table
                        # Only accept if we're on a page after the start page
                        # AND we've already been collecting units for this scenario
                        if current_side is None:
                            # Haven't started collecting yet, skip this continuation
                            continue
                    current_side = 'Confederate'
                    continue
                elif 'union set-up' in line_lower:
                    if '(cntd)' in line_lower or 'cntd' in line_lower:
                        # This is a continuation of a PREVIOUS scenario's table
                        if current_side is None:
                            # Haven't started collecting yet, skip this continuation
                            continue
                    current_side = 'Union'
                    continue
                
                # Skip header rows
                if 'unit/leader' in line_lower or 'unIt/leader' in line_lower:
                    continue
                
                # Capture footnotes (lines starting with * or ^ or $)
                footnote_match = re.match(r'^([\*\^†‡§\$\+]+)\s+(.+)$', line_stripped)
                if footnote_match:
                    symbol = footnote_match.group(1)
                    explanation = footnote_match.group(2)
                    # Store footnote in the appropriate side's dict
                    if current_side == 'Confederate':
                        confederate_footnotes[symbol] = explanation
                    elif current_side == 'Union':
                        union_footnotes[symbol] = explanation
                    continue
                
                # Try to parse as unit row
                if current_side:
                    unit = self._parse_unit_line(line_stripped, current_side)
                    if unit:
                        if current_side == 'Confederate':
                            scenario.confederate_units.append(unit)
                        else:
                            scenario.union_units.append(unit)
            
            # Stop parsing if we've hit the next scenario
            if stop_parsing:
                break
        
        scenario.confederate_footnotes = confederate_footnotes
        scenario.union_footnotes = union_footnotes
        return scenario
    
    def _parse_unit_line(self, line: str, side: str) -> Optional[Unit]:
        """Parse a single line as a unit entry."""
        parts = line.split()
        
        if len(parts) < 4:
            return None
        
        # Handle special units first (Gunboat, Wagon Train, Naval Battery)
        # These have format: "Name - - - - Location" or similar
        # Valid patterns: "Gunboat-1", "Gunboat-2", "Naval Battery", "Wagon Train-A"
        # Skip lines that are clearly rules text (lowercase "gunboat" in explanatory text)
        first_part = parts[0].lower()
        
        # More specific check for valid special unit names
        # Gunboat must start with uppercase G (to avoid "gunboat" in rules text)
        is_gunboat = re.match(r'^Gunboat-?\d*$', parts[0]) is not None
        is_naval = first_part == 'naval' and len(parts) > 1 and parts[1].lower() == 'battery'
        is_wagon = first_part == 'wagon' and len(parts) > 1 and parts[1].lower().startswith('train')
        
        # Also accept parenthesized gunboat like "(Gunboat-2)"
        is_paren_gunboat = parts[0].startswith('(Gunboat')
        
        if is_gunboat or is_naval or is_wagon or is_paren_gunboat:
            # Special unit - parse differently
            unit_name = parts[0]
            if parts[0].lower() == 'wagon' and len(parts) > 1:
                unit_name = f"{parts[0]} {parts[1]}"  # "Wagon Train-A"
            elif parts[0].lower() == 'naval' and len(parts) > 1:
                unit_name = f"{parts[0]} {parts[1]}"  # "Naval Battery"
            
            # For special units, find location after the dashes
            # Expected format: "Gunboat-1 - - - - Location" or "Naval Battery - - - Location"
            # Find the last dash and take everything after it as location
            dash_indices = [i for i, p in enumerate(parts) if p == '-']
            if dash_indices:
                last_dash = dash_indices[-1]
                hex_location = ' '.join(parts[last_dash + 1:])
            else:
                # No dashes - look for hex pattern or box/river keywords
                hex_location = ''
                for i, p in enumerate(parts):
                    if re.match(r'^[NS]\d{4}', p) or 'Box' in p or 'River' in p or 'Display' in p or 'Reinforcement' in p:
                        hex_location = ' '.join(parts[i:])
                        break
            
            # Sanity check: if hex_location is too long, it's probably rules text
            if len(hex_location) > 60:
                hex_location = ''
            
            return Unit(
                unit_leader=unit_name,
                size='-',
                command='-',
                unit_type='Special',
                manpower_value='-',
                hex_location=hex_location,
                side=side,
                notes=[]
            )
        
        # Find the size column for regular units
        size_idx = None
        size_value = None
        
        for i, part in enumerate(parts):
            # Check for Demi-Div which might appear as one token or as D-Div
            if part == 'Demi-Div' or part == 'D-Div':
                size_idx = i
                size_value = 'Demi-Div'  # Normalize D-Div to Demi-Div
                break
            elif part in self.VALID_SIZES:
                size_idx = i
                size_value = part
                break
        
        if size_idx is None:
            return None
        
        # Parse the fields relative to size position
        name_parts = parts[:size_idx]
        
        # HSN has an extra "Set" column (reinforcement arrival turn) between name and size
        # Strip the trailing number if it's a standalone digit (1-9)
        if self.game_id == "hsn" and name_parts and re.match(r'^\d$', name_parts[-1]):
            name_parts = name_parts[:-1]
        
        # RTG2 has "Wagon Train" special units that appear in tables as "Wagon Train 1", "Wagon Train 2", etc.
        # Strip the trailing number for these units
        if self.game_id == "rtg2" and len(name_parts) >= 2 and name_parts[0] == "Wagon" and name_parts[1] == "Train" and re.match(r'^\d$', name_parts[-1]):
            name_parts = name_parts[:-1]
        
        unit_name = ' '.join(name_parts)
        
        # Remaining parts after size
        remaining = parts[size_idx + 1:]
        
        if len(remaining) < 3:
            return None
        
        command = remaining[0]
        unit_type = remaining[1]
        manpower = remaining[2]
        hex_location = ' '.join(remaining[3:]) if len(remaining) > 3 else ''
        
        # Validate unit type
        if unit_type not in self.VALID_TYPES:
            return None
        
        # Extract footnote markers from unit name and manpower (including $ marker)
        note_markers = set()  # Use set to avoid duplicates
        for marker in ['*', '^', '†', '‡', '§', '$', '+']:
            if marker in unit_name:
                note_markers.add(marker)
                unit_name = unit_name.replace(marker, '')
            if marker in manpower:
                note_markers.add(marker)
        
        return Unit(
            unit_leader=unit_name.strip(),
            size=size_value,
            command=command,
            unit_type=unit_type,
            manpower_value=manpower,
            hex_location=hex_location,
            side=side,
            notes=sorted(list(note_markers))  # Convert back to sorted list
        )
    
    def _extract_notes(self, text: str) -> str:
        """Extract the NOTES section from scenario text."""
        match = re.search(r'NOTES?:\s*(.+?)(?=MAP:|GAME LENGTH:|SPECIAL RULES:|$)', 
                          text, re.IGNORECASE | re.DOTALL)
        if match:
            return ' '.join(match.group(1).split())[:500]  # Limit length
        return ""
    
    def _extract_map_info(self, text: str) -> str:
        """Extract MAP information."""
        match = re.search(r'MAP:\s*(.+?)(?=GAME LENGTH:|SPECIAL RULES:|NOTES:|$)', 
                          text, re.IGNORECASE | re.DOTALL)
        if match:
            return ' '.join(match.group(1).split())[:200]
        return ""
    
    def _extract_game_length(self, text: str) -> str:
        """Extract GAME LENGTH information."""
        match = re.search(r'GAME LENGTH:\s*(.+?)(?=SPECIAL RULES:|MAP:|NOTES:|$)', 
                          text, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            # Get just the first line
            first_line = result.split('\n')[0].strip()
            # Extract just the turns and date part (ends with year like 1864.)
            # Pattern: "X turns; Month Day to Month Day, Year." or "X turn, Month Day, Year."
            # Also handle en-dash (–) between dates
            date_match = re.match(r'^:?\s*(\d+\s+turns?[;,]\s+\w+\s+\d+(?:[\s–-]+(?:to\s+)?\w+\s+\d+)?,\s+\d{4})\.?', first_line)
            if date_match:
                return date_match.group(1) + "."
            # Fallback: just get everything up to and including the first "1864." or similar year
            # But stop at the period after the year to avoid merged text
            year_match = re.match(r'^:?\s*(.+?\d{4})\.?', first_line)
            if year_match:
                extracted = year_match.group(1).lstrip(': ')
                # Sanity check: if result is too long, likely includes merged text
                if len(extracted) > 60:
                    # Try to find just the date portion before any lowercase word starts
                    short_match = re.match(r'^:?\s*(\d+\s+turns?[;,][^a-z]+\d{4})', first_line)
                    if short_match:
                        return short_match.group(1).strip() + "."
                return extracted + "."
            return first_line
        return ""
    
    def _extract_special_rules(self, text: str) -> list[str]:
        """Extract SPECIAL RULES as a list."""
        match = re.search(r'SPECIAL RULES:\s*(.+?)(?=confederate set-up|union set-up|$)', 
                          text, re.IGNORECASE | re.DOTALL)
        if match:
            rules_text = match.group(1)
            # Split by numbered items
            rules = re.split(r'\n\s*\d+\.', rules_text)
            return [' '.join(r.split())[:300] for r in rules if r.strip()][:10]
        return []
    
    def to_json(self) -> str:
        """Convert all scenarios to JSON."""
        def serialize(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            return str(obj)
        
        return json.dumps([asdict(s) for s in self.scenarios], indent=2, default=serialize)


def main():
    import sys
    
    # Accept PDF path, game_id, and optional page range as arguments
    # Usage: python scenario_parser.py [pdf_path] [game_id] [start_page] [end_page]
    # game_id: "otr2" (default), "gtc2", "rtw", etc.
    # Page range is optional - if not provided, uses PAGE_RANGES config or entire PDF
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "../data/OTR2_Rules.pdf"
    
    # Determine game_id from argument or infer from filename
    if len(sys.argv) > 2:
        game_id = sys.argv[2]
    elif "GTC2" in pdf_path.upper():
        game_id = "gtc2"
    else:
        game_id = "otr2"
    
    # Parse optional page range
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else None
    end_page = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Set output filename based on game_id
    output_json = f"{game_id}_scenarios.json" if game_id != "otr2" else "all_scenarios.json"
    
    page_info = ""
    if start_page:
        page_info = f", pages {start_page}-{end_page or 'end'}"
    elif game_id in ScenarioParser.PAGE_RANGES:
        r = ScenarioParser.PAGE_RANGES[game_id]
        page_info = f", pages {r[0]}-{r[1]} (from config)"
    
    print(f"Parsing: {pdf_path} (game: {game_id}{page_info})")
    parser = ScenarioParser(pdf_path, game_id, start_page, end_page)
    scenarios = parser.parse()
    
    print(f"Found {len(scenarios)} scenarios\n")
    print("=" * 70)
    
    for scenario in scenarios:
        print(f"\nScenario {scenario.number}: {scenario.name}")
        print(f"  Start page: {scenario.start_page}")
        print(f"  Game length: {scenario.game_length}")
        print(f"  Map: {scenario.map_info[:60]}..." if len(scenario.map_info) > 60 else f"  Map: {scenario.map_info}")
        print(f"  Confederate units: {len(scenario.confederate_units)}")
        print(f"  Union units: {len(scenario.union_units)}")
        if scenario.confederate_footnotes:
            print(f"  Confederate footnotes: {scenario.confederate_footnotes}")
        if scenario.union_footnotes:
            print(f"  Union footnotes: {scenario.union_footnotes}")
    
    # Export JSON
    with open(output_json, 'w') as f:
        f.write(parser.to_json())
    print(f"\nExported scenario data to {output_json}")
    
    # Show sample units from first scenario
    print("\n" + "=" * 70)
    print("Sample units from Scenario 1:")
    print("=" * 70)
    if scenarios:
        for unit in scenarios[0].confederate_units[:5]:
            print(f"  {unit.unit_leader:15} {unit.size:10} {unit.command:5} {unit.unit_type:4} {unit.manpower_value:5} {unit.hex_location}")


if __name__ == "__main__":
    main()
