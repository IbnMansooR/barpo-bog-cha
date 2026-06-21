// models/ papkasini skanlab models.json yasaydi.
// - fayllarni web-xavfsiz nomga (slug) o'zgartiradi (probel/+/apostrofsiz)
// - names.json bo'lsa, chiroyli ko'rinish nomini oladi
// Ishga tushirish:  node generate.mjs
import { readdirSync, statSync, writeFileSync, existsSync, renameSync, readFileSync } from 'node:fs';
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

function slugify(base) {
  return base
    .toLowerCase()
    .replace(/['’`]/g, '')          // apostroflarni olib tashlash
    .replace(/[^a-z0-9]+/g, '-')    // qolgan belgilar -> -
    .replace(/^-+|-+$/g, '');
}

function prettify(slug) {
  return slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function findThumb(slug) {
  for (const ext of THUMB_EXT) {
    const p = join(THUMB_DIR, slug + ext);
    if (existsSync(p)) return p.replace(/\\/g, '/');
  }
  return null;
}

if (!existsSync(MODELS_DIR)) {
  console.error(`"${MODELS_DIR}" papkasi topilmadi.`);
  process.exit(1);
}

const names = existsSync('names.json')
  ? JSON.parse(readFileSync('names.json', 'utf8'))
  : {};

let files = readdirSync(MODELS_DIR)
  .filter(f => MODEL_EXT.includes(parse(f).ext.toLowerCase()));

// 1) Web-xavfsiz nomga o'zgartirish
const renamed = [];
for (const f of files) {
  const { name: base, ext } = parse(f);
  const slug = slugify(base);
  const target = slug + ext.toLowerCase();
  if (target !== f) {
    renameSync(join(MODELS_DIR, f), join(MODELS_DIR, target));
    renamed.push(`${f}  ->  ${target}`);
  }
}
if (renamed.length) {
  console.log('Web-xavfsiz nomga o\'zgartirildi:');
  renamed.forEach(r => console.log('  ' + r));
}

// 2) Manifest
files = readdirSync(MODELS_DIR)
  .filter(f => MODEL_EXT.includes(parse(f).ext.toLowerCase()))
  .sort((a, b) => a.localeCompare(b, 'uz'));

const models = files.map(f => {
  const slug = parse(f).name;
  const filePath = join(MODELS_DIR, f).replace(/\\/g, '/');
  const size = humanSize(statSync(filePath).size);
  const poster = findThumb(slug);
  return {
    id: slug,
    name: names[slug] || prettify(slug),
    file: filePath,
    size,
    ...(poster ? { poster } : {}),
  };
});

writeFileSync('models.json', JSON.stringify({ models }, null, 2) + '\n', 'utf8');
console.log(`\n✓ ${models.length} ta model -> models.json`);
models.forEach(m => console.log('  •', m.name, '—', m.size, `(${m.file})`));
