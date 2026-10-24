'use strict';
const $=id=>document.getElementById(id);
let observations=[], result=null, activeName='', requestNumber=0, importedRows=null, profileRequest=0, importedName='Imported observations', importedSource='IMPORTED DATA';
const keys=['steps','sleep','sodium','stress'];
const names={steps:'Movement',sleep:'Sleep',sodium:'Sodium',stress:'Stress'};
function announce(message){$('status').textContent=message;}
function error(message){$('error').textContent=message;$('error').hidden=!message;}
async function api(path,options){const r=await fetch(path,options);const data=await r.json();if(!r.ok){const d=data.detail;throw new Error(typeof d==='string'?d:Array.isArray(d)?d.map(v=>v.msg).join('; '):'Request failed');}return data;}
function labels(){keys.forEach(k=>{const v=Number($(k).value);$(k+'-value').textContent=k==='steps'?v.toLocaleString()+' steps':k==='sleep'?v.toFixed(1)+' hours':k==='sodium'?v.toLocaleString()+' mg':v+' / 10';});}
function setMeta(name,synthetic){activeName=name;$('avatar').textContent=name[0].toUpperCase();$('days-label').textContent=observations.length+' daily observations';$('dates-label').textContent=observations[0].date+' → '+observations.at(-1).date;$('data-chip').textContent=synthetic?'SYNTHETIC DATA':'IMPORTED DATA';}
function scenarioInputs(){return Object.fromEntries(keys.map(k=>[k,Number($(k).value)]));}
function setBusy(busy){
  $('simulate').disabled=busy;
  $('export').disabled=busy||!result;
  document.querySelectorAll('.result-action').forEach(b=>b.disabled=busy||!result);
}
function markDirty(){
  ++requestNumber;setBusy(false);
  $('export').disabled=true;
  document.querySelectorAll('.result-action').forEach(b=>b.disabled=true);
  announce('Settings changed. Simulate to update results.');
  $('insight').textContent='Settings changed. Select Simulate scenario to update the displayed results.';
}
async function loadProfile(){
  const load=++profileRequest;
  ++requestNumber;
  setBusy(true);
  try{
    error('');
    const selected=$('profile').value;
    const data=selected==='imported'?{observations:importedRows,name:importedName}:await api('/api/demo/'+selected);
    if(load!==profileRequest)return;
    observations=data.observations;
    setMeta(data.name,selected!=='imported');
    if(selected==='imported')$('data-chip').textContent=importedSource;
    await simulate();
  }catch(e){if(load===profileRequest){result=null;error(e.message);setBusy(false);}}
}
async function simulate(){
  if(!observations.length)return;
  const seq=++requestNumber;
  setBusy(true);error('');announce('Running simulation');
  const scenario=scenarioInputs(),confidence=Number($('confidence').value),horizon=Number($('horizon').value);
  const snapshot={observations:observations.map(o=>({...o})),profile:activeName,source:$('data-chip').textContent};
  try{
    const data=await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({observations:snapshot.observations,scenario,horizon,confidence})});
    if(seq!==requestNumber)return;
    result={...data,scenario,profile:snapshot.profile,source:snapshot.source,generated_at:new Date().toISOString()};
    render();announce('Simulation complete');
  }catch(e){if(seq===requestNumber){result=null;error(e.message);announce('Simulation failed');}}
  finally{if(seq===requestNumber)setBusy(false);}
}
function render(){const r=result,last=r.forecast.at(-1),v=r.validation;for(const [id,value] of Object.entries({current:r.current.toFixed(1),projected:last.scenario.toFixed(1),delta:(r.delta>0?'+':'')+r.delta.toFixed(1)+' mmHg',mae:v.twin_mae.toFixed(2),'metric-day':r.forecast.length,'effect-day':r.forecast.length,'twin-error':v.twin_mae.toFixed(2)+' mmHg','persistence-error':v.persistence_mae.toFixed(2)+' mmHg','mean-error':v.mean_baseline_mae.toFixed(2)+' mmHg'}))$(id).textContent=value;
$('test-label').textContent=v.test_days+' held-out days · '+v.train_days+' training days';$('validation-info').textContent='Trained on the first '+v.train_days+' days; evaluated on the next '+v.test_days+'. No held-out BP readings enter the fit.';$('coverage').textContent=r.confidence+'% interval coverage: '+(v.interval_coverage*100).toFixed(0)+'% on '+v.test_days+' held-out observations. Small synthetic samples do not establish clinical calibration.';
$('insight').textContent='At day '+r.forecast.length+', this scenario models '+Math.abs(r.delta).toFixed(1)+' mmHg '+(r.delta<=0?'lower':'higher')+' systolic pressure than unchanged habits. The predictive interval is '+last.lower.toFixed(1)+'–'+last.upper.toFixed(1)+' mmHg. This is a hypothesis to explore, not a promised outcome.';
$('effects').replaceChildren();const max=Math.max(1,...r.effects.map(e=>Math.abs(e.change)));r.effects.forEach(e=>{const row=document.createElement('div');row.className='effect';const label=document.createElement('span');label.textContent=names[e.feature];const track=document.createElement('div');track.className='effect-track';const fill=document.createElement('div');fill.className='effect-fill';fill.style.width=(Math.abs(e.change)/max*100)+'%';if(e.change>0)fill.style.background='#c79b7c';track.append(fill);const value=document.createElement('span');value.className='effect-value';value.textContent=(e.change>0?'+':'')+e.change.toFixed(2)+' mmHg';row.append(label,track,value);$('effects').append(row);});$('warnings').replaceChildren(...r.warnings.map(w=>{const li=document.createElement('li');li.textContent=w;return li;}));$('interval-label').textContent=r.confidence+'%';drawChart();if(typeof renderResearch==='function')renderResearch();}
function drawChart(){const history=observations.slice(-30),f=result.forecast,n=history.length+f.length;const width=660,height=300,p={l:35,r:10,t:25,b:30};const all=[...history.map(o=>o.sbp),...f.flatMap(o=>[o.lower,o.upper,o.baseline])];const low=Math.floor((Math.min(...all)-3)/10)*10,high=Math.ceil((Math.max(...all)+3)/10)*10;const x=i=>p.l+i/(n-1)*(width-p.l-p.r),y=v=>p.t+(high-v)/(high-low)*(height-p.t-p.b);const path=arr=>arr.map(([a,b],i)=>(i?'L':'M')+x(a).toFixed(2)+','+y(b).toFixed(2)).join(' ');let svg=`<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg"><title>Blood pressure history and conditional scenario forecast</title><desc>Current model ${result.current} mmHg. Day ${f.length} scenario ${f.at(-1).scenario} mmHg, predictive interval ${f.at(-1).lower} to ${f.at(-1).upper}.</desc>`;for(let v=low;v<=high;v+=10)svg+=`<line x1="${p.l}" x2="${width-p.r}" y1="${y(v)}" y2="${y(v)}" stroke="#edf0e9"/><text x="${p.l-9}" y="${y(v)+3}" text-anchor="end" fill="#92a093" font-size="9">${v}</text>`;const boundary=x(history.length-1);svg+=`<line x1="${boundary}" x2="${boundary}" y1="${p.t}" y2="${height-p.b}" stroke="#c5d3bd" stroke-dasharray="3 4"/><text x="${boundary+7}" y="15" fill="#84977d" font-size="9">SIMULATION →</text>`;const area=[...f.map((o,i)=>[history.length+i,o.upper]),...f.map((o,i)=>[history.length+i,o.lower]).reverse()];svg+=`<path d="${path(area)} Z" fill="#dcebd1" opacity=".7"/><path d="${path(history.map((o,i)=>[i,o.sbp]))}" fill="none" stroke="#8ca99a" stroke-width="2"/><path d="${path(f.map((o,i)=>[history.length+i,o.baseline]))}" fill="none" stroke="#ba9279" stroke-width="1.5" stroke-dasharray="5 5"/><path d="${path(f.map((o,i)=>[history.length+i,o.scenario]))}" fill="none" stroke="#13765b" stroke-width="3"/><circle cx="${x(n-1)}" cy="${y(f.at(-1).scenario)}" r="4" fill="#13765b"/>`;[[0,'−'+(history.length-1)+' days'],[history.length-1,'Today'],[n-1,'Day '+f.length]].forEach(([i,label])=>{svg+=`<text x="${x(i)}" y="${height-8}" text-anchor="${i===0?'start':i===n-1?'end':'middle'}" fill="#8b9b90" font-size="9">${label}</text>`;});$('chart').innerHTML=svg+'</svg>';}
function download(content,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('scenario-form').addEventListener('submit',e=>{e.preventDefault();simulate();});keys.forEach(k=>$(k).addEventListener('input',()=>{labels();markDirty();}));$('profile').addEventListener('change',loadProfile);$('horizon').addEventListener('change',simulate);$('confidence').addEventListener('change',simulate);
$('reset').addEventListener('click',()=>{if(!result)return;keys.forEach(k=>{$(k).value=result.baseline_inputs[k];});labels();simulate();});
$('export').addEventListener('click',()=>{if(result)download(JSON.stringify({...result,observations},null,2),'pulsetwin-report.json','application/json');});
$('download-data').addEventListener('click',()=>{if(!observations.length)return;const fields=['date','sbp',...keys];download(fields.join(',')+'\n'+observations.map(o=>fields.map(k=>o[k]).join(',')).join('\n')+'\n','pulsetwin-observations.csv','text/csv');});
$('upload').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>150000)throw new Error('CSV must be under 150 KB.');const data=await api('/api/import',{method:'POST',headers:{'Content-Type':'text/plain'},body:await file.text()});observations=data.observations;importedRows=observations;importedName='Imported observations';importedSource='IMPORTED DATA';let opt=$('profile').querySelector('[value="imported"]');if(!opt){opt=document.createElement('option');opt.value='imported';$('profile').append(opt);}opt.textContent='Imported observations';$('profile').value='imported';setMeta('Imported observations',false);await simulate();}catch(err){error(err.message);}finally{e.target.value='';}});
labels();
// features.js restores shared settings before the first profile is loaded.
