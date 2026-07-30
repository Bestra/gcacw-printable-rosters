import type { CSSProperties } from "react";
import type { Unit } from "../types";
import "./CommandCard.css";

export interface CommandCardUnit extends Pick<Unit, "name" | "type"> {
  scenarioLabel?: string;
}

interface CommandCardBaseProps {
  title: string;
  side: "confederate" | "union";
  commandColor: string;
  bodyColor?: string;
  footerColor: string;
  gameName: string;
  units: CommandCardUnit[];
  continuation?: boolean;
}

export type CommandCardProps = CommandCardBaseProps &
  (
    | { scenarioNumber: number; scenarioLabel?: never }
    | { scenarioNumber?: never; scenarioLabel: string }
  );

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
  if (side === "union") {
    const rows = [7, 7, 6, 7, 7];
    return (
      <svg
        className="command-card__flag"
        viewBox="0 0 52 32"
        role="img"
        aria-label="34-star United States flag"
      >
        <rect width="52" height="32" fill="#f4eee0" />
        {Array.from({ length: 7 }, (_, index) => (
          <rect key={index} y={index * 5} width="52" height="2.5" fill="#b52e31" />
        ))}
        <rect width="23" height="17.5" fill="#234579" />
        {rows.flatMap((count, row) =>
          Array.from({ length: count }, (_, column) => (
            <circle
              key={`${row}-${column}`}
              cx={2.2 + column * (18.6 / (count - 1))}
              cy={2.2 + row * 3.2}
              r="0.65"
              fill="#f4eee0"
            />
          )),
        )}
      </svg>
    );
  }

  const stars = Array.from({ length: 11 }, (_, index) => {
    const angle = (index / 11) * Math.PI * 2 - Math.PI / 2;
    return {
      x: 11.5 + Math.cos(angle) * 7,
      y: 10.5 + Math.sin(angle) * 7,
    };
  });

  return (
    <svg
      className="command-card__flag"
      viewBox="0 0 52 32"
      role="img"
      aria-label="11-star Confederate First National flag"
    >
      <rect width="52" height="32" fill="#b52e31" />
      <rect y="10.67" width="52" height="10.67" fill="#f4eee0" />
      <rect width="23" height="21.34" fill="#234579" />
      {stars.map((star, index) => (
        <circle key={index} cx={star.x} cy={star.y} r="0.9" fill="#f4eee0" />
      ))}
    </svg>
  );
}

export function CommandCard({
  title,
  side,
  commandColor,
  bodyColor,
  footerColor,
  gameName,
  scenarioNumber,
  scenarioLabel,
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
            <div className="command-card__counter-space" aria-label={`${unit.name} counter space`}>
              {unit.scenarioLabel && (
                <span className="command-card__counter-label">
                  {unit.scenarioLabel}
                </span>
              )}
            </div>
            <div className="command-card__counter-space" aria-label={`${unit.name} status space`} />
          </div>
        ))}
      </div>

      <footer className="command-card__footer">
        <span>{scenarioLabel ?? `Scenario ${scenarioNumber}`}</span>
        <span>{gameName}</span>
      </footer>
    </article>
  );
}
