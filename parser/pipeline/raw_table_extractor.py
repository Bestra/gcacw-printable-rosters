"""
Raw Table Extractor for GCACW Scenario PDFs

Extracts raw table data from PDFs and saves it in an intermediate format
that preserves:
- Table names/headers
- Page numbers
- Raw row values
- Table annotations/footnotes
- Per-side table groupings

This intermediate format is useful for debugging PDF extraction issues
and for manually reviewing how tables are parsed before unit conversion.
"""

import pdfplumber
import re
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Directory containing this script's parent (the parser directory)
PARSER_DIR = Path(__file__).parent.parent


@dataclass
class RawTableRow:
    """A single row from a setup table."""
    values: list[str]  # Raw cell values from the row
    

@dataclass
class RawTable:
    """A raw table extracted from the PDF."""
    name: str  # Table header name (e.g., "Union Set-Up", "Army Of The Potomac First Increment")
    page_numbers: list[int]  # Pages where this table appears (1-indexed)
    header_row: list[str]  # Column headers (e.g., ["Unit/Leader", "Size", "Command", ...])
    rows: list[list[str]] = field(default_factory=list)  # Raw row data
    annotations: dict[str, str] = field(default_factory=dict)  # Footnote symbols -> explanations


@dataclass
class RawScenarioTables:
    """All raw tables for a single scenario."""
    scenario_number: int
    scenario_name: str
    start_page: int  # First page of the scenario (1-indexed)
    end_page: int  # Last page of the scenario (1-indexed)
    advanced_game_rules_page: Optional[int] = None  # Page where advanced rules start (1-indexed)
    confederate_tables: list[RawTable] = field(default_factory=list)
    union_tables: list[RawTable] = field(default_factory=list)


class RawTableExtractor:
    """Extracts raw tables from GCACW scenario PDFs."""
    
    # Table header patterns - matches table section names
    # These patterns should match ONLY lines that are clearly table headers,
    # not lines that happen to contain these phrases in rules text.
    # We require the pattern to match at the START of the line (after leading whitespace).
    TABLE_HEADER_PATTERNS = [
        # Primary setup tables - must start at line beginning
        # Note: "Unon" is a typo for "Union" that appears in GTC2 PDF
        r'^(?:confederate|union|unon)\s+set-up',
        # Increment tables (RTG2 campaign scenarios)
        r'^army\s+of\s+(?:the\s+)?potomac\s+(?:first|second|third)\s+increment',
        r'^army\s+of\s+northern\s+virginia\s+(?:first|second|third)\s+increment',
        # Reinforcement tracks - must start at line beginning
        r'^(?:west\s+virginia|baltimore(?:/dc)?|pennsylvania\s+militia|confederate)\s+reinforcement\s+track',
        # Richmond garrison track - must start at line beginning
        r'^richmond\s+garrison\s+(?:track|reinforcement)',
        # Stuart's arrival (RTG2) - must start at line beginning
        # Note: PDF may use curly apostrophe (U+2019) instead of straight (')
        r"^placed\s+upon\s+stuart['\u2019]?s\s+arrival",
    ]
    
    # Page ranges for games that share a PDF (1-indexed, inclusive)
    PAGE_RANGES = {
        "hcr": (1, 44),
        "rtg2": (45, 95),
        "rwh": (96, 116),
    }
    
    # Known scenario names by game (from scenario_parser.py)
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
        "rwh": {
            1: "Monocacy",
            2: "Fort Stevens",
            3: "The Retreat From Washington",
            4: "From Winchester to Washington",
        },
        "tom": {
            1: "The Battle of Port Gibson",
            2: "Invasion and Breakout",
            3: "Unite Your Troops",
            4: "Yankee Blitzkrieg",
            5: "Loring's Memorandum",
            6: "Grant Moves West",
            7: "Champion Hill",
            8: "I Move At Once",
            9: "This Is Success",
            10: "Army of Relief",
            11: "Inflict All the Punishment You Can",
            12: "Starting and Ending the Game",
        },
        "tpc": {
            1: "My Best Achievement",
            2: "Battle of Jerusalem Plank Road",
            3: "Sheridan Crosses the James",
            4: "The Crater",
            5: "The Fourth Offensive",
            6: "The Fifth Offensive",
            7: "Burgess Mill",
            8: "Hatcher's Run",
            9: "Five Forks",
            10: "Retreat to Appomattox",
            11: "The Petersburg Campaign",
            12: "The Last Offensive",
        },
    }
    
    def __init__(self, pdf_path: str, game_id: str = "otr2", start_page: int = None, end_page: int = None):
        self.pdf_path = pdf_path
        self.game_id = game_id
        self.scenarios: list[RawScenarioTables] = []
        self.unknown_symbols: set[str] = set()  # Track symbols we don't recognize
        
        # Load footnote symbols from game_configs.json (in parent directory)
        config_path = os.path.join(os.path.dirname(__file__), '..', 'game_configs.json')
        with open(config_path) as f:
            config = json.load(f)
            self.known_footnote_symbols = set(config['defaults']['footnote_symbols'])
            # Build regex character class from symbols (escape special regex chars)
            escaped_symbols = [re.escape(s) for s in self.known_footnote_symbols]
            self.footnote_regex = re.compile(r'^([' + ''.join(escaped_symbols) + r']+)\s+(.+)$')
        
        # Use provided page range, or look up from PAGE_RANGES, or use entire PDF
        if start_page is not None:
            self.start_page = start_page - 1  # Convert to 0-indexed
            self.end_page = end_page if end_page else None
        elif game_id in self.PAGE_RANGES:
            range_start, range_end = self.PAGE_RANGES[game_id]
            self.start_page = range_start - 1
            self.end_page = range_end
        else:
            self.start_page = 0
            self.end_page = None
            
    def extract(self) -> list[RawScenarioTables]:
        """Extract raw tables from all scenarios in the PDF."""
        with pdfplumber.open(self.pdf_path) as pdf:
            if self.end_page is None:
                self.end_page = len(pdf.pages)
            
            # Find all scenario start pages
            scenario_pages = self._find_scenario_pages(pdf)
            
            # Extract tables for each scenario
            for i, (page_num, scenario_num, scenario_name) in enumerate(scenario_pages):
                # Determine end page for this scenario
                if i + 1 < len(scenario_pages):
                    scenario_end = scenario_pages[i + 1][0]
                else:
                    scenario_end = self.end_page
                
                raw_scenario = self._extract_scenario_tables(
                    pdf, page_num, scenario_end, scenario_num, scenario_name
                )
                self.scenarios.append(raw_scenario)
        
        return self.scenarios
    
    def _find_scenario_pages(self, pdf) -> list[tuple[int, int, str]]:
        """Find all scenario header pages. Returns [(page_num, scenario_num, name), ...]"""
        # Pattern to capture scenario number and name after the colon
        scenario_pattern = re.compile(r'scenario\s+(\d+):\s*(.+?)(?:\s{2,}|$)', re.IGNORECASE)
        known_names = self.SCENARIO_NAMES.get(self.game_id, {})
        
        results = []
        seen_scenarios = set()
        
        for i in range(self.start_page, min(self.end_page, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            if not text:
                continue
            
            # Skip actual TOC pages (which list multiple scenarios as links/references)
            text_lower = text.lower()
            if 'table of contents' in text_lower:
                continue
                
            for line in text.split('\n'):
                match = scenario_pattern.search(line)
                if match:
                    # Skip TOC-style lines that have dots or page numbers after scenario name
                    # e.g., "Scenario 1: The Warwick Line .......4"
                    if re.search(r'\.{2,}', line):  # Multiple dots = TOC entry
                        continue
                    
                    scenario_num = int(match.group(1))
                    if scenario_num in seen_scenarios:
                        continue
                    seen_scenarios.add(scenario_num)
                    
                    # Try to extract scenario name from the PDF text
                    extracted_name = match.group(2).strip() if len(match.groups()) > 1 else ""
                    # Clean up extracted name (remove trailing content, split on multiple spaces)
                    if extracted_name:
                        extracted_name = extracted_name.split('...')[0].strip()
                        # Proper title case the name
                        extracted_name = extracted_name.title()
                    
                    # Use extracted name if valid, otherwise fall back to known names, then generic
                    if extracted_name and len(extracted_name) > 3:  # Minimum reasonable name length
                        scenario_name = extracted_name
                    else:
                        scenario_name = known_names.get(scenario_num, f"Scenario {scenario_num}")
                    
                    results.append((i, scenario_num, scenario_name))
                    break
        
        return results
    
    def _extract_scenario_tables(self, pdf, start_page: int, end_page: int,
                                  scenario_num: int, scenario_name: str) -> RawScenarioTables:
        """Extract all raw tables from a single scenario."""
        raw_scenario = RawScenarioTables(
            scenario_number=scenario_num,
            scenario_name=scenario_name,
            start_page=start_page + 1,  # Convert to 1-indexed
            end_page=end_page
        )
        
        current_side = None  # 'Confederate' or 'Union'
        current_table = None
        found_scenario_header = False
        
        # Extend to catch continuation tables
        actual_end = min(end_page + 1, len(pdf.pages))
        
        for page_idx in range(start_page, actual_end):
            page = pdf.pages[page_idx]
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            stop_parsing = False
            
            for line in lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # On start page, find our scenario header first
                if page_idx == start_page and not found_scenario_header:
                    if re.search(rf'scenario\s+{scenario_num}:', line_lower):
                        found_scenario_header = True
                    continue
                
                # Stop at next scenario
                scenario_match = re.search(r'scenario\s+(\d+):', line_lower)
                if scenario_match:
                    next_num = int(scenario_match.group(1))
                    if next_num != scenario_num:
                        stop_parsing = True
                        break
                
                # Stop at Advanced Game Rules section header
                # These patterns match the actual section headers, not just mentions in text
                # We need to avoid false positives like "Advanced Game rules (see 17.2) apply..."
                is_advanced_game_section_header = (
                    # Numbered section header like "1.0 advanced Game sequence of play"
                    re.match(r'^\d+\.\d*\s+advanced\s+game', line_lower) or
                    # Line starts with "advanced game rules" as a section title
                    # Exclude lines that are references like "Advanced Game rules (see X.X) apply"
                    (re.match(r'^advanced\s+game\s+rules\b', line_lower) and 
                     not re.search(r'\(see\s+\d+', line_lower) and
                     'apply' not in line_lower) or
                    # The intro line for the advanced rules section
                    re.match(r'^the following rules are used only in advanced game', line_lower)
                )
                if is_advanced_game_section_header:
                    # Record the page where advanced rules start
                    raw_scenario.advanced_game_rules_page = page_idx + 1  # 1-indexed
                    stop_parsing = True
                    break
                
                # Check for table headers
                table_header = self._match_table_header(line_lower, line_stripped)
                if table_header:
                    # Save previous table if exists
                    if current_table:
                        self._add_table_to_scenario(raw_scenario, current_table, current_side)
                    
                    # Determine side from header
                    new_side = self._determine_side(table_header)
                    if new_side:
                        current_side = new_side
                    
                    # Start new table
                    current_table = RawTable(
                        name=table_header,
                        page_numbers=[page_idx + 1],  # 1-indexed
                        header_row=[]
                    )
                    continue
                
                # Check for column header row
                if 'unit/leader' in line_lower or 'unIt/leader' in line_lower:
                    if current_table:
                        current_table.header_row = self._parse_header_row(line_stripped)
                        # Track page if different
                        if page_idx + 1 not in current_table.page_numbers:
                            current_table.page_numbers.append(page_idx + 1)
                    continue
                
                # Check for footnotes
                footnote_match = self.footnote_regex.match(line_stripped)
                if footnote_match:
                    symbol = footnote_match.group(1)
                    explanation = footnote_match.group(2)
                    if current_table:
                        current_table.annotations[symbol] = explanation
                        # Check for unknown symbols
                        for char in symbol:
                            if char not in self.known_footnote_symbols:
                                self.unknown_symbols.add(char)
                    continue
                
                # Try to parse as data row
                if current_table:
                    row_data = self._parse_data_row(line_stripped)
                    if row_data:
                        current_table.rows.append(row_data)
                        # Track page for multi-page tables
                        if page_idx + 1 not in current_table.page_numbers:
                            current_table.page_numbers.append(page_idx + 1)
            
            if stop_parsing:
                break
        
        # Save final table
        if current_table:
            self._add_table_to_scenario(raw_scenario, current_table, current_side)
        
        return raw_scenario
    
    def _match_table_header(self, line_lower: str, line_original: str) -> Optional[str]:
        """Check if a line is a table header. Returns the cleaned header name or None."""
        # Skip (cntd) continuation markers - these are part of the same table
        if '(cntd)' in line_lower:
            return None
        
        # Skip lines that are clearly too long to be table headers (likely rules text)
        if len(line_lower) > 80:
            return None
        
        for pattern in self.TABLE_HEADER_PATTERNS:
            # Use re.match since patterns start with ^ (match at string start)
            if re.match(pattern, line_lower):
                # Return a cleaned version of the header
                return self._clean_header(line_original)
        
        return None
    
    def _clean_header(self, header: str) -> str:
        """Clean up a table header string."""
        # Remove extra whitespace and normalize
        header = ' '.join(header.split())
        # Fix common typos
        header = re.sub(r'\bUnon\b', 'Union', header, flags=re.IGNORECASE)
        
        # Truncate at patterns that indicate merged text from adjacent columns
        # (e.g., victory conditions merged with table headers)
        stop_patterns = [
            r'\s+\d+\s+or\s+(?:less|more)',  # "1 or less", "10 or more"
            r'\s+(?:decisive|substantive|marginal)\s+victory',  # victory conditions
        ]
        for pattern in stop_patterns:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                header = header[:match.start()].strip()
        
        # Capitalize properly
        return header.title()
    
    def _determine_side(self, header: str) -> Optional[str]:
        """Determine which side (Confederate/Union) a table belongs to."""
        header_lower = header.lower()
        
        # Explicit side markers (note: "unon" is a typo for "union" in GTC2)
        if 'confederate' in header_lower:
            return 'Confederate'
        if 'union' in header_lower or 'unon' in header_lower:
            return 'Union'
        
        # Army-specific markers
        if 'potomac' in header_lower:  # Army of the Potomac
            return 'Union'
        if 'northern virginia' in header_lower:  # Army of Northern Virginia
            return 'Confederate'
        
        # Location-based markers
        union_locations = ['baltimore', 'dc', 'pennsylvania', 'west virginia']
        for loc in union_locations:
            if loc in header_lower:
                return 'Union'
        
        # Stuart and Richmond are Confederate
        if 'stuart' in header_lower or 'richmond' in header_lower:
            return 'Confederate'
        
        return None
    
    def _add_table_to_scenario(self, scenario: RawScenarioTables, 
                                table: RawTable, side: Optional[str]):
        """Add a table to the appropriate side in the scenario."""
        if side == 'Confederate':
            scenario.confederate_tables.append(table)
        elif side == 'Union':
            scenario.union_tables.append(table)
        else:
            # Default to Confederate if we can't determine
            # (shouldn't happen with proper header matching)
            scenario.confederate_tables.append(table)
    
    def _parse_header_row(self, line: str) -> list[str]:
        """Parse a column header row into individual headers."""
        parts = line.split()
        headers = []
        
        i = 0
        while i < len(parts):
            # Handle multi-word headers
            if parts[i].lower() in ['unit/leader', 'unIt/leader']:
                headers.append('Unit/Leader')
            elif parts[i].lower() == 'manpower' and i + 1 < len(parts) and parts[i + 1].lower() == 'value':
                headers.append('Manpower Value')
                i += 1
            elif parts[i].lower() == 'reinforcement' and i + 1 < len(parts) and parts[i + 1].lower() == 'set':
                headers.append('Reinforcement Set #')
                # Skip "set" and "#" if present
                i += 1
                if i + 1 < len(parts) and parts[i + 1] == '#':
                    i += 1
            else:
                headers.append(parts[i].title())
            i += 1
        
        return headers
    
    def _parse_data_row(self, line: str) -> Optional[list[str]]:
        """Parse a data row into cell values. Returns None if not a valid data row."""
        parts = line.split()
        
        if len(parts) < 4:
            return None
        
        # Valid unit sizes and types
        valid_sizes = ['Army', 'District', 'Corps', 'Demi-Div', 'D-Div', 'Div', 'Brig', 'Regt']
        valid_types = ['Ldr', 'Inf', 'Cav', 'Art']
        
        # Check for special units (Gunboat, Wagon Train, Naval Battery)
        # These should have dashes (-) in the line for missing stat columns
        # or a clear hex pattern (S/N followed by 4 digits)
        first_lower = parts[0].lower()
        is_special_unit_name = (
            first_lower.startswith('gunboat') or
            first_lower.startswith('(gunboat') or
            first_lower == 'wagon' or
            first_lower == 'naval'
        )
        if is_special_unit_name:
            # Verify it looks like a table row, not prose text
            # Table rows for special units have dashes or hex patterns
            has_dash = '-' in parts
            has_hex = any(re.match(r'^[SN]\d{4}', p) for p in parts)
            if has_dash or has_hex:
                return parts
            # Otherwise this is likely prose mentioning a location name
            return None
        
        # For regular unit rows, the size should be in position 1-4 (after the unit name)
        # The unit name is typically 1-3 parts, so size should be found early
        size_idx = None
        for i, part in enumerate(parts[:6]):  # Only check first 6 tokens
            if part in valid_sizes:
                size_idx = i
                break
        
        if size_idx is None:
            return None
        
        # After size, we should have command (1-3 chars), type, and manpower
        remaining = parts[size_idx + 1:]
        if len(remaining) < 3:
            return None
        
        # The type should be in position 1 or 2 after size
        has_valid_type = remaining[1] in valid_types if len(remaining) > 1 else False
        
        if not has_valid_type:
            return None
        
        return parts
    
    def to_json(self, indent: int = 2) -> str:
        """Convert all scenarios to JSON."""
        def to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            return str(obj)
        
        return json.dumps(
            [asdict(s) for s in self.scenarios],
            indent=indent,
            default=to_dict
        )
    
    def to_json_file(self, output_path: str):
        """Save raw tables to a JSON file."""
        with open(output_path, 'w') as f:
            f.write(self.to_json())


def get_pdf_path(game_id: str) -> str:
    """
    Get the PDF path for a game from environment variables.
    
    Environment variable naming: {GAME_CODE}_RULES_PATH (e.g., GTC2_RULES_PATH)
    
    Raises:
        ValueError: If environment variable is not set
    """
    env_var = f"{game_id.upper()}_RULES_PATH"
    pdf_path = os.getenv(env_var)
    
    if not pdf_path:
        raise ValueError(
            f"Environment variable {env_var} not set.\n"
            f"Please set it in parser/.env:\n"
            f"  {env_var}=~/path/to/{game_id.upper()}_Rules.pdf"
        )
    
    return pdf_path


def main():
    import sys
    
    # Usage: python pipeline/raw_table_extractor.py [pdf_path] [game_id] [start_page] [end_page]
    # If game_id is provided but not pdf_path, we'll auto-detect the PDF path
    if len(sys.argv) > 2:
        # Both pdf_path and game_id provided
        pdf_path = sys.argv[1]
        game_id = sys.argv[2]
    elif len(sys.argv) > 1:
        # Only one arg - treat as game_id and auto-detect PDF path
        game_id = sys.argv[1]
        pdf_path = get_pdf_path(game_id)
    else:
        # No args - use defaults
        game_id = "rtg2"
        pdf_path = get_pdf_path(game_id)
    
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else None
    end_page = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    raw_dir = PARSER_DIR / "raw"
    raw_dir.mkdir(exist_ok=True)
    output_json = raw_dir / f"{game_id}_raw_tables.json"
    
    page_info = ""
    if start_page:
        page_info = f", pages {start_page}-{end_page or 'end'}"
    elif game_id in RawTableExtractor.PAGE_RANGES:
        r = RawTableExtractor.PAGE_RANGES[game_id]
        page_info = f", pages {r[0]}-{r[1]} (from config)"
    
    print(f"Extracting raw tables from: {pdf_path} (game: {game_id}{page_info})")
    extractor = RawTableExtractor(pdf_path, game_id, start_page, end_page)
    scenarios = extractor.extract()
    
    print(f"\nFound {len(scenarios)} scenarios\n")
    print("=" * 70)
    
    for scenario in scenarios:
        print(f"\nScenario {scenario.scenario_number}: {scenario.scenario_name}")
        print(f"  Pages: {scenario.start_page}-{scenario.end_page}")
        if scenario.advanced_game_rules_page:
            print(f"  Advanced Game Rules start: page {scenario.advanced_game_rules_page}")
        print(f"  Confederate tables: {len(scenario.confederate_tables)}")
        for table in scenario.confederate_tables:
            row_count = len(table.rows)
            pages = ', '.join(map(str, table.page_numbers))
            print(f"    - {table.name} ({row_count} rows, pages: {pages})")
            if table.annotations:
                print(f"      Annotations: {list(table.annotations.keys())}")
        
        print(f"  Union tables: {len(scenario.union_tables)}")
        for table in scenario.union_tables:
            row_count = len(table.rows)
            pages = ', '.join(map(str, table.page_numbers))
            print(f"    - {table.name} ({row_count} rows, pages: {pages})")
            if table.annotations:
                print(f"      Annotations: {list(table.annotations.keys())}")
    
    # Export JSON
    extractor.to_json_file(output_json)
    print(f"\nExported raw table data to {output_json}")
    
    # Report any unknown footnote symbols
    if extractor.unknown_symbols:
        print(f"\n⚠️  WARNING: Found unknown footnote symbols: {sorted(extractor.unknown_symbols)}")
        print("   These symbols are not in game_configs.json footnote_symbols and may not be parsed correctly.")
        print("   Consider adding them to the defaults.footnote_symbols array.")


if __name__ == "__main__":
    main()
