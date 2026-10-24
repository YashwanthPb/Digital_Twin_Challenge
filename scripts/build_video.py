"""Render a captioned, synthesized-voice walkthrough from generated slide PNGs.

Requires ffmpeg and espeak-ng. ESPEAK_BIN, ESPEAK_DATA_PATH and LD_LIBRARY_PATH
can select a locally extracted, trusted espeak installation.
"""
from pathlib import Path
import os
import json
import re
import subprocess
import wave
from demo_content import SCENES
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'artifacts/frames'
VOICE=os.environ.get('ESPEAK_BIN','espeak-ng')
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def stamp(sec):
    ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
timeline=[];captions=[];offset=0.;index=1
for i,(title,_,_,narration,_) in enumerate(SCENES,1):
    source=WORK/f'narration-{i:02d}.txt';source.write_text(narration)
    wav=WORK/f'narration-{i:02d}.wav'
    run([VOICE,'-v','en-us','-s','150','-p','43','-w',str(wav),'-f',str(source)])
    with wave.open(str(wav)) as w:voice_duration=w.getnframes()/w.getframerate()
    duration=max(51.,voice_duration+2.5)
    timeline.append({'chapter':i,'title':title,'start_seconds':round(offset,3),'duration_seconds':round(duration,3),'narration_seconds':round(voice_duration,3)})
    # Sentence-sized captions are approximately aligned by word count, not forced alignment.
    sentences=re.split(r'(?<=[.!?])\s+',narration);total=sum(len(s.split()) for s in sentences);cursor=offset
    for sentence in sentences:
        length=voice_duration*len(sentence.split())/total
        captions.append(f'{index}\n{stamp(cursor)} --> {stamp(cursor+length)}\n{sentence}\n');index+=1;cursor+=length
    segment=WORK/f'segment-{i:02d}.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','1','-i',str(WORK/f'slide-{i:02d}.png'),'-i',str(wav),'-t',str(duration),'-vf','scale=1280:720,setsar=1','-af','apad','-c:v','libx264','-threads','2','-preset','fast','-tune','stillimage','-crf','26','-r','10','-pix_fmt','yuv420p','-c:a','aac','-b:a','64k',str(segment)])
    offset+=duration
    print(f'Chapter {i:02d}: {duration:.1f}s; total {offset:.1f}s',flush=True)
assert 900<=offset<=1200, f'Demo duration outside 15–20 minutes: {offset}'
(ROOT/'artifacts/demo.srt').write_text('\n'.join(captions))
(ROOT/'artifacts/demo-timeline.json').write_text(json.dumps({'duration_seconds':round(offset,3),'caption_alignment':'Approximate sentence timing by word count','chapters':timeline},indent=2)+'\n')
concat=WORK/'segments.txt';concat.write_text(''.join(f"file 'segment-{i:02d}.mp4'\n" for i in range(1,len(SCENES)+1)))
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(ROOT/'artifacts/demo.srt'),'-map','0:v','-map','0:a','-map','1:0','-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata','title=PulseTwin — research prototype walkthrough','-metadata:s:s:0','language=eng','-movflags','+faststart',str(ROOT/'artifacts/pulsetwin-demo.mp4')])
print(f'Created narrated demo: {offset/60:.2f} minutes')
