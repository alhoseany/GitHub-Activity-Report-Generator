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

## 📜 License

MIT — Go wild! 🎉

---

<p align="center">
  <i>Now go show off those contribution stats!</i> 💪📊
</p>
