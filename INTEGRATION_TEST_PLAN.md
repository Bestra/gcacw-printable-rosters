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

| Boundary         | Input                    | Output                   | Language   | Tool   |
| ---------------- | ------------------------ | ------------------------ | ---------- | ------ |
| **raw → parsed** | `raw/*.json`             | `parsed/*.json`          | Python     | pytest |
| **parsed → web** | `parsed/*.json`          | `web/public/data/*.json` | Python     | pytest |
| **web → DOM**    | `web/public/data/*.json` | Rendered components      | TypeScript | Vitest |

**Key principle:** Each test layer uses the output of the previous stage as its source of truth. No reimplementation of parsing logic across languages.

---

## Part A: Vitest / React Tests (web → DOM)

### Goal

Validate that React components render correctly using a hybrid testing approach:

- **Smoke tests**: Verify unit counts match across all real game data
- **Unit tests**: Verify specific behaviors (footnotes, legend, key) with focused fixtures

### Testing Strategy

#### Smoke Tests (real data)

Load actual game JSON files, render components, verify counts match:

```typescript
test("renders correct number of units", () => {
  render(<RosterSheet scenario={realScenario} />);
  const unitCards = screen.getAllByTestId("unit-card");
  expect(unitCards).toHaveLength(
    realScenario.confederateUnits.length + realScenario.unionUnits.length
  );
});
```

#### Unit Tests (focused fixtures)

Hand-crafted minimal data to test specific behaviors:

```typescript
const fixtureWithFootnote = {
  number: 1,
  name: "Test",
  confederateUnits: [{ name: "Test Unit", notes: ["*"] }],
  confederateFootnotes: { "*": "Starts fatigued" },
};

test("footnote symbol appears on unit with note", () => {
  render(<RosterSheet scenario={fixtureWithFootnote} />);
  expect(screen.getByText("*")).toBeInTheDocument();
});
```

---

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

### Phase 2: Test Files

#### Step 2.1: Create `tests/integration/smokeTests.test.tsx`

Smoke tests across all real game data — verify unit counts.

```typescript
import { readFileSync } from "fs";
import { render, screen } from "@testing-library/react";

// Load games.json, iterate each game/scenario
// For each scenario: render, count units, assert match
```

#### Step 2.2: Create `tests/integration/rosterSheet.test.tsx`

Focused unit tests with hand-crafted fixtures:

- Footnote symbols render on units
- Footnote legend renders with definitions
- Conventions key renders
- Leaders render in headers (excluded from unit grid)
- Gunboats render in separate section

---

### What to Assert

| Test Type | Data Point | Assertion                             |
| --------- | ---------- | ------------------------------------- |
| Smoke     | Unit count | Number of rendered units matches JSON |
| Unit      | Footnotes  | Symbol appears on unit card           |
| Unit      | Legend     | Footnote definitions appear           |
| Unit      | Key        | Conventions key section renders       |
| Unit      | Leaders    | Leader names in header elements       |
| Unit      | Gunboats   | Appear in gunboats section            |

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
│   └── integration/
│       ├── smokeTests.test.tsx           # Real data: unit counts
│       └── rosterSheet.test.tsx          # Fixtures: specific behaviors
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

| Step | Task                          | Status |
| ---- | ----------------------------- | ------ |
| 1.1  | Install dependencies          | ✅     |
| 1.2  | Create `vitest.config.ts`     | ✅     |
| 1.3  | Create `tests/setup.ts`       | ✅     |
| 1.4  | Add npm scripts               | ✅     |
| 2.1  | Create `smokeTests.test.tsx`  |        |
| 2.2  | Create `rosterSheet.test.tsx` |        |
| 3    | Run tests, iterate            |        |
