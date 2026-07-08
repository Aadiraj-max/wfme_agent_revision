const fs = require('fs');
const path = require('path');

const baseDir = path.resolve(__dirname, '../../workforce-semantic-layer/node_modules/@cubejs-backend/server-core');

function searchFiles(dir, query) {
  if (!fs.existsSync(dir)) return;
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      if (file !== 'node_modules') {
        searchFiles(filePath, query);
      }
    } else if (file.endsWith('.js') || file.endsWith('.ts')) {
      const content = fs.readFileSync(filePath, 'utf8');
      if (content.includes(query)) {
        console.log(`Found "${query}" in: ${filePath}`);
        const lines = content.split('\n');
        lines.forEach((line, idx) => {
          if (line.includes(query) && !line.includes('import') && !line.includes('require')) {
            console.log(`  Line ${idx + 1}: ${line.trim()}`);
          }
        });
      }
    }
  }
}

console.log('Searching for "QueryFactory" in server-core...');
searchFiles(baseDir, 'QueryFactory');
