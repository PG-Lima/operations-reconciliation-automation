# Command-line interface

The command-line interface runs a local reconciliation without requiring a Python script to call the application function directly.

## Installation

With the virtual environment active, install the project and its dependencies:

```powershell
python -m pip install -e ".[dev]"
```

The package registers the `operations-reconciliation` command in the active Python environment.

## Run a reconciliation

```powershell
operations-reconciliation reconcile --movement-dir "data/movements" --reference-dir "data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13 --task-board "local-state/task-board.json"
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `reconcile` | Yes | Subcommand that runs one reconciliation. |
| `--movement-dir` | Yes | Local folder containing movement workbooks. |
| `--reference-dir` | Yes | Local folder containing the reference workbook. |
| `--competence` | Yes | Competence in `YYYY-MM` format. |
| `--cutoff-date` | Yes | Last included release date, in `YYYY-MM-DD` format. |
| `--output` | Yes | Local report destination with the `.xlsx` extension. |
| `--evaluation-date` | No | Date used to evaluate classifications. Defaults to the cutoff date. |
| `--task-board` | No | Path to a `.json` file for persistent local simulation. If omitted, no tasks are simulated. |

The CLI validates competence and date formats before calling `run_reconciliation()`. Business rules, file discovery, workbook reading, comparison, and report generation remain in the existing application and adapters. When `--task-board` is supplied, only `Menor` companies create simulated tasks with the title `Company - YYYY-MM`; repeated runs skip identities already stored. The `local-state/` directory is ignored by Git by default.

Input directories and workbooks must exist and satisfy the [Excel contracts](learning-guide.en.md#understand-the-workbook-contracts). Discovery scans files directly inside the supplied folders and does not recurse into subdirectories.

## Exit codes

- `0`: reconciliation completed and the report was generated.
- `1`: execution failure, such as a missing file, invalid workbook, incompatible parameters, or invalid task-board JSON. Because the report is generated before simulation, it may already exist when a task-board error occurs.
- `2`: missing or invalid arguments handled by argparse.

The CLI does not create sample data, schedule runs, access remote services, create tasks on external boards, or modify source workbooks. The `--task-board` argument enables only the local simulation.

## Verification

Run the interface tests:

```powershell
python -m pytest tests/unit/test_cli.py -v
```

Also run the complete quality suite before proposing changes.
