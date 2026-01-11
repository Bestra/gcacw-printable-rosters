#!/usr/bin/env python3
"""
Diagnostic tool to preview PDF table extraction and spot column anomalies.
Run this before parsing a new game to check for unexpected table structures.

Usage:
    uv run python diagnose_pdf.py ../data/SomeGame.pdf [page_number]
"""

import pdfplumber
import re
import sys
from collections import Counter


VALID_SIZES = ['Army', 'Corps', 'Demi-Div', 'D-Div', 'Div', 'Brig', 'Regt']
VALID_TYPES = ['Ldr', 'Inf', 'Cav', 'Art']


def find_size_index(parts: list[str]) -> int | None:
    """Find the index of the Size column in a row."""
    for i, part in enumerate(parts):
        if part in VALID_SIZES or part == 'D-Div':
            return i
    return None


def analyze_row(line: str) -> dict | None:
    """Analyze a potential unit row and return parsed fields."""
    parts = line.split()
    if len(parts) < 5:
        return None
    
    size_idx = find_size_index(parts)
    if size_idx is None:
        return None
    
    # Check if there's a suspicious standalone number before Size
    name_parts = parts[:size_idx]
    has_trailing_number = bool(name_parts and re.match(r'^\d+$', name_parts[-1]))
    
    remaining = parts[size_idx + 1:]
    if len(remaining) < 3:
        return None
    
    # Check if unit type is valid
    unit_type = remaining[1] if len(remaining) > 1 else None
    if unit_type not in VALID_TYPES:
        return None
    
    return {
        'raw': line,
        'name_parts': name_parts,
        'name': ' '.join(name_parts),
        'size': parts[size_idx],
        'command': remaining[0] if remaining else None,
        'type': unit_type,
        'manpower': remaining[2] if len(remaining) > 2 else None,
        'hex': ' '.join(remaining[3:]) if len(remaining) > 3 else '',
        'has_trailing_number': has_trailing_number,
        'columns_before_size': size_idx,
    }


def diagnose_page(pdf, page_idx: int):
    """Analyze a single page for unit table structure."""
    page = pdf.pages[page_idx]
    text = page.extract_text() or ''
    lines = text.split('\n')
    
    print(f"\n{'='*70}")
    print(f"PAGE {page_idx + 1}")
    print('='*70)
    
    units = []
    in_setup = False
    current_side = None
    
    for line in lines:
        line_lower = line.lower()
        
        # Track setup sections
        if 'confederate set-up' in line_lower:
            current_side = 'Confederate'
            in_setup = True
            print(f"\n--- Confederate Set-up ---")
            continue
        elif 'union set-up' in line_lower:
            current_side = 'Union'
            in_setup = True
            print(f"\n--- Union Set-up ---")
            continue
        
        if not in_setup:
            continue
        
        # Skip headers
        if 'unit/leader' in line_lower:
            print(f"  [HEADER] {line}")
            continue
        
        # Try to parse as unit
        result = analyze_row(line)
        if result:
            units.append(result)
            
            # Flag anomalies
            warnings = []
            if result['has_trailing_number']:
                warnings.append("⚠️  TRAILING NUMBER IN NAME")
            if result['columns_before_size'] > 2:
                warnings.append(f"⚠️  {result['columns_before_size']} COLUMNS BEFORE SIZE")
            
            warning_str = ' '.join(warnings) if warnings else ''
            print(f"  {result['name']:20} | {result['size']:8} | {result['command']:6} | {result['type']:4} | {result['manpower']:5} | {result['hex'][:30]}")
            if warning_str:
                print(f"    {warning_str}")
    
    return units


def diagnose_pdf(pdf_path: str, specific_page: int | None = None):
    """Run diagnostics on a PDF."""
    print(f"Diagnosing: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        all_units = []
        
        if specific_page:
            # Diagnose specific page
            all_units = diagnose_page(pdf, specific_page - 1)  # Convert to 0-indexed
        else:
            # Scan all pages for unit tables
            for page_idx in range(len(pdf.pages)):
                page = pdf.pages[page_idx]
                text = page.extract_text() or ''
                
                # Only process pages with setup tables
                if 'set-up' in text.lower():
                    units = diagnose_page(pdf, page_idx)
                    all_units.extend(units)
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)
        print(f"Total units found: {len(all_units)}")
        
        # Check for column anomalies
        trailing_numbers = [u for u in all_units if u['has_trailing_number']]
        if trailing_numbers:
            print(f"\n⚠️  ANOMALY: {len(trailing_numbers)} units have trailing numbers in name")
            print("   This may indicate an extra column (like 'Set' for reinforcement turns)")
            print("   Examples:")
            for u in trailing_numbers[:5]:
                print(f"     '{u['name']}' -> name_parts: {u['name_parts']}")
        
        # Check column counts
        col_counts = Counter(u['columns_before_size'] for u in all_units)
        if len(col_counts) > 1:
            print(f"\n⚠️  ANOMALY: Inconsistent columns before Size: {dict(col_counts)}")
        else:
            print(f"\n✓ Consistent columns before Size: {dict(col_counts)}")
        
        # Check for multi-word names (might include extra column)
        multi_word = [u for u in all_units if len(u['name_parts']) > 1 and not any(
            p in ['Wagon', 'Naval', 'Light'] for p in u['name_parts']
        )]
        if multi_word:
            print(f"\n⚠️  INFO: {len(multi_word)} units have multi-word names")
            print("   Verify these aren't picking up extra columns:")
            for u in multi_word[:5]:
                print(f"     '{u['name']}'")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python diagnose_pdf.py <pdf_path> [page_number]")
        print("  page_number: optional, 1-indexed page to analyze")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    specific_page = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    diagnose_pdf(pdf_path, specific_page)


if __name__ == "__main__":
    main()
