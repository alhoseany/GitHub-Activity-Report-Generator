# =============================================================================
# FILE: tests/__init__.py
# TASKS: UC-1.1 | PLAN-2.2
# PURPOSE: Test suite package for GitHub Activity Report Generator
# =============================================================================
"""
Test Suite Package.

Test organization:
- unit/: Fast tests without I/O (mock all external calls)
- integration/: Tests with filesystem access
- e2e/: End-to-end tests requiring live GitHub API
- fixtures/: Test data and expected outputs
  - api_responses/: Mock API response data
  - expected_outputs/: Expected report outputs for validation

Test markers:
- @pytest.mark.unit: Unit tests
- @pytest.mark.integration: Integration tests
- @pytest.mark.e2e: End-to-end tests (skipped by default)
"""
# UC-1.1 | PLAN-2.2
