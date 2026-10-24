# PulseTwin model card · version 1.1.0

## Intended use
Research and educational exploration of an individual's daily systolic-BP associations. Not diagnostic, therapeutic, triage or autonomous medical software. Dataset fixtures are entirely synthetic. No clinical or regulatory validation is claimed.

## Model specification
For each observation, the design vector is:

`x = [1, (steps-6000)/3000, (sleep-7)/1, (sodium-2300)/1000, (stress-5)/2]`.

The observation model is `y = x beta + z + epsilon`. Regression uses a diagonal Gaussian prior with means `[130, -2, -1.5, 2, 2]`, standard deviations `[20, 3, 3, 3, 3]`, and fixed observation standard deviation 5 mmHg. These are illustrative engineering parameters, not coefficients extracted from a clinical trial.

Posterior covariance: `C = inverse(P + X.T X / 25)`. Posterior mean: `m = C (P m0 + X.T y / 25)`, where `P` is prior precision. Each person is fitted independently; there is no population-trained model.

A scalar residual state starts at mean 0, variance 9. Each day adds process variance 0.15 mmHg². The Kalman gain is `K = v / (v + 25)`. State updates use `z <- z + K (y - x m - z)` and `v <- (1-K) v`. Regression is fitted on the full available history before filtering its residuals. This two-stage approximation does not jointly infer coefficients and state, so uncertainty omits their dependence.

For scenario day d, habits are `recent_7_day_mean + (target - recent_7_day_mean) * (1 - exp(-d/7))`. The seven-day adaptation time constant is assumed, not learned. Forecast mean is `x_d m + z`. Predictive variance is `25 + x_d C x_d.T + v + 0.15 d`. Bands use the standard-normal quantile for the selected 80%, 90%, 95% (default), or 99% level. Holdout interval coverage uses the same level. They represent noisy daily SBP, not confidence intervals for a treatment effect.

The baseline keeps recent habits and residual state constant. Contributions equal standardized input changes multiplied by corresponding coefficients and the adaptation fraction. They sum to the projected difference before rounding. Association signs are not constrained; imported datasets may produce counterintuitive coefficients. This is surfaced rather than concealed.

## Data contract
CSV header order: `date,sbp,steps,sleep,sodium,stress`. Consecutive, unique ISO dates; 28–730 rows. SBP 70–240 mmHg; steps 0–40,000; sleep 2–12 h; sodium 500–7,000 mg; stress 0–10. Scenario bounds differ to keep the controls usable: steps 0–20,000; sleep 4–10 h; sodium 500–6,000 mg; stress 0–10. These are software input limits, not recommended ranges. Missing data must be resolved upstream; the prototype refuses to silently impute it.

CSV request text is limited to 150,000 characters. Imported data must be synthetic or appropriately authorized and de-identified. The backend is stateless, but exports include raw observations and must be handled accordingly.

## Evaluation protocol
Test size is min(14, max(7, floor(n/5))). The initial days form the training set; the final days are the test set. Training labels alone determine coefficients and filtered state. Test-day covariates are observed inputs; the test state is not updated using held-out labels. Baselines are the last training BP and the training mean. MAE and empirical coverage at the selected predictive interval level (95% by default) are reported.

The production scenario fit uses all supplied history after this separate holdout evaluation. Do not confuse holdout predictions with future scenario forecasts.

## Known limitations
Synthetic data is generated using approximately linear effects similar to the fitted model. No population transportability, fairness, causal effect, long-term clinical benefit or subgroup performance is established. Daily autocorrelation, measurement timing, medication changes, kidney function, age, comorbidities and many other factors are not modeled. Fixed Gaussian noise may be inappropriate. The latent-state/regression split can double count patterns and underrepresent uncertainty. Out-of-range habits generate a warning; there is no guarantee extrapolated scenarios are physiologically plausible. No clinical threshold classification is performed.

## Reproducibility
Generator seeds: Asha 42, Dev 57, Mira 71. Dates: 2026-01-01 through 2026-03-31. Run `python scripts/generate_data.py` then `python scripts/evaluate.py`. Dependencies are pinned in requirements files. Full held-out predictions are stored in `artifacts/evaluation.json`.

## Research workbench diagnostics (v1.1)

Quality review flags SBP values farther from the history median than `max(15, 3 × 1.4826 × MAD)`, daily SBP changes above 25 mmHg, constant predictors (standard deviation below 1e-8), and nonconstant predictor pairs with absolute Pearson correlation at least 0.85. These are engineering heuristics, not clinical thresholds. Flags never remove or repair rows.

Trends use trailing seven-day means, latest-week minus previous-week means, a least-squares slope over the final 28 days, and sample standard deviation over that window. Error diagnostics use the rounded held-out predictions: signed actual-minus-predicted bias, RMSE and maximum absolute residual.

Sensitivity evaluates seven evenly spaced target values within the intersection of a feature's observed range and scenario bounds. Other targets remain fixed. An empty intersection yields no sweep. Coefficient intervals remain at 95% and are labeled separately from the selectable predictive interval. A flat observed feature cannot identify its personal association; the prior still supplies a coefficient.

Scenario comparisons refit both targets on the same current history and apply the current horizon/confidence to both. Saved and shared scenarios contain inputs only, never patient observations or fitted results. Daily additions must pass the full existing schema and date-sequence checks before replacing session history.
