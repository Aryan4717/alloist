#!/usr/bin/env node
'use strict';

/**
 * ACT-lite conformance test runner.
 * Run: npm run generate && npm test
 */

const path = require('path');
const fs = require('fs');

async function main() {
  const fixturesDir = path.join(__dirname, 'fixtures');
  if (!fs.existsSync(fixturesDir) || fs.readdirSync(fixturesDir).length === 0) {
    console.log('Generating fixtures...');
    const { execSync } = require('child_process');
    execSync('node scripts/generate_fixtures.js', { cwd: __dirname, stdio: 'inherit' });
  }

  const { runConformanceTests } = require('./tests/conformance.test.js');
  const { runRevokePropagationTest } = require('./tests/revoke_propagation.test.js');

  const out = await runConformanceTests();
  if (out.error) {
    console.error(out.error);
    process.exit(1);
  }

  const propResult = await runRevokePropagationTest();
  out.results.push({ n: 'P', ok: propResult.ok, msg: propResult.msg });
  out.ok = out.ok && propResult.ok;

  console.log('\nACT-lite Conformance Tests\n');
  for (const r of out.results) {
    const status = r.ok ? 'PASS' : 'FAIL';
    const label = typeof r.n === 'number' ? `#${r.n}` : r.n;
    console.log(`  [${status}] ${label}: ${r.msg}`);
  }
  const passed = out.results.filter((r) => r.ok).length;
  const total = out.results.length;
  console.log(`\n${passed}/${total} passed\n`);

  process.exit(out.ok ? 0 : 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
