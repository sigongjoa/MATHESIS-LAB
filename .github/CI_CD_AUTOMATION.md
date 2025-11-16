# CI/CD Automation for MATHESIS LAB

## Overview

This document describes the automated testing and report generation infrastructure using GitHub Actions. The pipeline ensures code quality through comprehensive testing and generates detailed test reports automatically.

## GitHub Actions Workflow

**File**: `.github/workflows/test-and-report.yml`

### Workflow Triggers

The pipeline runs automatically on:
1. **Push events**: On branches `master`, `main`, `develop`
2. **Pull requests**: Against `master`, `main`, `develop`
3. **Manual trigger**: Via GitHub Actions interface

### Jobs Overview

#### 1. Backend Tests (test-backend)

**Purpose**: Run Python backend unit and integration tests using pytest

**Steps**:
1. Check out code with submodules
2. Set up Python 3.11 with cached dependencies
3. Create virtual environment (.venv)
4. Install backend dependencies from `backend/requirements.txt`
5. Run pytest on `backend/tests/` directory
6. Generate JUnit-format test results
7. Upload test results as artifact

**Configuration**:
- Python: 3.11
- Test framework: pytest
- Output: JUnit XML format
- Artifact name: `backend-test-results`

#### 2. Frontend Tests (test-frontend)

**Purpose**: Run React frontend tests using npm/vitest

**Steps**:
1. Check out code with submodules
2. Set up Node.js 22 with npm cache
3. Install dependencies in `MATHESIS-LAB_FRONT`
4. Run `npm test` with coverage
5. Upload coverage reports as artifact

**Configuration**:
- Node.js: 22.x LTS
- Package manager: npm
- Test framework: Vitest (React Testing Library)
- Coverage output
- Artifact name: `frontend-coverage`
- Note: `continue-on-error: true` prevents workflow failure if tests fail

#### 3. E2E Tests (test-e2e)

**Purpose**: Run Playwright end-to-end tests with backend service

**Services**:
- Backend running on `http://localhost:8000` (FastAPI + uvicorn)

**Steps**:
1. Check out code with submodules
2. Set up Node.js 22 with npm cache
3. Install frontend dependencies
4. Install Playwright browsers and system dependencies
5. Wait for backend service to be ready (timeout: 30s)
6. Run `npx playwright test e2e/`
7. Upload HTML test report
8. Upload E2E screenshots

**Configuration**:
- Node.js: 22.x
- Browser: Chromium (Playwright)
- Reporter: HTML with screenshots
- Artifacts: `e2e-report`, `e2e-screenshots`
- Note: `continue-on-error: true` allows subsequent jobs to run

#### 4. Generate Report (generate-report)

**Purpose**: Generate comprehensive test report combining all test results

**Depends on**: All three test jobs

**Steps**:
1. Check out code with submodules
2. Set up Python 3.11
3. Create virtual environment
4. Install all dependencies (pytest, npm packages, weasyprint, markdown, PIL)
5. Download artifacts from all test jobs
6. Run `test_report_generator.py` to create comprehensive report
7. Upload generated report as artifact
8. (If PR) Post test summary comment on pull request

**Features**:
- Combines backend, frontend, and E2E test results
- Generates both Markdown and PDF reports
- Validates image integrity
- Checks test count consistency
- Posts summary to PR comments

**Artifact name**: `test-report`

#### 5. Publish Report (publish-report)

**Purpose**: Deploy test reports to GitHub Pages (optional)

**Runs only**: On push to `master` or `main` branch

**Steps**:
1. Download test report artifacts
2. Deploy to GitHub Pages using `peaceiris/actions-gh-pages`
3. Create release notes with test reports (on tagged releases)

**Configuration**:
- Uses `GITHUB_TOKEN` for authentication
- Publishes to `gh-pages` branch
- Optional: Custom domain support
- On tags: Attaches reports to GitHub release

---

## File Structure

```
.github/
├── workflows/
│   └── test-and-report.yml        # Main CI/CD workflow
└── CI_CD_AUTOMATION.md            # This documentation
```

---

## Integration with Test Report Generator

The workflow uses `/tools/test_report_generator.py` which:

### Functionality
- Runs backend pytest tests
- Runs frontend npm tests
- Runs Playwright E2E tests
- Validates test count consistency
- Validates image file integrity
- Generates Markdown reports
- Converts to PDF with embedded images
- Organizes reports in timestamped directories

### Report Generation
```bash
python tools/test_report_generator.py --report-title "CI/CD Automated Test Report"
```

Generates in `test_reports/`:
```
test_reports/
└── CI_CD_Automated_Test_Report__2025-11-16_14-00-00/
    ├── README.md                  # Markdown report
    ├── README.pdf                 # PDF with embedded images
    └── screenshots/               # E2E screenshots
        ├── gcp-settings-page.png
        ├── backup-manager.png
        └── ... (25+ more)
```

---

## Environment Variables

The workflow uses standard GitHub Actions environment variables:

- `GITHUB_TOKEN`: Automatic access token for GitHub API
- `GITHUB_REF`: Current git reference (branch/tag)
- `GITHUB_RUN_ID`: Unique workflow run identifier

No additional secrets required for basic testing.

---

## Artifact Retention

All artifacts are retained for 90 days (GitHub default):

- `backend-test-results`: JUnit XML format
- `frontend-coverage`: Coverage reports
- `e2e-report`: HTML test report with screenshots
- `e2e-screenshots`: Raw screenshot images
- `test-report`: Final comprehensive report (MD + PDF)

Access artifacts at:
```
https://github.com/{owner}/{repo}/actions/runs/{run_id}
```

---

## Pull Request Integration

When workflow runs on a PR:

1. Tests run on PR commit
2. Test report is generated
3. Automated comment is posted to PR with test summary
4. Artifacts are available for download
5. Full report links are provided in comment

Example PR comment:
```
## 📊 Test Report Generated

**Summary**: 115 backend tests, 0 frontend tests, 0 E2E tests

✅ All tests passed!

[View full report in artifacts](https://github.com/{owner}/{repo}/actions/runs/{id})
```

---

## GitHub Pages Deployment

On push to `master`/`main`:

1. Test reports automatically deployed to GitHub Pages
2. Published at: `https://{owner}.github.io/{repo}/`
3. Latest report accessible at root URL
4. Historical reports maintained as artifacts

Optional custom domain:
```yaml
cname: mathesis-lab-tests.example.com
```

---

## Troubleshooting

### Backend Tests Fail
- Check Python version compatibility
- Verify backend requirements.txt is up to date
- Review test output in `backend-test-results` artifact

### Frontend Tests Timeout
- Vitest pool issue: May be WSL/GitHub Actions environment issue
- Check Node.js version compatibility (should be 22.x LTS)
- Review `frontend-coverage` artifact

### E2E Tests Timeout
- Backend service may not be starting in time
- Check service logs in workflow output
- Increase wait timeout if needed
- Ensure port 8000 is available

### Report Generation Fails
- Check all test artifacts are downloaded
- Verify PIL (Pillow) installed: `pip install pillow`
- Check image files are valid: see `test_report_generator.py` validation

### Images Not Embedding in PDF
- Check image paths are relative or absolute
- Verify images exist in `e2e-screenshots/`
- Check image file sizes (should be > 100 bytes)
- Review image validation report output

---

## Best Practices

### For Contributors

1. **Push to feature branch**: Your workflow will run tests
2. **Review test reports**: Check artifacts before creating PR
3. **Fix failing tests**: Address any test failures before PR
4. **Monitor PR checks**: GitHub will show test status

### For Maintainers

1. **Monitor workflow runs**: Check for recurring failures
2. **Update dependencies**: Keep Python, Node.js, packages current
3. **Archive old reports**: GitHub keeps artifacts 90 days
4. **Scale resources**: Consider runner upgrades if needed

---

## Performance Metrics

Expected workflow duration:
- Backend tests: ~5-10 minutes
- Frontend tests: ~3-5 minutes (vitest setup)
- E2E tests: ~10-15 minutes (browser startup + tests)
- Report generation: ~2-3 minutes
- **Total**: ~20-30 minutes

---

## Future Enhancements

### Planned
- [ ] Code coverage badge in README
- [ ] Performance benchmarking
- [ ] Cross-browser testing (Firefox, Safari, Edge)
- [ ] Load testing / stress tests
- [ ] Security scanning (SAST)
- [ ] Dependency checking (SCA)

### Under Consideration
- Parallel test execution
- Test result caching
- Build artifact caching
- Database migration testing
- Docker image building
- Helm chart validation

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions)
- [Pytest Documentation](https://docs.pytest.org)
- [Vitest Documentation](https://vitest.dev)
- [Playwright Testing](https://playwright.dev)
- [GitHub Pages Deployment](https://pages.github.com)

---

## Contact & Support

For issues with CI/CD automation:
1. Check workflow logs: Actions tab in GitHub repo
2. Review artifacts for error details
3. Check test execution for compatibility issues
4. Refer to tool documentation (pytest, vitest, Playwright)
5. Create GitHub issue with workflow logs

---

**Last Updated**: 2025-11-16
**Maintained By**: Development Team
**Version**: 1.0
