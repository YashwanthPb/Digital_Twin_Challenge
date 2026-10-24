"""Generate the architecture and presentation PDFs, narration and slide images."""
from pathlib import Path
from xml.sax.saxutils import escape
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("OpenSans", "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("OpenSans-Bold", "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"))
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from demo_content import SCENES
ROOT=Path(__file__).resolve().parents[1]
W,H=1280,720
INK='#19352f';GREEN='#13765b';MUTED='#687b74';PAPER='#f7f9f5';LIME='#d8f18a'
def text(c,s,x,y,size=20,color=INK,width=1100,font='OpenSans',leading=None):
    style=ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.35,textColor=HexColor(color))
    p=Paragraph(escape(s),style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return h

def base(c,kicker,index):
    c.setFillColor(HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0)
    text(c,'PulseTwin',58,677,24,GREEN,font='OpenSans-Bold')
    text(c,kicker,58,604,12,GREEN,font='OpenSans-Bold')
    c.setStrokeColor(HexColor('#dce5d8'));c.line(58,55,1222,55)
    text(c,'TEAM GIMITES  /  DIGITAL TWIN CHALLENGE 2026  /  SYNTHETIC RESEARCH PROTOTYPE',58,36,9,MUTED)
    text(c,f'{index:02d}',1180,38,12,GREEN)

out=ROOT/'docs/presentation.pdf';c=canvas.Canvas(str(out),pagesize=(W,H));c.setTitle('PulseTwin — Digital Twin Challenge 2026');c.setAuthor('Team Gimites')
for i,(title,kicker,bullets,narration,img) in enumerate(SCENES,1):
    base(c,kicker,i)
    if img and (ROOT/'artifacts'/f'demo-{img}.png').exists():
        text(c,title,58,565,35,width=1160,font='OpenSans-Bold')
        c.drawImage(str(ROOT/'artifacts'/f'demo-{img}.png'),58,118,width=810,height=380,preserveAspectRatio=True,anchor='c',mask='auto')
        y=490
        for n,b in enumerate(bullets,1):
            text(c,f'0{n}',908,y,13,GREEN,font='OpenSans-Bold');y-=28
            y-=text(c,b,908,y,17,width=300)+26
    else:
        text(c,title,58,554,48,width=1150,font='OpenSans-Bold')
        y=420
        for n,b in enumerate(bullets,1):
            c.setFillColor(HexColor('#eaf2df'));c.roundRect(58,y-70,1160,88,12,fill=1,stroke=0)
            text(c,f'0{n}',82,y-4,18,GREEN,font='OpenSans-Bold')
            text(c,b,140,y-1,23,width=1040)
            y-=110
    c.showPage()
c.save()

c=canvas.Canvas(str(ROOT/'docs/architecture.pdf'),pagesize=(W,H));c.setTitle('PulseTwin system architecture');base(c,'SYSTEM ARCHITECTURE / IMPLEMENTED PROTOTYPE',1)
text(c,'A transparent observation-to-scenario loop.',58,557,37,font='OpenSans-Bold')
boxes=[(58,320,'01  Browser','HTML / CSS / JavaScript','Compare, save settings, CSV, PDF export'),(460,320,'02  API contract','FastAPI / Pydantic','Schema, bounds, consecutive dates'),(862,320,'03  Personal model','NumPy / Bayesian + Kalman','Fit, state, forecast, holdout')]
for x,y,a,b,d in boxes:
    c.setFillColor(HexColor('#eaf2df'));c.roundRect(x,y,360,150,12,fill=1,stroke=0)
    text(c,a,x+22,y+125,22,GREEN,font='OpenSans-Bold');text(c,b,x+22,y+82,17);text(c,d,x+22,y+43,13,MUTED,width=320)
for x in [423,825]:
    c.setStrokeColor(HexColor(GREEN));c.setLineWidth(2);c.line(x,395,x+30,395);c.line(x+24,401,x+30,395);c.line(x+24,389,x+30,395)
text(c,'REQUEST',58,275,12,GREEN,font='OpenSans-Bold');text(c,'Observations + hypothetical inputs + horizon -> validated request -> personal fit and state -> conditional trajectory + evidence',58,245,21,width=1160)
text(c,'TRUST BOUNDARY',58,170,12,GREEN,font='OpenSans-Bold');text(c,'Local browser and server. Named settings only in browser storage; observations stay in memory. No authentication, live devices or external AI calls. Use authorized data.',58,140,18,MUTED,width=1160)
c.showPage();base(c,'MODEL FLOW / EVALUATION SEPARATION',2)
text(c,'One history. Two separate model fits.',58,550,40,font='OpenSans-Bold')
for x,title,lines in [(58,'Scenario path',['All supplied history -> Bayesian coefficient posterior','Residual sequence -> Kalman state','Recent 7-day habits -> assumed gradual scenario','Mean + selected predictive band -> contribution report']), (665,'Evaluation path',['Chronological training prefix only -> separate fit','Held-out daily habits -> conditional predictions','Held-out BP labels -> MAE and interval coverage','Last reading + training mean -> comparison baselines'])]:
    text(c,title,x,450,26,GREEN,font='OpenSans-Bold');y=395
    for s in lines:y-=text(c,s,x,y,20,width=540)+30
text(c,'Important: no held-out BP label enters the evaluation fit. Known held-out habits make this conditional prediction, not prospective causal validation.',58,130,17,MUTED,width=1150)
c.showPage();c.save()
(ROOT/'docs/demo-script.md').write_text('# PulseTwin narrated demo script\n\nSynthesized narration over actual application captures and technical slides. Not a live clinical demonstration.\n\n'+'\n\n'.join(f'## {i:02d}. {title}\n\n{narration}' for i,(title,_,_,narration,_) in enumerate(SCENES,1))+'\n')
frames=ROOT/'artifacts/frames';frames.mkdir(exist_ok=True)
subprocess.run(['pdftoppm','-scale-to','1280','-png',str(out),str(frames/'slide')],check=True,stdout=subprocess.DEVNULL)
print(f'Generated {len(SCENES)}-slide presentation, 2-page architecture, narration and slide PNGs.')
