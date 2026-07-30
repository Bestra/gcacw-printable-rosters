import type { CSSProperties } from "react";
import type { Unit } from "../types";
import "./CommandCard.css";

export interface CommandCardProps {
  title: string;
  side: "confederate" | "union";
  commandColor: string;
  bodyColor?: string;
  footerColor: string;
  gameName: string;
  scenarioNumber: number;
  units: Pick<Unit, "name" | "type">[];
  continuation?: boolean;
}

function UnitSymbol({ type }: { type: string }) {
  const normalizedType = type.toLowerCase();
  const symbolType = normalizedType.startsWith("cav")
    ? "cavalry"
    : normalizedType.startsWith("art")
      ? "artillery"
      : "infantry";

  return (
    <span className={`command-card__symbol command-card__symbol--${symbolType}`} aria-label={type}>
      {symbolType === "artillery" && <span className="command-card__artillery-dot" />}
    </span>
  );
}

function SideFlag({ side }: { side: CommandCardProps["side"] }) {
  return <span className={`command-card__flag command-card__flag--${side}`} aria-label={side} />;
}

export function CommandCard({
  title,
  side,
  commandColor,
  bodyColor,
  footerColor,
  gameName,
  scenarioNumber,
  units,
  continuation = false,
}: CommandCardProps) {
  const style = {
    "--command-color": commandColor,
    "--body-color": bodyColor ?? (side === "union" ? "#b9daea" : "#c8c8c4"),
    "--footer-color": footerColor,
  } as CSSProperties;

  return (
    <article className={`command-card command-card--${side}`} style={style}>
      <header className="command-card__header">
        <h3 className="command-card__title">
          {title}
          {continuation && <span className="command-card__continuation"> (cont.)</span>}
        </h3>
        <SideFlag side={side} />
      </header>

      <div className="command-card__units">
        {units.map((unit, index) => (
          <div className="command-card__unit" key={`${unit.name}-${index}`}>
            <div className="command-card__unit-label">
              <span className="command-card__unit-name">{unit.name}</span>
              <UnitSymbol type={unit.type} />
            </div>
            <div className="command-card__counter-space" aria-label={`${unit.name} counter space`} />
            <div className="command-card__counter-space" aria-label={`${unit.name} status space`} />
          </div>
        ))}
      </div>

      <footer className="command-card__footer">
        <span>Scenario {scenarioNumber}</span>
        <span>{gameName}</span>
      </footer>
    </article>
  );
}
