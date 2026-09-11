// Собирает site/app.html: берёт исходник index.html и вшивает в него songs/*.txt.
// Опубликованная страница не может читать файлы с диска, поэтому тексты песен должны
// лежать внутри неё. Исходник при этом не меняется — его можно спокойно править параллельно.
// Запуск: node build.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const srcPath = join(root, 'index.html');
const outPath = join(root, 'site/app.html');

const names = JSON.parse(readFileSync(join(root, 'songs/index.json'), 'utf8'));
const songs = {};
for (const name of names) songs[name] = readFileSync(join(root, 'songs', name), 'utf8');

const START = '  // === SONGS DATA START (генерируется build.mjs из songs/*.txt — вручную не править) ===';
const END = '  // === SONGS DATA END ===';

const page = readFileSync(srcPath, 'utf8');
const from = page.indexOf(START);
const to = page.indexOf(END);
if (from === -1 || to === -1) {
  throw new Error('В index.html не найдены маркеры SONGS DATA START/END');
}

const literal = JSON.stringify(songs, null, 0).replace(/</g, '\\u003c');
const block = `${START}\n  const SONG_FILES = ${literal};\n`;

writeFileSync(outPath, page.slice(0, from) + block + page.slice(to), 'utf8');
console.log(`site/app.html собран, песен: ${names.length} (${names.join(', ')})`);
