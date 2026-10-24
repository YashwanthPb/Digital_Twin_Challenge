"""Reproducible synthetic fixtures; no real people or clinical records."""
import csv
import json
from datetime import date, timedelta
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
for name,seed,offset in [('asha',42,0),('dev',57,9),('mira',71,-8)]:
    rng = np.random.default_rng(seed)
    rows=[]
    drift=0.
    for i in range(90):
        steps=round(float(np.clip(6100+1500*np.sin(i/5)+rng.normal(0,1200),1500,14000)))
        sleep=round(float(np.clip(6.8+rng.normal(0,.8),4.5,9)),1)
        sodium=round(float(np.clip(2700+rng.normal(0,650),1000,4500)))
        stress=round(float(np.clip(5+rng.normal(0,1.6),1,9)),1)
        drift=.92*drift+rng.normal(0,.25)
        sbp=round(135+offset-2.4*(steps-6000)/3000-1.8*(sleep-7)+2.7*(sodium-2300)/1000+2.2*(stress-5)/2+drift+rng.normal(0,3.8),1)
        rows.append(dict(date=(date(2026,1,1)+timedelta(days=i)).isoformat(),sbp=sbp,steps=steps,sleep=sleep,sodium=sodium,stress=stress))
    payload={'id':name, 'name':name.title()+' · synthetic', 'description':'Generated 90-day research fixture; not a real patient.', 'seed':seed, 'observations':rows}
    (ROOT/'data'/f'{name}.json').write_text(json.dumps(payload,indent=2)+'\n')
    with (ROOT/'data'/f'{name}.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
