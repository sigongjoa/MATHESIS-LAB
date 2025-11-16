import { test, expect } from '@playwright/test';

test.describe('Frontend Console Log Capture', () => {
  let consoleLogs: {
    type: string;
    message: string;
    timestamp: string;
    location?: string;
  }[] = [];
  let networkErrors: {
    url: string;
    status: number;
    statusText: string;
  }[] = [];

  test.beforeEach(async ({ page }) => {
    consoleLogs = [];
    networkErrors = [];

    // Capture all console messages (log, error, warning, debug, info)
    page.on('console', (msg) => {
      const timestamp = new Date().toLocaleTimeString();
      const location = msg.location();
      const logEntry = {
        type: msg.type(),
        message: msg.text(),
        timestamp,
        location: location ? `${location.url}:${location.lineNumber}` : 'unknown',
      };
      consoleLogs.push(logEntry);

      // Print to terminal immediately for visibility
      const icon =
        msg.type() === 'error'
          ? '❌'
          : msg.type() === 'warning'
            ? '⚠️'
            : msg.type() === 'debug'
              ? '🐛'
              : 'ℹ️';
      console.log(
        `[${timestamp}] ${icon} [${msg.type().toUpperCase()}] ${msg.text()}`
      );
    });

    // Capture uncaught exceptions
    page.on('pageerror', (error) => {
      const timestamp = new Date().toLocaleTimeString();
      const entry = {
        type: 'error',
        message: `Uncaught Exception: ${error.message}`,
        timestamp,
        location: error.stack || 'unknown',
      };
      consoleLogs.push(entry);
      console.error(
        `[${timestamp}] ❌ [UNCAUGHT] ${error.message}\nStack: ${error.stack}`
      );
    });

    // Capture failed network requests
    page.on('response', (response) => {
      if (response.status() >= 400) {
        const networkError = {
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        };
        networkErrors.push(networkError);
        console.warn(
          `[${new Date().toLocaleTimeString()}] ⚠️ [NETWORK] ${response.status()} ${response.statusText()} - ${response.url()}`
        );
      }
    });
  });

  test.afterEach(async () => {
    console.log('\n' + '='.repeat(80));
    console.log('📊 SUMMARY - Frontend Session Report');
    console.log('='.repeat(80));

    if (consoleLogs.length > 0) {
      console.log(`\n📋 Browser Console Messages (${consoleLogs.length} total):`);
      const errors = consoleLogs.filter((l) => l.type === 'error');
      const warnings = consoleLogs.filter((l) => l.type === 'warning');
      const logs = consoleLogs.filter((l) => l.type === 'log');
      const debugs = consoleLogs.filter((l) => l.type === 'debug');

      if (errors.length > 0) {
        console.log(`\n  ❌ ERRORS (${errors.length}):`);
        errors.forEach((log) => {
          console.log(`    - [${log.timestamp}] ${log.message}`);
          if (log.location) console.log(`      at ${log.location}`);
        });
      }

      if (warnings.length > 0) {
        console.log(`\n  ⚠️ WARNINGS (${warnings.length}):`);
        warnings.forEach((log) => {
          console.log(`    - [${log.timestamp}] ${log.message}`);
        });
      }

      if (logs.length > 0) {
        console.log(`\n  ℹ️ LOGS (${logs.length}):`);
        logs.forEach((log) => {
          console.log(`    - [${log.timestamp}] ${log.message}`);
        });
      }

      if (debugs.length > 0) {
        console.log(`\n  🐛 DEBUG (${debugs.length}):`);
        debugs.forEach((log) => {
          console.log(`    - [${log.timestamp}] ${log.message}`);
        });
      }
    } else {
      console.log('\n✅ No console messages captured');
    }

    if (networkErrors.length > 0) {
      console.log(`\n🌐 Network Errors (${networkErrors.length}):`);
      networkErrors.forEach((err) => {
        console.log(`  ❌ [${err.status}] ${err.statusText} - ${err.url}`);
      });
    } else {
      console.log('\n✅ No network errors detected');
    }

    console.log('\n' + '='.repeat(80) + '\n');
  });

  test('01-capture-homepage-logs', async ({ page }) => {
    console.log('\n🌐 Loading homepage: http://localhost:3003');
    await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

    const title = await page.title();
    console.log(`✓ Page title: "${title}"`);

    // Wait a bit for any deferred JS to execute
    await page.waitForTimeout(2000);

    // Check if app root exists
    const appRoot = await page.$('#root');
    if (appRoot) {
      console.log('✓ App root element (#root) found');
    } else {
      console.log('⚠️ App root element (#root) not found');
    }
  });

  test('02-capture-api-calls-logs', async ({ page }) => {
    console.log('\n🌐 Loading application and monitoring API calls');
    await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

    // Wait for initial API calls to complete
    await page.waitForTimeout(3000);

    // Get all API calls made to backend
    const apiCalls: { url: string; status: number }[] = [];
    page.on('response', (response) => {
      if (response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status(),
        });
      }
    });

    // Wait a bit longer to catch any subsequent API calls
    await page.waitForTimeout(2000);

    if (apiCalls.length > 0) {
      console.log(`\n✓ API Calls Made (${apiCalls.length}):`);
      apiCalls.forEach((call) => {
        const statusIcon = call.status < 400 ? '✓' : '❌';
        console.log(`  ${statusIcon} [${call.status}] ${call.url}`);
      });
    } else {
      console.log('\nℹ️ No API calls detected');
    }
  });

  test('03-test-button-interactions', async ({ page }) => {
    console.log('\n🌐 Testing interactive elements');
    await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

    // Find and list all buttons
    const buttons = await page.$$('button');
    console.log(`\nFound ${buttons.length} buttons on page`);

    if (buttons.length > 0) {
      console.log('\nButton Details:');
      for (let i = 0; i < Math.min(buttons.length, 5); i++) {
        const text = await buttons[i].textContent();
        const disabled = await buttons[i].isDisabled();
        console.log(
          `  Button ${i + 1}: "${text?.trim()}" ${disabled ? '[DISABLED]' : '[ENABLED]'}`
        );
      }
    }

    // Look for any error messages on the page
    const errorElements = await page.$$('[class*="error"], [role="alert"]');
    if (errorElements.length > 0) {
      console.log(`\n⚠️ Found ${errorElements.length} error/alert elements on page:`);
      for (const elem of errorElements) {
        const text = await elem.textContent();
        console.log(`  - ${text?.trim()}`);
      }
    }
  });

  test('04-check-localStorage-and-sessionStorage', async ({ page }) => {
    console.log('\n💾 Checking browser storage');
    await page.goto('http://localhost:3003', { waitUntil: 'networkidle' });

    const storage = await page.evaluate(() => {
      const local = Object.fromEntries(
        Object.entries(localStorage).map(([k, v]) => [
          k,
          v.length > 100 ? `${v.substring(0, 100)}...` : v,
        ])
      );
      const session = Object.fromEntries(
        Object.entries(sessionStorage).map(([k, v]) => [
          k,
          v.length > 100 ? `${v.substring(0, 100)}...` : v,
        ])
      );
      return { localStorage: local, sessionStorage: session };
    });

    if (Object.keys(storage.localStorage).length > 0) {
      console.log('\n📦 LocalStorage:');
      Object.entries(storage.localStorage).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });
    } else {
      console.log('\n📦 LocalStorage: (empty)');
    }

    if (Object.keys(storage.sessionStorage).length > 0) {
      console.log('\n📦 SessionStorage:');
      Object.entries(storage.sessionStorage).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });
    } else {
      console.log('\n📦 SessionStorage: (empty)');
    }
  });
});
