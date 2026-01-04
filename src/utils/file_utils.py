# =============================================================================
# FILE: src/utils/file_utils.py
# TASKS: UC-2.4
# PLAN: Section 3.6
# =============================================================================
"""
File Operation Utilities.

This module provides file operation helpers:

Functions:
- ensure_dir(): Ensure directory exists
- get_next_version(): Get next version number for a file pattern
- safe_write(): Safely write content to file
- get_next_filename(): Get next available filename with increment

Directory structure:
reports/
  {year}/
    {username}/
      {year}-{MM}-github-activity-{n}.md
      {year}-{MM}-github-activity-{n}.json
      {year}-Q{Q}-github-activity-{n}.md
      {year}-Q{Q}-github-activity-{n}.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Any


def ensure_dir(dir_path: Path | str) -> Path:  # UC-2.4 | PLAN-3.6
    """
    Ensure directory exists, creating if necessary.

    Args:
        dir_path: Path to directory

    Returns:
        Path: The directory path
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_next_version(
    base_dir: Path,
    prefix: str,
    extension: str
) -> int:  # UC-2.4 | PLAN-3.6
    """
    Get next version number for a file pattern.

    Args:
        base_dir: Directory to search in
        prefix: File prefix (e.g., "2024-12-github-activity")
        extension: File extension (e.g., "md" or "json")

    Returns:
        int: Next version number (1 if no existing files)
    """
    pattern = f"{prefix}-*.{extension}"
    existing = sorted(base_dir.glob(pattern))

    if not existing:
        return 1

    # Extract last number and increment
    last_file = existing[-1]
    try:
        last_num = int(last_file.stem.split("-")[-1])
        return last_num + 1
    except (ValueError, IndexError):
        return 1


def get_next_filename(
    base_dir: Path | str,
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int,
    extension: str = "md",
    username: str | None = None
) -> Path:  # UC-2.4 | PLAN-3.6
    """
    Get next available filename, incrementing if exists.

    Monthly pattern: {year}-{month:02d}-github-activity-{n}.{ext}
    Quarterly pattern: {year}-Q{quarter}-github-activity-{n}.{ext}

    Directory structure:
    - With username: reports/{year}/{username}/...
    - Without username: reports/{year}/...

    Args:
        base_dir: Base reports directory
        year: Report year
        period_type: "monthly" or "quarterly"
        period_value: Month (1-12) or quarter (1-4)
        extension: File extension (default: "md")
        username: GitHub username for subdirectory (optional)

    Returns:
        Path: Full path to next available filename
    """
    base_dir = Path(base_dir)

    # Build output directory: reports/{year}/{username}/ or reports/{year}/
    if username:
        output_dir = base_dir / str(year) / username
    else:
        output_dir = base_dir / str(year)
    ensure_dir(output_dir)

    # Build prefix
    if period_type == "monthly":
        prefix = f"{year}-{period_value:02d}-github-activity"
    else:
        prefix = f"{year}-Q{period_value}-github-activity"

    # Get next version
    version = get_next_version(output_dir, prefix, extension)

    return output_dir / f"{prefix}-{version}.{extension}"


def safe_write(
    file_path: Path | str,
    content: str | dict[str, Any],
    encoding: str = "utf-8"
) -> Path:  # UC-2.4 | PLAN-3.6
    """
    Safely write content to file.

    Creates parent directories if needed.
    Handles both string content and JSON dictionaries.

    Args:
        file_path: Path to write to
        content: String content or dictionary (will be JSON serialized)
        encoding: File encoding (default: utf-8)

    Returns:
        Path: The written file path
    """
    path = Path(file_path)
    ensure_dir(path.parent)

    if isinstance(content, dict):
        with open(path, "w", encoding=encoding) as f:
            json.dump(content, f, indent=2, default=str, ensure_ascii=False)
    else:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)

    return path


def write_report(
    file_path: Path | str,
    content: str | dict[str, Any]
) -> None:  # UC-2.4 | PLAN-3.6
    """
    Write report to file (JSON or text).

    Creates parent directories if needed.

    Args:
        file_path: Path to write to
        content: String content or dictionary
    """
    safe_write(file_path, content)


def read_json_file(file_path: Path | str) -> dict[str, Any] | None:  # UC-2.4 | PLAN-3.6
    """
    Read and parse JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        dict | None: Parsed JSON or None if file doesn't exist/invalid
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_file_size_mb(file_path: Path | str) -> float:  # UC-2.4 | PLAN-3.6
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        float: File size in MB, or 0 if file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)


def list_reports(
    base_dir: Path | str,
    year: int | None = None,
    period_type: Literal["monthly", "quarterly"] | None = None,
    extension: str | None = None
) -> list[Path]:  # UC-2.4 | PLAN-3.6
    """
    List report files matching criteria.

    Args:
        base_dir: Base reports directory
        year: Filter by year (optional)
        period_type: Filter by period type (optional)
        extension: Filter by extension (optional)

    Returns:
        list[Path]: List of matching report file paths
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    # Build search pattern
    if year:
        search_dir = base_dir / str(year)
        if not search_dir.exists():
            return []
        search_dirs = [search_dir]
    else:
        search_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.isdigit()]

    results: list[Path] = []
    for search_dir in search_dirs:
        # Build pattern based on filters
        if period_type == "monthly":
            pattern = "*-??-github-activity-*"
        elif period_type == "quarterly":
            pattern = "*-Q?-github-activity-*"
        else:
            pattern = "*-github-activity-*"

        if extension:
            pattern = f"{pattern}.{extension}"
        else:
            pattern = f"{pattern}.*"

        results.extend(search_dir.glob(pattern))

    return sorted(results)
