---
name: extract-vassal-images
description: Extract unit counter images from VASSAL game modules (.vmod files) for roster generation. Use when adding counter images to a game, setting up image mappings for units, or troubleshooting missing/mismatched unit images. Handles both individual pre-rendered images and template-based composite images with automatic counter type detection.
---

# Extract VASSAL Module Images

## Overview

VASSAL modules are ZIP files containing game piece definitions and images. This workflow covers:

1. Automatically detecting the counter image system used (`detect_counter_type.py`)
2. Understanding module structure
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

**Important**: For HYBRID systems where VASSAL adds text labels dynamically (detected by `detect_counter_type.py`), use `--no-text` flag to avoid double text overlay:

```bash
cd parser && uv run python image_extraction/generate_counters.py tom ~/Documents/vasl/gcacw/TOM_3_17.vmod --no-text
```

## Quick Start

**VMOD Files Location**: `~/Documents/vasl/gcacw/` (store all GCACW .vmod files here)

**For a streamlined extraction workflow, see:**

- **Quick Reference**: `parser/EXTRACT_IMAGES_QUICKSTART.md` - 30-second workflow cheat sheet
- **Integration Script**: `parser/image_extraction/integrate_game_images.py` - Automates post-extraction setup

## Extraction Workflow

### Step 1: Detect Counter Type (CRITICAL - Always Start Here)

Use `detect_counter_type.py` to automatically determine the counter image system:

```bash
cd parser && uv run python image_extraction/detect_counter_type.py /path/to/GAME.vmod
```

This analyzes buildFile.xml and image naming patterns to determine:

- **INDIVIDUAL**: Each unit has a dedicated pre-rendered image (e.g., RTG2)
- **TEMPLATE_COMPOSITE**: Units use generic backgrounds with text overlays (e.g., HCR, OTR2, GTC2, HSN)
- **HYBRID**: Mixed approach (usually leaders are individual, units are templates)

To analyze all modules in a directory:

```bash
cd parser && uv run python image_extraction/detect_counter_type.py --all /path/to/vmods/
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
uv run python image_extraction/extract_images.py GAME /path/to/GAME.vmod
```

**For TEMPLATE_COMPOSITE games:**

```bash
# HCR
cd parser && uv run python image_extraction/generate_counters.py hcr ~/Documents/vasl/gcacw/HCR.vmod

# OTR2
cd parser && uv run python image_extraction/generate_counters.py otr2 ~/Documents/vasl/gcacw/OTR2.vmod

# GTC2
cd parser && uv run python image_extraction/generate_counters.py gtc2 ~/Documents/vasl/gcacw/GTC2.vmod

# TOM (HYBRID - uses --no-text because VASSAL adds labels)
cd parser && uv run python image_extraction/generate_counters.py tom ~/Documents/vasl/gcacw/TOM_3_17.vmod --no-text
```

For new games, add game-specific configuration to `image_extraction/generate_counters.py`.

### Step 6: Integrate into Web App

Use the integration helper script to automate the post-extraction setup:

```bash
cd parser && uv run python image_extraction/integrate_game_images.py GAME
```

This automatically:

1. Copies `image_mappings/game_images.json` to `web/src/data/`
2. Updates `web/src/data/imageMap.ts` with necessary imports and registrations
3. Validates the setup

Then verify the build:

```bash
make build
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

### Integration script fails with "No such file or directory"

If `integrate_game_images.py` or the extraction creates files in the wrong location (e.g., `parser/web/` instead of project root `web/`), the path calculations in the scripts may be incorrect. After adding a new game configuration:

1. **Check output directory**: Images should go to `web/public/images/counters/{game}/` at the project root
2. **Verify paths**: Scripts in `parser/image_extraction/` need `.parent.parent.parent` to reach project root (up from `parser/image_extraction/` → `parser/` → project root)
3. **Manual integration**: If the integration script's regex fails, manually update `web/src/data/imageMap.ts`:
   - Add import: `import {game}Data from "./{game}_images.json";`
   - Add to `imageMap`: `{game}: {game}Data.matched_with_ext,`
   - Add to `counterTypeMap`: `{game}: ({game}Data as {{ counterType?: CounterType }}).counterType ?? 'template',`

## Related Files

- `parser/image_extraction/detect_counter_type.py` - Automatic counter type detection
- `parser/image_extraction/extract_images.py` - INDIVIDUAL (RTG2-style) extractor
- `parser/image_extraction/generate_counters.py` - Unified TEMPLATE_COMPOSITE generator (HCR, OTR2, GTC2, HSN)
- `parser/image_extraction/integrate_game_images.py` - Post-extraction integration automation
- `parser/image_mappings/*.json` - Generated mappings
- `parser/EXTRACT_IMAGES_QUICKSTART.md` - Quick reference cheat sheet
- `web/src/data/imageMap.ts` - TypeScript image map
