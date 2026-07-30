import type { Scenario } from "../types";
import {
  buildRangeCards,
  type CardSide,
  type RangeCommandCard,
} from "../utils/cardUtils";
import { CommandCard } from "./CommandCard";
import "./ScenarioCardSheet.css";
import "./RangeCardSheet.css";

interface RangeCardSheetProps {
  scenarios: Scenario[];
  gameName: string;
  gameId: string;
  confederateBodyColor: string;
  unionBodyColor: string;
}

const FOOTER_COLOR = "#315d46";

function scenarioRangeLabel(scenarios: Scenario[]): string {
  const first = scenarios[0].number;
  const last = scenarios[scenarios.length - 1].number;
  return first === last ? `Scenario ${first}` : `Scenarios ${first}-${last}`;
}

function sideCards(
  gameId: string,
  scenarios: Scenario[],
  side: CardSide,
): RangeCommandCard[] {
  return buildRangeCards(gameId, scenarios, side);
}

function CardSection({
  side,
  cards,
  bodyColor,
  gameName,
  footerLabel,
}: {
  side: CardSide;
  cards: RangeCommandCard[];
  bodyColor: string;
  gameName: string;
  footerLabel: string;
}) {
  return (
    <section className={`scenario-card-sheet__side scenario-card-sheet__side--${side}`}>
      <h2 className="scenario-card-sheet__side-title no-print">
        {side === "confederate" ? "Confederate" : "Union"}
      </h2>
      <div className="scenario-card-sheet__cards">
        {cards.map((card) => (
          <CommandCard
            key={card.id}
            title={card.title}
            side={card.side}
            commandColor={card.color}
            bodyColor={bodyColor}
            footerColor={FOOTER_COLOR}
            gameName={gameName}
            scenarioLabel={footerLabel}
            units={card.units.map((entry) => ({
              name: entry.unit.name,
              type: entry.unit.type,
              scenarioLabel: entry.scenarioLabel,
            }))}
            continuation={card.cardIndex > 1}
          />
        ))}
      </div>
    </section>
  );
}

export function RangeCardSheet({
  scenarios,
  gameName,
  gameId,
  confederateBodyColor,
  unionBodyColor,
}: RangeCardSheetProps) {
  const confederateCards = sideCards(gameId, scenarios, "confederate");
  const unionCards = sideCards(gameId, scenarios, "union");
  const cards = [...confederateCards, ...unionCards];
  const units = cards.flatMap((card) => card.units);
  const physicalUnitCount = new Set(units.map((unit) => unit.identity)).size;
  const duplicatedSlotCount = units.length - physicalUnitCount;
  const duplicatedSlotLabel =
    duplicatedSlotCount === 1 ? "moving-command slot" : "moving-command slots";
  const footerLabel = scenarioRangeLabel(scenarios);

  return (
    <div className="scenario-card-sheet range-card-sheet">
      <header className="scenario-card-sheet__header no-print">
        {gameName} — Reusable Deck: {footerLabel}
      </header>
      <div className="range-card-sheet__summary no-print">
        <span>{physicalUnitCount} physical units</span>
        <span>{cards.length} cards</span>
        <span>{duplicatedSlotCount} {duplicatedSlotLabel}</span>
      </div>

      <CardSection
        side="confederate"
        cards={confederateCards}
        bodyColor={confederateBodyColor}
        gameName={gameName}
        footerLabel={footerLabel}
      />
      <CardSection
        side="union"
        cards={unionCards}
        bodyColor={unionBodyColor}
        gameName={gameName}
        footerLabel={footerLabel}
      />
    </div>
  );
}
