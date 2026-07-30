import counterColors from "./counter_colors.json";

type Side = "confederate" | "union";
type CounterColors = Record<string, Record<string, string>>;

const colors = counterColors as CounterColors;

export function getUnitCounterColor(
  gameId: string,
  side: Side,
  unitName: string,
): string | undefined {
  const prefix = side === "confederate" ? "C" : "U";
  return colors[gameId]?.[`${prefix}:${unitName}`];
}
