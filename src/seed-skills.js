"use strict";

const path = require('path');
const fs = require('fs');
const db = require('./db');

const configPath = path.join(__dirname, '..', 'config.json');

async function main() {
  db.init(configPath);
  const skillsPath = path.join(__dirname, '..', 'data', 'skills.json');
  if (!fs.existsSync(skillsPath)) {
    console.error('skills.json not found');
    process.exit(1);
  }
  const skills = JSON.parse(fs.readFileSync(skillsPath, 'utf8'));
  const ok = await db.seedSkillsAsync(skills);
  if (ok) console.log('✓ Skills seeded (or stored in fallback)');
  else console.error('✗ Skills seeding failed');
  process.exit(0);
}

main();
