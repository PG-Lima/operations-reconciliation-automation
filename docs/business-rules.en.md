# Business Rules — Reconciliation

This document records the rules extracted from the original operational workflow and implemented in the domain, Excel input, and report output milestones. It is intentionally independent of the original source code and uses no real business data.

## Input and eligibility

1. The movement reader accepts `.xls`, `.xlsx`, and `.xlsm`, as well as HTML-based Excel exports saved with an `.xls` extension.
2. The movement workbook must contain `Contrato`, `Data da Liberação`, `Situação do Arquivo`, and `Quantidade`; `Tipo da Carga` is optional.
3. The reference is read from the `Referencia_Principal` worksheet, with row 5 as the default header row. Columns beginning with `Empresa`, `Quantidade consolidada`, and `Dias de liberação observados` are required; `Carteira` is optional.
4. Reference competence is extracted from the month/year in a `Quantidade consolidada (mmm/YYYY)` header when recognized.
5. Header matching ignores accents, letter case, and surrounding whitespace; duplicate headers after normalization are ambiguous and stop the import.
6. Movement quantities provided as text may use Brazilian numeric notation, for example `1.234,50`.
7. Only records whose status is `LIBERADO` participate in consolidation.
8. Blank contract names and summary rows such as `nan` or `Total` are ignored.
9. A released row with an un-normalizable company name, invalid quantity, or invalid release date must stop processing rather than silently alter totals.
10. The analysis period begins on day 1 of the cutoff month and ends on the actual cutoff date.
11. The release date determines the month. A separate load-month field does not override it.

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
5. Missing/negative expected quantity or missing/invalid scheduled days results in `Aguardando` with a review note.
6. After the deadline:
   - `Igual`: released quantity equals expected quantity within a tolerance of `1e-9`.
   - `Maior`: released quantity exceeds expected quantity.
   - `Não pagou`: no release was recorded.
   - `Menor`: some quantity was released, but the total is below expected.
7. A quantity above the reference does not override `Aguardando` before the scheduled deadline.

## Excel report

1. The report is generated from an already-computed `ComparisonReport`; the output adapter does not rerun comparison rules.
2. The workbook is saved locally to the caller-supplied `.xlsx` path. The destination directory is created when needed.
3. The `Resumo` worksheet contains company counts, released-quantity totals, and counts by classification.
4. The `Aguardando`, `Menor`, `Igual`, `Maior`, and `Não pagou` worksheets contain only companies in their respective classifications.
5. The `Novas empresas` worksheet lists movements from companies absent from the reference; these companies are not compared against an expected quantity.
6. Report generation does not modify input workbooks or access external services.

## Monthly close — planned workflow

1. The prior month is closed on the first Monday of the new month, or on the first run after that date if the scheduled machine was unavailable.
2. The closing source is selected using the greatest valid release date inside the closing month; file modification time is only a tie-breaker.
3. The greatest actual release date is the cutoff. The source does not require a movement on the last calendar day.
4. The month is evaluated on the first day of the following month so the final scheduled day has elapsed.
5. Generate the final report and process `Menor` tasks before promoting the new monthly reference.
6. The new reference contains companies with at least one released movement in the closed month. Companies with no movement are removed; newly observed companies are added.
7. If a valid closing source cannot be selected or validated, preserve the current reference and stop the next month's comparison.

## Work-board integration — planned workflow

1. Only companies classified as `Menor` create tasks.
2. A task title contains company and competency; the pair is the deduplication key.
3. Existing tasks are ignored, including when a previous run partially completed.
4. Create a task with its title only; do not populate other columns.
5. Automated tests and demo runs use a local mock board. A real API connector is not part of the current milestone.
