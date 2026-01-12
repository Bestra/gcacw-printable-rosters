# Extract VASSAL Module Images

Extract unit counter images from VASSAL modules (.vmod files) for use in the web roster generator.

## Overview

VASSAL modules are ZIP files containing game piece definitions and images. This skill covers:

1. Understanding module structure
2. Identifying the counter image system used
3. Extracting and mapping images to parsed unit data
4. Generating composite images when needed

## VASSAL Module Structure

A `.vmod` file is a ZIP archive containing:

```
module.vmod/
├── buildFile.xml      # Piece definitions, prototypes, image references
├── moduledata         # Module metadata
├── images/            # All image files (jpg, gif, png)
│   ├── counters...
│   ├── markers...
│   └── maps...
└── *.vsav             # Saved game files for scenarios
```

### buildFile.xml

This XML file defines all game pieces. Key elements:

```xml
<!-- PieceSlot defines a placeable piece -->
<VASSAL.build.widget.PieceSlot entryName="UnitName" gpid="123">
  +/null/prototype;USA Infantry Division\
  piece;;;ImageFile.jpg;UnitName/
</VASSAL.build.widget.PieceSlot>

<!-- The piece definition format: -->
<!-- piece;;;IMAGE_FILE;PIECE_NAME/ -->
```

## Counter Image Systems

### Type 1: Individual Counter Images (RTG2-style)

Games like RTG2, OTR2, GTC2 have dedicated images per unit:

- `C_Lee.jpg` - Confederate unit "Lee"
- `U_Meade.jpg` - Union unit "Meade"
- `CL_Stuart.jpg` - Confederate leader
- `UL_Hooker.jpg` - Union leader

**Extraction**: Use `extract_images.py` with the game code.

### Type 2: Composite Counters (HCR-style)

Games like HCR use layered composition:

- **Background**: Corps/wing identifier + quality + strength (e.g., `I-P-2-4.jpg`)
- **Manpower overlay**: `UMP_01.gif` to `UMP_16.gif` (Union), `CMP_1.gif` to `CMP_17.gif` (CSA)
- **Text label**: Unit name rendered dynamically

Only **leaders** have dedicated images. Brigade/division counters are composited.

**Background image naming patterns:**

- Union: `I-P-2-4.jpg` = Corps I, quality 2, strength 4
- Confederate: `J-3-4.jpg` = Jackson's Wing, quality 3, strength 4
- `L-3-2.jpg` = Longstreet's Wing
- `Balt-N-1-1.jpg` = Baltimore defense units
- `DC-N-1-0.jpg` = Washington DC defense

**Extraction**: Use `generate_hcr_counters.py` which:

1. Parses buildFile.xml for unit→background mappings
2. Loads parsed game data for actual unit names
3. Copies leader images directly
4. Composites brigade/division images with unit name text overlay

## Extraction Workflow

### Step 1: Extract the VMOD

```bash
mkdir /tmp/game_vmod
unzip "/path/to/GAME.vmod" -d /tmp/game_vmod
```

### Step 2: Explore the Images

```bash
# List all images
ls /tmp/game_vmod/images/

# Find unit counters (filter out maps, charts, markers)
ls /tmp/game_vmod/images/ | grep -vE "Map-|Chart|VP|Turn|Control"
```

### Step 3: Examine buildFile.xml

```bash
# Find piece definitions
grep -o 'entryName="[^"]*".*piece;;;[^;]*;[^/]*/' buildFile.xml | head -50

# Look for prototype definitions (counter composition)
grep "PrototypeDefinition" buildFile.xml | head -20
```

### Step 4: Determine Counter System

**Check for individual images:**

```bash
# RTG2-style: Look for C_/U_ prefixed images
ls /tmp/game_vmod/images/ | grep -E "^[CU]_"
```

**Check for composite system:**

```bash
# HCR-style: Look for corps/manpower markers
ls /tmp/game_vmod/images/ | grep -E "^[IVX]+-P-|CMP_|UMP_"
```

### Step 5: Run Appropriate Extractor

**For RTG2-style games:**

```bash
cd parser
uv run python extract_images.py GAME /path/to/GAME.vmod
```

**For HCR-style games:**

```bash
cd parser
uv run python generate_hcr_counters.py /path/to/extracted/vmod
```

## Name Matching Challenges

Unit names often differ between VASSAL and parsed data:

| VASSAL       | Parsed        | Issue             |
| ------------ | ------------- | ----------------- |
| `Heitzelman` | `Heintzelman` | Typo              |
| `A.P.Hill`   | `A.P. Hill`   | Spacing           |
| `Rodes`      | `Rodes-A`     | Suffix            |
| `Wilcox`     | `Willcox-A`   | Spelling + suffix |
| `D'Utassy`   | `D'Utassy`    | Curly apostrophe  |

The extractors include name normalization to handle these variations.

## Output Files

### Image Mapping JSON

Location: `parser/image_mappings/{game}_images.json`

```json
{
  "game": "hcr",
  "matched": {
    "C:Jackson": "Jackson",
    "U:Meade": "U_Meade"
  },
  "matched_with_ext": {
    "C:Jackson": "Jackson.jpg",
    "U:Meade": "U_Meade.jpg"
  },
  "unmatched": ["Union (Cav): IL", ...],
  "unused_images": [...]
}
```

### TypeScript Image Map

Location: `web/src/data/imageMap.ts`

This file is auto-generated and maps unit keys to image filenames for the web app.

### Counter Images

Location: `web/public/images/counters/{game}/`

## Adding a New Game's Images

1. **Identify the counter system** by examining the VMOD
2. **For RTG2-style**: Add game patterns to `extract_images.py`
3. **For composite-style**: Create a game-specific generator or adapt `generate_hcr_counters.py`
4. **Run the extractor**
5. **Check unmatched units** and add name normalization as needed
6. **Update `imageMap.ts`** if not auto-generated

## Troubleshooting

### "Missing background" errors

The VASSAL module may not have all referenced images. Check if images exist:

```bash
ls /tmp/game_vmod/images/ | grep -i "imagename"
```

### High unmatched count

Usually indicates:

- Wrong counter system identification
- Name normalization issues
- Parsing artifacts in source data (e.g., turn numbers mixed into unit names)

### Composite images look wrong

Check the Pillow font loading - the script uses system fonts with fallback to default.

## Related Files

- `parser/extract_images.py` - RTG2-style extractor
- `parser/generate_hcr_counters.py` - HCR composite generator
- `parser/image_mappings/*.json` - Generated mappings
- `web/src/data/imageMap.ts` - TypeScript image map
