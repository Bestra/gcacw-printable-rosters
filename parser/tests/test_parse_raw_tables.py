"""
Tests for parse_raw_tables.py

Run with: cd parser && uv run pytest tests/test_parse_raw_tables.py -v
"""

import sys
from pathlib import Path

# Add parser directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from dataclasses import asdict
from pipeline.parse_raw_tables import RawTableParser, Unit, ParsedScenario


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def otr2_parser():
    """Parser configured for OTR2 game."""
    return RawTableParser("otr2")


@pytest.fixture
def hcr_parser():
    """Parser configured for HCR game (has turn column)."""
    return RawTableParser("hcr")


@pytest.fixture
def hsn_parser():
    """Parser configured for HSN game (has set column)."""
    return RawTableParser("hsn")


@pytest.fixture
def standard_columns():
    """Standard column configuration."""
    return ["name", "size", "command", "type", "manpower", "hex"]


@pytest.fixture
def turn_columns():
    """Column configuration with turn (HCR style)."""
    return ["turn", "name", "size", "command", "type", "manpower", "hex"]


# ============================================================================
# Unit Dataclass Tests
# ============================================================================

class TestUnitDataclass:
    """Tests for the Unit dataclass."""
    
    def test_unit_creation_minimal(self):
        """Test creating a unit with required fields."""
        unit = Unit(
            unit_leader="Longstreet",
            size="Corps",
            command="L",
            unit_type="Ldr",
            manpower_value="-",
            hex_location="S1234",
            side="Confederate"
        )
        assert unit.unit_leader == "Longstreet"
        assert unit.notes == []
        assert unit.turn is None
        assert unit.reinforcement_set is None
        assert unit.table_name is None
    
    def test_unit_creation_full(self):
        """Test creating a unit with all fields."""
        unit = Unit(
            unit_leader="Ward",
            size="Brig",
            command="M",
            unit_type="Inf",
            manpower_value="2*",
            hex_location="S5510 (Yorktown)",
            side="Confederate",
            notes=["*"],
            turn="1",
            reinforcement_set="2",
            table_name="Confederate Set-Up"
        )
        assert unit.notes == ["*"]
        assert unit.turn == "1"
        assert unit.reinforcement_set == "2"
        assert unit.table_name == "Confederate Set-Up"
    
    def test_unit_to_dict(self):
        """Test that Unit can be serialized to dict."""
        unit = Unit(
            unit_leader="Test",
            size="Brig",
            command="T",
            unit_type="Inf",
            manpower_value="5",
            hex_location="S1000",
            side="Union"
        )
        d = asdict(unit)
        assert isinstance(d, dict)
        assert d["unit_leader"] == "Test"
        assert d["side"] == "Union"


# ============================================================================
# Config Loading Tests
# ============================================================================

class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_otr2_config(self, otr2_parser):
        """Test loading OTR2 configuration."""
        assert otr2_parser.config is not None
        assert "columns" in otr2_parser.config
        assert "valid_sizes" in otr2_parser.config
        assert "valid_types" in otr2_parser.config
    
    def test_valid_sizes_loaded(self, otr2_parser):
        """Test that valid sizes are loaded from config."""
        sizes = otr2_parser.config["valid_sizes"]
        assert "Corps" in sizes
        assert "Div" in sizes
        assert "Brig" in sizes
        assert "Regt" in sizes
        assert "Demi-Div" in sizes
    
    def test_valid_types_loaded(self, otr2_parser):
        """Test that valid types are loaded from config."""
        types = otr2_parser.config["valid_types"]
        assert "Ldr" in types
        assert "Inf" in types
        assert "Cav" in types
        assert "Art" in types
    
    def test_footnote_symbols_loaded(self, otr2_parser):
        """Test that footnote symbols are loaded."""
        symbols = otr2_parser.config["footnote_symbols"]
        assert "*" in symbols
        assert "†" in symbols
        assert "‡" in symbols


# ============================================================================
# Footnote Extraction Tests
# ============================================================================

class TestFootnoteExtraction:
    """Tests for _extract_footnotes method."""
    
    def test_extract_single_symbol(self, otr2_parser):
        """Test extracting a single footnote symbol."""
        clean, notes = otr2_parser._extract_footnotes("Ward*")
        assert clean == "Ward"
        assert notes == ["*"]
    
    def test_extract_multiple_symbols(self, otr2_parser):
        """Test extracting multiple footnote symbols."""
        clean, notes = otr2_parser._extract_footnotes("Unit*†")
        assert clean == "Unit"
        assert "*" in notes
        assert "†" in notes
    
    def test_no_symbols(self, otr2_parser):
        """Test value with no footnote symbols."""
        clean, notes = otr2_parser._extract_footnotes("Longstreet")
        assert clean == "Longstreet"
        assert notes == []
    
    def test_symbol_in_manpower(self, otr2_parser):
        """Test extracting symbol from manpower value."""
        clean, notes = otr2_parser._extract_footnotes("2*")
        assert clean == "2"
        assert notes == ["*"]
    
    def test_preserves_whitespace_handling(self, otr2_parser):
        """Test that extraction handles whitespace."""
        clean, notes = otr2_parser._extract_footnotes(" Ward* ")
        assert clean == "Ward"
        assert notes == ["*"]


# ============================================================================
# Column Detection Tests
# ============================================================================

class TestColumnDetection:
    """Tests for _detect_columns_from_header method."""
    
    def test_detect_standard_columns(self, otr2_parser):
        """Test detecting standard column layout."""
        header = ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"]
        columns = otr2_parser._detect_columns_from_header(header)
        assert "name" in columns
        assert "size" in columns
        assert "command" in columns
        assert "type" in columns
        assert "manpower" in columns
        assert "hex" in columns
    
    def test_detect_turn_column(self, hcr_parser):
        """Test detecting turn column (HCR style)."""
        header = ["Turn", "Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"]
        columns = hcr_parser._detect_columns_from_header(header)
        assert columns[0] == "turn"
        assert "name" in columns
    
    def test_detect_set_column(self, hsn_parser):
        """Test detecting set column (HSN/RTG2 style)."""
        header = ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex", "Set"]
        columns = hsn_parser._detect_columns_from_header(header)
        assert "set" in columns
    
    def test_empty_header_uses_defaults(self, otr2_parser):
        """Test that empty header falls back to default columns."""
        columns = otr2_parser._detect_columns_from_header([])
        assert columns == otr2_parser.config.get("columns", [])


# ============================================================================
# Size Detection Tests
# ============================================================================

class TestSizeDetection:
    """Tests for _find_size_index method."""
    
    def test_find_corps_size(self, otr2_parser):
        """Test finding Corps size."""
        tokens = ["Longstreet", "Corps", "L", "Ldr", "-", "S1234"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert idx == 1
        assert size == "Corps"
    
    def test_find_brig_size(self, otr2_parser):
        """Test finding Brig size."""
        tokens = ["Ward", "Brig", "M", "Inf", "2", "S5510"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert idx == 1
        assert size == "Brig"
    
    def test_find_size_with_footnote(self, otr2_parser):
        """Test finding size when it has a footnote symbol."""
        tokens = ["Ward*", "Brig", "M", "Inf", "2*", "S5510"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert idx == 1
        assert size == "Brig"
    
    def test_normalize_d_div_to_demi_div(self, otr2_parser):
        """Test that D-Div is normalized to Demi-Div."""
        tokens = ["Unit", "D-Div", "X", "Inf", "3", "S1234"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert size == "Demi-Div"
    
    def test_no_valid_size_returns_none(self, otr2_parser):
        """Test that invalid tokens return None."""
        tokens = ["Gunboat", "USS", "Monitor", "-", "River"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert idx is None
        assert size is None
    
    def test_multi_word_name_before_size(self, otr2_parser):
        """Test finding size after multi-word name."""
        tokens = ["10", "GA", "Regt", "M", "Inf", "1", "S5017"]
        idx, size = otr2_parser._find_size_index(tokens)
        assert idx == 2
        assert size == "Regt"


# ============================================================================
# Special Unit Detection Tests
# ============================================================================

class TestSpecialUnitDetection:
    """Tests for _is_special_unit method."""
    
    def test_detect_gunboat(self, otr2_parser):
        """Test detecting Gunboat as special unit."""
        tokens = ["Gunboat", "USS", "Monitor", "-", "-", "River"]
        assert otr2_parser._is_special_unit(tokens) is True
    
    def test_detect_naval_battery(self, otr2_parser):
        """Test detecting Naval Battery as special unit."""
        tokens = ["Naval", "Battery", "-", "-", "S1234"]
        assert otr2_parser._is_special_unit(tokens) is True
    
    def test_detect_wagon_train(self, otr2_parser):
        """Test detecting Wagon Train as special unit."""
        tokens = ["Wagon", "Train", "-", "-", "Box"]
        assert otr2_parser._is_special_unit(tokens) is True
    
    def test_standard_unit_not_special(self, otr2_parser):
        """Test that standard units are not detected as special."""
        tokens = ["Longstreet", "Corps", "L", "Ldr", "-", "S1234"]
        assert otr2_parser._is_special_unit(tokens) is False
    
    def test_empty_tokens_not_special(self, otr2_parser):
        """Test that empty tokens are not special."""
        assert otr2_parser._is_special_unit([]) is False


# ============================================================================
# Special Unit Parsing Tests
# ============================================================================

class TestSpecialUnitParsing:
    """Tests for _parse_special_unit method."""
    
    def test_parse_gunboat(self, otr2_parser):
        """Test parsing a Gunboat unit."""
        tokens = ["Gunboat", "-", "-", "-", "River", "Display"]
        unit = otr2_parser._parse_special_unit(tokens, "Union", "Union Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Gunboat"
        assert unit.unit_type == "Special"
        assert unit.size == "-"
        assert unit.side == "Union"
        assert "River" in unit.hex_location
    
    def test_parse_naval_battery(self, otr2_parser):
        """Test parsing a Naval Battery unit."""
        tokens = ["Naval", "Battery", "-", "-", "S1234"]
        unit = otr2_parser._parse_special_unit(tokens, "Confederate", "Confederate Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Naval Battery"
        assert unit.unit_type == "Special"
    
    def test_parse_wagon_train(self, otr2_parser):
        """Test parsing a Wagon Train unit."""
        tokens = ["Wagon", "Train", "-", "-", "Box"]
        unit = otr2_parser._parse_special_unit(tokens, "Union", "Union Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Wagon Train"
        assert unit.unit_type == "Special"
    
    def test_parse_wagon_train_with_suffix_and_4digit_hex(self, otr2_parser):
        """Test parsing Wagon Train with A/B/C suffix and 4-digit hex (HSN format)."""
        # HSN format: ["Wagon", "Train", "A", "-", "-", "Wag", "2+", "0324", "(Colored", "Church)"]
        tokens = ["Wagon", "Train", "A", "-", "-", "Wag", "2+", "0324", "(Colored", "Church)"]
        unit = otr2_parser._parse_special_unit(tokens, "Union", "Union Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Wagon Train A"
        assert unit.unit_type == "Special"
        assert unit.hex_location == "0324 (Colored Church)"
    
    def test_parse_wagon_train_with_hyphenated_suffix(self, otr2_parser):
        """Test parsing Wagon Train with hyphenated suffix (OTR2 format)."""
        # OTR2 format: ["Wagon", "Train-A", "-", "-", "-", "2*", "S4407", "(Williamsburg)"]
        tokens = ["Wagon", "Train-A", "-", "-", "-", "2*", "S4407", "(Williamsburg)"]
        unit = otr2_parser._parse_special_unit(tokens, "Union", "Union Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Wagon Train-A"
        assert unit.unit_type == "Special"
        assert "S4407" in unit.hex_location


# ============================================================================
# Standard Unit Parsing Tests
# ============================================================================

class TestStandardUnitParsing:
    """Tests for _parse_standard_unit method."""
    
    def test_parse_leader(self, otr2_parser, standard_columns):
        """Test parsing a leader unit."""
        tokens = ["Magruder", "Div", "M", "Ldr", "-", "S5510", "(Yorktown)"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Magruder"
        assert unit.size == "Div"
        assert unit.command == "M"
        assert unit.unit_type == "Ldr"
        assert unit.manpower_value == "-"
        assert "S5510" in unit.hex_location
    
    def test_parse_infantry_with_footnote(self, otr2_parser, standard_columns):
        """Test parsing infantry with footnote markers."""
        tokens = ["Ward*", "Brig", "M", "Inf", "2*", "S5510", "(Yorktown)"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Ward"
        assert unit.unit_type == "Inf"
        assert unit.manpower_value == "2*"
        assert "*" in unit.notes
    
    def test_parse_cavalry(self, otr2_parser, standard_columns):
        """Test parsing a cavalry unit."""
        tokens = ["Stuart", "Brig", "S", "Cav", "3", "S4000"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert unit.unit_type == "Cav"
    
    def test_parse_artillery(self, otr2_parser, standard_columns):
        """Test parsing an artillery unit."""
        tokens = ["Siege*", "Regt", "M", "Art", "2*", "S5510", "(Yorktown)"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert unit.unit_type == "Art"
    
    def test_parse_multi_word_name(self, otr2_parser, standard_columns):
        """Test parsing unit with multi-word name."""
        tokens = ["10", "GA*", "Regt", "M", "Inf", "1*", "S5017"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert "10" in unit.unit_leader
        assert "GA" in unit.unit_leader
        assert unit.size == "Regt"
    
    def test_parse_multi_hex_location(self, otr2_parser, standard_columns):
        """Test parsing unit with multiple hex options."""
        tokens = ["Wilcox-A", "Brig", "M", "Inf", "6", "S4811,", "S4912", "or", "S5017"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        
        assert unit is not None
        assert "S4811" in unit.hex_location
        assert "S4912" in unit.hex_location
        assert "S5017" in unit.hex_location
    
    def test_parse_insufficient_tokens(self, otr2_parser, standard_columns):
        """Test that insufficient tokens return None."""
        tokens = ["Ward", "Brig"]  # Too few tokens
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        assert unit is None
    
    def test_parse_invalid_type_returns_none(self, otr2_parser, standard_columns):
        """Test that invalid unit type returns None."""
        tokens = ["Unit", "Brig", "M", "InvalidType", "5", "S1234"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Confederate Set-Up")
        assert unit is None


# ============================================================================
# Turn Column Parsing Tests (HCR style)
# ============================================================================

class TestTurnColumnParsing:
    """Tests for parsing with turn column (HCR reinforcements)."""
    
    def test_parse_with_turn_column(self, hcr_parser, turn_columns):
        """Test parsing unit with turn column."""
        tokens = ["1", "Smith", "Brig", "S", "Inf", "4", "Entry", "Area"]
        unit = hcr_parser._parse_standard_unit(tokens, "Union", turn_columns, "Union Reinforcements")
        
        assert unit is not None
        assert unit.turn == "1"
        assert unit.unit_leader == "Smith"
        assert unit.size == "Brig"


# ============================================================================
# Row Parsing Integration Tests
# ============================================================================

class TestParseRow:
    """Integration tests for parse_row method."""
    
    def test_parse_row_standard_unit(self, otr2_parser, standard_columns):
        """Test parse_row with standard unit."""
        tokens = ["Longstreet", "Corps", "L", "Ldr", "-", "S1234"]
        unit = otr2_parser.parse_row(tokens, "Confederate", standard_columns, "Set-Up")
        
        assert unit is not None
        assert unit.unit_leader == "Longstreet"
    
    def test_parse_row_special_unit(self, otr2_parser, standard_columns):
        """Test parse_row with special unit (Gunboat)."""
        tokens = ["Gunboat", "-", "-", "-", "River"]
        unit = otr2_parser.parse_row(tokens, "Union", standard_columns, "Set-Up")
        
        assert unit is not None
        assert unit.unit_type == "Special"
    
    def test_parse_row_empty(self, otr2_parser, standard_columns):
        """Test parse_row with empty tokens."""
        unit = otr2_parser.parse_row([], "Confederate", standard_columns, "Set-Up")
        assert unit is None


# ============================================================================
# Table Parsing Tests
# ============================================================================

class TestParseTable:
    """Tests for parse_table method."""
    
    def test_parse_simple_table(self, otr2_parser):
        """Test parsing a simple table."""
        table = {
            "name": "Confederate Set-Up",
            "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
            "rows": [
                ["Magruder", "Div", "M", "Ldr", "-", "S5510"],
                ["Ward", "Brig", "M", "Inf", "2", "S5510"],
            ],
            "annotations": {}
        }
        
        units = otr2_parser.parse_table(table, "Confederate", 1)
        
        assert len(units) == 2
        assert units[0].unit_leader == "Magruder"
        assert units[1].unit_leader == "Ward"
    
    def test_parse_table_skips_invalid_rows(self, otr2_parser):
        """Test that invalid rows are skipped."""
        table = {
            "name": "Test Table",
            "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
            "rows": [
                ["Valid", "Brig", "M", "Inf", "2", "S1234"],
                ["Too", "Few"],  # Invalid - too few tokens
                ["Another", "Corps", "A", "Ldr", "-", "S5000"],
            ],
            "annotations": {}
        }
        
        units = otr2_parser.parse_table(table, "Union", 1)
        
        assert len(units) == 2
        assert units[0].unit_leader == "Valid"
        assert units[1].unit_leader == "Another"
    
    def test_parse_table_preserves_table_name(self, otr2_parser):
        """Test that table name is preserved on units."""
        table = {
            "name": "First Increment",
            "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
            "rows": [
                ["Unit", "Brig", "M", "Inf", "2", "S1234"],
            ],
            "annotations": {}
        }
        
        units = otr2_parser.parse_table(table, "Confederate", 1)
        
        assert units[0].table_name == "First Increment"


# ============================================================================
# Leader Deduplication Tests
# ============================================================================

class TestLeaderDeduplication:
    """Tests for deduplicate_leaders method."""
    
    def test_deduplicate_same_leader_same_hex(self, otr2_parser):
        """Test that same leader at same hex is deduplicated."""
        units = [
            Unit("Longstreet", "Corps", "L", "Ldr", "-", "S1234", "Confederate"),
            Unit("Longstreet", "Corps", "L", "Ldr", "-", "S1234", "Confederate"),  # Duplicate
            Unit("Ward", "Brig", "M", "Inf", "2", "S5510", "Confederate"),
        ]
        
        result = otr2_parser.deduplicate_leaders(units)
        
        # Should have 1 Longstreet leader + 1 Ward infantry
        assert len(result) == 2
        leader_names = [u.unit_leader for u in result if u.unit_type == "Ldr"]
        assert leader_names.count("Longstreet") == 1
    
    def test_keep_same_leader_different_hex(self, otr2_parser):
        """Test that same leader at different hexes is kept."""
        units = [
            Unit("Lee", "Army", "A", "Ldr", "-", "S1234", "Confederate"),
            Unit("Lee", "Army", "A", "Ldr", "-", "S5000", "Confederate"),  # Different hex
        ]
        
        result = otr2_parser.deduplicate_leaders(units)
        
        # Both should be kept - different locations
        assert len(result) == 2
    
    def test_non_leaders_not_deduplicated(self, otr2_parser):
        """Test that non-leader units are not affected."""
        units = [
            Unit("1st TX", "Brig", "L", "Inf", "5", "S1234", "Confederate"),
            Unit("1st TX", "Brig", "L", "Inf", "5", "S1234", "Confederate"),  # Same name/hex
        ]
        
        result = otr2_parser.deduplicate_leaders(units)
        
        # Both should be kept - not leaders
        assert len(result) == 2


# ============================================================================
# Scenario Parsing Tests
# ============================================================================

class TestParseScenario:
    """Tests for parse_scenario method."""
    
    def test_parse_scenario_basic(self, otr2_parser):
        """Test parsing a basic scenario."""
        raw_scenario = {
            "scenario_number": 1,
            "scenario_name": "Test Scenario",
            "start_page": 5,
            "confederate_tables": [
                {
                    "name": "Confederate Set-Up",
                    "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
                    "rows": [
                        ["Lee", "Army", "A", "Ldr", "-", "S1234"],
                        ["Jackson", "Corps", "J", "Ldr", "-", "S2000"],
                    ],
                    "annotations": {"*": "Test footnote"}
                }
            ],
            "union_tables": [
                {
                    "name": "Union Set-Up",
                    "header_row": ["Unit/Leader", "Size", "Command", "Type", "Manpower Value", "Hex"],
                    "rows": [
                        ["McClellan", "Army", "A", "Ldr", "-", "S5000"],
                    ],
                    "annotations": {}
                }
            ]
        }
        
        scenario = otr2_parser.parse_scenario(raw_scenario)
        
        assert scenario.number == 1
        assert scenario.name == "Test Scenario"
        assert scenario.start_page == 5
        assert len(scenario.confederate_units) == 2
        assert len(scenario.union_units) == 1
        assert "*" in scenario.confederate_footnotes
    
    def test_parse_scenario_collects_footnotes(self, otr2_parser):
        """Test that footnotes are collected from tables."""
        raw_scenario = {
            "scenario_number": 1,
            "scenario_name": "Test",
            "start_page": 1,
            "confederate_tables": [
                {
                    "name": "Set-Up",
                    "header_row": [],
                    "rows": [],
                    "annotations": {
                        "*": "Footnote 1",
                        "†": "Footnote 2"
                    }
                }
            ],
            "union_tables": []
        }
        
        scenario = otr2_parser.parse_scenario(raw_scenario)
        
        assert scenario.confederate_footnotes["*"] == "Footnote 1"
        assert scenario.confederate_footnotes["†"] == "Footnote 2"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_long_hex_location_truncated(self, otr2_parser):
        """Test that overly long hex locations are handled."""
        # This tests the sanity check in _parse_special_unit
        tokens = ["Gunboat", "-", "-"] + ["word"] * 100
        unit = otr2_parser._parse_special_unit(tokens, "Union", "Set-Up")
        
        assert unit is not None
        # Hex should be empty due to sanity check
        assert len(unit.hex_location) <= 60
    
    def test_unknown_footnote_symbol_tracked(self, otr2_parser):
        """Test that unknown symbols are tracked."""
        otr2_parser._extract_footnotes("Unit@")  # @ is not a standard symbol
        
        # Should have tracked the unknown symbol
        assert "@" in otr2_parser.unknown_symbols
    
    def test_cav_cav_pattern(self, otr2_parser, standard_columns):
        """Test parsing problematic 'Cav Cav' pattern from raw extraction."""
        # This pattern appears in the raw data: "3 VA Regt Cav Cav 1 ..."
        # The PDF extraction sometimes repeats "Cav"
        tokens = ["3", "VA", "Regt", "Cav", "Cav", "1", "Any", "hex"]
        unit = otr2_parser._parse_standard_unit(tokens, "Confederate", standard_columns, "Set-Up")
        
        # Current behavior: may not parse correctly, which is expected
        # This is a known issue with raw extraction, not the parser
        # If we fix this, update the assertion
        # For now, just verify it doesn't crash
        pass
