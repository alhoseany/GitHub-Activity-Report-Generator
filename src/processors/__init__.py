# =============================================================================
# FILE: src/processors/__init__.py
# TASKS: UC-2.3, UC-7.1
# PLAN: Section 3.7, 4.1
# =============================================================================
"""
Data Processing Package.

This package handles data aggregation and metrics calculation:
- aggregator.py: DataAggregator for combining fetched data
- metrics.py: MetricsCalculator for PR, review, engagement metrics

Features:
- Date filtering and validation
- Summary statistics calculation
- Metrics calculation (PR time, review turnaround, etc.)
- Data deduplication
- Productivity patterns analysis

Usage:
    from src.processors import DataAggregator, AggregatedData
    from src.processors import MetricsCalculator, PRMetrics, ReviewMetrics
"""
# UC-2.3, UC-7.1 | PLAN-3.7, 4.1

from .aggregator import DataAggregator, AggregatedData
from .metrics import (
    MetricsCalculator,
    PRMetrics,
    ReviewMetrics,
    EngagementMetrics,
    ProductivityPatterns,
    ReactionBreakdown,
    create_metrics_calculator,
)

__all__ = [
    # Aggregator
    "DataAggregator",
    "AggregatedData",
    # Metrics
    "MetricsCalculator",
    "PRMetrics",
    "ReviewMetrics",
    "EngagementMetrics",
    "ProductivityPatterns",
    "ReactionBreakdown",
    "create_metrics_calculator",
]
