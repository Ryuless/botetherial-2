"use strict";

const fs = require("fs");
const path = require("path");
const {
  Client,
  GatewayIntentBits,
  Partials,
  EmbedBuilder,
} = require("discord.js");

const db = require("./db");
const core = require("./game-core");
const stats = require("./stats");
const commandData = require("./command-data");

const ROOT = path.resolve(__dirname, "..");
const CONFIG_PATH = path.join(ROOT, "config.json");

function readConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    return { token: null, prefix: "!" };
  }
  return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
}

function toDiscordEmbed(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const embed = new EmbedBuilder();
  if (payload.title) embed.setTitle(payload.title);
  if (payload.description) embed.setDescription(payload.description);
  if (payload.color !== undefined) embed.setColor(payload.color);
  if (payload.author) embed.setAuthor(payload.author);
  if (payload.footer) embed.setFooter(payload.footer);
  for (const field of payload.fields || []) {
    embed.addFields({ name: field.name, value: field.value ?? "", inline: Boolean(field.inline) });
  }
  return embed;
}

function sendPayload(message, payload) {
  if (typeof payload === "string") {
    return message.reply(payload);
  }
  if (payload && payload.embed) {
    return message.reply({ embeds: [toDiscordEmbed(payload.embed)] });
  }
  return message.reply({ embeds: [toDiscordEmbed(payload)] });
}

async function handleHelp(message) {
  return sendPayload(message, commandData.createHelpEmbed(0));
}

async function handleCommand(message, command, args, config) {
  const prefix = config.prefix || "!";
  const session = core.ensureSession(await db.getSessionAsync(message.author.id));
  const worldState = core.ensureWorldState(await db.getWorldStateAsync());

  if (command === "help" || command === "commands" || command === "helpbot") {
    return handleHelp(message);
  }
  if (command === "races" || command === "listraces") {
    return sendPayload(message, commandData.buildRaceCommandPayload());
  }
  if (command === "jobs" || command === "listjobs") {
    return sendPayload(message, commandData.buildJobCommandPayload());
  }
  if (command === "profile") {
    return sendPayload(message, commandData.buildProfilePayload(session));
  }
  if (command === "statpoints") {
    return sendPayload(message, commandData.buildStatPointsPayload(session));
  }
  if (command === "alloc") {
    const [stat, amountRaw] = args;
    const amount = Number.parseInt(amountRaw || "1", 10) || 1;
    if (session.created && stat && amount > 0 && amount <= (session.stat_points || 0)) {
      session.base_stats = session.base_stats || structuredClone(core.DEFAULT_SESSION.base_stats);
      session.base_stats[String(stat).toLowerCase()] = (session.base_stats[String(stat).toLowerCase()] || 0) + amount;
      session.stat_points = (session.stat_points || 0) - amount;
      const combined = stats.combineBaseStats(session.base_stats, stats.loadJobStats(core.JOBS, session.job));
      session.derived_stats = stats.calculateDerivedStats(combined, session.level || 1, core.resolveEquipmentBonuses(session));
      session.max_hp = session.derived_stats.max_hp;
      session.max_sp = session.derived_stats.max_sp;
      session.hp = Math.min(session.hp || session.max_hp, session.max_hp);
      session.sp = Math.min(session.sp || session.max_sp, session.max_sp);
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, commandData.buildAllocPayload(session, stat, amount));
  }
  if (command === "stats") {
    return sendPayload(message, commandData.buildStatsPayload(session));
  }
  if (command === "skills" || command === "listskills") {
    return sendPayload(message, commandData.buildSkillsPayload(session));
  }
  if (command === "map") {
    return sendPayload(message, commandData.buildMapPayload());
  }
  if (command === "travel") {
    const destination = args.join(" ").trim();
    const resolved = core.findLocation(destination);
    if (session.created && resolved) {
      const nextWorld = core.tickWorldTurn(worldState, "travel");
      session.location = resolved;
      session.last_encounter = null;
      await db.saveSessionAsync(message.author.id, session);
      await db.saveWorldStateAsync(nextWorld);
    }
    return sendPayload(message, commandData.buildTravelPayload(session, destination, worldState));
  }
  if (command === "cityhall" || command === "receptionist" || command === "recepsionist") {
    return sendPayload(message, commandData.buildCityHallPayload(session, prefix));
  }
  if (command === "guild" || command === "adventurerguild") {
    const result = commandData.buildGuildPayload(session, worldState, prefix);
    if (session.created) {
      session.quest_offers = result.offers;
      if (!core.guildRegistered(session)) {
        session.registered_at_guild = true;
        session.registered_at_receptionist = true;
      }
      await db.saveSessionAsync(message.author.id, session);
      await db.saveWorldStateAsync(worldState);
    }
    return sendPayload(message, result.embed);
  }
  if (command === "blacksmith" || command === "smith") {
    return sendPayload(message, commandData.buildServiceLocationPayload("BlackSmith", prefix));
  }
  if (command === "alchemist") {
    return sendPayload(message, commandData.buildServiceLocationPayload("Alchemist", prefix));
  }
  if (command === "tavern" || command === "kedai_petualang") {
    return sendPayload(message, commandData.buildServiceLocationPayload("Kedai Petualang", prefix));
  }
  if (command === "frontier" || command === "kedai_perbatasan") {
    return sendPayload(message, commandData.buildServiceLocationPayload("Kedai Perbatasan", prefix));
  }
  if (command === "questboard" || command === "quests" || command === "questlist") {
    if (!core.guildRegistered(session)) {
      return sendPayload(message, commandData.buildGuildPayload(session, worldState, prefix).embed);
    }
    return sendPayload(message, commandData.buildQuestBoardPayload(session, worldState));
  }
  if (command === "inventory" || command === "inv" || command === "bag") {
    return sendPayload(message, commandData.buildInventoryPayload(session));
  }
  if (command === "shop" || command === "store" || command === "toko") {
    const location = session.location || "Kedai Petualang";
    return sendPayload(message, commandData.buildShopPayload(location));
  }
  if (command === "recipes" || command === "recipe" || command === "resep") {
    return sendPayload(message, commandData.buildRecipesPayload(session));
  }
  if (command === "battle" || command === "battlelvl" || command === "battlestatus") {
    return sendPayload(message, commandData.buildBattleStatusPayload(session));
  }
  if (command === "bestiary" || command === "monsters") {
    const location = args.join(" ").trim() || session.location || "Hutan Berbisik";
    return sendPayload(message, commandData.buildBestiaryPayload(location));
  }
  if (command === "party" || command === "grup" || command === "team") {
    const action = args[0]?.toLowerCase() || "info";
    if (action === "create" || action === "buat") {
      const partyName = args.slice(1).join(" ") || `${message.author.username}'s Party`;
      if (session.created) {
        session.party = { name: partyName, leader: message.author.id, members: [message.author.username] };
        await db.saveSessionAsync(message.author.id, session);
      }
    }
    return sendPayload(message, commandData.buildPartyInfoPayload(session));
  }
  if (command === "companions" || command === "companion" || command === "pendamping") {
    return sendPayload(message, commandData.buildCompanionsPayload(session));
  }
  if (command === "achievements" || command === "achievement" || command === "pencapaian") {
    return sendPayload(message, commandData.buildAchievementsPayload(session));
  }
  if (command === "reputation" || command === "reputasi" || command === "faction") {
    return sendPayload(message, commandData.buildReputationPayload(session));
  }
  if (command === "createchar" || command === "createcharacter" || command === "buatkarakter") {
    const [raceArg, ...nameArgs] = args;
    const charName = nameArgs.join(" ").trim();
    if (!raceArg || !charName) {
      const embed = {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}createchar <race> <name>\`\nExample: \`${prefix}createchar Elf Aisha\``,
        color: 0xE74C3C,
      };
      return sendPayload(message, embed);
    }

    const raceResult = core.findRace(raceArg);
    if (!raceResult) {
      const embed = {
        title: "❌ Race Not Found",
        description: `Available races: ${Object.keys(core.raceCatalog()).join(", ")}`,
        color: 0xE74C3C,
      };
      return sendPayload(message, embed);
    }

    const baseStats = stats.loadRaceStats(core.RACES, raceResult.key);
    const jobStats = stats.loadJobStats(core.JOBS, "Novice");
    const combined = stats.combineBaseStats(baseStats, jobStats);
    const derived = stats.calculateDerivedStats(combined, 1, {});

    const newSession = {
      ...core.DEFAULT_SESSION,
      created: true,
      title: charName,
      race: raceResult.key,
      job: "Novice",
      base_stats: baseStats,
      derived_stats: derived,
      max_hp: derived.max_hp,
      max_sp: derived.max_sp,
      hp: derived.max_hp,
      sp: derived.max_sp,
      location: "Kota Utama",
      level: 1,
      exp: 0,
      gold: 100,
      stat_points: 5,
      inventory: [],
      active_quests: [],
      achievements: [],
      reputation: {},
      companions: [],
      skills: [],
    };

    await db.saveSessionAsync(message.author.id, newSession);
    const embed = {
      title: "✅ Character Created!",
      description: `Welcome, **${charName}** the **${raceResult.key}**!`,
      color: 0x2ECC71,
      fields: [
        { name: "Race", value: raceResult.key, inline: true },
        { name: "Job", value: "Novice", inline: true },
        { name: "Level", value: "1", inline: true },
        { name: "HP", value: `${derived.max_hp}`, inline: true },
        { name: "SP", value: `${derived.max_sp}`, inline: true },
        { name: "Gold", value: "100", inline: true },
      ],
    };
    return sendPayload(message, embed);
  }
  if (command === "equip" || command === "pasang") {
    const itemName = args.join(" ").trim();
    if (!itemName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}equip <item>\``,
        color: 0xE74C3C,
      });
    }
    if (session.created) {
      session.equipped = session.equipped || {};
      session.equipped.weapon = itemName;
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Equipment Updated",
      description: `You equipped **${itemName}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "unequip" || command === "lepas") {
    const slot = args[0]?.toLowerCase() || "weapon";
    if (session.created) {
      session.equipped = session.equipped || {};
      session.equipped[slot] = null;
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Equipment Removed",
      description: `You unequipped **${slot}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "equipped" || command === "gear") {
    const equipped = session.equipped || {};
    let gearsText = "";
    for (const [slot, item] of Object.entries(equipped)) {
      gearsText += `• **${slot}**: ${item || "—"}\n`;
    }
    return sendPayload(message, {
      title: "⚙️ Equipped Items",
      description: gearsText || "No items equipped",
      color: 0x3498DB,
    });
  }
  if (command === "use" || command === "pakai") {
    const itemName = args.join(" ").trim();
    if (!itemName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}use <item>\``,
        color: 0xE74C3C,
      });
    }
    return sendPayload(message, {
      title: "✅ Used Item",
      description: `You used **${itemName}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "buy" || command === "beli") {
    const [itemName, qtyRaw] = args;
    const qty = Number.parseInt(qtyRaw || "1", 10) || 1;
    if (!itemName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}buy <item> [qty]\``,
        color: 0xE74C3C,
      });
    }
    return sendPayload(message, {
      title: "✅ Purchase Successful",
      description: `You bought **${qty}x ${itemName}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "craft" || command === "buat") {
    const [itemName, qtyRaw] = args;
    const qty = Number.parseInt(qtyRaw || "1", 10) || 1;
    if (!itemName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}craft <item> [qty]\``,
        color: 0xE74C3C,
      });
    }
    return sendPayload(message, {
      title: "✅ Crafted Item",
      description: `You crafted **${qty}x ${itemName}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "upgrade" || command === "tingkat") {
    const itemName = args.join(" ").trim();
    if (!itemName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}upgrade <item>\``,
        color: 0xE74C3C,
      });
    }
    return sendPayload(message, {
      title: "✅ Item Upgraded",
      description: `You upgraded **${itemName}**`,
      color: 0x2ECC71,
    });
  }
  if (command === "startbattle" || command === "battle" || command === "fight") {
    if (session.created) {
      const monster = core.randomMonsterForLocation(session.location || "Hutan Berbisik");
      if (monster) {
        session.in_battle = true;
        session.battle_state = {
          enemy_name: monster.name,
          enemy_hp: monster.hp,
          enemy_max_hp: monster.hp,
          player_hp: session.hp,
          turn: 1,
          round: 1,
        };
        await db.saveSessionAsync(message.author.id, session);
        return sendPayload(message, {
          title: "⚔️ Battle Started!",
          description: `You encountered a **${monster.name}** (HP: ${monster.hp})!`,
          color: 0xC0392B,
        });
      }
    }
    return sendPayload(message, {
      title: "❌ Battle Failed",
      description: "No monster found in this location.",
      color: 0xE74C3C,
    });
  }
  if (command === "attack" || command === "serang") {
    if (session.in_battle) {
      const battleState = session.battle_state || {};
      battleState.enemy_hp = Math.max(0, (battleState.enemy_hp || 100) - 10);
      if (battleState.enemy_hp <= 0) {
        session.in_battle = false;
        session.battle_state = null;
        session.gold = (session.gold || 0) + 50;
        await db.saveSessionAsync(message.author.id, session);
        return sendPayload(message, {
          title: "✅ Victory!",
          description: `You defeated the enemy and gained 50 gold!`,
          color: 0x2ECC71,
        });
      }
      await db.saveSessionAsync(message.author.id, session);
      return sendPayload(message, {
        title: "⚔️ Attack!",
        description: `You attacked! Enemy HP: ${battleState.enemy_hp}`,
        color: 0x3498DB,
      });
    }
    return sendPayload(message, {
      title: "❌ Not in Battle",
      description: "Use `!startbattle` to begin a battle.",
      color: 0xE74C3C,
    });
  }
  if (command === "flee" || command === "kabur") {
    if (session.in_battle) {
      session.in_battle = false;
      session.battle_state = null;
      await db.saveSessionAsync(message.author.id, session);
      return sendPayload(message, {
        title: "🏃 Fled!",
        description: "You successfully fled from battle!",
        color: 0x95A5A6,
      });
    }
    return sendPayload(message, {
      title: "❌ Not in Battle",
      description: "Use `!startbattle` to begin a battle.",
      color: 0xE74C3C,
    });
  }
  if (command === "loot" || command === "ambil") {
    const monsterName = args.join(" ").trim();
    return sendPayload(message, {
      title: "🎁 Loot",
      description: `Loot table for **${monsterName}**:\n• Rare Item\n• Common Drop`,
      color: 0x27AE60,
    });
  }
  if (command === "acceptquest" || command === "ambilquest") {
    const questId = args[0] || "1";
    if (session.created) {
      session.active_quests = session.active_quests || [];
      session.active_quests.push({ id: questId, name: `Quest ${questId}`, progress: { current: 0, total: 10 } });
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Quest Accepted",
      description: `You accepted **Quest ${questId}**!`,
      color: 0x2ECC71,
    });
  }
  if (command === "completequest" || command === "selesaiquests") {
    const questId = args[0] || "1";
    if (session.created) {
      session.active_quests = (session.active_quests || []).filter((q) => q.id !== questId);
      session.gold = (session.gold || 0) + 100;
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Quest Complete",
      description: `You completed **Quest ${questId}**! Gained 100 gold!`,
      color: 0x2ECC71,
    });
  }
  if (command === "recruit" || command === "rekrut") {
    const companionName = args.join(" ").trim();
    if (!companionName) {
      return sendPayload(message, {
        title: "❌ Usage Error",
        description: `Usage: \`${prefix}recruit <name>\``,
        color: 0xE74C3C,
      });
    }
    if (session.created) {
      session.companions = session.companions || [];
      session.companions.push({ name: companionName, level: 1 });
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Companion Recruited",
      description: `You recruited **${companionName}**!`,
      color: 0x2ECC71,
    });
  }
  if (command === "dismiss" || command === "lepas_companion") {
    const companionName = args.join(" ").trim();
    if (session.created) {
      session.companions = (session.companions || []).filter((c) => c.name !== companionName);
      await db.saveSessionAsync(message.author.id, session);
    }
    return sendPayload(message, {
      title: "✅ Dismissed",
      description: `You dismissed **${companionName}**!`,
      color: 0x2ECC71,
    });
  }
  if (command === "scene" || command === "adegan" || command === "roleplay") {
    const action = args.join(" ").trim();
    return sendPayload(message, {
      title: "🎭 Scene",
      description: `**${session.title}** ${action || "poses dramatically..."}`,
      color: 0x9B59B6,
    });
  }
  if (command === "status") {
    const embed = {
      title: "📊 Status",
      description: `**${session.title}** the **${session.race}** **${session.job}**`,
      color: 0x3498DB,
      fields: [
        { name: "Level", value: session.level || 1, inline: true },
        { name: "HP", value: `${session.hp || 0}/${session.max_hp || 100}`, inline: true },
        { name: "Gold", value: session.gold || 0, inline: true },
      ],
    };
    return sendPayload(message, embed);
  }
  if (command === "dbstatus") {
    const fsStatus = db.getFirestoreStatus();
    const statusText = fsStatus.enabled ? "✅ **Firestore Connected**" : "❌ **Firestore Disabled** (using in-memory storage)";
    const details = [
      `• Firestore Enabled: ${fsStatus.enabled}`,
      `• Sessions Collection: ${fsStatus.sessions_collection}`,
      `• World State Doc: ${fsStatus.world_doc}`,
      `• App Initialized: ${fsStatus.app_initialized}`,
      "",
      "**Fallback Storage:**",
      `• Sessions in memory: ${fsStatus.fallback_sessions_count}`,
      `• World state cached: ${fsStatus.fallback_world_state}`,
    ].join("\n");
    const embed = {
      title: "💾 Database Status",
      description: statusText,
      color: fsStatus.enabled ? 0x2ECC71 : 0xF1C40F,
      fields: [{ name: "Details", value: details, inline: false }],
    };
    return sendPayload(message, embed);
  }

  return null;
}

async function main() {
  const config = readConfig();
  db.init(CONFIG_PATH);

  if (!config.token) {
    console.log("Tidak ada token di config.json — buat file dari config.example.json dan isi tokenmu.");
    return;
  }

  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.GuildMessageReactions,
    ],
    partials: [Partials.Message, Partials.Channel, Partials.Reaction],
  });

  client.once("ready", () => {
    const fsStatus = db.getFirestoreStatus();
    const firestoreMsg = fsStatus.enabled ? "✅ Firestore connected" : "⚠️ Using in-memory storage";
    console.log(`Bot ready as ${client.user.tag} — prefix=${config.prefix || "!"}`);
    console.log(`Database: ${firestoreMsg}`);
    console.log(`Loaded locations: ${core.allLocations().length}`);
  });

  client.on("messageCreate", async (message) => {
    if (!message.content || message.author.bot) {
      return;
    }
    const prefix = config.prefix || "!";
    if (!message.content.startsWith(prefix)) {
      return;
    }

    const raw = message.content.slice(prefix.length).trim();
    if (!raw) {
      return;
    }
    const [command, ...args] = raw.split(/\s+/);
    try {
      await handleCommand(message, command.toLowerCase(), args, config);
    } catch (error) {
      console.error(error);
    }
  });

  await client.login(config.token);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});