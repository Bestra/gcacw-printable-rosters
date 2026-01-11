import { useState, useEffect } from "react";
import { GameSelector } from "./components/GameSelector";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { RosterSheet } from "./components/RosterSheet";
import type { GameData, GameInfo, GamesIndex } from "./types";
import "./App.css";

function App() {
  const [games, setGames] = useState<GameInfo[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load games index on mount
  useEffect(() => {
    fetch("/data/games.json")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load games index");
        return res.json();
      })
      .then((data: GamesIndex) => {
        setGames(data.games);
        // Auto-select first game
        if (data.games.length > 0) {
          setSelectedGameId(data.games[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Load game data when game selection changes
  useEffect(() => {
    if (!selectedGameId) return;

    const game = games.find((g) => g.id === selectedGameId);
    if (!game) return;

    setLoading(true);
    setGameData(null);
    setSelectedScenario(null);

    fetch(`/data/${game.file}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load ${game.name} data`);
        return res.json();
      })
      .then((data: GameData) => {
        setGameData(data);
        // Auto-select first scenario
        if (data.scenarios.length > 0) {
          setSelectedScenario(data.scenarios[0].number);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedGameId, games]);

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (loading && games.length === 0) {
    return <div className="loading">Loading...</div>;
  }

  const scenario = gameData?.scenarios.find((s) => s.number === selectedScenario);

  return (
    <div className="app">
      <div className="selectors no-print">
        <GameSelector
          games={games}
          selectedGameId={selectedGameId}
          onSelect={setSelectedGameId}
        />
        {gameData && (
          <ScenarioSelector
            scenarios={gameData.scenarios}
            selectedNumber={selectedScenario}
            onSelect={setSelectedScenario}
          />
        )}
      </div>
      {loading && <div className="loading">Loading game data...</div>}
      {scenario && gameData && (
        <RosterSheet scenario={scenario} gameName={gameData.name} />
      )}
    </div>
  );
}

export default App;
