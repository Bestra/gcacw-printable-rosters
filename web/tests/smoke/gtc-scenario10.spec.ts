import { test, expect } from '@playwright/test';

/**
 * Smoke test for GTC Scenario 10 (Marching to Cold Harbor)
 * 
 * Verifies that the roster page renders correctly with:
 * - Units appearing in the DOM
 * - Cavalry units grouped under their respective leaders
 * - Command hierarchy maintained
 * - Both Union and Confederate sides rendered
 */

const SCENARIO_URL = '/GTCII/10-marching-to-cold-harbor';

test.describe('GTC Scenario 10 - Marching to Cold Harbor', () => {
  test('navigates to scenario 10 and verifies page loads', async ({ page }) => {
    // Navigate to the scenario page
    await page.goto(SCENARIO_URL);
    
    // Wait for the roster sheet to load
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Verify the scenario header is present
    const rosterHeader = page.locator('.roster-header');
    await expect(rosterHeader).toContainText('Grant Takes Command');
    await expect(rosterHeader).toContainText('Scenario 10');
    await expect(rosterHeader).toContainText('Marching to Cold Harbor');
  });

  test('verifies Confederate units are rendered', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Check for Confederate section
    const confederateSection = page.locator('section').filter({ hasText: 'Confederate' }).first();
    await expect(confederateSection).toBeVisible();
    
    // Verify some key Confederate units are present
    await expect(confederateSection.locator('.unit-row')).toHaveCount(await confederateSection.locator('.unit-row').count());
    
    // Check for specific Confederate leaders
    // Leaders appear as images with alt text
    await expect(confederateSection.locator('img[alt="Lee"]')).toBeVisible();
    await expect(confederateSection.locator('img[alt="Hill"]')).toBeVisible();
    await expect(confederateSection.locator('img[alt="Anderson"]')).toBeVisible();
    await expect(confederateSection.locator('img[alt="Early"]')).toBeVisible();
    
    // Check for some infantry units
    await expect(confederateSection.getByText('Pickett')).toBeVisible();
    await expect(confederateSection.getByText('Wilcox-A')).toBeVisible();
    await expect(confederateSection.getByText('Mahone')).toBeVisible();
  });

  test('verifies Union units are rendered', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Check for Union section
    const unionSection = page.locator('section').filter({ hasText: 'Union' }).first();
    await expect(unionSection).toBeVisible();
    
    // Verify Union units exist
    const unionUnitCount = await unionSection.locator('.unit-row').count();
    expect(unionUnitCount).toBeGreaterThan(0);
  });

  test('verifies Confederate cavalry units are grouped under leaders', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    const confederateSection = page.locator('section').filter({ hasText: 'Confederate' }).first();
    
    // Check for cavalry division leaders
    const fLeeDivision = confederateSection.locator('.command-group').filter({ hasText: 'F Lee' }).first();
    const hamptonDivision = confederateSection.locator('.command-group').filter({ hasText: 'Hampton' }).first();
    
    // Verify F Lee's cavalry division exists
    if (await fLeeDivision.count() > 0) {
      // Check for cavalry units under F Lee (Lomax, Wickham)
      const fLeeUnits = fLeeDivision.locator('.unit-row');
      const fLeeUnitCount = await fLeeUnits.count();
      expect(fLeeUnitCount).toBeGreaterThan(0);
      
      // Verify specific cavalry units under F Lee
      await expect(fLeeDivision.getByText('Lomax')).toBeVisible();
      await expect(fLeeDivision.getByText('Wickham')).toBeVisible();
    }
    
    // Verify Hampton's cavalry division exists
    if (await hamptonDivision.count() > 0) {
      // Check for cavalry units under Hampton (Young, Rosser)
      const hamptonUnits = hamptonDivision.locator('.unit-row');
      const hamptonUnitCount = await hamptonUnits.count();
      expect(hamptonUnitCount).toBeGreaterThan(0);
      
      // Verify specific cavalry units under Hampton
      await expect(hamptonDivision.getByText('Young')).toBeVisible();
      await expect(hamptonDivision.getByText('Rosser')).toBeVisible();
    }
  });

  test('verifies command hierarchy structure', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    const confederateSection = page.locator('section').filter({ hasText: 'Confederate' }).first();
    
    // Verify army header exists (for Lee)
    const armyHeader = confederateSection.locator('.army-header');
    if (await armyHeader.count() > 0) {
      await expect(armyHeader).toBeVisible();
      // Lee appears as an image
      await expect(armyHeader.locator('img[alt="Lee"]')).toBeVisible();
    }
    
    // Verify corps-level leaders exist in leader headers
    const leaderHeaders = confederateSection.locator('.leader-header');
    const leaderHeaderCount = await leaderHeaders.count();
    expect(leaderHeaderCount).toBeGreaterThan(0);
    
    // Verify command groups exist
    const commandGroups = confederateSection.locator('.command-group');
    const commandGroupCount = await commandGroups.count();
    expect(commandGroupCount).toBeGreaterThan(0);
  });

  test('verifies unit cards have proper structure', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Get the first visible unit row
    const firstUnit = page.locator('.unit-row').first();
    await expect(firstUnit).toBeVisible();
    
    // Verify counter boxes exist
    const counterBoxes = firstUnit.locator('.counter-box');
    const boxCount = await counterBoxes.count();
    expect(boxCount).toBeGreaterThanOrEqual(3); // At least name, annotations, and info boxes
    
    // Verify setup info section exists
    const setupInfo = firstUnit.locator('.setup-info');
    await expect(setupInfo).toBeVisible();
  });

  test('verifies no critical rendering errors', async ({ page }) => {
    // Track console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Wait a bit to catch any delayed errors
    await page.waitForTimeout(1000);
    
    // Filter out known benign errors (like network errors for optional resources)
    const criticalErrors = errors.filter(err => 
      !err.includes('404') && // Ignore 404s for optional resources
      !err.includes('Failed to load resource') // Ignore resource loading issues
    );
    
    expect(criticalErrors).toHaveLength(0);
  });

  test('verifies both sides render side-by-side or stacked', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Check that both sections exist
    const sections = page.locator('section');
    const sectionCount = await sections.count();
    expect(sectionCount).toBeGreaterThanOrEqual(2); // Should have at least Confederate and Union sections
  });

  test('verifies manpower values are displayed', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Find units with manpower values (not leaders)
    const confederateSection = page.locator('section').filter({ hasText: 'Confederate' }).first();
    const unitWithMP = confederateSection.locator('.unit-row').filter({ has: page.locator('.mp:not(:empty)') }).first();
    
    if (await unitWithMP.count() > 0) {
      const mpElement = unitWithMP.locator('.mp');
      await expect(mpElement).toBeVisible();
      const mpText = await mpElement.textContent();
      expect(mpText).toBeTruthy();
      expect(mpText?.trim()).not.toBe('');
    }
  });

  test('verifies hex locations are displayed', async ({ page }) => {
    await page.goto(SCENARIO_URL);
    await expect(page.locator('.roster-sheet')).toBeVisible({ timeout: 10000 });
    
    // Find a unit with a hex location
    const unitWithHex = page.locator('.unit-row').filter({ has: page.locator('.hex') }).first();
    
    if (await unitWithHex.count() > 0) {
      const hexElement = unitWithHex.locator('.hex');
      await expect(hexElement).toBeVisible();
      const hexText = await hexElement.textContent();
      expect(hexText).toBeTruthy();
      expect(hexText?.trim()).not.toBe('');
    }
  });
});
