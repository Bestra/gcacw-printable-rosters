# Plan: Extract Unit Stats from VASSAL Module

## Status: ✅ COMPLETED

All implementation steps have been completed. Unit tactical/artillery stats are now extracted from VASSAL module and merged into web JSON.

## Problem

ALL units in HCR show 0/0 for tactical/artillery values because the PDF scenario tables only contain manpower values. The tactical and artillery values are counter stats that only exist in the VASSAL module (encoded in background image filenames).

**Example:** Unit "8 IL-A" (cavalry):

- Parsed from PDF: `manpower_value: "1"` - that's all
- VASSAL background: `Cav-V-0-0.jpg` → tactical=0, artillery=0

**Example:** Unit "Doubleday" (infantry):

- Parsed from PDF: `manpower_value: "9*"` - that's all
- VASSAL background: `I-P-2-4.jpg` → tactical=2, artillery=4

## Counter Stats (from game manual)

```
         FRONT
    ┌───────────────┐
    │    Early-B    │ ← Name
    │      DH       │ ← Organization (corps/wing)
    │    ┌───┐      │
    │    │ X │      │ ← Symbol (infantry/cavalry)
    │    └───┘      │
    │    2   1      │ ← Tactical Value / Artillery Value
    └───────────────┘
```

## Background Image Naming Patterns (HCR)

From buildFile.xml analysis:

```
Union Corps:     I-P-2-4.jpg    = Corps I, tactical 2, artillery 4
                 II-P-3-6.jpg   = Corps II, tactical 3, artillery 6
CSA Jackson:     J-3-4.jpg      = Jackson's Wing, tactical 3, artillery 4
CSA Longstreet:  L-3-2.jpg      = Longstreet's Wing, tactical 3, artillery 2
Cavalry:         Cav-1-2.jpg    = tactical 1, artillery 2
Baltimore:       Balt-N-1-1.jpg = Baltimore defense, tactical 1, artillery 1
DC Defense:      DC-N-1-0.jpg   = DC defense, tactical 1, artillery 0
```

**Pattern:** `{corps/wing}-{optional-P/N}-{tactical}-{artillery}.jpg`

## Implementation Steps

### Step 1: Analyze VASSAL Background Image Patterns ✅

**File:** Already extracted at `/tmp/hcr_vmod/`

**Findings:** 52 unique background image patterns found:

```
Union Corps:     I-P-2-4.jpg    = Corps I, tactical 2, artillery 4
                 II-P-3-6.jpg   = Corps II, tactical 3, artillery 6
CSA Jackson:     J-3-4.jpg      = Jackson's Wing, tactical 3, artillery 4
CSA Longstreet:  L-3-2.jpg      = Longstreet's Wing, tactical 3, artillery 2
Cavalry:         Cav-V-0-0.jpg  = Union cavalry, tactical 0, artillery 0
                 Cav-1-0.jpg    = CSA cavalry, tactical 1, artillery 0
Baltimore:       Balt-N-1-1.jpg = Baltimore defense, tactical 1, artillery 1
DC Defense:      DC-N-1-0.jpg   = DC defense, tactical 1, artillery 0
```

**Pattern:** `{corps/wing}-{optional-P/N/V}-{tactical}-{artillery}.jpg`

### Step 2: Create Unit Stats Extraction Script ✅

**File:** `parser/extract_hcr_stats.py` (created)

**Usage:**

```bash
cd parser && uv run python extract_hcr_stats.py /tmp/hcr_vmod --verbose
```

**Output:** `parser/vassal_stats/hcr_stats.json`

**Results:**

- Extracted stats for 102 units
- Built lookup table with 315 name variants for fuzzy matching

### Step 3: Modify convert_to_web.py to Merge Stats ✅

**File:** `parser/convert_to_web.py` (modified)

**Changes:**

1. Added `load_vassal_stats()` function to load stats file if available
2. Added `get_name_variants()` for fuzzy matching unit names
3. Added `lookup_vassal_stats()` to find unit stats with name variant matching
4. Modified `convert_unit()` to add `tacticalValue` and `artilleryValue` fields
5. Modified `convert_scenario()` and `convert_game_data()` to pass VASSAL data

### Step 4: Update TypeScript Types ✅

**File:** `web/src/types.ts` (modified)

**Added to Unit interface:**

```typescript
tacticalValue?: number;
artilleryValue?: number;
```

### Step 5: Regenerate HCR Web JSON ✅

**Commands:**

```bash
cd /Users/bestra/projects/gcacw-scenario-parser/parser
uv run python convert_to_web.py
```

**Results verified:**

- Doubleday: tactical=2, artillery=4 ✓
- A.P. Hill: tactical=3, artillery=4 ✓ (fuzzy match with space handling)
- 8 IL-A: tactical=0, artillery=0 ✓ (matches VASSAL module)

**Note:** Union cavalry regiments show 0/0 stats because that's how they're defined in the VASSAL module (using `Cav-V-0-0.jpg` background). This appears to be intentional in the module design.

## Files Created/Modified

| File                                 | Action                                    | Status |
| ------------------------------------ | ----------------------------------------- | ------ |
| `parser/extract_hcr_stats.py`        | CREATE - stats extraction script          | ✅     |
| `parser/vassal_stats/hcr_stats.json` | CREATE - extracted stats                  | ✅     |
| `parser/convert_to_web.py`           | MODIFY - merge VASSAL stats               | ✅     |
| `web/src/types.ts`                   | MODIFY - add tacticalValue/artilleryValue | ✅     |
| `web/public/data/hcr.json`           | REGENERATE - now has stats                | ✅     |

## Next Steps (Optional)

### Display Stats in UI

The stats are now in the data but not yet displayed. To show them in UnitCard:

1. Modify `web/src/components/UnitCard.tsx` to show `unit.tacticalValue` and `unit.artilleryValue`
2. Could display as "T2/A4" or similar compact format

### Extend to Other Games

This approach can be extended to other games that have VASSAL modules:

1. Extract the VMOD file
2. Analyze the background image patterns (may differ per game)
3. Create a game-specific extraction script or generalize `extract_hcr_stats.py`
4. Run extraction and regenerate

## Notes

- This approach keeps PDF parsing separate from VASSAL extraction
- VASSAL stats act as supplemental data, not replacement
- Can be extended to other games that have similar composite counter systems
- The generate_hcr_counters.py already has the unit matching logic we can reuse

## VASSAL Module Location

The HCR VASSAL module should be at:
`/Users/bestra/Documents/vasl/gcacw/HCR_3_28.vmod`

If not extracted, run:

```bash
mkdir -p /tmp/hcr_vmod
unzip "/Users/bestra/Documents/vasl/gcacw/HCR_3_28.vmod" -d /tmp/hcr_vmod
```
