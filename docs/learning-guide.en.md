# Learning Guide — Operations Reconciliation Automation

This guide provides a path to study the project, reproduce the reconciliation workflow with synthetic data, and adapt the implementation to another context. The repository has two equally important goals: a professional portfolio and an open learning resource.

## What you will learn

- Organize a Python application into domain, service, adapter, and application layers.
- Validate and interpret Excel workbooks through explicit data contracts.
- Normalize and consolidate records before comparing them with a reference.
- Separate business rules from file input and output operations.
- Coordinate a complete workflow and test it with synthetic workbooks.
- Use Pytest, code coverage, and Ruff in a Python project.

## Prerequisites

- Python 3.13 or newer.
- Git.
- Basic familiarity with the terminal, virtual environments, and Python.
- Basic knowledge of Excel workbooks.

The repository's continuous integration runs the test suite with Python 3.14. The project can also be installed in compatible Python 3.13+ environments.

## Set up the environment

Clone the repository and enter its directory:

```bash
git clone https://github.com/PG-Lima/operations-reconciliation-automation.git
cd operations-reconciliation-automation
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the project and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Reproduce the complete workflow

The workflow can be executed through the CLI with synthetic workbooks that satisfy the contracts described in this guide. The integration test also remains available as a reproducible end-to-end demonstration:

```bash
python -m pytest tests/integration/test_application_workflow_integration.py -v
```

This test creates synthetic Excel workbooks in temporary directories, runs the real application workflow, and checks the generated report. No corporate workbooks or remote connections are needed.

The test scenario uses:

- A movement workbook containing released and pending records.
- A reference workbook on the `Referencia_Principal` worksheet, with headers on row 5.
- Two ACME releases totaling 50 units.
- A Beta company present in the reference but with no released movement.
- A new company, absent from the reference, with 5 released units.

The run uses November 2026 as the competence, November 12 as the cutoff date, and November 13 as the evaluation date. The test checks classifications, totals, all seven report worksheets, and preservation of the source workbooks.

## Run from the command line

With the virtual environment active and the project installed using `python -m pip install -e ".[dev]"`, run this command in PowerShell, adjusting the folders and dates to match the synthetic workbooks you prepared:

```powershell
operations-reconciliation reconcile --movement-dir "examples/data/movements" --reference-dir "examples/data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13 --task-board "local-state/task-board.json"
```

Competence uses `YYYY-MM`; dates use `YYYY-MM-DD`. The evaluation date may be omitted, in which case the cutoff date is used. `--task-board` is also optional: when supplied, it persists simulated tasks in a local JSON file; when omitted, no tasks are created. The command prints the paths of the selected workbooks and the generated report. It does not create input workbooks: the directories and files must exist and follow this guide's contracts.

See the [Command-line interface guide](cli.en.md) for all arguments and exit codes.

## Simulate local tasks

To enable the simulation, add `--task-board "local-state/task-board.json"` to the CLI command. Only companies classified as `Menor` create tasks. The title contains the company and competence; deduplication internally uses the normalized company name and competence so repeated runs do not duplicate existing tasks.

The JSON file stores the simulator's local state. The default `local-state/` folder is listed in `.gitignore`, but alternate paths are not ignored automatically. Use synthetic data and do not publish the file. The simulation does not connect to Monday.com or create remote items.

## Understand the workbook contracts

### Movement workbook

The reader accepts `.xls`, `.xlsx`, and `.xlsm`, as well as HTML-based Excel exports detected by their content and saved with an `.xls` extension.

The required columns are:

- `Contrato`
- `Data da Liberação`
- `Situação do Arquivo`
- `Quantidade`

The `Tipo da Carga` column is optional. Only records whose status is `LIBERADO` are included in consolidation. Blank contracts and summary rows such as `Total` are ignored.

### Reference workbook

The reader expects the `Referencia_Principal` worksheet and uses row 5 as the default header row. Recognized columns include:

- `Empresa`
- `Quantidade consolidada (mmm/YYYY)`
- `Dias de liberação observados`

The `Carteira` column is optional. Competence is extracted from the month and year in the consolidated-quantity header.

Header names are normalized to ignore accents, letter case, and surrounding whitespace. Ambiguous headers, invalid dates, invalid quantities, and duplicate companies after normalization stop the import with an explicit error.

See [Business Rules](business-rules.en.md) for detailed criteria and classification examples.

## Call the application function

The function coordinating one execution is `run_reconciliation()`, located in `src/operations_reconciliation/application/reconciliation.py`.

Example call for a reader who has already prepared synthetic workbooks matching the contracts above:

```python
from datetime import date
from pathlib import Path

from operations_reconciliation.application.reconciliation import run_reconciliation

result = run_reconciliation(
    movement_directory=Path("examples/data/movements"),
    reference_directory=Path("examples/data/references"),
    competence=date(2026, 11, 1),
    cutoff_date=date(2026, 11, 12),
    output_path=Path("output/reconciliation.xlsx"),
    evaluation_date=date(2026, 11, 13),
)

print(f"Movement workbook: {result.movement_workbook}")
print(f"Reference workbook: {result.reference_workbook}")
print(f"Report: {result.output_workbook}")
```

The paths in this example are illustrative: the directories and workbooks must exist and satisfy the input contracts. Discovery scans only files directly inside the supplied directories; it does not recurse into subdirectories.

The cutoff date must belong to the requested competence. When supplied, the evaluation date cannot precede the cutoff date. If the evaluation date is omitted, the application uses the cutoff date. The output path cannot point to either selected input workbook.

The function returns a `ReconciliationResult` containing the selected workbook paths, comparison report, and generated file path.

## Recommended code-reading path

1. `domain/models.py`: start with the models and structures representing the data and results.
2. `services/normalization.py`: understand how names and values are normalized.
3. `services/consolidation.py`: follow how released movements are aggregated.
4. `services/comparison.py`: study the classifications and comparison against the reference.
5. `adapters/excel_reader.py`: see how workbooks are converted into domain data.
6. `adapters/file_discovery.py`: understand the selection rules for local files.
7. `adapters/excel_report.py`: follow the generation of the report's seven worksheets.
8. `application/reconciliation.py`: finally, see how the application coordinates every step.

Use unit tests to understand isolated cases and `test_application_workflow_integration.py` to observe the end-to-end execution.

## Run the quality checks

Run the full test suite with statement and branch coverage:

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
```

Run static analysis:

```bash
python -m ruff check src tests
```

The configuration requires at least 100% coverage and enables branch measurement. See [Quality Assurance](quality-assurance.en.md) for the strategy, the meaning of these metrics, and CI automation.

## Adapt the project to another context

Before changing the code, identify the differences between the new scenario and the current contracts.

1. Document the columns, formats, identifiers, and rules of the new data sources.
2. Change the input adapters to interpret the new format without leaking spreadsheet details into the domain.
3. Review normalization, consolidation, and comparison rules in the services.
4. Update domain models only when the business concepts actually change.
5. Update or add unit and integration tests using synthetic data.
6. Run the complete test suite and Ruff before proposing the change.

Do not reuse real employer or customer data in examples, tests, or commits. See [Security](security.en.md) before introducing new data paths or integrations.

## Current limitations

The documented workflow runs locally. Scheduling, Monday.com integration, external task creation, automatic monthly closing, and reference promotion are not implemented in this milestone. The optional local task simulation is available; monthly closing and reference promotion remain planned.

The CLI runs the workflow with user-supplied workbooks; the integration test remains the self-contained demonstration that creates its own synthetic files.
