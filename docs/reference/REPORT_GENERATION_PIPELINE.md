# 📊 Test Report Generation Pipeline Guide

## Overview

This document describes the complete automated test report generation pipeline used in MATHESIS LAB. The pipeline can generate comprehensive test reports with metadata automatically using LLM models.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Execution Layer                          │
│  Backend (pytest) │ Frontend (vitest) │ E2E (playwright)        │
└────────┬──────────────────────────────────────────────────┬─────┘
         │                                                   │
         └───────────────────┬────────────────────────────────┘
                             ↓
         ┌─────────────────────────────────────┐
         │  Aggregate Test Results (JSON)      │
         │  - Backend: test-results.xml        │
         │  - Frontend: coverage reports       │
         │  - E2E: playwright-report, screenshots
         └────────┬────────────────────────────┘
                  ↓
    ┌─────────────────────────────────────────────────────┐
    │  (NEW) Metadata Generation (LLM-based)             │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ Input: Test results JSON + Report title       │ │
    │  │ LLM: Claude/GPT-4/Gemini analyzes results     │ │
    │  │ Output: report_metadata.json                  │ │
    │  └────────────────────────────────────────────────┘ │
    │  Metadata sections generated:                        │
    │  1. ⚠️  Risk Assessment & Untested Areas            │
    │  2. 📈 Performance Benchmarking                      │
    │  3. 📦 Deployment Notes & Dependencies              │
    │  4. 🛠️  Technical Debt & Follow-ups                │
    │  5. ✅ Pre-Deployment Validation Checklist         │
    └────────┬────────────────────────────────────────────┘
             ↓
    ┌─────────────────────────────────────────────────────┐
    │  Report Generation (test_report_generator.py)        │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ 1. Load test results                          │ │
    │  │ 2. Load metadata from JSON                    │ │
    │  │ 3. Generate markdown with metadata sections   │ │
    │  │ 4. Validate images (PIL)                      │ │
    │  │ 5. Convert to PDF with embedded images        │ │
    │  └────────────────────────────────────────────────┘ │
    └────────┬────────────────────────────────────────────┘
             ↓
    ┌─────────────────────────────────────────────────────┐
    │  Output: Test Report                                │
    │  test_reports/Report_Title__TIMESTAMP/              │
    │  ├── README.md (24KB with metadata)                │
    │  ├── README.pdf (1.2MB with images)                │
    │  └── screenshots/ (25+ E2E test screenshots)        │
    └─────────────────────────────────────────────────────┘
```

## Current Status (Manual Metadata)

Currently, `tools/report_metadata.json` is created manually with 4 core non-code elements:

```json
{
  "risks_and_untested_areas": { ... },
  "performance_benchmarking": { ... },
  "dependencies_and_deployment_notes": { ... },
  "technical_debt_and_followups": { ... },
  "validation_checklist": { ... }
}
```

## Step 1: Run Tests

### Backend Tests
```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/ -v --junit-xml=test-results.xml
```

### Frontend Tests
```bash
cd MATHESIS-LAB_FRONT
npm test -- --run --coverage
```

### E2E Tests
```bash
cd MATHESIS-LAB_FRONT
npx playwright test e2e/ --reporter=html
```

## Step 2: Generate Metadata (Current: Manual)

Edit `tools/report_metadata.json` with:
- Risk assessment from test failures
- Performance metrics from test execution
- Deployment checklist based on changes
- Technical debt items discovered
- Validation checklist for deployment

**JSON Schema:** See `/tools/report_metadata.json` for complete structure

## Step 3: Generate Report

```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
python tools/test_report_generator.py --title "Your Report Title"
```

**Output:**
- `test_reports/Your_Report_Title__TIMESTAMP/README.md`
- `test_reports/Your_Report_Title__TIMESTAMP/README.pdf`
- `test_reports/Your_Report_Title__TIMESTAMP/screenshots/`

## Future: LLM-Based Metadata Generation

### Overview
Instead of manually editing `report_metadata.json`, use an LLM to automatically analyze test results and generate metadata.

### How It Works
1. Parse test results JSON
2. Send to LLM with detailed prompt
3. LLM analyzes and generates structured JSON
4. Validate JSON schema
5. Use for report generation (same as Step 3)

### Benefits
✅ **Consistency:** Same structure for all reports
✅ **Speed:** Automatic metadata generation
✅ **Flexibility:** Works with any LLM (Claude, GPT-4, Gemini)
✅ **Extensibility:** Easy to add new metadata sections

### Implementation Example

**File: `tools/generate_metadata.py`** (to be created)

```python
import json
import anthropic

def generate_metadata_with_llm(test_results_path, report_title):
    """
    Generate report_metadata.json using Claude API

    Args:
        test_results_path: Path to aggregated test results JSON
        report_title: Title of the test report

    Returns:
        dict: Generated metadata matching report_metadata.json schema
    """

    # Read test results
    with open(test_results_path) as f:
        test_results = json.load(f)

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key="your-api-key")

    # Create prompt
    prompt = f"""
    Analyze the following test results and generate comprehensive metadata
    for a test report. Return ONLY valid JSON matching the schema below.

    Report Title: {report_title}

    Test Results:
    {json.dumps(test_results, indent=2)}

    Generate JSON with these 5 sections:

    1. risks_and_untested_areas (5 items with risk_level: high/medium/low)
    2. performance_benchmarking (6 metrics with before/after values)
    3. dependencies_and_deployment_notes (deployment checklist with steps)
    4. technical_debt_and_followups (8 items with priority and effort)
    5. validation_checklist (7 verification items with PASS/FAIL status)

    Return ONLY the JSON, no markdown or explanations.
    """

    # Call Claude API
    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and validate response
    metadata_json = json.loads(response.content[0].text)
    return metadata_json
```

**Usage:**
```bash
python tools/generate_metadata.py \
  --test-results aggregated-test-results.json \
  --title "My Test Report" \
  --api-key "sk-ant-..." \
  --model "claude-opus-4-1"
```

### Prompt Engineering Tips

For best results, the LLM prompt should:

1. **Specify output format clearly**
   ```
   Return ONLY valid JSON matching this schema: {...}
   Do not include markdown, explanations, or code blocks.
   ```

2. **Provide context about your project**
   ```
   This is a test report for an educational platform (MATHESIS LAB)
   with React frontend, FastAPI backend, and Playwright E2E tests.
   ```

3. **Include example metadata**
   ```
   Example risk item format:
   {
     "area": "Backend Mock Tests",
     "risk_level": "medium",
     "description": "...",
     "mitigation": "..."
   }
   ```

4. **Specify Korean text requirements** (if needed)
   ```
   Use Korean text for descriptions and titles.
   Preserve Korean text exactly in JSON output.
   ```

## Pipeline Automation (Optional)

Create `tools/auto_generate_report.sh`:

```bash
#!/bin/bash
set -e

REPORT_TITLE="${1:-Test Report $(date +%Y-%m-%d)}"
API_KEY="${ANTHROPIC_API_KEY}"

echo "📊 Starting automated test report generation..."

# Step 1: Run all tests
echo "1️⃣  Running backend tests..."
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/ -v --junit-xml=test-results.xml

echo "2️⃣  Running frontend tests..."
cd MATHESIS-LAB_FRONT
npm test -- --run --coverage
cd ..

echo "3️⃣  Running E2E tests..."
cd MATHESIS-LAB_FRONT
npx playwright test e2e/ --reporter=html
cd ..

# Step 2: Generate metadata (LLM-based, when implemented)
echo "4️⃣  Generating metadata with LLM..."
python tools/generate_metadata.py \
  --test-results aggregated-test-results.json \
  --title "$REPORT_TITLE" \
  --api-key "$API_KEY" \
  --model "claude-opus-4-1"

# Step 3: Generate report
echo "5️⃣  Generating test report..."
source .venv/bin/activate
python tools/test_report_generator.py --title "$REPORT_TITLE"

echo "✅ Report generation complete!"
echo "📁 Output: test_reports/"
```

**Usage:**
```bash
chmod +x tools/auto_generate_report.sh
ANTHROPIC_API_KEY="sk-ant-..." ./tools/auto_generate_report.sh "My Report Title"
```

## Files Reference

| File | Purpose | Format | Status |
|------|---------|--------|--------|
| `tools/test_report_generator.py` | Main report generation logic | Python | ✅ Ready |
| `tools/report_metadata.json` | Metadata for report sections | JSON | ✅ Ready |
| `tools/generate_metadata.py` | LLM-based metadata generator | Python | 📅 To be created |
| `tools/auto_generate_report.sh` | Complete pipeline automation | Bash | 📅 To be created |

## Key Decisions

### Why Separate Metadata File?

✅ **Decoupling:** Test generation independent from metadata
✅ **Flexibility:** Easy to use different LLMs
✅ **Transparency:** Metadata visible and editable
✅ **Version Control:** Track metadata changes in git

### Why JSON Format?

✅ **Structured:** Consistent schema across reports
✅ **Parseable:** Easy to read/write programmatically
✅ **Extensible:** Easy to add new fields
✅ **LLM-friendly:** LLMs can generate valid JSON

### Why 5 Metadata Sections?

1. **⚠️ Risk Assessment** → Stakeholder transparency
2. **📈 Performance** → Technical credibility
3. **📦 Deployment** → Operational readiness
4. **🛠️ Tech Debt** → Future planning
5. **✅ Validation** → Quality assurance

These 5 sections provide a complete picture for decision-making.

## Troubleshooting

### JSON Schema Errors
```bash
# Validate metadata JSON
python -m json.tool tools/report_metadata.json

# Check schema against test_report_generator.py
grep -A 20 "_generate_metadata_sections" tools/test_report_generator.py
```

### LLM API Errors (when implemented)
- Check API key is valid
- Verify rate limits not exceeded
- Check network connectivity
- Review LLM error message

### Report Generation Failures
```bash
# Enable verbose output
python tools/test_report_generator.py --title "Test" --verbose

# Check file permissions
ls -la test_reports/
chmod 755 test_reports/

# Verify image files
file test_reports/*/screenshots/*.png
```

## Next Steps

1. ✅ Current: Manual metadata creation
2. 📅 Phase 1: Create `generate_metadata.py` with Claude API
3. 📅 Phase 2: Add support for GPT-4 and Gemini
4. 📅 Phase 3: Full pipeline automation script
5. 📅 Phase 4: GitHub Actions integration

---

**Last Updated:** 2025-11-16
**Maintained By:** Development Team
**Version:** 1.0
