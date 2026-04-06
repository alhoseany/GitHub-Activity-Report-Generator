# 📊 GitHub Activity Report Generator

> *Because your quarterly review deserves more than "I did stuff"* 💪

A Python CLI tool that transforms your GitHub activity into beautiful, comprehensive reports. Perfect for performance reviews, personal tracking, or just flexing your contribution muscles.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📅 **Flexible Periods** | Monthly or quarterly reports — you choose |
| 🔍 **Activity Tracking** | Commits, PRs, issues, reviews, comments — the whole shebang |
| 📈 **Advanced Metrics** | PR approval times, commits per PR, review turnaround, productivity patterns |
| 🎯 **Repository Filtering** | Whitelist/blacklist with glob patterns — focus on what matters |
| ⚡ **Smart Caching** | Configurable TTL to keep things speedy |
| 📝 **Multiple Formats** | JSON (schema-validated) + Markdown — take your pick |
| 🚀 **Release Contributions** | Track your impact on releases — commits authored + PRs reviewed |
| ✅ **Report Verification** | Spot-check report data against live GitHub API |

## 🛠️ Requirements

- 🐍 Python 3.9+
- 🖥️ [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

## 🚀 Quick Start

```bash
# Clone it
git clone https://github.com/alhoseany/GitHub-Activity-Report-Generator.git
cd GitHub-Activity-Report-Generator

# Install dependencies
pip install -r requirements.txt

# Generate your first report 🎉
python generate_report.py
```

## 💻 Usage

```bash
# Current month — just run it!
python generate_report.py

# Specific month
python generate_report.py -m 6 -y 2024

# Quarterly report (Q4 crunch time? 😅)
python generate_report.py -q 4 -y 2024

# Different user
python generate_report.py -u octocat

# Only specific repos
python generate_report.py --include-repos "owner/repo1,owner/repo2"

# Skip the forks
python generate_report.py --exclude-repos "owner/fork1"

# JSON only (for the data nerds 🤓)
python generate_report.py -f json

# Dry run — see what you'd get
python generate_report.py --dry-run

# Fresh data, no cache
python generate_report.py --no-cache
```

## 🎛️ CLI Options

| Option | Short | What it does |
|--------|-------|--------------|
| `--month` | `-m` | Month (1-12) for monthly report |
| `--quarter` | `-q` | Quarter (1-4) for quarterly report |
| `--year` | `-y` | Year (default: current year) |
| `--user` | `-u` | GitHub username (default: logged-in user) |
| `--format` | `-f` | Output format: json, markdown, both |
| `--output-dir` | `-o` | Output directory (default: reports/) |
| `--include-repos` | | Comma-separated repos to include |
| `--exclude-repos` | | Comma-separated repos to exclude |
| `--no-cache` | | Disable caching |
| `--log-level` | | DEBUG, INFO, WARNING, ERROR |
| `--config` | `-c` | Path to config file |
| `--dry-run` | | Show what would be fetched |
| `--verify` | | Verify report data against GitHub API |

## ⚙️ Configuration

**Priority order:** CLI > Environment Variables > config.yaml > Defaults

### 🌍 Environment Variables

```bash
GITHUB_ACTIVITY_USER        # Override username
GITHUB_ACTIVITY_OUTPUT_DIR  # Override output directory
GITHUB_ACTIVITY_LOG_LEVEL   # Override log level
GITHUB_ACTIVITY_CACHE_DIR   # Override cache directory
```

### 📄 config.yaml

Customize everything in `config.yaml`:
- 🏷️ Repository filters (private, forks, whitelist/blacklist)
- ⏱️ Fetching settings (rate limiting, timeouts)
- 💾 Cache settings (TTL, directory)
- 📤 Output settings (formats, links, commit message format)
- 📊 Metrics toggles (PR, review, engagement, productivity)
- 🧹 Logging and cleanup settings

## 📁 Output

Reports land in organized directories:

```
reports/
└── 2024/
    └── octocat/
        ├── 2024-06-github-activity-1.json
        ├── 2024-06-github-activity-1.md
        └── 2024-Q2-github-activity-1.md   # Quarterly
```

Run multiple times? No problem — versions auto-increment (`-1`, `-2`, `-3`).

## 🚀 Release Contributions

Track your impact on releases across repositories. The tool automatically detects releases using the GitHub Releases API (with a tags fallback for repos without formal releases) and calculates your contribution weight based on commits authored and PRs reviewed.

```bash
# Reports include release contributions by default
python generate_report.py -q 1 -y 2026

# Example output in the Markdown report:
# ## Release Contributions
# | Release | Repository | Commits (User/Total) | Reviews (User/Total PRs) | Weight |
# |---------|-----------|---------------------|------------------------|--------|
# | 3.6.6   | org/repo  | 15/163              | 11/19                  | 28.6%  |
```

**Features:**
- Tiered detection: GitHub Releases API → Tags API fallback
- Monorepo support: auto-detects scoped tags (e.g., `plugin-name/1.0.0`)
- Anomaly detection: flags huge (500+ commits), empty, or rapid releases
- Contribution weight: 60% commit share + 40% review share
- Configurable: disable with `release_metrics: false` in config.yaml

## ✅ Report Verification

Verify your report data against the live GitHub API after generation:

```bash
python generate_report.py -m 3 -y 2026 --verify
```

The verifier spot-checks:
- Internal consistency (summary counts match activity data)
- Comment uniqueness (no duplicates)
- Commit SHAs exist on GitHub
- PR and issue states match GitHub
- Review states match GitHub
- Release data matches GitHub

```
Verification: PASSED
  ✓ internal_consistency: 12/12
  ✓ comment_uniqueness: 93/93
  ✓ commit_spot_check: 5/5
  ✓ pr_state_verification: 3/3
  ✓ review_spot_check: 5/5
  ✓ issue_state_verification: 4/4
  ✓ release_spot_check: 5/5
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing

# Specific test file
pytest tests/unit/test_metrics.py -v
```

## 🏗️ Built With

This project was created using **spec-driven development** — a detailed plan was created first, then implemented methodically. Check out the `docs/` folder to see how it all came together:

- 📋 `PROJECT.md` — Original requirements
- 🧠 `MEMORY.md` — Project context for AI sessions
- 📐 `plan-v2.md` — Full specifications
- ✅ `tasks.md` — Implementation tracking

## 📋 Changelog

### v2.0.0 (2026-04-06)

**New Features:**
- 🚀 **Release Contribution Tracking** — Detects releases across repos, calculates contribution weight from commits + reviews, supports monorepos and tags-only repos
- ✅ **Post-Generation Verification** (`--verify`) — Spot-checks report data against live GitHub API
- 🔗 **Review PR Links** — Reviews in Markdown reports now link to the PR on GitHub

**Bug Fixes:**
- Fixed comment deduplication — prevented cross-source duplicates between events API and direct API
- Fixed missing merged PRs — now catches PRs created before the period but merged within it
- Fixed missing reviews — now captures reviews on PRs created before the reporting period
- Fixed missing issues — now captures issues closed/updated in period but created before it
- Fixed PR review count — dedup now uses (repo, pr_number) instead of pr_number alone

**Tests:**
- 281 tests (up from 213), all passing
- New test suites for release fetcher and report verifier

### v1.0.0 (2026-01-04)
- Initial release with full pipeline: fetchers, aggregator, metrics, reporters
- Monthly and quarterly reports in JSON + Markdown
- Adaptive fetching, caching, repository filtering, cleanup

## 📜 License

MIT — Go wild! 🎉

---

<p align="center">
  <i>Now go show off those contribution stats!</i> 💪📊
</p>
