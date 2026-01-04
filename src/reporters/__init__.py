# =============================================================================
# FILE: src/reporters/__init__.py
# TASKS: UC-2.4
# PLAN: Section 5
# =============================================================================
"""
Report Generation Package.

This package generates output reports in various formats:
- json_report.py: JsonReporter for structured JSON output
- markdown_report.py: MarkdownReporter for human-readable reports
- validator.py: Schema validation for JSON reports

Output formats:
- JSON: Full structured data with metadata and metrics
- Markdown: Human-readable summary with formatted sections

File naming convention:
- Monthly: {year}-{MM}-github-activity-{n}.{ext}
- Quarterly: {year}-Q{Q}-github-activity-{n}.{ext}

Usage:
    from src.reporters import JsonReporter, MarkdownReporter
"""
# UC-2.4 | PLAN-5

from .json_report import JsonReporter
from .markdown_report import MarkdownReporter
from .validator import ReportValidator, validate_report

__all__ = [
    "JsonReporter",
    "MarkdownReporter",
    "ReportValidator",
    "validate_report",
]
