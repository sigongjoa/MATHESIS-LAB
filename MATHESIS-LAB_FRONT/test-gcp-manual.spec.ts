import { test, expect } from '@playwright/test';

test('GCP Settings page should load without errors', async ({ page }) => {
  // Capture console errors
  const errors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
      console.error(`[Browser Console Error] ${msg.text()}`);
    }
  });

  // Navigate to GCP Settings
  console.log('📄 Navigating to GCP Settings page...');
  await page.goto('http://localhost:3002/#/gcp-settings', { waitUntil: 'networkidle' });

  // Wait for page to fully load
  await page.waitForTimeout(3000);

  // Check for heading
  const heading = await page.locator('h1, h2, h3').filter({ hasText: /GCP Settings/ }).first();
  const headingVisible = await heading.isVisible({ timeout: 5000 }).catch(() => false);

  console.log(`\n✅ GCP Settings heading visible: ${headingVisible}`);
  console.log(`❌ Console errors found: ${errors.length}`);

  if (errors.length > 0) {
    console.log('\n🚨 ERRORS:');
    errors.forEach((err, i) => {
      console.log(`  ${i + 1}. ${err}`);
    });
  } else {
    console.log('✅ No console errors!');
  }

  // Assertions
  expect(headingVisible).toBe(true);
  expect(errors.length).toBe(0);
});
