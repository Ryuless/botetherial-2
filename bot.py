import asyncio
import copy
import json
import os
import random
import time
import logging
from collections import Counter

import discord
from discord.ext import commands
import functools

import db
import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(ROOT, "config.json")
DATA_DIR = os.path.join(ROOT, "data")

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
else:
    cfg = {"token": None, "prefix": "!"}

TOKEN = cfg.get("token")
PREFIX = cfg.get("prefix", "!")

db.init(CONFIG_PATH)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


def load_json(name, use_root=False):
    if use_root:
        path = os.path.join(ROOT, name)
    else:
        path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


MAP = load_json("map.json")
MONSTERS = load_json("monsters.json")
ITEMS = load_json("items.json")
CHARACTER_OPTIONS = load_json("character_options.json")
RECIPES = load_json("recipes.json")
WORLD_EVENTS = load_json("world_events.json")
RACES = load_json("races.json", use_root=True)
JOBS = load_json("jobs.json", use_root=True)

FACTION_NAMES = [
    "Adventurer Guild",
    "BlackSmith",
    "Alchemist",
    "Tavern Circle",
    "Wilds",
    "Shadow Court",
    "Sky Choir",
    "Sea Court",
]

COMPANION_CATALOG = {
    "Mira the Lanternkeeper": {
        "role": "Guide",
        "locations": ["Kedai Petualang", "Kota Utama", "Adventurer Guild"],
        "bonuses": {"luck": 1, "exp": 4},
        "flavor": "Mira selalu membawa lentera kecil yang seolah tahu jalan paling aman di malam yang panjang.",
    },
    "Bram Ironwake": {
        "role": "Shieldbearer",
        "locations": ["BlackSmith", "Dataran Keras", "Kedai Perbatasan"],
        "bonuses": {"defense": 2, "hp": 8},
        "flavor": "Bram berdiri tegak seperti pilar besi tua yang tak mau runtuh meski dunia berguncang.",
    },
    "Selene Quietwind": {
        "role": "Scout",
        "locations": ["Alam Mistis", "Hutan Berbisik", "Puncak Langit"],
        "bonuses": {"travel": 2, "luck": 1},
        "flavor": "Selene nyaris tak bersuara, tetapi setiap langkahnya selalu membawa kabar kecil dari kejauhan.",
    },
    "Kora Ashwhisper": {
        "role": "Hunter",
        "locations": ["Kawasan Bayangan", "Dataran Keras", "Hutan Gelap"],
        "bonuses": {"attack": 1, "luck": 1},
        "flavor": "Kora membaca napas makhluk liar seperti pemburu membaca jejak api di abu.",
    },
    "Tama Riverchant": {
        "role": "Sage",
        "locations": ["Samudra", "Pesisir Berbisik", "Sungai Sihir"],
        "bonuses": {"mana": 8, "exp": 3},
        "flavor": "Tama menyanyikan ombak seolah air selalu menyimpan nama-nama lama di dalamnya.",
    },
    "Arielle Dawnfeather": {
        "role": "Chronicler",
        "locations": ["Puncak Langit", "Kota Atas Langit", "Istana Langit"],
        "bonuses": {"exp": 6, "luck": 1},
        "flavor": "Arielle mencatat dunia dengan bulu pena yang berkilau seperti fajar baru.",
    },
}

ACHIEVEMENT_CATALOG = {
    "awakened": {
        "title": "Awakened",
        "description": "Membuat karakter pertamamu.",
        "reward": {"exp": 10, "gold": 10},
    },
    "first_blood": {
        "title": "First Blood",
        "description": "Menang battle pertamamu.",
        "reward": {"exp": 18, "gold": 12},
    },
    "first_quest": {
        "title": "Quest Starter",
        "description": "Menyelesaikan quest pertamamu.",
        "reward": {"exp": 20, "gold": 15},
    },
    "first_party": {
        "title": "Party Maker",
        "description": "Membuat party channel pertamamu.",
        "reward": {"exp": 12, "gold": 12},
    },
    "first_companion": {
        "title": "Bond Keeper",
        "description": "Merekrut companion pertamamu.",
        "reward": {"exp": 16, "gold": 10},
    },
    "first_story": {
        "title": "Legend Walker",
        "description": "Menyelesaikan story event pertamamu.",
        "reward": {"exp": 22, "gold": 14},
    },
}

STORY_EVENT_POOL = [
    {
        "id": "guild_oath",
        "title": "Guild Oath",
        "race": ["Human", "Dwarf", "Orc", "Bunny"],
        "job": ["Warrior", "Hunter", "Archer", "Jobless"],
        "regions": ["Kota Utama", "Dataran Keras"],
        "narrative": "Kau mengucap sumpah kecil di antara suara guild dan janji jalan yang panjang.",
        "reward": {"exp": 18, "gold": 12, "reputation": {"Adventurer Guild": 4}},
    },
    {
        "id": "forest_hearing",
        "title": "Forest Hearing",
        "race": ["Elf", "Fairy", "Nymph", "Sylvan"],
        "job": ["Oracle", "Poet", "Witch", "Alchemist"],
        "regions": ["Alam Mistis"],
        "narrative": "Bisikan daun, air, dan akar membentuk sidang sunyi yang hanya bisa dipahami oleh mereka yang peka.",
        "reward": {"exp": 20, "gold": 8, "reputation": {"Wilds": 3}},
    },
    {
        "id": "shadow_bargain",
        "title": "Shadow Bargain",
        "race": ["Vampire", "Demon", "Abyssborn", "Werewolf"],
        "job": ["Rogue", "Oracle", "Witch", "Poet"],
        "regions": ["Kawasan Bayangan"],
        "narrative": "Kau menawar rahasia di bawah cahaya yang tak pernah benar-benar terang.",
        "reward": {"exp": 22, "gold": 16, "reputation": {"Shadow Court": 4}},
    },
    {
        "id": "sky_choir",
        "title": "Sky Choir",
        "race": ["Angel", "Pegasus", "Griffin", "Fairy"],
        "job": ["Poet", "Oracle", "Hunter", "Archer"],
        "regions": ["Puncak Langit"],
        "narrative": "Nada-nada langit memantul pada awan, dan dunia terasa lebih luas dari biasanya.",
        "reward": {"exp": 20, "gold": 10, "reputation": {"Sky Choir": 4}},
    },
    {
        "id": "sea_memory",
        "title": "Sea Memory",
        "race": ["Mermaid", "Human", "Demon", "Bunny"],
        "job": ["Oracle", "Poet", "Alchemist"],
        "regions": ["Samudra"],
        "narrative": "Laut seolah menyimpan kisahmu di dalam gelombang dan mengembalikannya sebagai tanda.",
        "reward": {"exp": 18, "gold": 14, "reputation": {"Sea Court": 3}},
    },
    {
        "id": "forge_echo",
        "title": "Forge Echo",
        "race": ["Dwarf", "Orc", "Human", "Dragontamer"],
        "job": ["Blacksmith", "Warrior", "Alchemist", "Runesmith"],
        "regions": ["Dataran Keras", "Kota Utama"],
        "narrative": "Dentang palu dan bara membuat udara seperti punya denyut jantung sendiri.",
        "reward": {"exp": 19, "gold": 15, "reputation": {"BlackSmith": 4}},
    },
]

DEFAULT_SESSION = {
    "location": "Kota Utama",
    "race": "Human",
    "job": "Jobless",
    "title": "Wanderer",
    "level": 1,
    "stat_points": 0,
    "created": False,
    "hp": 100,
    "max_hp": 100,
    "sp": 50,
    "max_sp": 50,
    "gold": 40,
    "exp": 0,
    "inventory": [],
    "equipped": {"weapon": None, "armor": None, "trinket": None, "backpack": None},
    "base_stats": {
        "str": 10,
        "agi": 10,
        "vit": 10,
        "int": 10,
        "dex": 10,
        "luk": 10,
        "tec": 10,
        "men": 10,
        "crt": 10,
    },
    "derived_stats": {},
    "battle": None,
    "quests": [],
    "quest_offers": [],
    "last_encounter": None,
    "last_loot": [],
    "gear_upgrades": {},
    "skill_cooldowns": {},
    "race_power_cooldowns": {},
    "companions": [],
    "reputation": {},
    "achievements": [],
    "party_role": "member",
    "party_tag": None,
    "battle_context": {},
    "registered_at_guild": False,
    "registered_at_receptionist": False,
    "tier0_race_skills": {},
    "tier0_job_skills_by_job": {},
}

DEFAULT_WORLD_STATE = {
    "event": None,
    "turns_left": 0,
    "turn_counter": 0,
    "history": [],
    "parties": {},
    "chronicle": [],
}

MAIN_SERVICE_LOCATIONS = {
    "Kedai Petualang": "Tavern Keeper",
    "Adventurer Guild": "Guild Clerk",
    "Kedai Perbatasan": "Frontier Clerk",
    "Kota Utama": "City Clerk",
    "BlackSmith": "Blacksmith",
    "Alchemist": "Alchemist",
}

SERVICE_ACTIONS_BY_LOCATION = {
    "Kota Utama": [
        ("cityhall", "City Hall", "Info kota, help, world state"),
        ("travel", "Travel", "Pindah ke lokasi lain"),
        ("rest", "Rest", "Istirahat di area aman"),
    ],
    "Adventurer Guild": [
        ("guild", "Guild Desk", "Registrasi petualang dan quest"),
        ("questboard", "Quest Board", "Lihat quest yang tersedia"),
        ("changejob", "Job Office", "Ubah job di guild"),
    ],
    "BlackSmith": [
        ("blacksmith", "Forge Desk", "Lihat pandai besi dan upgrade gear"),
        ("upgrade", "Upgrade", "Tingkatkan weapon atau armor"),
        ("shop", "Shop", "Beli equipment"),
    ],
    "Alchemist": [
        ("alchemist", "Alchemy Desk", "Lihat alchemist dan upgrade trinket"),
        ("upgrade", "Upgrade", "Tingkatkan trinket"),
        ("shop", "Shop", "Beli item dan potion"),
    ],
    "Kedai Petualang": [
        ("tavern", "Tavern Counter", "Rest, companion, dan supply"),
        ("rest", "Rest", "Pulihkan HP di penginapan"),
        ("companions", "Companions", "Lihat companion yang dimiliki"),
        ("recruit", "Recruit", "Rekrut companion baru"),
        ("shop", "Shop", "Beli item"),
    ],
    "Kedai Perbatasan": [
        ("frontier", "Frontier Post", "Travel, explore, dan supply"),
        ("travel", "Travel", "Pindah lokasi"),
        ("explore", "Explore", "Jelajah area sekitar"),
        ("shop", "Shop", "Beli item perjalanan"),
    ],
}

SHOP_STOCKS = {
    "Kedai Petualang": ["Health Potion", "Ration Pack", "Torch", "Rope", "Traveler Pack"],
    "Adventurer Guild": ["Health Potion", "Stamina Tonic", "Guild Sigil"],
    "BlackSmith": ["Rusty Sword", "Leather Armor", "Iron Dagger", "Shield Buckler", "Ranger Framepack", "Aegis Expedition Pack"],
    "Alchemist": ["Antidote", "Mana Tonic", "Health Potion", "Spirit Herb"],
    "Kedai Perbatasan": ["Torch", "Rope", "Ration Pack", "Health Potion", "Traveler Pack"],
}

QUEST_REWARD_POOL = {
    "hunt": [(35, ["Health Potion"]), (50, ["Ration Pack"]), (75, ["Iron Dagger"])],
    "collect": [(25, ["Health Potion"]), (40, ["Antidote"]), (60, ["Leather Armor"])],
    "visit": [(20, ["Torch"]), (35, ["Rope"]), (55, ["Guild Sigil"])],
}

# Embed styling helper functions
COLOR_PRIMARY = 0x9B59B6  # Purple
COLOR_SUCCESS = 0x2ECC71  # Green
COLOR_INFO = 0x3498DB    # Blue
COLOR_WARNING = 0xF39C12  # Orange
COLOR_ERROR = 0xE74C3C   # Red
COLOR_NEUTRAL = 0x95A5A6  # Gray

# Menu Category Colors
COLOR_RACE = 0xFF6B00    # Orange
COLOR_JOB = 0xE91E63     # Pink
COLOR_SKILL = 0x9C27B0   # Purple
COLOR_COMPANION = 0xFF1493 # Deep Pink
COLOR_QUEST = 0x8B0000   # Dark Red
COLOR_WORLD = 0x00CED1   # Dark Turquoise
COLOR_ITEM = 0xFFD700    # Gold
COLOR_STAT = 0x3498DB    # Blue

def create_embed(title="", description="", color=COLOR_PRIMARY, author_name=None, author_icon=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon)
    return embed

def add_field(embed, name, value, inline=False):
    embed.add_field(name=name, value=value, inline=inline)
    return embed

def set_footer(embed, text, icon_url=None):
    embed.set_footer(text=text, icon_url=icon_url)
    return embed

# Modern Menu Styling Helper Functions
def create_menu_embed(title, description="", color=COLOR_PRIMARY, icon=""):
    """Create a modern menu embed with consistent styling."""
    full_title = f"{icon} {title}" if icon else title
    return create_embed(title=full_title, description=description, color=color)

def add_menu_item(embed, name, value, emoji="", inline=False):
    """Add an item to menu with emoji prefix."""
    display_name = f"{emoji} {name}" if emoji else name
    embed.add_field(name=display_name, value=value, inline=inline)
    return embed

def format_menu_footer(current=None, total=None, extra=""):
    """Format footer for menu navigation."""
    parts = []
    if current is not None and total is not None:
        parts.append(f"Page {current}/{total}")
    if extra:
        parts.append(extra)
    footer_text = " • ".join(parts) if parts else "─────────────────────"
    return footer_text


def all_locations():
    return [location for group in MAP.get("Etherial", {}).values() for location in group]


LOCATION_TO_REGION = {
    location: region
    for region, locations in MAP.get("Etherial", {}).items()
    for location in locations
}


def normalize_name(value):
    return " ".join(str(value).strip().split())


# Command-channel mapping persistence (in `config.json` under key `command_channels`)
def load_command_channels():
    try:
        return cfg.get("command_channels", {}) if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def save_command_channels(mapping: dict):
    try:
        cfg["command_channels"] = mapping
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def resolve_allowed_entries(entries):
    """Normalize entries to list of strings/ids."""
    if not entries:
        return []
    if isinstance(entries, str):
        return [entries]
    if isinstance(entries, (list, tuple)):
        return list(entries)
    return []


def find_channel_by_name_or_id(ctx, name_or_id):
    if not ctx.guild:
        return None
    s = str(name_or_id).strip()
    # try id
    if s.isdigit():
        cid = int(s)
        ch = ctx.guild.get_channel(cid)
        if ch:
            return ch
    # try mention format <#id>
    if s.startswith("<#") and s.endswith(">"):
        inner = s[2:-1]
        if inner.isdigit():
            ch = ctx.guild.get_channel(int(inner))
            if ch:
                return ch
    # fallback: find by name
    lookup = s.lower().lstrip("#")
    for ch in ctx.guild.channels:
        if getattr(ch, "name", "").lower() == lookup:
            return ch
    return None


def require_channel_config(command_key):
    """Decorator that enforces allowed channels from `command_channels` config.

    Allowed entries can be channel names or channel IDs (as strings or ints).
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            try:
                mapping = load_command_channels() or {}
                allowed = resolve_allowed_entries(mapping.get(command_key))
                if not allowed:
                    # no restriction configured, allow
                    return await func(ctx, *args, **kwargs)

                # check channel id or name
                current_id = getattr(ctx.channel, "id", None)
                current_name = getattr(ctx.channel, "name", "").lower()

                allowed_ok = False
                mentions = []
                for entry in allowed:
                    entry_s = str(entry).strip()
                    # try id match
                    if entry_s.isdigit() and current_id == int(entry_s):
                        allowed_ok = True
                    else:
                        # try name or mention
                        ch = find_channel_by_name_or_id(ctx, entry_s)
                        if ch and ch.id == current_id:
                            allowed_ok = True
                        mentions.append(ch.mention if ch else (f"#{entry_s}"))

                if not allowed_ok:
                    mention_text = ", ".join(mentions) if mentions else ", ".join([f"#{e}" for e in allowed])
                    embed = create_menu_embed(
                        "⚠️ Salah Channel",
                        f"Perintah ini hanya dapat digunakan di channel: {mention_text}",
                        color=COLOR_WARNING,
                        icon="⚠️"
                    )
                    embed.add_field(name="Arahkan ke:", value=f"Silakan gunakan perintah di {mention_text}", inline=False)
                    await ctx.send(embed=embed)
                    return
            except Exception:
                # On error, allow command to run (fail-open)
                return await func(ctx, *args, **kwargs)
            return await func(ctx, *args, **kwargs)

        return wrapper
    return decorator


def find_location(query):
    query = normalize_name(query).lower()
    for location in all_locations():
        if location.lower() == query:
            return location
    for location in all_locations():
        if query in location.lower():
            return location
    return None


def item_catalog():
    return ITEMS if isinstance(ITEMS, dict) else {}
    
def item_weight_text(item_name):
    item = item_catalog().get(item_name, {})
    if not isinstance(item, dict):
        return None
    weight = item.get("weight")
    if weight is None:
        return None
    unit = item.get("weight_unit", "kg")
    return f"{weight} {unit}"


def item_weight_value(item_name):
    item = item_catalog().get(item_name, {})
    if not isinstance(item, dict):
        return 0.0
    try:
        return max(0.0, float(item.get("weight", 0) or 0))
    except Exception:
        return 0.0


def current_inventory_weight(session):
    counts = inventory_counts(session)
    total = 0.0
    for item_name, qty in counts.items():
        total += item_weight_value(item_name) * int(qty)
    return round(total, 2)


def current_weight_limit(session):
    derived = session.get("derived_stats", {}) if isinstance(session.get("derived_stats", {}), dict) else {}
    try:
        return float(derived.get("weight_limit", 500))
    except Exception:
        return 500.0


def can_add_item_by_weight(session, item_name, qty=1):
    per_item = item_weight_value(item_name)
    if per_item <= 0:
        return True
    current = current_inventory_weight(session)
    limit = current_weight_limit(session)
    required = per_item * max(0, int(qty))
    return (current + required) <= limit + 1e-9


def max_addable_quantity(session, item_name):
    per_item = item_weight_value(item_name)
    if per_item <= 0:
        return 999999
    current = current_inventory_weight(session)
    limit = current_weight_limit(session)
    free = max(0.0, limit - current)
    return int(free // per_item)

def item_detail_lines(item_name):
    item = item_catalog().get(item_name, {})
    lines = []
    if isinstance(item, dict):
        description = item.get("description")
        if description:
            lines.append(description)
        weight_text = item_weight_text(item_name)
        if weight_text:
            lines.append(f"Berat: {weight_text}")
    return lines


def race_catalog():
    # Prefer the new RACES file; fall back to CHARACTER_OPTIONS for compatibility
    if isinstance(RACES, dict) and RACES:
        return RACES
    races = CHARACTER_OPTIONS.get("races", {}) if isinstance(CHARACTER_OPTIONS, dict) else {}
    return races if isinstance(races, dict) else {}


def job_catalog():
    # Prefer the new JOBS file; fall back to CHARACTER_OPTIONS for compatibility
    if isinstance(JOBS, dict) and JOBS:
        return JOBS
    jobs = CHARACTER_OPTIONS.get("jobs", {}) if isinstance(CHARACTER_OPTIONS, dict) else {}
    return jobs if isinstance(jobs, dict) else {}


def all_races():
    return list(race_catalog().keys())


def all_jobs():
    return list(job_catalog().keys())


def find_race(name):
    lookup = normalize_name(name).lower()
    for race_name, data in race_catalog().items():
        if race_name.lower() == lookup or lookup in race_name.lower():
            return race_name, data
    return None, None


def find_job(name):
    lookup = normalize_name(name).lower()
    for job_name, data in job_catalog().items():
        if job_name.lower() == lookup or lookup in job_name.lower():
            return job_name, data
    return None, None


def find_item(name):
    lookup = normalize_name(name).lower()
    for item_name, data in item_catalog().items():
        if item_name.lower() == lookup:
            return item_name, data
    for item_name, data in item_catalog().items():
        if lookup in item_name.lower():
            return item_name, data
    return None, None


def item_price(item_name):
    _, data = find_item(item_name)
    if not data:
        return None
    return int(data.get("price", 0))


def recipe_catalog():
    return RECIPES if isinstance(RECIPES, dict) else {}


def world_event_catalog():
    if isinstance(WORLD_EVENTS, dict):
        events = WORLD_EVENTS.get("events", [])
        return events if isinstance(events, list) else []
    return []


def find_recipe(name):
    lookup = normalize_name(name).lower()
    for recipe_name, data in recipe_catalog().items():
        if recipe_name.lower() == lookup or lookup in recipe_name.lower():
            return recipe_name, data
    return None, None


def inventory_material_counts(session):
    return Counter(session.get("inventory", []))


def station_for_location(location):
    if location in {"Alchemist", "Adventurer Guild", "Kedai Petualang", "BlackSmith", "Kedai Perbatasan"}:
        return location
    return MAIN_SERVICE_LOCATIONS.get(location)


def require_location_config(command_key, allowed_locations, location_label="lokasi ini"):
    """Decorator that enforces allowed character locations for a command."""

    normalized_allowed = {normalize_name(location).lower() for location in allowed_locations}

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            session = await get_session_async(ctx.author.id)
            if not session.get("created", False):
                return await func(ctx, *args, **kwargs)

            current_location = normalize_name(session.get("location", DEFAULT_SESSION["location"]))
            if current_location.lower() not in normalized_allowed:
                allowed_text = ", ".join(sorted(allowed_locations))
                embed = create_menu_embed(
                    "❌ Lokasi Tidak Sesuai",
                    f"Kamu sedang berada di **{current_location}**.",
                    color=COLOR_ERROR,
                    icon="📍"
                )
                embed.add_field(
                    name="Keterangan",
                    value=f"Command ini hanya bisa digunakan di {location_label}.",
                    inline=False
                )
                embed.add_field(
                    name="Lokasi yang Diizinkan",
                    value=allowed_text,
                    inline=False
                )
                await ctx.send(embed=embed)
                return

            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def recipe_available_at_location(recipe_name, location):
    recipe = recipe_catalog().get(recipe_name)
    if not recipe:
        return False
    required_station = recipe.get("station")
    current_station = station_for_location(location)
    return required_station == current_station or required_station == location


def can_pay_requirements(session, requirements, multiplier=1):
    counts = inventory_material_counts(session)
    for item_name, amount in requirements.items():
        if counts.get(item_name, 0) < amount * multiplier:
            return False, item_name
    return True, None


def consume_requirements(session, requirements, multiplier=1):
    for item_name, amount in requirements.items():
        remove_item(session, item_name, amount * multiplier)


def add_item(session, item_name, qty=1):
    session.setdefault("inventory", [])
    added = 0
    for _ in range(max(0, int(qty))):
        if not can_add_item_by_weight(session, item_name, 1):
            break
        session["inventory"].append(item_name)
        added += 1
    return added


def remove_item(session, item_name, qty=1):
    inventory = session.setdefault("inventory", [])
    removed = 0
    for _ in range(qty):
        try:
            inventory.remove(item_name)
            removed += 1
        except ValueError:
            break
    return removed


def inventory_counts(session):
    return Counter(session.get("inventory", []))


def quest_reward_template(kind, world_state=None):
    reward_gold, reward_items = random.choice(QUEST_REWARD_POOL.get(kind, [(25, ["Health Potion"])]))
    world_bonus = max(0, event_modifier(world_state or {}, "quest_bonus", 0))
    reward_gold = int(round(reward_gold * (1 + world_bonus / 100)))
    if world_state and active_world_event(world_state):
        if random.random() < min(0.5, 0.15 + (world_bonus / 200)):
            reward_items = list(reward_items) + [random.choice(["Spirit Herb", "Moon Salt", "Iron Ore"])]
    return {"gold": reward_gold, "items": list(reward_items)}


def random_monster_for_location(location):
    if location in MONSTERS:
        return random.choice(MONSTERS[location])
    region = LOCATION_TO_REGION.get(location)
    if not region:
        return None
    possible = []
    for loc in MAP.get("Etherial", {}).get(region, []):
        possible.extend(MONSTERS.get(loc, []))
    return random.choice(possible) if possible else None


def quest_id():
    return f"Q{random.randint(1000, 9999)}"


def ensure_session(session):
    session = session or {}
    merged = copy.deepcopy(DEFAULT_SESSION)
    for key, default_value in DEFAULT_SESSION.items():
        if key not in session:
            continue
        if isinstance(default_value, dict) and isinstance(session[key], dict):
            merged[key].update(session[key])
        else:
            merged[key] = session[key]

    # Normalize container types
    if not isinstance(merged.get("inventory"), list):
        merged["inventory"] = []
    if not isinstance(merged.get("quests"), list):
        merged["quests"] = []
    if not isinstance(merged.get("quest_offers"), list):
        merged["quest_offers"] = []
    if not isinstance(merged.get("equipped"), dict):
        merged["equipped"] = copy.deepcopy(DEFAULT_SESSION["equipped"])
    for slot in ["weapon", "armor", "trinket", "backpack"]:
        merged["equipped"].setdefault(slot, None)
    if not isinstance(merged.get("gear_upgrades"), dict):
        merged["gear_upgrades"] = {}
    if not isinstance(merged.get("companions"), list):
        merged["companions"] = []
    if not isinstance(merged.get("reputation"), dict):
        merged["reputation"] = {}
    if not isinstance(merged.get("achievements"), list):
        merged["achievements"] = []
    if not merged.get("party_role"):
        merged["party_role"] = "member"
    if not merged.get("party_tag"):
        merged["party_tag"] = None
    if not isinstance(merged.get("battle_context"), dict):
        merged["battle_context"] = {}
    if not isinstance(merged.get("tier0_race_skills"), dict):
        merged["tier0_race_skills"] = {}
    if not isinstance(merged.get("tier0_job_skills_by_job"), dict):
        merged["tier0_job_skills_by_job"] = {}

    if not merged.get("race"):
        merged["race"] = DEFAULT_SESSION["race"]
    if not merged.get("job"):
        merged["job"] = DEFAULT_SESSION["job"]
    if not merged.get("registered_at_guild") and merged.get("registered_at_receptionist", False):
        merged["registered_at_guild"] = True

    merged["bonuses"] = resolve_character_bonuses(merged)
    merged["max_hp"] = max(merged.get("max_hp", 100), 100 + merged["bonuses"].get("hp", 0))
    merged["hp"] = min(merged.get("hp", merged["max_hp"]), merged["max_hp"])

    # Initialize stats block if needed
    if merged.get("level", 1) > 0 and merged.get("race"):
        race_key = merged.get("race", "Human")
        job_key = merged.get("job", "Novice")
        level = merged.get("level", 1)
        # If base_stats missing, load from definitions
        if not merged.get("base_stats"):
            if race_key.lower() in RACES:
                merged["base_stats"] = stats.load_race_stats(RACES, race_key)
            else:
                merged["base_stats"] = DEFAULT_SESSION.get("base_stats", {}).copy()
        # Apply job bonuses if available
        job_bonus = stats.load_job_stats(JOBS, job_key)
        combined = stats.combine_base_stats(merged.get("base_stats", {}), job_bonus)
        equip_bonus = resolve_equipment_bonuses(merged)
        merged["derived_stats"] = stats.calculate_derived_stats(combined, level, equipment_bonus=equip_bonus)
        merged["max_hp"] = merged["derived_stats"].get("max_hp", merged.get("max_hp", 100))
        merged["max_sp"] = merged["derived_stats"].get("max_sp", merged.get("max_sp", 50))
        merged.setdefault("hp", merged["max_hp"])
        merged.setdefault("sp", merged["max_sp"])

    return merged
    # Ensure stats are initialized if character has been created
    if merged.get("level", 1) > 0 and merged.get("race") != "Human":
        # Character has been created, ensure stats are set up
        if not merged.get("base_stats") or not merged.get("derived_stats"):
            race_key = merged.get("race", "Human")
            job_key = merged.get("job", "Novice")
            level = merged.get("level", 1)
            
            # Try to load from RACES/JOBS data
            if race_key.lower() in RACES:
                char_stats = stats.create_character_stats(RACES, race_key, job_key, JOBS, level)
                merged["base_stats"] = char_stats.get("base_stats", merged.get("base_stats", DEFAULT_SESSION["base_stats"]))
                merged["derived_stats"] = char_stats.get("derived_stats", {})
                merged["max_hp"] = char_stats.get("derived_stats", {}).get("max_hp", merged.get("max_hp", 100))
                merged["max_sp"] = char_stats.get("derived_stats", {}).get("max_sp", merged.get("max_sp", 50))
                if merged.get("hp", 0) == 0:
                    merged["hp"] = merged["max_hp"]
                if merged.get("sp", 0) == 0:
                    merged["sp"] = merged["max_sp"]
    
    return merged


def default_world_state():
    return copy.deepcopy(DEFAULT_WORLD_STATE)


def ensure_world_state(state):
    merged = default_world_state()
    state = state or {}
    for key, value in state.items():
        merged[key] = value
    if not isinstance(merged.get("history"), list):
        merged["history"] = []
    if not isinstance(merged.get("parties"), dict):
        merged["parties"] = {}
    if not isinstance(merged.get("chronicle"), list):
        merged["chronicle"] = []
    return merged


def resolve_character_bonuses(session):
    bonuses = {
        "hp": 0,
        "attack": 0,
        "defense": 0,
        "mana": 0,
        "luck": 0,
        "craft": 0,
        "travel": 0,
        "exp": 0,
        "gold": 0,
        "heal": 0,
    }

    race_name = session.get("race")
    job_name = session.get("job")
    for source_name, source_catalog in ((race_name, race_catalog()), (job_name, job_catalog())):
        if source_name and source_name in source_catalog:
            for key, value in source_catalog[source_name].get("bonuses", {}).items():
                bonuses[key] = bonuses.get(key, 0) + int(value)

    return bonuses


def resolve_equipment_bonuses(session):
    """Aggregate numeric bonuses from equipped items for derived stat calculation."""
    bonuses = {}
    for slot in (session.get("equipped") or {}):
        item_name = session.get("equipped", {}).get(slot)
        if not item_name:
            continue
        item = item_catalog().get(item_name)
        if not isinstance(item, dict):
            continue
        # First, a generic bonuses dict on the item
        for k, v in item.get("bonuses", {}).items():
            try:
                bonuses[k] = bonuses.get(k, 0) + int(v)
            except Exception:
                try:
                    bonuses[k] = bonuses.get(k, 0) + float(v)
                except Exception:
                    pass
        # Then, common flat numeric keys
        for k in ("attack", "defense", "max_hp", "max_sp", "aspd", "hit", "crit", "weight_limit", "success_rate", "vct_reduction"):
            if k in item:
                try:
                    bonuses[k] = bonuses.get(k, 0) + int(item.get(k, 0))
                except Exception:
                    try:
                        bonuses[k] = bonuses.get(k, 0) + float(item.get(k, 0))
                    except Exception:
                        pass
    return bonuses


def race_modifier_text(race_name):
    race_name, race_data = find_race(race_name)
    if not race_name:
        return "Race tidak dikenal."
    bonuses = race_data.get("bonuses", {})
    bonus_text = ", ".join(f"{key}+{value}" for key, value in bonuses.items()) or "Tidak ada bonus"
    return f"{race_name}: {race_data.get('description', '')} | Bonus: {bonus_text}"


def job_modifier_text(job_name):
    job_name, job_data = find_job(job_name)
    if not job_name:
        return "Job tidak dikenal."
    bonuses = job_data.get("bonuses", {})
    bonus_text = ", ".join(f"{key}+{value}" for key, value in bonuses.items()) or "Tidak ada bonus"
    return f"{job_name}: {job_data.get('description', '')} | Bonus: {bonus_text}"


JOB_SKILLS = {
    "Archer": {
        "snipe": {
            "name": "Snipe",
            "cooldown": 2,
            "description": "Tembakan presisi yang menembus pertahanan musuh.",
            "battle": "damage",
            "damage": (20, 32),
            "pierce": 3,
            "flavor": "Anak panahmu melesat lurus, seperti garis takdir yang tak bisa dibelokkan.",
        },
        "pin_down": {
            "name": "Pin Down",
            "cooldown": 3,
            "description": "Hujan panah yang menahan gerak lawan.",
            "battle": "debuff",
            "damage": (10, 18),
            "debuff": {"monster_atk": -3, "turns": 2},
            "flavor": "Langit di atas musuhmu berubah menjadi kisi panah yang menekan langkahnya.",
        },
    },
    "Warrior": {
        "cleave": {
            "name": "Cleave",
            "cooldown": 2,
            "description": "Ayunan berat untuk menghancurkan pertahanan musuh.",
            "battle": "damage",
            "damage": (18, 28),
            "pierce": 1,
            "flavor": "Bilahmu membelah udara dan mengguncang arena pertempuran.",
        },
        "guard_break": {
            "name": "Guard Break",
            "cooldown": 3,
            "description": "Serangan keras yang melemahkan balasan musuh.",
            "battle": "debuff",
            "damage": (14, 22),
            "debuff": {"monster_atk": -4, "turns": 2},
            "flavor": "Bahu dan pedangmu menghantam dengan ritme yang memaksa lawan kehilangan keseimbangan.",
        },
    },
    "Rogue": {
        "backstab": {
            "name": "Backstab",
            "cooldown": 2,
            "description": "Serangan diam-diam yang memanfaatkan celah.",
            "battle": "damage",
            "damage": (16, 30),
            "crit_bonus": 10,
            "flavor": "Kau muncul dari sudut gelap, dan satu tusukan cukup untuk membuat musuh panik.",
        },
        "smoke_step": {
            "name": "Smoke Step",
            "cooldown": 3,
            "description": "Menyelinap ke kabut untuk menghindari serangan berikutnya.",
            "battle": "buff",
            "heal": 8,
            "guard": 2,
            "flavor": "Jejakmu memudar dalam asap tipis, meninggalkan lawan memukul bayangan.",
        },
    },
    "Poet": {
        "inspire": {
            "name": "Inspire",
            "cooldown": 2,
            "description": "Bait kata yang menguatkan jiwa dan napas.",
            "battle": "buff",
            "heal": 18,
            "exp_boost": 10,
            "flavor": "Kata-katamu mengisi udara, dan bahkan luka terasa lebih ringan untuk dipikul.",
        },
        "lullaby": {
            "name": "Lullaby",
            "cooldown": 3,
            "description": "Nyanyian lembut yang meredam kekuatan musuh.",
            "battle": "debuff",
            "damage": (8, 14),
            "debuff": {"monster_atk": -2, "turns": 3},
            "flavor": "Nada halusmu menurunkan tensi seolah dunia berhenti sejenak untuk mendengar.",
        },
    },
    "Oracle": {
        "foresight": {
            "name": "Foresight",
            "cooldown": 2,
            "description": "Melihat beberapa detik masa depan.",
            "battle": "buff",
            "heal": 10,
            "guard": 3,
            "flavor": "Pola pertempuran terbuka di hadapan matamu, seolah waktu memberi petunjuk lebih dulu.",
        },
        "omen": {
            "name": "Omen",
            "cooldown": 3,
            "description": "Pertanda yang melemahkan niat musuh.",
            "battle": "debuff",
            "damage": (10, 16),
            "debuff": {"monster_atk": -3, "turns": 2},
            "flavor": "Bayangan pertanda menempel di tubuh lawan dan membuat geraknya terasa berat.",
        },
    },
    "Witch": {
        "hex": {
            "name": "Hex",
            "cooldown": 2,
            "description": "Kutukan singkat yang melukai dan mengacaukan.",
            "battle": "debuff",
            "damage": (15, 24),
            "debuff": {"monster_atk": -4, "turns": 2},
            "flavor": "Mantra gelap merayap di bawah kulit lawan seperti duri yang tidak terlihat.",
        },
        "vial_burst": {
            "name": "Vial Burst",
            "cooldown": 3,
            "description": "Ledakan ramuan yang membakar area musuh.",
            "battle": "damage",
            "damage": (18, 28),
            "pierce": 1,
            "flavor": "Ramuanmu pecah dengan cahaya asing, mengubah aroma udara menjadi kabut reaktif.",
        },
    },
    "Hunter": {
        "mark": {
            "name": "Mark",
            "cooldown": 2,
            "description": "Menandai target untuk membuka celah berikutnya.",
            "battle": "debuff",
            "damage": (12, 18),
            "debuff": {"marked": 2},
            "flavor": "Tanda perburuan menempel di tubuh lawan, memancing naluri untuk menyerah lebih dulu.",
        },
        "track_shot": {
            "name": "Track Shot",
            "cooldown": 3,
            "description": "Tembakan pemburu yang mengikuti jejak mangsa.",
            "battle": "damage",
            "damage": (16, 26),
            "flavor": "Panahmu menembus jarak seakan mengenali ritme napas mangsanya.",
        },
    },
    "Alchemist": {
        "catalyst_burst": {
            "name": "Catalyst Burst",
            "cooldown": 2,
            "description": "Reaksi alkimia yang meledak dalam satu napas.",
            "battle": "damage",
            "damage": (14, 24),
            "flavor": "Botol kecil pecah dan udara bergetar oleh reaksi warna-warni yang tak stabil.",
        },
        "brew_salve": {
            "name": "Brew Salve",
            "cooldown": 3,
            "description": "Ramuan instan untuk menahan luka dan racun.",
            "battle": "buff",
            "heal": 24,
            "guard": 1,
            "flavor": "Larutan hangat menutup luka dalam dan memberi napas baru pada tubuhmu.",
        },
    },
    "Blacksmith": {
        "forge_strike": {
            "name": "Forge Strike",
            "cooldown": 2,
            "description": "Hantaman tempa yang seperti palu pandai besi.",
            "battle": "damage",
            "damage": (18, 30),
            "pierce": 2,
            "flavor": "Setiap ayunan terasa seperti dentang palu yang ditempa dari bara dan baja.",
        },
        "iron_wall": {
            "name": "Iron Wall",
            "cooldown": 3,
            "description": "Bertahan layaknya benteng logam.",
            "battle": "buff",
            "heal": 15,
            "guard": 4,
            "flavor": "Kau menancapkan kaki dan tubuhmu terasa sekeras gerbang kota tua.",
        },
    },
    "Jobless": {
        "adapt": {
            "name": "Adapt",
            "cooldown": 2,
            "description": "Meniru pola serangan dan bertahan dengan cepat.",
            "battle": "adaptive",
            "damage": (12, 22),
            "heal": 8,
            "flavor": "Kau menyesuaikan langkah dengan ritme lawan, seolah selalu satu napas lebih siap.",
        },
        "spark": {
            "name": "Spark",
            "cooldown": 3,
            "description": "Ledakan kecil yang tak terduga.",
            "battle": "damage",
            "damage": (10, 20),
            "flavor": "Satu percikan kecil tiba-tiba berubah menjadi momen yang memaksa lawan mundur.",
        },
    },
    "Bard": {
        "soothe": {
            "name": "Soothe",
            "cooldown": 2,
            "description": "Nada yang menyembuhkan dan menenangkan.",
            "battle": "buff",
            "heal": 20,
            "guard": 1,
            "flavor": "Melodimu menambal luka dan menenangkan detak jantung yang liar.",
        },
        "crescendo": {
            "name": "Crescendo",
            "cooldown": 3,
            "description": "Puncak lagu yang mengguncang musuh.",
            "battle": "damage",
            "damage": (14, 24),
            "flavor": "Bait terakhir menggelegar, seperti panggung yang ikut mengangkat semangat.",
        },
    },
    "Paladin": {
        "sanctify": {
            "name": "Sanctify",
            "cooldown": 2,
            "description": "Cahaya suci yang menyucikan luka.",
            "battle": "buff",
            "heal": 28,
            "guard": 2,
            "flavor": "Sinar putih menyelimuti tubuhmu dan meninggalkan rasa hangat yang menenangkan.",
        },
        "judgment": {
            "name": "Judgment",
            "cooldown": 3,
            "description": "Serangan putusan yang penuh tekanan ilahi.",
            "battle": "damage",
            "damage": (18, 28),
            "pierce": 2,
            "flavor": "Hukuman turun bersama kilau yang membuat lawan gentar pada bayangannya sendiri.",
        },
    },
    "Beastmaster": {
        "call_pack": {
            "name": "Call Pack",
            "cooldown": 2,
            "description": "Mengikat insting alam untuk menyerang bersama.",
            "battle": "damage",
            "damage": (16, 26),
            "flavor": "Kau memanggil gema liar dari hutan; seolah tanah sendiri bergerak mendukungmu.",
        },
        "calm_beast": {
            "name": "Calm Beast",
            "cooldown": 3,
            "description": "Menjinakkan amukan lawan untuk sementara.",
            "battle": "debuff",
            "damage": (10, 16),
            "debuff": {"monster_atk": -3, "turns": 2},
            "flavor": "Tatapanmu menjadi tali tak terlihat yang menahan amarah lawan.",
        },
    },
    "Runesmith": {
        "rune_blast": {
            "name": "Rune Blast",
            "cooldown": 2,
            "description": "Ledakan rune yang meletup dari ukiran kuno.",
            "battle": "damage",
            "damage": (18, 28),
            "pierce": 2,
            "flavor": "Rune yang kau ukir menyala dan pecah menjadi serpihan cahaya yang menabrak musuh.",
        },
        "glyph_guard": {
            "name": "Glyph Guard",
            "cooldown": 3,
            "description": "Perisai simbol yang menahan serangan.",
            "battle": "buff",
            "heal": 12,
            "guard": 4,
            "flavor": "Simbol tua muncul di sekelilingmu, membentuk dinding yang terasa purba dan kuat.",
        },
    },
}


RACE_ABILITIES = {
    "Human": {
        "adaptation": {
            "name": "Adaptation",
            "cooldown": 2,
            "description": "Menyesuaikan diri dengan cepat pada suasana sekitar.",
            "kind": "scene",
            "flavor": "Kehadiranmu terasa lentur dan siap menanggapi apa pun yang berubah di sekitar.",
            "effects": {"exp": 8, "gold": 5},
        },
    },
    "Elf": {
        "forest_whisper": {
            "name": "Forest Whisper",
            "cooldown": 2,
            "description": "Mendengar bisikan alam dan membaca arah halus dunia.",
            "kind": "sense",
            "flavor": "Angin kecil membawa petunjuk lembut yang hanya bisa ditangkap indera terasah.",
            "effects": {"exp": 10, "hint": 1},
        },
    },
    "Orc": {
        "war_cry": {
            "name": "War Cry",
            "cooldown": 2,
            "description": "Teriakan yang memahat keberanian di dada.",
            "kind": "scene",
            "flavor": "Suaramu menggema keras, membuat suasana terasa seperti medan perang yang siap meletus.",
            "effects": {"gold": 3, "exp": 6},
        },
    },
    "Dwarf": {
        "stone_echo": {
            "name": "Stone Echo",
            "cooldown": 2,
            "description": "Membaca gema batu untuk menemukan rahasia tersembunyi.",
            "kind": "sense",
            "flavor": "Dari dinding, lantai, dan tanah, batu seolah menceritakan sesuatu yang tak terlihat.",
            "effects": {"craft": 1, "exp": 8},
        },
    },
    "Vampire": {
        "night_veil": {
            "name": "Night Veil",
            "cooldown": 2,
            "description": "Menyelubungi diri dalam aura malam yang elegan.",
            "kind": "stealth",
            "flavor": "Langkahmu memudar seperti lilin yang dipadamkan oleh bayangan sendiri.",
            "effects": {"exp": 8, "gold": 8},
        },
    },
    "Dragontamer": {
        "dragon_pact": {
            "name": "Dragon Pact",
            "cooldown": 3,
            "description": "Memanggil rasa hormat makhluk besar melalui ikrar.",
            "kind": "bond",
            "flavor": "Ada gema kuno di suaramu, seakan naga tua mengangguk dari kejauhan.",
            "effects": {"exp": 12, "loot_bonus": 1},
        },
    },
    "Fairy": {
        "glimmer_blessing": {
            "name": "Glimmer Blessing",
            "cooldown": 2,
            "description": "Cahaya kecil yang memulihkan semangat dan luka ringan.",
            "kind": "heal",
            "flavor": "Kilau lembut menempel pada kulitmu seperti embun pagi yang hangat.",
            "effects": {"heal": 18, "exp": 5},
        },
    },
    "Griffin": {
        "skyline_watch": {
            "name": "Skyline Watch",
            "cooldown": 2,
            "description": "Membaca ruang dari ketinggian pandang langit.",
            "kind": "sense",
            "flavor": "Pandanganmu terasa lebih luas, seperti sang penjaga langit menuntun arah.",
            "effects": {"travel": 1, "exp": 10},
        },
    },
    "Nymph": {
        "brook_song": {
            "name": "Brook Song",
            "cooldown": 2,
            "description": "Nyanyian air yang menyegarkan dan menenangkan.",
            "kind": "heal",
            "flavor": "Suaramu mengalir seperti air jernih yang membersihkan debu perjalanan.",
            "effects": {"heal": 15, "exp": 8},
        },
    },
    "Werewolf": {
        "scent_the_hunt": {
            "name": "Scent the Hunt",
            "cooldown": 2,
            "description": "Mencium jejak bahaya dan peluang di sekitar.",
            "kind": "sense",
            "flavor": "Dunia punya bau baru di hidungmu; target, bahaya, dan jalan pulang jadi lebih jelas.",
            "effects": {"exp": 8, "loot_bonus": 1},
        },
    },
    "Pegasus": {
        "wind_stride": {
            "name": "Wind Stride",
            "cooldown": 2,
            "description": "Melangkah seolah ditopang angin.",
            "kind": "travel",
            "flavor": "Gerakmu terasa ringan dan mulus, seperti lintasan cahaya di udara.",
            "effects": {"travel": 2, "exp": 8},
        },
    },
    "Mermaid": {
        "tide_call": {
            "name": "Tide Call",
            "cooldown": 2,
            "description": "Memanggil perhatian air dan arus sekitar.",
            "kind": "sense",
            "flavor": "Ada riak lembut di ujung kata-katamu, seolah lautan mendengarkan.",
            "effects": {"exp": 8, "gold": 4},
        },
    },
    "Angel": {
        "radiant_blessing": {
            "name": "Radiant Blessing",
            "cooldown": 2,
            "description": "Sinar lembut yang memulihkan harapan dan tubuh.",
            "kind": "heal",
            "flavor": "Cahaya putih menetes pelan dari atas, seakan langit sedang menepuk pundakmu.",
            "effects": {"heal": 22, "exp": 10},
        },
    },
    "Demon": {
        "abyss_bargain": {
            "name": "Abyss Bargain",
            "cooldown": 2,
            "description": "Membayar harga kecil untuk dorongan kekuatan sesaat.",
            "kind": "risk",
            "flavor": "Ada rasa dingin di belakang tengkuk, tapi hasilnya terasa lebih berat dan nyata.",
            "effects": {"gold": 12, "exp": 12, "hp_loss": 6},
        },
    },
    "Bunny": {
        "lucky_hop": {
            "name": "Lucky Hop",
            "cooldown": 2,
            "description": "Lompatan kecil yang memancing keberuntungan.",
            "kind": "luck",
            "flavor": "Langkah ringkas itu seakan memindahkan nasibmu ke jalur yang lebih baik.",
            "effects": {"gold": 10, "exp": 8, "loot_bonus": 1},
        },
    },
    "Sylvan": {
        "grove_whisper": {
            "name": "Grove Whisper",
            "cooldown": 2,
            "description": "Mendengar pesan dari akar dan daun.",
            "kind": "sense",
            "flavor": "Pepohonan di sekelilingmu bergerak pelan, seperti memberi hormat dan petunjuk.",
            "effects": {"craft": 1, "exp": 10},
        },
    },
    "Abyssborn": {
        "shadow_bind": {
            "name": "Shadow Bind",
            "cooldown": 2,
            "description": "Mengikat suasana dengan bayangan kuno.",
            "kind": "stealth",
            "flavor": "Bayangan di sekitarmu menegang seolah menerima perintah tak bersuara.",
            "effects": {"gold": 6, "exp": 10},
        },
    },
}


ROLEPLAY_ACTIONS = {
    "observe": {
        "name": "Observe",
        "cooldown": 0,
        "description": "Mengamati lokasi untuk menangkap detail, aroma, dan tanda bahaya.",
        "effect": "observe",
    },
    "greet": {
        "name": "Greet",
        "cooldown": 0,
        "description": "Menyapa NPC atau karakter lain dengan suasana yang hangat.",
        "effect": "social",
    },
    "rest": {
        "name": "Rest",
        "cooldown": 0,
        "description": "Menulis atau mendeskripsikan momen istirahat yang terasa nyata.",
        "effect": "rest",
    },
    "meditate": {
        "name": "Meditate",
        "cooldown": 0,
        "description": "Menenangkan pikiran dan meresapi atmosfer sekitar.",
        "effect": "meditate",
    },
}


TIER0_DAMAGE_TYPES = ["single_target", "aoe", "heal", "buff", "debuff"]
TIER0_SKILL_TYPES = ["Magic", "Physical", "Support", "Defense"]
TIER0_ELEMENTS = ["Fire", "Ice", "Wind", "Water"]


def _build_tier0_skill_pool(identity_name, source_kind):
    """Generate a deterministic pool of tier-0 skills for a race or job."""
    identity = normalize_name(identity_name)
    seed = f"{source_kind}:{identity.lower()}"
    rng = random.Random(seed)

    verbs = [
        "Arc", "Pulse", "Drift", "Rift", "Thorn", "Surge", "Echo", "Veil",
        "Ward", "Tide", "Spiral", "Bloom", "Flare", "Fang", "Howl", "Halo",
        "Glyph", "Shroud", "Lance", "Torrent", "Bastion", "Mirage", "Beacon", "Nova",
    ]
    motifs = [
        "Aster", "Cinder", "Frost", "Gale", "Mist", "Rune", "Sable", "Aurora",
        "Crimson", "Ivory", "Tempest", "Lumen", "Onyx", "Vesper", "Ember", "Nacre",
        "Solar", "Lunar", "Verdant", "Abyss", "Radiant", "Whisper", "Thunder", "Briar",
    ]
    descriptions = [
        "menata ritme pertempuran dengan ledakan terukur",
        "mengunci ruang gerak lawan lewat tekanan bertahap",
        "menciptakan celah untuk serangan lanjutan",
        "menyalakan momentum saat duel memanas",
        "menahan alur serang lawan tanpa kehilangan tempo",
        "mengguncang formasi lawan dengan resonansi kuat",
        "meredam ancaman sambil mempertebal pertahanan",
        "mengubah arus duel lewat kontrol area singkat",
        "membuka peluang kritikal pada momen tepat",
        "memulihkan posisi tempur saat keadaan menekan",
    ]

    pools = {}
    used_names = set()
    for idx in range(8):
        dmg_type = TIER0_DAMAGE_TYPES[idx % len(TIER0_DAMAGE_TYPES)]
        if dmg_type == "heal":
            skill_type = "Support"
        elif dmg_type == "buff":
            skill_type = "Defense"
        elif dmg_type == "debuff":
            skill_type = "Support"
        else:
            skill_type = rng.choice(["Magic", "Physical"])

        element = rng.choice(TIER0_ELEMENTS) if skill_type == "Magic" else None
        cast_time = round(rng.uniform(0.8, 2.8), 1) if skill_type in {"Magic", "Support"} else 0
        duration = rng.randint(2, 4) if dmg_type in {"buff", "debuff"} or skill_type == "Defense" else 0
        mp_cost = rng.randint(6, 16)
        cooldown = rng.randint(1, 3)

        # Build a unique name per identity.
        for _ in range(30):
            name = f"{identity} {rng.choice(verbs)} {rng.choice(motifs)}"
            if name not in used_names:
                used_names.add(name)
                break

        key = f"t0_{source_kind}_{identity.lower().replace(' ', '_')}_{idx + 1}"
        base_line = descriptions[idx % len(descriptions)]
        description = f"Teknik {identity} yang {base_line}."

        skill_data = {
            "name": name,
            "tier": 0,
            "origin": source_kind,
            "description": description,
            "type_damage": dmg_type,
            "type_skill": skill_type,
            "element": element,
            "cast_time": cast_time,
            "duration": duration,
            "mp_cost": mp_cost,
            "sp_cost": mp_cost,
            "cooldown": cooldown,
            "flavor": f"{identity} menyalurkan teknik ini dengan presisi khas {source_kind}.",
        }

        if dmg_type in {"single_target", "aoe"}:
            min_dmg = rng.randint(12, 20)
            max_dmg = min_dmg + rng.randint(8, 14)
            if dmg_type == "aoe":
                min_dmg = int(min_dmg * 0.85)
                max_dmg = int(max_dmg * 0.9)
            skill_data["battle"] = "damage"
            skill_data["damage"] = (min_dmg, max_dmg)
            if dmg_type == "aoe":
                skill_data["aoe"] = True
        elif dmg_type == "heal":
            skill_data["battle"] = "buff"
            skill_data["heal"] = rng.randint(18, 36)
            skill_data["guard"] = 1
        elif dmg_type == "buff":
            skill_data["battle"] = "buff"
            skill_data["heal"] = rng.randint(6, 16)
            skill_data["guard"] = rng.randint(2, 4)
        else:
            skill_data["battle"] = "debuff"
            skill_data["damage"] = (8, 16)
            skill_data["debuff"] = {"monster_atk": -rng.randint(2, 5), "turns": duration or 2}

        pools[key] = skill_data

    return pools


def random_skill_subset(skill_pool, min_count=5, max_count=10):
    keys = list(skill_pool.keys())
    if not keys:
        return {}
    take = min(len(keys), random.randint(min_count, min(max_count, len(keys))))
    chosen = random.sample(keys, k=take)
    return {key: copy.deepcopy(skill_pool[key]) for key in chosen}


def assign_tier0_skills_for_session(session):
    race_name = session.get("race", DEFAULT_SESSION["race"])
    job_name = session.get("job", DEFAULT_SESSION["job"])
    session["tier0_race_skills"] = random_skill_subset(_build_tier0_skill_pool(race_name, "race"), 1, 3)

    by_job = session.setdefault("tier0_job_skills_by_job", {})
    if not isinstance(by_job, dict):
        by_job = {}
        session["tier0_job_skills_by_job"] = by_job
    by_job[job_name] = random_skill_subset(_build_tier0_skill_pool(job_name, "job"), 1, 3)


def current_tier0_job_skills(session):
    job_name = session.get("job", DEFAULT_SESSION["job"])
    by_job = session.setdefault("tier0_job_skills_by_job", {})
    if not isinstance(by_job, dict):
        by_job = {}
        session["tier0_job_skills_by_job"] = by_job
    skills_map = by_job.get(job_name)
    if not isinstance(skills_map, dict) or not skills_map:
        skills_map = random_skill_subset(_build_tier0_skill_pool(job_name, "job"), 1, 3)
        by_job[job_name] = skills_map
    return skills_map


def current_battle_skills(session):
    merged = {}
    for skill_key, skill_data in current_job_skills(session).items():
        merged[skill_key] = skill_data
    for skill_key, skill_data in (session.get("tier0_race_skills", {}) or {}).items():
        merged[skill_key] = skill_data
    for skill_key, skill_data in current_tier0_job_skills(session).items():
        merged[skill_key] = skill_data
    return merged


def get_job_skills(job_name):
    return JOB_SKILLS.get(job_name, {})


def current_job_skills(session):
    job_name = session.get("job", DEFAULT_SESSION["job"])
    return get_job_skills(job_name)


def skill_lookup(session, skill_name):
    lookup = normalize_name(skill_name).lower()
    for skill_key, skill_data in current_battle_skills(session).items():
        if skill_key.lower() == lookup or skill_data.get("name", "").lower() == lookup:
            return skill_key, skill_data
    return None, None


def skill_cooldowns(session):
    cooldowns = session.setdefault("skill_cooldowns", {})
    if not isinstance(cooldowns, dict):
        cooldowns = {}
        session["skill_cooldowns"] = cooldowns
    return cooldowns


def get_skill_cooldown(session, skill_key):
    return int(skill_cooldowns(session).get(skill_key, 0))


def set_skill_cooldown(session, skill_key, cooldown):
    skill_cooldowns(session)[skill_key] = max(0, int(cooldown))


def reduce_skill_cooldowns(session):
    cooldowns = skill_cooldowns(session)
    for skill_key in list(cooldowns.keys()):
        cooldowns[skill_key] = max(0, int(cooldowns.get(skill_key, 0)) - 1)
        if cooldowns[skill_key] <= 0:
            cooldowns.pop(skill_key, None)


def race_power_cooldowns(session):
    cooldowns = session.setdefault("race_power_cooldowns", {})
    if not isinstance(cooldowns, dict):
        cooldowns = {}
        session["race_power_cooldowns"] = cooldowns
    return cooldowns


def get_race_power_cooldown(session, ability_key):
    ready_at = float(race_power_cooldowns(session).get(ability_key, 0))
    remaining = int(max(0, ready_at - time.time()))
    return remaining


def set_race_power_cooldown(session, ability_key, cooldown_seconds):
    race_power_cooldowns(session)[ability_key] = time.time() + max(0, int(cooldown_seconds))


def race_power_display_line(ability_key, ability_data, session=None):
    remaining = get_race_power_cooldown(session, ability_key) if session else 0
    desc = ability_data.get("description", "")
    return f"- {ability_data.get('name', ability_key)} | CD {ability_data.get('cooldown', 0)}s | {desc} | Ready {remaining == 0}"


def skill_display_line(skill_key, skill_data, session=None):
    cooldown = get_skill_cooldown(session, skill_key) if session else 0
    desc = skill_data.get("description", "")
    return f"- {skill_data.get('name', skill_key)} | CD {skill_data.get('cooldown', 0)} | {desc} | Ready {cooldown == 0}"


def skill_damage_roll(skill_data, session):
    base_min, base_max = skill_data.get("damage", (0, 0))
    bonuses = battle_stat_bonus(session)
    damage = random.randint(int(base_min), int(base_max)) + int(bonuses.get("attack", 0))
    if skill_data.get("crit_bonus") and random.random() < 0.35:
        damage += int(skill_data.get("crit_bonus", 0))
    return max(1, damage)


def get_race_abilities(race_name):
    return RACE_ABILITIES.get(race_name, {})


def current_race_abilities(session):
    race_name = session.get("race", DEFAULT_SESSION["race"])
    return get_race_abilities(race_name)


def race_ability_lookup(session, ability_name):
    lookup = normalize_name(ability_name).lower()
    for ability_key, ability_data in current_race_abilities(session).items():
        if ability_key.lower() == lookup or ability_data.get("name", "").lower() == lookup:
            return ability_key, ability_data
    return None, None


def roleplay_action_lookup(action_name):
    lookup = normalize_name(action_name).lower()
    for action_key, action_data in ROLEPLAY_ACTIONS.items():
        if action_key.lower() == lookup or action_data.get("name", "").lower() == lookup:
            return action_key, action_data
    return None, None


def apply_race_ability(session, world_state, ability_key, ability_data):
    effect_type = ability_data.get("kind", "scene")
    flavor = ability_data.get("flavor", "")
    effects = ability_data.get("effects", {}) if isinstance(ability_data.get("effects", {}), dict) else {}
    lines = []

    if effect_type == "heal":
        heal_amount = int(effects.get("heal", 0))
        session["hp"] = min(session["max_hp"], session["hp"] + heal_amount)
        lines.append(f"Kamu memanggil **{ability_data.get('name', ability_key)}** dan memulihkan {heal_amount} HP.")
    elif effect_type == "sense":
        lines.append(f"Kamu memakai **{ability_data.get('name', ability_key)}** dan memindai suasana sekitar.")
        lines.append(event_flavor(world_state))
        services = services_for_location(session.get("location", DEFAULT_SESSION["location"]))
        if services:
            lines.append("Fasilitas terdekat: " + ", ".join(services))
        session["exp"] += int(effects.get("exp", 0))
    elif effect_type == "travel":
        lines.append(f"Kamu memakai **{ability_data.get('name', ability_key)}** dan melangkah seolah dibantu angin.")
        session["exp"] += int(effects.get("exp", 0))
    elif effect_type == "stealth":
        lines.append(f"Kamu memakai **{ability_data.get('name', ability_key)}** dan menyatu dengan bayangan sekitar.")
        session["gold"] += int(effects.get("gold", 0))
        session["exp"] += int(effects.get("exp", 0))
    elif effect_type == "risk":
        session["gold"] += int(effects.get("gold", 0))
        session["exp"] += int(effects.get("exp", 0))
        session["hp"] = max(1, session["hp"] - int(effects.get("hp_loss", 0)))
        lines.append(f"Kamu menutup **{ability_data.get('name', ability_key)}** dengan harga kecil yang terasa di tubuhmu.")
    elif effect_type == "bond":
        session["exp"] += int(effects.get("exp", 0))
        lines.append(f"Kamu memakai **{ability_data.get('name', ability_key)}** dan menegaskan ikatan dengan dunia di sekitarmu.")
        if effects.get("loot_bonus"):
            bonus_item = random.choice(["Dragon Claw", "Scale", "Ancient Relic"])
            if add_item(session, bonus_item) > 0:
                lines.append(f"Ada resonansi langka yang meninggalkan **{bonus_item}** di inventory-mu.")
            else:
                lines.append("Resonansi menghasilkan loot, tapi inventory-mu sudah melewati weight limit.")
    else:
        session["gold"] += int(effects.get("gold", 0))
        session["exp"] += int(effects.get("exp", 0))
        if effects.get("heal"):
            session["hp"] = min(session["max_hp"], session["hp"] + int(effects.get("heal", 0)))
        if effects.get("craft"):
            session["exp"] += int(effects.get("craft", 0)) * 2
        lines.append(f"Kamu memakai **{ability_data.get('name', ability_key)}**.")

    if effects.get("loot_bonus"):
        loot_pick = random.choice(["Spirit Herb", "Moon Salt", "Iron Ore", "Leather Pelt"])
        if add_item(session, loot_pick) > 0:
            lines.append(f"Keberuntunganmu menghasilkan bonus **{loot_pick}**.")
        else:
            lines.append("Bonus loot gagal dibawa karena weight limit sudah penuh.")

    if flavor:
        lines.append(flavor)

    return lines


def apply_roleplay_action(session, world_state, action_key, action_data, freeform_text):
    effect_type = action_data.get("effect", "social")
    lines = []
    location = session.get("location", DEFAULT_SESSION["location"])
    race_name = session.get("race", DEFAULT_SESSION["race"])
    job_name = session.get("job", DEFAULT_SESSION["job"])
    world_flavor = event_flavor(world_state)

    if effect_type == "observe":
        lines.append(f"Kamu mengamati {location} dengan teliti. {world_flavor}")
        lines.append(f"Ras {race_name} dan job {job_name} membuatmu menangkap detail yang orang lain lewatkan.")
        lines.append(f"Aktivitasmu: {freeform_text or 'mengamati sekeliling dalam diam.'}")
        session["exp"] += 4
    elif effect_type == "social":
        lines.append(f"Kamu menyapa dengan hangat di {location}. Kata-katamu terdengar natural dan hidup.")
        lines.append(f"Aktivitasmu: {freeform_text or 'berinteraksi secara ramah dengan NPC atau pemain lain.'}")
        session["exp"] += 5
        session["gold"] += 2
    elif effect_type == "rest":
        lines.append(f"Kamu menenangkan diri di {location}. Suasana sekitar terasa lebih lembut.")
        lines.append(f"Aktivitasmu: {freeform_text or 'menulis, duduk, atau meresapi dunia sekitar.'}")
        healed = min(session["max_hp"] - session["hp"], 8)
        session["hp"] += healed
        session["exp"] += 3
    elif effect_type == "meditate":
        lines.append(f"Kamu bermeditasi dan membiarkan {location} masuk ke dalam napasmu.")
        lines.append(f"Aktivitasmu: {freeform_text or 'merenung dalam diam, mencari makna di balik kejadian kecil.'}")
        session["exp"] += 6
        session["hp"] = min(session["max_hp"], session["hp"] + 4)
    else:
        lines.append(f"Kamu mengekspresikan roleplay di {location}.")
        lines.append(f"Aktivitasmu: {freeform_text or 'menghidupkan suasana dengan narasi singkat.'}")
        session["exp"] += 4

    if active_world_event(world_state):
        lines.append(world_flavor)

    lines.append("Narasi ini tidak memulai battle dan cocok untuk memperkaya scene roleplay.")
    return lines


def apply_skill_effect(session, battle, skill_key, skill_data):
    damage = skill_damage_roll(skill_data, session)
    flavor = skill_data.get("flavor", "")
    result_lines = []
    effect_type = skill_data.get("battle", "damage")

    if effect_type == "damage":
        battle["monster_hp"] -= damage
        if skill_data.get("pierce"):
            battle["armor_pierce"] = int(skill_data.get("pierce", 0))
        result_lines.append(f"Kamu memakai **{skill_data.get('name', skill_key)}** dan memberi {damage} damage.")
    elif effect_type == "debuff":
        battle["monster_hp"] -= damage
        debuff = skill_data.get("debuff", {})
        if debuff:
            battle.setdefault("debuffs", {}).update(debuff)
        result_lines.append(f"Kamu memakai **{skill_data.get('name', skill_key)}** dan memberi {damage} damage sambil melemahkan musuh.")
    elif effect_type == "buff":
        heal_amount = int(skill_data.get("heal", 0))
        session["hp"] = min(session["max_hp"], session["hp"] + heal_amount)
        battle["player_hp"] = session["hp"]
        guard = int(skill_data.get("guard", 0))
        if guard:
            battle["player_guard"] = int(battle.get("player_guard", 0)) + guard
        result_lines.append(f"Kamu memakai **{skill_data.get('name', skill_key)}** dan memulihkan {heal_amount} HP.")
    elif effect_type == "adaptive":
        session["hp"] = min(session["max_hp"], session["hp"] + int(skill_data.get("heal", 0)))
        damage += int(battle_stat_bonus(session).get("defense", 0))
        battle["monster_hp"] -= damage
        result_lines.append(f"Kamu memakai **{skill_data.get('name', skill_key)}** dan meniru irama lawan untuk memberi {damage} damage.")

    if flavor:
        result_lines.append(flavor)

    return result_lines


def battle_debuff_attack_value(battle):
    debuffs = battle.get("debuffs", {})
    attack_value = int(battle.get("monster_atk", 0)) + int(debuffs.get("monster_atk", 0))
    return max(0, attack_value)


def advance_battle_debuffs(battle):
    debuffs = battle.get("debuffs")
    if not isinstance(debuffs, dict):
        return
    turns_left = int(debuffs.get("turns", 0))
    if turns_left > 0:
        debuffs["turns"] = turns_left - 1
    if debuffs.get("turns", 0) <= 0:
        battle.pop("debuffs", None)


def apply_player_guard(battle, damage):
    guard = int(battle.get("player_guard", 0))
    if guard <= 0:
        return max(0, damage)
    reduced = max(0, damage - guard)
    battle["player_guard"] = max(0, guard - 1)
    return reduced


def battle_victory_lines(session, battle, world_state):
    battle_context = session.get("battle_context", {}) if isinstance(session.get("battle_context", {}), dict) else {}
    loot_rolls = random.randint(1, 2)
    reward_loot = []
    for _ in range(loot_rolls):
        if battle["loot"] and random.random() < 0.85:
            reward_loot.append(random.choice(battle["loot"]))
    if not reward_loot and battle["loot"]:
        reward_loot.append(random.choice(battle["loot"]))

    if event_modifier(world_state, "loot_bonus", 0) > 0 and battle["loot"] and random.random() < 0.5:
        reward_loot.append(random.choice(battle["loot"]))
    if int(battle_context.get("loot_bonus", 0)) > 0 and battle["loot"] and random.random() < 0.35:
        reward_loot.append(random.choice(battle["loot"]))

    gold_gain = random.randint(8, 24) + session["level"] * 2 + max(0, session.get("bonuses", {}).get("gold", 0))
    gold_gain += int(battle_context.get("gold", 0))
    exp_gain = random.randint(18, 35) + session["level"] * 4 + max(0, session.get("bonuses", {}).get("exp", 0))
    exp_gain += int(battle_context.get("exp", 0))
    session["gold"] += gold_gain
    session["exp"] += exp_gain
    session["hp"] = max(1, battle["player_hp"])
    session["battle"] = None
    stored_loot = []
    for item_name in reward_loot:
        if add_item(session, item_name) > 0:
            stored_loot.append(item_name)
    session["last_loot"] = stored_loot
    unlock_achievement(session, "first_blood")
    return stored_loot, gold_gain, exp_gain


def battle_defeat_recovery(session, battle):
    session["battle"] = None
    session["hp"] = session["max_hp"]
    battle["player_hp"] = session["hp"]


async def battle_round_after_action(ctx, session, battle, world_state, result_lines):
    if battle["monster_hp"] <= 0:
        reward_loot, gold_gain, exp_gain = battle_victory_lines(session, battle, world_state)
        for item_name in reward_loot:
            await refresh_active_quests_from_event(session, "collect", item_name)
        await apply_level_up_if_needed(session)
        await save_session_async(ctx.author.id, session)
        await save_world_state_async(world_state)
        result_lines.append(f"{battle['monster_name']} tumbang. Kamu mendapat {gold_gain} gold dan {exp_gain} EXP.")
        if reward_loot:
            result_lines.append(f"Loot: {', '.join(reward_loot)}")
        else:
            result_lines.append("Loot: tidak ada item yang jatuh.")
        await ctx.send("\n".join(result_lines))
        return True

    monster_attack = battle_debuff_attack_value(battle)
    await asyncio.sleep(1)
    monster_damage = max(0, random.randint(1, max(1, monster_attack)) - battle_stat_bonus(session)["defense"])
    monster_damage = apply_player_guard(battle, monster_damage)
    if monster_damage == 0 and random.random() < 0.4:
        monster_damage = 1

    battle["player_hp"] -= monster_damage
    session["hp"] = max(0, battle["player_hp"])
    advance_battle_debuffs(battle)
    result_lines.append(f"{battle['monster_name']} membalas dan memberi {monster_damage} damage. HP kamu sekarang {session['hp']}.")

    if battle["player_hp"] <= 0:
        battle_defeat_recovery(session, battle)
        result_lines.append("Kamu kalah dan tersadar kembali di lokasi aman terdekat dengan HP penuh.")

    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    await ctx.send("\n".join(result_lines))
    return True


async def get_world_state_async():
    loop = bot.loop
    state = await loop.run_in_executor(None, db.get_world_state)
    return ensure_world_state(state)


async def save_world_state_async(state):
    loop = bot.loop
    await loop.run_in_executor(None, db.save_world_state, ensure_world_state(state))


def active_world_event(world_state):
    event = world_state.get("event")
    if isinstance(event, dict):
        return event
    return None


def pick_world_event():
    events = world_event_catalog()
    return copy.deepcopy(random.choice(events)) if events else None


async def tick_world_turn(world_state, trigger="travel"):
    world_state = ensure_world_state(world_state)
    world_state["turn_counter"] = int(world_state.get("turn_counter", 0)) + 1
    event = active_world_event(world_state)

    if event:
        world_state["turns_left"] = max(0, int(world_state.get("turns_left", 0)) - 1)
        if world_state["turns_left"] <= 0:
            world_state["history"].append(event["name"])
            world_state["event"] = None
            world_state["turns_left"] = 0
            event = None

    if not event and random.random() < 0.35:
        event = pick_world_event()
        if event:
            world_state["event"] = event
            world_state["turns_left"] = int(event.get("duration_turns", 3))
            world_state["history"].append(event["name"])

    return world_state


def event_modifier(world_state, key, default=0):
    event = active_world_event(world_state)
    if not event:
        return default
    return int(event.get(key, default))


def event_flavor(world_state):
    event = active_world_event(world_state)
    if not event:
        return "Tidak ada event dunia aktif saat ini."
    return (
        f"**{event['name']}** | {event.get('flavor', '')} | Sisa putaran: {world_state.get('turns_left', 0)}"
    )


def battle_stat_bonus(session):
    bonuses = resolve_character_bonuses(session)
    attack = int(bonuses.get("attack", 0))
    defense = int(bonuses.get("defense", 0))

    companion_bonuses = companion_bonus(session)
    attack += int(companion_bonuses.get("attack", 0))
    defense += int(companion_bonuses.get("defense", 0))
    bonuses["luck"] = bonuses.get("luck", 0) + int(companion_bonuses.get("luck", 0))
    bonuses["exp"] = bonuses.get("exp", 0) + int(companion_bonuses.get("exp", 0))
    bonuses["mana"] = bonuses.get("mana", 0) + int(companion_bonuses.get("mana", 0))

    battle_context = session.get("battle_context", {}) if isinstance(session.get("battle_context", {}), dict) else {}
    attack += int(battle_context.get("attack", 0))
    defense += int(battle_context.get("defense", 0))

    weapon = session.get("equipped", {}).get("weapon")
    armor = session.get("equipped", {}).get("armor")
    trinket = session.get("equipped", {}).get("trinket")

    for item_name in [weapon, armor, trinket]:
        if not item_name:
            continue
        item = item_catalog().get(item_name)
        if not isinstance(item, dict):
            continue
        attack += int(item.get("attack", 0))
        defense += int(item.get("defense", 0))
        upgrade_level = int(session.get("gear_upgrades", {}).get(item_name, 0))
        if upgrade_level:
            attack += upgrade_level
            defense += max(0, upgrade_level - 1)

    return {"attack": attack, "defense": defense}


def crafting_bonus(session):
    bonuses = resolve_character_bonuses(session)
    return int(bonuses.get("craft", 0))


def luck_bonus(session):
    bonuses = resolve_character_bonuses(session)
    return int(bonuses.get("luck", 0))


def companion_catalog():
    return COMPANION_CATALOG if isinstance(COMPANION_CATALOG, dict) else {}


def find_companion(name):
    lookup = normalize_name(name).lower()
    for companion_name, data in companion_catalog().items():
        if companion_name.lower() == lookup or lookup in companion_name.lower():
            return companion_name, data
    return None, None


def companion_bonus(session):
    bonuses = {"attack": 0, "defense": 0, "hp": 0, "luck": 0, "exp": 0, "travel": 0, "mana": 0}
    for companion in session.get("companions", []):
        companion_name = companion if isinstance(companion, str) else companion.get("name")
        if not companion_name:
            continue
        _, data = find_companion(companion_name)
        if not data:
            continue
        for key, value in data.get("bonuses", {}).items():
            bonuses[key] = bonuses.get(key, 0) + int(value)
    return bonuses


def companion_display_line(companion_name, data, session=None):
    active = False
    if session:
        active = any(
            (entry if isinstance(entry, str) else entry.get("name")) == companion_name
            for entry in session.get("companions", [])
        )
    bonuses = data.get("bonuses", {})
    bonus_text = ", ".join(f"{key}+{value}" for key, value in bonuses.items()) or "Tidak ada bonus"
    return f"- {companion_name} [{data.get('role', 'Companion')}] | {bonus_text} | Active {active}"


def reputation_defaults():
    return {faction: 0 for faction in FACTION_NAMES}


def reputation_map(session):
    reputation = session.setdefault("reputation", {})
    if not isinstance(reputation, dict):
        reputation = {}
        session["reputation"] = reputation
    for faction, value in reputation_defaults().items():
        reputation.setdefault(faction, value)
    return reputation


def adjust_reputation(session, faction, amount):
    reputation = reputation_map(session)
    reputation[faction] = int(reputation.get(faction, 0)) + int(amount)
    return reputation[faction]


def reputation_tier(value):
    if value >= 80:
        return "Legendary"
    if value >= 50:
        return "Honored"
    if value >= 25:
        return "Friendly"
    if value >= 10:
        return "Known"
    if value >= 0:
        return "Neutral"
    if value >= -15:
        return "Wary"
    return "Hostile"


def reputation_summary_lines(session, faction=None):
    reputation = reputation_map(session)
    if faction:
        value = reputation.get(faction, 0)
        return [f"{faction}: {value} ({reputation_tier(value)})"]
    lines = []
    for faction_name, value in sorted(reputation.items(), key=lambda item: item[0].lower()):
        lines.append(f"- {faction_name}: {value} ({reputation_tier(value)})")
    return lines


def world_party_map(world_state):
    world_state = ensure_world_state(world_state)
    parties = world_state.setdefault("parties", {})
    if not isinstance(parties, dict):
        parties = {}
        world_state["parties"] = parties
    return parties


def party_key_for_channel(channel_id):
    return str(channel_id)


def get_channel_party(world_state, channel_id):
    return world_party_map(world_state).get(party_key_for_channel(channel_id))


def set_channel_party(world_state, channel_id, party):
    world_party_map(world_state)[party_key_for_channel(channel_id)] = party


def party_member_entries(party):
    members = party.get("members", []) if isinstance(party, dict) else []
    return members if isinstance(members, list) else []


def party_member_ids(party):
    ids = []
    for member in party_member_entries(party):
        if isinstance(member, dict) and member.get("id") is not None:
            ids.append(str(member.get("id")))
    return ids


def party_size(party):
    return len(party_member_entries(party))


def build_party_bonus(party):
    size = party_size(party)
    return {
        "attack": max(0, size - 1),
        "defense": 1 if size >= 2 else 0,
        "luck": 1 if size >= 3 else 0,
        "exp": size * 2,
        "loot_bonus": 1 if size >= 3 else 0,
    }


def refresh_battle_context(session, world_state, channel_id):
    party = get_channel_party(world_state, channel_id)
    context = build_party_bonus(party) if party else {"attack": 0, "defense": 0, "luck": 0, "exp": 0, "loot_bonus": 0}
    session["battle_context"] = context
    return context


def party_summary_embed(party):
    if not party:
        embed = create_menu_embed(
            "Party",
            "Belum ada party di channel ini",
            color=COLOR_COMPANION,
            icon="👥"
        )
        return embed
    members = party_member_entries(party)
    member_names = ", ".join(member.get("name", "Unknown") for member in members) or "Tidak ada anggota"
    bonus = build_party_bonus(party)
    
    embed = create_menu_embed(
        party.get('name', 'Etherial Party'),
        f"Leader: {party.get('leader_name', 'Unknown')} • {len(members)} Members",
        color=COLOR_COMPANION,
        icon="👥"
    )
    
    embed.add_field(name="👨‍💼 Party Leader", value=party.get('leader_name', 'Unknown'), inline=True)
    embed.add_field(name="👥 Total Members", value=str(len(members)), inline=True)
    embed.add_field(name="📍 Anggota", value=member_names, inline=False)
    
    embed.add_field(
        name="⚔️ Bonus Damage",
        value=f"+{bonus['attack']}",
        inline=True
    )
    embed.add_field(
        name="🛡️ Bonus Defense",
        value=f"+{bonus['defense']}",
        inline=True
    )
    embed.add_field(
        name="⭐ Bonus EXP",
        value=f"+{bonus['exp']}",
        inline=True
    )
    embed.add_field(
        name="🎁 Bonus Loot",
        value=f"+{bonus['loot_bonus']}",
        inline=True
    )
    embed.set_footer(text="💡 Gunakan !party <create|join|leave|disband> untuk manage party")
    return embed


def story_event_candidates(session, world_state):
    race_name = session.get("race", DEFAULT_SESSION["race"])
    job_name = session.get("job", DEFAULT_SESSION["job"])
    location = session.get("location", DEFAULT_SESSION["location"])
    region = LOCATION_TO_REGION.get(location, location)
    candidates = []
    for event in STORY_EVENT_POOL:
        score = 0
        if location in event.get("regions", []):
            score += 3
        if region in event.get("regions", []):
            score += 2
        if race_name in event.get("race", []):
            score += 3
        if job_name in event.get("job", []):
            score += 3
        if active_world_event(world_state):
            score += 1
        if score > 0:
            candidates.append((score, event))
    return candidates


def choose_story_event(session, world_state):
    candidates = story_event_candidates(session, world_state)
    if not candidates:
        return random.choice(STORY_EVENT_POOL)
    weights = [score for score, _ in candidates]
    chosen = random.choices([event for _, event in candidates], weights=weights, k=1)[0]
    return chosen


def story_event_text(session, world_state, event, party=None):
    race_name = session.get("race", DEFAULT_SESSION["race"])
    job_name = session.get("job", DEFAULT_SESSION["job"])
    location = session.get("location", DEFAULT_SESSION["location"])
    companion_names = [c if isinstance(c, str) else c.get("name") for c in session.get("companions", [])]
    companion_text = ", ".join([name for name in companion_names if name]) or "Tidak ada companion"
    return [
        f"**{event['title']}**",
        event.get("narrative", ""),
        f"Lokasi: {location} | Ras: {race_name} | Job: {job_name}",
        f"Companion: {companion_text}",
        f"Party: {party.get('name') if party else 'Tidak ada party aktif'}",
    ]


def apply_story_event_reward(session, event):
    reward = event.get("reward", {})
    session["exp"] += int(reward.get("exp", 0))
    session["gold"] += int(reward.get("gold", 0))
    rep_reward = reward.get("reputation", {})
    for faction, amount in rep_reward.items():
        adjust_reputation(session, faction, amount)


def story_event_faction(session, event):
    rep = event.get("reward", {}).get("reputation", {})
    if rep:
        return next(iter(rep.keys()))
    race_name = session.get("race", DEFAULT_SESSION["race"])
    if race_name in {"Angel", "Pegasus", "Griffin"}:
        return "Sky Choir"
    if race_name in {"Mermaid"}:
        return "Sea Court"
    if race_name in {"Dwarf"}:
        return "BlackSmith"
    return "Adventurer Guild"


def achievement_catalog():
    return ACHIEVEMENT_CATALOG


def unlocked_achievement_ids(session):
    achievements = session.get("achievements", [])
    ids = []
    for entry in achievements:
        if isinstance(entry, dict) and entry.get("id"):
            ids.append(entry["id"])
        elif isinstance(entry, str):
            ids.append(entry)
    return ids


def unlock_achievement(session, achievement_id):
    catalog = achievement_catalog()
    if achievement_id not in catalog:
        return None
    unlocked = unlocked_achievement_ids(session)
    if achievement_id in unlocked:
        return None

    data = catalog[achievement_id]
    session.setdefault("achievements", []).append({
        "id": achievement_id,
        "title": data["title"],
        "description": data["description"],
        "unlocked_at": time.time(),
    })
    reward = data.get("reward", {})
    session["exp"] += int(reward.get("exp", 0))
    session["gold"] += int(reward.get("gold", 0))
    return data


def achievement_summary_lines(session):
    catalog = achievement_catalog()
    unlocked = unlocked_achievement_ids(session)
    if not unlocked:
        return ["Belum ada achievement yang terbuka."]

    lines = []
    for achievement_id in unlocked:
        data = catalog.get(achievement_id)
        if not data:
            continue
        lines.append(f"- {data['title']}: {data['description']}")
    return lines or ["Belum ada achievement yang terbuka."]


def get_starter_kit(race_key):
    """Get a random starter kit for the given race."""
    starter_kits = load_json("starter_kits.json", use_root=True)
    if not starter_kits or race_key not in starter_kits:
        # Fallback default kit if race not found
        return {
            "name": "Basic Starter",
            "description": "Perlengkapan dasar untuk memulai",
            "weapon": "Rusty Sword",
            "armor": "Leather Armor",
            "trinket": None,
            "backpack": "Traveler Pack"
        }
    
    kits = starter_kits[race_key]
    return random.choice(kits)


def apply_starter_kit_to_session(session, race_key):
    """Apply a random starter kit to a character session and add to inventory."""
    kit = get_starter_kit(race_key)

    items_added = []

    if kit.get("weapon"):
        if add_item(session, kit["weapon"], 1) > 0:
            items_added.append(kit["weapon"])

    if kit.get("armor"):
        if add_item(session, kit["armor"], 1) > 0:
            items_added.append(kit["armor"])

    if kit.get("trinket"):
        if add_item(session, kit["trinket"], 1) > 0:
            items_added.append(kit["trinket"])

    if kit.get("backpack"):
        if add_item(session, kit["backpack"], 1) > 0:
            items_added.append(kit["backpack"])

    # Equip the items if they exist
    if kit.get("weapon") and kit.get("weapon") in session.get("inventory", []):
        session["equipped"]["weapon"] = kit["weapon"]

    if kit.get("armor") and kit.get("armor") in session.get("inventory", []):
        session["equipped"]["armor"] = kit["armor"]

    if kit.get("trinket") and kit.get("trinket") in session.get("inventory", []):
        session["equipped"]["trinket"] = kit["trinket"]

    if kit.get("backpack") and kit.get("backpack") in session.get("inventory", []):
        session["equipped"]["backpack"] = kit["backpack"]
    
    return kit, items_added


async def get_session_async(user_id):
    loop = bot.loop
    session = await loop.run_in_executor(None, db.get_session, str(user_id))
    return ensure_session(session)


async def save_session_async(user_id, session):
    loop = bot.loop
    await loop.run_in_executor(None, db.save_session, str(user_id), ensure_session(session))


async def finalize_session(ctx, session):
    await save_session_async(ctx.author.id, session)


async def apply_level_up_if_needed(session):
    # Grant stat points and recalculate derived stats on level up
    while session["exp"] >= session["level"] * 100:
        session["exp"] -= session["level"] * 100
        session["level"] += 1
        # Grant 5 stat points per level
        session.setdefault("stat_points", 0)
        session["stat_points"] += 5
        # Recalculate derived stats with equipment bonuses
        base = session.get("base_stats", DEFAULT_SESSION.get("base_stats", {}))
        equip_bonus = resolve_equipment_bonuses(session)
        derived = stats.calculate_derived_stats(base, session.get("level", 1), equipment_bonus=equip_bonus)
        session["derived_stats"] = derived
        session["max_hp"] = derived.get("max_hp", session.get("max_hp", 100))
        session["max_sp"] = derived.get("max_sp", session.get("max_sp", 50))
        session["hp"] = session["max_hp"]
        session["sp"] = session["max_sp"]


def stat_block(session):
    weapon = session["equipped"].get("weapon") or "None"
    armor = session["equipped"].get("armor") or "None"
    trinket = session["equipped"].get("trinket") or "None"
    backpack = session["equipped"].get("backpack") or "None"
    active = [q for q in session.get("quests", []) if q.get("status") == "active"]
    bonuses = session.get("bonuses") or resolve_character_bonuses(session)
    battle_bonus = battle_stat_bonus(session)
    return (
        f"Ras: {session.get('race', 'Human')} | Job: {session.get('job', 'Jobless')}\n"
        f"Title: {session.get('title', 'Wanderer')}\n"
        f"Lokasi: {session['location']}\n"
        f"HP: {session['hp']}/{session['max_hp']}\n"
        f"Level: {session['level']} | EXP: {session['exp']}\n"
        f"Gold: {session['gold']}\n"
        f"Weapon: {weapon}\n"
        f"Armor: {armor}\n"
        f"Trinket: {trinket}\n"
        f"Backpack: {backpack}\n"
        f"Quest aktif: {len(active)}\n"
        f"Bonus aktif: atk+{battle_bonus['attack']} def+{battle_bonus['defense']} craft+{bonuses.get('craft', 0)} luck+{bonuses.get('luck', 0)}"
    )


def services_for_location(location):
    return [entry[1] for entry in SERVICE_ACTIONS_BY_LOCATION.get(location, [])]


def guild_registered(session):
    return bool(session.get("registered_at_guild", False) or session.get("registered_at_receptionist", False))


def location_service_lines(location):
    region = LOCATION_TO_REGION.get(location, "Wilayah Tak Dikenal")
    npc_name = MAIN_SERVICE_LOCATIONS.get(location, "NPC")
    actions = SERVICE_ACTIONS_BY_LOCATION.get(location, [])
    lines = [
        f"**{npc_name}** menatapmu dengan tenang dari {location}.",
        f"Area: {region}",
        "Gunakan command khusus lokasi ini untuk berinteraksi dengan NPC setempat.",
    ]
    if actions:
        action_text = ", ".join(f"`!{command}`" for command, _, _ in actions)
        lines.append(f"Command tersedia: {action_text}")
    return lines


def receptionist_lines(location):
    return location_service_lines(location)


def create_quest_offer(session, location, kind, title, objective_type, target, count, reward_gold, reward_items, branches=None):
    return {
        "id": quest_id(),
        "giver": MAIN_SERVICE_LOCATIONS.get(location, "Receptionist"),
        "location": location,
        "kind": kind,
        "title": title,
        "description": title,
        "objective": {"type": objective_type, "target": target, "count": count},
        "progress": 0,
        "count": count,
        "reward": {"gold": reward_gold, "items": reward_items},
        "branches": branches or [],
        "branch_selected": None,
        "status": "available",
    }


def generate_quest_offers(location, world_state=None):
    region = LOCATION_TO_REGION.get(location, "Kota Utama")
    region_monsters = []
    for loc in MAP.get("Etherial", {}).get(region, []):
        region_monsters.extend(MONSTERS.get(loc, []))

    offers = []
    if region_monsters:
        monster = random.choice(region_monsters)
        reward = quest_reward_template("hunt", world_state)
        offers.append(
            create_quest_offer(
                None,
                location,
                "hunt",
                f"Hunt: Singkirkan {monster['name']}",
                "hunt",
                monster["name"],
                random.randint(2, 4),
                reward["gold"],
                reward["items"],
            )
        )

    item_name, item_data = random.choice(list(item_catalog().items())) if item_catalog() else ("Health Potion", {"name": "Health Potion"})
    reward = quest_reward_template("collect", world_state)
    offers.append(
        create_quest_offer(
            None,
            location,
            "collect",
            f"Collect: Kumpulkan {item_name}",
            "collect",
            item_name,
            random.randint(2, 5),
            reward["gold"],
            reward["items"],
        )
    )

    visit_targets = [loc for loc in MAP.get("Etherial", {}).get(region, []) if loc != location]
    if visit_targets:
        target = random.choice(visit_targets)
        reward = quest_reward_template("visit", world_state)
        offers.append(
            create_quest_offer(
                None,
                location,
                "visit",
                f"Scout: Datangi {target}",
                "visit",
                target,
                1,
                reward["gold"],
                reward["items"],
            )
        )

    if random.random() < 0.75:
        branch_target = random.choice(region_monsters)["name"] if region_monsters else random.choice(all_locations())
        branch_reward_a = quest_reward_template("hunt", world_state)
        branch_reward_b = quest_reward_template("visit", world_state)
        branch_title = f"Dilema Regional: Jejak {branch_target}"
        offers.append(
            create_quest_offer(
                None,
                location,
                "branch",
                branch_title,
                "branch",
                branch_target,
                1,
                branch_reward_a["gold"],
                branch_reward_a["items"],
                branches=[
                    {
                        "id": "warpath",
                        "title": "Warpath",
                        "kind": "hunt",
                        "objective": {"type": "hunt", "target": branch_target, "count": 3},
                        "reward": branch_reward_a,
                    },
                    {
                        "id": "veilpath",
                        "title": "Veilpath",
                        "kind": "visit",
                        "objective": {"type": "visit", "target": location, "count": 1},
                        "reward": branch_reward_b,
                    },
                ],
            )
        )

    return offers[:3]


def quest_display_line(quest):
    objective = quest["objective"]
    progress = quest.get("progress", 0)
    base = (
        f"[{quest['id']}] {quest['title']} | Target: {objective['target']} x{objective['count']} | "
        f"Progress: {progress}/{objective['count']} | Reward: {quest['reward']['gold']} gold + {', '.join(quest['reward']['items'])}"
    )
    branches = quest.get("branches") or []
    if branches:
        branch_text = " | Branches: " + ", ".join(f"{branch['id']}({branch['title']})" for branch in branches)
        base += branch_text
    return base


async def refresh_active_quests_from_event(session, event_type, target):
    changed = False
    for quest in session.get("quests", []):
        if quest.get("status") != "active":
            continue
        objective = quest.get("objective", {})
        if objective.get("type") != event_type:
            continue
        if str(objective.get("target", "")).lower() != str(target).lower():
            continue
        if quest.get("progress", 0) < quest.get("count", 1):
            quest["progress"] = min(quest.get("count", 1), quest.get("progress", 0) + 1)
            changed = True
    if changed:
        await apply_level_up_if_needed(session)
    return changed


async def reward_quest(session, quest):
    session["gold"] += int(quest["reward"].get("gold", 0))
    stored_items = []
    for item in quest["reward"].get("items", []):
        if add_item(session, item) > 0:
            stored_items.append(item)
    quest.setdefault("reward", {})["items"] = stored_items
    session["exp"] += 40 + (quest.get("count", 1) * 10)
    quest_kind = quest.get("kind", "hunt")
    if quest_kind in {"hunt", "branch"}:
        adjust_reputation(session, "Adventurer Guild", 3)
    elif quest_kind == "collect":
        adjust_reputation(session, "Alchemist", 3)
    elif quest_kind == "visit":
        adjust_reputation(session, "Tavern Circle", 2)
    else:
        adjust_reputation(session, "Adventurer Guild", 1)
    unlock_achievement(session, "first_quest")
    await apply_level_up_if_needed(session)


async def complete_if_ready(session, quest):
    objective = quest.get("objective", {})
    if quest.get("status") != "active":
        return False, "Quest belum aktif."

    if objective.get("type") == "visit":
        if session.get("location") != objective.get("target"):
            return False, f"Kamu harus berada di {objective.get('target')} untuk menyelesaikan quest ini."
        quest["progress"] = 1

    if quest.get("progress", 0) < quest.get("count", 1):
        return False, f"Progress masih {quest.get('progress', 0)}/{quest.get('count', 1)}."

    quest["status"] = "completed"
    await reward_quest(session, quest)
    return True, f"Quest selesai: {quest['title']}"


@bot.event
async def on_ready():
    fs_status = db.get_firestore_status()
    firestore_msg = "✅ Firestore connected" if fs_status["enabled"] else "⚠️ Using in-memory storage"
    print(f"Bot ready as {bot.user} — prefix={PREFIX}")
    print(f"Database: {firestore_msg}")
    logger.info(f"Firestore status: {fs_status}")


def help_pages():
    return [
        {
            "title": "⚔️ Character & Profil",
            "color": 0xFF6B00,
            "commands": [
                ("createchar <race> <name>", "Buat atau ubah karakter"),
                ("profile", "Lihat profil karakter"),
                ("status", "Status karakter (HP, level, exp)"),
                ("races", "Daftar ras tersedia"),
                ("jobs", "Daftar job/class tersedia"),
                ("racepowers", "Daftar ability ras kamu"),
                ("racepower <ability>", "Pakai ability ras"),
            ]
        },
        {
            "title": "👥 Social & Companion",
            "color": 0xFF1493,
            "commands": [
                ("party <create|join|leave|info|disband>", "Kelola party channel"),
                ("companions", "Lihat companion yang dimiliki"),
                ("recruit <nama>", "Rekrut companion baru"),
                ("dismiss <nama>", "Lepas companion"),
                ("scene <aksi>", "Tampilkan adegan roleplay"),
                ("story", "Jalankan story event personal"),
                ("reputation [faction]", "Lihat reputasi faction"),
                ("achievements", "Lihat milestone terbuka"),
            ]
        },
        {
            "title": "🗺️ Locations & NPC",
            "color": 0x228B22,
            "commands": [
                ("cityhall", "City Hall - Kota Utama"),
                ("guild", "Adventurer Guild - Registrasi quest"),
                ("blacksmith", "BlackSmith - Upgrade weapon/armor"),
                ("alchemist", "Alchemist - Upgrade trinket"),
                ("tavern", "Tavern - Rest & companion"),
                ("frontier", "Frontier Post - Perjalanan"),
                ("map", "Tampilkan peta Etherial"),
                ("travel <lokasi>", "Pindah ke lokasi lain"),
                ("explore <lokasi>", "Jelajahi lokasi & dapat event"),
                ("bestiary [lokasi]", "Daftar monster di lokasi"),
            ]
        },
        {
            "title": "💼 Items & Crafting",
            "color": 0xFFD700,
            "commands": [
                ("inventory", "Daftar inventory kamu"),
                ("use <item>", "Gunakan item consumable"),
                ("equip <item>", "Pasang equipment"),
                    ("equipped", "Lihat equipment yang sedang dipakai"),
                ("unequip <slot>", "Lepas equipment"),
                ("recipes", "Lihat resep crafting"),
                ("craft <item> [qty]", "Buat item di station cocok"),
                ("upgrade <item>", "Tingkatkan equipment (di BlackSmith/Alchemist)"),
                ("shop", "Lihat toko lokasi"),
                ("buy <item> [qty]", "Beli item"),
            ]
        },
        {
            "title": "📜 Quest & Battle",
            "color": 0x8B0000,
            "commands": [
                ("guild", "Guild desk - Registrasi dan lihat quest"),
                ("questboard", "Lihat quest di Guild"),
                ("acceptquest <nomor|id>", "Ambil quest"),
                ("questpath <id> <branch>", "Pilih cabang quest"),
                ("quests", "Lihat quest aktif"),
                ("completequest <id>", "Selesaikan quest"),
                ("battle", "Cek battle aktif"),
                ("startbattle", "Mulai battle encounter"),
                ("attack", "Serang musuh"),
                ("skill <nama>", "Pakai skill job"),
                ("flee", "Kabur dari battle"),
                ("loot <monster>", "Lihat loot table"),
            ]
        },
        {
            "title": "🌍 World State",
            "color": 0x00CED1,
            "commands": [
                ("world", "Lihat state dunia"),
                ("event", "Lihat event dunia aktif"),
                ("help", "Tampilkan halaman help"),
            ]
        },
    ]


def create_help_embed(page_number=0):
    pages = help_pages()
    if page_number < 0 or page_number >= len(pages):
        page_number = 0
    
    page_data = pages[page_number]
    embed = discord.Embed(
        title=f"{page_data['title']} — Page {page_number + 1}/{len(pages)}",
        color=page_data["color"],
        description="─────────────────────\nGunakan reaction untuk navigasi"
    )
    
    for cmd, desc in page_data["commands"]:
        embed.add_field(
            name=f"``{PREFIX}{cmd}``",
            value=f"└─ {desc}",
            inline=False
        )
    
    nav_text = "⬅️ Prev  •  🏠 Home  •  Next ➡️"
    embed.set_footer(text=nav_text)
    return embed


@bot.command(name="help", aliases=["commands", "helpbot"])
async def cmd_help(ctx):
    pages = help_pages()
    current_page = 0
    
    embed = create_help_embed(current_page)
    msg = await ctx.send(embed=embed)
    
    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")
    await msg.add_reaction("🏠")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "🏠"] and reaction.message.id == msg.id
    
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=180, check=check)
            await msg.remove_reaction(reaction, user)
            
            if str(reaction.emoji) == "⬅️":
                current_page = (current_page - 1) % len(pages)
            elif str(reaction.emoji) == "➡️":
                current_page = (current_page + 1) % len(pages)
            elif str(reaction.emoji) == "🏠":
                current_page = 0
            
            embed = create_help_embed(current_page)
            await msg.edit(embed=embed)
            
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
            break


@bot.command(name="races", aliases=["listraces"])
async def cmd_races(ctx):
    """Tampilkan daftar ras dengan detail komprehensif dalam format modern."""
    embed = create_menu_embed(
        "Daftar Ras Etherial",
        "Pilih salah satu ras untuk karakter kamu • React untuk navigasi",
        color=COLOR_RACE,
        icon="🧬"
    )
    
    races = race_catalog()
    race_list = list(races.items())
    
    # Buat deskripsi singkat untuk setiap ras
    for race_name, data in race_list:
        stats = data.get("base_stats", {})
        desc = data.get("description", "")
        
        # Format stats display
        stats_str = f"STR:{stats.get('str', 10)} | AGI:{stats.get('agi', 10)} | VIT:{stats.get('vit', 10)}\n"
        stats_str += f"INT:{stats.get('int', 10)} | WIS:{stats.get('wis', 10)} | LUK:{stats.get('luk', 10)}"
        
        trait = data.get("special_trait", "—")
        bonus_text = f"**Trait:** {trait}"
        
        value = f"{desc}\n\n```{stats_str}```\n{bonus_text}"
        add_menu_item(embed, race_name, value, emoji="⚔️", inline=False)
    
    footer = format_menu_footer(extra=f"Total: {len(race_list)} Ras")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !createchar <ras> <nama> untuk membuat karakter")
    await ctx.send(embed=embed)


@bot.command(name="jobs", aliases=["listjobs"])
async def cmd_jobs(ctx):
    """Tampilkan daftar job/class dengan detail komprehensif."""
    embed = create_menu_embed(
        "Daftar Class / Job",
        "Spesialisasi untuk karakter kamu • React untuk navigasi",
        color=COLOR_JOB,
        icon="⚔️"
    )
    
    jobs = job_catalog()
    job_list = list(jobs.items())
    
    for job_name, data in job_list:
        stats = data.get("base_stats", {})
        desc = data.get("description", "")
        
        # Format stats display
        stats_str = f"STR:{stats.get('str', 10)} | AGI:{stats.get('agi', 10)} | VIT:{stats.get('vit', 10)}\n"
        stats_str += f"INT:{stats.get('int', 10)} | WIS:{stats.get('wis', 10)} | LUK:{stats.get('luk', 10)}"
        
        trait = data.get("special_trait", "—")
        level_req = data.get("level_requirement", 0)
        bonus_text = f"**Trait:** {trait} | **Req Lvl:** {level_req}"
        
        value = f"{desc}\n\n```{stats_str}```\n{bonus_text}"
        add_menu_item(embed, job_name, value, emoji="💼", inline=False)
    
    footer = format_menu_footer(extra=f"Total: {len(job_list)} Job")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !changejob <job> di Adventurer Guild untuk mengubah job")
    await ctx.send(embed=embed)


@bot.command(name="createchar")
async def cmd_createchar(ctx, *, query: str = None):
    """Create a character with race and name. Job selection can be done later at the Adventurer Guild."""
    session = await get_session_async(ctx.author.id)
    
    # Check if character already exists (has stats)
    if session.get("base_stats") and session.get("base_stats", {}).get("str", 0) != 10:
        embed = create_embed(
            title="⚠️ Character Already Exists",
            description="You already have a character. Use `!profile` to view it.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return
    
    if not query:
        embed = create_embed(
            title="❌ Character Creation",
            description=f"Format: `{PREFIX}createchar <race> <name>`\nExample: `{PREFIX}createchar Elf Aisha`\n\nUse `{PREFIX}races` to view available races.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    parts = normalize_name(query).split(maxsplit=1)
    if len(parts) < 2:
        embed = create_embed(
            title="❌ Missing Name",
            description=f"Format: `{PREFIX}createchar <race> <name>`\nExample: `{PREFIX}createchar Dwarf Ironforge`",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    race_query = parts[0]
    character_name = parts[1]

    # Find race
    race_key = None
    race_data = None
    for r_key, r_data in RACES.items():
        if r_key.lower() == race_query.lower() or race_query.lower() in r_key.lower():
            race_key = r_key
            race_data = r_data
            break

    if not race_key:
        embed = create_embed(
            title="❌ Race Not Found",
            description=f"'{race_query}' is not a valid race.\nUse `{PREFIX}races` to see available races.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    # Create character stats
    char_stats = stats.create_character_stats(RACES, race_key, "novice", JOBS, level=1)
    
    # Update session with new stats
    session.update(char_stats)
    session["title"] = character_name
    session["race"] = race_key
    session["job"] = "Novice"
    session["created"] = True
    session["location"] = "Kota Utama"
    session["level"] = 1
    session["exp"] = 0
    session["gold"] = 100
    session["hp"] = session["current_hp"]
    session["sp"] = session["current_sp"]
    session["max_hp"] = session["derived_stats"].get("max_hp", 100)
    session["max_sp"] = session["derived_stats"].get("max_sp", 50)
    # Apply random starter kit
    kit, items_added = apply_starter_kit_to_session(session, race_key)
    assign_tier0_skills_for_session(session)

    # Recalculate after starter gear (including backpack) is equipped.
    base = session.get("base_stats", DEFAULT_SESSION.get("base_stats", {}))
    job_bonus = stats.load_job_stats(JOBS, session.get("job", "Novice"))
    combined = stats.combine_base_stats(base, job_bonus)
    equip_bonus = resolve_equipment_bonuses(session)
    session["derived_stats"] = stats.calculate_derived_stats(combined, session.get("level", 1), equipment_bonus=equip_bonus)
    session["max_hp"] = session["derived_stats"].get("max_hp", session.get("max_hp", 100))
    session["max_sp"] = session["derived_stats"].get("max_sp", session.get("max_sp", 50))
    session["hp"] = min(session.get("hp", session["max_hp"]), session["max_hp"])
    session["sp"] = min(session.get("sp", session.get("max_sp", 50)), session["max_sp"])
    
    # Save achievements
    unlock_achievement(session, "awakened")
    await save_session_async(ctx.author.id, session)
    
    # Create response embed
    embed = create_embed(
        title="✅ Character Created!",
        description=f"Welcome, **{character_name}** the **{race_key}**!",
        color=COLOR_SUCCESS
    )
    
    # Add race info
    race_desc = race_data.get("description", "")
    race_trait = race_data.get("special_trait", "")
    embed.add_field(name="🧬 Race", value=f"{race_desc}\n\n**Trait:** {race_trait}", inline=False)
    
    # Add starting stats
    base_stats_str = "\n".join([
        f"STR: {char_stats['base_stats'].get('str', 10)} | AGI: {char_stats['base_stats'].get('agi', 10)} | VIT: {char_stats['base_stats'].get('vit', 10)}",
        f"INT: {char_stats['base_stats'].get('int', 10)} | DEX: {char_stats['base_stats'].get('dex', 10)} | LUK: {char_stats['base_stats'].get('luk', 10)}"
    ])
    embed.add_field(name="📊 Starting Stats", value=base_stats_str, inline=False)
    
    # Add starting stats summary
    derived = char_stats.get("derived_stats", {})
    hp_sp = f"❤️ HP: {session['hp']}/{session['max_hp']}\n💙 MP: {session['sp']}/{session['max_sp']}"
    embed.add_field(name="❤️ Health & Mana", value=hp_sp, inline=False)
    
    # Add starter kit info
    kit_items = "\n".join([f"- {item}" for item in items_added]) if items_added else "None"
    embed.add_field(
        name=f"🎁 Starter Kit: {kit['name']}",
        value=f"{kit['description']}\n\n**Items**:\n{kit_items}",
        inline=False
    )

    race_skill_count = len(session.get("tier0_race_skills", {}))
    job_skill_count = len(current_tier0_job_skills(session))
    embed.add_field(
        name="🧠 Tier-0 Skills",
        value=(
            f"Random Race Skills: **{race_skill_count}**\n"
            f"Random Job Skills: **{job_skill_count}**\n"
            f"Gunakan `{PREFIX}skills` untuk melihat semua skill"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📝 Next Steps",
        value=f"Use `{PREFIX}stats` to view detailed stats\nUse `{PREFIX}profile` to view your profile\nVisit the Adventurer Guild to choose your job!",
        inline=False
    )
    
    await ctx.send(embed=embed)


@bot.command(name="changejob")
@require_channel_config("changejob")
@require_location_config("changejob", ["Adventurer Guild"], "Adventurer Guild")
async def cmd_changejob(ctx, *, job_query: str = None):
    """Change player's job at the Adventurer Guild if requirements met."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    location = session.get("location")
    station = station_for_location(location)
    if station != "Adventurer Guild":
        embed = create_embed(
            title="❌ Cannot Change Job Here",
            description="You must be at the Adventurer Guild to change your job.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    if not job_query:
        embed = create_embed(
            title="❌ Missing Job Name",
            description=f"Usage: `{PREFIX}changejob <job>`\nUse `{PREFIX}jobs` to view available jobs.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    job_name, job_data = find_job(job_query)
    if not job_name:
        embed = create_embed(
            title="❌ Job Not Found",
            description=f"Job '{job_query}' not found. Use `{PREFIX}jobs`.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    # Check level requirement
    req = int(job_data.get("level_requirement", 1)) if isinstance(job_data, dict) else 1
    if session.get("level", 1) < req:
        embed = create_embed(
            title="❌ Level Too Low",
            description=f"{job_name} requires level {req}.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    # Assign job and recalc stats
    session["job"] = job_name
    base = session.get("base_stats", DEFAULT_SESSION.get("base_stats", {}))
    job_bonus = stats.load_job_stats(JOBS, job_name)
    combined = stats.combine_base_stats(base, job_bonus)
    equip_bonus = resolve_equipment_bonuses(session)
    derived = stats.calculate_derived_stats(combined, session.get("level", 1), equipment_bonus=equip_bonus)
    session["base_stats"] = combined
    session["derived_stats"] = derived
    session["max_hp"] = derived.get("max_hp", session.get("max_hp", 100))
    session["max_sp"] = derived.get("max_sp", session.get("max_sp", 50))
    session["hp"] = min(session.get("hp", session["max_hp"]), session["max_hp"])
    session["sp"] = min(session.get("sp", session.get("max_sp", 50)), session["max_sp"])

    by_job = session.setdefault("tier0_job_skills_by_job", {})
    if not isinstance(by_job, dict):
        by_job = {}
        session["tier0_job_skills_by_job"] = by_job
    if job_name not in by_job or not isinstance(by_job.get(job_name), dict) or not by_job.get(job_name):
        by_job[job_name] = random_skill_subset(_build_tier0_skill_pool(job_name, "job"), 1, 3)

    await save_session_async(ctx.author.id, session)

    embed = create_embed(
        title="✅ Job Changed",
        description=f"You are now a **{job_name}**.",
        color=COLOR_SUCCESS
    )
    embed.add_field(name="New Job", value=job_data.get("description", ""), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="profile")
async def cmd_profile(ctx):
    """View your character profile with stats and information."""
    session = await get_session_async(ctx.author.id)
    
    # Check if character is created
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet.\nUse `{PREFIX}createchar <race> <name>` to create one.\nExample: `{PREFIX}createchar Elf Aisha`",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    
    job_name = session.get("job", "Novice")
    race_name = session.get("race", "Unknown")
    level = session.get("level", 1)
    
    embed = create_embed(
        title="👤 Character Profile",
        description=session.get('title', 'Wanderer'),
        color=COLOR_PRIMARY
    )
    
    # Basic Info
    embed.add_field(name="🧬 Race", value=race_name, inline=True)
    embed.add_field(name="⚔️ Job", value=job_name, inline=True)
    embed.add_field(name="📍 Location", value=session.get("location", "Unknown"), inline=True)
    
    # Level and EXP
    exp = session.get("exp", 0)
    next_level_exp = level * 100  # Simple formula
    exp_progress = f"{exp}/{next_level_exp}"
    embed.add_field(name="📊 Level & EXP", value=f"Lv. {level} • EXP: {exp_progress}", inline=False)
    
    # HP and MP
    hp = session.get("hp", session.get("max_hp", 100))
    max_hp = session.get("max_hp", 100)
    sp = session.get("sp", session.get("max_sp", 50))
    max_sp = session.get("max_sp", 50)
    embed.add_field(name="❤️ Health & Mana", value=f"HP: {hp}/{max_hp} • MP: {sp}/{max_sp}", inline=False)
    
    # Gold and Inventory
    gold = session.get("gold", 0)
    inv_count = len(session.get("inventory", []))
    carry_now = current_inventory_weight(session)
    carry_limit = current_weight_limit(session)
    embed.add_field(name="💰 Resources", value=f"Gold: {gold} • Items: {inv_count} • Weight: {carry_now:.2f}/{carry_limit:.2f} kg", inline=False)
    
    # Combat Stats
    derived = session.get("derived_stats", {})
    if derived:
        atk = derived.get("atk", 0)
        matk = derived.get("matk", 0)
        def_stat = derived.get("def", 0)
        mdef = derived.get("mdef", 0)
        crit = derived.get("crit", 0)
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"ATK: {atk} | MATK: {matk}\nDEF: {def_stat} | MDEF: {mdef}\nCRIT: {crit:.1f}%",
            inline=False
        )
    
    # Footer with helpful info
    embed.set_footer(text=f"Use !stats for detailed stat breakdown | Gold: {gold}")
    await ctx.send(embed=embed)


@bot.command(name="statpoints")
async def cmd_statpoints(ctx):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    pts = session.get("stat_points", 0)
    embed = create_embed(
        title="🔢 Unspent Stat Points",
        description=f"You have **{pts}** SP (Stat Points). Use `{PREFIX}alloc <stat> <amount>` to allocate.",
        color=COLOR_INFO
    )
    await ctx.send(embed=embed)


@bot.command(name="alloc")
async def cmd_alloc(ctx, stat: str = None, amount: int = 1):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not stat:
        embed = create_embed(
            title="❌ Missing Stat",
            description=f"Usage: `{PREFIX}alloc <stat> <amount>`\nValid: str, agi, vit, int, dex, luk, tec, men, crt",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    stat = stat.lower()
    valid = {"str", "agi", "vit", "int", "dex", "luk", "tec", "men", "crt"}
    if stat not in valid:
        embed = create_embed(
            title="❌ Invalid Stat",
            description="Valid stats: str, agi, vit, int, dex, luk, tec, men, crt",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    pts = session.get("stat_points", 0)
    if amount <= 0 or amount > pts:
        embed = create_embed(
            title="❌ Invalid Amount",
            description=f"You have {pts} stat point(s). Specify a valid amount.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    base = session.setdefault("base_stats", DEFAULT_SESSION.get("base_stats", {}).copy())
    base[stat] = base.get(stat, 0) + int(amount)
    session["stat_points"] = pts - int(amount)
    # Recalculate derived
    equip_bonus = resolve_equipment_bonuses(session)
    derived = stats.calculate_derived_stats(base, session.get("level", 1), equipment_bonus=equip_bonus)
    session["derived_stats"] = derived
    session["max_hp"] = derived.get("max_hp", session.get("max_hp", 100))
    session["max_sp"] = derived.get("max_sp", session.get("max_sp", 50))
    session["hp"] = min(session.get("hp", session["max_hp"]), session["max_hp"])
    session["sp"] = min(session.get("sp", session.get("max_sp", 50)), session["max_sp"])
    await save_session_async(ctx.author.id, session)

    embed = create_embed(
        title="✅ Stat Allocated",
        description=f"Added **{amount}** to **{stat.upper()}**. Remaining points: {session['stat_points']}",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="stats")
async def cmd_stats(ctx):
    """View detailed character statistics breakdown."""
    session = await get_session_async(ctx.author.id)
    
    # Check if character is created
    race_name = session.get("race", DEFAULT_SESSION["race"])
    if race_name == "Human" and session.get("base_stats", {}).get("str", 0) == 10 and session.get("level", 0) < 1:
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet.\nUse `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    
    base_stats = session.get("base_stats", {})
    derived = session.get("derived_stats", {})
    title = session.get("title", "Wanderer")
    level = session.get("level", 1)
    
    # Page 1: Primary Stats
    embed1 = create_embed(
        title=f"📊 {title}'s Stats (1/3) - Base Stats",
        color=COLOR_INFO
    )
    embed1.add_field(
        name="Primary Stats",
        value=(
            f"**STR:** {base_stats.get('str', 10)}\n"
            f"**AGI:** {base_stats.get('agi', 10)}\n"
            f"**VIT:** {base_stats.get('vit', 10)}\n"
            f"**INT:** {base_stats.get('int', 10)}\n"
            f"**DEX:** {base_stats.get('dex', 10)}\n"
            f"**LUK:** {base_stats.get('luk', 10)}\n"
            f"**TEC:** {base_stats.get('tec', 10)}\n"
            f"**MEN:** {base_stats.get('men', 10)}\n"
            f"**CRT:** {base_stats.get('crt', 10)}"
        ),
        inline=False
    )
    embed1.add_field(
        name="📌 Description",
        value=(
            "STR: Strength - Physical damage and weight capacity\n"
            "AGI: Agility - Attack speed and dodge\n"
            "VIT: Vitality - Max HP and defense\n"
            "INT: Intelligence - Magic damage and MP\n"
            "DEX: Dexterity - Accuracy and ranged damage\n"
            "LUK: Luck - Critical rate and dodge"
        ),
        inline=False
    )
    
    # Page 2: Offensive Stats
    embed2 = create_embed(
        title=f"📊 {title}'s Stats (2/3) - Combat",
        color=COLOR_WARNING
    )
    embed2.add_field(
        name="⚔️ Offensive Stats",
        value=(
            f"**ATK:** {derived.get('atk', 0)}\n"
            f"**MATK:** {derived.get('matk', 0)}\n"
            f"**HIT:** {derived.get('hit', 0)}\n"
            f"**CRIT:** {derived.get('crit', 0):.1f}%\n"
            f"**ASPD:** {derived.get('aspd', 0)}"
        ),
        inline=True
    )
    embed2.add_field(
        name="🛡️ Defensive Stats",
        value=(
            f"**DEF:** {derived.get('def', 0)}\n"
            f"**MDEF:** {derived.get('mdef', 0)}\n"
            f"**FLEE:** {derived.get('flee', 0)}\n"
            f"**P.DODGE:** {derived.get('perfect_dodge', 0)}\n"
            f"**CRIT DEF:** {derived.get('crit_def', 0)}"
        ),
        inline=True
    )
    
    # Page 3: Utility Stats
    embed3 = create_embed(
        title=f"📊 {title}'s Stats (3/3) - Resources & Utility",
        color=COLOR_SUCCESS
    )
    embed3.add_field(
        name="❤️ Health & Mana",
        value=(
            f"**Max HP:** {derived.get('max_hp', 100)}\n"
            f"**Max MP:** {derived.get('max_sp', 50)}\n"
            f"**HP Recovery:** {derived.get('hp_recovery', 0)} per turn\n"
            f"**MP Recovery:** {derived.get('sp_recovery', 0)} per turn"
        ),
        inline=True
    )
    embed3.add_field(
        name="🎒 Utility",
        value=(
            f"**Weight Limit:** {derived.get('weight_limit', 500)} kg\n"
            f"**Current Weight:** {current_inventory_weight(session):.2f} kg\n"
            f"**Success Rate:** {derived.get('success_rate', 50):.0f}%\n"
            f"**Status Res.:** +{derived.get('status_resistance', 0)}\n"
            f"**VCT Reduction:** {derived.get('vct_reduction', 0):.1f}%"
        ),
        inline=True
    )
    
    # Send paginated embeds
    embeds = [embed1, embed2, embed3]
    current_page = 0
    
    msg = await ctx.send(embed=embeds[current_page])
    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")
    await msg.add_reaction("🏠")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "🏠"] and reaction.message.id == msg.id
    
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            
            if str(reaction.emoji) == "⬅️":
                current_page = (current_page - 1) % len(embeds)
            elif str(reaction.emoji) == "➡️":
                current_page = (current_page + 1) % len(embeds)
            elif str(reaction.emoji) == "🏠":
                current_page = 0
            
            await msg.edit(embed=embeds[current_page])
            await reaction.remove(user)
        except asyncio.TimeoutError:
            break


@bot.command(name="party")
async def cmd_party(ctx, action: str = None, *, detail: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    world_state = await get_world_state_async()
    party = get_channel_party(world_state, ctx.channel.id)
    action = normalize_name(action or "info").lower()

    if action in {"info", "show", "status"}:
        embed = party_summary_embed(party)
        await ctx.send(embed=embed)
        return

    if action == "create":
        if party:
            await ctx.send("Sudah ada party di channel ini. Pakai `!party info` untuk melihatnya.")
            return
        party = {
            "name": detail or f"Party-{ctx.channel.id}",
            "leader_id": str(ctx.author.id),
            "leader_name": ctx.author.display_name,
            "created_at": time.time(),
            "members": [
                {"id": str(ctx.author.id), "name": ctx.author.display_name, "joined_at": time.time(), "role": "leader"}
            ],
        }
        set_channel_party(world_state, ctx.channel.id, party)
        session = await get_session_async(ctx.author.id)
        unlock_achievement(session, "first_party")
        await save_session_async(ctx.author.id, session)
        await save_world_state_async(world_state)
        await ctx.send(f"Party **{party['name']}** dibuat. Kamu sekarang leader party itu.")
        return

    if action == "join":
        if not party:
            await ctx.send("Belum ada party di channel ini. Pakai `!party create [nama]` dulu.")
            return
        member_ids = party_member_ids(party)
        if str(ctx.author.id) in member_ids:
            await ctx.send("Kamu sudah ada di party ini.")
            return
        party.setdefault("members", []).append({"id": str(ctx.author.id), "name": ctx.author.display_name, "joined_at": time.time(), "role": "member"})
        set_channel_party(world_state, ctx.channel.id, party)
        await save_world_state_async(world_state)
        await ctx.send(f"{ctx.author.display_name} bergabung ke party **{party.get('name', 'Etherial Party')}**.")
        return

    if action == "leave":
        if not party:
            await ctx.send("Tidak ada party untuk ditinggalkan.")
            return
        members = party_member_entries(party)
        new_members = [member for member in members if str(member.get("id")) != str(ctx.author.id)]
        if len(new_members) == len(members):
            await ctx.send("Kamu tidak ada di party itu.")
            return
        if not new_members:
            world_party_map(world_state).pop(party_key_for_channel(ctx.channel.id), None)
            await save_world_state_async(world_state)
            await ctx.send("Party bubar karena semua anggota keluar.")
            return
        party["members"] = new_members
        if str(party.get("leader_id")) == str(ctx.author.id):
            leader = new_members[0]
            party["leader_id"] = leader.get("id")
            party["leader_name"] = leader.get("name", "Unknown")
            leader["role"] = "leader"
        set_channel_party(world_state, ctx.channel.id, party)
        await save_world_state_async(world_state)
        await ctx.send(f"{ctx.author.display_name} keluar dari party **{party.get('name', 'Etherial Party')}**.")
        return

    if action == "disband":
        if not party:
            await ctx.send("Tidak ada party untuk dibubarkan.")
            return
        if str(party.get("leader_id")) != str(ctx.author.id):
            await ctx.send("Hanya leader party yang bisa membubarkan party.")
            return
        world_party_map(world_state).pop(party_key_for_channel(ctx.channel.id), None)
        await save_world_state_async(world_state)
        await ctx.send(f"Party **{party.get('name', 'Etherial Party')}** dibubarkan.")
        return

    await ctx.send(f"Format party: `{PREFIX}party <create|join|leave|info|disband> [nama]`")


@bot.command(name="companions")
async def cmd_companions(ctx):
    """Tampilkan companion yang dimiliki dengan detail format kartu."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "Companion",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="🐱"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        await ctx.send(embed=embed)
        return
    
    owned = session.get("companions", [])
    embed = create_menu_embed(
        "Companion",
        f"Kamu memiliki {len(owned)}/3 companion",
        color=COLOR_COMPANION,
        icon="🐱"
    )
    
    if not owned:
        embed.description = "Kamu belum punya companion 🥺"
        embed.add_field(
            name="Cara Mendapat Companion",
            value=f"Cari companion di berbagai lokasi menggunakan `{PREFIX}recruit <nama>`\nContoh: `{PREFIX}recruit Mage Cat`",
            inline=False
        )
    else:
        for i, companion in enumerate(owned, 1):
            companion_name = companion if isinstance(companion, str) else companion.get("name")
            _, data = find_companion(companion_name)
            if data:
                role = data.get('role', 'Companion')
                flavor = data.get('flavor', 'Companion misterius')
                
                comp_detail = f"**Role:** {role}\n"
                comp_detail += f"**Type:** {data.get('type', 'Unknown')}\n"
                comp_detail += f"**Flavor:** {flavor}"
                
                add_menu_item(embed, f"{i}. {companion_name}", comp_detail, emoji="✨", inline=False)
    
    recruit_tip = f"💡 Gunakan `{PREFIX}recruit <nama>` untuk merekrut companion baru"
    footer = format_menu_footer(extra=f"Slot: {len(owned)}/3")
    embed.set_footer(text=f"{footer}\n{recruit_tip}")
    await ctx.send(embed=embed)


@bot.command(name="recruit")
async def cmd_recruit(ctx, *, companion_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not companion_name:
        await ctx.send(f"Format: `{PREFIX}recruit <nama_companion>`")
        return

    canonical, data = find_companion(companion_name)
    if not canonical:
        await ctx.send("Companion tidak ditemukan. Coba nama lain atau cek daftar nanti saat kamu sudah punya beberapa.")
        return

    owned_names = [entry if isinstance(entry, str) else entry.get("name") for entry in session.get("companions", [])]
    if canonical in owned_names:
        await ctx.send("Companion ini sudah ikut bersamamu.")
        return

    if len(owned_names) >= 3:
        await ctx.send("Batas companion aktif sementara adalah 3.")
        return

    session.setdefault("companions", []).append({
        "name": canonical,
        "role": data.get("role", "Companion"),
        "joined_at": time.time(),
        "location": session.get("location", DEFAULT_SESSION["location"]),
    })
    session["exp"] += int(data.get("bonuses", {}).get("exp", 0))
    unlock_achievement(session, "first_companion")
    await apply_level_up_if_needed(session)
    await save_session_async(ctx.author.id, session)
    await ctx.send(f"Kamu merekrut **{canonical}** sebagai companion. {data.get('flavor', '')}")


@bot.command(name="dismiss")
async def cmd_dismiss(ctx, *, companion_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not companion_name:
        await ctx.send(f"Format: `{PREFIX}dismiss <nama_companion>`")
        return

    canonical, _ = find_companion(companion_name)
    if not canonical:
        await ctx.send("Companion tidak ditemukan.")
        return

    companions = session.get("companions", [])
    updated = [entry for entry in companions if (entry if isinstance(entry, str) else entry.get("name")) != canonical]
    if len(updated) == len(companions):
        await ctx.send("Companion itu tidak sedang menemanimu.")
        return

    session["companions"] = updated
    await save_session_async(ctx.author.id, session)
    await ctx.send(f"Companion **{canonical}** kembali ke jalannya sendiri.")


@bot.command(name="story", aliases=["legend", "chronicle"])
async def cmd_story(ctx):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    world_state = await get_world_state_async()
    event = choose_story_event(session, world_state)
    party = get_channel_party(world_state, ctx.channel.id)
    lines = story_event_text(session, world_state, event, party)
    apply_story_event_reward(session, event)
    unlock_achievement(session, "first_story")
    adjust_reputation(session, story_event_faction(session, event), 2)
    world_state.setdefault("chronicle", []).append({
        "title": event.get("title", event.get("id", "story")),
        "location": session.get("location", DEFAULT_SESSION["location"]),
        "user": str(ctx.author.id),
        "time": time.time(),
    })
    await apply_level_up_if_needed(session)
    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    reward = event.get("reward", {})
    
    embed = create_embed(
        title=f"📖 {event.get('title', 'Story Event')}",
        color=COLOR_INFO
    )
    embed.description = "\n".join(lines)
    reward_text = f"Reward: +{reward.get('exp', 0)} EXP, +{reward.get('gold', 0)} Gold"
    embed.add_field(name="🎁 Reward", value=reward_text, inline=False)
    embed.set_footer(text=f"Location: {session.get('location', 'Unknown')}")
    await ctx.send(embed=embed)


@bot.command(name="reputation", aliases=["rep"])
async def cmd_reputation(ctx, *, faction: str = None):
    session = await get_session_async(ctx.author.id)
    if faction:
        faction_name = normalize_name(faction)
        if faction_name not in reputation_defaults():
            embed = create_embed(
                title="Faction Tidak Dikenal",
                description=f"Gunakan {PREFIX}reputation tanpa argumen untuk daftar lengkap.",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        rep_lines = reputation_summary_lines(session, faction_name)
        embed = create_embed(
            title=f"Reputasi {faction_name}",
            color=COLOR_PRIMARY
        )
        for line in rep_lines:
            if line:
                if embed.description:
                    embed.description += "\n" + line
                else:
                    embed.description = line
        await ctx.send(embed=embed)
        return
    embed = create_embed(
        title="Reputasi Semua Faction",
        color=COLOR_PRIMARY
    )
    for line in reputation_summary_lines(session):
        if line:
            if embed.description:
                embed.description += "\n" + line
            else:
                embed.description = line
    await ctx.send(embed=embed)


@bot.command(name="achievements", aliases=["milestones", "badges"])
async def cmd_achievements(ctx):
    """Tampilkan achievement yang telah dibuka dengan format terstruktur."""
    session = await get_session_async(ctx.author.id)
    unlocked = unlocked_achievement_ids(session)
    catalog = achievement_catalog()
    
    embed = create_menu_embed(
        "Achievements",
        f"Kamu telah membuka {len(unlocked)}/{len(catalog)} achievement",
        color=COLOR_WARNING,
        icon="🌟"
    )
    
    if not unlocked:
        embed.add_field(
            name="🔓 Mulai Journey",
            value="Tidak ada achievement yang terbuka. Mulai bermain untuk membuka!",
            inline=False
        )
        locked_preview = list(catalog.items())[:3]
        for achievement_id, data in locked_preview:
            add_menu_item(
                embed,
                f"🔒 {data['title']}",
                f"```{data['description']}```",
                emoji="",
                inline=False
            )
    else:
        for achievement_id in unlocked:
            data = catalog.get(achievement_id)
            if data:
                add_menu_item(
                    embed,
                    f"{data['title']}",
                    data['description'],
                    emoji="✅",
                    inline=False
                )
    
    footer = format_menu_footer(extra=f"Unlocked: {len(unlocked)}/{len(catalog)}")
    embed.set_footer(text=f"{footer}\n💡 Tingkatkan level dan selesaikan quest untuk membuka lebih banyak")
    await ctx.send(embed=embed)


@bot.command(name="racepowers")
async def cmd_racepowers(ctx):
    """Tampilkan race power/ability dengan format terstruktur."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "Race Power",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="🔥"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        await ctx.send(embed=embed)
        return
    
    race_name = session.get('race', 'Unknown')
    abilities = current_race_abilities(session)
    
    if not abilities:
        embed = create_menu_embed(
            f"Race Power - {race_name}",
            "Ras ini belum memiliki ability terdaftar",
            color=COLOR_RACE,
            icon="🔥"
        )
        embed.set_footer(text="Ganti ras untuk mendapat race power baru")
        await ctx.send(embed=embed)
        return

    embed = create_menu_embed(
        f"Race Power - {race_name}",
        f"Kamu memiliki {len(abilities)} ability tersedia",
        color=COLOR_RACE,
        icon="🔥"
    )
    
    for ability_key, ability_data in abilities.items():
        ability_name = ability_data.get('name', ability_key)
        desc = ability_data.get('description', 'Ability rahasia')
        cooldown = ability_data.get('cooldown', 0)
        power = ability_data.get('power', 0)
        
        details = f"{desc}\n"
        details += f"**Power:** {power} | **Cooldown:** {cooldown}s"
        
        current_cd = get_race_power_cooldown(session, ability_key)
        if current_cd > 0:
            details += f"\n⏱️ **Cooldown aktif:** {current_cd}s"
        
        add_menu_item(embed, ability_name, details, emoji="⚡", inline=False)
    
    footer = format_menu_footer(extra=f"Total Abilities: {len(abilities)}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !racepower <nama> untuk menggunakan ability")
    await ctx.send(embed=embed)


@bot.command(name="racepower")
async def cmd_racepower(ctx, *, ability_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not ability_name:
        await ctx.send(f"Format: `{PREFIX}racepower <nama_ability>`")
        return

    ability_key, ability_data = race_ability_lookup(session, ability_name)
    if not ability_key:
        await ctx.send("Ability ras tidak ditemukan. Cek `!racepowers`.")
        return

    if get_race_power_cooldown(session, ability_key) > 0:
        await ctx.send(f"Ability **{ability_data.get('name', ability_key)}** masih cooldown {get_race_power_cooldown(session, ability_key)} detik.")
        return

    world_state = await get_world_state_async()
    result_lines = apply_race_ability(session, world_state, ability_key, ability_data)
    set_race_power_cooldown(session, ability_key, int(ability_data.get("cooldown", 0)))
    await apply_level_up_if_needed(session)
    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    await ctx.send("\n".join(result_lines))


@bot.command(name="scene")
async def cmd_scene(ctx, *, action_text: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    world_state = await get_world_state_async()
    if not action_text:
        embed = create_embed(
            title="🎭 Scene Actions",
            color=COLOR_PRIMARY
        )
        actions_text = ""
        for action_key, action_data in ROLEPLAY_ACTIONS.items():
            actions_text += f"**{action_data['name']}** - {action_data['description']}\n"
        embed.add_field(name="Available Actions", value=actions_text, inline=False)
        embed.add_field(name="📝 How to Use", value=f"Use `{PREFIX}scene <action>` to perform a roleplay action.", inline=False)
        await ctx.send(embed=embed)
        return

    lookup_key, action_data = roleplay_action_lookup(action_text)
    freeform = action_text if not lookup_key else ""
    if not action_data:
        action_data = {
            "name": "Custom Scene",
            "cooldown": 0,
            "description": "Free roleplay scene.",
            "effect": "social",
        }

    result_lines = apply_roleplay_action(session, world_state, lookup_key or "custom", action_data, freeform)
    await apply_level_up_if_needed(session)
    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    
    embed = create_embed(
        title="🎭 Scene",
        color=COLOR_INFO
    )
    embed.description = "\n".join(result_lines)
    await ctx.send(embed=embed)


@bot.command(name="roleplay")
async def cmd_roleplay(ctx, *, action_text: str = None):
    await cmd_scene(ctx, action_text=action_text)


@bot.command(name="skills")
async def cmd_skills(ctx):
    """Tampilkan skill job kamu dengan detail terstruktur."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "Skill Job",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="⚡"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        embed.set_footer(text="Buat karakter dulu sebelum melihat skill")
        await ctx.send(embed=embed)
        return
    
    skills = current_battle_skills(session)
    job_name = session.get('job', 'Jobless')
    
    if not skills:
        embed = create_menu_embed(
            f"Skill - {job_name}",
            "Job ini belum memiliki skill terdaftar",
            color=COLOR_SKILL,
            icon="⚡"
        )
        embed.set_footer(text="Ganti job di Adventurer Guild untuk mendapat skill baru")
        await ctx.send(embed=embed)
        return
    
    embed = create_menu_embed(
        f"Skill - {job_name}",
        f"Kamu memiliki {len(skills)} skill tersedia (job + race/job tier-0)",
        color=COLOR_SKILL,
        icon="⚡"
    )
    
    for skill_key, skill_data in skills.items():
        skill_name = skill_data.get('name', skill_key)
        desc = skill_data.get('description', 'Skill rahasia')
        
        # Format skill details
        mp_cost = skill_data.get('mp_cost', skill_data.get('sp_cost', 0))
        cooldown = skill_data.get('cooldown', 0)
        damage = skill_data.get('damage', (0, 0))
        dmg_text = f"{damage[0]}-{damage[1]}" if isinstance(damage, (list, tuple)) and len(damage) == 2 else "0"
        type_damage = skill_data.get('type_damage', 'single_target')
        type_skill = skill_data.get('type_skill', skill_data.get('type', 'Physical'))
        element = skill_data.get('element', None)
        cast_time = skill_data.get('cast_time', 0)
        duration = skill_data.get('duration', 0)
        origin = skill_data.get('origin', 'job').capitalize()

        details = f"**Source:** {origin} | **Type:** {type_skill}\n"
        details += f"**Damage Type:** {type_damage} | **Damage:** {dmg_text}\n"
        details += f"**MP Cost:** {mp_cost} | **Cooldown:** {cooldown} turn\n"
        if element:
            details += f"**Element:** {element}\n"
        if cast_time:
            details += f"**Cast Time:** {cast_time}s\n"
        if duration:
            details += f"**Duration:** {duration} turn\n"
        details += desc
        
        add_menu_item(embed, skill_name, details, emoji="✨", inline=False)
    
    footer = format_menu_footer(extra=f"Total Skills: {len(skills)}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !skill <nama> untuk menggunakan skill")
    await ctx.send(embed=embed)


@bot.command(name="skill")
async def cmd_skill(ctx, *, skill_name: str = None):
    session = await get_session_async(ctx.author.id)
    battle = session.get("battle")
    if not battle:
        embed = create_embed(
            title="❌ Not in Battle",
            description="Battle skills can only be used during combat.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not skill_name:
        embed = create_embed(
            title="❌ Missing Skill Name",
            description=f"Usage: `{PREFIX}skill <skill_name>`",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    skill_key, skill_data = skill_lookup(session, skill_name)
    if not skill_key:
        embed = create_embed(
            title="❌ Skill Not Found",
            description=f"Check available skills with `{PREFIX}skills`.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    reduce_skill_cooldowns(session)
    cooldown = get_skill_cooldown(session, skill_key)
    if cooldown > 0:
        embed = create_embed(
            title="⏳ Skill on Cooldown",
            description=f"**{skill_data.get('name', skill_key)}** is on cooldown for {cooldown} turns.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    mp_cost = int(skill_data.get("mp_cost", skill_data.get("sp_cost", 0)))
    current_mp = int(session.get("sp", 0))
    if current_mp < mp_cost:
        embed = create_embed(
            title="❌ MP Tidak Cukup",
            description=f"Butuh {mp_cost} MP, MP kamu saat ini {current_mp}.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    world_state = await get_world_state_async()
    refresh_battle_context(session, world_state, ctx.channel.id)
    session["sp"] = max(0, current_mp - mp_cost)
    result_lines = apply_skill_effect(session, battle, skill_key, skill_data)
    result_lines.append(f"Biaya skill: {mp_cost} MP. Sisa MP: {session.get('sp', 0)}")
    set_skill_cooldown(session, skill_key, int(skill_data.get("cooldown", 0)))
    await battle_round_after_action(ctx, session, battle, world_state, result_lines)


@bot.command(name="world")
async def cmd_world(ctx):
    world_state = await get_world_state_async()
    embed = create_embed(
        title="🌍 World State - Etherial",
        description=event_flavor(world_state),
        color=COLOR_PRIMARY
    )
    if world_state.get("history"):
        history = ", ".join(world_state.get("history", [])[-5:])
        embed.add_field(name="📜 Event History", value=history, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="event")
async def cmd_event(ctx):
    await cmd_world(ctx)


@bot.command(name="map")
async def cmd_map(ctx):
    """Tampilkan peta Etherial dengan region dan lokasi."""
    embed = create_menu_embed(
        "Map of Etherial",
        "Jelajahi berbagai region dalam dunia Etherial",
        color=COLOR_WORLD,
        icon="🗺️"
    )
    
    for region, locs in MAP.get("Etherial", {}).items():
        region_emoji = {"Temperate": "🌲", "Tropical": "🏝️", "Arctic": "❄️", "Magiclands": "✨", "Underground": "⛏️"}.get(region, "📍")
        locations_text = f"{region_emoji} **{region}**\n"
        locations_text += ", ".join(f"`{loc}`" for loc in locs)
        
        embed.add_field(
            name=f"{region_emoji} {region} ({len(locs)})",
            value=locations_text,
            inline=False
        )
    
    footer = format_menu_footer(extra=f"Total Locations: {sum(len(locs) for locs in MAP.get('Etherial', {}).values())}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !travel <lokasi> untuk berpindah")
    await ctx.send(embed=embed)


@bot.command(name="travel")
async def cmd_travel(ctx, *, location: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not location:
        embed = create_embed(
            title="❌ Missing Location",
            description=f"Your current location: **{session['location']}**\nUse `{PREFIX}map` to view available locations.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    destination = find_location(location)
    if not destination:
        embed = create_embed(
            title="❌ Location Not Found",
            description=f"Use `{PREFIX}map` to view available locations.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    world_state = await get_world_state_async()
    world_state = await tick_world_turn(world_state, "travel")
    session["location"] = destination
    session["last_encounter"] = None
    await refresh_active_quests_from_event(session, "visit", destination)
    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    region = LOCATION_TO_REGION.get(destination, "mysterious region")
    event_text = event_flavor(world_state)
    
    embed = create_embed(
        title=f"🚶 Traveled to {destination}",
        description=f"You arrive at **{destination}** in {region}. The air, scent, and atmosphere feel different here.\n\n{event_text}",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="explore")
async def cmd_explore(ctx, *, location: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    world_state = await get_world_state_async()
    world_state = await tick_world_turn(world_state, "explore")
    if location:
        destination = find_location(location)
        if not destination:
            embed = create_embed(
                title="❌ Location Not Found",
                description=f"Use `{PREFIX}map` to view available locations.",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        session["location"] = destination
    else:
        destination = session["location"]

    roll = random.randint(1, 100) - max(0, event_modifier(world_state, "encounter_bonus", 0))
    region = LOCATION_TO_REGION.get(destination, "Unknown Region")

    if roll <= 45:
        monster = random_monster_for_location(destination)
        if monster:
            session["last_encounter"] = monster
            session["battle"] = None
            await save_session_async(ctx.author.id, session)
            await save_world_state_async(world_state)
            embed = create_embed(
                title=f"⚠️ {monster['name']} Appeared!",
                description=f"While exploring {destination}, **{monster['name']}** emerges from the shadows.\nUse `{PREFIX}startbattle` to fight.",
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
            return

    if roll <= 75:
        item_name, item_data = random.choice(list(item_catalog().items())) if item_catalog() else ("Health Potion", {"name": "Health Potion"})
        added = add_item(session, item_name)
        if added <= 0:
            await save_session_async(ctx.author.id, session)
            await save_world_state_async(world_state)
            embed = create_embed(
                title="⚖️ Loot Tertinggal",
                description=(
                    f"Kamu menemukan **{item_name}**, tapi inventory sudah melewati batas berat.\n"
                    f"Carry weight: {current_inventory_weight(session):.2f}/{current_weight_limit(session):.2f} kg"
                ),
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
            return
        await refresh_active_quests_from_event(session, "collect", item_name)
        await save_session_async(ctx.author.id, session)
        await save_world_state_async(world_state)
        flavor = item_data.get("description", "") if isinstance(item_data, dict) else ""
        extra_loot_note = ""
        if event_modifier(world_state, "loot_bonus", 0) > 0 and random.random() < 0.35:
            extra_item = random.choice(["Iron Ore", "Moon Salt", "Spirit Herb"])
            extra_added = add_item(session, extra_item)
            await save_session_async(ctx.author.id, session)
            if extra_added > 0:
                extra_loot_note = f"\nBonus: You also found **{extra_item}** from world anomaly!"
            else:
                extra_loot_note = "\nBonus loot tidak bisa dibawa karena weight limit penuh."
        
        embed = create_embed(
            title=f"🎁 Found {item_name}",
            description=f"{flavor}{extra_loot_note}",
            color=COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        return

    if roll <= 90 and destination in MAIN_SERVICE_LOCATIONS:
        await save_session_async(ctx.author.id, session)
        await save_world_state_async(world_state)
        embed = create_embed(
            title=f"👥 Arrived at {destination}",
            description="\n".join(receptionist_lines(destination)),
            color=COLOR_INFO
        )
        await ctx.send(embed=embed)
        return

    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    await ctx.send(
        f"Kamu menjelajahi {destination} di {region}. Angin, suara, dan suasana sekitar membangun momen roleplay yang tenang namun penuh misteri.\n{event_flavor(world_state)}"
    )


@bot.command(name="cityhall", aliases=["receptionist", "recepsionist"])
@require_channel_config("receptionist")
@require_location_config("cityhall", ["Kota Utama"], "Kota Utama")
async def cmd_cityhall(ctx):
    """Tampilkan layanan Kota Utama."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "City Hall",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="🏛️"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        await ctx.send(embed=embed)
        return

    location = session.get("location", "Kota Utama")
    npc_name = MAIN_SERVICE_LOCATIONS.get(location, "City Clerk")
    lines = location_service_lines(location)
    embed = create_menu_embed(
        f"City Hall - {location}",
        "\n".join(lines),
        color=COLOR_INFO,
        icon="🏛️"
    )
    embed.add_field(name="NPC", value=npc_name, inline=True)
    embed.add_field(
        name="Layanan Kota",
        value=(
            f"`{PREFIX}map`\n"
            f"`{PREFIX}world`\n"
            f"`{PREFIX}help`\n"
            f"`{PREFIX}travel <lokasi>`\n"
            f"`{PREFIX}rest`"
        ),
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command(name="guild", aliases=["adventurerguild"])
@require_channel_config("questboard")
@require_location_config("guild", ["Adventurer Guild"], "Adventurer Guild")
async def cmd_guild(ctx):
    """Tampilkan layanan Adventurer Guild dan registrasi quest."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "Adventurer Guild",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="📋"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        await ctx.send(embed=embed)
        return

    world_state = await get_world_state_async()
    lines = location_service_lines(session["location"])
    offers = generate_quest_offers(session["location"], world_state)
    session["quest_offers"] = offers

    is_first_visit = not guild_registered(session)
    if is_first_visit:
        session["registered_at_guild"] = True
        session["registered_at_receptionist"] = True

    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)

    location = session.get("location", "Adventurer Guild")
    welcome_desc = "\n".join(lines)
    if is_first_visit:
        welcome_desc += f"\n\n✅ **Selamat datang!** Kamu sekarang terdaftar sebagai petualang di {location}."

    embed = create_menu_embed(
        f"Guild Board - {location}",
        welcome_desc,
        color=COLOR_QUEST,
        icon="🛡️"
    )
    status_text = "✅ Sudah Terdaftar - Kamu dapat menerima quest" if guild_registered(session) else "❌ Belum Terdaftar"
    embed.add_field(name="📌 Status Registrasi", value=status_text, inline=False)

    quests_field = ""
    for index, quest in enumerate(offers, start=1):
        quests_field += f"**{index}**. {quest_display_line(quest)}\n"

    embed.add_field(
        name="🎯 Available Quests",
        value=quests_field if quests_field else "Tidak ada quest tersedia",
        inline=False
    )
    embed.add_field(name="🏷️ Guild Services", value=f"`{PREFIX}questboard` • `{PREFIX}changejob` • `{PREFIX}acceptquest <nomor>`", inline=False)
    embed.add_field(name="🌍 World State", value=event_flavor(world_state), inline=False)
    footer = format_menu_footer(extra=f"Quests: {len(offers)}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !acceptquest <nomor> untuk menerima quest")
    await ctx.send(embed=embed)


@bot.command(name="blacksmith", aliases=["smith"])
@require_location_config("blacksmith", ["BlackSmith"], "BlackSmith")
async def cmd_blacksmith(ctx):
    session = await get_session_async(ctx.author.id)
    location = session.get("location", "BlackSmith")
    lines = location_service_lines(location)
    embed = create_menu_embed(
        f"BlackSmith - {location}",
        "\n".join(lines),
        color=COLOR_ITEM,
        icon="⚒️"
    )
    embed.add_field(name="NPC", value=MAIN_SERVICE_LOCATIONS.get(location, "Blacksmith"), inline=True)
    embed.add_field(name="Layanan", value=f"`{PREFIX}upgrade <item>`\n`{PREFIX}shop`\nWeapon dan armor di sini lebih kuat setelah upgrade.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="alchemist")
@require_location_config("alchemist", ["Alchemist"], "Alchemist")
async def cmd_alchemist(ctx):
    session = await get_session_async(ctx.author.id)
    location = session.get("location", "Alchemist")
    lines = location_service_lines(location)
    embed = create_menu_embed(
        f"Alchemist - {location}",
        "\n".join(lines),
        color=COLOR_SKILL,
        icon="⚗️"
    )
    embed.add_field(name="NPC", value=MAIN_SERVICE_LOCATIONS.get(location, "Alchemist"), inline=True)
    embed.add_field(name="Layanan", value=f"`{PREFIX}upgrade <item>`\n`{PREFIX}shop`\nTrinket upgrade dilakukan di sini.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="tavern", aliases=["kedai_petualang"])
@require_location_config("tavern", ["Kedai Petualang"], "Kedai Petualang")
async def cmd_tavern(ctx):
    session = await get_session_async(ctx.author.id)
    location = session.get("location", "Kedai Petualang")
    lines = location_service_lines(location)
    embed = create_menu_embed(
        f"Tavern - {location}",
        "\n".join(lines),
        color=COLOR_COMPANION,
        icon="🍺"
    )
    embed.add_field(name="NPC", value=MAIN_SERVICE_LOCATIONS.get(location, "Tavern Keeper"), inline=True)
    embed.add_field(name="Layanan", value=f"`{PREFIX}rest`\n`{PREFIX}companions`\n`{PREFIX}recruit <nama>`\n`{PREFIX}shop`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="frontier", aliases=["kedai_perbatasan"])
@require_location_config("frontier", ["Kedai Perbatasan"], "Kedai Perbatasan")
async def cmd_frontier(ctx):
    session = await get_session_async(ctx.author.id)
    location = session.get("location", "Kedai Perbatasan")
    lines = location_service_lines(location)
    embed = create_menu_embed(
        f"Frontier Post - {location}",
        "\n".join(lines),
        color=COLOR_WARNING,
        icon="🧭"
    )
    embed.add_field(name="NPC", value=MAIN_SERVICE_LOCATIONS.get(location, "Frontier Clerk"), inline=True)
    embed.add_field(name="Layanan", value=f"`{PREFIX}travel <lokasi>`\n`{PREFIX}explore`\n`{PREFIX}shop`\nPerbatasan ini cocok untuk persiapan perjalanan.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="questboard")
@require_channel_config("questboard")
@require_location_config("questboard", MAIN_SERVICE_LOCATIONS.keys(), "lokasi receptionist")
async def cmd_questboard(ctx):
    """View available quests. Requires prior registration at receptionist."""
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_menu_embed(
            "Quest Board",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="📋"
        )
        embed.add_field(name="Error", value=f"Gunakan `{PREFIX}createchar <ras> <nama>` untuk membuat karakter terlebih dahulu", inline=False)
        await ctx.send(embed=embed)
        return
    
    if not guild_registered(session):
        embed = create_menu_embed(
            "⚠️ Belum Terdaftar",
            "Kamu belum terdaftar di Adventurer Guild",
            color=COLOR_WARNING,
            icon="⚠️"
        )
        embed.add_field(
            name="Langkah Pertama",
            value=f"Kunjungi guild untuk mendaftar.\nGunakan perintah `!guild` untuk memulai.",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    await cmd_guild(ctx)


@bot.command(name="setcommandchannel")
@commands.has_permissions(administrator=True)
async def cmd_setcommandchannel(ctx, command_key: str = None, channel_ref: str = None):
    """Admin: add a channel (name or id or mention) to a command's allowed list.

    Usage: `!setcommandchannel changejob #adventurer-guild` or `!setcommandchannel changejob 123456789012345678`
    """
    if not command_key or not channel_ref:
        await ctx.send("Usage: !setcommandchannel <command> <#channel|channel_name|channel_id>")
        return
    mapping = load_command_channels() or {}
    allowed = resolve_allowed_entries(mapping.get(command_key))
    # normalize input
    entry = channel_ref.strip()
    # Append if not present
    if entry in allowed:
        await ctx.send(f"Entry already present for `{command_key}`: {entry}")
        return
    allowed.append(entry)
    mapping[command_key] = allowed
    if save_command_channels(mapping):
        await ctx.send(f"✅ Updated allowed channels for `{command_key}`: {', '.join(allowed)}")
    else:
        await ctx.send("❌ Failed to save config. Check filesystem permissions.")


@bot.command(name="removecommandchannel")
@commands.has_permissions(administrator=True)
async def cmd_removecommandchannel(ctx, command_key: str = None, channel_ref: str = None):
    """Admin: remove a channel entry from a command's allowed list."""
    if not command_key or not channel_ref:
        await ctx.send("Usage: !removecommandchannel <command> <#channel|channel_name|channel_id>")
        return
    mapping = load_command_channels() or {}
    allowed = resolve_allowed_entries(mapping.get(command_key))
    entry = channel_ref.strip()
    if entry not in allowed:
        await ctx.send(f"Entry not found for `{command_key}`: {entry}")
        return
    allowed = [a for a in allowed if a != entry]
    mapping[command_key] = allowed
    if save_command_channels(mapping):
        await ctx.send(f"✅ Removed {entry} from `{command_key}` allowed list")
    else:
        await ctx.send("❌ Failed to save config. Check filesystem permissions.")


@bot.command(name="listcommandchannels")
@commands.has_permissions(administrator=True)
async def cmd_listcommandchannels(ctx):
    mapping = load_command_channels() or {}
    if not mapping:
        await ctx.send("No command-channel mappings configured.")
        return
    lines = []
    for k, v in mapping.items():
        lines.append(f"`{k}`: {', '.join(map(str, resolve_allowed_entries(v)))}")
    embed = create_menu_embed("Command Channel Mappings", "Current mappings", color=COLOR_INFO, icon="🔧")
    embed.add_field(name="Mappings", value="\n".join(lines), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="dbstatus")
@commands.has_permissions(administrator=True)
async def cmd_dbstatus(ctx):
    """Check database and Firestore status."""
    fs_status = db.get_firestore_status()
    
    status_text = "✅ **Firestore Connected**" if fs_status["enabled"] else "❌ **Firestore Disabled** (using in-memory storage)"
    
    details = f"""
**Connection Details:**
• Firestore Enabled: {fs_status['enabled']}
• Sessions Collection: {fs_status['sessions_collection']}
• World State Doc: {fs_status['world_doc']}
• App Initialized: {fs_status['app_initialized']}

**Fallback Storage:**
• Sessions in memory: {fs_status['fallback_sessions_count']}
• World state cached: {fs_status['fallback_world_state']}
""".strip()
    
    embed = create_menu_embed("Database Status", status_text, color=COLOR_SUCCESS if fs_status["enabled"] else COLOR_WARNING, icon="💾")
    embed.add_field(name="Details", value=details, inline=False)
    
    if not fs_status["enabled"]:
        embed.add_field(
            name="⚠️ Warning",
            value="Firestore is not connected. Data will be stored in memory only and will be lost on bot restart.",
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command(name="acceptquest")
@require_channel_config("acceptquest")
@require_location_config("acceptquest", MAIN_SERVICE_LOCATIONS.keys(), "lokasi receptionist")
async def cmd_acceptquest(ctx, *, quest_ref: str = None):
    session = await get_session_async(ctx.author.id)
    if not session.get("created", False):
        embed = create_embed(
            title="❌ No Character",
            description=f"You haven't created a character yet. Use `{PREFIX}createchar <race> <name>` to create one.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not session.get("quest_offers"):
        session["quest_offers"] = generate_quest_offers(session["location"], await get_world_state_async())
    if not quest_ref:
        embed = create_embed(
            title="❌ Missing Quest Reference",
            description=f"Select a quest by number or ID. Use `{PREFIX}questboard` to view available quests.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    quest_ref = normalize_name(quest_ref)
    parts = quest_ref.split()
    branch_choice = None
    if len(parts) >= 2:
        quest_ref = parts[0]
        branch_choice = parts[1].lower()

    selected = None
    if quest_ref.isdigit():
        index = int(quest_ref) - 1
        if 0 <= index < len(session["quest_offers"]):
            selected = session["quest_offers"][index]
    else:
        for quest in session["quest_offers"]:
            if quest["id"].lower() == quest_ref.lower():
                selected = quest
                break

    if not selected:
        embed = create_embed(
            title="❌ Quest Not Found",
            description="This quest is not in your available offers.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    branches = selected.get("branches") or []
    if branches and not branch_choice:
        branch_text = ", ".join(f"{branch['id']}({branch['title']})" for branch in branches)
        embed = create_embed(
            title="🔀 Quest has Branches",
            description=f"Use `{PREFIX}questpath {selected['id']} <branch_id>`\nAvailable: {branch_text}",
            color=COLOR_INFO
        )
        await ctx.send(embed=embed)
        return

    if branches and branch_choice:
        chosen_branch = None
        for branch in branches:
            if branch["id"].lower() == branch_choice:
                chosen_branch = branch
                break
        if not chosen_branch:
            embed = create_embed(
                title="❌ Branch Not Found",
                description=f"Use `{PREFIX}questboard` to view available branches.",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        selected["title"] = f"{selected['title']} - {chosen_branch['title']}"
        selected["objective"] = chosen_branch["objective"]
        selected["reward"] = chosen_branch["reward"]
        selected["branches"] = []
        selected["branch_selected"] = chosen_branch["id"]
        selected["count"] = chosen_branch["objective"].get("count", 1)

    active_ids = {q["id"] for q in session["quests"]}
    if selected["id"] in active_ids:
        embed = create_embed(
            title="⚠️ Quest Already Active",
            description="This quest is already in your active quest log.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    selected["status"] = "active"
    selected["progress"] = 0
    session["quests"].append(selected)
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"✅ Accepted: {selected['title']}",
        color=COLOR_SUCCESS
    )
    embed.add_field(name="Target", value=f"{selected['objective']['target']} x{selected['count']}", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="questpath")
async def cmd_questpath(ctx, quest_id_ref: str = None, branch_id: str = None):
    session = await get_session_async(ctx.author.id)
    if not quest_id_ref or not branch_id:
        await ctx.send(f"Format: `{PREFIX}questpath <id> <branch_id>`")
        return

    target_offer = None
    for offer in session.get("quest_offers", []):
        if offer["id"].lower() == normalize_name(quest_id_ref).lower():
            target_offer = offer
            break

    if not target_offer:
        await ctx.send("Quest offer tidak ditemukan. Gunakan `!questboard` dulu.")
        return

    branches = target_offer.get("branches") or []
    chosen_branch = None
    for branch in branches:
        if branch["id"].lower() == normalize_name(branch_id).lower():
            chosen_branch = branch
            break

    if not chosen_branch:
        await ctx.send("Branch tidak ditemukan.")
        return

    active_ids = {q["id"] for q in session["quests"]}
    if target_offer["id"] in active_ids:
        await ctx.send("Quest ini sudah aktif.")
        return

    branch_quest = copy.deepcopy(target_offer)
    branch_quest["title"] = f"{branch_quest['title']} - {chosen_branch['title']}"
    branch_quest["objective"] = chosen_branch["objective"]
    branch_quest["reward"] = chosen_branch["reward"]
    branch_quest["branches"] = []
    branch_quest["branch_selected"] = chosen_branch["id"]
    branch_quest["count"] = chosen_branch["objective"].get("count", 1)
    branch_quest["status"] = "active"
    branch_quest["progress"] = 0
    session["quests"].append(branch_quest)
    await save_session_async(ctx.author.id, session)
    await ctx.send(f"Cabang quest dipilih: **{branch_quest['title']}**")


@bot.command(name="quests")
async def cmd_quests(ctx):
    """Tampilkan quest log dengan quest aktif dan completed."""
    session = await get_session_async(ctx.author.id)
    active = [q for q in session.get("quests", []) if q.get("status") == "active"]
    completed = [q for q in session.get("quests", []) if q.get("status") == "completed"]
    
    if not active and not completed:
        embed = create_menu_embed(
            "Quest Log",
            "Kamu belum punya quest aktif atau selesai",
            color=COLOR_WARNING,
            icon="📋"
        )
        embed.add_field(
            name="🔍 Cara Mendapat Quest",
            value=f"Gunakan `{PREFIX}receptionist` atau `{PREFIX}questboard` untuk menemukan quest baru",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    embed = create_menu_embed(
        "Quest Log",
        f"Active: {len(active)} • Completed: {len(completed)}",
        color=COLOR_QUEST,
        icon="📋"
    )
    
    if active:
        active_text = ""
        for quest in active:
            active_text += f"**[{quest['id']}]** {quest_display_line(quest)}\n"
        embed.add_field(
            name="🔴 Active Quests",
            value=active_text.strip() or "Tidak ada quest aktif",
            inline=False
        )
    
    if completed:
        completed_text = ""
        for quest in completed[-5:]:
            completed_text += f"✅ [{quest['id']}] {quest['title']}\n"
        embed.add_field(
            name="✅ Completed Quests (Recent)",
            value=completed_text.strip(),
            inline=False
        )
    
    footer = format_menu_footer(extra=f"Total: {len(active) + len(completed)}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !completequest <id> untuk menyelesaikan quest")
    await ctx.send(embed=embed)


@bot.command(name="completequest")
async def cmd_completequest(ctx, quest_id_ref: str = None):
    session = await get_session_async(ctx.author.id)
    if not quest_id_ref:
        embed = create_embed(
            title="❌ Missing Quest ID",
            description=f"Use `{PREFIX}quests` to view active quests.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    quest_id_ref = normalize_name(quest_id_ref)
    quest = None
    for candidate in session.get("quests", []):
        if candidate["id"].lower() == quest_id_ref.lower():
            quest = candidate
            break

    if not quest:
        embed = create_embed(
            title="❌ Quest Not Found",
            description="This quest ID is not in your quest log.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    success, message = await complete_if_ready(session, quest)
    if not success:
        await save_session_async(ctx.author.id, session)
        embed = create_embed(
            title="⏳ Quest Not Ready",
            description=message,
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    await save_session_async(ctx.author.id, session)
    reward_items = ", ".join(quest["reward"].get("items", [])) or "No items"
    
    embed = create_embed(
        title="✅ Quest Completed",
        description=message,
        color=COLOR_SUCCESS
    )
    embed.add_field(name="💰 Gold", value=quest['reward'].get('gold', 0), inline=True)
    embed.add_field(name="🎁 Items", value=reward_items, inline=True)
    await ctx.send(embed=embed)


@bot.command(name="status")
async def cmd_status(ctx):
    session = await get_session_async(ctx.author.id)
    embed = create_embed(
        title="📊 Status Karakter",
        color=COLOR_INFO
    )
    stats_text = stat_block(session)
    embed.description = stats_text
    embed.set_footer(text=f"Level {session.get('level', 1)} • Location: {session.get('location', 'Unknown')}")
    await ctx.send(embed=embed)


@bot.command(name="inventory")
async def cmd_inventory(ctx):
    """Tampilkan inventory dengan format terstruktur dan terorganisir."""
    session = await get_session_async(ctx.author.id)
    counts = inventory_counts(session)
    
    embed = create_menu_embed(
        "Inventory",
        f"Kamu memiliki {sum(counts.values())} item",
        color=COLOR_ITEM,
        icon="🎒"
    )
    
    if not counts:
        embed.description = "Inventory kosong 🥺"
        embed.add_field(
            name="Cara Mendapat Item",
            value="Jelajahi dunia, selesaikan quest, atau beli dari shop untuk mengisi inventory",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Group items by type
    items_by_type = {}
    for item_name, qty in counts.items():
        item_info = item_catalog().get(item_name, {})
        item_kind = item_info.get("type", "misc") if isinstance(item_info, dict) else "misc"
        if item_kind not in items_by_type:
            items_by_type[item_kind] = []
        items_by_type[item_kind].append((item_name, qty))
    
    # Display items grouped by type
    for item_type in sorted(items_by_type.keys()):
        items = items_by_type[item_type]
        type_emoji = {"equipment": "⚔️", "consumable": "🧪", "misc": "📦", "crafting": "🔧"}.get(item_type, "📦")
        
        type_text = f"{type_emoji} **{item_type.upper()}** ({len(items)})\n"
        for item_name, qty in items:
            weight_text = item_weight_text(item_name)
            if weight_text:
                type_text += f"• {item_name} × **{qty}**  |  Berat: {weight_text}\n"
            else:
                type_text += f"• {item_name} × **{qty}**\n"
        
        embed.add_field(
            name=f"{type_emoji} {item_type.capitalize()}",
            value=type_text.strip(),
            inline=False
        )
    
    carry_now = current_inventory_weight(session)
    carry_limit = current_weight_limit(session)
    footer = format_menu_footer(extra=f"Total: {sum(counts.values())} item | Weight: {carry_now:.2f}/{carry_limit:.2f} kg")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !use <item> atau !equip <item>")
    await ctx.send(embed=embed)


@bot.command(name="use")
async def cmd_use(ctx, *, item_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not item_name:
        embed = create_embed(
            title="❌ Missing Item Name",
            description="Please specify an item to use.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    canonical, item = find_item(item_name)
    if not canonical:
        embed = create_embed(
            title="❌ Item Not Found",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if canonical not in session.get("inventory", []):
        embed = create_embed(
            title="❌ Item Not in Inventory",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    item_type = item.get("type", "misc") if isinstance(item, dict) else "misc"
    if item_type != "consumable":
        embed = create_embed(
            title="❌ Not a Consumable",
            description=f"This item cannot be used. Try `{PREFIX}equip` if it's equipment.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    remove_item(session, canonical, 1)
    heal = int(item.get("heal", 0))
    mana = int(item.get("mana", 0))
    session["hp"] = min(session["max_hp"], session["hp"] + heal)
    session["sp"] = min(session.get("max_sp", 50), session.get("sp", 0) + mana)
    await apply_level_up_if_needed(session)
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"✨ Used {canonical}",
        color=COLOR_SUCCESS
    )
    effect_lines = []
    if heal:
        effect_lines.append(f"HP +{heal}")
    if mana:
        effect_lines.append(f"MP +{mana}")
    embed.description = f"Effects: {', '.join(effect_lines) if effect_lines else 'No effects'}"
    await ctx.send(embed=embed)



@bot.command(name="equipped")
async def cmd_equipped(ctx):
    """Tampilkan equipment yang sedang dipakai."""
    session = await get_session_async(ctx.author.id)
    
    if not session.get("created", False):
        embed = create_menu_embed(
            "Equipment",
            "Kamu belum membuat karakter",
            color=COLOR_ERROR,
            icon="⚔️"
        )
        await ctx.send(embed=embed)
        return
    
    embed = create_menu_embed(
        "Equipped Items",
        "Equipment yang sedang kamu gunakan",
        color=COLOR_ITEM,
        icon="⚔️"
    )
    
    equipped = session.get("equipped", {})
    has_equipped = False
    
    # Display weapon
    weapon = equipped.get("weapon")
    if weapon:
        item_info = item_catalog().get(weapon, {})
        weapon_str = f"**{weapon}**"
        if isinstance(item_info, dict):
            attack = item_info.get("attack", 0)
            if attack:
                weapon_str += f"\n🗡️ Attack: **+{attack}**"
            rarity = item_info.get("rarity", "common")
            weapon_str += f"\n✨ Rarity: {rarity.capitalize()}"
            weight_text = item_info.get("weight")
            if weight_text is not None:
                unit = item_info.get("weight_unit", "kg")
                weapon_str += f"\n⚖️ Weight: **{weight_text} {unit}**"
        embed.add_field(name="🗡️ Weapon", value=weapon_str, inline=True)
        has_equipped = True
    else:
        embed.add_field(name="🗡️ Weapon", value="*Tidak diperlengkapi*", inline=True)
    
    # Display armor
    armor = equipped.get("armor")
    if armor:
        item_info = item_catalog().get(armor, {})
        armor_str = f"**{armor}**"
        if isinstance(item_info, dict):
            defense = item_info.get("defense", 0)
            if defense:
                armor_str += f"\n🛡️ Defense: **+{defense}**"
            rarity = item_info.get("rarity", "common")
            armor_str += f"\n✨ Rarity: {rarity.capitalize()}"
            weight_text = item_info.get("weight")
            if weight_text is not None:
                unit = item_info.get("weight_unit", "kg")
                armor_str += f"\n⚖️ Weight: **{weight_text} {unit}**"
        embed.add_field(name="🛡️ Armor", value=armor_str, inline=True)
        has_equipped = True
    else:
        embed.add_field(name="🛡️ Armor", value="*Tidak diperlengkapi*", inline=True)
    
    # Display trinket
    trinket = equipped.get("trinket")
    if trinket:
        item_info = item_catalog().get(trinket, {})
        trinket_str = f"**{trinket}**"
        if isinstance(item_info, dict):
            rarity = item_info.get("rarity", "common")
            trinket_str += f"\n✨ Rarity: {rarity.capitalize()}"
            weight_text = item_info.get("weight")
            if weight_text is not None:
                unit = item_info.get("weight_unit", "kg")
                trinket_str += f"\n⚖️ Weight: **{weight_text} {unit}**"
        embed.add_field(name="💎 Trinket", value=trinket_str, inline=True)
        has_equipped = True
    else:
        embed.add_field(name="💎 Trinket", value="*Tidak diperlengkapi*", inline=True)

    # Display backpack
    backpack = equipped.get("backpack")
    if backpack:
        item_info = item_catalog().get(backpack, {})
        backpack_str = f"**{backpack}**"
        if isinstance(item_info, dict):
            rarity = item_info.get("rarity", "common")
            backpack_str += f"\n✨ Rarity: {rarity.capitalize()}"
            weight_text = item_info.get("weight")
            if weight_text is not None:
                unit = item_info.get("weight_unit", "kg")
                backpack_str += f"\n⚖️ Weight: **{weight_text} {unit}**"
            bonus_limit = item_info.get("bonuses", {}).get("weight_limit", 0) if isinstance(item_info.get("bonuses", {}), dict) else 0
            if bonus_limit:
                backpack_str += f"\n🎒 Capacity Bonus: **+{bonus_limit} kg**"
        embed.add_field(name="🎒 Backpack", value=backpack_str, inline=True)
        has_equipped = True
    else:
        embed.add_field(name="🎒 Backpack", value="*Tidak diperlengkapi*", inline=True)
    
    # Add summary of bonuses if anything equipped
    if has_equipped:
        bonus_summary = resolve_equipment_bonuses(session)
        if bonus_summary:
            bonus_text = "\n".join([f"• {k.upper()}: +{v}" for k, v in bonus_summary.items()])
            embed.add_field(name="📊 Total Bonuses", value=bonus_text or "Tidak ada bonus", inline=False)

    carry_now = current_inventory_weight(session)
    carry_limit = current_weight_limit(session)
    embed.add_field(name="⚖️ Carry Weight", value=f"{carry_now:.2f}/{carry_limit:.2f} kg", inline=False)
    
    embed.add_field(
        name="💡 Tips",
        value=f"Gunakan `{PREFIX}equip <item>` untuk melengkapi item\nGunakan `{PREFIX}unequip <slot>` untuk melepas item (weapon/armor/trinket/backpack)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="equip")
async def cmd_equip(ctx, *, item_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not item_name:
        embed = create_embed(
            title="❌ Missing Equipment Name",
            description="Specify an equipment to equip.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    canonical, item = find_item(item_name)
    if not canonical or canonical not in session.get("inventory", []):
        embed = create_embed(
            title="❌ Equipment Not Found in Inventory",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    item_type = item.get("type", "misc") if isinstance(item, dict) else "misc"
    slot = item.get("slot") if isinstance(item, dict) else None
    if item_type != "equipment" or slot not in session["equipped"]:
        embed = create_embed(
            title="❌ Cannot Equip",
            description="This item cannot be equipped.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    session["equipped"][slot] = canonical
    # Recalculate derived stats after equipping
    base = session.get("base_stats", DEFAULT_SESSION.get("base_stats", {}))
    job_bonus = stats.load_job_stats(JOBS, session.get("job", "Novice"))
    combined = stats.combine_base_stats(base, job_bonus)
    equip_bonus = resolve_equipment_bonuses(session)
    session["derived_stats"] = stats.calculate_derived_stats(combined, session.get("level", 1), equipment_bonus=equip_bonus)
    session["max_hp"] = session["derived_stats"].get("max_hp", session.get("max_hp", 100))
    session["max_sp"] = session["derived_stats"].get("max_sp", session.get("max_sp", 50))
    session["hp"] = min(session.get("hp", session["max_hp"]), session["max_hp"])
    session["sp"] = min(session.get("sp", session.get("max_sp", 50)), session["max_sp"])
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"⚔️ Equipped {canonical}",
        description=f"Equipped to slot: **{slot}**",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="unequip")
async def cmd_unequip(ctx, slot: str = None):
    session = await get_session_async(ctx.author.id)
    if not slot:
        embed = create_embed(
            title="❌ Missing Slot Name",
            description="Specify a slot: weapon, armor, trinket, or backpack.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    slot = normalize_name(slot).lower()
    if slot not in session["equipped"]:
        embed = create_embed(
            title="❌ Slot Not Found",
            description="Valid slots: weapon, armor, trinket, backpack",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    session["equipped"][slot] = None
    # Recalculate derived stats after unequipping
    base = session.get("base_stats", DEFAULT_SESSION.get("base_stats", {}))
    job_bonus = stats.load_job_stats(JOBS, session.get("job", "Novice"))
    combined = stats.combine_base_stats(base, job_bonus)
    equip_bonus = resolve_equipment_bonuses(session)
    session["derived_stats"] = stats.calculate_derived_stats(combined, session.get("level", 1), equipment_bonus=equip_bonus)
    session["max_hp"] = session["derived_stats"].get("max_hp", session.get("max_hp", 100))
    session["max_sp"] = session["derived_stats"].get("max_sp", session.get("max_sp", 50))
    session["hp"] = min(session.get("hp", session["max_hp"]), session["max_hp"])
    session["sp"] = min(session.get("sp", session.get("max_sp", 50)), session["max_sp"])
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"✨ Unequipped from {slot}",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="recipes")
async def cmd_recipes(ctx):
    """Tampilkan daftar resep crafting yang tersedia dengan format modern."""
    session = await get_session_async(ctx.author.id)
    location = session["location"]
    current_station = station_for_location(location)
    
    embed = create_menu_embed(
        "Crafting Recipes",
        f"📍 {location}",
        color=COLOR_ITEM,
        icon="📖"
    )
    
    if current_station:
        embed.description += f" • **{current_station}** Station"
    
    available_recipes = []
    for recipe_name, recipe in recipe_catalog().items():
        if recipe_available_at_location(recipe_name, location):
            available_recipes.append((recipe_name, recipe))
    
    if not available_recipes:
        embed.add_field(
            name="❌ No Recipes",
            value=f"Tidak ada resep tersedia di **{location}**. Coba lokasi lain dengan crafting station.",
            inline=False
        )
    else:
        for recipe_name, recipe in available_recipes:
            requirements = recipe.get("requires", {})
            req_text = " + ".join(f"{item} ×{amount}" for item, amount in requirements.items())
            success = int(recipe.get("success_rate", 1.0) * 100)
            output_qty = recipe.get('output_qty', 1)
            
            recipe_detail = f"**Ingredients:** {req_text}\n"
            recipe_detail += f"**Output:** {output_qty} item\n"
            recipe_detail += f"**Success Rate:** {success}%"
            
            add_menu_item(
                embed,
                recipe_name,
                recipe_detail,
                emoji="🔨",
                inline=False
            )
    
    footer = format_menu_footer(extra=f"Recipes: {len(available_recipes)}")
    embed.set_footer(text=f"{footer}\n💡 Gunakan !craft <recipe> untuk membuat item")
    await ctx.send(embed=embed)


@bot.command(name="craft")
async def cmd_craft(ctx, *, query: str = None):
    session = await get_session_async(ctx.author.id)
    if not query:
        embed = create_embed(
            title="❌ Invalid Format",
            description=f"Usage: `{PREFIX}craft <item> [qty]`",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    parts = normalize_name(query).split()
    qty = 1
    if parts and parts[-1].isdigit():
        qty = max(1, int(parts[-1]))
        item_query = " ".join(parts[:-1])
    else:
        item_query = normalize_name(query)

    recipe_name, recipe = find_recipe(item_query)
    if not recipe:
        embed = create_embed(
            title="❌ Recipe Not Found",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    if not recipe_available_at_location(recipe_name, session["location"]):
        embed = create_embed(
            title="❌ Recipe Not Available",
            description=f"This recipe can only be crafted at {recipe.get('station', 'a specific station')}.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    requirements = recipe.get("requires", {})
    if not requirements:
        embed = create_embed(
            title="❌ Invalid Recipe",
            description="This recipe has no valid requirements.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    can_pay, missing_item = can_pay_requirements(session, requirements, qty)
    if not can_pay:
        embed = create_embed(
            title="❌ Insufficient Materials",
            description=f"Missing: **{missing_item}**",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    # Combine recipe base chance with character's success_rate derived stat
    recipe_base = float(recipe.get("success_rate", 1.0))
    derived = session.get("derived_stats", {})
    char_success = float(derived.get("success_rate", 50)) / 100.0
    # final success = recipe_base + (char_success - 0.5)
    success_rate = recipe_base + (char_success - 0.5)
    success_rate = min(0.99, max(0.01, success_rate))
    consume_requirements(session, requirements, qty)

    crafted = 0
    blocked_by_weight = 0
    for _ in range(qty):
        if random.random() <= success_rate:
            out_qty = int(recipe.get("output_qty", 1))
            added = add_item(session, recipe_name, out_qty)
            crafted += added
            blocked_by_weight += max(0, out_qty - added)
    await save_session_async(ctx.author.id, session)

    if crafted:
        embed = create_embed(
            title=f"✨ Crafted {recipe_name} x{crafted}",
            color=COLOR_SUCCESS
        )
        if blocked_by_weight > 0:
            embed.add_field(
                name="⚖️ Weight Limit",
                value=f"{blocked_by_weight} item hasil craft tidak bisa masuk inventory karena melebihi weight limit.",
                inline=False
            )
    else:
        embed = create_embed(
            title="❌ Crafting Failed",
            description="Materials were used but crafting failed.",
            color=COLOR_WARNING
        )
    await ctx.send(embed=embed)


def upgrade_requirements(item_name, level):
    item = item_catalog().get(item_name, {})
    slot = item.get("slot") if isinstance(item, dict) else None
    if slot == "weapon":
        return {"Iron Ore": 2 * level, "Monster Bone": 1 * level}
    if slot == "armor":
        return {"Leather Pelt": 2 * level, "Iron Ore": 1 * level}
    if slot == "trinket":
        return {"Moon Salt": 1 * level, "Night Gem": 1 * level}
    return None


@bot.command(name="upgrade")
async def cmd_upgrade(ctx, *, item_name: str = None):
    session = await get_session_async(ctx.author.id)
    if not item_name:
        embed = create_embed(
            title="❌ Invalid Format",
            description=f"Usage: `{PREFIX}upgrade <item>`",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    canonical, item = find_item(item_name)
    if not canonical or not isinstance(item, dict) or item.get("type") != "equipment":
        embed = create_embed(
            title="❌ Not Equipment",
            description="This item cannot be upgraded.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    if canonical not in session.get("inventory", []) and canonical not in session.get("equipped", {}).values():
        embed = create_embed(
            title="❌ Item Not Found",
            description="Equipment must be in inventory or equipped.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    current_level = int(session.get("gear_upgrades", {}).get(canonical, 0))
    next_level = current_level + 1
    if next_level > 5:
        embed = create_embed(
            title="❌ Max Upgrade Level",
            description="This equipment is at max upgrade level.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    requirements = upgrade_requirements(canonical, next_level)
    if not requirements:
        embed = create_embed(
            title="❌ No Upgrade Scheme",
            description="This equipment cannot be upgraded.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    can_pay, missing_item = can_pay_requirements(session, requirements)
    if not can_pay:
        embed = create_embed(
            title="❌ Insufficient Materials",
            description=f"Missing: **{missing_item}**",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    location = session["location"]
    if item.get("slot") in {"weapon", "armor"} and station_for_location(location) != "BlackSmith":
        embed = create_embed(
            title="❌ Wrong Location",
            description="Weapon and armor upgrades must be done at the BlackSmith.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if item.get("slot") == "trinket" and station_for_location(location) != "Alchemist":
        embed = create_embed(
            title="❌ Wrong Location",
            description="Trinket upgrades must be done at the Alchemist.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    consume_requirements(session, requirements)
    session.setdefault("gear_upgrades", {})[canonical] = next_level
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"✨ {canonical} Upgraded",
        description=f"Upgrade level: +{next_level}",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="shop")
@require_location_config("shop", SHOP_STOCKS.keys(), "lokasi shop")
async def cmd_shop(ctx):
    session = await get_session_async(ctx.author.id)
    location = session["location"]
    stock = SHOP_STOCKS.get(location)
    if not stock:
        embed = create_embed(
            title="❌ No Shop",
            description="There is no shop at this location.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return
    embed = create_embed(
        title=f"🛍️ Shop {location}",
        description=f"Your Gold: {session['gold']}",
        color=COLOR_PRIMARY
    )
    shop_items = ""
    for item_name in stock:
        item = item_catalog().get(item_name, {})
        price = int(item.get("price", 10)) if isinstance(item, dict) else 10
        rarity = item.get("rarity", "common") if isinstance(item, dict) else "common"
        weight_text = item_weight_text(item_name)
        backpack_bonus = 0
        if isinstance(item, dict) and item.get("slot") == "backpack":
            backpack_bonus = int(item.get("bonuses", {}).get("weight_limit", 0)) if isinstance(item.get("bonuses", {}), dict) else 0
        line = f"**{item_name}** | {price} gold | {rarity}"
        if weight_text:
            line += f" | {weight_text}"
        if backpack_bonus > 0:
            line += f" | +{backpack_bonus} kg capacity"
        shop_items += line + "\n"
    embed.add_field(name="Items for Sale", value=shop_items, inline=False)
    embed.add_field(name="📝 How to Buy", value=f"Use `{PREFIX}buy <item> [qty]` to purchase.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="buy")
@require_location_config("buy", SHOP_STOCKS.keys(), "lokasi shop")
async def cmd_buy(ctx, *, query: str = None):
    session = await get_session_async(ctx.author.id)
    stock = SHOP_STOCKS.get(session["location"])
    if not stock:
        embed = create_embed(
            title="❌ No Shop",
            description="There is no shop at this location.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if not query:
        embed = create_embed(
            title="❌ Missing Item Name",
            description="Specify what you want to buy.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    parts = normalize_name(query).split()
    qty = 1
    if parts and parts[-1].isdigit():
        qty = max(1, int(parts[-1]))
        item_query = " ".join(parts[:-1])
    else:
        item_query = normalize_name(query)

    canonical, item = find_item(item_query)
    if not canonical or canonical not in stock:
        embed = create_embed(
            title="❌ Item Not in Stock",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    price = int(item.get("price", 10)) if isinstance(item, dict) else 10
    total = price * qty

    max_qty_by_weight = max_addable_quantity(session, canonical)
    if max_qty_by_weight <= 0:
        embed = create_embed(
            title="❌ Weight Limit Penuh",
            description=(
                f"Tasmu sudah penuh untuk item **{canonical}**.\n"
                f"Carry weight: {current_inventory_weight(session):.2f}/{current_weight_limit(session):.2f} kg"
            ),
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if qty > max_qty_by_weight:
        embed = create_embed(
            title="❌ Melebihi Weight Limit",
            description=(
                f"Jumlah maksimal **{canonical}** yang bisa dibeli sekarang: **{max_qty_by_weight}**.\n"
                f"Carry weight: {current_inventory_weight(session):.2f}/{current_weight_limit(session):.2f} kg"
            ),
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return

    if session["gold"] < total:
        embed = create_embed(
            title="❌ Insufficient Gold",
            description=f"You need {total} gold, but you only have {session['gold']}.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    session["gold"] -= total
    added = add_item(session, canonical, qty)
    if added <= 0:
        session["gold"] += total
        embed = create_embed(
            title="❌ Gagal Menambahkan Item",
            description="Inventory melebihi weight limit.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title=f"✨ Purchased {canonical} x{qty}",
        description=f"Cost: {total} gold",
        color=COLOR_SUCCESS
    )
    await ctx.send(embed=embed)


@bot.command(name="battle")
async def cmd_battle(ctx):
    session = await get_session_async(ctx.author.id)
    battle = session.get("battle")
    if not battle:
        embed = create_embed(
            title="❌ No Active Battle",
            description=f"Explore locations or use `{PREFIX}startbattle` to find enemies.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return
    embed = create_embed(
        title="⚔️ Battle Status",
        color=COLOR_PRIMARY
    )
    embed.add_field(name="Enemy", value=f"**{battle['monster_name']}**", inline=True)
    embed.add_field(name="Enemy HP", value=f"{battle['monster_hp']}", inline=True)
    embed.add_field(name="Your HP", value=f"{battle['player_hp']}", inline=True)
    embed.add_field(name="Actions", value=f"Use `{PREFIX}attack` or `{PREFIX}flee`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="startbattle")
async def cmd_startbattle(ctx):
    session = await get_session_async(ctx.author.id)
    world_state = await get_world_state_async()
    monster = session.get("last_encounter")
    if not monster:
        embed = create_embed(
            title="❌ No Enemy Nearby",
            description="Explore locations first to find enemies.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    refresh_battle_context(session, world_state, ctx.channel.id)

    session["battle"] = {
        "monster_name": monster["name"],
        "monster_hp": int(monster["hp"]),
        "monster_atk": int(monster["atk"]),
        "loot": list(monster.get("loot", [])),
        "player_hp": int(session["hp"]),
    }
    await save_session_async(ctx.author.id, session)
    await save_world_state_async(world_state)
    
    embed = create_embed(
        title=f"⚔️ Battle Started!",
        color=COLOR_WARNING
    )
    embed.add_field(name="Enemy", value=f"**{monster['name']}**", inline=True)
    embed.add_field(name="Enemy HP", value=f"{monster['hp']}", inline=True)
    embed.add_field(name="Your HP", value=f"{session['hp']}", inline=True)
    embed.add_field(name="Combat", value=f"Use `{PREFIX}attack` to attack or `{PREFIX}flee` to run away.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="attack")
async def cmd_attack(ctx):
    session = await get_session_async(ctx.author.id)
    battle = session.get("battle")
    if not battle:
        embed = create_embed(
            title="❌ Not in Battle",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    reduce_skill_cooldowns(session)
    world_state = await get_world_state_async()
    refresh_battle_context(session, world_state, ctx.channel.id)
    bonus = battle_stat_bonus(session)
    player_damage = random.randint(8, 20) + (session["level"] - 1) * 2 + bonus["attack"]
    battle["monster_hp"] -= player_damage
    lines = [f"💥 **Attack!**\nYou dealt **{player_damage}** damage to **{battle['monster_name']}**."]
    await battle_round_after_action(ctx, session, battle, world_state, lines)


@bot.command(name="flee")
async def cmd_flee(ctx):
    session = await get_session_async(ctx.author.id)
    battle = session.get("battle")
    if not battle:
        embed = create_embed(
            title="❌ Not in Battle",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    reduce_skill_cooldowns(session)
    world_state = await get_world_state_async()
    refresh_battle_context(session, world_state, ctx.channel.id)
    if random.random() < 0.55:
        session["battle"] = None
        await save_session_async(ctx.author.id, session)
        await save_world_state_async(world_state)
        
        embed = create_embed(
            title="✨ Escaped!",
            description="You successfully disappeared into the shadows.",
            color=COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        return

    damage = random.randint(1, int(battle["monster_atk"]))
    battle["player_hp"] -= damage
    session["hp"] = max(0, battle["player_hp"])
    if battle["player_hp"] <= 0:
        session["battle"] = None
        session["hp"] = session["max_hp"]
        embed = create_embed(
            title="💀 Fled Failed - Defeated",
            description="The monster's final attack knocked you out. You recovered at a safe place.",
            color=COLOR_ERROR
        )
    else:
        embed = create_embed(
            title="❌ Fled Failed",
            description=f"The enemy hit you for **{damage}** damage. Your HP: {session['hp']}",
            color=COLOR_WARNING
        )
    await save_session_async(ctx.author.id, session)
    await ctx.send(embed=embed)


@bot.command(name="loot")
async def cmd_loot(ctx, *, target: str = None):
    if not target:
        embed = create_embed(
            title="❌ Missing Monster Name",
            description="Specify a monster name to view its loot table.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    target = normalize_name(target).lower()
    found = None
    for location, monsters in MONSTERS.items():
        for monster in monsters:
            if monster["name"].lower() == target or target in monster["name"].lower():
                found = monster
                break
        if found:
            break

    if not found:
        embed = create_embed(
            title="❌ Monster Not Found",
            description="This monster is not in the bestiary.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return

    embed = create_embed(
        title=f"🐉 {found['name']}",
        color=COLOR_PRIMARY
    )
    embed.add_field(name="HP", value=f"{found['hp']}", inline=True)
    embed.add_field(name="ATK", value=f"{found['atk']}", inline=True)
    drop_text = ", ".join(found.get('loot', [])) or "No drops"
    embed.add_field(name="Loot", value=drop_text, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="bestiary")
async def cmd_bestiary(ctx, *, location: str = None):
    if location:
        destination = find_location(location)
        if not destination:
            embed = create_embed(
                title="❌ Location Not Found",
                description=f"Could not find location: {location}",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        monsters = MONSTERS.get(destination, [])
        if not monsters:
            embed = create_embed(
                title="❌ No Monsters",
                description=f"No monsters recorded at {destination} yet.",
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
            return
        embed = create_embed(
            title=f"🐉 Monsters at {destination}",
            color=COLOR_PRIMARY
        )
        for monster in monsters:
            monster_info = f"**HP:** {monster['hp']} | **ATK:** {monster['atk']}\n**Loot:** {', '.join(monster.get('loot', []))}"
            embed.add_field(name=monster['name'], value=monster_info, inline=False)
        await ctx.send(embed=embed)
        return

    embed = create_embed(
        title="📖 Bestiary",
        description="Monsters by Location",
        color=COLOR_PRIMARY
    )
    for location_name, monsters in MONSTERS.items():
        monster_names = ", ".join(monster["name"] for monster in monsters)
        embed.add_field(name=location_name, value=monster_names, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="quest")
async def cmd_quest(ctx):
    await cmd_quests(ctx)


@bot.command(name="rest")
async def cmd_rest(ctx):
    session = await get_session_async(ctx.author.id)
    if session["location"] not in {"Kota Utama", "Kedai Petualang", "Kedai Perbatasan"}:
        embed = create_embed(
            title="❌ Cannot Rest Here",
            description="You can only rest at safe places like cities or taverns.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    healed = min(session["max_hp"] - session["hp"], random.randint(20, 45))
    session["hp"] += healed
    await save_session_async(ctx.author.id, session)
    
    embed = create_embed(
        title="😴 Rested",
        color=COLOR_SUCCESS
    )
    embed.add_field(name="HP Restored", value=f"+{healed}", inline=True)
    embed.add_field(name="Current HP", value=f"{session['hp']}/{session['max_hp']}", inline=True)
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed(
            title="❌ Missing Argument",
            description=f"Use `{PREFIX}help` for command list.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if isinstance(error, commands.BadArgument):
        embed = create_embed(
            title="❌ Invalid Argument",
            description=f"Use `{PREFIX}help` for help.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    if isinstance(error, commands.CommandNotFound):
        # Ignore unknown commands to avoid noisy error logs when users mistype.
        return
    raise error


if __name__ == "__main__":
    if not TOKEN:
        print("Tidak ada token di config.json — buat file dari config.example.json dan isi tokenmu.")
    else:
        bot.run(TOKEN)
