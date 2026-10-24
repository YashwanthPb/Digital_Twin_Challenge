"""Interpretable Bayesian regression + a filtered, time-varying residual state.

Effects are associations, not causal treatment estimates. Priors are illustrative.
All validation fits use only observations before the temporal split.
"""
from datetime import date
from typing import Annotated
import csv
import io
import numpy as np
from pydantic import BaseModel, Field, ConfigDict, model_validator

class Observation(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    date: date
    sbp: float = Field(ge=70, le=240)
    steps: float = Field(ge=0, le=40000)
    sleep: float = Field(ge=2, le=12)
    sodium: float = Field(ge=500, le=7000)
    stress: float = Field(ge=0, le=10)

class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    steps: float = Field(default=7500, ge=0, le=20000)
    sleep: float = Field(default=7.5, ge=4, le=10)
    sodium: float = Field(default=2000, ge=500, le=6000)
    stress: float = Field(default=4, ge=0, le=10)

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    observations: Annotated[list[Observation], Field(min_length=28, max_length=730)]
    scenario: Scenario = Field(default_factory=Scenario)
    horizon: int = Field(default=28, ge=7, le=90)

    @model_validator(mode='after')
    def chronological(self):
        days = [o.date for o in self.observations]
        if any((b-a).days != 1 for a,b in zip(days, days[1:])):
            raise ValueError('Provide consecutive daily observations, oldest first, with no duplicate or missing dates.')
        return self

FEATURES = ['steps', 'sleep', 'sodium', 'stress']
CENTERS = np.array([6000., 7., 2300., 5.])
SCALES = np.array([3000., 1., 1000., 2.])
PRIOR_MEAN = np.array([130., -2., -1.5, 2., 2.])
PRIOR_SD = np.array([20., 3., 3., 3., 3.])
NOISE = 5.0
PROCESS_VARIANCE = .15

def design(rows):
    a = np.array([[getattr(o, k) for k in FEATURES] for o in rows])
    return np.column_stack([np.ones(len(rows)), (a - CENTERS) / SCALES])

def fit(rows):
    x = design(rows)
    y = np.array([o.sbp for o in rows])
    precision = np.diag(1/PRIOR_SD**2)
    cov = np.linalg.inv(precision + x.T @ x / NOISE**2)
    mean = cov @ (precision @ PRIOR_MEAN + x.T @ y / NOISE**2)
    # Scalar Kalman filter updates the unobserved residual BP state each day.
    state, variance = 0., 9.
    for residual in y - x @ mean:
        variance += PROCESS_VARIANCE
        gain = variance / (variance + NOISE**2)
        state += gain * (residual-state)
        variance *= 1-gain
    return mean, cov, state, variance

def temporal_validation(rows):
    count = min(14, max(7, len(rows)//5))
    train, test = rows[:-count], rows[-count:]
    coef, cov, state, variance = fit(train)
    x = design(test)
    actual = np.array([r.sbp for r in test])
    prediction = x @ coef + state
    spread = np.sqrt(NOISE**2 + np.einsum('ij,jk,ik->i', x,cov,x) + variance + PROCESS_VARIANCE*np.arange(1,count+1))
    error = lambda p: round(float(np.mean(np.abs(actual-p))), 2)
    return {'train_days': len(train), 'test_days': count,
            'split_date': test[0].date.isoformat(), 'twin_mae': error(prediction),
            'persistence_mae': error(train[-1].sbp),
            'mean_baseline_mae': error(np.mean([r.sbp for r in train])),
            'interval_coverage': round(float(np.mean(np.abs(actual-prediction)<=1.96*spread)),3),
            'protocol': 'Chronological holdout; coefficients and state fit on training days only. Held-out lifestyle covariates are observed, not forecast.',
            'predictions': [{'date':r.date.isoformat(), 'actual':r.sbp, 'predicted':round(float(p),2)} for r,p in zip(test,prediction)]}

def analyze(req):
    rows = req.observations
    coef,cov,state,state_var = fit(rows)
    baseline = np.mean([[getattr(o,k) for k in FEATURES] for o in rows[-7:]],axis=0)
    target = np.array([getattr(req.scenario,k) for k in FEATURES])
    base_x = np.r_[1., (baseline-CENTERS)/SCALES]
    current = float(base_x @ coef + state)
    forecast = []
    for day in range(1,req.horizon+1):
        fraction = 1-np.exp(-day/7.)
        x = np.r_[1., (baseline+(target-baseline)*fraction-CENTERS)/SCALES]
        mean = float(x @ coef + state)
        sd = float(np.sqrt(NOISE**2 + x@cov@x + state_var + PROCESS_VARIANCE*day))
        forecast.append({'day':day,'baseline':round(current,2),'scenario':round(mean,2), 'lower':round(mean-1.96*sd,2),'upper':round(mean+1.96*sd,2)})
    changes = (target-baseline)/SCALES * coef[1:] * (1-np.exp(-req.horizon/7.))
    warnings = ['Research simulation only. Not medical advice or a validated medical device.',
                'Observational associations do not establish causal intervention effects. Do not change medication based on this tool.',
                'Intervals reflect model assumptions; they do not cover all confounding, measurement bias or clinical uncertainty.']
    outside = [k for j,k in enumerate(FEATURES) if target[j]<min(getattr(o,k) for o in rows) or target[j]>max(getattr(o,k) for o in rows)]
    if outside: warnings.append('Extrapolation beyond observed range: '+', '.join(outside)+'. Interpret scenarios cautiously.')
    if len(rows)<60: warnings.append('Limited history: fewer than 60 daily observations. Personal effect estimates may be unstable.')
    if any(o.sbp >= 180 for o in rows[-7:]): warnings.append('Recent very high systolic readings are present. This simulator cannot triage symptoms or replace professional assessment.')
    return {'model_version':'1.0.0','observations':len(rows),'current':round(current,2),
            'delta':round(forecast[-1]['scenario']-current,2), 'forecast':forecast,
            'baseline_inputs':dict(zip(FEATURES,map(float,baseline))),
            'effects':[{'feature':k,'change':round(float(v),2),'coefficient_per_unit':round(float(coef[j+1]/SCALES[j]),6)} for j,(k,v) in enumerate(zip(FEATURES,changes))],
            'validation':temporal_validation(rows), 'warnings':warnings,
            'provenance':{'method':'Bayesian linear regression + scalar Kalman residual state', 'interval':'95% posterior predictive, Gaussian assumptions', 'adaptation_days':7, 'data_retention':'No server-side persistence', 'causal':False}}

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    required = ['date','sbp',*FEATURES]
    if reader.fieldnames != required:
        raise ValueError('CSV header must be exactly: '+','.join(required))
    rows = []
    for i,row in enumerate(reader,start=2):
        if i>731: raise ValueError('Maximum 730 observations allowed.')
        try: rows.append(Observation.model_validate(row))
        except Exception: raise ValueError(f'Invalid observation at CSV line {i}. Check date, numeric ranges and missing values.') from None
    # Validate sequence and sample size with the same rules as JSON input.
    return AnalysisRequest(observations=rows).observations
