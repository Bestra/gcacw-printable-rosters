import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  Link,
  useParams,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { GameSelector } from "./components/GameSelector";
import { ScenarioSelector } from "./components/ScenarioSelector";
import { RosterSheet, type RosterVariant } from "./components/RosterSheet";
import { ScenarioCardSheet } from "./components/ScenarioCardSheet";
import { RangeCardSheet } from "./components/RangeCardSheet";
import { getGameIdFromSlug, getGameSlug, getScenarioSlug, getScenarioNumberFromSlug } from "./utils/slugs";
import {
  copyCardPaletteParams,
  normalizeScenarioRange,
} from "./utils/rangeUtils";
import type { GameData, GameInfo, GamesIndex } from "./types";
import "./App.css";

const DEFAULT_LAYOUT: RosterVariant = "hierarchical";
const DEFAULT_CONFEDERATE_CARD_COLOR = "#c8c8c4";
const DEFAULT_UNION_CARD_COLOR = "#b9daea";
type LayoutMode = RosterVariant | "cards";

function colorParam(value: string | null, fallback: string): string {
  return value && /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
}

function setColorParam(
  searchParams: URLSearchParams,
  param: "confederateColor" | "unionColor",
  value: string,
  defaultValue: string,
) {
  if (value.toLowerCase() === defaultValue) {
    searchParams.delete(param);
  } else {
    searchParams.set(param, value);
  }
}

function CardColorControls({
  confederateColor,
  unionColor,
  onChange,
}: {
  confederateColor: string;
  unionColor: string;
  onChange: (
    param: "confederateColor" | "unionColor",
    value: string,
    defaultValue: string,
  ) => void;
}) {
  return (
    <div className="card-color-controls">
      <label>
        <span>Confederate:</span>
        <input
          type="color"
          value={confederateColor}
          onChange={(event) =>
            onChange(
              "confederateColor",
              event.target.value,
              DEFAULT_CONFEDERATE_CARD_COLOR,
            )
          }
        />
      </label>
      <label>
        <span>Union:</span>
        <input
          type="color"
          value={unionColor}
          onChange={(event) =>
            onChange(
              "unionColor",
              event.target.value,
              DEFAULT_UNION_CARD_COLOR,
            )
          }
        />
      </label>
    </div>
  );
}

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
  const layoutMode: LayoutMode = viewParam === "hierarchical" || viewParam === "flow" || viewParam === "cards"
    ? viewParam 
    : DEFAULT_LAYOUT;
  const confederateCardColor = colorParam(
    searchParams.get("confederateColor"),
    DEFAULT_CONFEDERATE_CARD_COLOR,
  );
  const unionCardColor = colorParam(
    searchParams.get("unionColor"),
    DEFAULT_UNION_CARD_COLOR,
  );

  // Get images mode from query param, default to ON
  const imagesParam = searchParams.get("images");
  const showImages = imagesParam !== "off"; // Default ON unless explicitly "off"

  const handleLayoutChange = (mode: LayoutMode) => {
    if (mode === DEFAULT_LAYOUT) {
      // Remove param if it's the default
      searchParams.delete("view");
    } else {
      searchParams.set("view", mode);
    }
    setSearchParams(searchParams, { replace: true });
  };

  const handleCardColorChange = (
    param: "confederateColor" | "unionColor",
    value: string,
    defaultValue: string,
  ) => {
    setColorParam(searchParams, param, value, defaultValue);
    setSearchParams(searchParams, { replace: true });
  };

  const handleImagesChange = (show: boolean) => {
    if (show) {
      // Remove param if it's the default (images on)
      searchParams.delete("images");
    } else {
      searchParams.set("images", "off");
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
  const reusableDeckParams = new URLSearchParams();
  if (scenarioNumber) {
    reusableDeckParams.set("from", String(scenarioNumber));
    reusableDeckParams.set("to", String(scenarioNumber));
  }
  copyCardPaletteParams(searchParams, reusableDeckParams);

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
              <option value="cards">Playing cards</option>
            </select>
          </label>
        </div>
        {layoutMode === "cards" && (
         <>
           <CardColorControls
             confederateColor={confederateCardColor}
             unionColor={unionCardColor}
             onChange={handleCardColorChange}
           />
           {gameSlug && scenarioNumber && (
             <Link
               className="range-card-link"
               to={`/${gameSlug}/cards?${reusableDeckParams.toString()}`}
             >
               Reusable deck
             </Link>
           )}
         </>
        )}
        {layoutMode !== "cards" && <div className="image-toggle">
         <label>
            <input
              type="checkbox"
              checked={showImages}
              onChange={(e) => handleImagesChange(e.target.checked)}
            />
            <span>Show counter images</span>
          </label>
        </div>}
      </div>
      {scenario && gameData && layoutMode === "cards" && gameId && (
        <ScenarioCardSheet
          scenario={scenario}
          gameName={gameData.name}
          gameId={gameId}
          confederateBodyColor={confederateCardColor}
          unionBodyColor={unionCardColor}
        />
      )}
      {scenario && gameData && layoutMode !== "cards" && (
        <RosterSheet 
          scenario={scenario} 
          gameName={gameData.name} 
          gameId={gameId ?? undefined} 
          showImages={showImages}
          variant={layoutMode}
        />
      )}
    </div>
  );
}

function RangeCardView({ games }: { games: GameInfo[] }) {
  const { gameSlug } = useParams<{ gameSlug: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const gameId = gameSlug ? getGameIdFromSlug(gameSlug) : null;
  const game = games.find((entry) => entry.id === gameId);
  const [loadState, setLoadState] = useState<{
    gameId: string | null;
    gameData: GameData | null;
    error: string | null;
  }>({
    gameId: null,
    gameData: null,
    error: null,
  });
  const confederateCardColor = colorParam(
    searchParams.get("confederateColor"),
    DEFAULT_CONFEDERATE_CARD_COLOR,
  );
  const unionCardColor = colorParam(
    searchParams.get("unionColor"),
    DEFAULT_UNION_CARD_COLOR,
  );

  useEffect(() => {
    if (!game) {
      return;
    }

    let cancelled = false;
    fetch(`${BASE_URL}data/${game.file}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load ${game.name} data`);
        }
        return response.json();
      })
      .then((data: GameData) => {
        if (!cancelled) {
          setLoadState({
            gameId: game.id,
            gameData: data,
            error: null,
          });
        }
      })
      .catch((caughtError: Error) => {
        if (!cancelled) {
          setLoadState({
            gameId: game.id,
            gameData: null,
            error: caughtError.message,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [game]);

  if (!game) {
    return <div className="error">Game not found: {gameSlug}</div>;
  }
  if (loadState.gameId !== game.id) {
    return <div className="loading">Loading...</div>;
  }
  if (loadState.error) {
    return <div className="error">Error: {loadState.error}</div>;
  }
  const gameData = loadState.gameData;
  if (!gameData || gameData.scenarios.length === 0) {
    return <div className="error">No scenarios found</div>;
  }

  const requestedFrom = Number(searchParams.get("from")) || null;
  const requestedTo = Number(searchParams.get("to")) || null;
  const range = normalizeScenarioRange(
    gameData.scenarios,
    requestedFrom,
    requestedTo,
  );
  const normalizedParams = new URLSearchParams(searchParams);
  normalizedParams.set("from", String(range.from));
  normalizedParams.set("to", String(range.to));
  const needsNormalization =
    searchParams.get("from") !== String(range.from) ||
    searchParams.get("to") !== String(range.to);

  if (needsNormalization) {
    return <Navigate to={`?${normalizedParams.toString()}`} replace />;
  }

  const updateRange = (from: number, to: number) => {
    const normalized = normalizeScenarioRange(gameData.scenarios, from, to);
    searchParams.set("from", String(normalized.from));
    searchParams.set("to", String(normalized.to));
    setSearchParams(searchParams, { replace: true });
  };
  const handleCardColorChange = (
    param: "confederateColor" | "unionColor",
    value: string,
    defaultValue: string,
  ) => {
    setColorParam(searchParams, param, value, defaultValue);
    setSearchParams(searchParams, { replace: true });
  };
  const handleGameSelect = (newGameId: string | null) => {
    if (!newGameId) {
      return;
    }
    const nextGame = games.find((entry) => entry.id === newGameId);
    if (nextGame) {
      const nextParams = new URLSearchParams();
      copyCardPaletteParams(searchParams, nextParams);
      const query = nextParams.toString();
      const path = `/${getGameSlug(nextGame.id)}/cards`;
      navigate(query ? `${path}?${query}` : path);
    }
  };
  const startingScenario = range.scenarios[0];
  const scenarioCardParams = new URLSearchParams("view=cards");
  copyCardPaletteParams(searchParams, scenarioCardParams);

  return (
    <div className="app">
      <div className="selectors no-print">
        <GameSelector
          games={games}
          selectedGameId={gameId}
          onSelect={handleGameSelect}
        />
        <ScenarioSelector
          scenarios={gameData.scenarios}
          selectedNumber={range.from}
          label="From:"
          id="range-from"
          onSelect={(from) => updateRange(from, Math.max(from, range.to))}
        />
        <ScenarioSelector
          scenarios={gameData.scenarios}
          selectedNumber={range.to}
          label="Through:"
          id="range-to"
          onSelect={(to) => updateRange(Math.min(range.from, to), to)}
        />
        <CardColorControls
          confederateColor={confederateCardColor}
          unionColor={unionCardColor}
          onChange={handleCardColorChange}
        />
        <Link
          className="range-card-link"
          to={`/${gameSlug}/${getScenarioSlug(
            startingScenario.number,
            startingScenario.name,
          )}?${scenarioCardParams.toString()}`}
        >
          Scenario cards
        </Link>
      </div>
      <RangeCardSheet
        scenarios={range.scenarios}
        gameName={gameData.name}
        gameId={gameData.id}
        confederateBodyColor={confederateCardColor}
        unionBodyColor={unionCardColor}
      />
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
      <Route path="/:gameSlug/cards" element={<RangeCardView games={games} />} />
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
