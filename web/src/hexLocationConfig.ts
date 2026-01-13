/**
 * Hex location parsing using shared configuration.
 * The source of truth is parser/utils/hex_location_config.json
 */

import configJson from "../../parser/utils/hex_location_config.json";

interface PatternConfig {
  _comment?: string;
  type: string;
  regex: string;
  hexCodeTemplate?: string;
  hexCodeGroups?: number[];
  locationGroup?: number;
}

interface Config {
  gameMapPrefixes: string[];
  boxAbbreviations: Record<string, string>;
  locationAbbreviations: Record<string, string>;
  specialLocations: Record<string, { hexCode: string; locationName: string | null }>;
  patterns: PatternConfig[];
  knownUnparseable: string[];
}

const CONFIG = configJson as Config;

function applyTemplate(template: string, match: RegExpMatchArray): string {
  let result = template;
  for (let i = 1; i <= 9; i++) {
    const placeholder = `{${i}}`;
    if (result.includes(placeholder)) {
      result = result.replace(placeholder, match[i] || "");
    }
  }
  return result.trim();
}

function applyAbbreviations(text: string): string {
  let result = text;
  for (const [full, abbrev] of Object.entries(CONFIG.locationAbbreviations)) {
    result = result.replace(new RegExp(full, "gi"), abbrev);
  }
  return result;
}

/**
 * Parse a hex location string into display components.
 */
export function parseHexLocation(hexLocation: string): { hexCode: string; locationName?: string } {
  if (!hexLocation || !hexLocation.trim()) {
    return { hexCode: "" };
  }

  hexLocation = hexLocation.trim();

  // Check for known unparseable strings
  for (const unparseable of CONFIG.knownUnparseable) {
    if (hexLocation.toLowerCase().includes(unparseable.toLowerCase())) {
      return { hexCode: hexLocation.substring(0, 20) + "..." };
    }
  }

  // Check for exact match in special locations
  for (const [pattern, result] of Object.entries(CONFIG.specialLocations)) {
    if (hexLocation.toLowerCase() === pattern.toLowerCase()) {
      return { hexCode: result.hexCode, locationName: result.locationName || undefined };
    }
  }

  // Try each pattern in order
  for (const patternConfig of CONFIG.patterns) {
    const flags = patternConfig.type === "hex" ? "" : "i";
    const regex = new RegExp(patternConfig.regex, flags);
    const match = hexLocation.match(regex);

    if (match) {
      const patternType = patternConfig.type;

      if (patternType === "hex") {
        // Build hex code from groups
        const groups = patternConfig.hexCodeGroups || [];
        const hexCode = groups.map(g => match[g] || "").join("").trim();
        
        // Get location name
        const locGroup = patternConfig.locationGroup;
        let locationName = locGroup && match[locGroup] ? match[locGroup] : undefined;
        
        if (locationName) {
          locationName = applyAbbreviations(locationName);
        }
        
        return { hexCode, locationName };
      }
      
      if (patternType === "box") {
        const template = patternConfig.hexCodeTemplate || "{1} Box";
        let hexCode = applyTemplate(template, match);
        
        // Check for box abbreviations
        hexCode = CONFIG.boxAbbreviations[hexCode] || hexCode;
        
        return { hexCode };
      }
      
      if (patternType === "dateReinforcement" || patternType === "namedReinforcement" || patternType === "plainReinforcement") {
        const template = patternConfig.hexCodeTemplate || "{1} Reinf.";
        const hexCode = applyTemplate(template, match);
        return { hexCode };
      }
      
      if (patternType === "radius") {
        const template = patternConfig.hexCodeTemplate || "{1} hex radius";
        const hexCode = applyTemplate(template, match);
        
        const locGroup = patternConfig.locationGroup;
        let locationName = locGroup && match[locGroup] ? match[locGroup] : undefined;
        
        if (locationName) {
          locationName = applyAbbreviations(locationName);
        }
        
        return { hexCode, locationName };
      }
      
      // Generic handler for other pattern types (county, near, etc.)
      const template = patternConfig.hexCodeTemplate || "{1}";
      const hexCode = applyTemplate(template, match);
      
      const locGroup = patternConfig.locationGroup;
      let locationName = locGroup && match[locGroup] ? match[locGroup] : undefined;
      
      if (locationName) {
        locationName = applyAbbreviations(locationName);
      }
      
      return { hexCode, locationName };
    }
  }

  // Fallback: use first word, check for parenthetical
  const locMatch = hexLocation.match(/\(([^)]+)\)/);
  return {
    hexCode: hexLocation.split(" ")[0],
    locationName: locMatch ? locMatch[1] : undefined,
  };
}
