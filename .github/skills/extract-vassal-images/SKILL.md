# Extract VASSAL Module Images

Extract unit counter images from VASSAL modules (.vmod files) for use in the web roster generator.

## Overview

VASSAL modules are ZIP files containing game piece definitions and images. This skill covers:

1. Understanding module structure
2. Automatically detecting the counter image system used
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

### Type 1: INDIVIDUAL (RTG2-style)

Each unit has a dedicated pre-rendered image with the unit name already on it:

- `C_Lee.jpg` - Confederate unit "Lee"
- `U_Meade.jpg` - Union unit "Meade"
- `CL_Stuart.jpg` - Confederate leader
- `UL_Hooker.jpg` - Union leader

**Extraction**: Use `extract_images.py` with the game code.

### Type 2: TEMPLATE_COMPOSITE (HCR/OTR2/GTC2-style)

Units use generic background images based on corps/type, with unit names overlaid via VASSAL's label mechanism:

- **Background**: Corps/wing identifier + quality + strength (e.g., `I-P-2-4.jpg`, `UII_2_3.jpg`, `USA_I_24.jpg`)
- **Text label**: Unit name rendered dynamically by VASSAL

Only **leaders** have dedicated images. Brigade/division counters are composited.

**Background image naming patterns:**

- Union corps: `I-P-2-4.jpg`, `UII_2_3.jpg`, `UV_2_2.jpg`
- Confederate: `J-3-4.jpg` (Jackson's Wing), `CIII_3_4.jpg`
- OTR2-style: `USA_I_24.jpg`, `CSA_M_20.jpg`

**Extraction**: Use the unified generator `generate_counters.py` with the appropriate game_id:

1. Parses buildFile.xml for unit→background mappings
2. Loads parsed game data for actual unit names
3. Copies leader images directly
4. Composites brigade/division images with unit name text overlay

## Extraction Workflow

### Step 1: Detect Counter Type (Recommended)

Use the automatic counter type detection script:

```bash
cd parser && uv run python detect_counter_type.py /path/to/GAME.vmod
```

This analyzes the buildFile.xml and image naming patterns to determine:

- **INDIVIDUAL**: Each unit has a dedicated pre-rendered image
- **TEMPLATE_COMPOSITE**: Units use generic backgrounds with text overlays
- **HYBRID**: Mixed (usually leaders are individual, units are templates)

To analyze all modules in a directory:

```bash
cd parser && uv run python detect_counter_type.py --all /path/to/vmods/
```

### Step 2: Extract the VMOD (if needed for manual inspection)

```bash
mkdir /tmp/game_vmod
unzip "/path/to/GAME.vmod" -d /tmp/game_vmod
```

### Step 3: Explore the Images

```bash
# List all images
ls /tmp/game_vmod/images/

# Find unit counters (filter out maps, charts, markers)
ls /tmp/game_vmod/images/ | grep -vE "Map-|Chart|VP|Turn|Control"
```

### Step 4: Examine buildFile.xml

```bash
# Find piece definitions
grep -o 'entryName="[^"]*".*piece;;;[^;]*;[^/]*/' buildFile.xml | head -50

# Look for prototype definitions (counter composition)
grep "PrototypeDefinition" buildFile.xml | head -20
```

### Step 5: Run Appropriate Extractor

**For INDIVIDUAL (RTG2-style) games:**

```bash
cd parser
uv run python extract_images.py GAME /path/to/GAME.vmod
```

**For TEMPLATE_COMPOSITE games:**

Use the unified generator with the appropriate game_id:

```bash
# HCR
cd parser && uv run python generate_counters.py --game hcr /path/to/HCR.vmod

# OTR2
cd parser && uv run python generate_counters.py --game otr2 /path/to/OTR2.vmod

# GTC2
cd parser && uv run python generate_counters.py --game gtc2 /path/to/GTC2.vmod
```

For new games, add game-specific configuration to `generate_counters.py`.

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

1. **Detect the counter system** using `detect_counter_type.py`
2. **For INDIVIDUAL**: Add game patterns to `extract_images.py`
3. **For TEMPLATE_COMPOSITE**: Add game-specific configuration to `generate_counters.py`
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

- `parser/detect_counter_type.py` - Automatic counter type detection
- `parser/extract_images.py` - INDIVIDUAL (RTG2-style) extractor
- `parser/generate_counters.py` - Unified TEMPLATE_COMPOSITE generator (HCR, OTR2, GTC2)
- `parser/image_mappings/*.json` - Generated mappings
- `web/src/data/imageMap.ts` - TypeScript image map
