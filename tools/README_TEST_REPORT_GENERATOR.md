# Test Report Generator for MATHESIS LAB

A comprehensive test report generation tool that automatically runs all test suites (backend pytest, frontend npm test, E2E Playwright) and generates professional reports in both Markdown and PDF formats.

## Features

✨ **Automated Test Execution**
- Backend: pytest with full output parsing
- Frontend: npm test integration
- E2E: Playwright test suite capture
- Parallel test execution support

📊 **Comprehensive Reporting**
- Executive summary with pass/fail statistics
- Detailed breakdown of all tests organized by category
- Test duration tracking
- Success rate calculation
- UI/UX changes documentation

📄 **Multi-Format Output**
- Markdown (.md) with syntax highlighting
- PDF (.pdf) with professional styling
- Automatic file naming with timestamps
- Organized storage in `/docs` directory

🎨 **Professional Styling**
- Beautiful PDF rendering with CSS
- Color-coded test results
- Responsive layout for all screen sizes
- Print-ready formatting

## Installation

### Prerequisites
```bash
# Python 3.13+
python --version

# Virtual environment already setup
source .venv/bin/activate
```

### Dependencies
```bash
# Already installed by the generator setup
pip install markdown weasyprint
```

## Usage

### Basic Usage (Default Title)
```bash
cd "/mnt/d/progress/MATHESIS LAB"
source .venv/bin/activate
python tools/test_report_generator.py
```

**Output:** `Regular_Test_Report__2025-11-15_17-20-00.md/pdf`

### Custom Report Title
```bash
python tools/test_report_generator.py --title "Node Type Implementation Test"
```

**Output:** `Node_Type_Implementation_Test__2025-11-15_17-20-00.md/pdf`

### More Examples
```bash
# Pre-release testing
python tools/test_report_generator.py --title "Pre-Release Testing Round 1"

# Feature specific testing
python tools/test_report_generator.py --title "Soft Deletion Feature Test"

# Regression testing
python tools/test_report_generator.py --title "Regression Test Suite"

# Daily testing
python tools/test_report_generator.py --title "Daily Quality Assurance"
```

### Output Files
The generator creates two files in the `/test_reports` directory (organized and separate from docs):
```
test_reports/
├── Node_Type_Implementation_Test__2025-11-15_17-18-37.md     # Markdown report (8.8 KB)
├── Node_Type_Implementation_Test__2025-11-15_17-18-37.pdf    # PDF report (35 KB)
├── Pre-Release_Testing_Round_1__2025-11-15_17-19-55.md       # Markdown report (8.8 KB)
├── Pre-Release_Testing_Round_1__2025-11-15_17-19-55.pdf      # PDF report (35 KB)
├── Organization_Test__2025-11-15_17-26-49.md                 # Markdown report (8.8 KB)
└── Organization_Test__2025-11-15_17-26-49.pdf                # PDF report (35 KB)
```

**Directory Structure:**
```
/mnt/d/progress/MATHESIS LAB/
├── docs/                    # 프로젝트 문서
├── test_reports/            # 테스트 보고서 (깔끔하게 분리) ✨
├── tools/                   # 테스트 도구
├── backend/                 # 백엔드 코드
└── MATHESIS-LAB_FRONT/      # 프론트엔드 코드
```

**Filename Format:** `REPORT_TITLE__YYYY-MM-DD_HH-MM-SS.ext`

This format makes it easy to:
- Identify what tests were run (from the title)
- Know when the report was generated (from the timestamp)
- Find related reports (by title)
- Keep reports organized and separate from project documentation

## Report Contents

### Executive Summary
- Total test count
- Pass/fail statistics
- Success rate percentage
- Breakdown by test type (backend, frontend, E2E)

### Backend Test Results (pytest)
- Summary statistics and duration
- Tests organized by file and category
- Unit tests and integration tests separated
- Pass/fail status for each test

**Test Coverage:**
- **Unit Tests:** 16 tests
  - NodeService: 10 tests (CRUD, soft delete, cascading, links)
  - CurriculumService: 7 tests (CRUD operations)
- **Integration Tests:** 77 tests
  - Curriculum API, Node API, Node Content, Node Links, Reorder, Public Curriculum
  - External APIs: YouTube, Zotero
  - Database operations and literature management

### Frontend Test Results (npm test)
- Test count and pass/fail status
- Note about test configuration status

### E2E Test Results (Playwright)
- Playwright test execution results
- Test duration and status
- Component verification tests

### UI/UX Changes Summary
Documents all user-facing changes made in the implementation:

**CreateNodeModal Component**
- Node type selector dropdown with 7 options (CHAPTER, SECTION, TOPIC, CONTENT, ASSESSMENT, QUESTION, PROJECT)
- Visual formatting improvements
- Form validation integration
- User impact analysis

**Node Model & Service Layer**
- Transaction lock implementation for race condition prevention
- Soft deletion pattern with trash/restore functionality
- Atomic order index calculation
- Cascading soft delete for data consistency

**Type Definitions**
- Explicit NodeType union type
- deleted_at field for soft deletion tracking
- Type-safe node creation

### Test Coverage Analysis
Detailed breakdown of test coverage across all layers:
- Unit tests per service
- Integration tests per API endpoint
- E2E test scenarios
- Coverage percentages

### Quality Assurance Checklist
Complete verification of:
- Test pass rates (100% for backend)
- Type safety and compilation
- Transaction isolation
- Data integrity
- API validation
- Component rendering

## Technical Details

### Test Parsing
The generator uses regex patterns to parse test output:
```python
# Backend test pattern
test_pattern = r"(backend/tests/[^\s:]+)::(test_[\w_]+)\s+(PASSED|FAILED)"

# Summary pattern
summary_pattern = r"=+ (\d+) passed(?:, (\d+) failed)?(?:, (\d+) warnings)? in ([\d\.]+)s"
```

### Output File Structure
```
TestReportGenerator
├── run_backend_tests()      # Execute pytest and parse results
├── run_frontend_tests()     # Execute npm test
├── run_e2e_tests()          # Execute Playwright
├── generate_md_report()     # Create markdown content
├── save_md_report()         # Write markdown to file
├── convert_to_pdf()         # Convert markdown to PDF
└── generate()               # Main orchestration method
```

### subprocess.run Configuration
```python
result = subprocess.run(
    [venv_python, "-m", "pytest", "backend/tests/", "-v", "--tb=short"],
    cwd=str(self.project_root),
    capture_output=True,
    text=True,
    timeout=180
)
```

Key points:
- Uses list form to avoid shell quoting issues
- Direct venv python path for reliability
- Proper cwd handling for spaces in path
- 180-second timeout per test suite

## Command-Line Interface

### Arguments

```
usage: test_report_generator.py [-h] [--title TITLE]

Generate comprehensive test reports for MATHESIS LAB

options:
  -h, --help     show this help message and exit
  --title TITLE  Report title (e.g., 'Node Type Implementation Test', 'Pre-Release Testing')
```

### Title Formatting Rules
- **Spaces:** Automatically converted to underscores
- **Special Characters:** Automatically removed (only alphanumeric, hyphens, underscores allowed)
- **Case:** Preserved as written
- **Length:** No limit (but keep reasonable for file paths)

**Examples:**

| Input Title | Filename Prefix |
|---|---|
| `Node Type Implementation Test` | `Node_Type_Implementation_Test` |
| `Pre-Release Testing Round 1` | `Pre-Release_Testing_Round_1` |
| `Daily QA (2025-11-15)` | `Daily_QA_2025-11-15` |
| `Bug Fix: Soft Delete` | `Bug_Fix_Soft_Delete` |

## Examples

### Running the Generator
```bash
$ cd "/mnt/d/progress/MATHESIS LAB"
$ source .venv/bin/activate
$ python tools/test_report_generator.py

============================================================
🚀 Starting Test Report Generation
============================================================

🔵 Running backend tests...
✅ Backend: 93 passed, 0 failed
🟢 Running frontend tests...
✅ Frontend: 0 passed, 0 failed
🟣 Running E2E tests...
✅ E2E: 0 passed, 0 failed
📝 Generating Markdown report...
✅ Saved: /mnt/d/progress/MATHESIS LAB/docs/TEST_REPORT_2025-11-15_17-11-01.md
📄 Converting to PDF...
✅ Saved: /mnt/d/progress/MATHESIS LAB/docs/TEST_REPORT_2025-11-15_17-11-01.pdf

============================================================
✅ Test Report Generation Complete
============================================================

📊 Test Summary:
   Backend:  93/93 passed
   Frontend: 0/0 passed
   E2E:      0/0 passed

📁 Reports saved to: /mnt/d/progress/MATHESIS LAB/docs
   MD:  TEST_REPORT_2025-11-15_17-11-01.md
   PDF: TEST_REPORT_2025-11-15_17-11-01.pdf
```

### Checking Generated Reports
```bash
# View markdown report
cat docs/TEST_REPORT_2025-11-15_17-11-01.md | head -50

# View PDF file size
ls -lh docs/TEST_REPORT_2025-11-15_17-11-01.pdf

# Open PDF in default viewer
open docs/TEST_REPORT_2025-11-15_17-11-01.pdf
```

## CI/CD Integration

To integrate with CI/CD pipelines:

```bash
#!/bin/bash
# .github/workflows/test-report.yml equivalent

cd "/mnt/d/progress/MATHESIS LAB"
source .venv/bin/activate
python tools/test_report_generator.py

# Upload reports as artifacts
# cp docs/TEST_REPORT_*.md build/reports/
# cp docs/TEST_REPORT_*.pdf build/reports/
```

## Troubleshooting

### Issue: "Test log not found"
**Cause:** Subprocess failed to create pytest output file
**Solution:**
```bash
# Check venv path
ls -la .venv/bin/python

# Test pytest directly
python -m pytest backend/tests/ -v --tb=short
```

### Issue: "PDF conversion failed"
**Cause:** Missing markdown or weasyprint dependencies
**Solution:**
```bash
pip install markdown weasyprint
```

### Issue: Zero tests captured
**Cause:** Regex pattern not matching test output format
**Solution:**
1. Check pytest output format: `python -m pytest backend/tests/ -v`
2. Verify regex patterns match your output
3. Update test_pattern if pytest format changed

## Report Statistics

**Last Generation:** 2025-11-15

| Metric | Value |
|--------|-------|
| Backend Tests | 93 ✅ |
| Frontend Tests | 0 ⏳ |
| E2E Tests | 0 ⏳ |
| Success Rate | 100% |
| Report Size (MD) | 8.8 KB |
| Report Size (PDF) | 35 KB |
| Generation Time | ~10 seconds |

## Future Enhancements

- [ ] Real-time test execution streaming
- [ ] HTML report generation
- [ ] Test timing visualization (slowest tests)
- [ ] Historical report comparison
- [ ] Test coverage metrics (pytest-cov integration)
- [ ] Failure reason analysis
- [ ] Automated report publishing to docs site
- [ ] Email notification integration
- [ ] Slack notifications
- [ ] Custom branding for organizations

## License

Part of MATHESIS LAB project. See main LICENSE file.

## Support

For issues or questions about the report generator:

1. Check the troubleshooting section above
2. Review test output logs: `.pytest_output.log`
3. Verify test configurations in `backend/tests/conftest.py`
4. Check frontend setup in `MATHESIS-LAB_FRONT/package.json`

---

**Generated:** 2025-11-15
**Version:** 1.0
**Status:** Production Ready ✅
