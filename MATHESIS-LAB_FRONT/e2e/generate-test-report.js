const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(__dirname, '../test-report-with-logs');
const SCREENSHOTS_DIR = path.join(REPORT_DIR, 'screenshots');
const LOGS_DIR = path.join(REPORT_DIR, 'logs');

// Create directories
[REPORT_DIR, SCREENSHOTS_DIR, LOGS_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

const tests = [
  {
    name: 'GCP Settings Page',
    url: 'http://localhost:3002/#/gcp-settings',
    checks: [
      { selector: 'h1', expectText: 'GCP Settings' },
      { selector: 'text=Available Features', expectVisible: true },
      { selector: 'text=GCP Integration Status', expectVisible: true },
    ]
  },
  {
    name: 'Home Page',
    url: 'http://localhost:3002/',
    checks: [
      { selector: 'h1', expectText: null },
    ]
  },
  {
    name: 'Curriculum List',
    url: 'http://localhost:3002/#/curriculums',
    checks: [
      { selector: 'button', expectVisible: true },
    ]
  }
];

(async () => {
  const browser = await chromium.launch();
  const results = [];

  for (const test of tests) {
    console.log(`\n🧪 Testing: ${test.name}`);
    console.log(`📍 URL: ${test.url}`);

    const page = await browser.newPage();
    const consoleLogs = [];
    const consoleErrors = [];
    const networkRequests = [];

    // Collect console logs
    page.on('console', msg => {
      const logEntry = {
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString()
      };
      consoleLogs.push(logEntry);
      if (msg.type() === 'error') {
        consoleErrors.push(logEntry);
      }
    });

    // Collect network requests
    page.on('response', response => {
      networkRequests.push({
        url: response.url(),
        status: response.status(),
        method: response.request().method(),
        timestamp: new Date().toISOString()
      });
    });

    try {
      // Set viewport
      await page.setViewportSize({ width: 1280, height: 720 });

      // Navigate
      console.log('  ⏳ Loading...');
      await page.goto(test.url, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(500);

      // Perform checks
      let checksPass = true;
      for (const check of test.checks) {
        try {
          if (check.expectText !== null) {
            const element = await page.locator(check.selector);
            const text = await element.textContent();
            const pass = text && text.includes(check.expectText);
            console.log(`  ${pass ? '✅' : '❌'} Check: "${check.expectText}" in ${check.selector}`);
            if (!pass) checksPass = false;
          } else if (check.expectVisible !== null) {
            const element = await page.locator(check.selector);
            const visible = await element.isVisible().catch(() => false);
            console.log(`  ${visible ? '✅' : '❌'} Check: Visible ${check.selector}`);
            if (!visible) checksPass = false;
          }
        } catch (err) {
          console.log(`  ❌ Check failed: ${err.message}`);
          checksPass = false;
        }
      }

      // Take screenshot
      const screenshotPath = path.join(SCREENSHOTS_DIR, `${test.name.replace(/\s+/g, '-').toLowerCase()}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`  📸 Screenshot: ${path.basename(screenshotPath)}`);

      // Save logs
      const logPath = path.join(LOGS_DIR, `${test.name.replace(/\s+/g, '-').toLowerCase()}.json`);
      fs.writeFileSync(logPath, JSON.stringify({
        test: test.name,
        url: test.url,
        timestamp: new Date().toISOString(),
        status: consoleErrors.length === 0 ? '✅ PASS' : '❌ FAIL',
        consoleLogs: consoleLogs,
        consoleErrors: consoleErrors,
        networkRequests: networkRequests,
        checksPass: checksPass
      }, null, 2));
      console.log(`  📝 Logs: ${path.basename(logPath)}`);

      results.push({
        name: test.name,
        url: test.url,
        status: consoleErrors.length === 0 && checksPass ? 'PASS' : 'FAIL',
        errors: consoleErrors.length,
        requests: networkRequests.length
      });

    } catch (err) {
      console.log(`  ❌ Error: ${err.message}`);
      results.push({
        name: test.name,
        url: test.url,
        status: 'ERROR',
        error: err.message
      });
    } finally {
      await page.close();
    }
  }

  // Generate summary report
  const summary = {
    generatedAt: new Date().toISOString(),
    totalTests: tests.length,
    passed: results.filter(r => r.status === 'PASS').length,
    failed: results.filter(r => r.status === 'FAIL').length,
    errors: results.filter(r => r.status === 'ERROR').length,
    results: results
  };

  const reportPath = path.join(REPORT_DIR, 'summary.json');
  fs.writeFileSync(reportPath, JSON.stringify(summary, null, 2));

  // Generate HTML report
  const htmlReport = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>E2E Test Report</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    h1 { color: #333; margin-bottom: 30px; }
    .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
    .summary-card { padding: 15px; border-radius: 6px; color: white; text-align: center; }
    .summary-card.total { background: #2196F3; }
    .summary-card.pass { background: #4CAF50; }
    .summary-card.fail { background: #f44336; }
    .summary-card.error { background: #ff9800; }
    .summary-card h3 { font-size: 32px; margin-bottom: 5px; }
    .summary-card p { font-size: 12px; opacity: 0.9; }
    .test-results { margin-top: 30px; }
    .test-card { border: 1px solid #ddd; border-radius: 6px; margin-bottom: 20px; overflow: hidden; }
    .test-header { padding: 15px 20px; background: #f9f9f9; border-bottom: 1px solid #ddd; }
    .test-header h3 { margin: 0 0 5px 0; font-size: 16px; }
    .test-header p { margin: 5px 0; font-size: 12px; color: #666; }
    .test-status { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 10px; }
    .test-status.pass { background: #c8e6c9; color: #2e7d32; }
    .test-status.fail { background: #ffcdd2; color: #c62828; }
    .test-status.error { background: #ffe0b2; color: #e65100; }
    .test-body { padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .screenshot { }
    .screenshot img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
    .logs { }
    .logs h4 { margin-bottom: 10px; font-size: 13px; }
    .log-section { margin-bottom: 15px; }
    .log-section h5 { font-size: 11px; color: #666; margin-bottom: 5px; text-transform: uppercase; }
    .log-list { font-size: 11px; max-height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 3px; }
    .log-entry { margin-bottom: 5px; padding: 3px; border-left: 2px solid #ccc; padding-left: 8px; }
    .log-entry.error { border-left-color: #f44336; color: #f44336; }
    .log-entry.warning { border-left-color: #ff9800; color: #ff9800; }
    .log-entry.info { border-left-color: #2196F3; color: #2196F3; }
    .timestamp { font-size: 10px; color: #999; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🧪 E2E Test Report</h1>

    <div class="summary">
      <div class="summary-card total">
        <h3>${summary.totalTests}</h3>
        <p>Total Tests</p>
      </div>
      <div class="summary-card pass">
        <h3>${summary.passed}</h3>
        <p>Passed</p>
      </div>
      <div class="summary-card fail">
        <h3>${summary.failed}</h3>
        <p>Failed</p>
      </div>
      <div class="summary-card error">
        <h3>${summary.errors}</h3>
        <p>Errors</p>
      </div>
    </div>

    <div class="test-results">
      ${results.map((result, idx) => `
        <div class="test-card">
          <div class="test-header">
            <h3>${result.name} <span class="test-status ${result.status.toLowerCase()}">${result.status}</span></h3>
            <p>🔗 ${result.url}</p>
            ${result.errors ? `<p>❌ Console Errors: ${result.errors} | Network Requests: ${result.requests}</p>` : ''}
          </div>
          <div class="test-body">
            <div class="screenshot">
              <img src="screenshots/${result.name.replace(/\s+/g, '-').toLowerCase()}.png" alt="${result.name}" onerror="this.style.display='none';">
            </div>
            <div class="logs">
              <h4>📋 Logs & Details</h4>
              <div class="log-section">
                <h5>Summary</h5>
                <div class="log-list">
                  <div class="log-entry info">
                    <strong>Status:</strong> ${result.status}
                  </div>
                  <div class="log-entry ${result.errors > 0 ? 'error' : 'info'}">
                    <strong>Console Errors:</strong> ${result.errors || 0}
                  </div>
                  <div class="log-entry info">
                    <strong>Network Requests:</strong> ${result.requests || 0}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `).join('')}
    </div>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
      <p>📌 Report Generated: ${new Date().toLocaleString()}</p>
      <p>📂 Logs Location: <code>${LOGS_DIR}</code></p>
      <p>📸 Screenshots Location: <code>${SCREENSHOTS_DIR}</code></p>
    </div>
  </div>
</body>
</html>
  `;

  const htmlPath = path.join(REPORT_DIR, 'index.html');
  fs.writeFileSync(htmlPath, htmlReport);

  console.log('\n========================================');
  console.log('✅ Test Report Generated!');
  console.log('========================================');
  console.log(`📊 Summary: ${summary.passed}/${summary.totalTests} tests passed`);
  console.log(`📁 Report Location: ${REPORT_DIR}`);
  console.log(`🌐 Open: file://${htmlPath}`);
  console.log('========================================\n');

  await browser.close();
})();
