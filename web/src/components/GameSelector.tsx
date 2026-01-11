import type { GameInfo } from "../types";
import "./GameSelector.css";

interface GameSelectorProps {
  games: GameInfo[];
  selectedGameId: string | null;
  onSelect: (gameId: string) => void;
}

export function GameSelector({
  games,
  selectedGameId,
  onSelect,
}: GameSelectorProps) {
  return (
    <div className="game-selector no-print">
      <label htmlFor="game-select">Game:</label>
      <select
        id="game-select"
        value={selectedGameId ?? ""}
        onChange={(e) => onSelect(e.target.value)}
      >
        <option value="" disabled>
          Choose a game...
        </option>
        {games.map((game) => (
          <option key={game.id} value={game.id}>
            {game.name}
          </option>
        ))}
      </select>
    </div>
  );
}
