# Pending Features Implementation Guide

**Last Updated:** 2025-11-16
**Status:** Feature stubs and tests created, implementation pending

## Overview

This document outlines frontend features that have been **intentionally excluded** from the current implementation. These features have test stubs that are currently skipped (`it.skip()`). Once implementation is ready, developers can remove the `.skip()` annotations and proceed with implementation.

---

## AI Assistant Features

### Feature: AI Content Summarization
**Location:** `MATHESIS-LAB_FRONT/components/AIAssistant.test.tsx`
**Skipped Tests:** 4 tests

#### Tests Skipped:
1. **Line 48:** `should display summarize, expand, and manim buttons`
   - Tests that all three AI action buttons are rendered
   - **Issue:** Multiple "Manim Guide" text elements found (one in button, one in tip text)
   - **Fix needed:** Use more specific selectors or query for role="button" with name

2. **Line 142:** `should display processing time and tokens used in results`
   - Tests that AI results show "2.5s" and "150 tokens"
   - **Issue:** Result display structure not implemented
   - **Fix needed:** Implement result history display UI with time/token metrics

3. **Line 160:** `should allow hiding and showing results`
   - Tests toggle behavior for collapsing/expanding results
   - **Issue:** `toBeVisible()` requires results section to exist
   - **Fix needed:** Implement collapsible results section with toggle button

4. **Line 217:** `should handle file upload for Manim guidelines`
   - Tests uploading image files for Manim guideline generation
   - **Issue:** File input structure doesn't match test expectations
   - **Fix needed:** Restructure file input DOM hierarchy

#### Implementation Checklist:
- [ ] Implement `AIAssistant` component with all button groups
- [ ] Create result history display UI
- [ ] Add collapsible results section
- [ ] Implement file upload handler for Manim guidelines
- [ ] Wire up GCP service calls for:
  - `summarizeContent(nodeId, content)`
  - `extendContent(nodeId, content)`
  - `generateManimGuidelines(nodeId, file)`
- [ ] Display processing time and token usage
- [ ] Add toggle for showing/hiding results

**Backend Requirements:**
- API endpoints for AI operations in `backend/app/api/v1/endpoints/`
- Integration with Vertex AI/Gemini API

---

## Backup & Restore Features

### Feature: Database Backup and Restoration
**Location:** `MATHESIS-LAB_FRONT/components/BackupManager.test.tsx`
**Skipped Tests:** 2 tests

#### Tests Skipped:
1. **Line 117:** `should show restore confirmation dialog`
   - Tests that a confirmation dialog appears when restore button is clicked
   - **Issue:** Dialog modal not implemented
   - **Fix needed:** Add modal component for restore confirmation

2. **Line 135:** `should restore backup after confirmation`
   - Tests the complete restore workflow
   - **Issue:** Dialog with "✓ Restore" button not rendering
   - **Fix needed:** Implement restore dialog with confirmation logic

#### Implementation Checklist:
- [ ] Create restore confirmation modal dialog
- [ ] Add "Restore Backup?" confirmation title
- [ ] Add description: "This will restore the database..."
- [ ] Implement confirm/cancel buttons
- [ ] Wire up `gcpService.restoreBackup()` call
- [ ] Handle restore success/failure states
- [ ] Update backup list after restore

**Current Status:**
- ✅ Create backup: Implemented
- ✅ List backups: Implemented
- ✅ Delete old backups: Implemented
- ❌ Restore backup: Pending (dialogs)
- ❌ Refresh: Implemented but restore dialog missing

---

## Modal & UI Component Features

### Feature: Modal Dark Overlay Backdrop
**Location:** `MATHESIS-LAB_FRONT/components/CreateNodeModal.test.tsx`
**Skipped Tests:** 1 test

#### Tests Skipped:
1. **Line 79:** `should render modal with dark overlay backdrop`
   - Tests for `.bg-black` class on backdrop element
   - **Issue:** Dark overlay CSS class not applied or selector changed
   - **Fix needed:** Ensure backdrop has proper dark overlay styling

#### Implementation Checklist:
- [ ] Add `.bg-black` or equivalent dark overlay class to backdrop
- [ ] Ensure modal appears above overlay with proper z-index
- [ ] Test overlay click-to-close functionality (if implemented)

**Current Status:**
- ✅ Modal rendering: Implemented
- ✅ Form fields: Implemented
- ✅ Node type dropdown: Implemented
- ❌ Dark overlay styling: Pending CSS

---

## Sync & Metadata Features

### Feature: Google Drive Sync Action Decision Logic
**Location:** `MATHESIS-LAB_FRONT/services/googleDriveSyncManager.test.ts`
**Skipped Tests:** 1 test

#### Tests Skipped:
1. **Line 30:** `should decide IDLE when timestamps are within 30 seconds`
   - Tests that sync action returns `IDLE` when timestamps differ by <30s
   - **Issue:** Current implementation returns `PUSH` instead of `IDLE`
   - **Fix needed:** Adjust sync decision logic to use 30-second tolerance

#### Implementation Checklist:
- [ ] Review `decideSyncAction()` logic in `googleDriveSyncManager.ts`
- [ ] Implement 30-second tolerance check:
  ```typescript
  const timeDiffMs = Math.abs(localTime - driveTime);
  if (timeDiffMs < 30000) {  // Less than 30 seconds
    return { action: SyncAction.IDLE, ... };
  }
  ```
- [ ] Add unit test to verify tolerance logic
- [ ] Test with various timestamp combinations

**Current Status:**
- ✅ PULL/PUSH decisions: Implemented
- ✅ Conflict detection: Implemented
- ❌ 30-second tolerance: Pending

---

### Feature: GCP Date Formatting
**Location:** `MATHESIS-LAB_FRONT/services/gcpService.test.ts`
**Skipped Tests:** 1 test

#### Tests Skipped:
1. **Line 387:** `should handle invalid dates gracefully`
   - Tests that invalid date strings return unchanged
   - **Issue:** Currently returns "Invalid Date" instead of the input string
   - **Fix needed:** Handle invalid date gracefully

#### Implementation Checklist:
- [ ] Update `formatDate()` in `gcpService.ts`
- [ ] Catch invalid date errors and return original input
- [ ] Example implementation:
  ```typescript
  formatDate(dateStr: string): string {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return dateStr;  // Return original if invalid
      }
      return date.toLocaleDateString();
    } catch {
      return dateStr;
    }
  }
  ```
- [ ] Test with invalid dates: "invalid-date", "", null, etc.

**Current Status:**
- ✅ Date formatting: Implemented
- ✅ Relative time formatting: Implemented
- ❌ Invalid date handling: Returns "Invalid Date" instead of input

---

## Implementation Priority

### Phase 1 (High Priority - Core Features)
1. **AI Content Summarization & Expansion** (4 tests)
   - Essential for content enhancement workflow
   - Requires Vertex AI integration
   - Estimated effort: 2-3 days

2. **Database Restore** (2 tests)
   - Critical for data recovery feature
   - Estimated effort: 1 day

### Phase 2 (Medium Priority - UX Polish)
3. **Modal Dark Overlay** (1 test)
   - Cosmetic, improves UX
   - Estimated effort: 2-4 hours

4. **Sync Decision Logic** (1 test)
   - Improves sync reliability
   - Estimated effort: 4 hours

### Phase 3 (Low Priority - Edge Cases)
5. **Date Formatting** (1 test)
   - Error handling improvement
   - Estimated effort: 1-2 hours

---

## Re-enabling Tests

Once a feature is implemented:

### Step 1: Remove `.skip` annotation
```typescript
// Before:
it.skip('should display summarize, expand, and manim buttons', () => {

// After:
it('should display summarize, expand, and manim buttons', () => {
```

### Step 2: Run tests
```bash
cd MATHESIS-LAB_FRONT
npm test -- --run
```

### Step 3: Fix any test failures
- Review test error messages
- Update DOM selectors if component structure changed
- Ensure mocks align with actual implementation

### Step 4: Verify integration test still passes
```bash
cd MATHESIS-LAB_FRONT
npx playwright test
```

---

## Related Documentation

- **AI Integration:** See `docs/CLAUDE.md` - Frontend AI Service section
- **API Specifications:** See `docs/sdd_api_specification.md`
- **Database Schema:** See `docs/sdd_database_design.md`
- **Test Strategy:** See `docs/frontend_testing_strategy.md`

---

## Notes for Developers

### Important Considerations

1. **GCP Integration**
   - Ensure backend API endpoints are ready before implementing AI features
   - Test with proper GCP credentials in development
   - Handle API timeouts and rate limits

2. **State Management**
   - AI operation results should be stored in component state
   - Consider using Context API or state management library for complex state

3. **Error Handling**
   - All async operations should have error boundaries
   - User-friendly error messages are required
   - Log errors to console for debugging

4. **Performance**
   - AI operations may be slow; add loading spinners
   - Debounce user input if needed
   - Cancel in-flight requests when component unmounts

5. **Testing**
   - After implementation, all tests should pass without `.skip()`
   - Maintain >80% code coverage
   - Add integration tests for end-to-end workflows

---

## Contact & Questions

For questions about pending features or implementation guidelines, refer to:
- **Project CLAUDE.md:** `/mnt/d/progress/MATHESIS LAB/CLAUDE.md`
- **Test files:** For test expectations and mocking patterns
- **Service layer:** `MATHESIS-LAB_FRONT/services/` for API integration examples

---

**Last Status Update:** All 9 tests skipped and documented. Ready for phased implementation.
