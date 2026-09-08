# GCACW Scenario Parser & Roster Generator

Printable roster sheets for Great Campaigns of the American Civil War (GCACW) board games.

**🎮 [Try it live](https://bestra.github.io/gcacw-printable-rosters/)**

## The Problem

GCACW games use stacks of 1/2" counters to track each unit's state—the unit itself, fatigue markers, entrenchments, etc. This creates handling overhead and obscures information during play.

## The Solution

**Printable roster sheets** with dedicated spaces for each unit's counters:

```
┌─────────────────────────────┐
│ Unit Name           Command │
├─────────┬─────────┬─────────┤
│  Fort   │   MP    │ Fatigue │  ← Place counters here instead
│  box    │   Hex   │  box    │     of stacking on the map
└─────────┴─────────┴─────────┘
```

Counter boxes are sized at 0.55" to fit GCACW's 1/2" counters.

## Quick Start

```bash
cd web && npm install
make dev
```

Open http://localhost:5173, select a game and scenario, then `Cmd+P` / `Ctrl+P` to print.

## Supported Games

- ✅ On To Richmond!
- ✅ Grant Takes Command
- ✅ Hood Strikes North
- ✅ Here Come the Rebels!
- ✅ Roads to Gettysburg 2
- ✅ Rebels in the White House

## Adding More Games

The project includes a Python parser that extracts unit data from GCACW rulebook PDFs. See [CLAUDE.md](CLAUDE.md) for technical details on extending the parser.

## Development

- **Web app**: `make dev`
- **Storybook**: `cd web && npm run storybook` (component development & docs)
- **Parser**: Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv)
- **Deploy**: Push to `main` triggers GitHub Pages deploy

### Running Tests

```bash
make test  # Run all tests (parser + web)

# Or individually:
cd parser && uv run pytest tests/ -v
cd web && npm test
```

### Storybook

Interactive component development and documentation:

```bash
cd web
npm run storybook        # Start dev server at http://localhost:6006
npm run build-storybook  # Build static site
```

See [web/STORYBOOK.md](web/STORYBOOK.md) for details on using Storybook and writing stories.

### LLM Evaluation

An LLM-powered integration test compares raw PDF table data to rendered DOM output:

```bash
make snapshots   # Generate DOM snapshots (run after data changes)
make llm-eval    # Run LLM evaluation across all scenarios
```

See [docs/plans/LLM_EVAL_PLAN.md](docs/plans/LLM_EVAL_PLAN.md) for implementation details.

## License

MIT
bar
