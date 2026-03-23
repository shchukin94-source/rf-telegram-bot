import random
from typing import Optional

from config import ARMOR_SLOTS, DROP_GEAR_CHANCE, UPGRADE_CHANCES
from data import ARMOR_NAMES, CRAFT_RECIPES, GEAR_TIERS, WEAPON_NAMES
from models import Gear


def roll_weighted_tier(is_boss: bool) -> dict:
    weights = []
    for tier in GEAR_TIERS:
        weight = tier["weight"]
        if is_boss and tier["id"] in {"type_c", "leon"}:
            weight *= 3
        weights.append(weight)
    return random.choices(GEAR_TIERS, weights=weights, k=1)[0]


def make_gear(slot: str, level: int, is_boss: bool) -> Gear:
    tier = roll_weighted_tier(is_boss)
    names = WEAPON_NAMES if slot == "weapon" else ARMOR_NAMES[slot]
    base = max(1, level)
    if slot == "weapon":
        stat = max(1, int((3 + base * 0.9) * tier["weapon_mult"]))
    else:
        stat = max(1, int((2 + base * 0.6) * tier["armor_mult"]))
    return Gear(
        id=f"{slot}_{tier['id']}_{level}_{random.randint(1000, 9999)}",
        name=f"{random.choice(names)} [{tier['name']}] lv.{level}",
        slot=slot,
        level=level,
        tier_id=tier["id"],
        tier_name=tier["name"],
        base_stat=stat,
    )


def maybe_gear_drop(enemy_level: int, is_boss: bool, elite: bool = False) -> Optional[Gear]:
    chance = 100 if is_boss else (DROP_GEAR_CHANCE * 10 if elite else DROP_GEAR_CHANCE)
    if random.randint(1, 100) > min(100, chance):
        return None
    slot = random.choice(["weapon"] + ARMOR_SLOTS)
    return make_gear(slot, enemy_level, is_boss or elite)


def salvage_reward(gear: Gear) -> int:
    return max(2, gear.level + gear.base_stat + gear.upgrade * 2)


def craft_item(player, slot: str, level: int) -> Optional[Gear]:
    recipe = CRAFT_RECIPES["weapon" if slot == "weapon" else "armor"]
    if player.components < recipe["components"] or player.dizens < recipe["dizens"]:
        return None
    player.components -= recipe["components"]
    player.dizens -= recipe["dizens"]
    return make_gear(slot, level, False)


def try_upgrade(current_upgrade: int) -> tuple[bool, int]:
    rule = UPGRADE_CHANCES[current_upgrade]
    success = random.randint(1, 100) <= rule["chance"]
    if success:
        return True, rule["next"]
    return False, current_upgrade
