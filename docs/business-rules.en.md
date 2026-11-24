# Business Rules — Reconciliation

This document records the rules extracted from the original operational workflow and implemented in the first domain milestone. It is intentionally independent of the original source code and uses no real business data.

## Input and eligibility

1. Only records whose status is `LIBERADO` participate in consolidation.
2. Blank contract names and summary rows such as `nan` or `Total` are ignored.
3. A released row with an un-normalizable company name or an invalid quantity must stop processing rather than silently alter totals.
4. The analysis period begins on day 1 of the cutoff month and ends on the actual cutoff date.
5. The release date determines the month. A separate load-month field does not override it.

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
