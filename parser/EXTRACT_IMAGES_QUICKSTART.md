# VASSAL Counter Image Extraction - Quick Start

**30-second workflow for extracting counter images from a VASSAL module.**

## Prerequisites

- Game parsed: `parser/parsed/{game}_parsed.json` exists
- VASSAL module: `/path/to/GAME.vmod` file available

## 3-Step Workflow

### Step 1: Detect Counter Type

```bash
cd parser && uv run python detect_counter_type.py /path/to/GAME.vmod
```

**Output tells you:**

- `TEMPLATE_COMPOSITE` → Use `generate_counters.py` (HCR, OTR2, GTC2, HSN style)
- `INDIVIDUAL` → Use `extract_images.py` (RTG2 style)

### Step 2A: For TEMPLATE_COMPOSITE Games

If the game is already configured (check `GAME_CONFIGS` in `generate_counters.py`):

```bash
cd parser && uv run python generate_counters.py GAME /path/to/GAME.vmod
```

**If NOT configured yet**, add to `generate_counters.py`:

```python
# Add after existing configs, before "Game registry"

def game_get_name_variants(name: str) -> list[str]:
    """Generate variants of a name for fuzzy matching (GAME-specific)."""
    variants = base_get_name_variants(name)

    # Add game-specific typos, spelling variants, etc.
    # Example: Handle "O'Neill" vs "O Neill"
    if "O'Neill" in name or "O Neill" in name:
        variants.extend(["O'Neill", "O Neill", "ONeill"])

    return list(set(variants))

def game_extract_unit_mappings(buildfile_path: Path) -> dict:
    """Parse buildFile.xml to extract unit-to-background mappings for GAME."""
    content = buildfile_path.read_text(encoding='utf-8', errors='ignore')

    mappings = {
        "Union": {},
        "Confederate": {},
        "Leaders": {"Union": {}, "Confederate": {}}
    }

    slot_pattern = r'<VASSAL\.build\.widget\.PieceSlot\s+entryName="([^"]+)"[^>]*>([^<]*)</VASSAL\.build\.widget\.PieceSlot>'

    for match in re.finditer(slot_pattern, content, re.DOTALL):
        entry_name = match.group(1)
        slot_content = match.group(2)

        image_match = re.search(r'piece;;;([^;]+\.jpg);[^/]+/', slot_content, re.IGNORECASE)
        if not image_match:
            continue
        image_file = image_match.group(1)

        # Skip markers
        if any(skip in entry_name.lower() for skip in ['vp', 'wagon', 'control']):
            continue

        if 'prototype;Leader' in slot_content:
            # Detect leader side by image prefix or known names
            if image_file.startswith('UL_'):
                mappings["Leaders"]["Union"][entry_name] = image_file
            elif image_file.startswith('CL_'):
                mappings["Leaders"]["Confederate"][entry_name] = image_file
        else:
            type_match = re.search(r'prototype;(USA|CSA)\s+(Infantry|Cavalry)\s+(Division|Brigade|Regiment)', slot_content)
            if type_match:
                side = "Union" if type_match.group(1) == "USA" else "Confederate"
                unit_type = f"{type_match.group(2)} {type_match.group(3)}"
                mappings[side][entry_name] = {
                    "image": image_file,
                    "type": unit_type
                }

    return mappings

GAME_CONFIG = GameConfig(
    game_id='game',
    name_variants_fn=game_get_name_variants,
    extract_mappings_fn=game_extract_unit_mappings,
)

# Then update GAME_CONFIGS dict:
GAME_CONFIGS: dict[str, GameConfig] = {
    'gtc2': GTC2_CONFIG,
    'hcr': HCR_CONFIG,
    'otr2': OTR2_CONFIG,
    'hsn': HSN_CONFIG,
    'game': GAME_CONFIG,  # Add your game
}
```

### Step 2B: For INDIVIDUAL Games

```bash
cd parser && uv run python extract_images.py GAME /path/to/GAME.vmod
```

(May need to add game-specific patterns to `extract_images.py`)

### Step 3: Integrate into Web App

```bash
cd parser && uv run python integrate_game_images.py GAME
```

This automatically:

- Copies `image_mappings/game_images.json` to `web/src/data/`
- Updates `web/src/data/imageMap.ts` with imports and registrations

### Step 4: Verify Build

```bash
cd web && npm run build
```

### Step 5: Validate Setup (Optional)

```bash
cd parser && uv run python validate_game_images.py GAME
# Or check all games:
cd parser && uv run python validate_game_images.py --all
```

## Troubleshooting

### High Unmatched Count

**Problem**: "Unmatched: 45 units"

**Solutions**:

1. Check for typos in VASSAL: `grep -i "unit_name" /tmp/extracted/buildFile.xml`
2. Add name variants to `*_get_name_variants()` function
3. Check for number suffixes: "Cooper 12" needs handling
4. Check for qualifiers: "Thompson (USCT)" needs handling

### Missing Background Images

**Problem**: "Missing: CSA_III_34.jpg for Smith"

**Check**:

```bash
ls /tmp/extracted/images/ | grep -i "III"
```

The background might have a different naming pattern. Update `extract_mappings_fn` to match.

### Wrong Counter Type Detected

**Problem**: detect_counter_type says INDIVIDUAL but should be TEMPLATE

**Manual Override**: Look at sample images:

```bash
ls /tmp/extracted/images/ | head -20
```

If backgrounds are generic (like `UUU-XX1.jpg`), use TEMPLATE approach even if detected as INDIVIDUAL.

## Common Name Variants Patterns

```python
# Number suffixes: "Cooper 12" -> "Cooper"
if ' ' in name and name.split()[-1].isdigit():
    variants.append(' '.join(name.split()[:-1]))

# Initials: "R Johnson" -> "R. Johnson", "RJohnson"
if re.match(r'^[A-Z]\s', name):
    base = name[2:]
    variants.append(f"{name[0]}. {base}")
    variants.append(f"{name[0]}{base}")

# Suffixes: "Lowrey" -> "Lowrey - A", "Lowrey-A"
if 'Lowrey' in name:
    variants.extend(['Lowrey', 'Lowrey - A', 'Lowrey-A'])

# Special markers: "Lyon#" -> "Lyon"
if name.endswith('#'):
    variants.append(name[:-1])

# Qualifiers: "Thompson (USCT)" -> "Thompson"
if '(USCT)' in name:
    variants.append(name.replace('(USCT)', '').strip())
```

## Reference Files

- **Full documentation**: `.github/skills/extract-vassal-images/SKILL.md`
- **Counter detection**: `parser/detect_counter_type.py`
- **Template generator**: `parser/generate_counters.py`
- **Individual extractor**: `parser/extract_images.py`
- **Integration helper**: `parser/integrate_game_images.py`
- **Validation script**: `parser/validate_game_images.py`
