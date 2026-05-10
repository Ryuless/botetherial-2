"use strict";

const path = require("path");
const fs = require("fs");
const stats = require("./stats");

const root = path.join(__dirname, "..");
const races = JSON.parse(fs.readFileSync(path.join(root, "races.json"), "utf8"));
const jobs = JSON.parse(fs.readFileSync(path.join(root, "jobs.json"), "utf8"));

const elfChar = stats.createCharacterStats(races, "elf", "archer", jobs, 1);
console.log("=== Elf Archer Character ===");
console.log("Base Stats:", elfChar.base_stats);
console.log("Level:", elfChar.level);
console.log("Max HP:", elfChar.derived_stats.max_hp);
console.log("Max SP:", elfChar.derived_stats.max_sp);
console.log("ATK:", elfChar.derived_stats.atk);
console.log("MATK:", elfChar.derived_stats.matk);
console.log("DEF:", elfChar.derived_stats.def);
console.log("Flee:", elfChar.derived_stats.flee);
console.log("CRIT:", elfChar.derived_stats.crit, "%");
console.log();

console.log("=== Dwarf Blacksmith Character ===");
const dwarfChar = stats.createCharacterStats(races, "dwarf", "blacksmith", jobs, 1);
console.log("Base Stats:", dwarfChar.base_stats);
console.log("Max HP:", dwarfChar.derived_stats.max_hp);
console.log("ATK:", dwarfChar.derived_stats.atk);
console.log("DEF:", dwarfChar.derived_stats.def);
console.log("Weight Limit:", dwarfChar.derived_stats.weight_limit, "kg");
console.log();

console.log("=== Demon Mage Character ===");
const demonChar = stats.createCharacterStats(races, "demon", "mage", jobs, 1);
console.log("Base Stats:", demonChar.base_stats);
console.log("Max HP:", demonChar.derived_stats.max_hp);
console.log("Max SP:", demonChar.derived_stats.max_sp);
console.log("MATK:", demonChar.derived_stats.matk);
console.log("MDEF:", demonChar.derived_stats.mdef);

console.log("\n✅ Stats system test completed successfully!");