import type { Scenario } from "../types";

export interface NormalizedScenarioRange {
  from: number;
  to: number;
  scenarios: Scenario[];
}

export function normalizeScenarioRange(
  scenarios: Scenario[],
  requestedFrom: number | null,
  requestedTo: number | null,
): NormalizedScenarioRange {
  const requestedFirstIndex = scenarios.findIndex(
    (scenario) => scenario.number === requestedFrom,
  );
  const requestedLastIndex = scenarios.findIndex(
    (scenario) => scenario.number === requestedTo,
  );
  const firstIndex = requestedFirstIndex >= 0 ? requestedFirstIndex : 0;
  const lastIndex =
    requestedLastIndex >= 0 ? requestedLastIndex : scenarios.length - 1;
  const fromIndex = Math.min(firstIndex, lastIndex);
  const toIndex = Math.max(firstIndex, lastIndex);

  return {
    from: scenarios[fromIndex].number,
    to: scenarios[toIndex].number,
    scenarios: scenarios.slice(fromIndex, toIndex + 1),
  };
}

export function copyCardPaletteParams(
  source: URLSearchParams,
  destination: URLSearchParams,
) {
  for (const param of ["confederateColor", "unionColor"]) {
    const value = source.get(param);
    if (value) {
      destination.set(param, value);
    }
  }
}
