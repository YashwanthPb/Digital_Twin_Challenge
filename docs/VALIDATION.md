# Validation evidence

## Automated model/API checks

Command: `python -m unittest discover -s tests -v`.

14 tests pass: finite forecasts and ordered bands; unchanged-habit invariance; no held-out target leakage; observation-driven updates; uncertainty growth; duplicate/missing dates; non-finite/out-of-range data; insufficient history; extrapolation warnings; CSV round-trip; malformed CSV; API analysis; API rejection; and all three fixture profiles.

## Browser acceptance

Command: `python scripts/browser_check.py`, with the server on port 8000 and Chromium available.

Passed in real headless Chromium: initial dashboard render, scenario submission, horizon changes, profile changes, CSV import, switching back to imported data, report download and contents, invalid CSV feedback, 390px mobile viewport without horizontal overflow, and no uncaught JavaScript errors. Screenshots are in `artifacts/`.

## Model evaluation

Command: `python scripts/evaluate.py`. Full results and predictions: `artifacts/evaluation.json`.

| Fixture | Train / test | Twin MAE | Persistence MAE | Mean MAE | Coverage |
|---|---|---:|---:|---:|---:|
| Asha | 76 / 14 | 3.01 | 5.18 | 3.60 | 1.00 |
| Dev | 76 / 14 | 3.19 | 5.49 | 3.85 | 1.00 |
| Mira | 76 / 14 | 2.81 | 5.41 | 4.47 | 1.00 |

All errors are mmHg. Only synthetic fixtures were evaluated. Holdout covariates are known inputs. These checks do not establish clinical safety, efficacy, causal validity, prospective accuracy, subgroup fairness, production load capacity or regulatory compliance.

## Generated media and publication

The presentation contains 18 pages; the architecture PDF contains 2 pages. Representative rendered PDF pages were visually inspected. FFprobe identifies H.264 1280×720 video, AAC audio and an English subtitle track in the final MP4. Duration is 1133.33 seconds (18:53). A full FFmpeg audio/video decode completed without errors.

The source was pushed to the repository's `main` branch. The public repository page reports Public, and README, architecture PDF, presentation PDF and MP4 return HTTP 200 through unauthenticated HTTP requests (no explicit authorization headers). This verifies repository asset access, not a YouTube upload or Unstop submission.
