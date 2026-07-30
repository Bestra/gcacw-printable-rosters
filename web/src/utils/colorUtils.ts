function channelLuminance(channel: number): number {
  const normalized = channel / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hexColor: string): number | null {
  const match = hexColor.match(/^#([0-9a-f]{6})$/i);
  if (!match) {
    return null;
  }

  const value = match[1];
  const red = parseInt(value.slice(0, 2), 16);
  const green = parseInt(value.slice(2, 4), 16);
  const blue = parseInt(value.slice(4, 6), 16);

  return (
    0.2126 * channelLuminance(red) +
    0.7152 * channelLuminance(green) +
    0.0722 * channelLuminance(blue)
  );
}

function contrastRatio(left: number, right: number): number {
  const lighter = Math.max(left, right);
  const darker = Math.min(left, right);
  return (lighter + 0.05) / (darker + 0.05);
}

export function getContrastingTextColor(backgroundColor: string): string {
  const backgroundLuminance = relativeLuminance(backgroundColor);
  if (backgroundLuminance === null) {
    return "#151515";
  }

  const darkLuminance = relativeLuminance("#151515") ?? 0;
  const lightLuminance = relativeLuminance("#ffffff") ?? 1;
  return contrastRatio(backgroundLuminance, lightLuminance) >
    contrastRatio(backgroundLuminance, darkLuminance)
    ? "#ffffff"
    : "#151515";
}
