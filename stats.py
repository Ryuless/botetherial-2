"""
Character stat calculation system.
Handles base stats, derived stats, and formula calculations for the RPG system.
"""

from typing import Dict, Tuple


def load_race_stats(races_data: dict, race_key: str) -> dict:
    """Load base stats for a race from races.json data."""
    if race_key.lower() not in races_data:
        return {}
    race = races_data[race_key.lower()]
    return race.get("base_stats", {}).copy()


def load_job_stats(jobs_data: dict, job_key: str) -> dict:
    """Load bonus stats for a job from jobs.json data."""
    if job_key.lower() not in jobs_data:
        return {}
    job = jobs_data[job_key.lower()]
    return job.get("base_stats", {}).copy()


def combine_base_stats(race_stats: dict, job_stats: dict = None) -> dict:
    """Combine race and job base stats."""
    combined = race_stats.copy()
    if job_stats:
        for key, value in job_stats.items():
            combined[key] = combined.get(key, 0) + value
    return combined


def calculate_derived_stats(base_stats: dict, level: int = 1, equipment_bonus: dict = None) -> dict:
    """Calculate all derived stats from base stats and level."""
    if equipment_bonus is None:
        equipment_bonus = {}

    # Extract primary stats
    str_val = base_stats.get("str", 0)
    agi_val = base_stats.get("agi", 0)
    vit_val = base_stats.get("vit", 0)
    int_val = base_stats.get("int", 0)
    dex_val = base_stats.get("dex", 0)
    luk_val = base_stats.get("luk", 0)
    tec_val = base_stats.get("tec", 0)
    men_val = base_stats.get("men", 0)
    crt_val = base_stats.get("crt", 0)

    derived = {}

    # === OFFENSIVE STATS ===
    
    # ATK (Attack): STR for melee, DEX for ranged + LUK bonus
    atk_base = str_val + dex_val + (luk_val // 3)
    derived["atk"] = atk_base + equipment_bonus.get("atk", 0)

    # MATK (Magic Attack): INT (main), DEX (every 5 = +1), LUK (every 3 = +1)
    matk_base = int(int_val * 1.5) + (dex_val // 5) + (luk_val // 3)
    derived["matk"] = matk_base + equipment_bonus.get("matk", 0)

    # Hit (Accuracy): DEX (main) + LUK (every 3 = +1)
    hit_base = dex_val + (luk_val // 3)
    derived["hit"] = hit_base + equipment_bonus.get("hit", 0)

    # Critical: LUK * 0.3 + 1 + CRT bonus
    critical_rate = (luk_val * 0.3) + (crt_val * 0.5) + 1
    derived["crit"] = round(critical_rate, 2) + equipment_bonus.get("crit", 0)

    # ASPD (Attack Speed): AGI (main) + DEX (minor)
    aspd_base = agi_val + (dex_val // 2)
    derived["aspd"] = aspd_base + equipment_bonus.get("aspd", 0)

    # === DEFENSIVE STATS ===

    # DEF (Defense): VIT (every 1) + AGI (every 5 = +1) + equipment
    def_base = vit_val + (agi_val // 5)
    derived["def"] = def_base + equipment_bonus.get("def", 0)

    # MDEF (Magic Defense): INT (every 2 = +1) + VIT (every 5 = +1) + DEX (every 5 = +1) + MEN
    mdef_base = (int_val // 2) + (vit_val // 5) + (dex_val // 5) + men_val
    derived["mdef"] = mdef_base + equipment_bonus.get("mdef", 0)

    # Flee: AGI (main) + LUK (every 5 = +1)
    flee_base = agi_val + (luk_val // 5)
    derived["flee"] = flee_base + equipment_bonus.get("flee", 0)

    # Perfect Dodge: LUK (every 10 = +1)
    perfect_dodge = luk_val // 10
    derived["perfect_dodge"] = perfect_dodge + equipment_bonus.get("perfect_dodge", 0)

    # Critical Defense: LUK (every 5 = +1)
    crit_def = luk_val // 5
    derived["crit_def"] = crit_def + equipment_bonus.get("crit_def", 0)

    # === HP & MP ===

    # Max HP: VIT * 1% base + level bonus
    # Base Max HP = (10 + VIT) + (level - 1) * 2
    max_hp = (10 + vit_val) + (level - 1) * 2
    max_hp = int(max_hp * (1 + vit_val * 0.01))  # Apply VIT bonus
    derived["max_hp"] = max_hp + equipment_bonus.get("max_hp", 0)

    # Max SP: INT * 1% base + level bonus
    # Base Max SP = (10 + INT) + (level - 1) * 1
    max_sp = (10 + int_val) + (level - 1) * 1
    max_sp = int(max_sp * (1 + int_val * 0.01))  # Apply INT bonus
    derived["max_sp"] = max_sp + equipment_bonus.get("max_sp", 0)

    # === UTILITY STATS ===

    # Cast Time reduction: DEX (main), INT (half effect)
    # VCT reduction = -(DEX * 0.1 + INT * 0.05) percent
    # FCT cannot be reduced by stats
    vct_reduction = (dex_val * 0.1 + int_val * 0.05)
    derived["vct_reduction"] = min(vct_reduction, 100) + equipment_bonus.get("vct_reduction", 0)

    # HP Recovery: VIT based
    hp_recovery = 1 + (vit_val // 10)
    derived["hp_recovery"] = hp_recovery + equipment_bonus.get("hp_recovery", 0)

    # SP Recovery: INT based (every 6 INT = +1 SP per second)
    sp_recovery = 1 + (int_val // 6)
    derived["sp_recovery"] = sp_recovery + equipment_bonus.get("sp_recovery", 0)

    # Weight Limit: STR * 30 kg per point + base 500 kg
    weight_limit = 500 + (str_val * 30)
    derived["weight_limit"] = weight_limit + equipment_bonus.get("weight_limit", 0)

    # Success Rate (for crafting): Combination of DEX, LUK, INT, TEC
    # Base formula: 50% + (TEC * 0.5) + (DEX * 0.1) + (LUK * 0.05) + (INT * 0.05)
    success_rate = 50 + (tec_val * 0.5) + (dex_val * 0.1) + (luk_val * 0.05) + (int_val * 0.05)
    derived["success_rate"] = min(success_rate, 100) + equipment_bonus.get("success_rate", 0)

    # Status Resistance (VIT and LUK reduce status duration and chance)
    status_resistance = (vit_val // 5) + (luk_val // 10)
    derived["status_resistance"] = status_resistance + equipment_bonus.get("status_resistance", 0)

    return derived


def calculate_damage_scaling(base_stats: dict, weapon_type: str = "melee") -> Dict[str, float]:
    """Calculate damage scaling modifiers based on weapon type and stats."""
    str_val = base_stats.get("str", 0)
    dex_val = base_stats.get("dex", 0)

    scaling = {}

    if weapon_type == "melee":
        # Melee: STR = +1 ATK and +0.5% weapon damage
        scaling["atk_bonus"] = str_val
        scaling["damage_bonus"] = 1 + (str_val * 0.005)
    elif weapon_type == "ranged":
        # Ranged: DEX = +1 ATK and +0.5% weapon damage
        scaling["atk_bonus"] = dex_val
        scaling["damage_bonus"] = 1 + (dex_val * 0.005)
    elif weapon_type == "magic":
        # Magic: INT based
        int_val = base_stats.get("int", 0)
        scaling["matk_bonus"] = int_val
        scaling["damage_bonus"] = 1 + (int_val * 0.01)

    return scaling


def apply_status_effects(base_stats: dict, status_effect: str) -> int:
    """Calculate resistance/duration modification for status effects."""
    vit_val = base_stats.get("vit", 0)
    luk_val = base_stats.get("luk", 0)
    men_val = base_stats.get("men", 0)

    # Base resistance = (VIT + LUK + MEN) combined
    resistance = vit_val // 5 + luk_val // 10 + men_val // 10

    # Status effect categories with additional resistances
    effect_reduction = {
        "poison": vit_val // 3,  # VIT reduces poison
        "stun": vit_val // 5,     # VIT reduces stun duration
        "frozen": luk_val // 5,   # LUK helps break freeze
        "curse": luk_val // 5,    # LUK helps resist curse
        "sleep": men_val // 5,    # MEN helps resist sleep
        "blind": luk_val // 3,    # LUK helps resist blind
        "fear": men_val // 3,     # MEN helps resist fear
        "confusion": men_val // 5, # MEN helps resist confusion
    }

    return resistance + effect_reduction.get(status_effect.lower(), 0)


def calculate_critical_damage(crit_stat: float, base_damage: float) -> float:
    """Calculate critical damage multiplier."""
    # Base crit damage = 150% of normal damage
    # Each additional CRIT stat point adds 0.5% damage
    base_multiplier = 1.5
    additional_multiplier = (crit_stat * 0.005)
    return base_damage * (base_multiplier + additional_multiplier)


def calculate_potion_effectiveness(base_stats: dict) -> float:
    """Calculate potion effectiveness multiplier."""
    vit_val = base_stats.get("vit", 0)
    # Base = 100%, +2% per VIT
    return 1.0 + (vit_val * 0.02)


def create_character_stats(race_data: dict, race_key: str, job_key: str = "novice",
                          jobs_data: dict = None, level: int = 1) -> dict:
    """Create complete character stats from race and job."""
    if jobs_data is None:
        jobs_data = {}

    # Get race and job stats
    race_stats = load_race_stats(race_data, race_key)
    job_stats = load_job_stats(jobs_data, job_key) if jobs_data else {}

    # Combine base stats
    base_stats = combine_base_stats(race_stats, job_stats)

    # Calculate derived stats
    derived_stats = calculate_derived_stats(base_stats, level)

    # Create character stat object
    char_stats = {
        "base_stats": base_stats,
        "derived_stats": derived_stats,
        "race": race_key.lower(),
        "job": job_key.lower(),
        "level": level,
        "current_hp": derived_stats.get("max_hp", 100),
        "current_sp": derived_stats.get("max_sp", 50),
    }

    return char_stats


def format_stats_display(char_stats: dict) -> str:
    """Format character stats for display."""
    base = char_stats.get("base_stats", {})
    derived = char_stats.get("derived_stats", {})

    display = (
        f"**PRIMARY STATS**\n"
        f"STR: {base.get('str', 0)} | AGI: {base.get('agi', 0)} | VIT: {base.get('vit', 0)}\n"
        f"INT: {base.get('int', 0)} | DEX: {base.get('dex', 0)} | LUK: {base.get('luk', 0)}\n"
        f"TEC: {base.get('tec', 0)} | MEN: {base.get('men', 0)} | CRT: {base.get('crt', 0)}\n\n"
        f"**HP & MANA**\n"
        f"HP: {char_stats.get('current_hp', 0)}/{derived.get('max_hp', 0)}\n"
        f"MP: {char_stats.get('current_sp', 0)}/{derived.get('max_sp', 0)}\n\n"
        f"**OFFENSIVE**\n"
        f"ATK: {derived.get('atk', 0)} | MATK: {derived.get('matk', 0)} | Hit: {derived.get('hit', 0)}\n"
        f"CRIT: {derived.get('crit', 0)}% | ASPD: {derived.get('aspd', 0)}\n\n"
        f"**DEFENSIVE**\n"
        f"DEF: {derived.get('def', 0)} | MDEF: {derived.get('mdef', 0)} | Flee: {derived.get('flee', 0)}\n"
        f"Perfect Dodge: {derived.get('perfect_dodge', 0)} | CRIT DEF: {derived.get('crit_def', 0)}\n\n"
        f"**UTILITY**\n"
        f"Weight Limit: {derived.get('weight_limit', 0)} kg | Success Rate: {derived.get('success_rate', 0)}%\n"
        f"Status Resistance: +{derived.get('status_resistance', 0)}"
    )

    return display
