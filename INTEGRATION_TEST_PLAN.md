# Test Suite Implementation Plan

## Architecture: Layered Testing

Each stage of the data pipeline is tested in isolation with clear boundaries:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PDF                                                                        │
│   ↓                                                                         │
│  raw_table_extractor.py                                                     │
│   ↓                                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  raw/{game}_raw_tables.json                                                 │
│   ↓                                                                         │
│  parse_raw_tables.py  ←── game_configs.json          [pytest: raw→parsed]   │
│   ↓                                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  parsed/{game}_parsed.json                                                  │
│   ↓                                                                         │
│  convert_to_web.py                                   [pytest: parsed→web]   │
│   ↓                                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  web/public/data/{game}.json                                                │
│   ↓                                                                         │
│  React components                                    [vitest: web→DOM]      │
│   ↓                                                                         │
│  Rendered DOM                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Boundary | Input | Output | Language | Tool |
|----------|-------|--------|----------|------|
| **raw → parsed** | `raw/*.json` | `parsed/*.json` | Python | pytest |
| **parsed → web** | `parsed/*.json` | `web/public/data/*.json` | Python | pytest |
| **web → DOM** | `web/public/data/*.json` | Rendered components | TypeScript | Vitest |

**Key principle:** Each test layer uses the output of the previous stage as its source of truth. No reimplementation of parsing logic across languages.

---

## Part A: Vitest / React Tests (web → DOM)

### Goal

Validate that all units in `web/public/data/{game}.json` render correctly in the DOM. New games are automatically tested with zero configuration.

### Phase 1: Setup Vitest ✅

#### Step 1.1: Install dependencies ✅

```bash
cd web
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
```

#### Step 1.2: Create `vitest.config.ts` ✅

Configure Vitest with JSDOM environment and globals for cleaner test syntax.

#### Step 1.3: Create `tests/setup.ts` ✅

Import `@testing-library/jest-dom` matchers, mock `import.meta.env.BASE_URL`.

#### Step 1.4: Add npm scripts to `package.json` ✅

```json
"test": "vitest run",
"test:watch": "vitest",
"test:ui": "vitest --ui"
```

---

### Phase 2: Fixture Utilities

#### Step 2.1: Create `tests/fixtures/gameDiscovery.ts`

Auto-discover all games from `games.json` — no hardcoded list.

```typescript
export interface GameInfo {
  id: string;
  name: string;
}
export function discoverGames(): GameInfo[]
```

#### Step 2.2: Create `tests/fixtures/loadWebData.ts`

Load web JSON for any game.

```typescript
import type { GameData } from '../../src/types';
export function loadWebData(gameId: string): GameData
```

---

### Phase 3: Integration Test Suite

#### Step 3.1: Create `tests/integration/rosterRendering.test.tsx`

```typescript
import { discoverGames } from '../fixtures/gameDiscovery';
import { loadWebData } from '../fixtures/loadWebData';
import { render, screen } from '@testing-library/react';
import { RosterSheet } from '../../src/components/RosterSheet';

const games = discoverGames();

describe.each(games)('$name ($id)', ({ id, name }) => {
  const gameData = loadWebData(id);
  
  describe.each(gameData.scenarios)('Scenario $number: $name', (scenario) => {
    test('renders all Confederate units from web JSON', () => {
      render(<RosterSheet scenario={scenario} gameName={name} showImages={false} />);
      
      for (const unit of scenario.confederate.units) {
        expect(screen.getByText(unit.name)).toBeInTheDocument();
      }
    });
    
    test('renders all Union units from web JSON', () => {
      // Similar structure
    });
  });
});
```

#### Step 3.2: Test wrapper for context providers (if needed)

Create wrapper component if `RosterSheet` requires additional context.

---

### What to Assert

| Data Point | Assertion |
|------------|-----------|
| Unit names | Text appears in DOM |
| Unit count | Number of unit elements matches scenario data |
| Hex locations | Hex code appears in unit card |
| Footnotes | Symbol appears on units with notes |
| Leaders | Leader names appear in leader headers |
| Gunboats | Appear in gunboats section |

### What NOT to Assert

- CSS styling/layout
- Image rendering
- Print layout
- Routing behavior

---

### File Structure (Vitest)

```
web/
├── vitest.config.ts                      # ✅ Created
├── package.json                          # ✅ Updated with test scripts
├── tests/
│   ├── setup.ts                          # ✅ Created
│   ├── fixtures/
│   │   ├── gameDiscovery.ts              # Discover games from games.json
│   │   └── loadWebData.ts                # Load web/public/data/*.json
│   └── integration/
│       └── rosterRendering.test.tsx      # Main test suite
```

---

## Part B: Pytest Tests (Python pipeline) — Future

### raw → parsed tests

Validate that `parse_raw_tables.py` correctly transforms raw table data.

```python
# parser/tests/test_parse_raw_tables.py
def test_unit_name_extraction():
    """Multi-cell names are joined correctly"""
    
def test_footnote_symbols_stripped():
    """Footnote markers removed from values"""
    
def test_column_mapping_applied():
    """game_configs.json column positions used correctly"""
```

### parsed → web tests

Validate that `convert_to_web.py` correctly transforms parsed data.

```python
# parser/tests/test_convert_to_web.py
def test_snake_case_to_camel_case():
    """Field names converted correctly"""
    
def test_all_scenarios_included():
    """No scenarios dropped during conversion"""
```

---

## Adding a New Game

1. Add entry to `web/public/data/games.json`
2. Add web data to `web/public/data/{newgame}.json`
3. **Run `npm test`** — automatically discovered and tested!

**No test code changes needed.**

---

## Success Criteria

- [ ] `npm test` runs all games/scenarios in < 30 seconds
- [ ] All current games (7) pass with all scenarios
- [ ] Adding a new game automatically adds tests
- [ ] Clear error messages when a unit is missing from DOM
- [ ] Tests run in CI (GitHub Actions)

---

## Implementation Order

| Step | Task | Status |
|------|------|--------|
| 1.1 | Install dependencies | ✅ |
| 1.2 | Create `vitest.config.ts` | ✅ |
| 1.3 | Create `tests/setup.ts` | ✅ |
| 1.4 | Add npm scripts | ✅ |
| 2.1 | Create `gameDiscovery.ts` | |
| 2.2 | Create `loadWebData.ts` | |
| 3.1 | Create `rosterRendering.test.tsx` | |
| 3.2 | Test wrapper (if needed) | |
| 4 | Run tests, iterate | |
