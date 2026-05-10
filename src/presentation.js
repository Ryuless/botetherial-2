"use strict";

const COLOR_PRIMARY = 0xFF6B00;
const COLOR_SECONDARY = 0xFF1493;
const COLOR_RACE = 0x8A2BE2;
const COLOR_JOB = 0xE91E63;
const COLOR_SKILL = 0x9C27B0;
const COLOR_COMPANION = 0xFF1493;
const COLOR_QUEST = 0x8B0000;
const COLOR_WORLD = 0x00CED1;
const COLOR_ITEM = 0xFFD700;
const COLOR_STAT = 0x3498DB;

function createEmbed(title = "", description = "", color = COLOR_PRIMARY, authorName = null, authorIcon = null) {
  const embed = { title, description, color, fields: [] };
  if (authorName) {
    embed.author = { name: authorName, icon_url: authorIcon || null };
  }
  return embed;
}

function addField(embed, name, value, inline = false) {
  embed.fields = embed.fields || [];
  embed.fields.push({ name, value, inline });
  return embed;
}

function setFooter(embed, text, iconUrl = null) {
  embed.footer = { text, icon_url: iconUrl };
  return embed;
}

function createMenuEmbed(title, description = "", color = COLOR_PRIMARY, icon = "") {
  const fullTitle = icon ? `${icon} ${title}` : title;
  return createEmbed(fullTitle, description, color);
}

function addMenuItem(embed, name, value, emoji = "", inline = false) {
  const displayName = emoji ? `${emoji} ${name}` : name;
  return addField(embed, displayName, value, inline);
}

function formatMenuFooter(current = null, total = null, extra = "") {
  const parts = [];
  if (current !== null && total !== null) {
    parts.push(`Page ${current}/${total}`);
  }
  if (extra) {
    parts.push(extra);
  }
  return parts.length ? parts.join(" • ") : "─────────────────────";
}

module.exports = {
  COLOR_PRIMARY,
  COLOR_SECONDARY,
  COLOR_RACE,
  COLOR_JOB,
  COLOR_SKILL,
  COLOR_COMPANION,
  COLOR_QUEST,
  COLOR_WORLD,
  COLOR_ITEM,
  COLOR_STAT,
  createEmbed,
  addField,
  setFooter,
  createMenuEmbed,
  addMenuItem,
  formatMenuFooter,
};