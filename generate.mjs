// models/ papkasini skanlab models.json yasaydi.
// Ishga tushirish:  node generate.mjs
import { readdirSync, statSync, writeFileSync, existsSync } from 'node:fs';
import { join, parse } from 'node:path';

const MODELS_DIR = 'models';
const THUMB_DIR = 'thumbnails';
const MODEL_EXT = ['.glb', '.gltf'];
const THUMB_EXT = ['.webp', '.png', '.jpg', '.jpeg'];

function humanSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  const u = ['KB', 'MB', 'GB'];
  let i = -1, n = bytes;
  do { n /= 1024; i++; } while (n >= 1024 && i < u.length - 1);
  return n.toFixed(n < 10 ? 1 : 0) + ' ' + u[i];
}

function prettyName(base) {
  return base
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());
}

function findThumb(base) {
  for (const ext of THUMB_EXT) {
    const p = join(THUMB_DIR, base + ext);
    if (existsSync(p)) return p.replace(/\\/g, '/');
  }
  return null;
}

if (!existsSync(MODELS_DIR)) {
  console.error(`"${MODELS_DIR}" papkasi topilmadi.`);
  process.exit(1);
}

const files = readdirSync(MODELS_DIR)
  .filter(f => MODEL_EXT.includes(parse(f).ext.toLowerCase()))
  .sort((a, b) => a.localeCompare(b, 'uz'));

const models = files.map(f => {
  const { name: base } = parse(f);
  const filePath = join(MODELS_DIR, f).replace(/\\/g, '/');
  const size = humanSize(statSync(filePath).size);
  const poster = findThumb(base);
  return {
    id: base.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    name: prettyName(base),
    file: filePath,
    size,
    ...(poster ? { poster } : {}),
  };
});

writeFileSync('models.json', JSON.stringify({ models }, null, 2) + '\n', 'utf8');
console.log(`✓ ${models.length} ta model topildi va models.json yangilandi.`);
models.forEach(m => console.log('  •', m.name, '—', m.size));
