from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .model import AnalysisRequest, analyze, parse_csv

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='PulseTwin', version='1.1.0', description='Research-only personalized systolic blood-pressure digital twin. No clinical claims.')
app.mount('/static', StaticFiles(directory=ROOT/'web'), name='static')

@app.get('/')
def index():
    return FileResponse(ROOT/'web/index.html')

@app.get('/api/health')
def health():
    return {'status':'ok','model_version':'1.1.0','mode':'research','persistence':False}

@app.get('/api/demo/{profile}')
def demo(profile: str):
    if profile not in ('asha','dev','mira'):
        raise HTTPException(404, 'Unknown synthetic profile')
    return json.loads((ROOT/'data'/f'{profile}.json').read_text())

@app.post('/api/analyze')
def analysis(req: AnalysisRequest):
    return analyze(req)

@app.post('/api/import')
def import_csv(text: str = Body(media_type='text/plain', max_length=150000)):
    try:
        return {'observations':[o.model_dump(mode='json') for o in parse_csv(text)]}
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from None
