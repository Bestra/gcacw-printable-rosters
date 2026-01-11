---
name: debug-pdf-extraction
description: Debug PDF text extraction issues. Use when parser is producing wrong data, missing units, or garbled text from a PDF.
---

# Debug PDF Extraction

PDFs store visual layout, not logical text structure. This causes extraction issues like merged columns, wrong reading order, and corrupted characters.

## Inspect Raw Page Text

Create a temporary script to see exactly what pdfplumber extracts:

```python
# parser/debug_pdf.py
import pdfplumber

with pdfplumber.open("../data/SomeGame.pdf") as pdf:
    page = pdf.pages[PAGE_NUMBER - 1]  # 0-indexed
    text = page.extract_text()

    for j, line in enumerate(text.split("\n")):
        print(f"{j:3}: {repr(line)}")
```

Run with:

```bash
cd parser && uv run python debug_pdf.py
```

## Common Issues

### Merged columns

Text from sidebars gets concatenated with main content:

```
"sCenario 10: marChinG to CoLd harbor 4. Destroyed RR Stations: The following..."
```

Solution: Use regex to extract just the part you need.

### Weird capitalization

Small caps fonts appear as mixed case:

```
"sCenario" instead of "Scenario"
```

Solution: Use case-insensitive matching (`re.IGNORECASE`).

### Table extraction issues

Tables may not parse correctly with `extract_text()`. Try:

```python
tables = page.extract_tables()
for table in tables:
    for row in table:
        print(row)
```

## Inspect Specific Elements

```python
# Find text containing a pattern
import re
for i, page in enumerate(pdf.pages):
    text = page.extract_text() or ""
    if re.search(r"pattern", text, re.IGNORECASE):
        print(f"Found on page {i+1}")
```

## Clean Up

Delete `parser/debug_pdf.py` when done—it's just for investigation.
