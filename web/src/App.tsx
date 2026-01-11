import { useEffect, useState } from "react";
import { Routes, Route, Navigate, useParams, useNavigate, useSearchParams } from "react-router-dom";
import { GameSelector } from "./components/GameSelector";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { HierarchicalRosterSheet } from "./components/HierarchicalRosterSheet";
import { FlowRosterSheet } from "./components/FlowRosterSheet";
import { getGameIdFromSlug, getGameSlug, getScenarioSlug, getScenarioNumberFromSlug } from "./utils/slugs";
import type { GameData, GameInfo, GamesIndex } from "./types";
import "./App.css";

type LayoutMode = "hierarchical" | "flow";
const DEFAULT_LAYOUT: LayoutMode = "hierarchical";

// Get base path from Vite (handles GitHub Pages deployment)
const BASE_URL = import.meta.env.BASE_URL;

function ScenarioView({
  games,
  gamesLoading,
}: {
  games: GameInfo[];
  gamesLoading: boolean;
}) {
  const { gameSlug, scenarioSlug } = useParams<{ gameSlug: string; scenarioSlug: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get layout mode from query param, default to hierarchical
  const viewParam = searchParams.get("view");
  const layoutMode: LayoutMode = viewParam === "hierarchical" || viewParam === "flow"
    ? viewParam 
    : DEFAULT_LAYOUT;

  const handleLayoutChange = (mode: LayoutMode) => {
    if (mode === DEFAULT_LAYOUT) {
      // Remove param if it's the default
      searchParams.delete("view");
    } else {
      searchParams.set("view", mode);
    }
    setSearchParams(searchParams, { replace: true });
  };

  const gameId = gameSlug ? getGameIdFromSlug(gameSlug) : null;
  const game = games.find((g) => g.id === gameId);
  const scenarioNumber = scenarioSlug ? getScenarioNumberFromSlug(scenarioSlug) : null;

  // Load game data when game changes
  useEffect(() => {
    if (!game) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setGameData(null);

    fetch(`${BASE_URL}data/${game.file}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load ${game.name} data`);
        return res.json();
      })
      .then((data: GameData) => {
        setGameData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [game]);

  // Handle game selection
  const handleGameSelect = (newGameId: string | null) => {
    if (newGameId) {
      const newGame = games.find((g) => g.id === newGameId);
      if (newGame) {
        // Navigate to the new game's first scenario (will be handled by redirect)
        // Preserve query params (like view mode)
        const queryString = searchParams.toString();
        const path = `/${getGameSlug(newGameId)}`;
        navigate(queryString ? `${path}?${queryString}` : path);
      }
    }
  };

  // Handle scenario selection
  const handleScenarioSelect = (newScenarioNumber: number | null) => {
    if (newScenarioNumber && gameSlug && gameData) {
      const scenario = gameData.scenarios.find((s) => s.number === newScenarioNumber);
      if (scenario) {
        // Preserve query params (like view mode)
        const queryString = searchParams.toString();
        const path = `/${gameSlug}/${getScenarioSlug(scenario.number, scenario.name)}`;
        navigate(queryString ? `${path}?${queryString}` : path);
      }
    }
  };

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (gamesLoading || loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!game) {
    return <div className="error">Game not found: {gameSlug}</div>;
  }

  const scenario = gameData?.scenarios.find((s) => s.number === scenarioNumber);

  // If scenario not found but we have game data, redirect to first scenario
  if (gameData && !scenario && gameData.scenarios.length > 0) {
    const firstScenario = gameData.scenarios[0];
    const queryString = searchParams.toString();
    const path = `/${gameSlug}/${getScenarioSlug(firstScenario.number, firstScenario.name)}`;
    return (
      <Navigate
        to={queryString ? `${path}?${queryString}` : path}
        replace
      />
    );
  }

  return (
    <div className="app">
      <div className="selectors no-print">
        <GameSelector
          games={games}
          selectedGameId={gameId}
          onSelect={handleGameSelect}
        />
        {gameData && (
          <ScenarioSelector
            scenarios={gameData.scenarios}
            selectedNumber={scenarioNumber}
            onSelect={handleScenarioSelect}
          />
        )}
        <div className="layout-toggle">
          <label>
            <span>Layout:</span>
            <select 
              value={layoutMode} 
              onChange={(e) => handleLayoutChange(e.target.value as LayoutMode)}
            >
              <option value="hierarchical">Hierarchical</option>
              <option value="flow">Flow (compact)</option>
            </select>
          </label>
        </div>
      </div>
      {scenario && gameData && (
        layoutMode === "flow"
          ? <FlowRosterSheet scenario={scenario} gameName={gameData.name} />
          : <HierarchicalRosterSheet scenario={scenario} gameName={gameData.name} />
      )}
    </div>
  );
}

function GameRedirect({ games }: { games: GameInfo[] }) {
  const { gameSlug } = useParams<{ gameSlug: string }>();
  const [searchParams] = useSearchParams();
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(true);

  const gameId = gameSlug ? getGameIdFromSlug(gameSlug) : null;
  const game = games.find((g) => g.id === gameId);

  useEffect(() => {
    if (!game) {
      setLoading(false);
      return;
    }

    fetch(`${BASE_URL}data/${game.file}`)
      .then((res) => res.json())
      .then((data: GameData) => {
        setGameData(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [game]);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!game) {
    return <div className="error">Game not found: {gameSlug}</div>;
  }

  if (gameData && gameData.scenarios.length > 0) {
    const firstScenario = gameData.scenarios[0];
    const queryString = searchParams.toString();
    const path = `/${gameSlug}/${getScenarioSlug(firstScenario.number, firstScenario.name)}`;
    return (
      <Navigate
        to={queryString ? `${path}?${queryString}` : path}
        replace
      />
    );
  }

  return <div className="error">No scenarios found</div>;
}

function App() {
  const [games, setGames] = useState<GameInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load games index on mount
  useEffect(() => {
    fetch(`${BASE_URL}data/games.json`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load games index");
        return res.json();
      })
      .then((data: GamesIndex) => {
        setGames(data.games);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  // Default redirect to first game
  const defaultGame = games[0];
  const defaultRedirect = defaultGame ? `/${getGameSlug(defaultGame.id)}` : "/";

  return (
    <Routes>
      <Route path="/" element={<Navigate to={defaultRedirect} replace />} />
      <Route path="/:gameSlug" element={<GameRedirect games={games} />} />
      <Route
        path="/:gameSlug/:scenarioSlug"
        element={
          <ScenarioView 
            games={games} 
            gamesLoading={loading} 
          />
        }
      />
    </Routes>
  );
}

export default App;
