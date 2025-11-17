# Frontend Testing Guide

## Overview

This document outlines the frontend testing strategy for MATHESIS LAB, covering unit tests, integration tests, and E2E tests.

## Test Stack

- **Framework**: Vitest + React Testing Library
- **E2E Testing**: Playwright
- **Coverage Target**: 80%+

## Test Structure

```
MATHESIS-LAB_FRONT/
├── __tests__/                    # Unit and integration tests
├── e2e/                          # End-to-end tests
│   ├── gcp-features.spec.ts      # GCP Settings page tests
│   ├── capture-frontend-logs.spec.ts
│   ├── node-type-selector.spec.ts
│   └── generate-test-report.mjs  # Test report generator
├── components/                   # React components
├── pages/                        # Page components
├── services/                     # API services
└── types.ts                      # TypeScript definitions
```

## Unit & Integration Tests

### Running Tests

```bash
cd MATHESIS-LAB_FRONT

# Run all tests
npm test

# Run specific test file
npm test ComponentName.test.tsx

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Test Files Naming Convention

- **Component Tests**: `components/ComponentName.test.tsx`
- **Page Tests**: `pages/PageName.test.tsx`
- **Service Tests**: `services/serviceName.test.ts`

### Example Test Structure

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GCPSettings } from './GCPSettings';

describe('GCPSettings Component', () => {
  beforeEach(() => {
    // Setup before each test
  });

  it('should render GCP Settings heading', () => {
    render(<GCPSettings />);
    expect(screen.getByText(/GCP Settings/i)).toBeInTheDocument();
  });

  it('should display available features', () => {
    render(<GCPSettings />);
    expect(screen.getByText(/Cloud Storage/i)).toBeVisible();
  });
});
```

### Current Test Status

✅ **159 tests passed**
⏭️ **9 tests skipped**
📊 **Test Duration**: ~22 seconds

### Key Tests

#### GCPSettings Component Tests
- Rendering with mock data
- Feature card visibility
- Tab switching functionality
- Error state handling
- Loading states

#### CurriculumEditor Tests
- Create curriculum
- Edit curriculum properties
- Delete curriculum
- Node management

#### NodeEditor Tests
- Node content display
- Linked resources management
- AI Assistant integration
- Error handling

## E2E Tests (Playwright)

### Running E2E Tests

```bash
cd MATHESIS-LAB_FRONT

# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test e2e/gcp-features.spec.ts

# Run with UI mode
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

### E2E Test Files

#### 1. **gcp-features.spec.ts**
Tests for GCP Settings page functionality
- ✅ Display GCP Settings page heading
- ✅ Display tab buttons
- ✅ Backup Manager component
- ✅ Multi-Device Sync section
- ✅ Feature availability cards
- ✅ GCP status information display

#### 2. **capture-frontend-logs.spec.ts**
Frontend console log capture tests
- Captures all console messages
- Detects console errors
- Monitors network requests
- Validates page structure

#### 3. **node-type-selector.spec.ts**
Node type selector functionality tests
- App loading verification
- Button visibility checks
- Network status verification
- Styling consistency

### Current E2E Test Status

✅ **23 tests passed** (18.9s)
- GCP Features Integration: 13 tests
- Frontend Console Log Capture: 4 tests
- Node Type Selector: 6 tests

## Test Report Generation

### Overview

A comprehensive test report generator that captures:
- Page screenshots
- Console logs with timestamps
- Network requests and status codes
- Test results summary

### Running Report Generator

```bash
cd MATHESIS-LAB_FRONT
node e2e/generate-test-report.mjs
```

### Generated Report Structure

```
test-report-with-logs/
├── index.html                    # HTML report
├── summary.json                  # Test results summary
├── screenshots/                  # Page screenshots
│   ├── gcp-settings-page.png
│   ├── home-page.png
│   └── curriculum-list.png
└── logs/                         # Detailed test logs (JSON)
    ├── gcp-settings-page.json
    ├── home-page.json
    └── curriculum-list.json
```

### Report Contents

#### HTML Report
- Visual test summary with pass/fail counts
- Screenshots for each tested page
- Links to detailed JSON logs
- Network request counts
- Console error summary

#### JSON Logs

Each log file contains:

```json
{
  "test": "GCP Settings Page",
  "url": "http://localhost:3002/#/gcp-settings",
  "timestamp": "2025-11-17T00:55:44.409Z",
  "status": "✅ PASS",
  "consoleLogs": [
    {
      "type": "warning|error|info|debug",
      "text": "Log message",
      "timestamp": "ISO timestamp"
    }
  ],
  "consoleErrors": [
    // Only error-type console messages
  ],
  "networkRequests": [
    {
      "url": "http://...",
      "status": 200,
      "method": "GET",
      "timestamp": "ISO timestamp"
    }
  ],
  "checksPass": true
}
```

## Key Testing Areas

### 1. GCP Settings Page

**What to Test:**
- Page loads without errors
- All UI elements render correctly
- Network requests to backend succeed
- Console has no errors
- Feature cards display properly
- Tab navigation works

**Test File:** `e2e/gcp-features.spec.ts`

**Expected Results:**
```
✅ No console errors
✅ GCP Settings heading visible
✅ Available Features section visible
✅ GCP Integration Status section visible
✅ Network requests: 40+ (normal)
```

### 2. API Integration

**Endpoints Tested:**
- `GET /api/v1/gcp/status` - GCP status check
- `GET /api/v1/gcp/sync-devices` - Device list
- `GET /api/v1/curriculums` - Curriculum list
- `POST /api/v1/nodes` - Create node

**Verification:**
- Status codes are 200/201
- Response structure matches TypeScript types
- No network errors in console logs

### 3. Component Rendering

**Components Verified:**
- GCPSettings
- BackupManager
- MultiDeviceSync
- AIAssistant
- CreateNodeModal
- CurriculumEditor

**Checks:**
- Props render correctly
- Event handlers work
- Loading/error states display
- Conditional rendering works

## Common Issues & Debugging

### Issue: E2E Test Timeout

**Cause:** Page taking too long to load or selector not found

**Solution:**
```bash
# Increase timeout in test
await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });

# Use explicit wait
await page.waitForSelector('selector', { timeout: 10000 });
```

### Issue: Console Error in Tests

**Debug:** Check the generated JSON logs

```bash
cat test-report-with-logs/logs/gcp-settings-page.json | grep -A5 "consoleErrors"
```

**Common Causes:**
- Missing API responses
- TypeScript type mismatches
- React props validation failures

### Issue: Screenshot Not Generated

**Check:**
```bash
ls -la test-report-with-logs/screenshots/
```

**Solution:** Ensure viewport is set before screenshot:
```typescript
await page.setViewportSize({ width: 1280, height: 720 });
await page.screenshot({ path: 'screenshot.png' });
```

## Best Practices

### ✅ DO

1. **Test User Interactions**
   ```typescript
   await page.click('button:has-text("Create")');
   ```

2. **Wait for Elements**
   ```typescript
   await page.waitForSelector('text=Success');
   ```

3. **Verify Console Logs**
   ```typescript
   expect(consoleErrors).toHaveLength(0);
   ```

4. **Test Error States**
   ```typescript
   // Mock API error
   page.route('**/api/v1/**', route => {
     route.abort('failed');
   });
   ```

5. **Use Descriptive Test Names**
   ```typescript
   test('should display GCP Settings page with all feature cards', async () => {
   ```

### ❌ DON'T

1. **Hardcode Timeouts**
   - Use `waitForSelector` instead
   - Use `waitForLoadState('networkidle')`

2. **Test Implementation Details**
   - Test user-visible behavior instead
   - Don't test internal state directly

3. **Create Test Dependencies**
   - Each test should be independent
   - Don't rely on test execution order

4. **Ignore Console Errors**
   - Always check and fix console errors
   - They indicate real problems

5. **Skip Accessibility Testing**
   - Use semantic HTML
   - Test keyboard navigation
   - Verify ARIA labels

## Continuous Integration

### GitHub Actions (Recommended Setup)

```yaml
name: Frontend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '22'

      - name: Install dependencies
        run: npm install

      - name: Run unit tests
        run: npm test

      - name: Run E2E tests
        run: npx playwright test

      - name: Generate test report
        if: always()
        run: node e2e/generate-test-report.mjs

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test-report-with-logs/
```

## Performance Monitoring

### Metrics to Track

1. **Test Duration**
   - Unit tests: < 30 seconds
   - E2E tests: < 5 minutes
   - Report generation: < 2 minutes

2. **Coverage**
   - Target: 80%+
   - Current: Track with `npm test -- --coverage`

3. **Flaky Tests**
   - Monitor test stability
   - Fix timeout-related flakiness
   - Improve selectors if needed

## Troubleshooting Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend dev server is running on port 3002
- [ ] All dependencies are installed (`npm install`)
- [ ] Node version is 20+ (`node --version`)
- [ ] Screenshots directory exists
- [ ] No leftover browser processes (`pkill -f chromium`)
- [ ] Network requests are responding (check browser console)
- [ ] API endpoints are accessible

## References

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)

## Additional Resources

### Test Report Location
```
MATHESIS-LAB_FRONT/test-report-with-logs/index.html
```

### View in Browser
```bash
# Generate report
node e2e/generate-test-report.mjs

# Open in browser (macOS)
open test-report-with-logs/index.html

# Open in browser (Linux)
xdg-open test-report-with-logs/index.html

# Open in browser (Windows)
start test-report-with-logs/index.html
```

## Summary

| Category | Status | Details |
|----------|--------|---------|
| Unit Tests | ✅ 159 passed | ~22s duration |
| E2E Tests | ✅ 23 passed | ~19s duration |
| Coverage | 📊 In progress | Target: 80%+ |
| Test Reports | ✅ Generated | Screenshots + logs |
| CI/CD | 📋 Recommended | GitHub Actions setup |

---

Last Updated: November 17, 2025
Maintained by: MATHESIS LAB Development Team
