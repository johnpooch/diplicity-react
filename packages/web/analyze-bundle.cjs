const fs = require('fs');
const html = fs.readFileSync('stats.html', 'utf-8');

// Find the start of data
const startIdx = html.indexOf('const data = {');
if (startIdx === -1) {
  console.log('Could not find data start');
  process.exit(1);
}

// Find the matching closing brace
let depth = 0;
let inString = false;
let escape = false;
let endIdx = -1;

for (let i = startIdx + 14; i < html.length; i++) {
  const c = html[i];

  if (escape) {
    escape = false;
    continue;
  }

  if (c === '\\') {
    escape = true;
    continue;
  }

  if (c === '"') {
    inString = !inString;
    continue;
  }

  if (inString) continue;

  if (c === '{') depth++;
  if (c === '}') {
    if (depth === 0) {
      endIdx = i;
      break;
    }
    depth--;
  }
}

const jsonStr = html.substring(startIdx + 13, endIdx + 1);
const data = JSON.parse(jsonStr);
const tree = data.tree;
const nodeParts = data.nodeParts || {};

function extractPackageName(path) {
  if (!path) return 'unknown';
  path = path.replace(/^\u0000\//, '').replace(/^\u0000/, '');

  if (path.includes('node_modules/')) {
    const parts = path.split('node_modules/')[1].split('/');
    if (parts[0].startsWith('@')) {
      return parts[0] + '/' + parts[1];
    }
    return parts[0];
  }

  if (path.startsWith('src/') || path.includes('/src/')) {
    return 'src (app code)';
  }

  return path;
}

// Get all modules with their paths
function getAllModules(node, path = '', modules = []) {
  const currentPath = path ? path + '/' + node.name : node.name;
  if (node.uid) {
    const parts = nodeParts[node.uid];
    if (parts) {
      modules.push({
        uid: node.uid,
        path: currentPath,
        name: node.name,
        size: parts.renderedLength || 0,
        gzip: parts.gzipLength || 0
      });
    }
  }
  if (node.children) {
    for (const child of node.children) {
      getAllModules(child, currentPath, modules);
    }
  }
  return modules;
}

console.log('\n=== Bundle Size Breakdown by Package ===\n');

// Aggregate all chunks
const allPackageSizes = {};
const chunkSizes = {};

for (const chunk of tree.children || []) {
  const chunkName = chunk.name;
  const modules = getAllModules(chunk);

  // Sum total chunk size
  let chunkTotal = 0;
  const packageSizes = {};

  for (const mod of modules) {
    const size = mod.size;
    chunkTotal += size;
    const pkgName = extractPackageName(mod.path);
    if (!packageSizes[pkgName]) packageSizes[pkgName] = 0;
    packageSizes[pkgName] += size;

    if (!allPackageSizes[pkgName]) allPackageSizes[pkgName] = 0;
    allPackageSizes[pkgName] += size;
  }

  chunkSizes[chunkName] = { total: chunkTotal, packages: packageSizes };
}

// Sort all packages by total size
const sorted = Object.entries(allPackageSizes).sort((a, b) => b[1] - a[1]);
const grandTotal = sorted.reduce((sum, [, size]) => sum + size, 0);

console.log('Size (KB)   % of Total   Package');
console.log('-'.repeat(70));
sorted.slice(0, 35).forEach(([name, size]) => {
  const kb = (size / 1024).toFixed(1);
  const pct = ((size / grandTotal) * 100).toFixed(1);
  console.log(`${kb.padStart(8)}   ${pct.padStart(6)}%      ${name}`);
});
console.log('-'.repeat(70));
console.log(`${(grandTotal / 1024).toFixed(1).padStart(8)}   100.0%      TOTAL`);

// Show main chunk specifically
const mainChunk = Object.entries(chunkSizes).find(([name]) => name.includes('index-') && !name.includes('vendor'));
if (mainChunk) {
  console.log(`\n\n=== Main Bundle (${mainChunk[0]}) - ${(mainChunk[1].total/1024).toFixed(0)} KB ===\n`);
  const mainSorted = Object.entries(mainChunk[1].packages).sort((a, b) => b[1] - a[1]);
  console.log('Size (KB)   Package');
  console.log('-'.repeat(60));
  mainSorted.slice(0, 25).forEach(([name, size]) => {
    if (size > 5000) {
      const kb = (size / 1024).toFixed(1);
      console.log(`${kb.padStart(8)}   ${name}`);
    }
  });
}
