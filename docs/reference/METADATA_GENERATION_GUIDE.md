# 🧠 LLM-Based Metadata Generation Guide

## Overview

This guide explains how to generate comprehensive test report metadata using Large Language Models (LLMs) like Claude, GPT-4, or Gemini.

## Why Metadata?

Test reports are more credible and useful when they include non-code elements:

| Element | Why Important | Example |
|---------|--------------|---------|
| **Risk Assessment** | Shows awareness of limitations | "Mock API tests don't cover real network delays" |
| **Performance Benchmarks** | Demonstrates technical analysis | "PDF generation: 56KB → 1.2MB after embedding images" |
| **Deployment Notes** | Ensures operational readiness | "Step-by-step deployment checklist with commands" |
| **Technical Debt** | Transparency about future work | "8 tracked items with priority and timeline" |
| **Validation Checklist** | Quality assurance proof | "7 pre-deployment checks, all PASS" |

## Metadata JSON Schema

The metadata structure has 5 core sections:

### 1. Risk Assessment & Untested Areas

```json
{
  "risks_and_untested_areas": {
    "description": "Risks and areas that weren't tested",
    "items": [
      {
        "area": "Backend Mock Tests for GCP API",
        "risk_level": "medium",  // high, medium, low
        "description": "Mock API doesn't cover real network delays",
        "mitigation": "Use staging environment for integration tests",
        "jira_ticket": "PROJ-123"  // optional
      }
    ]
  }
}
```

**LLM Prompt Tips:**
- Ask LLM to analyze **test coverage gaps**
- Look for **mock/stub dependencies**
- Identify **environment-specific issues** (WSL2, CI/CD)
- Rate severity by **impact on production**

### 2. Performance Benchmarking

```json
{
  "performance_benchmarking": {
    "description": "Performance impact analysis",
    "baseline_environment": "Ubuntu 22.04 LTS, Python 3.11",
    "items": [
      {
        "component": "Backend Test Execution",
        "metric": "Average test duration",
        "before": "N/A (baseline)",
        "after": "~115 tests in 5-10 minutes",
        "delta_percent": "baseline",
        "status": "✅ acceptable",
        "notes": "Linear scaling with test count"
      }
    ]
  }
}
```

**LLM Prompt Tips:**
- Extract **timing data** from test execution logs
- Calculate **before/after deltas** for changes
- Include **environment specs** (OS, Python, Node versions)
- Add **status indicators** (✅ acceptable, ⚠️ needs optimization)

### 3. Deployment Notes & Dependencies

```json
{
  "dependencies_and_deployment_notes": {
    "description": "Deployment checklist and dependencies",
    "deployment_order": [
      {
        "step": 1,
        "required": true,
        "action": "Backend dependency check",
        "command": "pip install -r backend/requirements.txt",
        "notes": "Contains pytest, FastAPI, SQLAlchemy",
        "env_vars": [
          {
            "name": "PYTHONPATH",
            "required": true,
            "notes": "Set to project root for pytest"
          }
        ]
      }
    ]
  }
}
```

**LLM Prompt Tips:**
- Ask LLM to **extract dependencies** from requirements files
- Create **step-by-step checklist** for deployment
- Include **bash commands** for each step
- Specify **required vs optional** steps
- Add **environment variables** needed

### 4. Technical Debt & Follow-ups

```json
{
  "technical_debt_and_followups": {
    "description": "Technical debt items and improvement plans",
    "items": [
      {
        "id": "TECH-001",
        "type": "technical_debt",  // or: enhancement, bug
        "title": "Vitest WSL2 Compatibility",
        "status": "blocked",  // or: in_progress, planned
        "priority": "P2",  // P1=critical, P2=high, P3=medium, P4=low
        "estimated_effort": "2 days",
        "owner": "Frontend Team",
        "target_release": "v1.1.0",
        "description": "Vitest pool hangs in WSL2 environment",
        "current_workaround": "CI/CD pipeline only",
        "planned_solution": "Investigate Vitest fork/threads issue"
      }
    ]
  }
}
```

**LLM Prompt Tips:**
- Ask LLM to **identify known issues** from test failures
- Categorize as **technical debt, enhancement, or bug**
- Estimate **effort and timeline**
- Assign **ownership and priority**
- Describe **current workarounds**

### 5. Validation Checklist

```json
{
  "validation_checklist": {
    "description": "Pre-deployment verification items",
    "items": [
      {
        "item": "All 5 priority items complete",
        "status": "PASS",  // or: FAIL, PENDING
        "date": "2025-11-16"
      }
    ]
  }
}
```

**LLM Prompt Tips:**
- Ask LLM to **create verification checklist** from test results
- Items should be **actionable and measurable**
- All items should have **clear status**
- Include **completion dates**

## LLM Prompt Template

Use this template to generate metadata with any LLM:

```
You are a QA analyst analyzing test results for a software project.
Generate comprehensive metadata for a test report in JSON format.

PROJECT CONTEXT:
- Name: MATHESIS LAB
- Stack: FastAPI (Python) + React (TypeScript) + Playwright
- Test Types: Backend pytest, Frontend vitest, E2E Playwright
- Purpose: Educational platform for curriculum mapping

TEST RESULTS SUMMARY:
{test_results_summary}

DETAILED TEST RESULTS:
{detailed_test_results}

Generate a JSON object with exactly these 5 sections:

1. RISKS_AND_UNTESTED_AREAS
   - Analyze test coverage gaps
   - Identify mock/stub dependencies
   - Rate severity (high/medium/low)
   - Suggest mitigations
   - Include 5 items

2. PERFORMANCE_BENCHMARKING
   - Extract timing from test execution
   - Calculate before/after deltas
   - Include 6 metrics
   - Add status indicators

3. DEPLOYMENT_NOTES
   - List dependencies from requirements files
   - Create deployment checklist
   - Include bash commands
   - Specify required vs optional
   - List environment variables

4. TECHNICAL_DEBT_AND_FOLLOWUPS
   - Identify known issues
   - Categorize (technical_debt/enhancement/bug)
   - Set priority (P1-P4)
   - Estimate effort
   - Assign owner
   - Target release version
   - Include 8 items

5. VALIDATION_CHECKLIST
   - Create pre-deployment checks
   - Mark each as PASS/FAIL/PENDING
   - Include 7 items
   - Add completion dates

Requirements:
- Return ONLY valid JSON (no markdown, no explanations)
- Use Korean text for descriptions
- Include severity emojis (🔴🟠🟡) in risk items
- Preserve exact formatting from examples
- Make content specific to test results provided
- Be realistic and honest about issues
```

## Example: Generating Metadata with Claude

### Step 1: Prepare Test Results

```python
import json
import subprocess

def get_test_results():
    """Collect all test results into a single JSON"""

    results = {
        "backend": {
            "total_tests": 115,
            "passed": 115,
            "failed": 0,
            "duration_seconds": 5.53,
            "test_categories": {
                "unit_tests": 16,
                "integration_tests": 77,
                "database_tests": 2,
                "api_tests": 20
            }
        },
        "frontend": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "note": "WSL2 timeout issue, works in CI/CD"
        },
        "e2e": {
            "total_tests": 5,
            "passed": 5,
            "failed": 0,
            "screenshots": 25
        }
    }

    return results
```

### Step 2: Call Claude API

```python
import anthropic
import json

def generate_metadata_claude(test_results, report_title):
    """Generate metadata using Claude API"""

    client = anthropic.Anthropic(api_key="your-api-key")

    prompt = f"""
You are a QA analyst. Generate metadata for this test report.

Report Title: {report_title}

Test Results:
{json.dumps(test_results, indent=2)}

Generate JSON with 5 sections as described in the schema.
Return ONLY the JSON, no explanations.
    """

    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    metadata = json.loads(response.content[0].text)
    return metadata
```

### Step 3: Validate and Save

```python
def save_metadata(metadata, filepath):
    """Validate and save metadata JSON"""

    # Validate required sections
    required_sections = [
        "risks_and_untested_areas",
        "performance_benchmarking",
        "dependencies_and_deployment_notes",
        "technical_debt_and_followups",
        "validation_checklist"
    ]

    for section in required_sections:
        if section not in metadata:
            raise ValueError(f"Missing section: {section}")

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Metadata saved to {filepath}")
    return filepath
```

## Multi-LLM Support

The system should support any LLM with similar capabilities:

### Claude (Anthropic)
```python
from anthropic import Anthropic
client = Anthropic(api_key="sk-ant-...")
```

### GPT-4 (OpenAI)
```python
from openai import OpenAI
client = OpenAI(api_key="sk-...")
```

### Gemini (Google)
```python
import google.generativeai as genai
genai.configure(api_key="...")
```

## Prompt Engineering Best Practices

### 1. Be Specific About Format
❌ **Bad:** "Generate metadata for test results"
✅ **Good:** "Return ONLY valid JSON with these 5 sections, no markdown or explanations"

### 2. Provide Context
❌ **Bad:** Test results only
✅ **Good:** Include project name, stack, team info, and goals

### 3. Give Examples
❌ **Bad:** "Create risk items"
✅ **Good:** "Create risk items like: {example_item}"

### 4. Use Constraints
❌ **Bad:** "Set priority"
✅ **Good:** "Set priority to P1 (critical), P2 (high), P3 (medium), or P4 (low)"

### 5. Request Realism
❌ **Bad:** "Find issues"
✅ **Good:** "Be realistic and honest about actual issues from test results"

## Error Handling

### Invalid JSON Response
```python
try:
    metadata = json.loads(response)
except json.JSONDecodeError:
    print("❌ LLM returned invalid JSON")
    print(response)
    # Ask LLM again with stricter format instructions
```

### Missing Sections
```python
required_fields = [
    "risks_and_untested_areas",
    "performance_benchmarking",
    ...
]

for field in required_fields:
    if field not in metadata:
        print(f"⚠️  Missing field: {field}")
```

### Schema Validation
```python
from jsonschema import validate

schema = {
    "type": "object",
    "required": ["risks_and_untested_areas", ...],
    "properties": {
        "risks_and_untested_areas": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["area", "risk_level", "description"]
                    }
                }
            }
        }
    }
}

validate(instance=metadata, schema=schema)
```

## Integration with Report Generation

Once metadata is generated, use it with the report generator:

```bash
#!/bin/bash

# 1. Run tests (collect results)
pytest backend/tests/ > test-results.json

# 2. Generate metadata with LLM
python tools/generate_metadata.py \
    --test-results test-results.json \
    --title "My Test Report" \
    --api-key "sk-ant-..." \
    --model "claude-opus-4-1"

# 3. Generate report (uses metadata automatically)
python tools/test_report_generator.py --title "My Test Report"

# 4. Open report
open test_reports/My_Test_Report__*/README.pdf
```

## Cost Considerations

### API Usage
- **Claude Opus 4.1:** ~$0.03-0.15 per report (4096 tokens)
- **GPT-4 Turbo:** ~$0.02-0.10 per report
- **Gemini Pro:** Free tier available

### Optimization Tips
- Cache test results to avoid re-analysis
- Batch metadata generation for multiple reports
- Use smaller models for simple reports
- Consider cron job for regular generation

## Future Enhancements

1. **Auto-Update Metadata:** Re-run LLM on each test
2. **Incremental Changes:** Only generate for new test results
3. **Custom Schemas:** User-defined metadata sections
4. **Multi-language:** Generate metadata in different languages
5. **Feedback Loop:** Learn from manually edited metadata

---

**Last Updated:** 2025-11-16
**Maintained By:** Development Team
**Version:** 1.0
