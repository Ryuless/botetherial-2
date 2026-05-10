"use strict";

const core = require("./game-core");
const stats = require("./stats");
const presentation = require("./presentation");

function helpPages() {
  return [
    {
      title: "⚔️ Character & Profil",
      color: presentation.COLOR_PRIMARY,
      commands: [
        ["createchar <race> <name>", "Buat atau ubah karakter"],
        ["profile", "Lihat profil karakter"],
        ["status", "Status karakter (HP, level, exp)"],
        ["stats", "Lihat statistik detail"],
        ["skills", "Lihat tier-0 skills yang dimiliki"],
        ["races", "Daftar ras tersedia"],
        ["jobs", "Daftar job/class tersedia"],
        ["racepowers", "Daftar ability ras kamu"],
        ["racepower <ability>", "Pakai ability ras"],
      ],
    },
    {
      title: "👥 Social & Companion",
      color: presentation.COLOR_SECONDARY,
      commands: [
        ["party <create|join|leave|info|disband>", "Kelola party channel"],
        ["companions", "Lihat companion yang dimiliki"],
        ["recruit <nama>", "Rekrut companion baru"],
        ["dismiss <nama>", "Lepas companion"],
        ["scene <aksi>", "Tampilkan adegan roleplay"],
        ["story", "Jalankan story event personal"],
        ["reputation [faction]", "Lihat reputasi faction"],
        ["achievements", "Lihat milestone terbuka"],
      ],
    },
    {
      title: "🗺️ Locations & NPC",
      color: presentation.COLOR_WORLD,
      commands: [
        ["cityhall", "City Hall - Kota Utama"],
        ["guild", "Adventurer Guild - Registrasi quest"],
        ["blacksmith", "BlackSmith - Upgrade weapon/armor"],
        ["alchemist", "Alchemist - Upgrade trinket"],
        ["tavern", "Tavern - Rest & companion"],
        ["frontier", "Frontier Post - Perjalanan"],
        ["map", "Tampilkan peta Etherial"],
        ["travel <lokasi>", "Pindah ke lokasi lain"],
        ["explore <lokasi>", "Jelajahi lokasi & dapat event"],
        ["bestiary [lokasi]", "Daftar monster di lokasi"],
      ],
    },
    {
      title: "💼 Items & Crafting",
      color: presentation.COLOR_ITEM,
      commands: [
        ["inventory", "Daftar inventory kamu"],
        ["use <item>", "Gunakan item consumable"],
        ["equip <item>", "Pasang equipment"],
        ["equipped", "Lihat equipment yang sedang dipakai"],
        ["unequip <slot>", "Lepas equipment"],
        ["recipes", "Lihat resep crafting"],
        ["craft <item> [qty]", "Buat item di station cocok"],
        ["upgrade <item>", "Tingkatkan equipment (di BlackSmith/Alchemist)"],
        ["shop", "Lihat toko lokasi"],
        ["buy <item> [qty]", "Beli item"],
      ],
    },
    {
      title: "📜 Quest & Battle",
      color: presentation.COLOR_QUEST,
      commands: [
        ["guild", "Guild desk - Registrasi dan lihat quest"],
        ["questboard", "Lihat quest di Guild"],
        ["acceptquest <nomor|id>", "Ambil quest"],
        ["questpath <id> <branch>", "Pilih cabang quest"],
        ["quests", "Lihat quest aktif"],
        ["completequest <id>", "Selesaikan quest"],
        ["battle", "Cek battle aktif"],
        ["startbattle", "Mulai battle encounter"],
        ["attack", "Serang musuh"],
        ["skill <nama>", "Pakai skill job"],
        ["flee", "Kabur dari battle"],
        ["loot <monster>", "Lihat loot table"],
      ],
    },
    {
      title: "🌍 World State",
      color: presentation.COLOR_WORLD,
      commands: [
        ["world", "Lihat state dunia"],
        ["event", "Lihat event dunia aktif"],
        ["help", "Tampilkan halaman help"],
      ],
    },
  ];
}

function createHelpEmbed(pageNumber = 0) {
  const pages = helpPages();
  const currentPage = pageNumber < 0 || pageNumber >= pages.length ? 0 : pageNumber;
  const pageData = pages[currentPage];
  const embed = presentation.createEmbed(
    `${pageData.title} — Page ${currentPage + 1}/${pages.length}`,
    "─────────────────────\nGunakan reaction untuk navigasi",
    pageData.color,
  );

  for (const [cmd, desc] of pageData.commands) {
    presentation.addField(embed, `\`\`${core.cfg.prefix || "!"}${cmd}\`\``, `└─ ${desc}`, false);
  }

  presentation.setFooter(embed, "⬅️ Prev  •  🏠 Home  •  Next ➡️");
  return embed;
}

function buildRaceCommandPayload() {
  const embed = presentation.createMenuEmbed(
    "Daftar Ras Etherial",
    "Pilih salah satu ras untuk karakter kamu • React untuk navigasi",
    presentation.COLOR_RACE,
    "🧬",
  );
  const races = core.raceCatalog();
  const raceList = Object.entries(races);

  const emojiMap = {
    human: "🧑",
    elf: "🧝",
    orc: "👹",
    dwarf: "🛡️",
    vampire: "🦇",
    dragontamer: "🐉",
    fairy: "🧚",
    griffin: "🦅",
    nymph: "🌿",
    werewolf: "🐺",
    pegasus: "🦄",
    mermaid: "🧜",
    angel: "😇",
    demon: "😈",
    bunny: "🐰",
  };

  // Use compact inline fields for nicer layout (Discord will arrange them in columns)
  for (const [raceKey, data] of raceList) {
    const raceStats = data.base_stats || {};
    const desc = (data.description || "").split(".")[0] || ""; // short description
    const statsText = `STR ${raceStats.str ?? 10} • AGI ${raceStats.agi ?? 10} • VIT ${raceStats.vit ?? 10}`;
    const statsText2 = `INT ${raceStats.int ?? 10} • DEX ${raceStats.dex ?? 10} • LUK ${raceStats.luk ?? 10}`;
    const trait = data.special_trait || "—";
    const nameDisplay = (emojiMap[raceKey] || "⚔️") + "  " + (data.name || raceKey);
    const value = `*${desc}*\n\n${statsText}\n${statsText2}\n**Trait:** ${trait}`;
    // add as inline for compact 2-3 column layout
    presentation.addMenuItem(embed, nameDisplay, value, "", true);
  }

  presentation.setFooter(
    embed,
    `${presentation.formatMenuFooter(null, null, `Total: ${raceList.length} Ras`)}\n💡 Gunakan !createchar <ras> <nama> untuk membuat karakter`,
  );
  return embed;
}

function buildJobCommandPayload() {
  const embed = presentation.createMenuEmbed(
    "Daftar Class / Job",
    "Spesialisasi untuk karakter kamu • React untuk navigasi",
    presentation.COLOR_JOB,
    "⚔️",
  );

  const jobList = Object.entries(core.jobCatalog());
  for (const [jobName, data] of jobList) {
    const jobStats = data.base_stats || {};
    const desc = data.description || "";
    const statsText = `STR:${jobStats.str ?? 10} | AGI:${jobStats.agi ?? 10} | VIT:${jobStats.vit ?? 10}\nINT:${jobStats.int ?? 10} | WIS:${jobStats.wis ?? 10} | LUK:${jobStats.luk ?? 10}`;
    const trait = data.special_trait || "—";
    const levelReq = data.level_requirement || 0;
    const value = `${desc}\n\n\`\`${statsText}\`\`\`\n**Trait:** ${trait} | **Req Lvl:** ${levelReq}`;
    presentation.addMenuItem(embed, jobName, value, "⚔️", false);
  }

  presentation.setFooter(embed, `${presentation.formatMenuFooter(null, null, `Total: ${jobList.length} Job`)}\n💡 Gunakan !createchar <ras> <nama> untuk membuat karakter`);
  return embed;
}

function buildProfilePayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet.\nUse \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.\nExample: \`${core.cfg.prefix || "!"}createchar Elf Aisha\``,
      0xE74C3C,
    );
  }

  const embed = presentation.createEmbed("👤 Character Profile", session.title || "Wanderer", presentation.COLOR_PRIMARY);
  presentation.addField(embed, "🧬 Race", session.race || "Unknown", true);
  presentation.addField(embed, "⚔️ Job", session.job || "Novice", true);
  presentation.addField(embed, "📍 Location", session.location || "Unknown", true);

  const level = session.level || 1;
  const exp = session.exp || 0;
  presentation.addField(embed, "📊 Level & EXP", `Lv. ${level} • EXP: ${exp}/${level * 100}`, false);
  presentation.addField(embed, "❤️ Health & Mana", `HP: ${session.hp || session.max_hp || 100}/${session.max_hp || 100} • MP: ${session.sp || session.max_sp || 50}/${session.max_sp || 50}`, false);
  presentation.addField(embed, "💰 Resources", `Gold: ${session.gold || 0} • Items: ${(session.inventory || []).length} • Weight: ${core.currentInventoryWeight(session).toFixed(2)}/${core.currentWeightLimit(session).toFixed(2)} kg`, false);

  const derived = session.derived_stats || {};
  if (Object.keys(derived).length > 0) {
    presentation.addField(embed, "⚔️ Combat Stats", `ATK: ${derived.atk || 0} | MATK: ${derived.matk || 0}\nDEF: ${derived.def || 0} | MDEF: ${derived.mdef || 0}\nCRIT: ${(derived.crit || 0).toFixed(1)}%`, false);
  }

  presentation.setFooter(embed, "Use !stats for detailed stat breakdown | Gold: " + (session.gold || 0));
  return embed;
}

function buildStatPointsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const pts = session.stat_points || 0;
  return presentation.createEmbed(
    "🔢 Unspent Stat Points",
    `You have **${pts}** SP (Stat Points). Use \`${core.cfg.prefix || "!"}alloc <stat> <amount>\` to allocate.`,
    0x3498DB,
  );
}

function buildAllocPayload(session, stat, amount = 1) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  if (!stat) {
    return presentation.createEmbed(
      "❌ Missing Stat",
      `Usage: \`${core.cfg.prefix || "!"}alloc <stat> <amount>\`\nValid: str, agi, vit, int, dex, luk, tec, men, crt`,
      0xE74C3C,
    );
  }

  const valid = new Set(["str", "agi", "vit", "int", "dex", "luk", "tec", "men", "crt"]);
  const normalized = String(stat).toLowerCase();
  if (!valid.has(normalized)) {
    return presentation.createEmbed(
      "❌ Invalid Stat",
      "Valid stats: str, agi, vit, int, dex, luk, tec, men, crt",
      0xE74C3C,
    );
  }

  const pts = session.stat_points || 0;
  if (amount <= 0 || amount > pts) {
    return presentation.createEmbed(
      "❌ Invalid Amount",
      `You have ${pts} stat point(s). Specify a valid amount.`,
      0xE74C3C,
    );
  }

  return presentation.createEmbed(
    "✅ Stat Allocated",
    `Added **${amount}** to **${normalized.toUpperCase()}**. Remaining points: ${pts - amount}`,
    0x2ECC71,
  );
}

function buildStatsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet.\nUse \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  return stats.formatStatsDisplay(session);
}

function buildSkillsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet.\nUse \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed(
    "⚡ Tier-0 Skills",
    `Skill dari ras **${session.race}**`,
    presentation.COLOR_SKILL,
    "⚡",
  );

  const skills = session.tier0_race_skills || [];
  if (skills.length === 0) {
    presentation.addField(embed, "Tidak Ada Skill", "Belum ada skill yang di-roll. Recreate karakter atau hubungi admin.", false);
  } else {
    for (const skill of skills) {
      const line = `**${skill.name}**\nDamage: ${skill.damage || 0} | Mana: ${skill.mana_cost || 0} | Type: ${skill.skill_type || 'Support'}\nElement: ${skill.element || 'None'} | Cast: ${skill.cast_time || 0}s | Duration: ${skill.duration || 0}s\n_${skill.description || 'Tidak ada deskripsi'}_`;
      presentation.addField(embed, `\`${skill.id}\``, line, false);
    }
  }

  presentation.setFooter(embed, `Total Skills: ${skills.length} | Upgrade tersedia di setiap level`);
  return embed;
}

function buildMapPayload() {
  const embed = presentation.createMenuEmbed(
    "Map of Etherial",
    "Jelajahi berbagai region dalam dunia Etherial",
    presentation.COLOR_WORLD,
    "🗺️",
  );

  const regionEmoji = {
    Temperate: "🌲",
    Tropical: "🏝️",
    Arctic: "❄️",
    Magiclands: "✨",
    Underground: "⛏️",
  };

  let total = 0;
  for (const [region, locs] of Object.entries(core.MAP.Etherial || {})) {
    const emoji = regionEmoji[region] || "📍";
    total += locs.length;
    const locationsText = `${emoji} **${region}**\n${locs.map((loc) => `\`${loc}\``).join(", ")}`;
    presentation.addField(embed, `${emoji} ${region} (${locs.length})`, locationsText, false);
  }

  presentation.setFooter(embed, `${presentation.formatMenuFooter(null, null, `Total Locations: ${total}`)}\n💡 Gunakan !travel <lokasi> untuk berpindah`);
  return embed;
}

function buildTravelPayload(session, location, worldState) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  if (!location) {
    return presentation.createEmbed(
      "❌ Missing Location",
      `Your current location: **${session.location}**\nUse \`${core.cfg.prefix || "!"}map\` to view available locations.`,
      0xE74C3C,
    );
  }

  const destination = core.findLocation(location);
  if (!destination) {
    return presentation.createEmbed(
      "❌ Location Not Found",
      `Use \`${core.cfg.prefix || "!"}map\` to view available locations.`,
      0xE74C3C,
    );
  }

  const region = core.LOCATION_TO_REGION[destination] || "mysterious region";
  const eventText = core.eventFlavor(worldState || {});
  return presentation.createEmbed(
    `🚶 Traveled to ${destination}`,
    `You arrive at **${destination}** in ${region}. The air, scent, and atmosphere feel different here.\n\n${eventText}`,
    0x2ECC71,
  );
}

function buildCityHallPayload(session, prefix = "!") {
  if (!session?.created) {
    const embed = presentation.createMenuEmbed("City Hall", "Kamu belum membuat karakter", 0xE74C3C, "🏛️");
    presentation.addField(embed, "Error", `Gunakan \`${prefix}createchar <ras> <nama>\` untuk membuat karakter terlebih dahulu`, false);
    return embed;
  }

  const location = session.location || "Kota Utama";
  const embed = presentation.createMenuEmbed(`City Hall - ${location}`, core.locationServiceLines(location).join("\n"), 0x3498DB, "🏛️");
  presentation.addField(embed, "NPC", core.MAIN_SERVICE_LOCATIONS[location] || "City Clerk", true);
  presentation.addField(embed, "Layanan Kota", [`\`${prefix}map\``, `\`${prefix}world\``, `\`${prefix}help\``, `\`${prefix}travel <lokasi>\``, `\`${prefix}rest\``].join("\n"), false);
  return embed;
}

function buildGuildPayload(session, worldState, prefix = "!") {
  if (!session?.created) {
    const embed = presentation.createMenuEmbed("Adventurer Guild", "Kamu belum membuat karakter", 0xE74C3C, "📋");
    presentation.addField(embed, "Error", `Gunakan \`${prefix}createchar <ras> <nama>\` untuk membuat karakter terlebih dahulu`, false);
    return { embed, offers: [] };
  }

  const offers = core.generateQuestOffers(session.location, worldState);
  const welcomeLines = core.locationServiceLines(session.location);
  const isFirstVisit = !core.guildRegistered(session);

  const description = isFirstVisit
    ? `${welcomeLines.join("\n")}\n\n✅ **Selamat datang!** Kamu sekarang terdaftar sebagai petualang di ${session.location}.`
    : welcomeLines.join("\n");

  const embed = presentation.createMenuEmbed(`Guild Board - ${session.location}`, description, presentation.COLOR_QUEST, "🛡️");
  presentation.addField(embed, "📌 Status Registrasi", core.guildRegistered(session) ? "✅ Sudah Terdaftar - Kamu dapat menerima quest" : "❌ Belum Terdaftar", false);

  const questsField = offers.map((quest, index) => `**${index + 1}**. ${core.questDisplayLine(quest)}`).join("\n");
  presentation.addField(embed, "🎯 Available Quests", questsField || "Tidak ada quest tersedia", false);
  presentation.addField(embed, "🏷️ Guild Services", [`\`${prefix}questboard\``, `\`${prefix}changejob\``, `\`${prefix}acceptquest <nomor>\``].join(" • "), false);
  presentation.addField(embed, "🌍 World State", core.eventFlavor(worldState || {}), false);
  presentation.setFooter(embed, `${presentation.formatMenuFooter(null, null, `Quests: ${offers.length}`)}\n💡 Gunakan !acceptquest <nomor> untuk menerima quest`);
  return { embed, offers };
}

function buildServiceLocationPayload(location, prefix = "!") {
  const titleMap = {
    BlackSmith: "BlackSmith",
    Alchemist: "Alchemist",
    "Kedai Petualang": "Tavern",
    "Kedai Perbatasan": "Frontier Post",
  };

  const title = `${titleMap[location] || location} - ${location}`;
  const colorMap = {
    BlackSmith: presentation.COLOR_ITEM,
    Alchemist: presentation.COLOR_SKILL,
    "Kedai Petualang": presentation.COLOR_COMPANION,
    "Kedai Perbatasan": presentation.COLOR_WORLD,
  };

  const iconMap = {
    BlackSmith: "⚒️",
    Alchemist: "⚗️",
    "Kedai Petualang": "🍺",
    "Kedai Perbatasan": "🧭",
  };

  const embed = presentation.createMenuEmbed(title, core.locationServiceLines(location).join("\n"), colorMap[location] || presentation.COLOR_PRIMARY, iconMap[location] || "📍");
  presentation.addField(embed, "NPC", core.MAIN_SERVICE_LOCATIONS[location] || "NPC", true);

  const serviceText = core.servicesForLocation(location).length > 0 ? core.servicesForLocation(location).map((service) => `\`${prefix}${service}\``).join("\n") : "Tidak ada layanan.";
  presentation.addField(embed, "Layanan", serviceText, false);
  return embed;
}

function buildInventoryPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("💼 Inventory", `${session.title}'s Items`, presentation.COLOR_ITEM, "🎒");
  const inventory = session.inventory || [];

  if (inventory.length === 0) {
    presentation.addField(embed, "Empty", "No items in inventory.", false);
  } else {
    let itemsText = "";
    for (const item of inventory) {
      const itemName = typeof item === "string" ? item : item.name || "Unknown";
      const qty = typeof item === "object" && item.qty ? ` (x${item.qty})` : "";
      itemsText += `• ${itemName}${qty}\n`;
    }
    presentation.addField(embed, `Items (${inventory.length})`, itemsText, false);
  }

  const weight = core.currentInventoryWeight(session);
  const maxWeight = core.currentWeightLimit(session);
  presentation.addField(embed, "📦 Weight", `${weight.toFixed(2)}/${maxWeight.toFixed(2)} kg`, true);
  presentation.addField(embed, "💰 Gold", session.gold || 0, true);

  presentation.setFooter(embed, `Use !equip <item>, !use <item>, or !drop <item>`);
  return embed;
}

function buildShopPayload(location) {
  const embed = presentation.createMenuEmbed("🏪 Shop", location || "Kedai Petualang", presentation.COLOR_ITEM, "🛍️");
  
  const itemCatalog = core.itemCatalog();
  const items = Object.entries(itemCatalog).slice(0, 10);

  let shopText = "";
  for (const [itemName, itemData] of items) {
    const price = itemData.price || 0;
    const rarity = itemData.rarity || "common";
    shopText += `**${itemName}** - ${price}g ⭐${rarity}\n`;
  }

  presentation.addField(embed, "Available Items", shopText || "No items available", false);
  presentation.setFooter(embed, `Use !buy <item> [qty] to purchase | Max 10 items shown`);
  return embed;
}

function buildRecipesPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("📜 Recipes", "Crafting Recipes", 0xE8DAEF, "⚒️");
  
  const recipeCatalog = core.recipeCatalog();
  const recipeEntries = Object.entries(recipeCatalog).slice(0, 15);

  let recipesText = "";
  for (const [recipeName, recipeData] of recipeEntries) {
    const ingredients = recipeData.ingredients ? Object.keys(recipeData.ingredients).join(", ") : "Unknown";
    const result = recipeData.result || "Unknown";
    recipesText += `**${recipeName}**: ${ingredients} → ${result}\n`;
  }

  presentation.addField(embed, "Known Recipes", recipesText || "No recipes available", false);
  presentation.setFooter(embed, `Use !craft <item> [qty] at a crafting station`);
  return embed;
}

function buildQuestBoardPayload(session, worldState) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("📋 Quest Board", "Available Quests", presentation.COLOR_QUEST, "📜");

  const activeEvent = core.activeWorldEvent(worldState || {});
  const quests = core.generateQuestOffers(session, worldState || {});

  if (quests.length === 0) {
    presentation.addField(embed, "No Quests", "Come back later!", false);
  } else {
    let questsText = "";
    for (let i = 0; i < Math.min(quests.length, 8); i++) {
      const q = quests[i];
      questsText += core.questDisplayLine(q) + "\n";
    }
    presentation.addField(embed, "Available Quests", questsText, false);
  }

  if (activeEvent) {
    presentation.addField(embed, "🌍 World Event", activeEvent.name || "Unknown Event", true);
  }

  presentation.setFooter(embed, `Use !acceptquest <number|id> to start a quest`);
  return embed;
}

function buildActiveQuestsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("🎯 Active Quests", `${session.title}'s Progress`, presentation.COLOR_QUEST, "📋");

  const activeQuests = session.active_quests || [];
  if (activeQuests.length === 0) {
    presentation.addField(embed, "No Active Quests", "Visit the Guild to accept quests!", false);
  } else {
    let questsText = "";
    for (const quest of activeQuests) {
      const questName = quest.name || "Unknown";
      const progress = quest.progress ? `${quest.progress.current}/${quest.progress.total}` : "—";
      questsText += `**${questName}** [${progress}]\n`;
    }
    presentation.addField(embed, "Quests", questsText, false);
  }

  presentation.setFooter(embed, `Use !questpath <id> <branch> to choose quest branches | !completequest <id> to finish`);
  return embed;
}

function buildBattleStatusPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const inBattle = session.in_battle || false;
  const battleInfo = session.battle_state || {};

  if (!inBattle) {
    return presentation.createEmbed("⚔️ Battle Status", "You are not in battle.\nUse `!startbattle` to begin!", 0x95A5A6);
  }

  const embed = presentation.createEmbed("⚔️ Battle Status", session.title || "Character", presentation.COLOR_PRIMARY);
  
  presentation.addField(embed, "Enemy", battleInfo.enemy_name || "Unknown", true);
  presentation.addField(embed, "HP", `${battleInfo.player_hp || 0}/${session.max_hp || 100}`, true);
  presentation.addField(embed, "Enemy HP", `${battleInfo.enemy_hp || 0}/${battleInfo.enemy_max_hp || 100}`, true);
  
  presentation.addField(embed, "Turn", battleInfo.turn || 1, true);
  presentation.addField(embed, "Round", battleInfo.round || 1, true);

  presentation.setFooter(embed, `Use !attack, !skill <name>, or !flee`);
  return embed;
}

function buildBestiaryPayload(location) {
  const embed = presentation.createMenuEmbed("📚 Bestiary", location || "All Locations", 0x884EA0, "🐉");

  const monsterCatalog = core.monsterCatalog?.() || {};
  const monstersInLocation = Object.entries(monsterCatalog)
    .filter(([_, m]) => !location || m.location === location)
    .slice(0, 15);

  if (monstersInLocation.length === 0) {
    presentation.addField(embed, "No Monsters", "No monsters found in this location.", false);
  } else {
    let monstersText = "";
    for (const [monsterName, monsterData] of monstersInLocation) {
      const level = monsterData.level || 1;
      const rarity = monsterData.rarity || "common";
      monstersText += `**${monsterName}** (Lv. ${level}) ⭐${rarity}\n`;
    }
    presentation.addField(embed, "Monsters", monstersText, false);
  }

  presentation.setFooter(embed, `Use !loot <monster> for drop table`);
  return embed;
}

function buildPartyInfoPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("👥 Party Info", session.title || "Character", 0xA9DFBF, "👥");

  const partyInfo = session.party || {};
  const members = partyInfo.members || [];

  if (members.length === 0) {
    presentation.addField(embed, "Status", "Not in a party", true);
  } else {
    presentation.addField(embed, "Party Leader", partyInfo.leader || "Unknown", true);
    presentation.addField(embed, "Members", members.length.toString(), true);
    
    let membersText = "";
    for (const member of members.slice(0, 8)) {
      membersText += `• ${member}\n`;
    }
    presentation.addField(embed, "Party Members", membersText || "No members", false);
  }

  presentation.setFooter(embed, `Use !party <create|join|leave|disband>`);
  return embed;
}

function buildCompanionsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("🐾 Companions", session.title || "Character", 0xF8C471, "🐾");

  const companions = session.companions || [];

  if (companions.length === 0) {
    presentation.addField(embed, "No Companions", "Use !recruit <name> to recruit a companion.", false);
  } else {
    let companionsText = "";
    for (const companion of companions) {
      const compName = typeof companion === "string" ? companion : companion.name || "Unknown";
      const compLevel = typeof companion === "object" ? companion.level || 1 : 1;
      companionsText += `• **${compName}** (Lv. ${compLevel})\n`;
    }
    presentation.addField(embed, `Companions (${companions.length})`, companionsText, false);
  }

  presentation.setFooter(embed, `Use !recruit <name> to add | !dismiss <name> to remove`);
  return embed;
}

function buildAchievementsPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("🏆 Achievements", session.title || "Character", 0xF4D03F, "🏆");

  const achievements = session.achievements || [];
  const unlockedCount = Array.isArray(achievements) ? achievements.length : 0;

  if (unlockedCount === 0) {
    presentation.addField(embed, "Achievements", "No achievements unlocked yet.", false);
  } else {
    let achievementsText = "";
    for (const achievement of achievements.slice(0, 12)) {
      const achName = typeof achievement === "string" ? achievement : achievement.name || "Unknown";
      achievementsText += `🏅 ${achName}\n`;
    }
    presentation.addField(embed, `Unlocked (${unlockedCount})`, achievementsText, false);
  }

  presentation.setFooter(embed, `Unlock achievements through gameplay!`);
  return embed;
}

function buildReputationPayload(session) {
  if (!session?.created) {
    return presentation.createEmbed(
      "❌ No Character",
      `You haven't created a character yet. Use \`${core.cfg.prefix || "!"}createchar <race> <name>\` to create one.`,
      0xE74C3C,
    );
  }

  const embed = presentation.createMenuEmbed("📊 Reputation", session.title || "Character", 0xAED6F1, "⭐");

  const reputation = session.reputation || {};
  const factions = Object.entries(reputation).slice(0, 10);

  if (factions.length === 0) {
    presentation.addField(embed, "No Reputation", "Complete quests and events to gain reputation.", false);
  } else {
    let reputationText = "";
    for (const [faction, rep] of factions) {
      reputationText += `**${faction}**: ${rep.toFixed(0)} points\n`;
    }
    presentation.addField(embed, "Factions", reputationText, false);
  }

  presentation.setFooter(embed, `Reputation unlocks special items and events`);
  return embed;
}

module.exports = {
  helpPages,
  createHelpEmbed,
  buildRaceCommandPayload,
  buildJobCommandPayload,
  buildProfilePayload,
  buildStatPointsPayload,
  buildAllocPayload,
  buildStatsPayload,
  buildSkillsPayload,
  buildMapPayload,
  buildTravelPayload,
  buildCityHallPayload,
  buildGuildPayload,
  buildServiceLocationPayload,
  buildInventoryPayload,
  buildShopPayload,
  buildRecipesPayload,
  buildQuestBoardPayload,
  buildActiveQuestsPayload,
  buildBattleStatusPayload,
  buildBestiaryPayload,
  buildPartyInfoPayload,
  buildCompanionsPayload,
  buildAchievementsPayload,
  buildReputationPayload,
};