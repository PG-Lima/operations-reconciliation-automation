# Quality Assurance — Operations Reconciliation Automation

This document describes how quality is checked locally and through continuous integration. The strategy combines unit tests, integration tests, code coverage, and static analysis.

## Objectives

- Verify domain rules and workbook contracts.
- Detect regressions in reading, discovery, consolidation, comparison, and report generation.
- Validate the end-to-end reconciliation workflow with synthetic Excel workbooks.
- Require statement and branch coverage according to the project configuration.
- Apply static analysis rules through Ruff.

## Test organization

Tests are separated into two layers:

- **Unit tests — tests/unit/:** verify isolated rules and components, including normalization, consolidation, comparison, Excel reading, discovery, report generation, application orchestration, and CLI parsing/execution.
- **Integration tests — tests/integration/:** verify workflows connecting real components. They include the Excel-to-comparison flow and the complete flow from input workbooks to the final report.

CLI tests verify date parsing, required arguments, application execution, and error messages. The test test_application_workflow_integration.py creates synthetic workbooks in temporary directories and runs the application function without replacing components with mocks. It verifies classifications, totals, all seven report worksheets, and that the original workbooks remain unchanged.

## Run checks locally

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the complete suite with coverage:

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
```

Run only unit tests:

```bash
python -m pytest tests/unit -v
```

Run only integration tests:

```bash
python -m pytest tests/integration -v
```

Run the end-to-end application test:

```bash
python -m pytest tests/integration/test_application_workflow_integration.py -v
```

Run Ruff:

```bash
python -m ruff check src tests
```

## Code coverage

The configuration in pyproject.toml enables branch measurement and limits analysis to the operations_reconciliation package.

The configured target is 100% coverage. The pytest-cov command uses --cov-fail-under=100 so the command fails when coverage is below the target.

Statement coverage indicates which statements were executed by the tests. Branch coverage indicates whether measured decision paths were exercised. Both metrics help identify gaps, but they do not prove the absence of defects, the quality of every test case, or production suitability.

When adding a condition, exception, or alternative path, add tests that exercise both the expected behavior and relevant rejection paths.

## Static analysis with Ruff

Ruff is configured in pyproject.toml with a maximum line length of 100 characters, Python 3.13 as the target, and the E4, E7, E9, F, I, B, and UP rule families.

Run:

```bash
python -m ruff check src tests
```

The current configuration runs lint checks. The CI workflow does not run ruff format or a separate formatting check.

## Continuous integration

The .github/workflows/ci.yml workflow runs on:

- Pushes to the main branch.
- Pull requests targeting the main branch.

The job uses Ubuntu, sets up Python 3.14, installs the project with development dependencies, runs the test suite with the 100% coverage target, and runs Ruff.

The workflow limits the token permissions to contents: read and uses concurrency to cancel an earlier run in the same group when a new run starts.

Current CI checks tests and lint. It does not run static type analysis, automated dependency auditing, secret scanning, dynamic analysis, package builds, or automated documentation and link validation.

## Recommended pull request workflow

1. Create a working branch from the updated main branch.
2. Implement the change and its tests.
3. Run unit and integration tests locally.
4. Run the full suite with coverage and Ruff.
5. Review the diffs and confirm that only intended files changed.
6. Open the pull request and wait for CI.
7. Fix failures and rerun checks before merging.

Do not lower the coverage target merely to make a change pass. If the coverage policy needs to change, document the reason and its impact.

## Interpreting results

- **Tests passed:** the executed automated cases passed; this does not guarantee that every possible scenario was covered.
- **Coverage below 100%:** identify unexercised statements or branches and consider additional tests.
- **Ruff failure:** fix lint issues before merging.
- **CI failure:** inspect the job log, reproduce the command locally, and fix the cause rather than only the symptom.

A green CI run is an important integration condition, but it does not replace code review, business-rule review, or security assessment.

## Current strategy limitations

The current configuration does not include performance tests, load tests, compatibility tests across all Python versions, Windows/macOS CI runs, static type analysis, vulnerability auditing, or automated documentation validation.

These checks can be added as the scope grows. Until then, they must not be described as existing controls.

## Internal references

- [Architecture](architecture.en.md)
- [Business Rules](business-rules.en.md)
- [Learning Guide](learning-guide.en.md)
- [Security](security.en.md)
