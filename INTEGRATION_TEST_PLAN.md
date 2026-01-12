# Integration Test Suite Implementation Plan

## Goal

Create a Vitest + React Testing Library test suite that validates all units from raw table data appear correctly in the rendered DOM. New games should be automatically tested with zero additional configuration.

---

## Phase 1: Setup Vitest

### Step 1.1: Install dependencies ✅

```bash
cd web
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
```

### Step 1.2: Create `vitest.config.ts` ✅

Configure Vitest with JSDOM environment, set up path aliases to match Vite config, and enable globals for cleaner test syntax.

### Step 1.3: Create `tests/setup.ts` ✅

Import `@testing-library/jest-dom` matchers (e.g., `toBeInTheDocument()`), set up any global mocks needed (like `import.meta.env.BASE_URL`).

### Step 1.4: Add npm scripts to `package.json` ✅

```json
"test": "vitest run",
"test:watch": "vitest",
"test:ui": "vitest --ui"
```

---

## Phase 2: Fixture Utilities (Auto-Discovery)

### Step 2.1: Create `tests/fixtures/gameDiscovery.ts`

**Purpose:** Automatically discover all games from `games.json` — no hardcoded list.

```typescript
// Reads web/public/data/games.json
// Returns array of { id, name, file } for all games
export function discoverGames(): GameInfo[]
```

### Step 2.2: Create `tests/fixtures/loadRawTables.ts`

**Purpose:** Load raw table JSON for any game.

```typescript
// Reads parser/raw/{gameId}_raw_tables.json
// Returns parsed JSON with all scenarios
export function loadRawTables(gameId: string): RawScenario[]
```

### Step 2.3: Create `tests/fixtures/loadWebData.ts`

**Purpose:** Load web JSON for comparison/rendering.

```typescript
// Reads web/public/data/{gameId}.json
// Returns GameData with scenarios ready for component props
export function loadWebData(gameId: string): GameData
```

---

## Phase 3: Raw Data Extraction Utilities

### Step 3.1: Create `tests/utils/extractUnits.ts`

**Purpose:** Extract unit names from raw table format (mirroring parser logic).

```typescript
interface ExtractedUnit {
  name: string;           // Joined from multi-cell names
  manpowerValue: string;
  hexLocation: string;
  side: 'confederate' | 'union';
}

// Extracts all units from a scenario's raw tables
export function extractUnitsFromRaw(scenario: RawScenario): {
  confederate: ExtractedUnit[];
  union: ExtractedUnit[];
}
```

**Key logic to implement:**
- Join multi-cell unit names (e.g., `["D.H.", "Hill-A"]` → `"D.H. Hill-A"`)
- Strip footnote symbols from values
- Identify hex column by pattern (e.g., `W3212`, `S5510`)
- Handle special units (Gunboats, etc.)

### Step 3.2: Reference `game_configs.json` for column mappings

Each game may have different column layouts. The extraction utility should either:
- Option A: Read `parser/game_configs.json` for authoritative column positions
- Option B: Use heuristics (simpler, but may drift from parser)

**Recommendation:** Option A — read the real config to stay in sync.

---

## Phase 4: Test Suite Structure

### Step 4.1: Create `tests/integration/dataIntegrity.test.ts`

**Structure:**
```typescript
import { discoverGames } from '../fixtures/gameDiscovery';
import { loadRawTables } from '../fixtures/loadRawTables';
import { loadWebData } from '../fixtures/loadWebData';
import { extractUnitsFromRaw } from '../utils/extractUnits';
import { render, screen, within } from '@testing-library/react';
import { RosterSheet } from '../../src/components/RosterSheet';

// Auto-discover all games
const games = discoverGames();

describe.each(games)('$name ($id)', ({ id, name }) => {
  const rawData = loadRawTables(id);
  const webData = loadWebData(id);
  
  describe.each(webData.scenarios)('Scenario $number: $name', (scenario) => {
    // Find matching raw scenario
    const rawScenario = rawData.find(r => r.scenario_number === scenario.number);
    const expectedUnits = extractUnitsFromRaw(rawScenario);
    
    test('all Confederate units appear in DOM', () => {
      render(<RosterSheet scenario={scenario} gameName={name} showImages={false} variant="flow" />);
      
      const confSection = screen.getByRole('region', { name: /confederate/i });
      
      for (const unit of expectedUnits.confederate) {
        expect(within(confSection).getByText(unit.name)).toBeInTheDocument();
      }
    });
    
    test('all Union units appear in DOM', () => {
      // Similar structure
    });
  });
});
```

### Step 4.2: Wrapper component for context providers

The `RosterSheet` uses `RosterProvider` internally, but may need additional context. Create a test wrapper if needed.

---

## Phase 5: Test Assertions

### What to Assert

| Data Point | Assertion |
|------------|-----------|
| Unit names | Text appears in correct army section |
| Unit count | Number of `.unit-row` elements matches expected |
| Manpower values | MP value appears (or empty if "-") |
| Hex locations | Hex code appears in unit card |
| Footnotes rendered | Symbol appears on units that have notes |
| Leaders rendered | Leader names appear in `.leader-header` elements |
| Gunboats | Appear in `.gunboats-list` section |

### What NOT to Assert (save for later)

- CSS styling/layout
- Image rendering
- Print layout
- Routing behavior

---

## Phase 6: Adding a New Game (Zero Boilerplate!)

### When you add a new game:

1. Add entry to `web/public/data/games.json` ✓ (already required)
2. Add raw data to `parser/raw/{newgame}_raw_tables.json` ✓ (already required)
3. Add web data to `web/public/data/{newgame}.json` ✓ (already required)
4. **Run tests** — the new game is automatically discovered and tested!

**No test code changes needed.**

---

## File Structure Summary

```
web/
├── vitest.config.ts                      # Vitest configuration
├── package.json                          # + test scripts
├── tests/
│   ├── setup.ts                          # Test setup (matchers, mocks)
│   ├── fixtures/
│   │   ├── gameDiscovery.ts              # Auto-discover games from games.json
│   │   ├── loadRawTables.ts              # Load parser/raw/*.json
│   │   └── loadWebData.ts                # Load web/public/data/*.json
│   ├── utils/
│   │   └── extractUnits.ts               # Parse raw tables → unit list
│   └── integration/
│       └── dataIntegrity.test.ts         # Main test suite
```

---

## Implementation Order

| Step | Task | Depends On |
|------|------|------------|
| 1 | Install dependencies | - |
| 2 | Create `vitest.config.ts` | Step 1 |
| 3 | Create `tests/setup.ts` | Step 2 |
| 4 | Add npm scripts | Step 1 |
| 5 | Create `gameDiscovery.ts` | - |
| 6 | Create `loadRawTables.ts` | - |
| 7 | Create `loadWebData.ts` | - |
| 8 | Create `extractUnits.ts` | Step 6 |
| 9 | Create `dataIntegrity.test.ts` | Steps 5-8 |
| 10 | Run tests, iterate on assertions | Step 9 |

---

## Success Criteria

- [ ] `npm test` runs all games/scenarios in < 30 seconds
- [ ] All current games (7) pass with all scenarios
- [ ] Adding a new game to `games.json` + data files automatically adds tests
- [ ] Clear error messages when a unit is missing from DOM
- [ ] Tests run in CI (GitHub Actions)

---

## Open Questions

1. **Column mapping strategy:** Should `extractUnits.ts` read `game_configs.json` or use heuristics?
   - *Recommendation:* Read config for accuracy

2. **How to handle intentional filtering?** (e.g., Leaders excluded from grid)
   - *Solution:* Test leaders separately in leader headers

3. **Parallel test execution?** Vitest runs in parallel by default — may need to verify no state conflicts
