"use strict";

function loadRaceStats(racesData, raceKey) {
  if (!racesData || !raceKey) {
    return {};
  }

  const race = racesData[String(raceKey).toLowerCase()];
  if (!race) {
    return {};
  }

  return { ...(race.base_stats || {}) };
}

function loadJobStats(jobsData, jobKey) {
  if (!jobsData || !jobKey) {
    return {};
  }

  const job = jobsData[String(jobKey).toLowerCase()];
  if (!job) {
    return {};
  }

  return { ...(job.base_stats || {}) };
}

function combineBaseStats(raceStats, jobStats = null) {
  const combined = { ...(raceStats || {}) };
  if (jobStats) {
    for (const [key, value] of Object.entries(jobStats)) {
      combined[key] = (combined[key] || 0) + value;
    }
  }
  return combined;
}

function calculateDerivedStats(baseStats, level = 1, equipmentBonus = null) {
  const bonus = equipmentBonus || {};

  const strVal = baseStats?.str || 0;
  const agiVal = baseStats?.agi || 0;
  const vitVal = baseStats?.vit || 0;
  const intVal = baseStats?.int || 0;
  const dexVal = baseStats?.dex || 0;
  const lukVal = baseStats?.luk || 0;
  const tecVal = baseStats?.tec || 0;
  const menVal = baseStats?.men || 0;
  const crtVal = baseStats?.crt || 0;

  const derived = {};

  const atkBase = strVal + dexVal + Math.floor(lukVal / 3);
  derived.atk = atkBase + (bonus.atk || 0);

  const matkBase = Math.floor(intVal * 1.5) + Math.floor(dexVal / 5) + Math.floor(lukVal / 3);
  derived.matk = matkBase + (bonus.matk || 0);

  const hitBase = dexVal + Math.floor(lukVal / 3);
  derived.hit = hitBase + (bonus.hit || 0);

  const criticalRate = (lukVal * 0.3) + (crtVal * 0.5) + 1;
  derived.crit = Math.round(criticalRate * 100) / 100 + (bonus.crit || 0);

  const aspdBase = agiVal + Math.floor(dexVal / 2);
  derived.aspd = aspdBase + (bonus.aspd || 0);

  const defBase = vitVal + Math.floor(agiVal / 5);
  derived.def = defBase + (bonus.def || 0);

  const mdefBase = Math.floor(intVal / 2) + Math.floor(vitVal / 5) + Math.floor(dexVal / 5) + menVal;
  derived.mdef = mdefBase + (bonus.mdef || 0);

  const fleeBase = agiVal + Math.floor(lukVal / 5);
  derived.flee = fleeBase + (bonus.flee || 0);

  const perfectDodge = Math.floor(lukVal / 10);
  derived.perfect_dodge = perfectDodge + (bonus.perfect_dodge || 0);

  const critDef = Math.floor(lukVal / 5);
  derived.crit_def = critDef + (bonus.crit_def || 0);

  let maxHp = (10 + vitVal) + (level - 1) * 2;
  maxHp = Math.floor(maxHp * (1 + vitVal * 0.01));
  derived.max_hp = maxHp + (bonus.max_hp || 0);

  let maxSp = (10 + intVal) + (level - 1) * 1;
  maxSp = Math.floor(maxSp * (1 + intVal * 0.01));
  derived.max_sp = maxSp + (bonus.max_sp || 0);

  const vctReduction = dexVal * 0.1 + intVal * 0.05;
  derived.vct_reduction = Math.min(vctReduction, 100) + (bonus.vct_reduction || 0);

  const hpRecovery = 1 + Math.floor(vitVal / 10);
  derived.hp_recovery = hpRecovery + (bonus.hp_recovery || 0);

  const spRecovery = 1 + Math.floor(intVal / 6);
  derived.sp_recovery = spRecovery + (bonus.sp_recovery || 0);

  const weightLimit = 500 + (strVal * 30);
  derived.weight_limit = weightLimit + (bonus.weight_limit || 0);

  const successRate = 50 + (tecVal * 0.5) + (dexVal * 0.1) + (lukVal * 0.05) + (intVal * 0.05);
  derived.success_rate = Math.min(successRate, 100) + (bonus.success_rate || 0);

  const statusResistance = Math.floor(vitVal / 5) + Math.floor(lukVal / 10);
  derived.status_resistance = statusResistance + (bonus.status_resistance || 0);

  return derived;
}

function calculateDamageScaling(baseStats, weaponType = "melee") {
  const strVal = baseStats?.str || 0;
  const dexVal = baseStats?.dex || 0;
  const scaling = {};

  if (weaponType === "melee") {
    scaling.atk_bonus = strVal;
    scaling.damage_bonus = 1 + (strVal * 0.005);
  } else if (weaponType === "ranged") {
    scaling.atk_bonus = dexVal;
    scaling.damage_bonus = 1 + (dexVal * 0.005);
  } else if (weaponType === "magic") {
    const intVal = baseStats?.int || 0;
    scaling.matk_bonus = intVal;
    scaling.damage_bonus = 1 + (intVal * 0.01);
  }

  return scaling;
}

function applyStatusEffects(baseStats, statusEffect) {
  const vitVal = baseStats?.vit || 0;
  const lukVal = baseStats?.luk || 0;
  const menVal = baseStats?.men || 0;

  const resistance = Math.floor(vitVal / 5) + Math.floor(lukVal / 10) + Math.floor(menVal / 10);

  const effectReduction = {
    poison: Math.floor(vitVal / 3),
    stun: Math.floor(vitVal / 5),
    frozen: Math.floor(lukVal / 5),
    curse: Math.floor(lukVal / 5),
    sleep: Math.floor(menVal / 5),
    blind: Math.floor(lukVal / 3),
    fear: Math.floor(menVal / 3),
    confusion: Math.floor(menVal / 5),
  };

  return resistance + (effectReduction[String(statusEffect || "").toLowerCase()] || 0);
}

function calculateCriticalDamage(critStat, baseDamage) {
  const baseMultiplier = 1.5;
  const additionalMultiplier = critStat * 0.005;
  return baseDamage * (baseMultiplier + additionalMultiplier);
}

function calculatePotionEffectiveness(baseStats) {
  const vitVal = baseStats?.vit || 0;
  return 1.0 + (vitVal * 0.02);
}

function createCharacterStats(raceData, raceKey, jobKey = "novice", jobsData = null, level = 1) {
  const raceStats = loadRaceStats(raceData, raceKey);
  const jobStats = jobsData ? loadJobStats(jobsData, jobKey) : {};
  const baseStats = combineBaseStats(raceStats, jobStats);
  const derivedStats = calculateDerivedStats(baseStats, level);

  return {
    base_stats: baseStats,
    derived_stats: derivedStats,
    race: String(raceKey).toLowerCase(),
    job: String(jobKey).toLowerCase(),
    level,
    current_hp: derivedStats.max_hp ?? 100,
    current_sp: derivedStats.max_sp ?? 50,
  };
}

function formatStatsDisplay(charStats) {
  const base = charStats?.base_stats || {};
  const derived = charStats?.derived_stats || {};

  return [
    "**PRIMARY STATS**",
    `STR: ${base.str || 0} | AGI: ${base.agi || 0} | VIT: ${base.vit || 0}`,
    `INT: ${base.int || 0} | DEX: ${base.dex || 0} | LUK: ${base.luk || 0}`,
    `TEC: ${base.tec || 0} | MEN: ${base.men || 0} | CRT: ${base.crt || 0}`,
    "",
    "**HP & MANA**",
    `HP: ${charStats?.current_hp || 0}/${derived.max_hp || 0}`,
    `MP: ${charStats?.current_sp || 0}/${derived.max_sp || 0}`,
    "",
    "**OFFENSIVE**",
    `ATK: ${derived.atk || 0} | MATK: ${derived.matk || 0} | Hit: ${derived.hit || 0}`,
    `CRIT: ${derived.crit || 0}% | ASPD: ${derived.aspd || 0}`,
    "",
    "**DEFENSIVE**",
    `DEF: ${derived.def || 0} | MDEF: ${derived.mdef || 0} | Flee: ${derived.flee || 0}`,
    `Perfect Dodge: ${derived.perfect_dodge || 0} | CRIT DEF: ${derived.crit_def || 0}`,
    "",
    "**UTILITY**",
    `Weight Limit: ${derived.weight_limit || 0} kg | Success Rate: ${derived.success_rate || 0}%`,
    `Status Resistance: +${derived.status_resistance || 0}`,
  ].join("\n");
}

module.exports = {
  loadRaceStats,
  loadJobStats,
  combineBaseStats,
  calculateDerivedStats,
  calculateDamageScaling,
  applyStatusEffects,
  calculateCriticalDamage,
  calculatePotionEffectiveness,
  createCharacterStats,
  formatStatsDisplay,
};