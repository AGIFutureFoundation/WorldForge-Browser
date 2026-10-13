// Validate every LOD1 GLB with the Khronos glTF validator and write worldforge/out/assets/lod/validation.json.
//   node worldforge/lod/validate_lod.mjs
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..', '..');
const require = createRequire(path.join(repo, 'tools', 'gltf-validator', 'package.json'));
const validator = require('gltf-validator');
const lodRoot = path.join(repo, 'worldforge', 'out', 'assets', 'lod');
const files = {};
let bad = 0, n = 0;
for (const kind of ['landmarks', 'avatars']) {
  const dir = path.join(lodRoot, kind);
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.lod1.glb')).sort()) {
    const bytes = fs.readFileSync(path.join(dir, f));
    const r = await validator.validateBytes(new Uint8Array(bytes));
    const i = r.issues;
    n++;
    files[`${kind}/${f}`] = {
      sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
      errors: i.numErrors, warnings: i.numWarnings, infos: i.numInfos, hints: i.numHints,
      messages: i.messages.filter(m => m.severity <= 1).slice(0, 5),
    };
    if (i.numErrors || i.numWarnings) { bad++; console.log(f, i.numErrors, 'errors', i.numWarnings, 'warnings', JSON.stringify(i.messages.slice(0, 3))); }
  }
}
fs.writeFileSync(path.join(lodRoot, 'validation.json'), JSON.stringify({
  schemaVersion: 'worldforge-lod-validation/0.1', validator: `gltf-validator ${validator.version()}`, files,
}, null, 1));
console.log(`${n} LOD1 GLBs validated, ${bad} with errors/warnings`);
process.exitCode = bad ? 1 : 0;
