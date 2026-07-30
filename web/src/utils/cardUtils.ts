import type { Unit } from "../types";
import { getCardLayoutOverride } from "../data/cardLayoutConfig";
import { getUnitCounterColor } from "../data/counterColors";
import {
  buildCommandHierarchy,
  splitGroupIntoColumns,
  type CommandGroup,
} from "./rosterUtils";

export type CardSide = "confederate" | "union";

export interface ScenarioCommandCard {
  id: string;
  side: CardSide;
  commandCode: string;
  title: string;
  color: string;
  cardIndex: number;
  cardCount: number;
  units: Unit[];
}

const MAX_UNITS_PER_CARD = 6;
const FALLBACK_COLORS: Record<CardSide, string> = {
  confederate: "#d28b45",
  union: "#7aa9d3",
};

function flattenGroups(groups: CommandGroup[]): CommandGroup[] {
  const flattened: CommandGroup[] = [];

  for (const group of groups) {
    if (group.units.length > 0) {
      flattened.push({ ...group, subgroups: [] });
    }
    flattened.push(...flattenGroups(group.subgroups));
  }

  return flattened;
}

function commandColor(
  gameId: string,
  side: CardSide,
  units: Unit[],
): string {
  const counts = new Map<string, number>();

  for (const unit of units) {
    const color = getUnitCounterColor(gameId, side, unit.name);
    if (color) {
      counts.set(color, (counts.get(color) ?? 0) + 1);
    }
  }

  let selected = FALLBACK_COLORS[side];
  let selectedCount = 0;
  for (const [color, count] of counts) {
    if (count > selectedCount) {
      selected = color;
      selectedCount = count;
    }
  }
  return selected;
}

function generatedTitle(group: CommandGroup): string {
  if (group.commandCode === "-" || group.commandCode === "—") {
    return "Independent";
  }
  return group.leader
    ? `${group.commandCode} ${group.leader.name}`
    : group.commandCode;
}

function idPart(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function buildScenarioCards(
  gameId: string,
  scenarioNumber: number,
  side: CardSide,
  units: Unit[],
): ScenarioCommandCard[] {
  const eligibleUnits = units.filter((unit) => unit.type !== "Special");
  const groups = flattenGroups(buildCommandHierarchy(eligibleUnits));
  const orderedGroups = groups
    .map((group, sourceIndex) => ({
      group,
      sourceIndex,
      override: getCardLayoutOverride(
        gameId,
        scenarioNumber,
        side,
        group.commandCode,
      ),
    }))
    .sort((left, right) => {
      const leftOrder = left.override?.order ?? Number.MAX_SAFE_INTEGER;
      const rightOrder = right.override?.order ?? Number.MAX_SAFE_INTEGER;
      return leftOrder - rightOrder || left.sourceIndex - right.sourceIndex;
    });

  return orderedGroups.flatMap(({ group, override }) => {
    const color = override?.color ?? commandColor(gameId, side, group.units);
    const title = override?.title ?? generatedTitle(group);

    return splitGroupIntoColumns(group, MAX_UNITS_PER_CARD).map((splitGroup) => ({
      id: `${side}-${idPart(group.commandCode || "independent")}-${splitGroup.columnIndex ?? 1}`,
      side,
      commandCode: group.commandCode,
      title,
      color,
      cardIndex: splitGroup.columnIndex ?? 1,
      cardCount: splitGroup.totalColumns ?? 1,
      units: splitGroup.units,
    }));
  });
}
