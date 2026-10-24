"""Descriptive diagnostics. Flags are data-review prompts, never diagnoses."""
import numpy as np

FEATURES = ['steps', 'sleep', 'sodium', 'stress']
BOUNDS = {'steps': (0, 20000), 'sleep': (4, 10), 'sodium': (500, 6000), 'stress': (0, 10)}

def diagnostics(rows, validation, coef, cov, target, baseline, horizon, state):
    y = np.array([r.sbp for r in rows])
    median = float(np.median(y))
    mad = float(np.median(np.abs(y-median)))
    flags = []
    # A floor avoids flagging tiny deviations in an otherwise constant series.
    threshold = max(15., 3 * 1.4826 * mad)
    for i, row in enumerate(rows):
        if abs(row.sbp-median) > threshold:
            flags.append({'date': row.date.isoformat(), 'kind': 'unusual_reading', 'detail': 'SBP differs from the history median by more than the robust review threshold.'})
        if i and abs(y[i]-y[i-1]) > 25:
            flags.append({'date': row.date.isoformat(), 'kind': 'large_daily_change', 'detail': 'SBP changed by more than 25 mmHg since the previous day; check measurement context.'})
    flat = [k for k in FEATURES if np.std([getattr(r,k) for r in rows]) < 1e-8]
    for k in flat:
        flags.append({'date': None, 'kind': 'constant_feature', 'detail': f'{k} does not vary; its personal association is not identifiable from this history.'})
    correlations = []
    for i,a in enumerate(FEATURES):
        for b in FEATURES[i+1:]:
            if a not in flat and b not in flat:
                corr = float(np.corrcoef([getattr(r,a) for r in rows], [getattr(r,b) for r in rows])[0,1])
                if abs(corr) >= .85:
                    correlations.append({'first':a,'second':b,'correlation':round(corr,3)})
    roll = [{'date':rows[i].date.isoformat(), 'mean':round(float(np.mean(y[i-6:i+1])),2)} for i in range(6,len(rows))]
    recent = y[-28:]
    trend = {'recent_week':round(float(np.mean(y[-7:])),2), 'previous_week':round(float(np.mean(y[-14:-7])),2),
             'weekly_change':round(float(np.mean(y[-7:])-np.mean(y[-14:-7])),2),
             'slope_per_day':round(float(np.polyfit(np.arange(len(recent)),recent,1)[0]),3),
             'recent_sd':round(float(np.std(recent,ddof=1)),2), 'window_days':len(recent), 'rolling_mean':roll}
    actual = np.array([p['actual'] for p in validation['predictions']])
    predicted = np.array([p['predicted'] for p in validation['predictions']])
    residual = actual-predicted
    residuals = [{'date':p['date'], 'actual':p['actual'], 'predicted':p['predicted'], 'residual':round(float(e),2)} for p,e in zip(validation['predictions'],residual)]
    error = {'bias':round(float(np.mean(residual)),2), 'rmse':round(float(np.sqrt(np.mean(residual**2))),2),
             'max_error':round(float(np.max(np.abs(residual))),2), 'residuals':residuals,
             'bias_definition':'Actual minus predicted; positive means underprediction.'}
    from .model import CENTERS, SCALES
    sensitivity = []
    adaptation = 1-np.exp(-horizon/7.)
    for i,k in enumerate(FEATURES):
        values = [getattr(r,k) for r in rows]
        lo,hi = max(BOUNDS[k][0],min(values)), min(BOUNDS[k][1],max(values))
        points = []
        if lo <= hi:
            for value in np.linspace(lo,hi,7):
                changed = target.copy();changed[i] = value
                x = np.r_[1., (baseline+(changed-baseline)*adaptation-CENTERS)/SCALES]
                points.append({'input':round(float(value),2), 'prediction':round(float(x@coef+state),2)})
        sd = np.sqrt(cov[i+1,i+1])/SCALES[i]
        slope = coef[i+1]/SCALES[i]
        sensitivity.append({'feature':k, 'points':points, 'slope':float(slope),
                            'slope_lower':float(slope-1.96*sd), 'slope_upper':float(slope+1.96*sd)})
    return {'quality':{'rows':len(rows), 'consecutive':True, 'flags':flags, 'correlated_features':correlations,
                       'unchanged_rows':len(rows), 'note':'Heuristic review prompts only. No observations have been removed or repaired.'},
            'trend':trend, 'diagnostics':error, 'sensitivity':sensitivity}
