export interface CardLayoutOverride {
  title?: string;
  color?: string;
  order?: number;
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

export function getCardLayoutOverride(
  gameId: string,
  scenarioNumber: number,
  side: "confederate" | "union",
  commandCode: string,
): CardLayoutOverride | undefined {
  return cardLayoutConfig[`${gameId}:${scenarioNumber}:${side}:${commandCode}`];
}
