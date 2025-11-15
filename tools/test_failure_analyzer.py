#!/usr/bin/env python3
"""
Test Failure Analyzer for MATHESIS LAB

Analyzes test failures and provides detailed error reports with:
- Error classification (assertion, exception, timeout, etc.)
- Stack trace analysis
- Root cause identification
- Suggestions for fixes
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class FailureType(Enum):
    """Categorizes test failure types."""
    ASSERTION = "AssertionError"
    EXCEPTION = "Exception"
    TIMEOUT = "Timeout"
    IMPORT = "ImportError"
    ATTRIBUTE = "AttributeError"
    TYPE = "TypeError"
    VALUE = "ValueError"
    KEY = "KeyError"
    INDEX = "IndexError"
    NETWORK = "NetworkError"
    DATABASE = "DatabaseError"
    UNKNOWN = "Unknown"


@dataclass
class TestFailure:
    """Represents a test failure with detailed analysis."""
    test_file: str
    test_name: str
    failure_type: FailureType
    error_message: str
    stack_trace: List[str]
    line_number: Optional[int] = None
    source_line: Optional[str] = None
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class TestFailureAnalyzer:
    """Analyzes test output and extracts failure information."""

    def __init__(self, project_root: str = "/mnt/d/progress/MATHESIS LAB"):
        self.project_root = Path(project_root)
        self.failures: List[TestFailure] = []

    def analyze_pytest_output(self, output: str) -> List[TestFailure]:
        """
        Analyze pytest output and extract failure details.

        Args:
            output: Raw pytest output text

        Returns:
            List of TestFailure objects with detailed analysis
        """
        self.failures = []

        # Split by test section markers
        test_sections = re.split(r'^_{5,}', output, flags=re.MULTILINE)

        for section in test_sections:
            if 'FAILED' not in section:
                continue

            failure = self._parse_test_section(section)
            if failure:
                self.failures.append(failure)

        return self.failures

    def _parse_test_section(self, section: str) -> Optional[TestFailure]:
        """Parse a single test failure section."""
        # Extract test file and name
        test_match = re.search(
            r'(backend/tests/[^\s:]+)::(test_[\w_]+)',
            section
        )
        if not test_match:
            return None

        test_file = test_match.group(1)
        test_name = test_match.group(2)

        # Extract error type and message
        error_match = re.search(
            r'(?:^|E\s+)(\w+(?:Error)?): (.+?)(?=\n|$)',
            section,
            re.MULTILINE
        )

        if not error_match:
            return None

        error_type_str = error_match.group(1)
        error_message = error_match.group(2).strip()

        # Classify failure type
        failure_type = self._classify_failure(error_type_str)

        # Extract stack trace
        stack_trace = self._extract_stack_trace(section)

        # Extract line number and source
        line_info = self._extract_line_info(section)

        # Generate suggestions
        suggestions = self._generate_suggestions(
            failure_type, error_message, error_type_str
        )

        return TestFailure(
            test_file=test_file,
            test_name=test_name,
            failure_type=failure_type,
            error_message=error_message,
            stack_trace=stack_trace,
            line_number=line_info[0],
            source_line=line_info[1],
            suggestions=suggestions
        )

    def _classify_failure(self, error_type_str: str) -> FailureType:
        """Classify the failure type based on error string."""
        error_type_str = error_type_str.lower()

        if 'assert' in error_type_str:
            return FailureType.ASSERTION
        elif 'timeout' in error_type_str:
            return FailureType.TIMEOUT
        elif 'import' in error_type_str:
            return FailureType.IMPORT
        elif 'attribute' in error_type_str:
            return FailureType.ATTRIBUTE
        elif 'type' in error_type_str:
            return FailureType.TYPE
        elif 'value' in error_type_str:
            return FailureType.VALUE
        elif 'key' in error_type_str:
            return FailureType.KEY
        elif 'index' in error_type_str:
            return FailureType.INDEX
        elif 'network' in error_type_str or 'connection' in error_type_str:
            return FailureType.NETWORK
        elif 'database' in error_type_str or 'db' in error_type_str:
            return FailureType.DATABASE
        else:
            return FailureType.UNKNOWN

    def _extract_stack_trace(self, section: str) -> List[str]:
        """Extract stack trace lines from failure section."""
        lines = []
        in_trace = False

        for line in section.split('\n'):
            if 'Traceback' in line or 'File' in line:
                in_trace = True
            if in_trace:
                if line.strip():
                    lines.append(line)
                if not line.startswith(' ') and 'File' not in line:
                    in_trace = False

        return lines[-20:] if lines else []  # Return last 20 lines

    def _extract_line_info(self, section: str) -> Tuple[Optional[int], Optional[str]]:
        """Extract line number and source code from failure."""
        # Look for line number
        line_match = re.search(r'line (\d+)', section)
        line_num = int(line_match.group(1)) if line_match else None

        # Look for source line (usually after ">")
        source_match = re.search(r'>\s+(.+?)$', section, re.MULTILINE)
        source_line = source_match.group(1) if source_match else None

        return line_num, source_line

    def _generate_suggestions(
        self,
        failure_type: FailureType,
        error_message: str,
        error_type_str: str
    ) -> List[str]:
        """Generate helpful suggestions based on failure type."""
        suggestions = []

        if failure_type == FailureType.ASSERTION:
            suggestions.append(
                "✓ Check that the expected value matches the actual value"
            )
            suggestions.append(
                "✓ Review the assertion condition logic"
            )
            if "None" in error_message:
                suggestions.append(
                    "✓ Ensure the tested function/method returns the expected value"
                )

        elif failure_type == FailureType.TIMEOUT:
            suggestions.append(
                "✓ Increase test timeout or optimize slow operations"
            )
            suggestions.append(
                "✓ Check for infinite loops or blocking I/O operations"
            )

        elif failure_type == FailureType.IMPORT:
            suggestions.append(
                "✓ Verify the module/package is installed and accessible"
            )
            suggestions.append(
                "✓ Check PYTHONPATH includes the project root"
            )
            if "test_reports" in error_message:
                suggestions.append(
                    "✓ Ensure test_reports directory exists: mkdir -p test_reports"
                )

        elif failure_type == FailureType.ATTRIBUTE:
            suggestions.append(
                "✓ Verify the object has the accessed attribute"
            )
            suggestions.append(
                "✓ Check for typos in attribute names"
            )
            if "None" in error_message:
                suggestions.append(
                    "✓ Ensure the object is not None before accessing attributes"
                )

        elif failure_type == FailureType.TYPE:
            suggestions.append(
                "✓ Check type compatibility in the operation"
            )
            suggestions.append(
                "✓ Review type annotations and conversions"
            )

        elif failure_type == FailureType.VALUE:
            suggestions.append(
                "✓ Verify input values are within expected range"
            )
            suggestions.append(
                "✓ Check for invalid or unexpected value formats"
            )

        elif failure_type == FailureType.KEY:
            suggestions.append(
                "✓ Verify the key exists in the dictionary"
            )
            suggestions.append(
                "✓ Use .get() method with a default value for safer access"
            )

        elif failure_type == FailureType.INDEX:
            suggestions.append(
                "✓ Verify the index is within list bounds"
            )
            suggestions.append(
                "✓ Check for empty sequences before indexing"
            )

        elif failure_type == FailureType.NETWORK:
            suggestions.append(
                "✓ Verify network connectivity and server availability"
            )
            suggestions.append(
                "✓ Check firewall and proxy settings"
            )

        elif failure_type == FailureType.DATABASE:
            suggestions.append(
                "✓ Verify database connection and credentials"
            )
            suggestions.append(
                "✓ Check database is running and accessible"
            )
            suggestions.append(
                "✓ Review database schema and migrations"
            )

        return suggestions

    def format_failure_report(self, failure: TestFailure) -> str:
        """Format a single failure as markdown."""
        report = []
        report.append(f"### ❌ {failure.test_file}::{failure.test_name}\n")

        report.append(f"**Error Type:** `{failure.failure_type.value}`\n")
        report.append(f"**Error Message:** {failure.error_message}\n")

        if failure.line_number:
            report.append(f"**Line Number:** {failure.line_number}\n")

        if failure.source_line:
            report.append(f"**Source Code:**\n```python\n{failure.source_line}\n```\n")

        if failure.stack_trace:
            report.append("**Stack Trace:**\n```\n")
            for line in failure.stack_trace:
                report.append(line + "\n")
            report.append("```\n")

        if failure.suggestions:
            report.append("**Suggestions:**\n")
            for suggestion in failure.suggestions:
                report.append(f"- {suggestion}\n")

        report.append("\n---\n")
        return "".join(report)

    def format_all_failures(self) -> str:
        """Format all failures as markdown."""
        if not self.failures:
            return "## ✅ No Test Failures\n\nAll tests passed successfully!\n"

        report = []
        report.append(f"## ❌ Test Failures Summary\n\n")
        report.append(f"**Total Failures:** {len(self.failures)}\n\n")

        # Group by failure type
        by_type = {}
        for failure in self.failures:
            type_key = failure.failure_type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(failure)

        # Summary table
        report.append("| Failure Type | Count |\n")
        report.append("|---|---|\n")
        for type_name, failures in sorted(by_type.items()):
            report.append(f"| {type_name} | {len(failures)} |\n")
        report.append("\n")

        # Detailed failures
        for failure in self.failures:
            report.append(self.format_failure_report(failure))

        return "".join(report)

    def get_failure_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all failures."""
        if not self.failures:
            return {
                "total": 0,
                "by_type": {},
                "most_common": None
            }

        by_type = {}
        for failure in self.failures:
            type_name = failure.failure_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        most_common = max(by_type.items(), key=lambda x: x[1])[0] if by_type else None

        return {
            "total": len(self.failures),
            "by_type": by_type,
            "most_common": most_common
        }


def main():
    """Test the analyzer with a sample pytest output."""
    analyzer = TestFailureAnalyzer()

    # Read pytest output
    log_file = Path("/mnt/d/progress/MATHESIS LAB/.pytest_output.log")
    if log_file.exists():
        output = log_file.read_text()
        failures = analyzer.analyze_pytest_output(output)

        print("Failure Analysis Report")
        print("=" * 60)
        print(analyzer.format_all_failures())

        summary = analyzer.get_failure_summary()
        print("\nSummary Statistics:")
        print(f"Total Failures: {summary['total']}")
        print(f"By Type: {summary['by_type']}")
        print(f"Most Common: {summary['most_common']}")
    else:
        print("No pytest output log found")


if __name__ == "__main__":
    main()
