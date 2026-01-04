# GitHub Activity Report Generator - Implementation Plan

> **Single Source of Truth** for the GitHub Activity Report Generator (Monthly & Quarterly)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Flow Architecture](#data-flow-architecture)
3. [System Architecture](#system-architecture)
4. [Module Structure](#module-structure)
5. [GitHub API Data Sources](#github-api-data-sources)
6. [Adaptive Fetching Strategy](#adaptive-fetching-strategy)
7. [JSON Schema Definition](#json-schema-definition)
8. [Report Generation Flow](#report-generation-flow)
9. [Advanced Metrics Calculations](#advanced-metrics-calculations)
10. [File Organization](#file-organization)
11. [Clarifying Questions](#clarifying-questions)
12. [Implementation Phases](#implementation-phases)
13. [Testing Strategy](#testing-strategy)
14. [Error Handling Strategy](#error-handling-strategy)
15. [Logging System](#logging-system)
16. [Configuration Options](#configuration-options)

---

## Executive Summary

This document outlines the implementation plan for a Python-based GitHub Activity Report Generator that uses the local `gh` CLI to fetch user activity data and generate comprehensive reports (monthly or quarterly).

### Key Features
- Flexible period support: Monthly or Quarterly activity aggregation
- Activity tracking: commits, PRs, issues, reviews, comments
- Advanced metrics (PR approval times, commits per PR, response times)
- JSON output validated against a defined schema
- Markdown reports with metadata and quick stats
- Modular, extensible, portable architecture

### Technology Stack
- **Language:** Python 3.9+
- **CLI Tool:** GitHub CLI (`gh`)
- **Output Format:** JSON (validated) + Markdown
- **Schema Validation:** jsonschema library

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW DIAGRAM                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   GitHub    │
                              │    API      │
                              └──────┬──────┘
                                     │
                                     ▼
┌──────────────┐            ┌─────────────────┐
│   User       │            │    gh CLI       │
│   Input      │───────────▶│   Commands      │
│  (month OR   │            │                 │
│   quarter,   │            │  - events API   │
│   year)      │            │  - search API   │
└──────────────┘            │                 │
                            │  - graphQL API  │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Data Fetchers  │
                            │                 │
                            │  - commits      │
                            │  - PRs          │
                            │  - issues       │
                            │  - reviews      │
                            │  - comments     │
                            │  - reactions    │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   Aggregator    │
                            │                 │
                            │  - filter by    │
                            │    date range   │
                            │  - group data   │
                            │  - calculate    │
                            │    metrics      │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   Validator     │
                            │                 │
                            │  - JSON schema  │
                            │    validation   │
                            └────────┬────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │                               │
                     ▼                               ▼
            ┌─────────────────┐            ┌─────────────────┐
            │   JSON Report   │            │ Markdown Report │
            │                 │            │                 │
            │  - structured   │            │  - human        │
            │    data         │            │    readable     │
            │  - schema       │            │  - metadata     │
            │    compliant    │            │  - quick stats  │
            └─────────────────┘            └─────────────────┘
                     │                               │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  File System    │
                            │                 │
                            │  reports/       │
                            │  └── 2024/      │
                            │      ├── 2024-  │
                            │      │   12-... │
                            │      └── 2024-  │
                            │          Q4-... │
                            └─────────────────┘
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI Interface                                   │
│                                                                              │
│   python generate_report.py                  # Current month, current user  │
│   python generate_report.py -q               # Current quarter              │
│   python generate_report.py -m 12 -y 2024    # Specific month/year          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Core Engine                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Config        │  │   Orchestrator  │  │   Logger        │             │
│  │   Manager       │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Fetchers    │           │   Processors  │           │   Reporters   │
│               │           │               │           │               │
│ - EventFetch  │           │ - Aggregator  │           │ - JSONReport  │
│ - CommitFetch │           │ - MetricCalc  │           │ - MDReport    │
│ - PRFetch     │           │ - DateFilter  │           │ - Validator   │
│ - IssueFetch  │           │ - Deduplicator│           │               │
│ - ReviewFetch │           │               │           │               │
│ - RepoFetch   │           │               │           │               │
└───────────────┘           └───────────────┘           └───────────────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Utilities                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   gh_client     │  │   date_utils    │  │   file_utils    │             │
│  │   (subprocess)  │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
.scripts/github-activity/
│
├── docs/
│   └── plan.md                    # This document (single source of truth)
│
├── reports/                       # Generated reports (grouped by user)
│   └── {year}/
│       └── {username}/            # User-specific subdirectory
│           ├── {year}-{month}-github-activity-{n}.md      # Monthly
│           └── {year}-Q{quarter}-github-activity-{n}.md   # Quarterly
│
├── logs/                          # Log files (organized by date)
│   ├── 2024/
│   │   └── 12/
│   │       ├── 2024-12-15_143052_activity.log
│   │       ├── 2024-12-15_143052_performance.log
│   │       └── 2024-12-16_091523_activity.log
│   ├── errors/                    # Rotated error logs (by size)
│   │   ├── errors_2024-10-15_091234.log.gz
│   │   ├── errors_2024-11-20_143052.log.gz
│   │   └── errors_2024-12-10_082315.log.gz
│   └── errors.log                 # Active error log (rotated when > 10MB)
│
├── src/                           # Source code modules
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py              # YAML config loader with validation
│   │   ├── settings.py            # Configuration dataclasses
│   │   └── schema.json            # JSON schema for validation
│   │
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base fetcher with adaptive strategy
│   │   ├── events.py              # User events fetcher (90-day limit)
│   │   ├── commits.py             # Commit search fetcher
│   │   ├── pull_requests.py       # PR fetcher with details, reviewed PRs, commits
│   │   ├── issues.py              # Issue fetcher
│   │   ├── reviews.py             # PR review fetcher (given and received)
│   │   └── comments.py            # Comment fetcher (issue + review comments)
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── aggregator.py          # Data aggregation and date filtering
│   │   └── metrics.py             # Advanced metrics calculation
│   │
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── json_report.py         # JSON report generator
│   │   ├── markdown_report.py     # Markdown report generator
│   │   └── validator.py           # Schema validator
│   │
│   └── utils/
│       ├── __init__.py
│       ├── gh_client.py           # GitHub CLI wrapper
│       ├── cache.py               # Response caching with TTL
│       ├── date_utils.py          # Date manipulation utilities
│       ├── file_utils.py          # File operations
│       ├── repo_filter.py         # Repository whitelist/blacklist filtering
│       ├── logger.py              # Structured logging with performance tracking
│       ├── log_cleanup.py         # Log cleanup with thresholds
│       └── report_cleanup.py      # Report cleanup with thresholds
│
├── tests/                         # Test suite
│   ├── conftest.py                # Shared fixtures
│   ├── fixtures/                  # Mock API responses & test data
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests (live API)
│
├── generate_report.py             # Main entry point
├── config.yaml                    # Configuration file (all settings)
├── pytest.ini                     # Pytest configuration
├── .coveragerc                    # Coverage configuration
├── requirements.txt               # Python dependencies
└── README.md                      # Usage documentation
```

---

## GitHub API Data Sources

### 1. Events API (Primary Source)

```
gh api /users/{username}/events --paginate
```

**Event Types Captured:**
| Event Type | Description | Data Extracted |
|------------|-------------|----------------|
| `PushEvent` | Git push | commits, repo, branch |
| `PullRequestEvent` | PR opened/closed/merged | PR details, state, timestamps |
| `PullRequestReviewEvent` | PR review submitted | review body, state (approved/changes requested) |
| `PullRequestReviewCommentEvent` | Review comment | comment body, file, line |
| `IssueCommentEvent` | Issue/PR comment | comment body, issue reference |
| `IssuesEvent` | Issue opened/closed | issue details, labels |
| `CreateEvent` | Repo/branch/tag created | ref type, ref name |
| `DeleteEvent` | Branch/tag deleted | ref type, ref name |
| `ForkEvent` | Repository forked | forked repo details |
| `WatchEvent` | Repository starred | repo details |
| `ReleaseEvent` | Release published | release tag, body |

### 2. Search APIs (Supplementary)

```
gh search commits --author={username} --committer-date={range}
gh search prs --author={username} --created={range}
gh search issues --author={username} --created={range}
```

### 3. GraphQL API (Aggregated Stats)

```graphql
query {
  viewer {
    contributionsCollection(from: "...", to: "...") {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
```

### 4. Repository-Specific APIs (For Metrics)

```
gh api /repos/{owner}/{repo}/pulls/{number}/reviews
gh api /repos/{owner}/{repo}/pulls/{number}/commits
gh api /repos/{owner}/{repo}/issues/{number}/timeline
```

---

## Adaptive Fetching Strategy

To avoid GitHub API rate limits while ensuring complete data collection, the fetchers use an adaptive week-by-week strategy with automatic day-level granularity for high-activity periods.

### Strategy Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADAPTIVE FETCHING ALGORITHM                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   Start Period      │
                    │   (Month/Quarter)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Split into Weeks   │
                    │  (7-day chunks)     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  Week 1  │    │  Week 2  │    │  Week N  │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  Fetch   │    │  Fetch   │    │  Fetch   │
        │  Week    │    │  Week    │    │  Week    │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             ▼               ▼               ▼
        ┌──────────────────────────────────────────┐
        │         Check Result Count               │
        └────────────────────┬─────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  Count < 100    │          │  Count >= 100   │
    │  (Normal Week)  │          │ (High Activity) │
    └────────┬────────┘          └────────┬────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  Use Week Data  │          │  Re-fetch by    │
    │  As-Is          │          │  Day (7 calls)  │
    └─────────────────┘          └─────────────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  Merge Daily    │
                                 │  Results        │
                                 └─────────────────┘
```

### Fetching Logic

```python
# Threshold for switching to day-by-day fetching
HIGH_ACTIVITY_THRESHOLD = 100  # events per week

def fetch_period_data(start_date: date, end_date: date) -> list[Event]:
    """
    Fetch data for a period using adaptive granularity.
    """
    all_events = []

    for week_start, week_end in iter_weeks(start_date, end_date):
        # First attempt: fetch entire week
        week_events = fetch_week(week_start, week_end)

        if len(week_events) >= HIGH_ACTIVITY_THRESHOLD:
            # High activity detected - fetch day by day for completeness
            logger.info(f"High activity week ({len(week_events)} events), "
                       f"switching to daily fetching")
            week_events = fetch_week_by_days(week_start, week_end)

        all_events.extend(week_events)

        # Respect rate limits between weeks
        rate_limit_pause()

    return deduplicate(all_events)


def fetch_week_by_days(week_start: date, week_end: date) -> list[Event]:
    """
    Fetch a high-activity week day by day for complete data.
    """
    daily_events = []

    for day in iter_days(week_start, week_end):
        day_events = fetch_day(day)
        daily_events.extend(day_events)
        rate_limit_pause()

    return daily_events
```

### Rate Limit Considerations

| Granularity | API Calls per Month | API Calls per Quarter |
|-------------|--------------------|-----------------------|
| Whole period | 1 | 1 |
| Weekly | 4-5 | 13-14 |
| Daily (fallback) | Up to 7 per week | Up to 7 per week |
| **Worst case** | ~35 calls | ~100 calls |

**GitHub API Limits:**
- Authenticated requests: 5,000/hour
- Search API: 30 requests/minute
- GraphQL: 5,000 points/hour

**Built-in Safeguards:**
- Automatic pause between requests (configurable, default 1s)
- Exponential backoff on rate limit errors
- Response header monitoring (`X-RateLimit-Remaining`)

### Week Boundary Handling

```python
def iter_weeks(start_date: date, end_date: date) -> Iterator[tuple[date, date]]:
    """
    Iterate through weeks, handling partial weeks at boundaries.

    Example for January 2024:
    - Week 1: Jan 1-7 (Mon-Sun or partial if month starts mid-week)
    - Week 2: Jan 8-14
    - Week 3: Jan 15-21
    - Week 4: Jan 22-28
    - Week 5: Jan 29-31 (partial week)
    """
    current = start_date
    while current <= end_date:
        week_end = min(current + timedelta(days=6), end_date)
        yield (current, week_end)
        current = week_end + timedelta(days=1)
```

---

## JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GitHub Activity Report",
  "type": "object",
  "required": ["metadata", "summary", "activity"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["generated_at", "user", "period"],
      "properties": {
        "generated_at": { "type": "string", "format": "date-time" },
        "user": {
          "type": "object",
          "properties": {
            "login": { "type": "string" },
            "id": { "type": "integer" },
            "name": { "type": "string" }
          }
        },
        "period": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["monthly", "quarterly"] },
            "year": { "type": "integer" },
            "month": { "type": "integer", "minimum": 1, "maximum": 12 },
            "quarter": { "type": "integer", "minimum": 1, "maximum": 4 },
            "period_label": { "type": "string" },
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" }
          }
        },
        "schema_version": { "type": "string" }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_commits": { "type": "integer" },
        "total_prs_opened": { "type": "integer" },
        "total_prs_merged": { "type": "integer" },
        "total_prs_reviewed": { "type": "integer" },
        "total_issues_opened": { "type": "integer" },
        "total_issues_closed": { "type": "integer" },
        "total_comments": { "type": "integer" },
        "total_reactions_given": { "type": "integer" },
        "total_reactions_received": { "type": "integer" },
        "repos_contributed_to": { "type": "integer" },
        "most_active_day": { "type": "string" },
        "most_active_repo": { "type": "string" }
      }
    },
    "activity": {
      "type": "object",
      "properties": {
        "commits": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sha": { "type": "string" },
              "message": { "type": "string" },
              "repository": { "type": "string" },
              "date": { "type": "string", "format": "date-time" },
              "additions": { "type": "integer" },
              "deletions": { "type": "integer" }
            }
          }
        },
        "pull_requests": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "number": { "type": "integer" },
              "title": { "type": "string" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "created_at": { "type": "string" },
              "merged_at": { "type": "string" },
              "closed_at": { "type": "string" },
              "commits_count": { "type": "integer" },
              "review_comments": { "type": "integer" },
              "additions": { "type": "integer" },
              "deletions": { "type": "integer" }
            }
          }
        },
        "reviews": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pr_number": { "type": "integer" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "submitted_at": { "type": "string" },
              "body_length": { "type": "integer" }
            }
          }
        },
        "issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "number": { "type": "integer" },
              "title": { "type": "string" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "created_at": { "type": "string" },
              "closed_at": { "type": "string" },
              "labels": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "comments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "repository": { "type": "string" },
              "issue_number": { "type": "integer" },
              "created_at": { "type": "string" },
              "body_length": { "type": "integer" }
            }
          }
        },
        "reactions": {
          "type": "object",
          "properties": {
            "given": {
              "type": "object",
              "additionalProperties": { "type": "integer" }
            },
            "received": {
              "type": "object",
              "additionalProperties": { "type": "integer" }
            }
          }
        },
        "repositories": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "activity_type": { "type": "string" },
              "commits": { "type": "integer" },
              "prs": { "type": "integer" },
              "issues": { "type": "integer" },
              "reviews": { "type": "integer" }
            }
          }
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "pr_metrics": {
          "type": "object",
          "properties": {
            "avg_commits_per_pr": { "type": "number" },
            "avg_time_to_merge_hours": { "type": "number" },
            "avg_time_to_first_review_hours": { "type": "number" },
            "avg_review_iterations": { "type": "number" },
            "prs_merged_without_changes": { "type": "integer" },
            "prs_with_requested_changes": { "type": "integer" }
          }
        },
        "review_metrics": {
          "type": "object",
          "properties": {
            "avg_review_turnaround_hours": { "type": "number" },
            "reviews_with_comments": { "type": "integer" },
            "approvals": { "type": "integer" },
            "changes_requested": { "type": "integer" }
          }
        },
        "engagement_metrics": {
          "type": "object",
          "properties": {
            "avg_response_time_hours": { "type": "number" },
            "comment_to_code_ratio": { "type": "number" },
            "collaboration_score": { "type": "number" }
          }
        },
        "productivity_by_day": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "productivity_by_hour": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        }
      }
    }
  }
}
```

---

## Report Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPORT GENERATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Initialize
────────────────────
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Parse CLI   │────▶│ Load Config │────▶│ Validate    │
    │ Arguments   │     │ Settings    │     │ gh CLI Auth │
    └─────────────┘     └─────────────┘     └─────────────┘


Step 2: Fetch Data (Parallel Execution)
────────────────────────────────────────
                    ┌─────────────────────┐
                    │   Orchestrator      │
                    └──────────┬──────────┘
                               │
       ┌───────────┬───────────┼───────────┬───────────┐
       │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼
   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐
   │Events │   │Commits│   │  PRs  │   │Issues │   │Reviews│
   │Fetcher│   │Fetcher│   │Fetcher│   │Fetcher│   │Fetcher│
   └───┬───┘   └───┬───┘   └───┬───┘   └───┬───┘   └───┬───┘
       │           │           │           │           │
       └───────────┴───────────┼───────────┴───────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Raw Data Pool     │
                    └──────────┬──────────┘


Step 3: Process Data
────────────────────
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Filter by  │────▶│ Deduplicate │────▶│  Aggregate  │
    │ Date Range  │     │   Records   │     │   by Type   │
    └─────────────┘     └─────────────┘     └─────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────┐
                                          │  Calculate  │
                                          │   Metrics   │
                                          └──────┬──────┘


Step 4: Generate Output
───────────────────────
                    ┌─────────────────────┐
                    │   Build JSON        │
                    │   Structure         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Validate vs       │
                    │   JSON Schema       │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
       ┌─────────────────┐          ┌─────────────────┐
       │   Save JSON     │          │ Generate & Save │
       │   Report        │          │ Markdown Report │
       └─────────────────┘          └─────────────────┘


Step 5: Finalize
────────────────
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Generate    │────▶│  Log        │────▶│  Return     │
    │ File Names  │     │  Summary    │     │  File Paths │
    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Advanced Metrics Calculations

### 1. PR Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR LIFECYCLE METRICS                          │
└─────────────────────────────────────────────────────────────────┘

 PR Created          First Review         Approved           Merged
     │                    │                  │                  │
     ▼                    ▼                  ▼                  ▼
     ●────────────────────●──────────────────●──────────────────●
     │                    │                  │                  │
     │◄─────────────────▶│◄────────────────▶│◄────────────────▶│
     │  Time to First    │  Review Cycles   │  Time to Merge   │
     │     Review        │                  │  (post-approval) │
     └───────────────────┴──────────────────┴──────────────────┘

Metrics Calculated:
├── avg_commits_per_pr:        sum(commits) / count(prs)
├── avg_time_to_merge_hours:   avg(merged_at - created_at)
├── avg_time_to_first_review:  avg(first_review_at - created_at)
├── avg_review_iterations:     avg(count of review rounds per PR)
├── prs_merged_without_changes: count(prs where approved on first review)
└── prs_with_requested_changes: count(prs with "changes_requested" review)
```

### 2. Review Metrics

```
Metrics Calculated:
├── avg_review_turnaround:    avg(review_submitted_at - review_requested_at)
├── reviews_with_comments:    count(reviews where body.length > 0)
├── approvals:               count(reviews where state == "APPROVED")
└── changes_requested:       count(reviews where state == "CHANGES_REQUESTED")
```

### 3. Engagement Metrics

```
Metrics Calculated:
├── avg_response_time:       avg(time between comment and reply)
├── comment_to_code_ratio:   total_comments / total_commits
└── collaboration_score:     weighted(reviews + comments + reactions)
```

---

## File Organization

### Report Naming Convention

```
reports/
└── {year}/
    ├── {year}-{month}-github-activity-{n}.md      # Monthly reports
    └── {year}-Q{quarter}-github-activity-{n}.md   # Quarterly reports

Monthly Examples:
reports/2024/2024-12-github-activity-1.md
reports/2024/2024-12-github-activity-2.md  (if regenerated)
reports/2025/2025-01-github-activity-1.md

Quarterly Examples:
reports/2024/2024-Q4-github-activity-1.md
reports/2024/2024-Q4-github-activity-2.md  (if regenerated)
reports/2025/2025-Q1-github-activity-1.md
```

### Period Date Ranges

**Monthly:**
| Month | Start Date | End Date |
|-------|------------|----------|
| 01 (Jan) | {year}-01-01 | {year}-01-31 |
| 02 (Feb) | {year}-02-01 | {year}-02-28/29 |
| ... | ... | ... |
| 12 (Dec) | {year}-12-01 | {year}-12-31 |

**Quarterly:**
| Quarter | Months | Start Date | End Date |
|---------|--------|------------|----------|
| Q1 | Jan, Feb, Mar | {year}-01-01 | {year}-03-31 |
| Q2 | Apr, May, Jun | {year}-04-01 | {year}-06-30 |
| Q3 | Jul, Aug, Sep | {year}-07-01 | {year}-09-30 |
| Q4 | Oct, Nov, Dec | {year}-10-01 | {year}-12-31 |

### Increment Logic

```python
from calendar import monthrange
from typing import Literal

def get_next_filename(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> str:
    """
    Scans existing reports and returns next available filename.

    Monthly pattern: {year}-{month:02d}-github-activity-{n}.md
    Quarterly pattern: {year}-Q{quarter}-github-activity-{n}.md
    """
    base_dir = reports_dir / str(year)

    if period_type == "monthly":
        pattern = f"{year}-{period_value:02d}-github-activity-*.md"
        prefix = f"{year}-{period_value:02d}-github-activity"
    else:
        pattern = f"{year}-Q{period_value}-github-activity-*.md"
        prefix = f"{year}-Q{period_value}-github-activity"

    existing = sorted(base_dir.glob(pattern))

    if not existing:
        return f"{prefix}-1.md"

    last_num = int(existing[-1].stem.split('-')[-1])
    return f"{prefix}-{last_num + 1}.md"


def get_period_dates(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> tuple[str, str]:
    """
    Returns start and end dates for a given period.
    """
    if period_type == "monthly":
        _, last_day = monthrange(year, period_value)
        return (
            f"{year}-{period_value:02d}-01",
            f"{year}-{period_value:02d}-{last_day:02d}"
        )
    else:
        quarters = {
            1: (f"{year}-01-01", f"{year}-03-31"),
            2: (f"{year}-04-01", f"{year}-06-30"),
            3: (f"{year}-07-01", f"{year}-09-30"),
            4: (f"{year}-10-01", f"{year}-12-31"),
        }
        return quarters[period_value]
```

### Report Cleanup Thresholds

Reports are automatically cleaned up based on configurable thresholds, similar to logs:

```yaml
# In config.yaml
output:
  directory: reports
  formats:
    - json
    - markdown

  # ===========================================================================
  # REPORT CLEANUP THRESHOLDS
  # ===========================================================================

  cleanup:
    # Enable automatic cleanup
    enabled: true

    # When to run cleanup: startup, shutdown, both, manual
    trigger: startup

    # -------------------------------------------------------------------------
    # Time-based cleanup
    # -------------------------------------------------------------------------
    retention_years: 2                # Keep reports for 2 years
    retention_months: 24              # Alternative: specify in months

    # -------------------------------------------------------------------------
    # Version-based cleanup (multiple regenerations of same period)
    # -------------------------------------------------------------------------
    keep_versions: 3                  # Keep last 3 versions per period
                                      # e.g., keep -1, -2, -3; delete -4, -5...

    # -------------------------------------------------------------------------
    # Size-based cleanup
    # -------------------------------------------------------------------------
    max_total_size_mb: 1000           # Max total size of all reports
    max_file_size_mb: 100             # Max size per report file

    # -------------------------------------------------------------------------
    # Count-based cleanup
    # -------------------------------------------------------------------------
    max_reports: 500                  # Max number of report files

    # -------------------------------------------------------------------------
    # Archive settings (instead of delete)
    # -------------------------------------------------------------------------
    archive:
      enabled: true                   # Archive old reports instead of delete
      directory: reports/archive      # Archive location
      compress: true                  # Compress archived reports (.gz)
      archive_after_days: 365         # Archive reports older than 1 year

    # -------------------------------------------------------------------------
    # Cleanup strategy
    # -------------------------------------------------------------------------
    strategy: oldest_first            # oldest_first, largest_first

    # Safety: always keep minimum reports
    keep_minimum_months: 6            # Always keep at least 6 months
```

### Report Cleanup Thresholds Summary

| Threshold | Default | Description |
|-----------|---------|-------------|
| `retention_years` | 2 | Delete/archive reports older than this |
| `keep_versions` | 3 | Keep N versions per period (delete older regenerations) |
| `max_total_size_mb` | 1000 | Max total size of reports directory |
| `max_file_size_mb` | 100 | Max size per individual report |
| `max_reports` | 500 | Maximum number of report files |
| `keep_minimum_months` | 6 | Always keep at least this many months |
| `archive.archive_after_days` | 365 | Archive reports older than this |

### Report Cleanup Implementation

```python
# src/utils/report_cleanup.py

from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
import gzip
import shutil
import re


@dataclass
class ReportCleanupThresholds:
    """Configurable cleanup thresholds for reports."""
    retention_years: int = 2
    keep_versions: int = 3
    max_total_size_mb: int = 1000
    max_file_size_mb: int = 100
    max_reports: int = 500
    keep_minimum_months: int = 6
    archive_enabled: bool = True
    archive_after_days: int = 365
    compress_archive: bool = True
    strategy: str = "oldest_first"


class ReportCleaner:
    """
    Automatic report cleanup based on configurable thresholds.
    """

    # Pattern: 2024-12-github-activity-1.md or 2024-Q4-github-activity-2.json
    REPORT_PATTERN = re.compile(
        r"(\d{4})-(\d{2}|Q[1-4])-github-activity-(\d+)\.(md|json)"
    )

    def __init__(self, reports_dir: Path, thresholds: ReportCleanupThresholds):
        self.reports_dir = reports_dir
        self.thresholds = thresholds
        self.stats = {
            "deleted": 0,
            "archived": 0,
            "freed_mb": 0,
            "versions_cleaned": 0
        }

    def cleanup(self) -> dict:
        """
        Run all cleanup operations and return statistics.
        """
        self._cleanup_old_versions()
        self._cleanup_by_age()
        self._archive_old_reports()
        self._cleanup_by_size()
        self._cleanup_by_count()
        self._remove_empty_directories()

        return self.stats

    def _cleanup_old_versions(self):
        """Keep only the last N versions of each period's report."""
        # Group reports by period (year-month or year-quarter)
        reports_by_period: dict[str, list[Path]] = {}

        for report_file in self.reports_dir.rglob("*.md"):
            match = self.REPORT_PATTERN.match(report_file.name)
            if not match:
                continue

            year, period, version, ext = match.groups()
            period_key = f"{year}-{period}"

            if period_key not in reports_by_period:
                reports_by_period[period_key] = []
            reports_by_period[period_key].append((int(version), report_file))

        # Also check JSON files
        for report_file in self.reports_dir.rglob("*.json"):
            match = self.REPORT_PATTERN.match(report_file.name)
            if not match:
                continue

            year, period, version, ext = match.groups()
            period_key = f"{year}-{period}-json"

            if period_key not in reports_by_period:
                reports_by_period[period_key] = []
            reports_by_period[period_key].append((int(version), report_file))

        # Delete old versions, keep only the last N
        for period_key, versions in reports_by_period.items():
            versions.sort(key=lambda x: x[0], reverse=True)

            for version_num, report_file in versions[self.thresholds.keep_versions:]:
                self._delete_file(report_file)
                self.stats["versions_cleaned"] += 1

    def _cleanup_by_age(self):
        """Delete reports older than retention threshold."""
        cutoff = datetime.now() - timedelta(
            days=self.thresholds.retention_years * 365
        )
        minimum_cutoff = datetime.now() - timedelta(
            days=self.thresholds.keep_minimum_months * 30
        )

        for report_file in self._get_all_reports():
            report_date = self._parse_date_from_report(report_file)
            if not report_date:
                continue

            # Never delete if within minimum retention
            if report_date >= minimum_cutoff:
                continue

            if report_date < cutoff:
                self._delete_file(report_file)

    def _archive_old_reports(self):
        """Archive reports older than archive threshold."""
        if not self.thresholds.archive_enabled:
            return

        archive_cutoff = datetime.now() - timedelta(
            days=self.thresholds.archive_after_days
        )
        minimum_cutoff = datetime.now() - timedelta(
            days=self.thresholds.keep_minimum_months * 30
        )

        archive_dir = self.reports_dir / "archive"

        for report_file in self._get_all_reports():
            report_date = self._parse_date_from_report(report_file)
            if not report_date:
                continue

            # Never archive if within minimum retention
            if report_date >= minimum_cutoff:
                continue

            if report_date < archive_cutoff:
                self._archive_file(report_file, archive_dir)

    def _archive_file(self, file_path: Path, archive_dir: Path):
        """Archive a report file (optionally compressed)."""
        # Maintain year structure in archive
        year = file_path.parent.name
        dest_dir = archive_dir / year
        dest_dir.mkdir(parents=True, exist_ok=True)

        if self.thresholds.compress_archive:
            archive_path = dest_dir / f"{file_path.name}.gz"
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            archive_path = dest_dir / file_path.name
            shutil.move(file_path, archive_path)

        # Delete original after archiving
        if file_path.exists():
            file_path.unlink()

        self.stats["archived"] += 1

    def _cleanup_by_size(self):
        """Delete reports if total size exceeds threshold."""
        max_bytes = self.thresholds.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.thresholds.max_file_size_mb * 1024 * 1024

        # First, handle oversized individual files
        for report_file in self._get_all_reports():
            if report_file.stat().st_size > max_file_bytes:
                self._delete_file(report_file)

        # Then, check total size
        total_size = sum(f.stat().st_size for f in self._get_all_reports())

        if total_size > max_bytes:
            self._free_space_by_strategy(total_size - max_bytes)

    def _cleanup_by_count(self):
        """Delete reports if file count exceeds threshold."""
        reports = sorted(
            self._get_all_reports(),
            key=lambda f: self._parse_date_from_report(f) or datetime.min
        )

        while len(reports) > self.thresholds.max_reports:
            oldest = reports.pop(0)
            self._delete_file(oldest)

    def _free_space_by_strategy(self, bytes_to_free: int):
        """Free up space using configured strategy."""
        reports = list(self._get_all_reports())

        if self.thresholds.strategy == "oldest_first":
            reports.sort(
                key=lambda f: self._parse_date_from_report(f) or datetime.min
            )
        elif self.thresholds.strategy == "largest_first":
            reports.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for report_file in reports:
            if freed >= bytes_to_free:
                break
            freed += report_file.stat().st_size
            self._delete_file(report_file)

    def _get_all_reports(self) -> list[Path]:
        """Get all report files (excluding archive)."""
        reports = []
        for ext in ("*.md", "*.json"):
            for f in self.reports_dir.rglob(ext):
                if "archive" not in f.parts:
                    reports.append(f)
        return reports

    def _parse_date_from_report(self, file_path: Path) -> datetime | None:
        """Parse date from report filename."""
        match = self.REPORT_PATTERN.match(file_path.name)
        if not match:
            return None

        year, period, _, _ = match.groups()

        try:
            if period.startswith("Q"):
                # Quarterly: use last month of quarter
                quarter = int(period[1])
                month = quarter * 3
            else:
                month = int(period)

            return datetime(int(year), month, 1)
        except (ValueError, IndexError):
            return None

    def _delete_file(self, file_path: Path):
        """Delete a file and update stats."""
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_path.unlink()
        self.stats["deleted"] += 1
        self.stats["freed_mb"] += size_mb

    def _remove_empty_directories(self):
        """Remove empty year directories."""
        for year_dir in self.reports_dir.iterdir():
            if year_dir.is_dir() and year_dir.name != "archive":
                if not any(year_dir.iterdir()):
                    year_dir.rmdir()
```

### Report Cleanup Display

```
┌─────────────────────────────────────────────────────────────────┐
│                     REPORT CLEANUP SUMMARY                       │
├─────────────────────────────────────────────────────────────────┤
│  Trigger: startup                                                │
│                                                                  │
│  Actions Taken:                                                  │
│  ├── Old versions cleaned: 8 files                              │
│  │   └── Kept last 3 versions per period                        │
│  ├── Archived (>1 year old): 24 files                           │
│  │   └── Compressed to reports/archive/                         │
│  ├── Deleted by age (>2 years): 6 files                         │
│  └── Deleted by size: 0 files                                   │
│                                                                  │
│  Space Freed: 45.2 MB                                           │
│  Current Usage: 234.5 MB / 1000 MB limit                        │
│  Reports Remaining: 156 / 500 limit                             │
│                                                                  │
│  Archive Status:                                                 │
│  └── reports/archive/: 24 files, 12.3 MB (compressed)           │
└─────────────────────────────────────────────────────────────────┘
```

### Version Cleanup Example

```
Before cleanup (keep_versions: 3):
reports/2024/
├── 2024-12-github-activity-1.md    # DELETE (old version)
├── 2024-12-github-activity-2.md    # DELETE (old version)
├── 2024-12-github-activity-3.md    # KEEP
├── 2024-12-github-activity-4.md    # KEEP
├── 2024-12-github-activity-5.md    # KEEP (latest)
├── 2024-Q4-github-activity-1.md    # KEEP
└── 2024-Q4-github-activity-2.md    # KEEP (latest)

After cleanup:
reports/2024/
├── 2024-12-github-activity-3.md    # Kept
├── 2024-12-github-activity-4.md    # Kept
├── 2024-12-github-activity-5.md    # Kept (latest)
├── 2024-Q4-github-activity-1.md    # Kept
└── 2024-Q4-github-activity-2.md    # Kept (latest)
```

---

## Clarifying Questions

Before proceeding with implementation, please clarify the following:

### 1. Scope & Access

| # | Question | Options | Default |
|---|----------|---------|---------|
| 1.1 | Should the script work with **private repositories** or only public? | A) Both private and public<br>B) Public only<br>C) Configurable | A |
| 1.2 | Should we include activity from **forked repositories**? | A) Yes<br>B) No<br>C) Configurable | C |
| 1.3 | Filter by specific **organizations** or all? | A) All accessible orgs<br>B) Configurable org list<br>C) Single org only | B |

### 2. Metrics & Data

| # | Question | Options | Default |
|---|----------|---------|---------|
| 2.1 | How detailed should **commit data** be? | A) Basic (sha, message, date)<br>B) Full (includes additions/deletions per file) | A |
| 2.2 | Should we track **draft PRs** separately? | A) Yes, separate category<br>B) Include with regular PRs<br>C) Exclude drafts | B |
| 2.3 | Include **reaction emoji breakdown** (👍, ❤️, etc.)? | A) Yes, detailed<br>B) Just totals<br>C) No reactions | A |

### 3. Output & Storage

| # | Question | Options | Default |
|---|----------|---------|---------|
| 3.1 | Should JSON file be saved alongside Markdown? | A) Yes, both files<br>B) JSON only (generate MD on demand)<br>C) MD only (JSON internal) | A |
| 3.2 | Should the report include **full commit messages** or just first line? | A) Full message<br>B) First line only<br>C) First 100 chars | B |
| 3.3 | Include **links to GitHub** in the report? | A) Yes, all items<br>B) Just PRs and Issues<br>C) No links | A |

### 4. Performance & Limits

| # | Question | Options | Default |
|---|----------|---------|---------|
| 4.1 | What's the expected **maximum events per period**? | A) < 500/month, < 1500/quarter<br>B) 500-2000/month, 1500-6000/quarter<br>C) Higher | B |
| 4.2 | Enable **caching** for repeated runs? | A) Yes, cache API responses<br>B) No, always fresh | A |
| 4.3 | **Rate limit handling** strategy? | A) Wait and retry<br>B) Fail fast<br>C) Use cached data | A |

### 5. User Experience

| # | Question | Options | Default |
|---|----------|---------|---------|
| 5.1 | ~~**Default username** behavior?~~ | ~~A) Use authenticated gh user~~ | **DECIDED: A** |
| 5.2 | **Progress output** preference? | A) Verbose with progress bar<br>B) Minimal (start/end only)<br>C) Silent (errors only) | A |
| 5.3 | Support **multiple periods** in one run? | A) Yes (--from/--to date range)<br>B) No, one period only | B |

---

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
- [ ] Set up project structure and virtual environment
- [ ] Create `config.yaml` with all settings
- [ ] Implement `settings.py` (load config with CLI/env override support)
- [ ] Implement `gh_client.py` wrapper for subprocess calls
- [ ] Implement `date_utils.py` for monthly/quarterly date range calculations
- [ ] Implement `file_utils.py` for report file management
- [ ] Add JSON schema file for report validation

### Phase 2: Data Fetching
- [ ] Implement base fetcher class
- [ ] Implement events fetcher (primary data source)
- [ ] Implement commits fetcher (search API)
- [ ] Implement PR fetcher with details
- [ ] Implement issues fetcher
- [ ] Implement reviews fetcher
- [ ] Implement comments fetcher
- [ ] Add pagination handling for all fetchers

### Phase 3: Data Processing
- [ ] Implement date range filtering
- [ ] Implement deduplication logic
- [ ] Implement data aggregation
- [ ] Build summary statistics calculator

### Phase 4: Metrics Calculation
- [ ] Implement PR metrics (time to merge, commits per PR, etc.)
- [ ] Implement review metrics (turnaround time, approval rate)
- [ ] Implement engagement metrics (response time, collaboration score)
- [ ] Implement productivity patterns (by day, by hour)

### Phase 5: Report Generation
- [ ] Implement JSON report builder
- [ ] Implement JSON schema validator
- [ ] Implement Markdown report generator
- [ ] Implement file naming with increment logic

### Phase 6: CLI & Polish
- [ ] Build CLI argument parser
- [ ] Add progress indicators
- [ ] Add error handling and logging
- [ ] Write README documentation

### Phase 7: Testing
- [ ] Set up pytest with fixtures and configuration
- [ ] Create mock GitHub API responses
- [ ] Write unit tests for all modules (target: 90% coverage)
- [ ] Write integration tests for end-to-end flows
- [ ] Add CI/CD pipeline configuration

---

## Testing Strategy

Comprehensive testing to ensure code integrity and prevent regressions.

### Test Structure

```
.scripts/github-activity/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures and configuration
│   │
│   ├── fixtures/                      # Test data
│   │   ├── api_responses/             # Mock GitHub API responses
│   │   │   ├── events_page_1.json
│   │   │   ├── events_page_2.json
│   │   │   ├── commits_search.json
│   │   │   ├── pr_details.json
│   │   │   ├── pr_reviews.json
│   │   │   └── user_info.json
│   │   ├── expected_outputs/          # Expected report outputs
│   │   │   ├── monthly_report.json
│   │   │   └── quarterly_report.md
│   │   └── config/                    # Test configurations
│   │       ├── minimal_config.yaml
│   │       └── full_config.yaml
│   │
│   ├── unit/                          # Unit tests (isolated, mocked)
│   │   ├── __init__.py
│   │   ├── test_config.py             # Configuration loading
│   │   ├── test_date_utils.py         # Date utilities
│   │   ├── test_file_utils.py         # File operations
│   │   ├── test_gh_client.py          # GitHub CLI wrapper
│   │   ├── fetchers/
│   │   │   ├── test_events_fetcher.py
│   │   │   ├── test_commits_fetcher.py
│   │   │   ├── test_pr_fetcher.py
│   │   │   └── test_adaptive_fetch.py
│   │   ├── processors/
│   │   │   ├── test_aggregator.py
│   │   │   ├── test_metrics.py
│   │   │   └── test_filters.py
│   │   └── reporters/
│   │       ├── test_json_report.py
│   │       ├── test_markdown_report.py
│   │       └── test_validator.py
│   │
│   ├── integration/                   # Integration tests (real flow, mocked API)
│   │   ├── __init__.py
│   │   ├── test_monthly_report.py
│   │   ├── test_quarterly_report.py
│   │   ├── test_cli.py
│   │   └── test_error_recovery.py
│   │
│   └── e2e/                           # End-to-end tests (optional, real API)
│       ├── __init__.py
│       └── test_live_api.py           # Skipped by default, run with --live
│
├── pytest.ini                         # Pytest configuration
└── .coveragerc                        # Coverage configuration
```

### Test Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, mocked API)
    e2e: End-to-end tests (requires live API, use --live flag)
    slow: Tests that take > 1s

# Default options
addopts =
    -v
    --tb=short
    --strict-markers
    -m "not e2e"
    --cov=src
    --cov-report=term-missing
    --cov-report=html:coverage_html
    --cov-fail-under=80

# Async support
asyncio_mode = auto
```

```ini
# .coveragerc
[run]
source = src
omit =
    src/__init__.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    if __name__ == .__main__.:

[html]
directory = coverage_html
```

### Shared Fixtures

```python
# tests/conftest.py

import pytest
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch
import json

# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def api_responses_dir(fixtures_dir):
    """Path to mock API responses."""
    return fixtures_dir / "api_responses"

@pytest.fixture
def temp_reports_dir(tmp_path):
    """Temporary directory for report output."""
    reports = tmp_path / "reports"
    reports.mkdir()
    return reports

@pytest.fixture
def temp_logs_dir(tmp_path):
    """Temporary directory for logs."""
    logs = tmp_path / "logs"
    logs.mkdir()
    return logs

# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def minimal_config():
    """Minimal configuration for testing."""
    return {
        "user": {"username": "testuser", "organizations": []},
        "repositories": {"include_private": True, "include_forks": False},
        "fetching": {"high_activity_threshold": 100, "request_delay": 0},
        "cache": {"enabled": False},
        "output": {"directory": "reports", "formats": ["json", "markdown"]},
        "logging": {"level": "DEBUG"},
    }

@pytest.fixture
def full_config(fixtures_dir):
    """Full configuration from fixture file."""
    config_path = fixtures_dir / "config" / "full_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

# =============================================================================
# Mock API Response Fixtures
# =============================================================================

@pytest.fixture
def mock_events_response(api_responses_dir):
    """Mock events API response."""
    with open(api_responses_dir / "events_page_1.json") as f:
        return json.load(f)

@pytest.fixture
def mock_user_info():
    """Mock user info response."""
    return {
        "login": "testuser",
        "id": 12345,
        "name": "Test User",
        "company": "Test Company",
    }

@pytest.fixture
def mock_gh_client(mock_events_response, mock_user_info):
    """Mock GitHub CLI client."""
    client = Mock()
    client.get_user_info.return_value = mock_user_info
    client.get_events.return_value = mock_events_response
    client.rate_limit_remaining = 5000
    return client

# =============================================================================
# Date Fixtures
# =============================================================================

@pytest.fixture
def sample_month():
    """Sample month for testing (December 2024)."""
    return {"year": 2024, "month": 12}

@pytest.fixture
def sample_quarter():
    """Sample quarter for testing (Q4 2024)."""
    return {"year": 2024, "quarter": 4}

@pytest.fixture
def sample_date_range():
    """Sample date range for December 2024."""
    return {
        "start": date(2024, 12, 1),
        "end": date(2024, 12, 31),
    }

# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_events():
    """Sample processed events for testing."""
    return [
        {
            "type": "PushEvent",
            "created_at": "2024-12-15T10:30:00Z",
            "repo": "owner/repo",
            "commits": [{"sha": "abc123", "message": "Fix bug"}],
        },
        {
            "type": "PullRequestEvent",
            "created_at": "2024-12-16T14:00:00Z",
            "repo": "owner/repo",
            "action": "opened",
            "number": 42,
            "title": "Add feature",
        },
    ]

@pytest.fixture
def sample_report_data(sample_events):
    """Sample report data structure."""
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "user": {"login": "testuser", "id": 12345},
            "period": {
                "type": "monthly",
                "year": 2024,
                "month": 12,
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
            },
        },
        "summary": {
            "total_commits": 15,
            "total_prs_opened": 3,
            "total_prs_merged": 2,
        },
        "activity": {
            "commits": [],
            "pull_requests": [],
        },
    }
```

### Unit Test Examples

```python
# tests/unit/test_date_utils.py

import pytest
from datetime import date
from src.utils.date_utils import (
    get_period_dates,
    get_quarter_from_month,
    iter_weeks,
)


class TestGetPeriodDates:
    """Tests for get_period_dates function."""

    def test_monthly_january(self):
        """January should be 01-01 to 01-31."""
        start, end = get_period_dates(2024, "monthly", 1)
        assert start == "2024-01-01"
        assert end == "2024-01-31"

    def test_monthly_february_leap_year(self):
        """February 2024 (leap year) should end on 29th."""
        start, end = get_period_dates(2024, "monthly", 2)
        assert end == "2024-02-29"

    def test_monthly_february_non_leap_year(self):
        """February 2023 (non-leap) should end on 28th."""
        start, end = get_period_dates(2023, "monthly", 2)
        assert end == "2023-02-28"

    def test_quarterly_q1(self):
        """Q1 should be January to March."""
        start, end = get_period_dates(2024, "quarterly", 1)
        assert start == "2024-01-01"
        assert end == "2024-03-31"

    def test_quarterly_q4(self):
        """Q4 should be October to December."""
        start, end = get_period_dates(2024, "quarterly", 4)
        assert start == "2024-10-01"
        assert end == "2024-12-31"

    @pytest.mark.parametrize("month,expected_quarter", [
        (1, 1), (2, 1), (3, 1),
        (4, 2), (5, 2), (6, 2),
        (7, 3), (8, 3), (9, 3),
        (10, 4), (11, 4), (12, 4),
    ])
    def test_get_quarter_from_month(self, month, expected_quarter):
        """Each month should map to correct quarter."""
        assert get_quarter_from_month(month) == expected_quarter


class TestIterWeeks:
    """Tests for week iteration function."""

    def test_full_month_weeks(self):
        """December 2024 should have 5 weeks."""
        weeks = list(iter_weeks(date(2024, 12, 1), date(2024, 12, 31)))
        assert len(weeks) == 5

    def test_week_boundaries(self):
        """Each week should be max 7 days."""
        weeks = list(iter_weeks(date(2024, 12, 1), date(2024, 12, 31)))
        for start, end in weeks:
            days = (end - start).days + 1
            assert 1 <= days <= 7

    def test_no_gaps(self):
        """Weeks should be contiguous with no gaps."""
        weeks = list(iter_weeks(date(2024, 12, 1), date(2024, 12, 31)))
        for i in range(1, len(weeks)):
            prev_end = weeks[i-1][1]
            curr_start = weeks[i][0]
            assert (curr_start - prev_end).days == 1
```

```python
# tests/unit/fetchers/test_adaptive_fetch.py

import pytest
from unittest.mock import Mock, patch, call
from src.fetchers.base import AdaptiveFetcher


class TestAdaptiveFetcher:
    """Tests for adaptive fetching strategy."""

    @pytest.fixture
    def fetcher(self, mock_gh_client, minimal_config):
        """Create fetcher with mocked client."""
        return AdaptiveFetcher(mock_gh_client, minimal_config)

    def test_normal_week_single_fetch(self, fetcher, mock_gh_client):
        """Week with < 100 events should use single fetch."""
        mock_gh_client.fetch_week.return_value = [{"id": i} for i in range(50)]

        result = fetcher.fetch_period(
            start=date(2024, 12, 1),
            end=date(2024, 12, 7)
        )

        assert mock_gh_client.fetch_week.call_count == 1
        assert mock_gh_client.fetch_day.call_count == 0
        assert len(result) == 50

    def test_high_activity_week_daily_fetch(self, fetcher, mock_gh_client):
        """Week with >= 100 events should switch to daily fetch."""
        # First call returns high activity
        mock_gh_client.fetch_week.return_value = [{"id": i} for i in range(120)]
        # Daily fetches return smaller chunks
        mock_gh_client.fetch_day.return_value = [{"id": i} for i in range(20)]

        result = fetcher.fetch_period(
            start=date(2024, 12, 1),
            end=date(2024, 12, 7)
        )

        assert mock_gh_client.fetch_week.call_count == 1
        assert mock_gh_client.fetch_day.call_count == 7  # One for each day

    def test_respects_rate_limit_pause(self, fetcher, mock_gh_client):
        """Should pause between API calls."""
        mock_gh_client.fetch_week.return_value = []

        with patch("time.sleep") as mock_sleep:
            fetcher.fetch_period(
                start=date(2024, 12, 1),
                end=date(2024, 12, 14)  # 2 weeks
            )

        # Should pause between weeks
        assert mock_sleep.call_count >= 1

    def test_deduplicates_events(self, fetcher, mock_gh_client):
        """Should remove duplicate events by ID."""
        # Return same event twice
        duplicate_event = {"id": "123", "type": "PushEvent"}
        mock_gh_client.fetch_week.return_value = [duplicate_event, duplicate_event]

        result = fetcher.fetch_period(
            start=date(2024, 12, 1),
            end=date(2024, 12, 7)
        )

        assert len(result) == 1
```

### Integration Test Examples

```python
# tests/integration/test_monthly_report.py

import pytest
from pathlib import Path
from click.testing import CliRunner
from src.cli import main
from src.reporters.validator import validate_report


class TestMonthlyReportGeneration:
    """Integration tests for monthly report generation."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_api(self, mock_gh_client):
        """Patch gh_client with mock."""
        with patch("src.fetchers.base.GHClient", return_value=mock_gh_client):
            yield mock_gh_client

    def test_generates_valid_json_report(
        self, runner, mock_api, temp_reports_dir, minimal_config
    ):
        """Should generate a valid JSON report."""
        result = runner.invoke(main, [
            "-m", "12",
            "-y", "2024",
            "--output-dir", str(temp_reports_dir),
            "--format", "json",
        ])

        assert result.exit_code == 0

        # Find generated report
        reports = list(temp_reports_dir.glob("2024/*.json"))
        assert len(reports) == 1

        # Validate against schema
        with open(reports[0]) as f:
            report_data = json.load(f)

        errors = validate_report(report_data)
        assert errors == []

    def test_generates_markdown_report(
        self, runner, mock_api, temp_reports_dir
    ):
        """Should generate a Markdown report with expected sections."""
        result = runner.invoke(main, [
            "-m", "12",
            "-y", "2024",
            "--output-dir", str(temp_reports_dir),
            "--format", "markdown",
        ])

        assert result.exit_code == 0

        reports = list(temp_reports_dir.glob("2024/*.md"))
        assert len(reports) == 1

        content = reports[0].read_text()
        assert "# GitHub Activity Report" in content
        assert "## Summary" in content
        assert "## Commits" in content
        assert "## Pull Requests" in content

    def test_increments_filename_on_regenerate(
        self, runner, mock_api, temp_reports_dir
    ):
        """Should increment filename when report exists."""
        # Generate first report
        runner.invoke(main, ["-m", "12", "-y", "2024",
                            "--output-dir", str(temp_reports_dir)])

        # Generate second report
        runner.invoke(main, ["-m", "12", "-y", "2024",
                            "--output-dir", str(temp_reports_dir)])

        reports = sorted(temp_reports_dir.glob("2024/*-github-activity-*.md"))
        assert len(reports) == 2
        assert "activity-1" in reports[0].name
        assert "activity-2" in reports[1].name

    def test_handles_empty_activity(self, runner, mock_api, temp_reports_dir):
        """Should handle months with no activity gracefully."""
        mock_api.get_events.return_value = []

        result = runner.invoke(main, [
            "-m", "12",
            "-y", "2024",
            "--output-dir", str(temp_reports_dir),
        ])

        assert result.exit_code == 0
        assert "No activity found" in result.output or "0 events" in result.output
```

### Test Commands

```bash
# Run all tests (except e2e)
pytest

# Run only unit tests (fast)
pytest -m unit

# Run integration tests
pytest -m integration

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_date_utils.py

# Run tests matching pattern
pytest -k "test_monthly"

# Run with verbose output
pytest -v

# Run e2e tests with live API (requires auth)
pytest -m e2e --live

# Run tests in parallel (faster)
pytest -n auto

# Generate coverage badge
pytest --cov=src --cov-report=xml
```

### Coverage Requirements

| Module | Minimum Coverage |
|--------|------------------|
| `src/utils/` | 95% |
| `src/config/` | 90% |
| `src/fetchers/` | 85% |
| `src/processors/` | 90% |
| `src/reporters/` | 90% |
| **Overall** | **80%** |

### CI/CD Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check src tests
          ruff format --check src tests

      - name: Run type checking
        run: |
          mypy src

      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: true

  e2e:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run e2e tests
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
        run: |
          pytest -m e2e --live
```

### Mock API Response Files

```json
// tests/fixtures/api_responses/events_page_1.json
[
  {
    "id": "12345678901",
    "type": "PushEvent",
    "actor": {"id": 12345, "login": "testuser"},
    "repo": {"id": 67890, "name": "owner/repo"},
    "payload": {
      "push_id": 123456,
      "size": 1,
      "commits": [
        {
          "sha": "abc123def456",
          "message": "Fix critical bug in authentication",
          "author": {"name": "Test User", "email": "test@example.com"}
        }
      ]
    },
    "created_at": "2024-12-15T10:30:00Z"
  },
  {
    "id": "12345678902",
    "type": "PullRequestEvent",
    "actor": {"id": 12345, "login": "testuser"},
    "repo": {"id": 67890, "name": "owner/repo"},
    "payload": {
      "action": "opened",
      "number": 42,
      "pull_request": {
        "id": 987654,
        "title": "Add new feature",
        "state": "open",
        "created_at": "2024-12-16T14:00:00Z"
      }
    },
    "created_at": "2024-12-16T14:00:00Z"
  }
]
```

---

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                           │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │  API Call   │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │ Error Type?                          │
    └──────┬──────────────┬───────────────┘
           │              │
   ┌───────▼───────┐  ┌──▼──────────────┐
   │ Rate Limited  │  │ Network/Timeout │
   │ (HTTP 429)    │  │ Errors          │
   └───────┬───────┘  └────────┬────────┘
           │                   │
           ▼                   ▼
   ┌───────────────┐  ┌────────────────┐
   │ Wait for      │  │ Retry with     │
   │ X-RateLimit-  │  │ exponential    │
   │ Reset header  │  │ backoff (3x)   │
   └───────┬───────┘  └────────┬───────┘
           │                   │
           └─────────┬─────────┘
                     │
                     ▼
           ┌─────────────────┐
           │ Still failing?  │
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  ┌───────────┐          ┌───────────┐
  │ Log Error │          │ Use Cache │
  │ Continue  │          │ if avail  │
  │ w/ partial│          │           │
  └───────────┘          └───────────┘
```

---

## Logging System

An extensive logging system for error identification, performance optimization, and debugging.

### Log Levels

| Level | Flag | Purpose | Example Output |
|-------|------|---------|----------------|
| **ERROR** | default | Critical failures only | API failures, validation errors |
| **WARNING** | default | Issues that don't stop execution | Rate limit approaching, cache miss |
| **INFO** | `-v` | Progress and summary information | Fetching week 3/5, Report saved |
| **DEBUG** | `-vv` | Detailed operation logging | API request/response, timing |
| **TRACE** | `-vvv` | Full data dumps for troubleshooting | Raw JSON responses, full stack traces |

### Log Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOG FORMAT STRUCTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

Console Output (colorized):
┌──────────────────────────────────────────────────────────────────────────┐
│ 12:34:56 INFO  [fetcher.events] Fetching week 2024-01-01 to 2024-01-07   │
│ 12:34:57 INFO  [fetcher.events] ✓ Retrieved 45 events (0.82s)            │
│ 12:34:58 WARN  [api.client] Rate limit: 4,521/5,000 remaining            │
│ 12:35:01 DEBUG [fetcher.events] High activity detected (127 events)      │
│ 12:35:01 INFO  [fetcher.events] Switching to daily fetch for this week   │
└──────────────────────────────────────────────────────────────────────────┘

File Output (JSON Lines for parsing):
┌──────────────────────────────────────────────────────────────────────────┐
│ {"ts":"2024-01-15T12:34:56.123Z","level":"INFO","module":"fetcher.events"│
│  ,"msg":"Fetching week","start":"2024-01-01","end":"2024-01-07"}         │
│ {"ts":"2024-01-15T12:34:57.456Z","level":"INFO","module":"fetcher.events"│
│  ,"msg":"Retrieved events","count":45,"duration_ms":820}                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### Performance Metrics Logging

Every significant operation logs timing and resource usage:

```python
# Automatic performance logging for all operations
@log_performance
def fetch_week(start: date, end: date) -> list[Event]:
    ...

# Produces log entries like:
# DEBUG [perf] fetch_week: 823ms, 45 items, 2 API calls
# DEBUG [perf] process_events: 12ms, 45 items processed
# DEBUG [perf] generate_report: 156ms, 2 files written
```

**Performance Metrics Tracked:**

| Metric | Description | Log Level |
|--------|-------------|-----------|
| `duration_ms` | Operation execution time | DEBUG |
| `api_calls` | Number of API requests made | DEBUG |
| `items_processed` | Count of items handled | DEBUG |
| `cache_hits` | Cache hit/miss ratio | DEBUG |
| `memory_mb` | Memory usage (if significant) | DEBUG |
| `rate_limit_remaining` | GitHub API quota remaining | INFO (when < 20%) |

### API Request Logging

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API REQUEST LOG ENTRY                                │
└─────────────────────────────────────────────────────────────────────────────┘

DEBUG [api.client] Request:
  ├── Method: GET
  ├── Endpoint: /users/alhoseany/events
  ├── Params: {per_page: 100, page: 1}
  └── Timestamp: 2024-01-15T12:34:56.123Z

DEBUG [api.client] Response:
  ├── Status: 200 OK
  ├── Duration: 342ms
  ├── Items: 100
  ├── Rate Limit: 4,521/5,000 (resets in 45m)
  ├── Cache: MISS (stored for 24h)
  └── Next Page: Yes (Link header present)
```

### Error Context Logging

Errors include full context for quick debugging:

```python
# Error log structure
ERROR [fetcher.commits] Failed to fetch commits for week 2024-01-08
  Context:
    ├── user: alhoseany
    ├── period: 2024-01-08 to 2024-01-14
    ├── attempt: 3/3
    ├── last_error: ConnectionTimeout after 30s
    └── api_endpoint: /search/commits
  Stack Trace:
    └── [full traceback in DEBUG mode]
  Recovery:
    └── Using cached data from 2024-01-14T10:30:00Z (6h old)
```

### Log File Organization

Logs are organized by date and time for easy navigation and cleanup:

```
.scripts/github-activity/
└── logs/
    ├── 2024/                                      # Year
    │   ├── 11/                                    # Month
    │   │   ├── 2024-11-28_093015_activity.log
    │   │   ├── 2024-11-28_093015_performance.log
    │   │   └── 2024-11-30_141230_activity.log
    │   └── 12/
    │       ├── 2024-12-15_143052_activity.log     # Session log
    │       ├── 2024-12-15_143052_performance.log  # Performance metrics
    │       ├── 2024-12-16_091523_activity.log
    │       └── 2024-12-16_091523_performance.log
    │
    ├── errors/                                    # Rotated error logs
    │   ├── errors_2024-10-15_091234.log.gz        # Rotated & compressed
    │   ├── errors_2024-11-20_143052.log.gz        # Rotated & compressed
    │   └── errors_2024-12-10_082315.log.gz        # Rotated & compressed
    │
    └── errors.log                                 # Active error log
```

**File Naming Conventions:**

```
Activity/Performance logs:
{YYYY}-{MM}-{DD}_{HHMMSS}_{type}.log
Example: 2024-12-15_143052_activity.log

Error logs (rotated by size):
errors_{YYYY}-{MM}-{DD}_{HHMMSS}.log[.gz]
Example: errors_2024-12-15_143052.log.gz
```

### Error Log Rotation

Error logs are automatically rotated when they exceed the size threshold:

```
When errors.log > 10MB:

1. Move to errors/: errors.log → errors/errors_2024-12-15_143052.log
2. Compress: errors/errors_2024-12-15_143052.log → errors/errors_2024-12-15_143052.log.gz
3. Create new: errors.log (empty)

Result:
logs/
├── errors/
│   ├── errors_2024-10-15_091234.log.gz   # Old (deleted after 1 year)
│   ├── errors_2024-11-20_143052.log.gz   # Older rotated
│   ├── errors_2024-12-10_082315.log.gz   # Recent rotated
│   └── errors_2024-12-15_143052.log.gz   # Just rotated
└── errors.log                             # New active log (empty)
```

**Log Types:**

| File | Description | Retention |
|------|-------------|-----------|
| `{date}_{time}_activity.log` | Full session log | Configurable (default 30 days) |
| `{date}_{time}_performance.log` | Timing/metrics data | Configurable (default 30 days) |
| `errors.log` | Active error log | Rotated when > 10MB |
| `errors/errors_{timestamp}.log.gz` | Rotated error logs | Max 50 files, 1 year |

### Cleanup Thresholds

Logs are automatically cleaned up based on configurable thresholds:

```yaml
# In config.yaml
logging:
  level: INFO

  file:
    enabled: true
    directory: logs
    organize_by_date: true
    timestamp_format: "%Y-%m-%d_%H%M%S"

    # =========================================================================
    # CLEANUP THRESHOLDS
    # =========================================================================

    cleanup:
      # When to run cleanup: startup, shutdown, both, manual
      trigger: startup

      # ---------------------------------------------------------------------------
      # Time-based cleanup (delete logs older than X days)
      # ---------------------------------------------------------------------------
      retention_days: 30              # Delete activity/performance logs after 30 days
      retention_days_performance: 14  # Performance logs can have shorter retention

      # ---------------------------------------------------------------------------
      # Size-based cleanup (prevent disk space issues)
      # ---------------------------------------------------------------------------
      max_total_size_mb: 500          # Max total size of all logs
      max_file_size_mb: 50            # Max size per log file
      max_files: 100                  # Max number of log files to keep

      # ---------------------------------------------------------------------------
      # Error log rotation (rotated by size with timestamp)
      # ---------------------------------------------------------------------------
      error_log:
        max_size_mb: 10               # Rotate when current error log exceeds 10MB
        max_files: 50                 # Keep max 50 rotated error log files
        max_age_days: 365             # Delete error logs older than 1 year
        compress_rotated: true        # Compress rotated error logs (.gz)

      # ---------------------------------------------------------------------------
      # Cleanup strategy when thresholds exceeded
      # ---------------------------------------------------------------------------
      strategy: oldest_first          # oldest_first, largest_first, or proportional

      # Keep minimum logs even if thresholds exceeded
      keep_minimum_days: 7            # Always keep at least 7 days of logs

    # Separate error log
    separate_errors: true
    error_file: errors.log

    # Performance log
    performance_log: true
```

### Cleanup Thresholds Summary

| Threshold | Default | Description |
|-----------|---------|-------------|
| `retention_days` | 30 | Delete activity logs older than this |
| `retention_days_performance` | 14 | Delete performance logs older than this |
| `max_total_size_mb` | 500 | Max total size of logs directory |
| `max_file_size_mb` | 50 | Max size per individual log file |
| `max_files` | 100 | Maximum number of log files |
| `keep_minimum_days` | 7 | Always keep at least this many days |
| `error_log.max_size_mb` | 10 | Rotate error log when exceeded |
| `error_log.max_files` | 50 | Max number of rotated error logs |
| `error_log.max_age_days` | 365 | Delete error logs older than this |
| `error_log.compress_rotated` | true | Compress rotated error logs |

### Cleanup Implementation

```python
# src/utils/log_cleanup.py

from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
import gzip
import shutil


@dataclass
class CleanupThresholds:
    """Configurable cleanup thresholds."""
    retention_days: int = 30
    retention_days_performance: int = 14
    max_total_size_mb: int = 500
    max_file_size_mb: int = 50
    max_files: int = 100
    keep_minimum_days: int = 7
    error_max_size_mb: int = 10          # Rotate error log when > 10MB
    error_max_files: int = 50            # Keep max 50 rotated error logs
    error_max_age_days: int = 365
    compress_rotated: bool = True        # Compress rotated error logs
    strategy: str = "oldest_first"


class LogCleaner:
    """
    Automatic log cleanup based on configurable thresholds.
    """

    def __init__(self, logs_dir: Path, thresholds: CleanupThresholds):
        self.logs_dir = logs_dir
        self.thresholds = thresholds
        self.stats = {"deleted": 0, "archived": 0, "freed_mb": 0}

    def cleanup(self) -> dict:
        """
        Run all cleanup operations and return statistics.
        """
        self._cleanup_by_age()
        self._cleanup_by_size()
        self._cleanup_by_count()
        self._handle_error_log()
        self._remove_empty_directories()

        return self.stats

    def _cleanup_by_age(self):
        """Delete logs older than retention threshold."""
        cutoff = datetime.now() - timedelta(days=self.thresholds.retention_days)
        cutoff_perf = datetime.now() - timedelta(
            days=self.thresholds.retention_days_performance
        )
        minimum_cutoff = datetime.now() - timedelta(
            days=self.thresholds.keep_minimum_days
        )

        for log_file in self.logs_dir.rglob("*.log"):
            if log_file.name == "errors.log":
                continue

            file_date = self._parse_date_from_filename(log_file)
            if not file_date:
                continue

            # Determine which cutoff to use
            if "_performance.log" in log_file.name:
                threshold = cutoff_perf
            else:
                threshold = cutoff

            # Never delete if within minimum retention
            if file_date >= minimum_cutoff:
                continue

            if file_date < threshold:
                self._delete_file(log_file)

    def _cleanup_by_size(self):
        """Delete logs if total size exceeds threshold."""
        max_bytes = self.thresholds.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.thresholds.max_file_size_mb * 1024 * 1024

        # First, handle oversized individual files
        for log_file in self.logs_dir.rglob("*.log"):
            if log_file.name == "errors.log":
                continue
            if log_file.stat().st_size > max_file_bytes:
                self._delete_file(log_file)

        # Then, check total size
        total_size = sum(
            f.stat().st_size
            for f in self.logs_dir.rglob("*.log")
            if f.name != "errors.log"
        )

        if total_size > max_bytes:
            self._free_space_by_strategy(total_size - max_bytes)

    def _cleanup_by_count(self):
        """Delete logs if file count exceeds threshold."""
        log_files = sorted(
            [f for f in self.logs_dir.rglob("*.log") if f.name != "errors.log"],
            key=lambda f: f.stat().st_mtime
        )

        while len(log_files) > self.thresholds.max_files:
            oldest = log_files.pop(0)
            self._delete_file(oldest)

    def _handle_error_log(self):
        """Handle error log rotation by size with timestamp."""
        errors_dir = self.logs_dir / "errors"
        errors_dir.mkdir(exist_ok=True)

        current_log = self.logs_dir / "errors.log"
        if not current_log.exists():
            current_log.touch()
            return

        max_bytes = self.thresholds.error_max_size_mb * 1024 * 1024

        # Rotate if current log exceeds size threshold
        if current_log.stat().st_size > max_bytes:
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            rotated_name = f"errors_{timestamp}.log"
            rotated_path = errors_dir / rotated_name

            # Move current log to errors/ directory with timestamp
            shutil.move(current_log, rotated_path)

            # Compress if enabled
            if self.thresholds.compress_rotated:
                with open(rotated_path, 'rb') as f_in:
                    with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                rotated_path.unlink()

            self.stats["archived"] += 1

            # Create new empty error log
            current_log.touch()

        # Cleanup old error logs
        self._cleanup_old_error_logs(errors_dir)

    def _cleanup_old_error_logs(self, errors_dir: Path):
        """Delete old rotated error logs based on age and count."""
        error_files = sorted(
            [f for f in errors_dir.glob("errors_*.log*")
             if f.name != "errors_current.log"],
            key=lambda f: f.stat().st_mtime
        )

        # Delete by age
        cutoff = datetime.now() - timedelta(days=self.thresholds.error_max_age_days)
        for f in error_files[:]:
            try:
                # Parse date from filename: errors_2024-12-15_143052.log
                date_str = f.stem.replace("errors_", "").split(".")[0]
                file_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink()
                    error_files.remove(f)
                    self.stats["deleted"] += 1
            except (ValueError, IndexError):
                pass

        # Delete by count (keep only max_files)
        while len(error_files) > self.thresholds.error_max_files:
            oldest = error_files.pop(0)
            oldest.unlink()
            self.stats["deleted"] += 1

    def _free_space_by_strategy(self, bytes_to_free: int):
        """Free up space using configured strategy."""
        log_files = [
            f for f in self.logs_dir.rglob("*.log")
            if f.name != "errors.log"
        ]

        if self.thresholds.strategy == "oldest_first":
            log_files.sort(key=lambda f: f.stat().st_mtime)
        elif self.thresholds.strategy == "largest_first":
            log_files.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for log_file in log_files:
            if freed >= bytes_to_free:
                break
            freed += log_file.stat().st_size
            self._delete_file(log_file)

    def _delete_file(self, file_path: Path):
        """Delete a file and update stats."""
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_path.unlink()
        self.stats["deleted"] += 1
        self.stats["freed_mb"] += size_mb

    def _parse_date_from_filename(self, file_path: Path) -> datetime | None:
        """Parse date from log filename."""
        try:
            date_str = file_path.stem.split("_")[0]
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, IndexError):
            return None

    def _remove_empty_directories(self):
        """Remove empty year/month directories."""
        for year_dir in self.logs_dir.iterdir():
            if not year_dir.is_dir() or year_dir.name == "archive":
                continue
            for month_dir in year_dir.iterdir():
                if month_dir.is_dir() and not any(month_dir.iterdir()):
                    month_dir.rmdir()
            if year_dir.is_dir() and not any(year_dir.iterdir()):
                year_dir.rmdir()
```

### Cleanup Triggers

```python
# Cleanup runs automatically at configured trigger points

# On startup (before generating report)
if config.logging.file.cleanup.trigger in ("startup", "both"):
    cleaner = LogCleaner(logs_dir, thresholds)
    stats = cleaner.cleanup()
    logger.info(f"Log cleanup: deleted {stats['deleted']} files, "
                f"freed {stats['freed_mb']:.1f}MB")

# On shutdown (after generating report)
if config.logging.file.cleanup.trigger in ("shutdown", "both"):
    cleaner.cleanup()

# Manual cleanup via CLI
# python generate_report.py --cleanup-logs
```

### Cleanup Summary Display

```
┌─────────────────────────────────────────────────────────────────┐
│                       LOG CLEANUP SUMMARY                        │
├─────────────────────────────────────────────────────────────────┤
│  Trigger: startup                                                │
│                                                                  │
│  Actions Taken:                                                  │
│  ├── Deleted by age (>30 days): 12 files                        │
│  ├── Deleted by size (>50MB): 2 files                           │
│  ├── Deleted by count (>100): 0 files                           │
│  └── Error log archived: Yes (was 105MB)                        │
│                                                                  │
│  Space Freed: 234.5 MB                                          │
│  Current Usage: 156.2 MB / 500 MB limit                         │
│  Files Remaining: 45 / 100 limit                                │
└─────────────────────────────────────────────────────────────────┘
```

### Progress Display

For interactive use, a rich progress display:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GitHub Activity Report Generator                                            │
│  User: alhoseany | Period: December 2024 (Monthly)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fetching Data                                                               │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░  Week 3/5  [00:04:23]            │
│                                                                              │
│  ┌─ Current Operation ─────────────────────────────────────────────────┐    │
│  │ Fetching: 2024-12-15 to 2024-12-21                                  │    │
│  │ Status: High activity detected, switching to daily fetch           │    │
│  │ Day: 3/7 (2024-12-17)                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Statistics So Far                                                           │
│  ├── Events fetched: 287                                                    │
│  ├── API calls: 12                                                          │
│  ├── Cache hits: 3                                                          │
│  └── Rate limit: 4,856/5,000                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Debug Mode Features

When running with `-vv` or `-vvv`:

```bash
# Debug mode
python generate_report.py -m 12 -vv

# Trace mode (full data dumps)
python generate_report.py -m 12 -vvv
```

**Debug Mode Extras:**

| Feature | `-vv` (DEBUG) | `-vvv` (TRACE) |
|---------|---------------|----------------|
| API request/response headers | ✓ | ✓ |
| Full API response bodies | ✗ | ✓ |
| Timing for every function | ✓ | ✓ |
| Memory profiling | ✗ | ✓ |
| Cache read/write details | ✓ | ✓ |
| Raw data before processing | ✗ | ✓ |
| SQL-like query explanations | ✓ | ✓ |

### Run Summary

At the end of each run, a summary is logged:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RUN SUMMARY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Status: SUCCESS                                                             │
│  Duration: 2m 34s                                                            │
│                                                                              │
│  Data Collection                                                             │
│  ├── Period: 2024-12-01 to 2024-12-31                                       │
│  ├── Total events: 456                                                      │
│  ├── API calls: 23 (8 cached)                                               │
│  ├── High-activity weeks: 2 (fetched daily)                                 │
│  └── Errors: 0                                                              │
│                                                                              │
│  Performance                                                                 │
│  ├── Fetch time: 1m 45s                                                     │
│  ├── Process time: 12s                                                      │
│  ├── Report generation: 3s                                                  │
│  └── Peak memory: 128MB                                                     │
│                                                                              │
│  Output                                                                      │
│  ├── JSON: reports/2024/2024-12-github-activity-1.json                      │
│  └── Markdown: reports/2024/2024-12-github-activity-1.md                    │
│                                                                              │
│  Rate Limit Status                                                           │
│  └── Remaining: 4,832/5,000 (resets in 42m)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Logger Implementation

```python
# src/utils/logger.py

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any
import json

class StructuredLogger:
    """
    Structured logger with performance tracking and context.
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._setup_handlers()
        self._context = {}
        self._timers = {}

    def set_context(self, **kwargs):
        """Set persistent context for all log entries."""
        self._context.update(kwargs)

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self._timers[operation] = datetime.now()

    def end_timer(self, operation: str, **extra) -> float:
        """End timing and log the duration."""
        if operation in self._timers:
            duration = (datetime.now() - self._timers[operation]).total_seconds()
            self.debug(f"{operation} completed",
                      duration_ms=int(duration * 1000), **extra)
            del self._timers[operation]
            return duration
        return 0

    def api_request(self, method: str, endpoint: str, **params):
        """Log an API request."""
        self.debug("API Request",
                  method=method,
                  endpoint=endpoint,
                  params=params)

    def api_response(self, status: int, duration_ms: int,
                     items: int = 0, rate_limit: dict = None):
        """Log an API response with rate limit info."""
        self.debug("API Response",
                  status=status,
                  duration_ms=duration_ms,
                  items=items,
                  rate_limit=rate_limit)

        # Warn if rate limit is getting low
        if rate_limit and rate_limit.get('remaining', 5000) < 1000:
            self.warning("Rate limit low",
                        remaining=rate_limit['remaining'],
                        resets_in=rate_limit.get('reset_in'))

    def error_with_context(self, msg: str, error: Exception,
                           recovery: str = None, **context):
        """Log an error with full context for debugging."""
        self.error(msg,
                  error_type=type(error).__name__,
                  error_msg=str(error),
                  recovery=recovery,
                  **{**self._context, **context})
```

### Config for Logging

```yaml
# In config.yaml - logging section
logging:
  # Console output level (ERROR, WARNING, INFO, DEBUG, TRACE)
  level: INFO

  # Colorized console output
  colorize: true

  # Show timestamps in console
  show_timestamps: true

  # Progress bar style: rich, simple, none
  progress_style: rich

  # File logging
  file:
    enabled: true
    directory: logs

    # JSON lines format for parsing
    format: jsonl

    # Rotation settings
    max_size_mb: 10
    backup_count: 5

    # Separate error log
    separate_errors: true
    error_file: errors.log

    # Performance metrics log
    performance_log: true
    performance_file: performance.log

  # What to include in logs
  include:
    timestamps: true
    module_name: true
    line_numbers: false  # true in DEBUG mode
    stack_traces: false  # true on errors, full in TRACE mode

  # Performance logging
  performance:
    log_api_calls: true
    log_timing: true
    log_memory: false  # true in TRACE mode
    slow_threshold_ms: 1000  # warn if operation > 1s
```

---

## Configuration Options

### Environment Variables

```bash
# Optional: Override default username
GITHUB_ACTIVITY_USER=alhoseany

# Optional: Cache directory
GITHUB_ACTIVITY_CACHE_DIR=/tmp/gh-activity-cache

# Optional: Log level
GITHUB_ACTIVITY_LOG_LEVEL=INFO
```

### CLI Arguments

```bash
# Run with all defaults (current month, current year, logged-in user)
python generate_report.py

# Current quarter report
python generate_report.py -q

# Specific month (defaults to current year)
python generate_report.py -m 6

# Specific quarter and year
python generate_report.py -q 4 -y 2024

# Full example with all options
python generate_report.py \
    -m 12 \
    -y 2024 \
    -u USERNAME \
    -o PATH \
    -f both \
    --include-repos "owner/repo1,owner/repo2" \
    --exclude-repos "owner/fork1" \
    --no-cache \
    --log-level DEBUG
```

**Smart Defaults:**

| Option | Default Value | Source |
|--------|---------------|--------|
| User | Logged-in gh user | `gh api /user --jq .login` |
| Year | Current year | `datetime.now().year` |
| Month | Current month | `datetime.now().month` |
| Quarter | Current quarter | Derived from current month |
| Format | both | JSON + Markdown |

**Available Options:**

| Short | Long | Description | Default |
|-------|------|-------------|---------|
| `-m` | `--month` | Monthly report (1-12) | Current month |
| `-q` | `--quarter` | Quarterly report (1-4) | Current quarter |
| `-y` | `--year` | Report year | Current year |
| `-u` | `--user` | GitHub username | Logged-in user |
| `-c` | `--config` | Path to config file | config.yaml |
| `-o` | `--output-dir` | Custom output path | ./reports |
| `-f` | `--format` | Output format (json/markdown/both) | both |
| | `--include-repos` | Comma-separated repos to include | All |
| | `--exclude-repos` | Comma-separated repos to exclude | None |
| | `--no-cache` | Disable caching | false |
| | `--log-level` | Log level (DEBUG/INFO/WARNING/ERROR) | INFO |
| | `--dry-run` | Show what would be fetched | false |
| `-h` | `--help` | Show help | - |

**Period Behavior:**
- No flags → Monthly report for current month
- `-q` alone → Quarterly report for current quarter
- `-q 2` → Quarterly report for Q2
- `-m` alone → Monthly report for current month (same as no flags)
- `-m 6` → Monthly report for June

**Note:** `-m/--month` and `-q/--quarter` are mutually exclusive.

### Configuration File

The script uses a `config.yaml` file for all configurable settings. CLI arguments override config file values.

**Location:** `.scripts/github-activity/config.yaml`

```yaml
# =============================================================================
# GitHub Activity Report Generator - Configuration
# =============================================================================
# All settings can be overridden via CLI arguments or environment variables.
# CLI args > Environment vars > Config file > Defaults
# =============================================================================

# -----------------------------------------------------------------------------
# User Settings
# -----------------------------------------------------------------------------
user:
  # GitHub username (default: auto-detected from gh CLI)
  # Override: -u/--user or GITHUB_ACTIVITY_USER env var
  username: null  # null = use logged-in gh user

  # Organizations to include (default: all accessible)
  # Override: -o/--orgs
  organizations: []  # empty = all orgs

# -----------------------------------------------------------------------------
# Repository Filters
# -----------------------------------------------------------------------------
repositories:
  # Include private repositories
  include_private: true

  # Include forked repositories
  include_forks: false

  # Exclude specific repositories (full name: owner/repo)
  exclude:
    - owner/repo-to-skip

# -----------------------------------------------------------------------------
# Fetching Settings
# -----------------------------------------------------------------------------
fetching:
  # Threshold for switching from weekly to daily fetching
  # If a week returns >= this many events, re-fetch day by day
  high_activity_threshold: 100

  # Pause between API requests (seconds)
  request_delay: 1.0

  # Maximum retries on failure
  max_retries: 3

  # Exponential backoff base (seconds)
  backoff_base: 2.0

  # Request timeout (seconds)
  timeout: 30

# -----------------------------------------------------------------------------
# Caching Settings
# -----------------------------------------------------------------------------
cache:
  # Enable response caching
  enabled: true

  # Cache directory (relative to script or absolute path)
  directory: .cache

  # Cache time-to-live (hours)
  ttl_hours: 24

# -----------------------------------------------------------------------------
# Output Settings
# -----------------------------------------------------------------------------
output:
  # Output directory for reports (relative to script or absolute path)
  directory: reports

  # Output formats: json, markdown, or both
  formats:
    - json
    - markdown

  # Include GitHub links in markdown report
  include_links: true

  # Commit message format: full, first_line, or truncated (100 chars)
  commit_message_format: first_line

# -----------------------------------------------------------------------------
# Metrics Settings
# -----------------------------------------------------------------------------
metrics:
  # Calculate PR metrics (time to merge, commits per PR, etc.)
  pr_metrics: true

  # Calculate review metrics (turnaround time, approval rate)
  review_metrics: true

  # Calculate engagement metrics (response time, collaboration score)
  engagement_metrics: true

  # Calculate productivity patterns (by day of week, by hour)
  productivity_patterns: true

  # Include reaction emoji breakdown
  reaction_breakdown: true

# -----------------------------------------------------------------------------
# Report Content Settings
# -----------------------------------------------------------------------------
report:
  # Include detailed commit list
  include_commits: true

  # Include detailed PR list
  include_pull_requests: true

  # Include detailed issue list
  include_issues: true

  # Include detailed review list
  include_reviews: true

  # Include comment list
  include_comments: true

  # Maximum items per category in markdown report (0 = unlimited)
  max_items_per_category: 50

# -----------------------------------------------------------------------------
# Logging Settings
# -----------------------------------------------------------------------------
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, TRACE
  level: INFO

  # Colorized console output
  colorize: true

  # Show timestamps in console
  show_timestamps: true

  # Progress bar style: rich, simple, none
  progress_style: rich

  # File logging
  file:
    enabled: true
    directory: logs
    organize_by_date: true
    timestamp_format: "%Y-%m-%d_%H%M%S"

    # JSON lines format for parsing
    format: jsonl

    # Cleanup thresholds
    cleanup:
      trigger: startup                    # startup, shutdown, both, manual
      retention_days: 30                  # Delete activity logs after 30 days
      retention_days_performance: 14      # Performance logs shorter retention
      max_total_size_mb: 500              # Max total size of all logs
      max_file_size_mb: 50                # Max size per log file
      max_files: 100                      # Max number of log files
      keep_minimum_days: 7                # Always keep at least 7 days
      strategy: oldest_first              # oldest_first, largest_first

      # Error log rotation (by size with timestamp)
      error_log:
        max_size_mb: 10                   # Rotate when > 10MB
        max_files: 50                     # Keep max 50 rotated files
        max_age_days: 365                 # Delete error logs older than 1 year
        compress_rotated: true            # Compress rotated logs (.gz)

    # Separate error log
    separate_errors: true
    error_file: errors.log

    # Performance metrics log
    performance_log: true

  # What to include in logs
  include:
    timestamps: true
    module_name: true
    line_numbers: false                   # true in DEBUG mode
    stack_traces: false                   # true on errors

  # Performance logging
  performance:
    log_api_calls: true
    log_timing: true
    log_memory: false                     # true in TRACE mode
    slow_threshold_ms: 1000               # warn if operation > 1s

# -----------------------------------------------------------------------------
# Output Cleanup Settings
# -----------------------------------------------------------------------------
output_cleanup:
  # Enable automatic cleanup
  enabled: true

  # When to run cleanup: startup, shutdown, both, manual
  trigger: startup

  # Time-based cleanup
  retention_years: 2                      # Keep reports for 2 years

  # Version-based cleanup (multiple regenerations of same period)
  keep_versions: 3                        # Keep last 3 versions per period

  # Size-based cleanup
  max_total_size_mb: 1000                 # Max total size of all reports
  max_file_size_mb: 100                   # Max size per report file

  # Count-based cleanup
  max_reports: 500                        # Max number of report files

  # Archive settings (instead of delete)
  archive:
    enabled: true                         # Archive old reports instead of delete
    directory: reports/archive            # Archive location
    compress: true                        # Compress archived reports (.gz)
    archive_after_days: 365               # Archive reports older than 1 year

  # Cleanup strategy
  strategy: oldest_first                  # oldest_first, largest_first

  # Safety: always keep minimum reports
  keep_minimum_months: 6                  # Always keep at least 6 months

# -----------------------------------------------------------------------------
# Advanced Settings
# -----------------------------------------------------------------------------
advanced:
  # JSON schema version for validation
  schema_version: "1.0"

  # Timezone for date calculations (null = local timezone)
  timezone: null

  # Include draft PRs in statistics
  include_draft_prs: true

  # Track PRs where user is author vs reviewer separately
  separate_author_reviewer_stats: true
```

### Config Loading Priority

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION PRIORITY                        │
│                      (highest to lowest)                         │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  CLI Arguments  │  ◄── Highest priority
    │  -m 12 -y 2024  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Environment    │
    │  Variables      │
    │  GITHUB_ACTIVITY│
    │  _USER=...      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  config.yaml    │
    │  (this file)    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Built-in       │  ◄── Lowest priority
    │  Defaults       │
    └─────────────────┘
```

### Environment Variable Mapping

| Config Path | Environment Variable |
|-------------|---------------------|
| `user.username` | `GITHUB_ACTIVITY_USER` |
| `cache.directory` | `GITHUB_ACTIVITY_CACHE_DIR` |
| `output.directory` | `GITHUB_ACTIVITY_OUTPUT_DIR` |
| `logging.level` | `GITHUB_ACTIVITY_LOG_LEVEL` |
| `logging.file.directory` | `GITHUB_ACTIVITY_LOG_DIR` |
| `fetching.high_activity_threshold` | `GITHUB_ACTIVITY_HIGH_THRESHOLD` |

---

## Summary

This plan provides a comprehensive blueprint for building a GitHub Activity Report Generator with the following characteristics:

| Aspect | Decision |
|--------|----------|
| **Report Periods** | Monthly (`--month 1-12`) or Quarterly (`--quarter 1-4`) |
| **Primary Data Source** | Events API + Search APIs |
| **Output Formats** | JSON (validated) + Markdown |
| **Architecture** | Modular with fetchers, processors, reporters |
| **Portability** | No hardcoded paths, relative paths from script |
| **Extensibility** | Plugin-style fetchers, configurable metrics |
| **Error Handling** | Graceful degradation with retries and caching |

The implementation is divided into 6 phases, estimated for incremental delivery. Each module is designed to be independently testable and maintainable.

### Quick Reference - File Naming

Reports are organized by year and username:

```
reports/
  {year}/
    {username}/
      {year}-{MM}-github-activity-{n}.md      # Monthly
      {year}-Q{Q}-github-activity-{n}.md      # Quarterly
```

| Period Type | CLI Flag | File Pattern | Example |
|-------------|----------|--------------|---------|
| Monthly | `--month 12` | `reports/{year}/{user}/{year}-{MM}-github-activity-{n}.md` | `reports/2024/octocat/2024-12-github-activity-1.md` |
| Quarterly | `--quarter 4` | `reports/{year}/{user}/{year}-Q{Q}-github-activity-{n}.md` | `reports/2024/octocat/2024-Q4-github-activity-1.md` |

---

*Document Version: 1.1*
*Last Updated: 2026-01-04*
*Status: Implementation Complete*
