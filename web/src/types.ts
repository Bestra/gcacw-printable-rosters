export interface Unit {
  name: string;
  size: string;
  command: string;
  type: string;
  manpowerValue: string;
  hexLocation: string;
  notes: string[];
}

export interface Scenario {
  number: number;
  name: string;
  gameLength: string;
  mapInfo: string;
  confederateFootnotes: Record<string, string>;
  unionFootnotes: Record<string, string>;
  confederateUnits: Unit[];
  unionUnits: Unit[];
}

export interface GameData {
  id: string;
  name: string;
  scenarios: Scenario[];
}
