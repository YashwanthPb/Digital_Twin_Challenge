# PulseTwin v1.1 research workbench

Built for **Team Gimites**: Yashwanth M (leader), Kalashikam Vijay Krishna, Subiksha K, and Shakthi K.

## 1. Scenario comparison
Run a scenario, then click **Pin current scenario as reference**. Change controls and simulate again. The comparison recomputes the reference against the same active history, horizon and confidence level, displays two curves and their endpoint difference. Switching datasets recomputes the comparison. This compares conditional means, not causal treatment effects. The pin exists only in the current session.

## 2. Named scenario library
Give the current simulated settings a generic name and save them. Up to eight entries persist in this browser's localStorage. **Load & simulate** applies an entry to the current history; **Delete selected** removes it. Stored fields are a chosen label, ID, four input settings, horizon and interval level. No observations, profile identities or model results are stored automatically. Storage failures display a message and leave the rest of the workflow usable.

## 3. Daily twin updates
Enter SBP and habits for the automatically selected next day. **Add observation & update twin** validates the entire sequence, appends the record, refits the personal model and compares the modeled current value before/after. The resulting session dataset remains selectable after switching profiles. It is not saved to a database; export CSV before closing the tab. At 730 records, further appends are disabled.

## 4. Data-quality review
Inspect robust unusual-reading flags, large daily changes, constant inputs and highly correlated feature pairs. All accepted rows remain in the analysis. These heuristics draw attention to measurement context and identifiability; a clean review does not certify data quality or clinical safety. Exact thresholds are documented in the model card.

## 5. Longitudinal trends
A seven-day rolling-mean plot separates historical movement from day-to-day variation. Summary cards report the latest week's mean, its difference from the previous week, and 28-day variability. The text reports the recent linear slope. These are descriptive statistics, not causes or forecasts.

## 6. Sensitivity explorer
Choose movement, sleep, sodium or stress. Seven target values span the permitted observed range while other scenario settings remain fixed. Inspect the conditional endpoint curve and the personal coefficient's 95% interval. There is no fabricated curve if observed values do not intersect the permitted scenario range.

## 7. Error diagnostics
Review every held-out prediction alongside its actual reading and signed residual. Bias shows systematic under/overprediction; RMSE emphasizes larger misses; maximum absolute error highlights the largest miss. The model still uses a chronological split without fitting on held-out BP labels.

## 8. Adjustable uncertainty
Select 80%, 90%, 95% or 99% in the scenario studio. Forecast bounds, legends, exports, printable reports and holdout coverage all use that level. The model's mean prediction does not change. Wider bands are not a more accurate model; they make a different coverage statement under the same assumptions.

## 9. Shareable scenario settings
**Create settings link** encodes only the input settings, horizon, interval and schema version in a URL fragment. No history, profile name or predictions are included. Settings are validated before application, including on same-tab fragment navigation. A localhost link is not a public hosted demo: recipients need a reachable instance of the application. Clipboard denial leaves a selectable link.

## 10. Printable research report
**Print / save as PDF** opens the browser print workflow with a dedicated, uncluttered layout. The report contains team attribution, model version, provenance, observation period, scenario assumptions, predicted outcome and interval, holdout performance, data flags and limitations. Exported reports may contain personal information; sharing remains the user's responsibility. A generated example is in `artifacts/sample-research-report.pdf`.

## Verification

`python -m unittest discover -s tests -v` covers mathematical invariants, quality flags, trends, diagnostics and sensitivity parity. With the server running, `python scripts/browser_features.py` exercises all ten workflows, including local persistence, deletion, shared-link privacy, invalid links, daily updates, session provenance, printed PDF generation and mobile layout.
