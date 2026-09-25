'use strict';

// Read-only portfolio summary. This does not connect to municipal systems.
function renderCivic() {
  const buildings = state.buildings;
  const sum = field => buildings.reduce((total, b) => total + b.analysis.totals[field], 0);
  const area = buildings.reduce((total, b) => total + b.floor_area_m2, 0);
  const months = buildings.reduce((total, b) => total + b.analysis.month_count, 0);
  $('#view-civic').innerHTML = `
    <div class="civic-hero">
      <div class="civic-badge">PROPOSED MUNICIPAL PILOT · UAE</div>
      <h2>One passport.<br>A city of possibilities.</h2>
      <p>Help building owners understand their footprint. Give participating municipalities a consistent picture of progress.</p>
      <div class="civic-hero-foot"><span>DUBAI</span><span>ABU DHABI</span><span>VOLUNTARY PARTICIPATION</span></div>
      <svg class="civic-skyline" viewBox="0 0 320 220" aria-hidden="true"><path d="M0 219h320M35 219V95h37v124M42 106h23m-23 15h23m-23 15h23m-23 15h23m-23 15h23M100 219V64h32v155m-20-155V34h8v30m-5-30V6m32 213V88l28-22 29 22v131M147 98h57m-57 19h57m-57 19h57m-57 19h57m-57 19h57M230 219V112h54v107m-44-94h34m-34 17h34m-34 17h34m-34 17h34m-34 17h34M16 219v-28m0 3c-20 0-17-25 0-36 18 11 21 36 0 36"/></svg>
    </div>
    <div class="section-heading"><div><h2>A portfolio view that starts with evidence</h2><p>Live totals from this fictional demo portfolio. These are not municipal statistics.</p></div></div>
    <div class="stats-grid">
      ${stat('Participating examples',num(buildings.length),'buildings','Fictional UAE properties','building')}
      ${stat('Combined floor area',num(area),'m²','Recorded in building profiles','grid')}
      ${stat('Annual grid electricity',num(sum('electricity_kwh')/1000),'MWh','Sample baseline consumption','energy')}
      ${stat('Monthly data coverage',num(months),'records',`${num(buildings.length*12)} expected records across the portfolio`,'data')}
    </div>
    <div class="section-heading"><div><h2>Local context. A shared ambition.</h2><p>Official sustainability references for proposed collaboration.</p></div><span class="mini-badge">PUBLIC RESOURCES</span></div>
    <div class="civic-authorities">
      <article class="civic-authority"><div class="civic-authority-label">01 / DUBAI</div><div class="civic-authority-title">${icon('civic')}<h3>Dubai Municipality</h3></div><p>Explore the Al Sa’fat Dubai Green Building System as a public reference for the emirate’s approach to sustainable buildings.</p><a href="https://www.dm.gov.ae/municipality-business/al-safat-dubai-green-building-system/" target="_blank" rel="noopener noreferrer">View official Al Sa’fat resource ↗</a><small>Proposed collaboration · No endorsement claimed</small></article>
      <article class="civic-authority"><div class="civic-authority-label">02 / ABU DHABI</div><div class="civic-authority-title">${icon('civic')}<h3>Abu Dhabi City Municipality</h3></div><p>Explore the municipality’s sustainable building guidance and its explanation of the Estidama Pearl Rating System.</p><a href="https://www.dmt.gov.ae/en/adm/Media-Centre/News/08Jan2025" target="_blank" rel="noopener noreferrer">View official sustainable building resource ↗</a><small>Proposed collaboration · No endorsement claimed</small></article>
    </div>
    <div class="civic-context-note">Structra’s demo score is independent. It does not calculate Al Sa’fat or Estidama compliance or replace a municipal assessment. Official links require internet; the demo itself works offline.</div>
    <div class="section-heading"><div><h2>A practical path to a pilot</h2><p>Proposed next steps, subject to a municipality’s agreement.</p></div></div>
    <div class="civic-steps"><article><span>01</span><h3>Agree the evidence</h3><p>Define reporting fields, owner consent, privacy rules and appropriate benchmarks with municipal stakeholders.</p></article><article><span>02</span><h3>Start with willing owners</h3><p>Run a small voluntary cohort using utility and maintenance records. Validate data before making decisions.</p></article><article><span>03</span><h3>Measure what changes</h3><p>Track completed actions, verified resource use and data completeness. Compare normalized results over time.</p></article></div>
    <div class="panel civic-table"><div class="panel-heading"><div><h2>Demo portfolio at a glance</h2><p>2025 baseline · Scores use illustrative building-type benchmarks</p></div></div><div class="table-wrap"><table><thead><tr><th>Building / city</th><th>Type</th><th>Demo score</th><th>Grid electricity<small>kWh/m²/year</small></th><th>Coverage</th></tr></thead><tbody>${buildings.map(b=>`<tr><td><b>${escapeHTML(b.name)}</b><small>${escapeHTML(b.city)}</small></td><td>${escapeHTML(b.building_type)}</td><td><span class="civic-score">${b.analysis.scores.overall}</span> / 100</td><td>${num(b.analysis.metrics.energy_intensity,1)}</td><td>${b.analysis.month_count} / 12</td></tr>`).join('')}</tbody></table></div></div>
    <div class="civic-patronage"><div>${icon('health')}<strong>Patronage & partnership</strong></div><p>Proposed, pending agreement. No municipal endorsement, sponsorship or live municipal data connection is represented in this prototype.</p><a href="https://dmt.gov.ae/en" target="_blank" rel="noopener noreferrer">Department of Municipalities and Transport ↗</a></div>`;
}

function intelligenceBrief(a) {
  const weakest = Object.keys(scoreNames).reduce((key, next) => a.scores[next] < a.scores[key] ? next : key, 'energy');
  const brief = {
    energy: [num(a.metrics.energy_intensity,1)+' kWh/m²/year', 'Purchased electricity per square metre.', 'Review cooling schedules and lighting. Test demand reductions before considering solar offsets.', 'hvac'],
    water: [num(a.metrics.water_intensity,2)+' m³/m²/year', 'Water consumption per square metre.', 'Review water records and investigate possible leaks. Test an illustrative 18% reduction.', 'water'],
    waste: [num(a.metrics.recycling_rate,1)+'% recycled', 'Share of recorded waste diverted to recycling.', 'Review separation and collection. Waste changes are outside the five upgrade simulations.', null],
    health: [num(a.metrics.maintenance_completion,1)+'% tasks completed', 'Scheduled maintenance completion across the year.', 'Review overdue tasks and test preventive maintenance to improve the asset health component.', 'maintenance']
  }[weakest];
  return `<section class="intelligence-brief"><div class="intelligence-heading"><div><span class="intelligence-kicker">STRUCTRA INTELLIGENCE</span><h2>See the reasoning. Make the next move.</h2></div><span class="intelligence-badge">EXPLAINABLE RULES</span></div><div class="intelligence-steps"><div><span class="step-number">01 / OBSERVE</span><strong>${brief[0]}</strong><p>${brief[1]} Based on ${a.month_count} sample records.</p></div><div><span class="step-number">02 / INTERPRET</span><strong>${scoreNames[weakest]} · ${a.scores[weakest]}/100</strong><p>The lowest component score in this building’s illustrative profile.</p></div><div><span class="step-number">03 / ACT</span><strong>A practical starting point</strong><p>${brief[2]}</p></div></div><div class="intelligence-footer"><span>Deterministic recommendations · No live AI model</span>${brief[3]?`<button data-action="${brief[3]}">Test this action ${icon('arrow')}</button>`:`<button data-go="data">Review the records ${icon('arrow')}</button>`}</div></section>`;
}

// A single presenter action; individual controls remain fully editable.
document.addEventListener('click', event => {
  if (!event.target.closest('#apply-plan')) return;
  state.options = Object.fromEntries(options.map(option => [option.id, true]));
  renderSimulator();
  updateSimulation();
});
