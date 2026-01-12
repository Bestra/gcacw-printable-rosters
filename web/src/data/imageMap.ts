// Import JSON mapping files directly - add new games here
import hcrData from "./hcr_images.json";
import rtg2Data from "./rtg2_images.json";
import otr2Data from "./otr2_images.json";
import gtc2Data from "./gtc2_images.json";

export type ImageMap = Record<string, Record<string, string>>;
export type CounterType = 'template' | 'individual';

// Build the map from imported JSON files
export const imageMap: ImageMap = {
  hcr: hcrData.matched_with_ext,
  rtg2: rtg2Data.matched_with_ext,
  otr2: otr2Data.matched_with_ext,
  gtc2: gtc2Data.matched_with_ext,
};

// Map of game to counter type
// 'template' = background image needs HTML text overlay
// 'individual' = pre-rendered images with text baked in
export const counterTypeMap: Record<string, CounterType> = {
  hcr: (hcrData as { counterType?: CounterType }).counterType ?? 'template',
  rtg2: (rtg2Data as { counterType?: CounterType }).counterType ?? 'individual',
  otr2: (otr2Data as { counterType?: CounterType }).counterType ?? 'template',
  gtc2: (gtc2Data as { counterType?: CounterType }).counterType ?? 'template',
};

/**
 * Get the counter type for a game.
 * @param game - Game code (e.g., "otr2")
 * @returns 'template' if needs HTML text overlay, 'individual' if text is pre-rendered
 */
export function getCounterType(game: string): CounterType {
  return counterTypeMap[game] ?? 'individual';
}

/**
 * Get the image filename for a unit.
 * @param game - Game code (e.g., "otr2")
 * @param side - "confederate" or "union"
 * @param unitName - The unit leader/name field
 * @returns The image filename or undefined if not found
 */
export function getUnitImage(
  game: string,
  side: "confederate" | "union",
  unitName: string
): string | undefined {
  const gameMap = imageMap[game];
  if (!gameMap) return undefined;
  const prefix = side === "confederate" ? "C" : "U";
  return gameMap[`${prefix}:${unitName}`];
}
