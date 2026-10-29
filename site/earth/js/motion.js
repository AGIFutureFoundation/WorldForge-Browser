// motion.js: the world's live movement corpus. Merges robot joint-trace episodes
// (worldforge-earth/robot-episode/3, from robots.js) with human union-training movement
// episodes (worldforge-earth/human-motion/1, from training-sim.js) into one JSONL stream,
// for the movement LM pipeline in earth/motion (tokenizer -> tiny transformer trained
// locally -> sampled movement scripts replayed in motion-lm.html).
export function motionCorpus(fleet, training) {
  const out = [];
  (fleet?.userData?.records || []).forEach(r => out.push(JSON.stringify(r)));
  (training?.getMotions() || []).forEach(h => out.push(JSON.stringify(h)));
  return out.length ? out.join('\n') + '\n' : '';
}

export function wireMotionCorpus({ slug, fleet, training }) {
  const host = document.getElementById('game');
  if (!host) return;
  const btn = document.createElement('button');
  btn.textContent = 'Movement corpus';
  btn.title = 'Download this world\'s robot + human movement episodes (JSONL) for the movement LM';
  btn.onclick = () => {
    const blob = new Blob([motionCorpus(fleet, training)], { type: 'application/x-ndjson' });
    Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `${slug}-motion-corpus.jsonl` }).click();
  };
  host.appendChild(btn);
}
