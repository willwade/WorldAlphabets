#!/usr/bin/env node
/**
 * Create index files for WorldAlphabets data
 * This script generates index.json and other metadata files
 */

const fs = require('fs').promises;
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const ALPHABETS_DIR = path.join(DATA_DIR, 'alphabets');

async function createIndex() {
  console.log('🔄 Creating data index...');
  
  try {
    // Read all alphabet files
    const files = await fs.readdir(ALPHABETS_DIR);
    const alphabetFiles = files.filter(f => f.endsWith('.json'));
    
    const index = [];
    const scripts = {};
    
    for (const file of alphabetFiles) {
      try {
        const content = await fs.readFile(path.join(ALPHABETS_DIR, file), 'utf8');
        const data = JSON.parse(content);
        
        // Extract language and script from filename
        const basename = path.basename(file, '.json');
        const parts = basename.split('-');
        const language = parts[0];
        const script = parts.slice(1).join('-') || 'Latn';
        
        // Add to index
        const entry = {
          language,
          script,
          name: data.language || language,
          iso639_1: data.iso639_1,
          iso639_3: data.iso639_3,
          letterCount: data.lowercase ? data.lowercase.length : 0,
          hasFrequency: data.frequency && Object.keys(data.frequency).length > 0,
          file: file
        };
        
        index.push(entry);
        
        // Group by language for scripts index
        if (!scripts[language]) {
          scripts[language] = [];
        }
        if (!scripts[language].includes(script)) {
          scripts[language].push(script);
        }
        
      } catch (err) {
        console.warn(`⚠️  Error processing ${file}: ${err.message}`);
      }
    }
    
    // Sort index by language code
    index.sort((a, b) => a.language.localeCompare(b.language));
    
    // Write main index
    const indexPath = path.join(DATA_DIR, 'index.json');
    await fs.writeFile(indexPath, JSON.stringify(index, null, 2));
    console.log(`✅ Created ${indexPath} with ${index.length} entries`);
    
    // Write scripts index
    const scriptsPath = path.join(DATA_DIR, 'scripts.json');
    await fs.writeFile(scriptsPath, JSON.stringify(scripts, null, 2));
    console.log(`✅ Created ${scriptsPath} with ${Object.keys(scripts).length} languages`);
    
    // Create summary stats
    const stats = {
      totalAlphabets: index.length,
      totalLanguages: Object.keys(scripts).length,
      totalScripts: new Set(index.map(e => e.script)).size,
      withFrequency: index.filter(e => e.hasFrequency).length,
      lastUpdated: new Date().toISOString(),
      scriptCounts: {}
    };
    
    // Count alphabets per script
    for (const entry of index) {
      stats.scriptCounts[entry.script] = (stats.scriptCounts[entry.script] || 0) + 1;
    }
    
    const statsPath = path.join(DATA_DIR, 'stats.json');
    await fs.writeFile(statsPath, JSON.stringify(stats, null, 2));
    console.log(`✅ Created ${statsPath}`);
    
    console.log('\n📊 Summary:');
    console.log(`   Alphabets: ${stats.totalAlphabets}`);
    console.log(`   Languages: ${stats.totalLanguages}`);
    console.log(`   Scripts: ${stats.totalScripts}`);
    console.log(`   With frequency data: ${stats.withFrequency}`);
    
  } catch (error) {
    console.error('❌ Error creating index:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  createIndex();
}

module.exports = { createIndex };
