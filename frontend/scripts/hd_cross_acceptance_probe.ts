// Acceptance probe (TypeScript): HD Incarnation Cross rendering layer.
// Compile + execute with the project tsc.
//
//   cd /app/frontend && yarn tsc --target es2020 --module nodenext --moduleResolution nodenext \
//      --outDir /tmp/hd_probe scripts/hd_cross_acceptance_probe.ts && \
//      node /tmp/hd_probe/scripts/hd_cross_acceptance_probe.js
//
// Verifies Isaac and Thaddeus render DISTINCT cards from the same
// "Right Angle" orientation, that gates surface in the subtitle, and
// that the bare generic "Personal destiny" subtitle never appears.

import {
  getCrossMirrorCard,
  extractCrossFamily,
  CROSS_FAMILY_MIRROR_CARDS,
} from '../utils/humanDesignMirrorCards';

const isaac    = getCrossMirrorCard('Right Angle Cross of Consciousness',    '63/64 | 5/35');
const thad     = getCrossMirrorCard('Right Angle Cross of Sleeping Phoenix', '20/34 | 55/59');
const pete     = getCrossMirrorCard('Left Angle Cross of Migration',         '37/40 | 5/35');
const unknown  = getCrossMirrorCard('', '');
const missing  = getCrossMirrorCard('Unknown', '—');

type Check = { name: string; pass: boolean; info?: string };
const checks: Check[] = [];
const expect = (name: string, cond: any, info = '') =>
  checks.push({ name, pass: !!cond, info });

expect('isaac.title canonical',          isaac?.title    === 'Right Angle Cross of Consciousness',    isaac?.title);
expect('thad.title canonical',           thad?.title     === 'Right Angle Cross of Sleeping Phoenix', thad?.title);
expect('pete.title canonical',           pete?.title     === 'Left Angle Cross of Migration',         pete?.title);
expect('isaac.subtitle contains gates',  isaac?.subtitle.includes('63/64 | 5/35'),     isaac?.subtitle);
expect('thad.subtitle contains gates',   thad?.subtitle.includes('20/34 | 55/59'),     thad?.subtitle);
expect('pete.subtitle contains gates',   pete?.subtitle.includes('37/40 | 5/35'),      pete?.subtitle);
expect('recognition differs',            isaac?.recognition !== thad?.recognition);
expect('tension differs',                isaac?.tension !== thad?.tension);
expect('truthShift differs',             isaac?.truthShift !== thad?.truthShift);
expect('realLifeMoments differ',         JSON.stringify(isaac?.realLifeMoments) !== JSON.stringify(thad?.realLifeMoments));
expect('thad card free of "Sphinx"',     !JSON.stringify(thad).toLowerCase().includes('sphinx'));
expect('subtitle ≠ bare "Personal destiny"', isaac?.subtitle !== 'Personal destiny' && thad?.subtitle !== 'Personal destiny');
expect('empty crossType → null',         unknown === null);
expect('"Unknown" → null',               missing === null);
expect('family extractor: Sphinx',       extractCrossFamily('Right Angle Cross of the Sphinx 1') === 'the Sphinx');
expect('family extractor: Sleeping Phoenix', extractCrossFamily('Right Angle Cross of Sleeping Phoenix 1') === 'Sleeping Phoenix');
expect('family extractor: Consciousness',extractCrossFamily('Right Angle Cross of Consciousness 2') === 'Consciousness');
expect('family map has Sleeping Phoenix',!!CROSS_FAMILY_MIRROR_CARDS['Sleeping Phoenix']);
expect('family map has Consciousness',   !!CROSS_FAMILY_MIRROR_CARDS['Consciousness']);
expect('family map has Migration',       !!CROSS_FAMILY_MIRROR_CARDS['Migration']);

let pass = 0, fail = 0;
for (const c of checks) {
  // eslint-disable-next-line no-console
  console.log(`${c.pass ? '✅' : '❌'} ${c.name}${c.info ? '  — ' + String(c.info).slice(0, 80) : ''}`);
  c.pass ? pass++ : fail++;
}
console.log(`\nsummary: ${pass} pass / ${fail} fail / ${checks.length} total`);

console.log('\n— Isaac card —');
console.log('  title:    ', isaac?.title);
console.log('  subtitle: ', isaac?.subtitle);
console.log('  recogn:   ', isaac?.recognition?.slice(0, 120), '…');

console.log('\n— Thaddeus card —');
console.log('  title:    ', thad?.title);
console.log('  subtitle: ', thad?.subtitle);
console.log('  recogn:   ', thad?.recognition?.slice(0, 120), '…');

console.log('\n— Pete card —');
console.log('  title:    ', pete?.title);
console.log('  subtitle: ', pete?.subtitle);
console.log('  recogn:   ', pete?.recognition?.slice(0, 120), '…');

process.exit(fail === 0 ? 0 : 1);
