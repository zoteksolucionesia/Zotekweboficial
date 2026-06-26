const fs   = require('fs');
const path = require('path');
const { minify } = require('terser');
const CleanCSS   = require('clean-css');

const ROOT = path.resolve(__dirname, '..');

const JS_FILES = [
  'www/admin/zotek_v9.js',
  'www/admin/email-leads.js',
  'www/admin/automations.js',
  'www/cita/cita.js',
  'www/portal/portal.js',
  'www/script.js',
];

const CSS_FILES = [
  'www/admin/zotek_v9.css',
  'www/portal/portal.css',
  'www/style.css',
];

function kb(bytes) {
  return (bytes / 1024).toFixed(1) + ' KB';
}

async function run() {
  console.log('🔒 Minificando www/ para producción...\n');

  for (const rel of JS_FILES) {
    const file = path.join(ROOT, rel);
    const src  = fs.readFileSync(file, 'utf8');
    const result = await minify(src, { compress: true, mangle: true });
    fs.writeFileSync(file, result.code, 'utf8');
    console.log(`  JS   ${rel.padEnd(36)} ${kb(src.length)} → ${kb(result.code.length)}`);
  }

  const cleaner = new CleanCSS({ level: 2 });
  for (const rel of CSS_FILES) {
    const file   = path.join(ROOT, rel);
    const src    = fs.readFileSync(file, 'utf8');
    const result = cleaner.minify(src);
    fs.writeFileSync(file, result.styles, 'utf8');
    console.log(`  CSS  ${rel.padEnd(36)} ${kb(src.length)} → ${kb(result.styles.length)}`);
  }

  console.log('\n✅ Listo. Para restaurar el código legible: npm run restore');
}

run().catch(err => {
  console.error('❌ Error al minificar:', err.message);
  process.exit(1);
});
