# GCACW Digital Roster System

## Problem Statement

Great Campaigns of the American Civil War (GCACW) games use stacks of 1/2" counters to track unit state:
- **Unit counter** - The unit itself (leader, infantry, cavalry, artillery)
- **Fatigue marker** - Current fatigue level (0-4)
- **Status marker** - Entrenchments (breastworks, forts), disorganized, etc.

This stacking creates handling overhead and can obscure unit information during play. A **printable roster sheet** would:
1. Reduce physical counter stacking on the map
2. Provide dedicated spaces for each unit's counters
3. Enable faster setup using parsed scenario data
4. Support multiple GCACW titles with similar data formats

---

## Project Phases

### Phase 1: PDF Parser ✅ COMPLETE
Extract scenario data from GCACW rulebook PDFs.

**Completed:**
- [x] Parse unit setup tables (Confederate & Union)
- [x] Handle multi-page tables with `(cntd)` continuations
- [x] Extract scenario metadata (name, game length, map, special rules)
- [x] Capture footnotes and special markers (*, ^, $, +)
- [x] Handle special units (Gunboat, Wagon Train, Naval Battery)
- [x] Export to CSV and JSON formats

**Output:**
- `scenario_parser.py` - Reusable parser class
- `all_scenarios_units.csv` - Flat unit data
- `all_scenarios.json` - Structured scenario data

**Supported Rulebooks:**
- [x] On To Richmond! (OTR2) - ✅ Parsed (9 scenarios, 604 units)
- [ ] Stonewall Jackson's Way
- [ ] Here Come the Rebels
- [ ] Roads to Gettysburg
- [ ] Stonewall's Last Battle
- [ ] Grant Takes Command
- [ ] Others...

---

### Phase 2: Web Application

**Tech Stack:**
- **Framework:** React + Vite (static build)
- **Styling:** CSS (print-optimized)
- **Data:** Static JSON files
- **Hosting:** GitHub Pages

**Features:**
1. Select a game system (OTR2, SJW, etc.)
2. Select a scenario
3. View/print roster sheets for Confederate and Union forces
4. Counters laid out in horizontal rows at correct print size

---

### Phase 3: Printable Roster Layout

**Counter Size:** Just over 1/2" square (~14mm) to fit GCACW counters

**Layout per unit:**
```
┌─────────────────────────────────────────────┐
│ Unit Name              Command   │ counter │
│                                  │  box    │
└─────────────────────────────────────────────┘
```

**Page Layout:**
- Units arranged in horizontal rows
- Grouped by side (Confederate / Union)
- Optionally grouped by command
- Print-optimized CSS (@media print)
- Target: US Letter or A4

**Example Row:**
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Longstreet   │ │ RH Anderson  │ │ Pickett      │ │ Art Res-1    │
│ Div - L      │ │ Demi-Div - L │ │ Demi-Div - L │ │ Brig - ANV   │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │          │ │ │ │          │ │ │ │          │ │ │ │          │ │
│ │  0.55"   │ │ │ │  0.55"   │ │ │ │  0.55"   │ │ │ │  0.55"   │ │
│ │          │ │ │ │          │ │ │ │          │ │ │ │          │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Data Structure

**JSON Files:**
```
/public/data/
  otr2.json        # On To Richmond scenarios + units
  sjw.json         # Stonewall Jackson's Way
  htcr.json        # Here Come the Rebels
  ...
```

**Schema:**
```typescript
interface GameData {
  id: string;              // "otr2"
  name: string;            // "On To Richmond!"
  scenarios: Scenario[];
}

interface Scenario {
  number: number;
  name: string;
  gameLength: string;
  mapInfo: string;
  footnotes: Record<string, string>;
  confederateUnits: Unit[];
  unionUnits: Unit[];
}

interface Unit {
  name: string;            // "RH Anderson"
  size: string;            // "Demi-Div"
  command: string;         // "L"
  type: string;            // "Inf"
  manpowerValue: string;   // "11" or "-"
  hexLocation: string;     // "N0926"
  notes: string[];         // ["*", "^"]
}
```

---

## Project Structure

```
gcacw-scenario-parser/
├── parser/                    # Python PDF parser
│   ├── scenario_parser.py
│   ├── pyproject.toml
│   └── uv.lock
├── web/                       # React web app
│   ├── public/
│   │   └── data/
│   │       └── otr2.json      # Generated from parser output
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── GameSelector.tsx
│   │   │   ├── ScenarioSelector.tsx
│   │   │   ├── RosterSheet.tsx
│   │   │   └── UnitCard.tsx
│   │   ├── styles/
│   │   │   ├── main.css
│   │   │   └── print.css
│   │   └── types.ts
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── data/                      # Source PDFs (gitignored)
│   └── OTR2_Rules.pdf
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Pages deployment
├── PLAN.md
└── README.md
```

**Workflow:**
1. Add PDF to `/data/`
2. Run parser: `cd parser && uv run python scenario_parser.py ../data/OTR2_Rules.pdf`
3. Copy/transform output to `web/public/data/otr2.json`
4. Push to GitHub → Actions builds and deploys to GitHub Pages

---

## Immediate Next Steps

1. [ ] **Convert parser output to web JSON format** - Transform `all_scenarios.json` to the simpler schema above
2. [ ] **Create Vite + React project** - Scaffold the web app
3. [ ] **Build UnitCard component** - Single unit with counter box at correct size
4. [ ] **Build RosterSheet component** - Grid of UnitCards
5. [ ] **Add print CSS** - Ensure correct sizing when printed
6. [ ] **Deploy to GitHub Pages** - Configure GitHub Actions for auto-deploy

---

## Print Sizing Notes

- GCACW counters are 1/2" (12.7mm)
- Target box size: ~0.55" (14mm) to allow slight margin
- CSS: `width: 0.55in; height: 0.55in;`
- Use `@media print` for print-specific styles
- Test with actual counters before finalizing

---

## Open Questions

- [ ] How many units per row? (4-6 depending on label width)
- [ ] Group by command or just list in setup order?
- [ ] Include hex location on roster or just unit info?
- [ ] Color coding by command/corps?
