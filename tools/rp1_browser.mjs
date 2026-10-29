// rp1_browser.mjs -- open a VISIBLE Chrome at dev.rp1.com with a persistent profile + a
// stable CDP port, so a human can log in by hand and an agent can then reconnect to the
// same authenticated session (credentials never pass through the agent).
//
//   node tools/rp1_browser.mjs            # open dev.rp1.com (persistent profile)
//   node tools/rp1_browser.mjs <url>       # open any URL instead
//
// Profile: ~/.rp1-chrome-profile (survives restarts -- the RP1 session stays logged in)
// CDP:    http://127.0.0.1:9222  (json/version, json/list -- reconnect any time)
import { spawn } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PROFILE = path.join(os.homedir(), '.rp1-chrome-profile');
const PORT = 9222;
const URL_TO_OPEN = process.argv[2] || 'https://dev.rp1.com';

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${PROFILE}`,
  '--no-first-run', '--no-default-browser-check',
  '--window-size=1440,900',
  URL_TO_OPEN,
], { stdio: 'ignore', detached: true });
chrome.unref();

// wait for the CDP endpoint (Chrome cold-start with a fresh profile can take ~20s)
for (let i = 0; i < 150; i++) {
  const v = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json()).catch(() => null);
  if (v) {
    console.log(`Chrome up (CDP :${PORT}, ${v.Browser})`);
    console.log(`profile: ${PROFILE}`);
    console.log(`opened:  ${URL_TO_OPEN}`);
    process.exit(0);
  }
  await new Promise(r => setTimeout(r, 200));
}
console.error('Chrome did not expose the CDP port in time; is another Chrome using port 9222?');
process.exit(1);
