#!/usr/bin/env python3
# =============================================================================
# FILE: generate_report.py
# TASKS: UC-2.1, UC-3.1, UC-4.1, UC-5.1, UC-6.1, UC-8.1, UC-9.1
# PLAN: Section 3.1, 3.2, 3.3, 3.5, 3.6, 3.8
# =============================================================================
"""
GitHub Activity Report Generator - CLI Entry Point.

This module provides the command-line interface for generating GitHub activity
reports.

Usage:
    ./generate_report.py --help
    ./generate_report.py -m 6          # Monthly report for June
    ./generate_report.py -q 2          # Quarterly report for Q2
    ./generate_report.py -u username   # Report for specific user
    ./generate_report.py --dry-run     # Show what would be fetched

Period Selection (UC-3.1 | PLAN-3.1):
    --month/-m: Monthly report (1-12)
    --quarter/-q: Quarterly report (1-4)
    --year/-y: Year (defaults to current year)
    Note: --month and --quarter are mutually exclusive

User Configuration (UC-4.1 | PLAN-3.2):
    --user/-u: GitHub username (overrides config and env)
    Environment: GITHUB_ACTIVITY_USER
    Config: user.username in config.yaml

Repository Filters (UC-5.1 | PLAN-3.3):
    --include-repos: Comma-separated list of repos to include (whitelist)
    --exclude-repos: Comma-separated list of repos to exclude (blacklist)

Output Settings (UC-6.1 | PLAN-3.6):
    --output-dir/-o: Output directory for reports
    --format/-f: Output format (json/markdown/both)

Caching (UC-8.1 | PLAN-3.5):
    --no-cache: Disable caching (fetch fresh data)

Logging (UC-9.1 | PLAN-3.8):
    --log-level: Set log level (DEBUG/INFO/WARNING/ERROR)
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import ReportOrchestrator
from src.utils.date_utils import get_current_month, get_current_quarter, get_current_year
from src.utils.repo_filter import parse_repo_list


class MutuallyExclusiveOption(click.Option):  # UC-3.1 | PLAN-3.1
    """
    Custom option class for mutually exclusive options.

    Used to enforce that --month and --quarter cannot be used together.
    """

    def __init__(self, *args, not_required_if: list[str] | None = None, **kwargs):
        self.not_required_if = not_required_if or []
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts and opts[self.name] is not None

        for other_param in self.not_required_if:
            if other_param in opts and opts[other_param] is not None:
                if current_opt:
                    raise click.UsageError(
                        f"Cannot use --{self.name.replace('_', '-')} with "
                        f"--{other_param.replace('_', '-')}"
                    )

        return super().handle_parse_result(ctx, opts, args)


@click.command()  # UC-2.1 | PLAN-3.1
@click.option(
    "--user", "-u",
    type=str,
    default=None,
    help="GitHub username (defaults to logged-in user from gh CLI)"  # UC-4.1 | PLAN-3.2
)
@click.option(
    "--month", "-m",
    type=click.IntRange(1, 12),
    default=None,
    cls=MutuallyExclusiveOption,
    not_required_if=["quarter"],
    help="Month (1-12) for monthly report"  # UC-3.1 | PLAN-3.1
)
@click.option(
    "--quarter", "-q",
    type=click.IntRange(1, 4),
    default=None,
    cls=MutuallyExclusiveOption,
    not_required_if=["month"],
    help="Quarter (1-4) for quarterly report"  # UC-3.1 | PLAN-3.1
)
@click.option(
    "--year", "-y",
    type=int,
    default=None,
    help=f"Year (defaults to current: {get_current_year()})"  # UC-3.1 | PLAN-3.1
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=False),
    default="config.yaml",
    help="Path to config file (default: config.yaml)"
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default=None,
    help="Output directory for reports (default: from config)"  # UC-6.1 | PLAN-3.6
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(["json", "markdown", "both"]),
    default=None,
    help="Output format (default: from config)"  # UC-6.1 | PLAN-3.6
)
@click.option(
    "--include-repos",
    type=str,
    default=None,
    help="Comma-separated list of repos to include (e.g., owner/repo1,owner/repo2)"  # UC-5.1 | PLAN-3.3
)
@click.option(
    "--exclude-repos",
    type=str,
    default=None,
    help="Comma-separated list of repos to exclude"  # UC-5.1 | PLAN-3.3
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching (fetch fresh data)"  # UC-8.1 | PLAN-3.5
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default=None,
    help="Log level (default: from config)"  # UC-9.1 | PLAN-3.8
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be fetched without actually fetching"
)
def main(
    user: str | None,
    month: int | None,
    quarter: int | None,
    year: int | None,
    config: str,
    output_dir: str | None,
    output_format: str | None,
    include_repos: str | None,
    exclude_repos: str | None,
    no_cache: bool,
    log_level: str | None,
    dry_run: bool,
) -> None:  # UC-2.1, UC-3.1, UC-4.1, UC-5.1, UC-6.1, UC-8.1, UC-9.1 | PLAN-3.1
    """
    Generate GitHub activity report for a user.

    Fetches activity data from GitHub and generates reports in JSON and/or
    Markdown format for monthly or quarterly periods.

    Period Selection (UC-3.1):
    - Use -m/--month for monthly reports (1-12)
    - Use -q/--quarter for quarterly reports (1-4)
    - Use -y/--year to specify year (default: current year)
    - If neither -m nor -q specified, defaults to current month

    Output Settings (UC-6.1):
    - Use -o/--output-dir to specify output directory
    - Use -f/--format to choose json, markdown, or both

    Caching (UC-8.1):
    - Use --no-cache to disable caching and fetch fresh data

    Logging (UC-9.1):
    - Use --log-level to set log verbosity (DEBUG/INFO/WARNING/ERROR)

    Examples:

        # Generate report for current month
        ./generate_report.py

        # Generate report for specific month
        ./generate_report.py -m 6 -y 2024

        # Generate quarterly report
        ./generate_report.py -q 4 -y 2024

        # Generate for specific user
        ./generate_report.py -u octocat -m 12

        # Output only JSON to custom directory
        ./generate_report.py -f json -o ~/my-reports

        # Filter to specific repos
        ./generate_report.py --include-repos "owner/repo1,owner/repo2"

        # Exclude certain repos
        ./generate_report.py --exclude-repos "owner/fork1,owner/fork2"

        # Force fresh data (no cache)
        ./generate_report.py --no-cache

        # Dry run to see what would be fetched
        ./generate_report.py --dry-run -m 6

        # Enable debug logging
        ./generate_report.py --log-level DEBUG
    """
    # Determine period type and value  # UC-3.1 | PLAN-3.1
    if month is not None:
        period_type = "monthly"
        period_value = month
    elif quarter is not None:
        period_type = "quarterly"
        period_value = quarter
    else:
        # Default to current month if neither specified
        period_type = "monthly"
        period_value = get_current_month()

    # Determine output formats  # UC-6.1 | PLAN-3.6
    if output_format == "both":
        output_formats = ["json", "markdown"]
    elif output_format:
        output_formats = [output_format]
    else:
        output_formats = None  # Use config default

    # Create and run orchestrator
    orchestrator = ReportOrchestrator(config_path=config)

    # Apply CLI overrides to settings  # UC-5.1 | PLAN-3.3
    if include_repos:
        repos = parse_repo_list(include_repos)
        orchestrator.settings.repositories.include = repos

    if exclude_repos:
        repos = parse_repo_list(exclude_repos)
        orchestrator.settings.repositories.exclude = repos

    # UC-9.1 | PLAN-3.8 - Apply log level override
    if log_level:
        orchestrator.settings.logging.level = log_level

    # Apply output directory override  # UC-6.1 | PLAN-3.6
    if output_dir:
        orchestrator.settings.output.directory = output_dir

    # Run the pipeline  # UC-8.1 | PLAN-3.5 - no_cache flag
    result = orchestrator.run(
        username=user,  # UC-4.1 - CLI overrides config/env
        period_type=period_type,  # UC-3.1 | PLAN-3.1
        period_value=period_value,  # UC-3.1 | PLAN-3.1
        year=year,  # UC-3.1 | PLAN-3.1
        output_formats=output_formats,  # UC-6.1 | PLAN-3.6
        output_dir=output_dir,  # UC-6.1 | PLAN-3.6
        dry_run=dry_run,
        no_cache=no_cache,  # UC-8.1 | PLAN-3.5
    )

    # Output results
    if result["success"]:
        if dry_run:
            click.echo("Dry run - would fetch:")
            for key, value in result.get("would_fetch", {}).items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo("Report generation complete!")
            click.echo(f"Files generated: {len(result['files'])}")
            for file_path in result["files"]:
                click.echo(f"  - {file_path}")

            # Show summary
            summary = result.get("summary", {})
            if summary:
                click.echo("\nSummary:")
                click.echo(f"  Commits: {summary.get('total_commits', 0)}")
                click.echo(f"  PRs Opened: {summary.get('total_prs_opened', 0)}")
                click.echo(f"  PRs Merged: {summary.get('total_prs_merged', 0)}")
                click.echo(f"  Issues: {summary.get('total_issues_opened', 0)}")
                click.echo(f"  Reviews: {summary.get('total_prs_reviewed', 0)}")

        sys.exit(0)
    else:
        click.echo("Report generation failed!", err=True)
        for error in result.get("errors", []):
            click.echo(f"  Error: {error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
