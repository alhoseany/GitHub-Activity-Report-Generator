# Project Description

> Original requirements and goals for the GitHub Activity Report Generator

---

## Goal

Create a Python script using the local `gh` CLI to generate monthly GitHub activity reports.

---

## Report Contents

The report should include:

- Commits
- Comments
- Reviews
- Reactions and descriptions
- Issues activity
- PR activity
- New repository activity
- Advanced metrics:
  - Commits per PR before approval
  - PR approval times
  - Other extractable GitHub statistics

---

## Technical Requirements

### Output Format
- JSON output validated against a defined schema
- Markdown reports for human readability
- Report metadata: generation date, user info, month analyzed, quick stats

### Code Quality
- Modular, extensible architecture
- Portable (no hardcoded paths)
- Well-organized into separate modules

### Report Organization
- Reports saved in `reports/` directory
- Organized by year: `reports/{year}/`
- Naming: `{year}-{month}-github-activity-{n}.{md,json}`
- Auto-increment if file exists (e.g., `-1`, `-2`, `-3`)

---

## Planning Requirements

- Detailed plan created before implementation
- Visual elements (flowcharts, diagrams, data flows)
- Clarifying questions for ambiguities
- Summary included
- Plan document as single source of truth

---

## Directory Structure

```
github-activity/
├── docs/           # Documentation and planning
├── src/            # Python modules
├── tests/          # Test suite
├── reports/        # Generated reports
│   └── {year}/
│       └── {username}/
│           ├── {year}-{MM}-github-activity-1.md
│           └── {year}-{MM}-github-activity-1.json
├── logs/           # Application logs
├── .cache/         # API response cache
├── config.yaml     # User configuration
└── generate_report.py  # CLI entry point
```

---

## Implementation Status

All original requirements have been implemented:

| Requirement | Status |
|-------------|--------|
| Monthly/quarterly reports | Implemented |
| Commits, comments, reviews | Implemented |
| Issues and PR activity | Implemented |
| Advanced metrics | Implemented |
| JSON schema validation | Implemented |
| Modular architecture | Implemented |
| Portable code | Implemented |
| Report versioning | Implemented |
| Report metadata | Implemented |

---

*This document captures the original project requirements from the initial specification.*
