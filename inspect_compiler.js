const fs = require('fs');
const path = require('path');

const baseDir = path.resolve(__dirname, '../../workforce-semantic-layer/node_modules/@cubejs-backend/schema-compiler');

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
      }
    }
  }
}

console.log('Searching for "dialectFactory" in schema-compiler...');
searchFiles(baseDir, 'dialectFactory');

console.log('Searching for "newFilter" in schema-compiler...');
searchFiles(baseDir, 'newFilter');

console.log('Searching for "likeIgnoreCase" in schema-compiler...');
searchFiles(baseDir, 'likeIgnoreCase');
