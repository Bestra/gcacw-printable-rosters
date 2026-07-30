import type { Scenario, Unit } from "../types";
import {
  getCardLayoutOverride,
  getRangeCommandConfig,
} from "../data/cardLayoutConfig";
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

export interface RangeCardUnit {
  unit: Unit;
  identity: string;
  scenarioNumbers: number[];
  scenarioLabel?: string;
}

export interface RangeCommandCard {
  id: string;
  side: CardSide;
  commandCode: string;
  title: string;
  color: string;
  cardIndex: number;
  cardCount: number;
  units: RangeCardUnit[];
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

export function normalizeCardCommand(command: string): string {
  const trimmed = command.trim();
  return trimmed === "" || trimmed === "-" || trimmed === "—" || trimmed === "(-)"
    ? "-"
    : trimmed;
}

function normalizedIdentityPart(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function getPhysicalUnitIdentity(side: CardSide, unit: Unit): string {
  return [
    side,
    normalizedIdentityPart(unit.name),
    normalizedIdentityPart(unit.type),
    normalizedIdentityPart(unit.size),
  ].join(":");
}

export function formatScenarioNumbers(numbers: number[]): string {
  if (numbers.length === 0) {
    return "";
  }

  const ranges: string[] = [];
  let start = numbers[0];
  let end = start;

  for (const number of numbers.slice(1)) {
    if (number === end + 1) {
      end = number;
      continue;
    }
    ranges.push(start === end ? `${start}` : `${start}-${end}`);
    start = number;
    end = number;
  }
  ranges.push(start === end ? `${start}` : `${start}-${end}`);
  return `S${ranges.join(",")}`;
}

function balancedChunks<T>(items: T[], capacity: number): T[][] {
  const chunkCount = Math.ceil(items.length / capacity);
  if (chunkCount === 0) {
    return [];
  }

  const baseSize = Math.floor(items.length / chunkCount);
  const largerChunkCount = items.length % chunkCount;
  const chunks: T[][] = [];
  let offset = 0;

  for (let index = 0; index < chunkCount; index += 1) {
    const size = baseSize + (index < largerChunkCount ? 1 : 0);
    chunks.push(items.slice(offset, offset + size));
    offset += size;
  }
  return chunks;
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

interface RangePlacement {
  unit: Unit;
  identity: string;
  scenarioNumbers: Set<number>;
  sourceIndex: number;
}

interface RangeCommandGroup {
  commandCode: string;
  placements: Map<string, RangePlacement>;
  leaderNames: Set<string>;
  sourceIndex: number;
}

function rangeTitle(commandCode: string, leaderNames: Set<string>): string {
  if (commandCode === "-") {
    return "Independent";
  }
  if (leaderNames.size === 1) {
    return `${commandCode} ${Array.from(leaderNames)[0]}`;
  }
  return commandCode;
}

export function buildRangeCards(
  gameId: string,
  scenarios: Scenario[],
  side: CardSide,
): RangeCommandCard[] {
  const groups = new Map<string, RangeCommandGroup>();
  let sourceIndex = 0;

  for (const scenario of scenarios) {
    const units = scenario[`${side}Units`];
    const leadersByCommand = new Map<string, Set<string>>();

    for (const leader of units.filter((unit) => unit.type === "Ldr")) {
      const command = normalizeCardCommand(leader.command);
      if (command === "-") {
        continue;
      }
      const names = leadersByCommand.get(command) ?? new Set<string>();
      names.add(leader.name);
      leadersByCommand.set(command, names);
    }

    for (const unit of units) {
      if (unit.type === "Ldr" || unit.type === "Special") {
        continue;
      }

      const commandCode = normalizeCardCommand(unit.command);
      const identity = getPhysicalUnitIdentity(side, unit);
      let group = groups.get(commandCode);
      if (!group) {
        group = {
          commandCode,
          placements: new Map(),
          leaderNames: new Set(),
          sourceIndex: sourceIndex++,
        };
        groups.set(commandCode, group);
      }

      for (const leaderName of leadersByCommand.get(commandCode) ?? []) {
        group.leaderNames.add(leaderName);
      }

      const existing = group.placements.get(identity);
      if (existing) {
        existing.scenarioNumbers.add(scenario.number);
      } else {
        group.placements.set(identity, {
          unit,
          identity,
          scenarioNumbers: new Set([scenario.number]),
          sourceIndex: sourceIndex++,
        });
      }
    }
  }

  const orderedGroups = Array.from(groups.values())
    .map((group) => ({
      group,
      config: getRangeCommandConfig(gameId, side, group.commandCode),
    }))
    .sort((left, right) => {
      const leftOrder = left.config?.order ?? Number.MAX_SAFE_INTEGER;
      const rightOrder = right.config?.order ?? Number.MAX_SAFE_INTEGER;
      return leftOrder - rightOrder || left.group.sourceIndex - right.group.sourceIndex;
    });

  return orderedGroups.flatMap(({ group, config }) => {
    const placements = Array.from(group.placements.values())
      .sort((left, right) => left.sourceIndex - right.sourceIndex)
      .map((placement): RangeCardUnit => {
        const scenarioNumbers = Array.from(placement.scenarioNumbers).sort(
          (left, right) => left - right,
        );
        return {
          unit: placement.unit,
          identity: placement.identity,
          scenarioNumbers,
          scenarioLabel: formatScenarioNumbers(scenarioNumbers),
        };
      });
    const chunks = balancedChunks(placements, MAX_UNITS_PER_CARD);
    const color =
      config?.color ??
      commandColor(
        gameId,
        side,
        placements.map((placement) => placement.unit),
      );
    const title =
      config?.title ?? rangeTitle(group.commandCode, group.leaderNames);

    return chunks.map((units, index) => ({
      id: `${side}-${idPart(group.commandCode || "independent")}-${index + 1}`,
      side,
      commandCode: group.commandCode,
      title,
      color,
      cardIndex: index + 1,
      cardCount: chunks.length,
      units,
    }));
  });
}
