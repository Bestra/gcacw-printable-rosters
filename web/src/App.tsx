import { useState, useEffect } from "react";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { RosterSheet } from "./components/RosterSheet";
import type { GameData } from "./types";
import "./App.css";

function App() {
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/otr2.json")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load game data");
        return res.json();
      })
      .then((data: GameData) => {
        setGameData(data);
        // Auto-select first scenario
        if (data.scenarios.length > 0) {
          setSelectedScenario(data.scenarios[0].number);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!gameData) {
    return <div className="loading">Loading...</div>;
  }

  const scenario = gameData.scenarios.find((s) => s.number === selectedScenario);

  return (
    <div className="app">
      <ScenarioSelector
        scenarios={gameData.scenarios}
        selectedNumber={selectedScenario}
        onSelect={setSelectedScenario}
      />
      {scenario && <RosterSheet scenario={scenario} gameName={gameData.name} />}
    </div>
  );
}

export default App;
