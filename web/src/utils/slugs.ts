/**
 * Mapping from game IDs to roman numeral route slugs
 */
const gameIdToSlug: Record<string, string> = {
  otr2: "OTRII",
  gtc2: "GTCII",
  hsn: "HSN",
  hcr: "HCR",
};

const slugToGameId: Record<string, string> = {
  otrii: "otr2",
  gtcii: "gtc2",
  hsn: "hsn",
  hcr: "hcr",
};

/**
 * Convert a game ID (e.g., "otr2") to a route slug (e.g., "OTRII")
 */
export function getGameSlug(gameId: string): string {
  return gameIdToSlug[gameId] || gameId.toUpperCase();
}

/**
 * Convert a route slug (e.g., "OTRII") to a game ID (e.g., "otr2")
 * Case-insensitive lookup
 */
export function getGameIdFromSlug(slug: string): string | null {
  return slugToGameId[slug.toLowerCase()] || null;
}

/**
 * Convert a scenario name to a URL-friendly slug
 * e.g., "Gaines' Mill" -> "gaines-mill"
 */
export function slugifyScenarioName(name: string): string {
  return name
    .toLowerCase()
    .replace(/['']/g, "") // Remove apostrophes
    .replace(/[^a-z0-9]+/g, "-") // Replace non-alphanumeric with dashes
    .replace(/^-+|-+$/g, ""); // Trim leading/trailing dashes
}

/**
 * Create a full scenario slug with number and name
 * e.g., (7, "Gaines' Mill") -> "7-gaines-mill"
 */
export function getScenarioSlug(scenarioNumber: number, scenarioName: string): string {
  const nameSlug = slugifyScenarioName(scenarioName);
  return `${scenarioNumber}-${nameSlug}`;
}

/**
 * Extract the scenario number from a scenario slug
 * e.g., "7-gaines-mill" -> 7
 */
export function getScenarioNumberFromSlug(slug: string): number | null {
  const match = slug.match(/^(\d+)/);
  if (match) {
    return parseInt(match[1], 10);
  }
  return null;
}
