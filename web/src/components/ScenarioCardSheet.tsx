import type { Scenario } from "../types";
import { buildScenarioCards } from "../utils/cardUtils";
import { CommandCard } from "./CommandCard";
import "./ScenarioCardSheet.css";

interface ScenarioCardSheetProps {
  scenario: Scenario;
  gameName: string;
  gameId: string;
  confederateBodyColor: string;
  unionBodyColor: string;
}

const FOOTER_COLOR = "#315d46";

export function ScenarioCardSheet({
  scenario,
  gameName,
  gameId,
  confederateBodyColor,
  unionBodyColor,
}: ScenarioCardSheetProps) {
  const confederateCards = buildScenarioCards(
    gameId,
    scenario.number,
    "confederate",
    scenario.confederateUnits,
  );
  const unionCards = buildScenarioCards(
    gameId,
    scenario.number,
    "union",
    scenario.unionUnits,
  );

  return (
    <div className="scenario-card-sheet">
      <header className="scenario-card-sheet__header no-print">
        {gameName} — Scenario {scenario.number}: {scenario.name}
      </header>

      <section className="scenario-card-sheet__side scenario-card-sheet__side--confederate">
        <h2 className="scenario-card-sheet__side-title no-print">Confederate</h2>
        <div className="scenario-card-sheet__cards">
          {confederateCards.map((card) => (
            <CommandCard
              key={card.id}
              title={card.title}
              side={card.side}
              commandColor={card.color}
              bodyColor={confederateBodyColor}
              footerColor={FOOTER_COLOR}
              gameName={gameName}
              scenarioNumber={scenario.number}
              units={card.units}
              continuation={card.cardIndex > 1}
            />
          ))}
        </div>
      </section>

      <section className="scenario-card-sheet__side scenario-card-sheet__side--union">
        <h2 className="scenario-card-sheet__side-title no-print">Union</h2>
        <div className="scenario-card-sheet__cards">
          {unionCards.map((card) => (
            <CommandCard
              key={card.id}
              title={card.title}
              side={card.side}
              commandColor={card.color}
              bodyColor={unionBodyColor}
              footerColor={FOOTER_COLOR}
              gameName={gameName}
              scenarioNumber={scenario.number}
              units={card.units}
              continuation={card.cardIndex > 1}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
