# GitHub Activity Report Generator

A Python CLI tool that generates monthly or quarterly GitHub activity reports using the local `gh` CLI. Outputs comprehensive reports in JSON and Markdown formats.

## Features

- **Flexible period selection**: Monthly or quarterly reports
- **Activity tracking**: Commits, PRs, issues, reviews, comments
- **Advanced metrics**: PR approval times, commits per PR, review turnaround, productivity patterns
- **Repository filtering**: Whitelist/blacklist with glob patterns
- **Caching**: Configurable TTL to avoid redundant API calls
- **Multiple output formats**: JSON (schema-validated) and Markdown

## Requirements

- Python 3.9+
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd github-activity

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Generate report for current month
python generate_report.py

# Monthly report for specific month
python generate_report.py -m 6 -y 2024

# Quarterly report
python generate_report.py -q 4 -y 2024

# For specific user
python generate_report.py -u octocat

# Filter to specific repositories
python generate_report.py --include-repos "owner/repo1,owner/repo2"

# Exclude repositories
python generate_report.py --exclude-repos "owner/fork1"

# Output only JSON
python generate_report.py -f json

# Dry run (show what would be fetched)
python generate_report.py --dry-run

# Skip cache (fetch fresh data)
python generate_report.py --no-cache
```

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
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

## Configuration

Configuration uses priority: CLI > Environment Variables > config.yaml > Defaults

### Environment Variables

- `GITHUB_ACTIVITY_USER` - Override username
- `GITHUB_ACTIVITY_OUTPUT_DIR` - Override output directory
- `GITHUB_ACTIVITY_LOG_LEVEL` - Override log level
- `GITHUB_ACTIVITY_CACHE_DIR` - Override cache directory

### config.yaml

See `config.yaml` for all available options including:
- Repository filters (private, forks, whitelist/blacklist)
- Fetching settings (rate limiting, timeouts)
- Cache settings (TTL, directory)
- Output settings (formats, links, commit message format)
- Metrics toggles (PR, review, engagement, productivity)
- Logging and cleanup settings

## Output

Reports are saved to:
- Monthly: `reports/{year}/{username}/{year}-{MM}-github-activity-{n}.{json,md}`
- Quarterly: `reports/{year}/{username}/{year}-Q{Q}-github-activity-{n}.{json,md}`

Example: `reports/2024/octocat/2024-06-github-activity-1.json`

Multiple runs for the same period create incremented versions (-1, -2, -3).

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_metrics.py -v
```

## License

MIT
