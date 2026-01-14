# Smoke Tests

Playwright-based smoke tests for verifying critical rendering functionality of the roster sheets.

## Running Smoke Tests

```bash
cd web
npm run test:smoke        # Run in headless mode
npm run test:smoke:headed # Run with browser visible
```

## What Gets Tested

### GTC Scenario 10 - Marching to Cold Harbor

Located at `tests/smoke/gtc-scenario10.spec.ts`, this test suite verifies:

1. **Page Navigation & Loading**
   - Scenario page loads correctly
   - Roster sheet renders
   - Game and scenario headers display properly

2. **Unit Rendering**
   - Confederate units appear in the DOM
   - Union units appear in the DOM
   - Unit cards have proper structure (counter boxes, setup info)

3. **Cavalry Grouping**
   - Cavalry units are properly grouped under their division leaders
   - F Lee division cavalry (Lomax, Wickham)
   - Hampton division cavalry (Young, Rosser)

4. **Command Hierarchy**
   - Army-level leaders render in army headers
   - Corps-level leaders render in leader headers
   - Command groups are properly structured

5. **Data Display**
   - Manpower values show correctly
   - Hex locations display
   - No critical JavaScript errors occur

## Configuration

The Playwright configuration (`playwright.config.ts`) is set up for local testing:

- Automatically starts the dev server on port 5173
- Uses headless Chromium by default
- Takes screenshots on failure for debugging
- Generates traces on retry for detailed debugging

### Dev Server Setup

The configuration includes a workaround to ensure the dev server runs with the correct base URL (`/` instead of `/gcacw-printable-rosters/`) even when running in GitHub Actions environment by unsetting the `GITHUB_ACTIONS` environment variable.

## Adding New Smoke Tests

To add a new scenario smoke test:

1. Create a new file in `tests/smoke/` (e.g., `gtc-scenario1.spec.ts`)
2. Import Playwright test utilities: `import { test, expect } from '@playwright/test';`
3. Define the scenario URL constant
4. Create test cases following the pattern in `gtc-scenario10.spec.ts`
5. Run the test to verify it works

Example structure:

```typescript
import { test, expect } from '@playwright/test';

const SCENARIO_URL = '/GTCII/1-the-battle-of-the-wilderness';

test.describe('GTC Scenario 1', () => {
  test('loads scenario page', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible();
  });
});
```

## Debugging

If a test fails:

1. Check the screenshot in `test-results/` directory
2. Review the error context markdown file
3. For retried tests, examine the trace file:
   ```bash
   npx playwright show-trace test-results/path-to-trace.zip
   ```

## CI/CD Integration

These tests are designed for local development and validation. To integrate into CI:

1. Add a GitHub Actions workflow
2. Ensure `GITHUB_ACTIONS` environment variable handling is correct
3. Configure artifact uploads for test results and screenshots
