#!/usr/bin/env node

/**
 * Generate frequency data index from available frequency files
 * This script scans the public/data/freq/top1000/ directory and creates
 * a freq_index.json file with the list of available languages.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FREQ_DIR = path.join(__dirname, '..', 'public', 'data', 'freq', 'top1000');
const OUTPUT_FILE = path.join(__dirname, '..', 'public', 'data', 'freq_index.json');

function generateFrequencyIndex() {
  console.log('Generating frequency data index...');
  
  // Check if frequency directory exists
  if (!fs.existsSync(FREQ_DIR)) {
    console.warn(`Frequency directory not found: ${FREQ_DIR}`);
    console.warn('Creating empty frequency index');
    
    // Create empty index if directory doesn't exist
    const emptyIndex = [];
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(emptyIndex, null, 2));
    console.log(`Created empty frequency index: ${OUTPUT_FILE}`);
    return;
  }
  
  try {
    // Read all files in the frequency directory
    const files = fs.readdirSync(FREQ_DIR);
    
    // Filter for .txt files and extract language codes
    const languageCodes = files
      .filter(file => file.endsWith('.txt'))
      .map(file => file.replace('.txt', ''))
      .sort();
    
    console.log(`Found ${languageCodes.length} frequency data files:`);
    console.log(languageCodes.join(', '));
    
    // Write the index file
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(languageCodes, null, 2));
    
    console.log(`✅ Generated frequency index: ${OUTPUT_FILE}`);
    console.log(`   Contains ${languageCodes.length} languages`);
    
  } catch (error) {
    console.error('❌ Error generating frequency index:', error);
    process.exit(1);
  }
}

// Copy additional indexes if they exist
function copyAdditionalIndexes() {
  const additionalIndexes = ['char_index.json', 'script_index.json'];
  const sourceDir = path.join(__dirname, '..', '..', 'data');
  const targetDir = path.join(__dirname, '..', 'public', 'data');

  for (const indexFile of additionalIndexes) {
    const sourcePath = path.join(sourceDir, indexFile);
    const targetPath = path.join(targetDir, indexFile);

    if (fs.existsSync(sourcePath)) {
      try {
        fs.copyFileSync(sourcePath, targetPath);
        console.log(`✅ Copied ${indexFile}`);
      } catch (error) {
        console.warn(`⚠️  Failed to copy ${indexFile}:`, error.message);
      }
    } else {
      console.log(`ℹ️  ${indexFile} not found, skipping`);
    }
  }
}

// Run the scripts
generateFrequencyIndex();
copyAdditionalIndexes();
