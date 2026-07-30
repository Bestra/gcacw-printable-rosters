export interface CardLayoutOverride {
  title?: string;
  color?: string;
  order?: number;
}

export interface RangeCommandConfig {
  title?: string;
  order?: number;
  color?: string;
}

const cardLayoutConfig: Record<string, CardLayoutOverride> = {
  "aga:5:confederate:P": {
    title: "P Beauregard",
    order: 1,
  },
  "aga:5:confederate:S": {
    title: "S Johnston",
    order: 2,
  },
};

const rangeCommandConfig: Record<string, RangeCommandConfig> = {
  "aga:confederate:P": {
    title: "P Beauregard",
    order: 1,
  },
  "aga:confederate:S": {
    title: "S Johnston",
    order: 2,
  },
};

export function getCardLayoutOverride(
  gameId: string,
  scenarioNumber: number,
  side: "confederate" | "union",
  commandCode: string,
): CardLayoutOverride | undefined {
  return cardLayoutConfig[`${gameId}:${scenarioNumber}:${side}:${commandCode}`];
}

export function getRangeCommandConfig(
  gameId: string,
  side: "confederate" | "union",
  commandCode: string,
): RangeCommandConfig | undefined {
  return rangeCommandConfig[`${gameId}:${side}:${commandCode}`];
}
