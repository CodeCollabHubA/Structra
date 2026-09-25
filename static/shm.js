'use strict';
let shmRequest = 0;
let shmData = null;
let shmSaving = false;

const shmStepNames = ['Observe', 'Review', 'Inspect', 'Maintain'];
const shmNextLabels = ['Simulate a signal change', 'Record demo inspection', 'Record demo maintenance'];

async function renderSHM() {
  if (!state.detail) return;
  const id = state.detail.building.id;
  const request = ++shmRequest;
  shmData = null;
  shmSaving = false;
  $('#view-shm').innerHTML = '<div class="empty-state">Loading structural monitoring scenario…</div>';
  try {
    const data = await api(`/api/buildings/${id}/shm`);
    if (request !== shmRequest || state.detail.building.id !== id) return;
    shmData = data;
    renderSHMContent();
    renderSHMPassportSummary();
  } catch (error) {
    if (request !== shmRequest || state.detail.building.id !== id) return;
    $('#view-shm').innerHTML = `<div class="empty-state"><p>${escapeHTML(error.message)}</p><button class="button secondary" id="shm-retry">Retry monitoring</button></div>`;
  }
}

function shmSignalChart(channel) {
  const values = channel.history;
  const min = Math.min(...values) * .85;
  const max = Math.max(...values) * 1.1;
  const points = values.map((value, i) => `${10+i*260/(values.length-1)},${61-(value-min)/(max-min||1)*49}`).join(' ');
  return `<svg class="shm-sparkline" viewBox="0 0 280 76" role="img" aria-label="${escapeHTML(channel.label)}: synthetic trend over 12 illustrative observations"><path d="M10 62H270"/><polyline points="${points}"/><text x="10" y="75">Earlier</text><text x="270" y="75" text-anchor="end">Latest</text></svg>`;
}

function shmDiagram(stage) {
  return `<svg class="shm-building" viewBox="0 0 400 290" role="img" aria-label="Conceptual building monitoring diagram with three simulated channels; not an engineering model"><path class="shm-ground" d="M30 259h345"/><path class="shm-structure" d="M100 255V68l115-41 90 41v187M215 27v228M100 68l115 42 90-42M100 105l115 42 90-42M100 142l115 42 90-42M100 179l115 42 90-42M100 216l115 42M130 58v198m28-208v208m28-218v218m58-216v207m30-195v196"/><g class="shm-node ${stage>0?'shm-node-review':''}"><circle cx="130" cy="116" r="12"/><circle cx="130" cy="116" r="4"/></g><g class="shm-node"><circle cx="243" cy="158" r="12"/><circle cx="243" cy="158" r="4"/></g><g class="shm-node"><circle cx="186" cy="51" r="12"/><circle cx="186" cy="51" r="4"/></g><path class="shm-leader" d="M117 116H51m204 42h70M186 38V15"/><text x="28" y="104">V1</text><text x="326" y="147">C1</text><text x="193" y="17">T1</text><text x="200" y="281" text-anchor="middle">CONCEPTUAL SENSOR LOCATIONS</text></svg>`;
}

function renderSHMContent() {
  const data = shmData;
  if (!data || data.building_id !== state.detail.building.id) return;
  const building = state.detail.building;
  const active = data.stage;
  $('#view-shm').innerHTML = `
    <div class="shm-intro"><span>STRUCTRA CORE / STRUCTURAL HEALTH MONITORING</span><p>Monitor the structure. Record the intervention. Connect it to the building’s wider footprint.</p></div>
    <div class="shm-layout">
      <section class="shm-twin"><div class="shm-twin-title"><div><span class="eyebrow">BUILDING MONITORING CONCEPT</span><h2>${escapeHTML(building.name)}</h2></div><span class="shm-sim-badge">SIMULATED</span></div>${shmDiagram(active)}<div class="shm-twin-foot"><span>3 illustrative channels</span><span>ST-${String(building.id).padStart(4,'0')}</span></div></section>
      <section class="panel shm-scenario"><div class="panel-heading"><div><h2>One connected building story</h2><p>Step ${active+1} of 4 · Saved with this building</p></div>${icon('pulse')}</div><div class="shm-stepper">${shmStepNames.map((name,i)=>`<div class="${i<=active?'done':''}"><span>${i+1}</span><small>${name}</small></div>`).join('')}</div><span class="shm-stage-label">${escapeHTML(data.stage_label)}</span><h3>${['The baseline starts the story.','A change needs context.','A human decision connects the data.','The intervention becomes part of the record.'][active]}</h3><p class="shm-story">${escapeHTML(data.story)}</p><div class="shm-scenario-actions">${active<3?`<button class="button primary" id="shm-next" data-stage="${active+1}" ${shmSaving?'disabled':''}>${shmNextLabels[active]} ${icon('arrow')}</button>`:`<button class="button primary" data-go="simulator">Explore operational upgrades ${icon('arrow')}</button>`}${active>0?`<button class="text-button" id="shm-reset" ${shmSaving?'disabled':''}>Reset SHM scenario</button>`:''}</div><p class="shm-save-status" id="shm-save-status" role="status" aria-live="polite">${shmSaving?'Saving demo step…':'Fictional workflow · No live sensor connection'}</p></section>
    </div>
    <div class="section-heading"><div><h2>Signals, with their context</h2><p>Invented readings for demonstration. No structural acceptance limits are applied.</p></div><span class="mini-badge">12 ILLUSTRATIVE OBSERVATIONS</span></div>
    <div class="shm-signals">${data.channels.map(channel=>`<article class="panel shm-signal"><div class="shm-channel-name">${icon('pulse')}<h3>${escapeHTML(channel.label)}</h3></div><p>${escapeHTML(channel.id)} · ${escapeHTML(channel.location)}</p><div class="shm-reading">${num(channel.current,3)}<small>${escapeHTML(channel.unit)}</small></div><div class="shm-reference">Scenario reference: ${num(channel.baseline,3)} ${escapeHTML(channel.unit)}</div>${shmSignalChart(channel)}</article>`).join('')}</div>
    <div class="shm-bottom-grid"><section class="panel"><div class="panel-heading"><div><h2>Inspection & maintenance trail</h2><p>Scripted demo records, stored per building</p></div></div><ol class="shm-events">${data.events.map(event=>`<li><div><b>${escapeHTML(event.title)}</b><span>${escapeHTML(event.status)}</span></div><p>${escapeHTML(event.note)}</p></li>`).join('')}</ol></section><section class="shm-connection"><span class="eyebrow">THE SUSTAINABILITY CONNECTION</span><h2>Care for the structure.<br>Improve how it operates.</h2><p>The SHM story supports informed maintenance and a record of what was reviewed. The sustainability scenario explores energy, water and operational improvements.</p><div class="shm-connection-path"><span>Monitoring evidence</span><span>Inspection & work record</span><span>One Building Passport</span></div><p class="shm-small">A future repair-versus-replacement comparison needs verified material quantities and carbon factors. This demo makes no quantified claim about material savings or longer building life.</p><button class="button secondary" data-go="passport">View connected passport ${icon('arrow')}</button></section></div>
    <div class="shm-boundary">${escapeHTML(data.disclaimer)} The sustainability score is not a structural safety rating. Advancing this workflow does not change utility readings or the sustainability score.</div>`;
}

function renderSHMPassportSummary() {
  const data = shmData;
  const target = $('#passport-shm-summary');
  if (!target || !data || data.building_id !== state.detail.building.id) return;
  target.innerHTML = `<div class="shm-passport-summary"><div>${icon('pulse')}<h3>Structra structural monitoring</h3><span>SIMULATED</span></div><strong>${escapeHTML(data.stage_label)}</strong><p>${escapeHTML(data.story)}</p><button class="text-button" data-go="shm">Review monitoring & maintenance trail ↗</button><small>Recorded alongside the sustainability profile; not a structural safety assessment.</small></div>`;
}

async function saveSHMStage(stage) {
  if (shmSaving || !state.detail || !shmData) return;
  const id = state.detail.building.id;
  const request = ++shmRequest;
  shmSaving = true;
  renderSHMContent();
  try {
    const data = await api(`/api/buildings/${id}/shm`, {method:'POST',body:JSON.stringify({stage})});
    if (request !== shmRequest || state.detail.building.id !== id) return;
    shmData = data;
    renderSHMPassportSummary();
  } catch (error) {
    if (request === shmRequest && state.detail.building.id === id) notify(error.message,true);
  } finally {
    if (request === shmRequest && state.detail.building.id === id) {
      shmSaving = false;
      renderSHMContent();
    }
  }
}

document.addEventListener('click', event => {
  const next = event.target.closest('#shm-next');
  if (next) saveSHMStage(Number(next.dataset.stage));
  if (event.target.closest('#shm-reset')) saveSHMStage(0);
  if (event.target.closest('#shm-retry')) renderSHM();
});
