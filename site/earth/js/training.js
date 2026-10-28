const $ = (id) => document.getElementById(id);
let worldsData = [];
const UNIONS = new Set();
const SECTORS = new Set();
const ROBOT_TYPES = new Set();

async function load() {
  const res = await fetch('worlds.json');
  worldsData = await res.json();
  
  worldsData.forEach(w => {
    const t = w.trades || {};
    (t.union_certifications || []).forEach(u => UNIONS.add(u));
    if (t.sector) SECTORS.add(t.sector);
    (t.robot_types || []).forEach(r => ROBOT_TYPES.add(r));
  });
  
  const us = $('f-union');
  UNIONS.forEach(u => { const o = document.createElement('option'); o.value = u; o.textContent = u; us.appendChild(o); });
  const ss = $('f-sector');
  SECTORS.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; ss.appendChild(o); });
  const rs = $('f-robot');
  ROBOT_TYPES.forEach(r => { const o = document.createElement('option'); o.value = r; o.textContent = r; rs.appendChild(o); });
  
  const live = worldsData.filter(w => w.status !== 'coming-soon');
  $('stats').textContent = live.length + ' Live Worlds · ' + UNIONS.size + ' Unions · ' + SECTORS.size + ' Sectors';
  
  const regions = [...new Set(worldsData.filter(w => w.region && w.region !== 'unknown').map(w => w.region))].sort();
  const nav = $('nav');
  const allBtn = document.createElement('button');
  allBtn.className = 'active'; allBtn.textContent = 'All';
  allBtn.onclick = () => { nav.querySelectorAll('button').forEach(b => b.classList.remove('active')); allBtn.classList.add('active'); render(); };
  nav.appendChild(allBtn);
  regions.forEach(r => {
    const btn = document.createElement('button'); btn.textContent = r;
    btn.onclick = () => { nav.querySelectorAll('button').forEach(b => b.classList.remove('active')); btn.classList.add('active'); render(r); };
    nav.appendChild(btn);
  });
  render();
}

function render(region) {
  let filtered = worldsData.filter(w => w.status !== 'coming-soon');
  if (region) filtered = filtered.filter(w => w.region === region);
  const uf = $('f-union').value;
  const sf = $('f-sector').value;
  const rf = $('f-robot').value;
  if (uf) filtered = filtered.filter(w => (w.trades?.union_certifications || []).includes(uf));
  if (sf) filtered = filtered.filter(w => w.trades?.sector === sf);
  if (rf) filtered = filtered.filter(w => (w.trades?.robot_types || []).includes(rf));
  
  const grid = $('grid');
  grid.innerHTML = '';
  filtered.forEach(w => {
    const t = w.trades || {};
    const r = w.robots || {};
    const scenarios = r.simulations || t.training_modules || [];
    const unions = t.union_certifications || [];
    const robots = t.robot_types || r.robot_types || [];
    const hours = t.training_hours || 80;
    const xp = hours * 10;
    
    const card = document.createElement('div');
    card.className = 'card';
    let html = '<h3>' + (w.name || w.slug) + '</h3><div class="meta">' + w.slug + ' · ' + hours + 'h · ' + xp + ' XP</div>';
    html += '<div>' + unions.map(u => '<span class="union">' + u + '</span>').join('') + '</div>';
    html += '<div class="meta">' + (t.sector || 'General') + ' · ' + (w.region || '') + '</div>';
    html += '<div class="robots">🤖 ' + (robots.join(', ') || 'Various') + '</div>';
    
    if (scenarios.length > 0) {
      const esc = (v) => String(v).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
      scenarios.slice(0, 5).forEach(s => {
        html += '<div class="scenario" data-slug="' + esc(w.slug) + '" data-s="' + esc(s) + '">' + esc(s) + '</div>';
      });
    }

    html += '<div class="xp">\u26a1 ' + xp + ' XP</div>';
    html += '<a href="world.html?world=' + w.slug + '" class="btn">Enter World</a>';
    card.innerHTML = html;
    card.addEventListener('click', (e) => {
      const d = e.target.closest('.scenario');
      if (d) openModule(d.dataset.slug, d.dataset.s);
    });
    grid.appendChild(card);
  });
}

function openModule(slug, scenario) {
  const w = worldsData.find(x => x.slug === slug);
  if (!w) return;
  const mp = $('mp');
  const mc = $('mc');
  const unions = w.trades?.union_certifications || [];
  const hours = w.trades?.training_hours || 80;
  
  let html = '<h2>' + (w.name || w.slug) + '</h2><div class="meta">' + scenario + '</div>';
  html += '<div class="meta">Union: ' + (unions.join(', ') || 'N/A') + '</div>';
  html += '<div class="meta">Sector: ' + (w.trades?.sector || 'General') + '</div>';
  html += '<div class="meta">Region: ' + (w.region || 'Unknown') + '</div>';
  html += '<div class="meta">Hours: ' + hours + 'h</div>';
  html += '<hr style="border-color:#1e333a;margin:16px 0"><h3>Training Steps</h3>';
  
  const steps = [
    { title: '1. Safety Briefing', desc: 'Review safety protocols for the training environment.' },
    { title: '2. Equipment Setup', desc: 'Configure ' + scenario + ' with proper calibration.' },
    { title: '3. Operation Simulation', desc: 'Run simulated operations in the environment.' },
    { title: '4. Performance Review', desc: 'Analyze metrics and identify improvements.' },
    { title: '5. Certification Prep', desc: 'Complete certification requirements.' }
  ];
  
  steps.forEach(s => {
    html += '<div class="step"><h4>' + s.title + '</h4><p>' + s.desc + '</p><div class="check">☐ Complete</div></div>';
  });
  
  html += '<div style="margin-top:16px"><button id="start-sim" style="background:var(--acc);color:#0b1214;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-weight:600">Start Simulation</button></div>';
  mc.innerHTML = html;
  const sb = document.getElementById('start-sim');
  if (sb) sb.onclick = () => window.alert('Starting simulation...');
  mp.style.display = 'block';
}

$('f-union').addEventListener('change', () => render());
$('f-sector').addEventListener('change', () => render());
$('f-robot').addEventListener('change', () => render());
load();