// Interactive Training Simulation System
import * as THREE from 'three';

const $ = (id) => document.getElementById(id);

// deterministic seeded RNG so recorded human movements are reproducible per scenario
function hashStr(s) { let h = 2166136261; for (const c of s) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; }
function mulberry32(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

export const SCENARIOS = {
  'Tech': [
    { name: 'Server Deployment', steps: ['Rack Setup', 'Network Config', 'Power On', 'Testing'], duration: 45 },
    { name: 'Network Cabling', steps: ['Cable Routing', 'Termination', 'Testing', 'Documentation'], duration: 30 },
    { name: 'Hardware Testing', steps: ['Bench Setup', 'Diagnostics', 'Stress Test', 'Report'], duration: 60 },
    { name: 'Cleanroom Protocol', steps: ['Gowning', 'Entry', 'Procedure', 'Exit'], duration: 20 },
    { name: 'Equipment Calibration', steps: ['Setup', 'Calibration', 'Verification', 'Logging'], duration: 40 }
  ],
  'Energy': [
    { name: 'Grid Automation', steps: ['System Check', 'Configuration', 'Testing', 'Activation'], duration: 90 },
    { name: 'Solar Install', steps: ['Site Prep', 'Panel Mount', 'Wiring', 'Commission'], duration: 120 },
    { name: 'Wind Turbine Maint', steps: ['Safety Check', 'Inspection', 'Repair', 'Testing'], duration: 180 },
    { name: 'Substation Setup', steps: ['Grounding', 'Equipment', 'Wiring', 'Energize'], duration: 150 },
    { name: 'Energy Storage', steps: ['Battery Install', 'BMS Config', 'Testing', 'Integration'], duration: 100 }
  ],
  'Aerospace': [
    { name: 'Drone Assembly', steps: ['Frame Build', 'Motor Install', 'ESC Config', 'Flight Test'], duration: 60 },
    { name: 'Aircraft Maint', steps: ['Pre-Flight', 'Inspection', 'Service', 'Post-Flight'], duration: 90 },
    { name: 'Satellite Deploy', steps: ['Integration', 'Testing', 'Launch Prep', 'Deployment'], duration: 240 },
    { name: 'Avionics Testing', steps: ['Bench Test', 'System Check', 'Calibration', 'Certify'], duration: 75 },
    { name: 'Quality Control', steps: ['Visual Insp', 'NDT', 'Documentation', 'Release'], duration: 45 }
  ],
  'Logistics': [
    { name: 'Warehouse Sorting', steps: ['System Start', 'Sort Config', 'Running', 'Audit'], duration: 60 },
    { name: 'Fleet Dispatch', steps: ['Route Plan', 'Vehicle Check', 'Dispatch', 'Monitor'], duration: 45 },
    { name: 'Loading Ops', steps: ['Dock Prep', 'Load Plan', 'Execution', 'Verify'], duration: 30 },
    { name: 'Inventory Mgmt', steps: ['Cycle Count', 'Reconciliation', 'Adjustment', 'Report'], duration: 90 },
    { name: 'Route Planning', steps: ['Data Input', 'Optimization', 'Review', 'Deploy'], duration: 40 }
  ],
  'Entertainment': [
    { name: 'Stage Setup', steps: ['Layout', 'Rigging', 'Lighting', 'Sound'], duration: 120 },
    { name: 'Lighting Design', steps: ['Plot', 'Focus', 'Program', 'Cue'], duration: 90 },
    { name: 'Sound Engineering', steps: ['System Setup', 'EQ', 'Mix', 'Show'], duration: 75 },
    { name: 'Event Production', steps: ['Load-In', 'Setup', 'Show', 'Load-Out'], duration: 240 },
    { name: 'Venue Automation', steps: ['System Check', 'Programming', 'Testing', 'Live'], duration: 60 }
  ],
  'Healthcare': [
    { name: 'Pharmacy Auto', steps: ['System Init', 'Drug Load', 'Config', 'Verify'], duration: 60 },
    { name: 'Lab Sample', steps: ['Collection', 'Processing', 'Analysis', 'Report'], duration: 45 },
    { name: 'Patient Transport', steps: ['Prep', 'Loading', 'Transit', 'Handoff'], duration: 30 },
    { name: 'Sterilization', steps: ['Prep', 'Cycle', 'Verification', 'Storage'], duration: 90 },
    { name: 'Supply Chain', steps: ['Order', 'Receive', 'Stock', 'Audit'], duration: 60 }
  ],
  'Finance': [
    { name: 'Vault Automation', steps: ['Security Check', 'System Init', 'Test', 'Live'], duration: 120 },
    { name: 'Trading Floor', steps: ['Network Setup', 'System Config', 'Testing', 'Go-Live'], duration: 90 },
    { name: 'Data Center', steps: ['Rack Setup', 'Power', 'Network', 'Deploy'], duration: 180 },
    { name: 'Security Patrol', steps: ['Route Plan', 'System Check', 'Patrol', 'Report'], duration: 60 },
    { name: 'Server Rack', steps: ['Install', 'Cable', 'Power', 'Test'], duration: 45 }
  ],
  'Solar': [
    { name: 'Panel Install', steps: ['Mount', 'Wire', 'Ground', 'Test'], duration: 90 },
    { name: 'Inverter Setup', steps: ['Mount', 'DC Connect', 'AC Connect', 'Commission'], duration: 60 },
    { name: 'Grid Connect', steps: ['Permit', 'Install', 'Inspection', 'Energize'], duration: 120 },
    { name: 'Maintenance', steps: ['Inspect', 'Clean', 'Test', 'Report'], duration: 45 },
    { name: 'Monitoring', steps: ['Install', 'Config', 'Test', 'Verify'], duration: 30 }
  ],
  'Manufacturing': [
    { name: 'Assembly Line', steps: ['Setup', 'Calibration', 'Run', 'QC'], duration: 120 },
    { name: 'Welding Ops', steps: ['Prep', 'Weld', 'Inspect', 'Finish'], duration: 60 },
    { name: 'Quality Inspect', steps: ['Sample', 'Measure', 'Record', 'Release'], duration: 45 },
    { name: 'Packaging', steps: ['Setup', 'Run', 'Inspect', 'Ship'], duration: 30 },
    { name: 'Material Handling', steps: ['Plan', 'Load', 'Move', 'Unload'], duration: 60 }
  ],
  'Tourism': [
    { name: 'Guest Services', steps: ['System Start', 'Config', 'Test', 'Live'], duration: 45 },
    { name: 'Tour Guidance', steps: ['Route Plan', 'System Check', 'Tour', 'Feedback'], duration: 90 },
    { name: 'Restaurant Auto', steps: ['Setup', 'Config', 'Test', 'Service'], duration: 60 },
    { name: 'Event Setup', steps: ['Layout', 'Setup', 'Test', 'Go'], duration: 120 },
    { name: 'Guest Relations', steps: ['Check-In', 'Assist', 'Follow-Up', 'Survey'], duration: 45 }
  ],
  'General': [
    { name: 'Workplace Safety', steps: ['Briefing', 'Hazard Scan', 'Task', 'Report'], duration: 30 },
    { name: 'Equipment Basics', steps: ['Inspect', 'Operate', 'Maintain', 'Log'], duration: 45 },
    { name: 'Site Orientation', steps: ['Check-In', 'Walkthrough', 'Practice', 'Review'], duration: 60 },
    { name: 'Team Coordination', steps: ['Assign', 'Rehearse', 'Execute', 'Debrief'], duration: 40 },
    { name: 'Quality Basics', steps: ['Standard', 'Self-Check', 'Fix', 'Verify'], duration: 35 }
  ]
};

export class TrainingSim {
  constructor() {
    this.currentScenario = null;
    this.currentStep = 0;
    this.score = 0;
    this.timer = null;
    this.timeElapsed = 0;
    this.completed = [];
    this.motions = [];               // human movement episodes (schema worldforge-earth/human-motion/1)
    this.motionEp = null;
    this.rng = null;
  }

  // human movement primitives for one union-module step, derived from the step's wording
  // (walk to station, then the step's characteristic verbs, then a verification)
  static stepMoves(name, rnd) {
    const s = name.toLowerCase(), mv = [];
    mv.push({ v: 'WALK', m: 3 + Math.floor(rnd() * 9), dir: Math.floor(rnd() * 16) });
    if (/rack|mount|panel|install|load|wire|cable|frame|rig|build/.test(s))
      mv.push({ v: 'LIFT', kg: +(1 + rnd() * 11).toFixed(1) }, { v: 'CARRY', m: +(1 + rnd() * 4).toFixed(1) }, { v: 'PLACE' });
    if (/test|check|inspect|scan|verif|audit|ndt|quality|diagnos/.test(s))
      mv.push({ v: 'INSPECT', s: 20 + Math.floor(rnd() * 40) });
    if (/config|program|type|log|document|report|record|plan|cue|eq|mix|reconcil/.test(s))
      mv.push({ v: 'TYPE', s: 30 + Math.floor(rnd() * 90) });
    if (/gown|entry|exit|prep|clean|cycle|stock|receive|sort|count|collect/.test(s))
      mv.push({ v: 'BEND', deg: 20 + Math.floor(rnd() * 40) });
    if (/power|energize|switch|launch|deploy|activate|live|commission|press/.test(s))
      mv.push({ v: 'REACH', m: +(0.4 + rnd() * 0.35).toFixed(2) }, { v: 'PRESS' });
    mv.push({ v: 'CHECK' });
    return mv;
  }

  startScenario(scenario) {
    this.currentScenario = scenario;
    this.currentStep = 0;
    this.score = 0;
    this.timeElapsed = 0;
    this.rng = mulberry32(hashStr(scenario.name));
    this.motionEp = { schema: 'worldforge-earth/human-motion/1', agent: 'human-trainee',
      scenario: scenario.name, sector: scenario.sector || null, steps: [], ts: new Date().toISOString() };
    this.updateUI();
    this.startTimer();
  }

  completeStep() {
    if (!this.currentScenario || this.currentStep >= this.currentScenario.steps.length) return;
    const stepName = this.currentScenario.steps[this.currentStep];
    const moves = TrainingSim.stepMoves(stepName, this.rng);
    if (this.motionEp) this.motionEp.steps.push({ step: stepName, elapsed_s: this.timeElapsed, moves,
      posture: { bend_deg: moves.some(m => m.v === 'BEND') ? moves.find(m => m.v === 'BEND').deg : 0,
        reach_m: +(0.3 + this.rng() * 0.4).toFixed(2),
        load_kg: moves.find(m => m.v === 'LIFT')?.kg ?? 0 } });
    this.currentStep++;
    this.score += Math.max(10, 100 - this.timeElapsed);
    if (this.currentStep >= this.currentScenario.steps.length) {
      this.completeScenario();
    }
    this.updateUI();
  }

  completeScenario() {
    if (this.timer) clearInterval(this.timer);
    this.completed.push({ scenario: this.currentScenario.name, score: this.score, time: this.timeElapsed, date: new Date().toISOString() });
    if (this.motionEp) { this.motionEp.outcome = 'success'; this.motionEp.total_s = this.timeElapsed;
      this.motions.push(this.motionEp); this.motionEp = null; }
    this.currentScenario = null;
    this.currentStep = 0;
  }

  startTimer() {
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => { this.timeElapsed++; this.updateTimer(); }, 1000);
  }

  updateUI() {
    const panel = $('training-panel');
    if (!panel) return;
    if (!this.currentScenario) {
      panel.innerHTML = '<h3>Select a Training Scenario</h3><p>Choose a scenario to begin.</p>';
      return;
    }
    const progress = (this.currentStep / this.currentScenario.steps.length) * 100;
    panel.innerHTML = '<h3>' + this.currentScenario.name + '</h3><div class="progress"><div class="bar" style="width:' + progress + '%"></div></div><div class="meta">Step ' + (this.currentStep + 1) + ' of ' + this.currentScenario.steps.length + '</div><div class="meta">Time: ' + this.timeElapsed + 's | Score: ' + this.score + '</div><h4>Current: ' + this.currentScenario.steps[this.currentStep] + '</h4><button onclick="window.__wf.training.completeStep()">Complete Step</button> <button onclick="window.__wf.training.reset()">Reset</button>';
  }

  updateTimer() {
    const el = $('training-timer');
    if (el) el.textContent = this.timeElapsed + 's';
  }

  reset() {
    if (this.timer) clearInterval(this.timer);
    this.currentScenario = null;
    this.currentStep = 0;
    this.score = 0;
    this.timeElapsed = 0;
    this.motionEp = null;
    this.updateUI();
  }

  getCompleted() { return this.completed; }
  getMotions() { return this.motions; }   // human movement episodes for the corpus
}

export function initTraining() {
  window.__wf = window.__wf || {};
  window.__wf.training = new TrainingSim();
  if (!$('training-panel')) {
    const panel = document.createElement('div');
    panel.id = 'training-panel';
    panel.className = 'panel';
    panel.style.cssText = 'right:12px;top:12px;max-width:380px;max-height:80vh;overflow:auto;display:none';
    document.body.appendChild(panel);
  }
  return window.__wf.training;
}
