import type { Scenario } from "../types";
import "./ScenarioSelector.css";

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  selectedNumber: number | null;
  onSelect: (number: number) => void;
}

export function ScenarioSelector({
  scenarios,
  selectedNumber,
  onSelect,
}: ScenarioSelectorProps) {
  return (
    <div className="scenario-selector no-print">
      <label htmlFor="scenario-select">Select Scenario:</label>
      <select
        id="scenario-select"
        value={selectedNumber ?? ""}
        onChange={(e) => onSelect(Number(e.target.value))}
      >
        <option value="" disabled>
          Choose a scenario...
        </option>
        {scenarios.map((s) => (
          <option key={s.number} value={s.number}>
            {s.number}. {s.name}
          </option>
        ))}
      </select>
    </div>
  );
}
