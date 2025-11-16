# E2E Test Suite Documentation

## Overview

This document describes all End-to-End tests in the MATHESIS LAB project. These tests focus on user interactions, feature availability, and UI/UX verification using Playwright.

## Test Files

### 1. gcp-features.spec.ts

**Purpose**: Verify Google Cloud Platform integration features are properly rendered and functional.

#### Test Suite: "GCP Features Integration"

| Test # | Name | Purpose | Assertions | Screenshots |
|--------|------|---------|-----------|-------------|
| 1 | `should display GCP Settings page heading and main layout` | Verify GCP Settings page loads with main heading | GCP Settings heading visible | gcp-settings-page.png |
| 2 | `should display all three tab buttons for GCP feature navigation` | Verify all tabs (Overview, Backup, Sync) are present | All three tabs visible | gcp-tabs-navigation.png |
| 3 | `should display Backup Manager component on tab click` | Verify Backup tab shows BackupManager component | Create Backup button visible after tab click | backup-manager-component.png |
| 4 | `should display Multi-Device Sync section on tab click` | Verify Sync tab shows synchronization options | Register device button/section visible | multi-device-sync.png |
| 5 | `should show overview tab active with feature cards by default` | Verify Overview tab is active on initial load | Overview tab has active class; feature cards visible | gcp-overview-tab.png |
| 6 | `should display AIAssistant in node editor when available` | Verify AI Assistant component renders in editor | Summarize, Expand, Manim buttons visible (when available) | ai-assistant-component.png |
| 7 | `should handle create backup flow with screenshots at each step` | Verify complete backup creation flow works | Backup tab clickable; Create Backup button clickable; modal appears; form can be filled | 01-backup-tab-before-click.png, 02-backup-tab-after-click.png, 03-create-backup-before-click.png, 04-create-backup-modal-opened.png, 05-create-backup-form-filled.png |
| 8 | `should display GCP status information card` | Verify GCP status/health information displays | Status card/information visible on overview | gcp-status-card.png |
| 9 | `should display feature availability cards` | Verify all feature availability indicators | Cloud Storage, Backup, Sync feature cards visible | feature-cards.png |
| 10 | `should display error handling UI elements` | Verify page handles errors gracefully | GCP Settings heading visible; page loads without errors | gcp-full-page-layout.png |
| 11 | `should be responsive on mobile devices` | Verify responsive design on iPhone 12 viewport | Page renders on 390x844 viewport; tabs clickable; content scrollable on mobile | mobile-01-overview-initial.png, mobile-02-overview-scrolled.png, mobile-03-backup-tab.png, mobile-04-backup-scrolled.png |
| 12 | `should handle tab switching with proper content transitions` | Verify smooth tab switching between Overview, Backup, Sync | Each tab shows correct content; scrolling works on each tab; tab transitions smooth | tab-01-overview-initial.png, tab-02-overview-scrolled.png, tab-03-backup-opened.png, tab-04-backup-scrolled.png, tab-05-sync-opened.png, tab-06-sync-scrolled.png |
| 13 | `should verify styling and layout consistency` | Verify CSS styles applied correctly | Heading has font size, color, font weight; page layout matches design | gcp-complete-layout.png |

**Setup**: All tests navigate to `http://localhost:3002/#/gcp-settings` and wait for network idle.

#### Test Assertions Summary

- **Navigation**: All tests verify that routing to GCP Settings works
- **UI Visibility**: Tests verify key UI elements are visible (tabs, buttons, cards)
- **Interaction**: Some tests verify click actions work (tab switches, button clicks)
- **Responsive Design**: Mobile viewport tests verify layout on 390x844 (iPhone 12)
- **Screenshots**: All tests capture screenshots at key points for visual regression testing

---

### 2. node-type-selector.spec.ts

**Purpose**: Verify basic app functionality, DOM structure, and user interaction capabilities using the Node Type Selector as a test vehicle.

#### Test Suite: "Node Type Selector E2E with Screenshots"

| Test # | Name | Purpose | Assertions | Screenshots |
|--------|------|---------|-----------|-------------|
| 1 | `01-app-loads-successfully` | Verify application loads and initializes | Page has title; app container (#root) exists; page fully loads | app-loads-01-initial-load.png, app-loads-02-page-ready.png, app-loads-03-app-verified.png |
| 2 | `02-find-and-verify-buttons` | Verify button elements are present on page | At least one button found on page; page DOM is populated | buttons-verification-01-initial-state.png, buttons-verification-02-buttons-found.png, buttons-verification-03-verified.png |
| 3 | `03-app-network-status` | Verify application loads over HTTP and network status | HTTP 200 response from server; navigator.onLine is true; network is functional | network-status-01-navigated.png, network-status-02-network-ok.png, network-status-03-online-verified.png |
| 4 | `04-check-styling` | Verify CSS/styling is loaded | Stylesheets are loaded (link[rel="stylesheet"] elements); page styling is applied | styling-01-initial.png, styling-02-stylesheets-loaded.png, styling-03-styled.png |
| 5 | `05-interact-with-page-elements` | Verify user interactions (hover, navigation) | Links exist on page; links are hoverable; hover effects work | interaction-01-initial-state.png, interaction-02-links-found.png, interaction-03-hover-effect.png, interaction-04-complete.png |
| 6 | `06-dom-structure-verification` | Verify proper DOM structure | Body element exists; header/heading elements found; HTML content non-empty | dom-structure-01-initial.png, dom-structure-02-body-found.png, dom-structure-03-headers-found.png, dom-structure-04-html-verified.png |

**Setup**: All tests navigate to `/` (app root) and wait for network idle.

#### Test Assertions Summary

- **Page Load**: Tests verify basic page loading and initialization
- **DOM Structure**: Tests check for expected HTML elements (body, headers, buttons, links)
- **Network**: Tests verify HTTP connectivity and online status
- **Styling**: Tests verify CSS resources load
- **Interactions**: Tests verify basic user interactions like hover work
- **Screenshots**: All tests take screenshots at multiple steps for debugging and documentation

---

## Test Execution

### Running All E2E Tests

```bash
cd MATHESIS-LAB_FRONT
npx playwright test e2e/
```

### Running Specific Test File

```bash
# GCP Features tests
npx playwright test e2e/gcp-features.spec.ts

# Node Type Selector tests
npx playwright test e2e/node-type-selector.spec.ts
```

### Running Specific Test

```bash
npx playwright test e2e/gcp-features.spec.ts -g "should display all three tab buttons"
```

### Running with UI Mode

```bash
npx playwright test e2e/ --ui
```

### Running in Headed Mode (see browser)

```bash
npx playwright test e2e/ --headed
```

---

## Screenshot Capture Strategy

All tests capture screenshots at key points:

1. **Initial State**: Before any user interactions
2. **After Interactions**: After clicking buttons, switching tabs, etc.
3. **Final State**: After all operations complete

This enables:
- Visual regression testing
- Documentation of feature flows
- Debugging of failures
- Report generation with screenshots

Screenshots are stored in: `/MATHESIS-LAB_FRONT/e2e-screenshots/`

---

## Test Quality Metrics

**Current Test Coverage:**
- GCP Features: 13 tests
- Basic App Functionality: 6 tests
- **Total: 19 E2E tests**

**Coverage Areas:**
- ✅ Page navigation and routing
- ✅ Tab switching and feature navigation
- ✅ Component visibility (buttons, forms, cards)
- ✅ User interactions (clicks, hover, scrolling)
- ✅ Responsive design (mobile viewport)
- ✅ Network connectivity
- ✅ DOM structure
- ✅ CSS/Styling loading

**Known Limitations:**
- Some tests use optional assertions (`.catch(() => false)`) for graceful degradation
- Mobile tests only cover iPhone 12 viewport
- No form submission or data validation tests yet
- No error state tests yet

---

## Future Enhancements

### Recommended Test Additions

1. **Form Submission Tests**
   - Test CreateNodeModal form submission
   - Test backup creation form with data
   - Test sync configuration forms

2. **Error State Tests**
   - Test behavior when API calls fail
   - Test error message display
   - Test error recovery flows

3. **Data Validation Tests**
   - Test form validation (required fields)
   - Test invalid input handling
   - Test data persistence across page reloads

4. **Cross-Browser Testing**
   - Test on Firefox, Safari, Edge
   - Test on different OS (Windows, macOS, Linux)

5. **Performance Tests**
   - Measure page load time
   - Measure time to first interactive
   - Test with network throttling

6. **Accessibility Tests**
   - Test keyboard navigation
   - Test screen reader compatibility
   - Test ARIA attributes

---

## Debugging Failed Tests

### Common Issues

1. **Timeout errors**: Increase `waitForTimeout` value or check if element selector is correct
2. **Element not found**: Use browser dev tools to verify selector works
3. **Screenshot path errors**: Ensure `e2e-screenshots/` directory exists
4. **Network errors**: Verify backend server is running on port 8000

### Debugging Steps

1. Run with `--headed` flag to see browser
2. Run with `--debug` flag to step through test
3. Check screenshot output for visual clues
4. Verify selectors with Playwright Inspector
5. Check browser console for JavaScript errors

---

## Integration with CI/CD

These tests are designed to run in GitHub Actions:

```yaml
- name: Run E2E tests
  run: npx playwright test e2e/
```

Tests will:
1. Capture screenshots on failure
2. Generate HTML report
3. Upload artifacts
4. Fail build if tests fail

See `.github/workflows/` for CI configuration.

---

## References

- [Playwright Documentation](https://playwright.dev)
- [Test Configuration](../playwright.config.ts)
- [GCP Features Implementation](../components/GCPSettings.tsx)
- [Backup Manager Component](../components/BackupManager.tsx)
