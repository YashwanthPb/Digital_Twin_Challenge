"""Compute reproducible conditional holdout metrics on all synthetic fixtures."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pulsetwin.model import AnalysisRequest, analyze
results={}
for name in ['asha','dev','mira']:
    data=json.loads((ROOT/'data'/f'{name}.json').read_text())
    result=analyze(AnalysisRequest(observations=data['observations']))
    results[name]=result['validation']
report={'dataset':'Synthetic fixtures only; not clinical validation','model_version':'1.1.0','profiles':results}
(ROOT/'artifacts/evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
for name,v in results.items(): print(f"{name}: twin MAE={v['twin_mae']}, persistence={v['persistence_mae']}, mean={v['mean_baseline_mae']}, coverage={v['interval_coverage']}")
