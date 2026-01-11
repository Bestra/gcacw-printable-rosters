export interface Unit {
  name: string;
  size: string;
  command: string;
  type: string;
  manpowerValue: string;
  hexLocation: string;
  notes: string[];
  reinforcementSet?: string;
}

export interface Gunboat {
  name: string;
  location: string;
}

export interface Scenario {
  number: number;
  name: string;
  confederateFootnotes: Record<string, string>;
  unionFootnotes: Record<string, string>;
  confederateUnits: Unit[];
  unionUnits: Unit[];
  confederateGunboats: Gunboat[];
  unionGunboats: Gunboat[];
}

export interface GameData {
  id: string;
  name: string;
  scenarios: Scenario[];
}

export interface GameInfo {
  id: string;
  name: string;
  file: string;
}

export interface GamesIndex {
  games: GameInfo[];
}
