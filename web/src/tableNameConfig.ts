// Configuration for table name abbreviations
// Tables that are considered "default setup" should map to null (no display)
// Other tables map to abbreviated forms to append to hex location

export const TABLE_ABBREVIATIONS: Record<string, string | null> = {
  // Default setup tables - don't show anything
  "Confederate Set-Up": null,
  "Union Set-Up": null,
  
  // Army of the Potomac increments
  "Army Of The Potomac First Increment": "Inc 1",
  "Army Of The Potomac Second Increment": "Inc 2",
  "Army Of The Potomac Third Increment": "Inc 3",
  
  // Reinforcement tracks
  "Baltimore/Dc Reinforcement Track": "Balt",
  "Confederate Reinforcement Track": "Reinf",
  "Pennsylvania Militia Reinforcement Track": "PA Mil",
  "Richmond Garrison Track": "Rich",
  "West Virginia Reinforcement Track": "WV",
  
  // Special conditions
  "Placed Upon Stuart'S Arrival": "Stuart",
};

/**
 * Get the abbreviated table name to display, or null if it's a default setup table
 */
export function getTableAbbreviation(tableName: string | undefined): string | null {
  if (!tableName) return null;
  
  // Check for exact match
  if (tableName in TABLE_ABBREVIATIONS) {
    return TABLE_ABBREVIATIONS[tableName];
  }
  
  // Check for partial matches (case-insensitive)
  const lowerName = tableName.toLowerCase();
  
  // Default setup tables
  if (lowerName.includes("set-up") || lowerName.includes("setup")) {
    return null;
  }
  
  // Increment tables
  if (lowerName.includes("first increment")) return "Inc 1";
  if (lowerName.includes("second increment")) return "Inc 2";
  if (lowerName.includes("third increment")) return "Inc 3";
  if (lowerName.includes("fourth increment")) return "Inc 4";
  
  // Reinforcement tracks
  if (lowerName.includes("reinforcement")) {
    // Try to extract a short name
    const parts = tableName.split(/\s+/);
    if (parts.length >= 1) {
      return parts[0].substring(0, 6) + " Reinf";
    }
    return "Reinf";
  }
  
  // Unknown table - show abbreviated form
  const words = tableName.split(/\s+/);
  if (words.length <= 2) {
    return tableName;
  }
  // Take first letter of each word
  return words.map(w => w[0]).join("").toUpperCase();
}
