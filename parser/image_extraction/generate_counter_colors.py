"""Generate unit symbol colors from the counter images used by the web app."""

import colorsys
import json
from collections import Counter
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "web" / "src" / "data"
IMAGE_DIR = PROJECT_ROOT / "web" / "public" / "images" / "counters"
OUTPUT_PATH = DATA_DIR / "counter_colors.json"


def quantize(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(min(240, round(channel / 16) * 16) for channel in color)


def symbol_color(image_path: Path) -> str | None:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    symbol = image.crop(
        (
            round(width * 0.32),
            round(height * 0.38),
            round(width * 0.69),
            round(height * 0.56),
        )
    )

    saturated: list[tuple[int, int, int]] = []
    neutral: list[tuple[int, int, int]] = []
    for color in symbol.get_flattened_data():
        red, green, blue = color
        _, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        if value < 0.35 or value > 0.97:
            continue
        if saturation >= 0.35 and value >= 0.45:
            saturated.append(quantize(color))
        elif saturation < 0.15 and value <= 0.85:
            neutral.append(quantize(color))

    candidates = saturated if len(saturated) >= len(neutral) else neutral
    if not candidates:
        return None

    selected, _ = Counter(candidates).most_common(1)[0]
    return f"#{selected[0]:02x}{selected[1]:02x}{selected[2]:02x}"


def main() -> None:
    output: dict[str, dict[str, str]] = {}

    for mapping_path in sorted(DATA_DIR.glob("*_images.json")):
        game_id = mapping_path.stem.removesuffix("_images")
        mapping = json.loads(mapping_path.read_text())
        colors: dict[str, str] = {}

        for unit_key, filename in mapping.get("matched_with_ext", {}).items():
            image_path = IMAGE_DIR / game_id / filename
            if not image_path.exists():
                continue
            color = symbol_color(image_path)
            if color:
                colors[unit_key] = color

        output[game_id] = colors

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {sum(len(colors) for colors in output.values())} colors to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
