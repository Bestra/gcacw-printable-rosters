# TPC Image Extraction Handoff

## Goal
Bring in more missing counter images for TPC (The Petersburg Campaign).

## Current State

### VMOD Location
`/Users/bestra/Documents/vasl/gcacw/TPC_3_09.vmod`

### Counter Type
TPC uses **TEMPLATE_COMPOSITE** system:
- Units use generic background images with text labels overlaid by VASSAL
- Leaders have dedicated image files
- 63% of units use text labels, 33% share images

### Current Mapping Stats
From `parser/image_extraction/image_mappings/tpc_images.json`:
- **Matched**: ~140 units
- **Unmatched**: 47 units

### Key Unmatched Units

**Union Leaders** (need images):
- Butler, DM Gregg, Hancock-B, Humphreys-B, Kautz, Mackenzie, Ord, Parke-B, Sheridan, Torbert, Warren-B, Weitzel, Wright-B

**Union Infantry**:
- Bartlett, Birney-25th, Devens-24th, Hartsuff, Kautz-25th, S. Griffin, Turner-24th, W. Birney

**Confederate Leaders**:
- AP Hill

**Confederate Infantry**:
- Benning, Bratton, Clingman, Colquit, Colquitt, Corse, DuBose, Elliott, Fulton, GT Anderson, Gracie-J, Gregg, Hagood, Hardaway (Art), Henagan, Hunton, Martin, Montague, Perry, Ransom, Simms, Stansel, Steuart-B, Terry, Wallace, Wise

## Investigation Findings

### Dry-Run Output Showed
The `generate_counters.py` dry-run revealed:
1. **Union Leaders incorrectly classified as Confederate** in the mappings - Birney II, Butler, Custer, DM Gregg, Gibbon, etc. are showing up under Confederate Leaders
2. Only 7 Union leaders detected vs 54 Confederate leaders (clearly wrong ratio)
3. The `tpc_extract_unit_mappings()` function's leader detection logic needs improvement

### Root Cause (Suspected)
The TPC configuration in `generate_counters.py` has leader classification issues:
- The `union_leaders` list in `tpc_extract_unit_mappings()` is incomplete
- Some leaders are falling through to Confederate classification due to fallback logic

## Next Steps

1. **Extract the VMOD** to inspect images directly:
   ```bash
   mkdir -p /tmp/tpc_vmod
   unzip -o "/Users/bestra/Documents/vasl/gcacw/TPC_3_09.vmod" -d /tmp/tpc_vmod
   ls /tmp/tpc_vmod/images/ | grep -iE '^(UL|CL)' | head -50
   ```

2. **Examine buildFile.xml** to understand leader naming patterns:
   ```bash
   grep -o 'entryName="[^"]*".*piece;;;[^;]*;' /tmp/tpc_vmod/buildFile.xml | grep -i leader | head -30
   ```

3. **Fix the TPC configuration** in `generate_counters.py`:
   - Update `union_leaders` list with missing names
   - Improve image filename pattern detection (UL- vs CL- prefixes)
   - May need to look at image filenames rather than entry names

4. **Re-run generation**:
   ```bash
   cd parser && uv run python image_extraction/generate_counters.py tpc "/Users/bestra/Documents/vasl/gcacw/TPC_3_09.vmod"
   ```

5. **Integrate and verify**:
   ```bash
   cd parser && uv run python image_extraction/integrate_game_images.py tpc
   make build
   ```

## Key Files
- `parser/image_extraction/generate_counters.py` - TPC config at `TPC_CONFIG` and `tpc_extract_unit_mappings()`
- `parser/image_extraction/image_mappings/tpc_images.json` - Current mappings
- `parser/parsed/tpc_parsed.json` - Parsed unit data (source of truth for unit names)
- `web/public/images/counters/tpc/` - Output image directory
