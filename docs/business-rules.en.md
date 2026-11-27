# Business Rules — Reconciliation

This document records the reconciliation workflow rules and distinguishes implemented behavior from rules proposed for future milestones. The public implementation is independent and uses synthetic data only.

## Input and eligibility

1. The movement reader accepts `.xls`, `.xlsx`, and `.xlsm`, as well as HTML-based Excel exports saved with an `.xls` extension.
2. The movement workbook must contain `Contrato`, `Data da Liberação`, `Situação do Arquivo`, and `Quantidade`; `Tipo da Carga` is optional.
3. The reference is read from the `Referencia_Principal` worksheet, with row 5 as the default header row. Columns beginning with `Empresa`, `Quantidade consolidada`, and `Dias de liberação observados` are required; `Carteira` is optional.
4. Reference competence is extracted from the month and year in a `Quantidade consolidada (mmm/YYYY)` header when recognized.
5. Header matching ignores accents, letter case, and surrounding whitespace. Duplicate headers after normalization are ambiguous and stop the import.
6. Movement quantities provided as text may use Brazilian numeric notation, for example `1.234,50`.
7. Only records whose status is `LIBERADO` participate in consolidation.
8. Blank contract names and summary rows such as `nan` or `Total` are ignored.
9. A released row with an un-normalizable company name, invalid quantity, or invalid release date stops processing rather than silently altering totals.
10. The analysis period begins on day 1 of the cutoff month and ends on the actual cutoff date.
11. The release date determines the month. A separate load-month field does not override it.

## Excel file discovery

1. Discovery scans only the supplied local directory; it does not recurse into subdirectories.
2. Hidden files, Excel temporary files beginning with `~$`, empty files, and unsupported extensions are ignored.
3. A non-empty candidate workbook that cannot be read or validated stops discovery with an error identifying the file.
4. Movement discovery considers only `LIBERADO` records whose Release Date belongs to the requested competence.
5. The selected movement workbook is the one containing the latest Release Date within the competence. File modification time is used only when the latest release dates tie.
6. If two or more movement workbooks tie on both the latest Release Date and file modification time, discovery stops with an ambiguity error.
7. Reference discovery requires the competence extracted from the header to match the requested month and exactly one matching workbook to exist. Missing or duplicate matches stop processing.
8. Discovery does not move, rename, overwrite, or modify source files and does not access remote services.

## Consolidation

1. Company identity is normalized by removing accents, punctuation, case differences, and repeated whitespace.
2. Quantities are summed by normalized company.
3. The aggregate retains the first and last release dates, unique release days, number of released records, and unique load types.
4. Original company display names are retained for reports; normalized keys are used only for matching.

## Comparison

1. Every company in the reference remains in the result, including companies without any released movement.
2. A company not found in the reference is reported separately as `Sem referência`; it is not compared against an expected quantity.
3. The final scheduled day is the largest valid day in the reference. A day beyond the calendar end of a month is capped at that month's last day.
4. The company remains `Aguardando` on the final scheduled day. Final classification starts on the following day.
5. Missing or negative expected quantity, or missing or invalid scheduled days, results in `Aguardando` with a review note.
6. After the deadline:
   - `Igual`: released quantity equals expected quantity within a tolerance of `1e-9`.
   - `Maior`: released quantity exceeds expected quantity.
   - `Não pagou`: no release was recorded.
   - `Menor`: some quantity was released, but the total is below expected.
7. A quantity above the reference does not override `Aguardando` before the scheduled deadline.

## Single-run orchestration

The `run_reconciliation()` function coordinates one complete local execution:

1. The cutoff date must belong to the requested competence.
2. The evaluation date, when supplied, cannot precede the cutoff date. When omitted, it defaults to the cutoff date.
3. The application discovers matching workbooks, reads and validates the data, consolidates movements, performs the comparison, and generates the report.
4. The output path cannot match the path of either selected input workbook.
5. The function returns a `ReconciliationResult` containing the selected file paths, comparison result, and report path.

This orchestration is local. Simulated task creation runs only when a `--task-board` path is supplied. The workflow does not schedule executions, create tasks on external boards, promote references, or access remote services.

## Excel report

1. The report is generated from an already-computed `ComparisonReport`; the output adapter does not rerun comparison rules.
2. The workbook is saved locally to the caller-supplied `.xlsx` path. The destination directory is created when needed.
3. The `Resumo` worksheet contains company counts, released-quantity totals, and counts by classification.
4. The `Aguardando`, `Menor`, `Igual`, `Maior`, and `Não pagou` worksheets contain only companies in their respective classifications.
5. The `Novas empresas` worksheet lists movements from companies absent from the reference; these companies are not compared against an expected quantity.
6. Report generation does not modify input workbooks or access external services.

## Monthly close — planned workflow

The rules below describe a future extension and are not part of the currently implemented workflow.

1. The prior month will be closed on the first Monday of the new month, or on the first run after that date if the scheduled machine was unavailable.
2. The closing workbook will be selected using the greatest valid Release Date inside the competence; file modification time will be only a tie-breaker.
3. The greatest actual release date will define the cutoff. A movement on the last calendar day will not be required.
4. The competence will be evaluated on the first day of the following month so the final scheduled day has elapsed.
5. The final report will be generated and `Menor` items will be processed before promoting the new monthly reference.
6. The new reference will contain companies with at least one released movement in the closed month. Companies with no movement will be removed; newly observed companies will be added.
7. If a closing source cannot be selected or validated, the current reference will be preserved and the next month's comparison will stop.

## Local task-board simulation

1. The simulator is optional and runs only when the caller supplies a JSON path through the `--task-board` argument or the application's `task_board_path` parameter.
2. Only companies classified as `Menor` create tasks. `Aguardando`, `Igual`, `Maior`, `Não pagou`, and `Sem referência` do not create tasks.
3. The visible title contains the company name and competence in the format `Company - YYYY-MM`.
4. The internal deduplication key consists of the normalized company name and the `YYYY-MM` competence. Repeated runs skip existing keys, including after a previous run was interrupted.
5. The visible task contains only its title. The company key and competence are internal metadata required for deduplication, not additional task fields.
6. The board is persisted in a local JSON file, uses a schema version, and writes updates by atomically replacing a temporary file.
7. Invalid or corrupted JSON, or duplicate identities, stops execution; the simulator does not silently discard existing state.
8. The simulator does not use APIs, authenticate with Monday.com, or create tasks on external boards. The local file must be protected and must not contain real employer or customer data.
