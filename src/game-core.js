"use strict";

const fs = require("fs");
const path = require("path");
const stats = require("./stats");

const ROOT = path.resolve(__dirname, "..");
const DATA_DIR = path.join(ROOT, "data");
const CONFIG_PATH = path.join(ROOT, "config.json");

function readJson(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function loadJson(name, useRoot = false) {
  const filePath = useRoot ? path.join(ROOT, name) : path.join(DATA_DIR, name);
  return readJson(filePath);
}

const cfg = readJson(CONFIG_PATH);

const MAP = loadJson("map.json");
const MONSTERS = loadJson("monsters.json");
const ITEMS = loadJson("items.json");
const CHARACTER_OPTIONS = loadJson("character_options.json");
const RECIPES = loadJson("recipes.json");
const WORLD_EVENTS = loadJson("world_events.json");
const RACES = loadJson("races.json", true);
const JOBS = loadJson("jobs.json", true);

const FACTION_NAMES = [
  "Adventurer Guild",
  "BlackSmith",
  "Alchemist",
  "Tavern Circle",
  "Wilds",
  "Shadow Court",
  "Sky Choir",
  "Sea Court",
];

const DEFAULT_SESSION = {
  location: "Kota Utama",
  race: "Human",
  job: "Jobless",
  title: "Wanderer",
  level: 1,
  stat_points: 0,
  created: false,
  hp: 100,
  max_hp: 100,
  sp: 50,
  max_sp: 50,
  gold: 40,
  exp: 0,
  inventory: [],
  equipped: { weapon: null, armor: null, trinket: null, backpack: null },
  base_stats: {
    str: 10,
    agi: 10,
    vit: 10,
    int: 10,
    dex: 10,
    luk: 10,
    tec: 10,
    men: 10,
    crt: 10,
  },
  derived_stats: {},
  battle: null,
  quests: [],
  quest_offers: [],
  last_encounter: null,
  last_loot: [],
  gear_upgrades: {},
  skill_cooldowns: {},
  race_power_cooldowns: {},
  companions: [],
  reputation: {},
  achievements: [],
  party_role: "member",
  party_tag: null,
  battle_context: {},
  registered_at_guild: false,
  registered_at_receptionist: false,
  tier0_race_skills: {},
  tier0_job_skills_by_job: {},
};

const DEFAULT_WORLD_STATE = {
  event: null,
  turns_left: 0,
  turn_counter: 0,
  history: [],
  parties: {},
  chronicle: [],
};

const MAIN_SERVICE_LOCATIONS = {
  "Kedai Petualang": "Tavern Keeper",
  "Adventurer Guild": "Guild Clerk",
  "Kedai Perbatasan": "Frontier Clerk",
  "Kota Utama": "City Clerk",
  BlackSmith: "Blacksmith",
  Alchemist: "Alchemist",
};

const SERVICE_ACTIONS_BY_LOCATION = {
  "Kota Utama": [
    ["cityhall", "City Hall", "Info kota, help, world state"],
    ["travel", "Travel", "Pindah ke lokasi lain"],
    ["rest", "Rest", "Istirahat di area aman"],
  ],
  "Adventurer Guild": [
    ["guild", "Guild Desk", "Registrasi petualang dan quest"],
    ["questboard", "Quest Board", "Lihat quest yang tersedia"],
    ["changejob", "Job Office", "Ubah job di guild"],
  ],
  BlackSmith: [
    ["blacksmith", "Forge Desk", "Lihat pandai besi dan upgrade gear"],
    ["upgrade", "Upgrade", "Tingkatkan weapon atau armor"],
    ["shop", "Shop", "Beli equipment"],
  ],
  Alchemist: [
    ["alchemist", "Alchemy Desk", "Lihat alchemist dan upgrade trinket"],
    ["upgrade", "Upgrade", "Tingkatkan trinket"],
    ["shop", "Shop", "Beli item dan potion"],
  ],
  "Kedai Petualang": [
    ["tavern", "Tavern Counter", "Rest, companion, dan supply"],
    ["rest", "Rest", "Pulihkan HP di penginapan"],
    ["companions", "Companions", "Lihat companion yang dimiliki"],
    ["recruit", "Recruit", "Rekrut companion baru"],
    ["shop", "Shop", "Beli item"],
  ],
  "Kedai Perbatasan": [
    ["frontier", "Frontier Post", "Travel, explore, dan supply"],
    ["travel", "Travel", "Pindah lokasi"],
    ["explore", "Explore", "Jelajah area sekitar"],
    ["shop", "Shop", "Beli item perjalanan"],
  ],
};

const LOCATION_TO_REGION = Object.fromEntries(
  Object.entries(MAP.Etherial || {}).flatMap(([region, locations]) =>
    (locations || []).map((location) => [location, region])
  )
);

function allLocations() {
  return Object.values(MAP.Etherial || {}).flat();
}

function findLocation(query) {
  const normalized = normalizeName(query).toLowerCase();
  for (const location of allLocations()) {
    if (location.toLowerCase() === normalized) {
      return location;
    }
  }
  for (const location of allLocations()) {
    if (location.toLowerCase().includes(normalized)) {
      return location;
    }
  }
  return null;
}

function normalizeName(value) {
  return String(value ?? "").trim().split(/\s+/).join(" ");
}

function loadCommandChannels() {
  try {
    return cfg.command_channels && typeof cfg.command_channels === "object" ? cfg.command_channels : {};
  } catch {
    return {};
  }
}

function saveCommandChannels(mapping) {
  try {
    const nextCfg = { ...cfg, command_channels: mapping };
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(nextCfg, null, 2), "utf8");
    return true;
  } catch {
    return false;
  }
}

function resolveAllowedEntries(entries) {
  if (!entries) {
    return [];
  }
  if (typeof entries === "string") {
    return [entries];
  }
  if (Array.isArray(entries)) {
    return [...entries];
  }
  return [];
}

function catalogFrom(data) {
  return data && typeof data === "object" ? data : {};
}

function raceCatalog() {
  return catalogFrom(RACES);
}

function jobCatalog() {
  return catalogFrom(JOBS);
}

function itemCatalog() {
  return catalogFrom(ITEMS);
}

function recipeCatalog() {
  return catalogFrom(RECIPES);
}

function worldEventCatalog() {
  return catalogFrom(WORLD_EVENTS);
}

function monsterCatalog() {
  const catalog = {};
  for (const [location, monsters] of Object.entries(MONSTERS)) {
    if (Array.isArray(monsters)) {
      for (const monster of monsters) {
        if (monster.name) {
          catalog[monster.name] = { ...monster, location };
        }
      }
    }
  }
  return catalog;
}

function findInCatalog(catalog, name) {
  const normalized = normalizeName(name).toLowerCase();
  if (!normalized) {
    return null;
  }

  const directKey = Object.keys(catalog).find((key) => key.toLowerCase() === normalized);
  if (directKey) {
    return { key: directKey, data: catalog[directKey] };
  }

  const partialKey = Object.keys(catalog).find((key) => key.toLowerCase().includes(normalized));
  if (partialKey) {
    return { key: partialKey, data: catalog[partialKey] };
  }

  return null;
}

function findRace(name) {
  return findInCatalog(raceCatalog(), name);
}

function findJob(name) {
  return findInCatalog(jobCatalog(), name);
}

function findItem(name) {
  return findInCatalog(itemCatalog(), name);
}

function findRecipe(name) {
  return findInCatalog(recipeCatalog(), name);
}

function stationForLocation(location) {
  if (Object.prototype.hasOwnProperty.call(MAIN_SERVICE_LOCATIONS, location)) {
    return location;
  }
  return MAIN_SERVICE_LOCATIONS[location] || null;
}

function itemWeightValue(itemName) {
  const item = findItem(itemName);
  const value = item?.data?.weight ?? item?.data?.stats?.weight ?? 0;
  return Number(value) || 0;
}

function itemWeightText(itemName) {
  const item = findItem(itemName);
  const data = item?.data;
  if (!data || typeof data !== "object") {
    return null;
  }
  const weight = data.weight;
  if (weight === null || weight === undefined) {
    return null;
  }
  const unit = data.weight_unit || "kg";
  return `${weight} ${unit}`;
}

function itemPrice(itemName) {
  const item = findItem(itemName);
  if (!item?.data) {
    return null;
  }
  return Number.parseInt(item.data.price || 0, 10);
}

function itemDetailLines(itemName) {
  const item = itemCatalog()[itemName] || {};
  const lines = [];
  if (item && typeof item === "object") {
    if (item.description) {
      lines.push(item.description);
    }
    const weightText = itemWeightText(itemName);
    if (weightText) {
      lines.push(`Berat: ${weightText}`);
    }
  }
  return lines;
}

function inventoryCounts(session) {
  const counts = {};
  for (const itemName of session?.inventory || []) {
    counts[itemName] = (counts[itemName] || 0) + 1;
  }
  return counts;
}

function inventoryMaterialCounts(session) {
  return inventoryCounts(session);
}

function currentInventoryWeight(session) {
  const total = (session?.inventory || []).reduce((sum, itemName) => sum + itemWeightValue(itemName), 0);
  return Math.round(total * 100) / 100;
}

function currentWeightLimit(session) {
  const derived = session?.derived_stats || {};
  return Number(derived.weight_limit ?? 500);
}

function canAddItemByWeight(session, itemName, qty = 1) {
  const perItem = itemWeightValue(itemName);
  if (perItem <= 0) {
    return true;
  }
  const current = currentInventoryWeight(session);
  const limit = currentWeightLimit(session);
  const required = perItem * Math.max(0, Number(qty) || 0);
  return current + required <= limit + 1e-9;
}

function maxAddableQuantity(session, itemName) {
  const weight = itemWeightValue(itemName);
  if (weight <= 0) {
    return 999999;
  }
  const remaining = currentWeightLimit(session) - currentInventoryWeight(session);
  return Math.max(0, Math.floor(remaining / weight));
}

function addItem(session, itemName, qty = 1) {
  if (!canAddItemByWeight(session, itemName, qty)) {
    return false;
  }
  session.inventory = session.inventory || [];
  for (let index = 0; index < qty; index += 1) {
    session.inventory.push(itemName);
  }
  return true;
}

function removeItem(session, itemName, qty = 1) {
  session.inventory = session.inventory || [];
  let removed = 0;
  session.inventory = session.inventory.filter((name) => {
    if (name === itemName && removed < qty) {
      removed += 1;
      return false;
    }
    return true;
  });
  return removed === qty;
}

function canPayRequirements(session, requirements, multiplier = 1) {
  const counts = inventoryMaterialCounts(session);
  for (const [itemName, amount] of Object.entries(requirements || {})) {
    if ((counts[itemName] || 0) < amount * multiplier) {
      return [false, itemName];
    }
  }
  return [true, null];
}

function consumeRequirements(session, requirements, multiplier = 1) {
  for (const [itemName, amount] of Object.entries(requirements || {})) {
    removeItem(session, itemName, amount * multiplier);
  }
}

function recipeAvailableAtLocation(recipeName, location) {
  const recipe = recipeCatalog()[recipeName];
  if (!recipe) {
    return false;
  }
  const requiredStation = recipe.station;
  const currentStation = stationForLocation(location);
  return requiredStation === currentStation || requiredStation === location;
}

function raceModifierText(raceName) {
  const race = findRace(raceName);
  if (!race?.key) {
    return "Race tidak dikenal.";
  }
  const bonuses = race.data?.bonuses || {};
  const bonusText = Object.entries(bonuses).map(([key, value]) => `${key}+${value}`).join(", ") || "Tidak ada bonus";
  return `${race.key}: ${race.data?.description || ""} | Bonus: ${bonusText}`;
}

function jobModifierText(jobName) {
  const job = findJob(jobName);
  if (!job?.key) {
    return "Job tidak dikenal.";
  }
  const bonuses = job.data?.bonuses || {};
  const bonusText = Object.entries(bonuses).map(([key, value]) => `${key}+${value}`).join(", ") || "Tidak ada bonus";
  return `${job.key}: ${job.data?.description || ""} | Bonus: ${bonusText}`;
}

function questId() {
  return `Q${Math.floor(1000 + Math.random() * 9000)}`;
}

function resolveCharacterBonuses(session) {
  const bonuses = {
    hp: 0,
    attack: 0,
    defense: 0,
    mana: 0,
    luck: 0,
    craft: 0,
    travel: 0,
    exp: 0,
    gold: 0,
    heal: 0,
  };

  const sources = [
    [session?.race, raceCatalog()],
    [session?.job, jobCatalog()],
  ];

  for (const [sourceName, sourceCatalog] of sources) {
    if (sourceName && sourceCatalog[sourceName]) {
      for (const [key, value] of Object.entries(sourceCatalog[sourceName].bonuses || {})) {
        bonuses[key] = (bonuses[key] || 0) + Number(value || 0);
      }
    }
  }

  return bonuses;
}

function resolveEquipmentBonuses(session) {
  const bonuses = {};
  for (const slot of Object.keys(session?.equipped || {})) {
    const itemName = session?.equipped?.[slot];
    if (!itemName) {
      continue;
    }
    const item = findItem(itemName);
    const itemBonuses = item?.data?.bonuses || item?.data?.stats || {};
    for (const [key, value] of Object.entries(itemBonuses)) {
      if (typeof value === "number") {
        bonuses[key] = (bonuses[key] || 0) + value;
      }
    }
  }
  return bonuses;
}

function ensureSession(session) {
  const merged = structuredClone(DEFAULT_SESSION);
  const input = session || {};

  for (const [key, defaultValue] of Object.entries(DEFAULT_SESSION)) {
    if (!(key in input)) {
      continue;
    }
    if (defaultValue && typeof defaultValue === "object" && !Array.isArray(defaultValue) && input[key] && typeof input[key] === "object" && !Array.isArray(input[key])) {
      merged[key] = { ...merged[key], ...input[key] };
    } else {
      merged[key] = input[key];
    }
  }

  if (!Array.isArray(merged.inventory)) {
    merged.inventory = [];
  }
  if (!Array.isArray(merged.quests)) {
    merged.quests = [];
  }
  if (!Array.isArray(merged.quest_offers)) {
    merged.quest_offers = [];
  }
  if (!merged.equipped || typeof merged.equipped !== "object") {
    merged.equipped = structuredClone(DEFAULT_SESSION.equipped);
  }
  for (const slot of ["weapon", "armor", "trinket", "backpack"]) {
    if (!(slot in merged.equipped)) {
      merged.equipped[slot] = null;
    }
  }
  if (!merged.gear_upgrades || typeof merged.gear_upgrades !== "object") merged.gear_upgrades = {};
  if (!Array.isArray(merged.companions)) merged.companions = [];
  if (!merged.reputation || typeof merged.reputation !== "object") merged.reputation = {};
  if (!Array.isArray(merged.achievements)) merged.achievements = [];
  if (!merged.party_role) merged.party_role = "member";
  if (!merged.party_tag) merged.party_tag = null;
  if (!merged.battle_context || typeof merged.battle_context !== "object") merged.battle_context = {};
  if (!merged.tier0_race_skills || typeof merged.tier0_race_skills !== "object") merged.tier0_race_skills = {};
  if (!merged.tier0_job_skills_by_job || typeof merged.tier0_job_skills_by_job !== "object") merged.tier0_job_skills_by_job = {};

  if (!merged.race) merged.race = DEFAULT_SESSION.race;
  if (!merged.job) merged.job = DEFAULT_SESSION.job;
  if (!merged.registered_at_guild && merged.registered_at_receptionist) {
    merged.registered_at_guild = true;
  }

  merged.bonuses = resolveCharacterBonuses(merged);
  merged.max_hp = Math.max(merged.max_hp || 100, 100 + (merged.bonuses.hp || 0));
  merged.hp = Math.min(merged.hp ?? merged.max_hp, merged.max_hp);

  if ((merged.level || 1) > 0 && merged.race) {
    const raceKey = merged.race;
    const jobKey = merged.job;
    const level = merged.level || 1;

    if (!merged.base_stats) {
      merged.base_stats = RACES[raceKey.toLowerCase()]?.base_stats ? stats.loadRaceStats(RACES, raceKey) : structuredClone(DEFAULT_SESSION.base_stats);
    }

    const jobBonus = stats.loadJobStats(JOBS, jobKey);
    const combined = stats.combineBaseStats(merged.base_stats || {}, jobBonus);
    const equipBonus = resolveEquipmentBonuses(merged);
    merged.derived_stats = stats.calculateDerivedStats(combined, level, equipBonus);
    merged.max_hp = merged.derived_stats.max_hp ?? merged.max_hp;
    merged.max_sp = merged.derived_stats.max_sp ?? merged.max_sp;
    merged.hp = merged.hp ?? merged.max_hp;
    merged.sp = merged.sp ?? merged.max_sp;
  }

  return merged;
}

function defaultWorldState() {
  return structuredClone(DEFAULT_WORLD_STATE);
}

function ensureWorldState(state) {
  const merged = defaultWorldState();
  for (const [key, value] of Object.entries(state || {})) {
    merged[key] = value;
  }
  if (!Array.isArray(merged.history)) merged.history = [];
  if (!merged.parties || typeof merged.parties !== "object") merged.parties = {};
  if (!Array.isArray(merged.chronicle)) merged.chronicle = [];
  return merged;
}

function currentInventoryWeightLimitSummary(session) {
  return {
    weight: currentInventoryWeight(session),
    limit: currentWeightLimit(session),
  };
}

function statBlock(session) {
  const weapon = session?.equipped?.weapon || "None";
  const armor = session?.equipped?.armor || "None";
  const trinket = session?.equipped?.trinket || "None";
  const backpack = session?.equipped?.backpack || "None";
  const active = (session?.quests || []).filter((quest) => quest?.status === "active");
  const bonuses = session?.bonuses || resolveCharacterBonuses(session);
  const battleBonus = battleStatBonus(session);

  return [
    `Ras: ${session?.race || "Human"} | Job: ${session?.job || "Jobless"}`,
    `Title: ${session?.title || "Wanderer"}`,
    `Lokasi: ${session?.location || "Kota Utama"}`,
    `HP: ${session?.hp || 0}/${session?.max_hp || 0}`,
    `Level: ${session?.level || 1} | EXP: ${session?.exp || 0}`,
    `Gold: ${session?.gold || 0}`,
    `Weapon: ${weapon}`,
    `Armor: ${armor}`,
    `Trinket: ${trinket}`,
    `Backpack: ${backpack}`,
    `Quest aktif: ${active.length}`,
    `Bonus aktif: atk+${battleBonus.attack} def+${battleBonus.defense} craft+${bonuses.craft || 0} luck+${bonuses.luck || 0}`,
  ].join("\n");
}

function battleStatBonus(session) {
  return {
    attack: 0,
    defense: 0,
  };
}

function servicesForLocation(location) {
  return (SERVICE_ACTIONS_BY_LOCATION[location] || []).map((entry) => entry[1]);
}

function guildRegistered(session) {
  return Boolean(session?.registered_at_guild || session?.registered_at_receptionist);
}

function locationServiceLines(location) {
  const region = LOCATION_TO_REGION[location] || "Wilayah Tak Dikenal";
  const npcName = MAIN_SERVICE_LOCATIONS[location] || "NPC";
  const actions = SERVICE_ACTIONS_BY_LOCATION[location] || [];
  const lines = [
    `**${npcName}** menatapmu dengan tenang dari ${location}.`,
    `Area: ${region}`,
    "Gunakan command khusus lokasi ini untuk berinteraksi dengan NPC setempat.",
  ];
  if (actions.length > 0) {
    const actionText = actions.map(([command]) => `\`!${command}\``).join(", ");
    lines.push(`Command tersedia: ${actionText}`);
  }
  return lines;
}

function receptionistLines(location) {
  return locationServiceLines(location);
}

function createQuestOffer(session, location, kind, title, objectiveType, target, count, rewardGold, rewardItems, branches = null) {
  return {
    id: questId(),
    giver: MAIN_SERVICE_LOCATIONS[location] || "Receptionist",
    location,
    kind,
    title,
    description: title,
    objective: { type: objectiveType, target, count },
    progress: 0,
    count,
    reward: { gold: rewardGold, items: rewardItems },
    branches: branches || [],
    branch_selected: null,
    status: "available",
  };
}

function questRewardTemplate(kind, worldState = null) {
  const pools = {
    hunt: [[25, ["Health Potion"]]],
    collect: [[20, ["Health Potion"]]],
    visit: [[18, ["Health Potion"]]],
  };
  const pool = pools[kind] || pools.hunt;
  const [rewardGold, rewardItems] = pool[Math.floor(Math.random() * pool.length)];
  const worldBonus = Math.max(0, eventModifier(worldState || {}, "quest_bonus", 0));
  const adjustedGold = Math.round(rewardGold * (1 + worldBonus / 100));
  return { gold: adjustedGold, items: [...rewardItems] };
}

function randomMonsterForLocation(location) {
  if (MONSTERS[location]) {
    const list = MONSTERS[location];
    return list[Math.floor(Math.random() * list.length)] || null;
  }
  const region = LOCATION_TO_REGION[location];
  if (!region) {
    return null;
  }
  const possible = [];
  for (const loc of MAP.Etherial?.[region] || []) {
    possible.push(...(MONSTERS[loc] || []));
  }
  return possible.length > 0 ? possible[Math.floor(Math.random() * possible.length)] : null;
}

function activeWorldEvent(worldState) {
  const event = worldState?.event;
  return event && typeof event === "object" ? event : null;
}

function pickWorldEvent() {
  const events = worldEventCatalog();
  const list = Array.isArray(events) ? events : Object.values(events || {});
  if (list.length === 0) {
    return null;
  }
  return structuredClone(list[Math.floor(Math.random() * list.length)]);
}

function tickWorldTurn(worldState, trigger = "travel") {
  const next = ensureWorldState(worldState);
  next.turn_counter = Number(next.turn_counter || 0) + 1;
  let event = activeWorldEvent(next);

  if (event) {
    next.turns_left = Math.max(0, Number(next.turns_left || 0) - 1);
    if (next.turns_left <= 0) {
      next.history.push(event.name);
      next.event = null;
      next.turns_left = 0;
      event = null;
    }
  }

  if (!event && Math.random() < 0.35) {
    event = pickWorldEvent();
    if (event) {
      next.event = event;
      next.turns_left = Number(event.duration_turns || 3);
      next.history.push(event.name);
    }
  }

  return next;
}

function eventModifier(worldState, key, defaultValue = 0) {
  const event = activeWorldEvent(worldState);
  if (!event) {
    return defaultValue;
  }
  return Number(event[key] ?? defaultValue);
}

function eventFlavor(worldState) {
  const event = activeWorldEvent(worldState);
  if (!event) {
    return "Tidak ada event dunia aktif saat ini.";
  }
  return `**${event.name}** | ${event.flavor || ""} | Sisa putaran: ${worldState?.turns_left || 0}`;
}

function generateQuestOffers(location, worldState = null) {
  const region = LOCATION_TO_REGION[location] || "Kota Utama";
  const regionMonsters = [];
  for (const loc of MAP.Etherial?.[region] || []) {
    regionMonsters.push(...(MONSTERS[loc] || []));
  }

  const offers = [];
  if (regionMonsters.length > 0) {
    const monster = regionMonsters[Math.floor(Math.random() * regionMonsters.length)];
    const reward = questRewardTemplate("hunt", worldState);
    offers.push(createQuestOffer(null, location, "hunt", `Hunt: Singkirkan ${monster.name}`, "hunt", monster.name, Math.floor(2 + Math.random() * 3), reward.gold, reward.items));
  }

  const itemEntries = Object.entries(itemCatalog());
  const [itemName, itemData] = itemEntries.length > 0 ? itemEntries[Math.floor(Math.random() * itemEntries.length)] : ["Health Potion", { name: "Health Potion" }];
  let reward = questRewardTemplate("collect", worldState);
  offers.push(createQuestOffer(null, location, "collect", `Collect: Kumpulkan ${itemName}`, "collect", itemName, Math.floor(2 + Math.random() * 4), reward.gold, reward.items));

  const visitTargets = (MAP.Etherial?.[region] || []).filter((loc) => loc !== location);
  if (visitTargets.length > 0) {
    const target = visitTargets[Math.floor(Math.random() * visitTargets.length)];
    reward = questRewardTemplate("visit", worldState);
    offers.push(createQuestOffer(null, location, "visit", `Scout: Datangi ${target}`, "visit", target, 1, reward.gold, reward.items));
  }

  if (Math.random() < 0.75) {
    const branchTarget = regionMonsters.length > 0 ? regionMonsters[Math.floor(Math.random() * regionMonsters.length)].name : allLocations()[Math.floor(Math.random() * allLocations().length)];
    const branchRewardA = questRewardTemplate("hunt", worldState);
    const branchRewardB = questRewardTemplate("visit", worldState);
    const branchTitle = `Dilema Regional: Jejak ${branchTarget}`;
    offers.push(createQuestOffer(null, location, "branch", branchTitle, "branch", branchTarget, 1, branchRewardA.gold, branchRewardA.items, [
      { id: "warpath", title: "Warpath", kind: "hunt", objective: { type: "hunt", target: branchTarget, count: 3 }, reward: branchRewardA },
      { id: "veilpath", title: "Veilpath", kind: "visit", objective: { type: "visit", target: location, count: 1 }, reward: branchRewardB },
    ]));
  }

  return offers.slice(0, 3);
}

function questDisplayLine(quest) {
  const objective = quest.objective || {};
  const progress = quest.progress || 0;
  let base = `[${quest.id}] ${quest.title} | Target: ${objective.target} x${objective.count} | Progress: ${progress}/${objective.count} | Reward: ${quest.reward?.gold || 0} gold + ${(quest.reward?.items || []).join(", ")}`;
  const branches = quest.branches || [];
  if (branches.length > 0) {
    base += " | Branches: " + branches.map((branch) => `${branch.id}(${branch.title})`).join(", ");
  }
  return base;
}

module.exports = {
  ROOT,
  DATA_DIR,
  cfg,
  MAP,
  MONSTERS,
  ITEMS,
  CHARACTER_OPTIONS,
  RECIPES,
  WORLD_EVENTS,
  RACES,
  JOBS,
  FACTION_NAMES,
  DEFAULT_SESSION,
  DEFAULT_WORLD_STATE,
  MAIN_SERVICE_LOCATIONS,
  SERVICE_ACTIONS_BY_LOCATION,
  LOCATION_TO_REGION,
  allLocations,
  normalizeName,
  loadCommandChannels,
  saveCommandChannels,
  resolveAllowedEntries,
  raceCatalog,
  jobCatalog,
  itemCatalog,
  recipeCatalog,
  worldEventCatalog,
  monsterCatalog,
  findRace,
  findJob,
  findItem,
  findRecipe,
  itemWeightValue,
  itemWeightText,
  itemPrice,
  itemDetailLines,
  inventoryCounts,
  inventoryMaterialCounts,
  currentInventoryWeight,
  currentWeightLimit,
  canAddItemByWeight,
  maxAddableQuantity,
  addItem,
  removeItem,
  canPayRequirements,
  consumeRequirements,
  recipeAvailableAtLocation,
  stationForLocation,
  findLocation,
  raceModifierText,
  jobModifierText,
  questId,
  resolveCharacterBonuses,
  resolveEquipmentBonuses,
  ensureSession,
  defaultWorldState,
  ensureWorldState,
  currentInventoryWeightLimitSummary,
  statBlock,
  battleStatBonus,
  servicesForLocation,
  guildRegistered,
  locationServiceLines,
  receptionistLines,
  createQuestOffer,
  generateQuestOffers,
  questDisplayLine,
  questRewardTemplate,
  randomMonsterForLocation,
  activeWorldEvent,
  pickWorldEvent,
  tickWorldTurn,
  eventModifier,
  eventFlavor,
};