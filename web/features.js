'use strict';
const LIBRARY_KEY='pulsetwin-scenarios-v1';
let library=[], pinnedScenario=null, comparisonGeneration=0, comparisonResult=null;
const units={steps:'steps',sleep:'hours',sodium:'mg',stress:'/ 10'};
const signed=n=>(n>0?'+':'')+Number(n).toFixed(2);
function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function postAnalysis(rows,settings){return api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({observations:rows,...settings})});}
function settingsFromResult(){return {scenario:{...result.scenario},horizon:result.forecast.length,confidence:result.confidence};}
function validateSettings(value){
  if(!value||typeof value!=='object'||![14,28,56,90].includes(value.horizon)||![80,90,95,99].includes(value.confidence))throw new Error('Invalid scenario settings.');
  const scenario={};
  keys.forEach(k=>{const v=value.scenario?.[k],input=$(k);if(typeof v!=='number'||!Number.isFinite(v)||v<Number(input.min)||v>Number(input.max))throw new Error('Invalid '+k+' scenario value.');scenario[k]=v;});
  return {scenario,horizon:value.horizon,confidence:value.confidence};
}
function applySettings(settings){const safe=validateSettings(settings);keys.forEach(k=>$(k).value=safe.scenario[k]);$('horizon').value=safe.horizon;$('confidence').value=safe.confidence;labels();}
function metrics(container,items){container.replaceChildren(...items.map(([value,label])=>{const div=node('div');div.append(node('strong',value),node('span',label));return div;}));}
function plot(container,series,xLabels,description){
  const values=series.flatMap(s=>s.values);if(!values.length){container.textContent='No valid observed range within scenario bounds.';return;}
  const width=460,height=200,pad={l:36,r:14,t:15,b:32};
  const lo=Math.floor(Math.min(...values)-2),hi=Math.ceil(Math.max(...values)+2);
  const count=Math.max(...series.map(s=>s.values.length));
  const x=i=>pad.l+i/Math.max(1,count-1)*(width-pad.l-pad.r),y=v=>pad.t+(hi-v)/(hi-lo)*(height-pad.t-pad.b);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',description);
  function part(type,attrs,text){const n=document.createElementNS(svg.namespaceURI,type);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);}
  for(let i=0;i<3;i++){const v=lo+(hi-lo)*i/2;part('line',{x1:pad.l,x2:width-pad.r,y1:y(v),y2:y(v),stroke:'#e2e8e1'});part('text',{x:pad.l-5,y:y(v)+3,'text-anchor':'end',fill:'#687b74','font-size':9},v.toFixed(0));}
  series.forEach(s=>part('path',{d:s.values.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(' '),fill:'none',stroke:s.color,'stroke-width':2.5}));
  part('text',{x:pad.l,y:height-8,fill:'#687b74','font-size':9},xLabels[0]);
  part('text',{x:width-pad.r,y:height-8,fill:'#687b74','font-size':9,'text-anchor':'end'},xLabels[1]);
  container.replaceChildren(svg);
}
function refreshLibrary(selected=''){
  const sel=$('saved-scenarios');sel.replaceChildren();
  if(!library.length){const opt=node('option','No saved scenarios');opt.value='';sel.append(opt);}
  library.forEach(entry=>{const opt=node('option',entry.name);opt.value=entry.id;sel.append(opt);});
  if(selected)sel.value=selected;
  $('load-scenario').disabled=$('delete-scenario').disabled=!library.length;
}
function persistLibrary(next){
  try{localStorage.setItem(LIBRARY_KEY,JSON.stringify(next));library=next;return true;}
  catch(e){$('library-status').textContent='Browser storage is unavailable or full. No changes were saved.';return false;}
}
try{
  const saved=JSON.parse(localStorage.getItem(LIBRARY_KEY)||'[]');
  if(!Array.isArray(saved)||saved.length>8)throw new Error('Invalid library');
  library=saved.map(e=>{if(typeof e.name!=='string'||!e.name.trim()||e.name.length>40||typeof e.id!=='string')throw new Error('Invalid library');return {id:e.id,name:e.name,settings:validateSettings(e.settings)};});
}catch(e){$('library-status').textContent='Saved settings could not be read. The observation workflow remains available.';}
refreshLibrary();
$('save-scenario').addEventListener('click',()=>{
  if(!result)return;
  const name=$('scenario-name').value.trim();
  if(!name){$('library-status').textContent='Enter a generic name first.';return;}
  if(library.length>=8){$('library-status').textContent='Eight scenarios are saved. Delete one before adding another.';return;}
  const entry={id:crypto.randomUUID(),name,settings:settingsFromResult()};
  if(persistLibrary([...library,entry])){refreshLibrary(entry.id);$('library-status').textContent='Settings saved on this browser only.';$('scenario-name').value='';}
});
$('load-scenario').addEventListener('click',()=>{const selected=library.find(e=>e.id===$('saved-scenarios').value);if(selected){applySettings(selected.settings);simulate();}});
$('delete-scenario').addEventListener('click',()=>{if(persistLibrary(library.filter(e=>e.id!==$('saved-scenarios').value))){refreshLibrary();$('library-status').textContent='Selected settings deleted.';}});
$('pin-scenario').addEventListener('click',()=>{if(result){pinnedScenario={...result.scenario};refreshComparison();}});
async function refreshComparison(){
  const generation=++comparisonGeneration,analysisGeneration=requestNumber;
  comparisonResult=null;
  if(!pinnedScenario||!result)return;
  const current=result;
  $('comparison').replaceChildren(node('p','Recomputing both scenarios against this history…','subtle'));
  try{
    const reference=await postAnalysis(observations,{scenario:pinnedScenario,horizon:current.forecast.length,confidence:current.confidence});
    if(generation!==comparisonGeneration||analysisGeneration!==requestNumber)return;
    comparisonResult=reference;
    const box=$('comparison');box.replaceChildren();
    const summary=node('div',undefined,'mini-metrics');metrics(summary,[[reference.forecast.at(-1).scenario.toFixed(1),'Reference · mmHg'],[current.forecast.at(-1).scenario.toFixed(1),'Current · mmHg'],[signed(current.forecast.at(-1).scenario-reference.forecast.at(-1).scenario),'Current − reference']]);box.append(summary);
    const chart=node('div');plot(chart,[{values:reference.forecast.map(r=>r.scenario),color:'#ba9279'},{values:current.forecast.map(r=>r.scenario),color:'#13765b'}],['Day 1','Day '+current.forecast.length],'Reference and current scenario means');box.append(chart);
    box.append(node('p','Reference: brown · Current: green. Same history, horizon and interval. Difference of conditional means, not a treatment-effect estimate.','footnote'));
    box.append(node('p','Reference settings: '+keys.map(k=>names[k]+' '+pinnedScenario[k]+' '+units[k]).join(' · '),'comparison-detail'));
  }catch(e){if(generation===comparisonGeneration)$('comparison').replaceChildren(node('p','Comparison unavailable: '+e.message,'subtle'));}
}
function renderResearch(){
  const r=result,q=r.quality,t=r.trend,d=r.diagnostics;
  $('quality-summary').textContent=`${q.rows} consecutive daily records validated · ${q.flags.length} review flags · ${q.correlated_features.length} highly correlated input pairs.`;
  const flags=q.flags.map(f=>(f.date?f.date+' — ':'')+f.detail);
  q.correlated_features.forEach(c=>flags.push(`${names[c.first]} / ${names[c.second]} correlation ${c.correlation}: individual coefficients may be difficult to separate.`));
  $('quality-flags').replaceChildren(...(flags.length?flags:['No review flags from these heuristics. This is not a clinical quality certification.']).map(v=>node('li',v)));
  metrics($('trend-stats'),[[t.recent_week.toFixed(1),'Last 7 days · mmHg'],[signed(t.weekly_change),'vs previous week'],[t.recent_sd.toFixed(2),'28-day SD · mmHg']]);
  plot($('trend-chart'),[{values:t.rolling_mean.map(v=>v.mean),color:'#13765b'}],[t.rolling_mean[0].date,t.rolling_mean.at(-1).date],'Seven-day rolling mean SBP');
  $('trend-context').textContent=`Descriptive slope over ${t.window_days} days: ${signed(t.slope_per_day)} mmHg/day. These historical trends do not attribute a cause or predict an outcome.`;
  metrics($('diagnostic-stats'),[[signed(d.bias),'Bias · mmHg'],[d.rmse.toFixed(2),'RMSE · mmHg'],[d.max_error.toFixed(2),'Largest error · mmHg']]);
  $('residual-table').replaceChildren(...d.residuals.map(row=>{const tr=node('tr');[row.date,row.actual.toFixed(1),row.predicted.toFixed(1),signed(row.residual)].forEach(v=>tr.append(node('td',v)));return tr;}));
  const f=r.forecast.at(-1);$('uncertainty-summary').textContent=`Current level: ${r.confidence}%. Day ${f.day} predictive interval: ${f.lower.toFixed(1)}–${f.upper.toFixed(1)} mmHg, width ${(f.upper-f.lower).toFixed(1)} mmHg. Holdout coverage: ${(r.validation.interval_coverage*100).toFixed(0)}% of ${r.validation.test_days} observations.`;
  const last=observations.at(-1),next=new Date(last.date+'T00:00:00Z');next.setUTCDate(next.getUTCDate()+1);$('obs-date').value=next.toISOString().slice(0,10);
  keys.forEach(k=>$('obs-'+k).value=last[k]);$('append-observation').disabled=observations.length>=730;
  $('share-link').value='';renderSensitivity();refreshComparison();buildPrintReport();
}
function renderSensitivity(){
  if(!result)return;const s=result.sensitivity.find(s=>s.feature===$('sensitivity-feature').value);
  plot($('sensitivity-chart'),[{values:s.points.map(p=>p.prediction),color:'#13765b'}],s.points.length?[String(s.points[0].input),String(s.points.at(-1).input)]:['',''],'Conditional SBP response to '+names[s.feature]);
  const precision=s.feature==='steps'||s.feature==='sodium'?5:3;
  $('sensitivity-summary').textContent=`Personal association per ${units[s.feature]}: ${s.slope.toFixed(precision)} mmHg (95% coefficient interval ${s.slope_lower.toFixed(precision)} to ${s.slope_upper.toFixed(precision)}). Curve shows day ${result.forecast.length} SBP in mmHg.`;
}
$('sensitivity-feature').addEventListener('change',renderSensitivity);
$('observation-form').addEventListener('submit',async e=>{
  e.preventDefault();if(!observations.length)return;
  const button=$('append-observation');button.disabled=true;
  const generation=requestNumber,oldRows=observations,oldCurrent=result?.current;
  const row={date:$('obs-date').value,sbp:Number($('obs-sbp').value),...Object.fromEntries(keys.map(k=>[k,Number($('obs-'+k).value)]))};
  try{
    const rows=[...oldRows,row];
    await postAnalysis(rows,{scenario:scenarioInputs(),horizon:Number($('horizon').value),confidence:Number($('confidence').value)});
    if(generation!==requestNumber){$('update-summary').textContent='The active analysis changed. Add the observation again to the intended history.';return;}
    importedRows=observations=rows;importedName='Updated observations';importedSource='SESSION DATA';let opt=$('profile').querySelector('[value="imported"]');
    if(!opt){opt=node('option','Updated observations');opt.value='imported';$('profile').append(opt);}else opt.textContent='Updated observations';
    $('profile').value='imported';setMeta('Updated observations',false);$('data-chip').textContent='SESSION DATA';
    await simulate();$('obs-sbp').value='';
    $('update-summary').textContent=result?`${row.date} added. History: ${rows.length} days. Modeled current SBP: ${oldCurrent?.toFixed(1)??'—'} → ${result.current.toFixed(1)} mmHg. Export CSV to retain this session history.`:'Observation added; analysis failed. Retry simulation.';
  }catch(err){$('update-summary').textContent=err.message;}
  finally{button.disabled=observations.length>=730;}
});
$('share-scenario').addEventListener('click',async()=>{
  if(!result)return;
  const url=new URL(location.href);url.hash='scenario='+encodeURIComponent(JSON.stringify({v:1,...settingsFromResult()}));
  $('share-link').value=url.href;
  try{await navigator.clipboard.writeText(url.href);$('share-status').textContent='Settings link copied. No observations or identity included. A local address requires this app on the recipient’s machine.';}
  catch(e){$('share-link').select();$('share-status').textContent='Select and copy the link above. Only scenario settings are included.';}
});
function buildPrintReport(){
  if(!result)return;const r=result,f=r.forecast.at(-1),box=$('print-report');box.replaceChildren();
  box.append(node('h1','PulseTwin · Research report'),node('p','Team Gimites · Yashwanth M (leader), Kalashikam Vijay Krishna, Subiksha K, Shakthi K'),node('p',`${r.profile} · ${r.source} · Model ${r.model_version} · ${r.generated_at}`),node('p','Research simulation only. Not diagnosis, treatment advice, or clinical validation. Conditional associations are not causal effects.','report-warning'));
  function section(title,rows){box.append(node('h2',title));const table=node('table');rows.forEach(([k,v])=>{const tr=node('tr');tr.append(node('th',k),node('td',v));table.append(tr);});box.append(table);}
  section('Observation history',[['Period',observations[0].date+' to '+observations.at(-1).date],['Daily records',String(observations.length)],['Current modeled SBP',r.current.toFixed(2)+' mmHg']]);
  section('Hypothetical scenario',[...keys.map(k=>[names[k],r.scenario[k]+' '+units[k]]),['Horizon',r.forecast.length+' days'],['Projected SBP',f.scenario.toFixed(2)+' mmHg'],[r.confidence+'% predictive interval',f.lower.toFixed(2)+'–'+f.upper.toFixed(2)+' mmHg'],['Difference vs unchanged habits',signed(r.delta)+' mmHg']]);
  section('Chronological holdout',[['Training / test',r.validation.train_days+' / '+r.validation.test_days+' days'],['Twin MAE',r.validation.twin_mae+' mmHg'],['Training-mean MAE',r.validation.mean_baseline_mae+' mmHg'],['Last-reading MAE',r.validation.persistence_mae+' mmHg'],['Interval coverage',(r.validation.interval_coverage*100).toFixed(0)+'%'],['RMSE / bias',r.diagnostics.rmse+' / '+r.diagnostics.bias+' mmHg']]);
  box.append(node('h2','Data review and boundaries'),node('p',`${r.quality.flags.length} heuristic flags; ${r.quality.correlated_features.length} highly correlated pairs. No observations removed. Holdout habits are known inputs; this is not prospective validation.`));
  const list=node('ul');[...r.quality.flags.map(x=>x.detail),...r.warnings].forEach(w=>list.append(node('li',w)));box.append(list);
}
$('print-report-button').addEventListener('click',()=>{buildPrintReport();window.print();});
let sharedError='';
try{
  if(location.hash.startsWith('#scenario=')){
    if(location.hash.length>3000)throw new Error('Shared settings are too long.');
    const settings=JSON.parse(decodeURIComponent(location.hash.slice(10)));
    if(settings.v!==1)throw new Error('Unsupported settings version.');
    applySettings(settings);$('share-status').textContent='Shared settings loaded. Applied to the active demo; no observations were shared.';
  }
}catch(e){sharedError='Shared settings rejected: '+e.message;}
loadProfile().then(()=>{if(sharedError)error(sharedError);});
// A settings link can be opened in the already-running tab as a fragment change.
window.addEventListener('hashchange',()=>{
  if(!location.hash.startsWith('#scenario='))return;
  try{
    if(location.hash.length>3000)throw new Error('Shared settings are too long.');
    const settings=JSON.parse(decodeURIComponent(location.hash.slice(10)));
    if(settings.v!==1)throw new Error('Unsupported settings version.');
    applySettings(settings);simulate();
  }catch(e){error('Shared settings rejected: '+e.message);}
});
