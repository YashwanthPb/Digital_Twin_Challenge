import json
import unittest
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from pulsetwin.model import AnalysisRequest, analyze
ROOT=Path(__file__).resolve().parents[1]

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'data/asha.json').read_text())['observations']
    def result(self,**kwargs):
        return analyze(AnalysisRequest(observations=self.rows,**kwargs))
    def test_confidence_changes_width_not_mean(self):
        results=[self.result(confidence=p) for p in [80,90,95,99]]
        self.assertEqual(len({r['forecast'][-1]['scenario'] for r in results}),1)
        widths=[r['forecast'][-1]['upper']-r['forecast'][-1]['lower'] for r in results]
        self.assertEqual(widths,sorted(widths))
        self.assertGreater(widths[-1],widths[0])
        self.assertEqual(results[0]['validation']['confidence'],80)
    def test_unsupported_interval_rejected(self):
        with self.assertRaises(ValidationError):self.result(confidence=92)
    def test_trend_matches_known_ramp(self):
        for i,r in enumerate(self.rows):r['sbp']=100+i
        result=self.result()['trend']
        self.assertEqual(result['weekly_change'],7)
        self.assertEqual(result['slope_per_day'],1)
        self.assertEqual(len(result['rolling_mean']),84)
        self.assertEqual(result['rolling_mean'][0]['mean'],103)
    def test_constant_inputs_are_flagged_and_finite(self):
        for r in self.rows:
            r.update(steps=6000,sleep=7,sodium=2300,stress=5,sbp=130)
        result=self.result()
        self.assertEqual(len([f for f in result['quality']['flags'] if f['kind']=='constant_feature']),4)
        self.assertEqual(result['quality']['correlated_features'],[])
        json.dumps(result,allow_nan=False)
    def test_quality_flags_do_not_remove_outlier(self):
        self.rows[40]['sbp']=230
        result=self.result()
        self.assertEqual(result['observations'],90)
        self.assertEqual(result['quality']['unchanged_rows'],90)
        self.assertTrue(any(f['kind']=='unusual_reading' for f in result['quality']['flags']))
        self.assertTrue(any(f['kind']=='large_daily_change' for f in result['quality']['flags']))
    def test_correlated_inputs_are_detected(self):
        for i,r in enumerate(self.rows):r.update(steps=5000+i*10,sodium=2000+i*2)
        result=self.result()
        pair=next(c for c in result['quality']['correlated_features'] if c['first']=='steps' and c['second']=='sodium')
        self.assertEqual(pair['correlation'],1)
    def test_residual_metrics_match_predictions(self):
        result=self.result();rows=result['validation']['predictions']
        e=np.array([r['actual']-r['predicted'] for r in rows])
        self.assertEqual(result['diagnostics']['bias'],round(float(e.mean()),2))
        self.assertEqual(result['diagnostics']['rmse'],round(float(np.sqrt(np.mean(e**2))),2))
        self.assertEqual(len(result['diagnostics']['residuals']),14)
    def test_sensitivity_sweep_matches_direct_simulation(self):
        result=self.result();feature=result['sensitivity'][0]
        for p in feature['points']:
            direct=self.result(scenario={'steps':p['input'],'sleep':7.5,'sodium':2000,'stress':4})
            self.assertAlmostEqual(direct['forecast'][-1]['scenario'],p['prediction'],delta=.02)
        self.assertLess(feature['slope_lower'],feature['slope_upper'])
    def test_no_intersection_sensitivity_is_empty(self):
        for r in self.rows:r['sleep']=2
        result=self.result()
        self.assertEqual(next(s for s in result['sensitivity'] if s['feature']=='sleep')['points'],[])
    def test_append_next_day_updates_evidence(self):
        from datetime import date,timedelta
        row=dict(self.rows[-1]);row['date']=(date.fromisoformat(row['date'])+timedelta(days=1)).isoformat();row['sbp']=180
        before=self.result();self.rows.append(row);after=self.result()
        self.assertEqual(after['observations'],91)
        self.assertNotEqual(before['current'],after['current'])
        self.assertEqual(after['diagnostics']['residuals'][-1]['date'],row['date'])

if __name__=='__main__':unittest.main()
