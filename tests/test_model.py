import csv
import io
import json
from pathlib import Path
import unittest
import numpy as np
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pulsetwin.app import app
from pulsetwin.model import AnalysisRequest, Scenario, analyze, parse_csv, temporal_validation
ROOT=Path(__file__).resolve().parents[1]

class TwinTests(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'data/asha.json').read_text())['observations']
        self.req=AnalysisRequest(observations=self.rows)
        self.client=TestClient(app)
    def test_model_outputs_finite_ordered_intervals(self):
        r=analyze(self.req)
        self.assertEqual(len(r['forecast']),28)
        for p in r['forecast']:
            self.assertTrue(all(np.isfinite(v) for v in p.values()))
            self.assertLess(p['lower'],p['scenario'])
            self.assertGreater(p['upper'],p['scenario'])
        self.assertAlmostEqual(sum(e['change'] for e in r['effects']),r['delta'],delta=.04)
    def test_unchanged_habits_zero_delta(self):
        baseline={k:np.mean([row[k] for row in self.rows[-7:]]) for k in ['steps','sleep','sodium','stress']}
        r=analyze(AnalysisRequest(observations=self.rows,scenario=Scenario(**baseline)))
        self.assertEqual(r['delta'],0)
    def test_holdout_does_not_leak_target(self):
        before=temporal_validation(self.req.observations)
        changed=[r.model_copy() for r in self.req.observations]
        for row in changed[-14:]:row.sbp+=20
        after=temporal_validation(changed)
        self.assertEqual([x['predicted'] for x in before['predictions']],[x['predicted'] for x in after['predictions']])
        self.assertNotEqual(before['twin_mae'],after['twin_mae'])
    def test_more_observations_update_twin(self):
        shorter=analyze(AnalysisRequest(observations=self.rows[:60]))
        full=analyze(self.req)
        self.assertNotEqual(shorter['current'],full['current'])
    def test_uncertainty_expands_with_horizon_at_fixed_inputs(self):
        baseline={k:np.mean([row[k] for row in self.rows[-7:]]) for k in ['steps','sleep','sodium','stress']}
        r=analyze(AnalysisRequest(observations=self.rows,scenario=Scenario(**baseline),horizon=90))
        self.assertGreater(r['forecast'][-1]['upper']-r['forecast'][-1]['lower'],r['forecast'][0]['upper']-r['forecast'][0]['lower'])
    def test_duplicate_and_missing_dates_rejected(self):
        for index in (0,2):
            rows=[dict(r) for r in self.rows];rows[1]['date']=rows[index]['date']
            with self.assertRaises(ValidationError):AnalysisRequest(observations=rows)
    def test_nonfinite_and_out_of_range_rejected(self):
        for value in ('NaN','Infinity',0,300):
            rows=[dict(r) for r in self.rows];rows[0]['sbp']=value
            with self.assertRaises(ValidationError):AnalysisRequest(observations=rows)
    def test_insufficient_history_rejected(self):
        with self.assertRaises(ValidationError):AnalysisRequest(observations=self.rows[:20])
    def test_extrapolation_warning(self):
        r=analyze(AnalysisRequest(observations=self.rows,scenario=Scenario(steps=20000)))
        self.assertTrue(any('Extrapolation' in w for w in r['warnings']))
    def test_csv_round_trip(self):
        rows=parse_csv((ROOT/'data/asha.csv').read_text())
        self.assertEqual([r.model_dump(mode='json') for r in rows],self.rows)
    def test_csv_bad_header_and_cell(self):
        for text in ('date,sbp\n2026-01-01,130','date,sbp,steps,sleep,sodium,stress\n2026-01-01,bad,6000,7,2300,5'):
            with self.assertRaises(ValueError):parse_csv(text)
    def test_api_end_to_end(self):
        self.assertEqual(self.client.get('/api/health').json()['status'],'ok')
        data=self.client.get('/api/demo/asha').json()
        response=self.client.post('/api/analyze',json={'observations':data['observations']})
        self.assertEqual(response.status_code,200)
        self.assertGreater(response.json()['validation']['twin_mae'],0)
        self.assertEqual(self.client.get('/api/demo/../../etc/passwd').status_code,404)
    def test_api_invalid_inputs(self):
        self.assertEqual(self.client.post('/api/analyze',json={'observations':[]}).status_code,422)
        self.assertEqual(self.client.post('/api/import',content='wrong',headers={'Content-Type':'text/plain'}).status_code,422)
    def test_all_demo_profiles(self):
        for name in ['asha','dev','mira']:
            data=self.client.get('/api/demo/'+name).json()
            r=analyze(AnalysisRequest(observations=data['observations']))
            self.assertEqual(r['validation']['test_days'],14)
            self.assertEqual(r['observations'],90)

if __name__=='__main__':unittest.main()
