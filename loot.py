import random
from typing import Optional

from config import ARMOR_SLOTS, DROP_GEAR_CHANCE, UPGRADE_CHANCES
from data import ARMOR_NAMES, CONTAINER_SET_NAMES, CRAFT_RECIPES, GEAR_TIERS, WEAPON_NAMES
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
    return max(1, gear.level)


def craft_item(player, slot: str, level: int) -> Optional[Gear]:
    cost = level * 10
    if player.components < cost:
        return None
    player.components -= cost
    return make_gear(slot, level, False)


def try_upgrade(current_upgrade: int) -> tuple[bool, int]:
    rule = UPGRADE_CHANCES[current_upgrade]
    success = random.randint(1, 100) <= rule["chance"]
    if success:
        return True, rule["next"]
    return False, current_upgrade


def make_container_relic(slot: str, level: int) -> Gear:
    base = max(1, level)
    if slot == "weapon":
        stat = max(1, int((5 + base * 1.4) * 2.8))
    else:
        stat = max(1, int((4 + base * 1.1) * 2.5))

    return Gear(
        id=f"relic_{slot}_{level}_{random.randint(1000, 9999)}",
        name=f"{CONTAINER_SET_NAMES[slot]} [реликт] lv.{level}",
        slot=slot,
        level=level,
        tier_id="relic",
        tier_name="реликт",
        base_stat=stat,
    )


def open_ancient_container(player):
    roll = random.randint(1, 1000)

    if roll <= 25:
        slot = random.choice(["weapon"] + ARMOR_SLOTS)
        gear = make_container_relic(slot, max(1, player.level))
        return gear, "🌟 Супер-дроп: предмет реликтового контейнерного сета."

    if roll <= 35:
        gear = make_gear("weapon", max(1, player.level), True)
        gear.tier_id = "leon"
        gear.tier_name = "леон"
        gear.name = f"{gear.name.split(' [')[0]} [леон] lv.{gear.level}"
        return gear, "🔥 Супер-дроп: леон оружие из древнего контейнера."

    if roll <= 85:
        slot = random.choice(["weapon"] + ARMOR_SLOTS)
        gear = make_gear(slot, max(1, player.level), True)
        gear.tier_id = "type_c"
        gear.tier_name = "тип с"
        gear.name = f"{gear.name.split(' [')[0]} [тип с] lv.{gear.level}"
        return gear, "✨ Редкий дроп: предмет тип с из древнего контейнера."

    if roll <= 225:
        slot = random.choice(["weapon"] + ARMOR_SLOTS)
        gear = make_gear(slot, max(1, player.level), False)
        gear.tier_id = "int"
        gear.tier_name = "инт"
        gear.name = f"{gear.name.split(' [')[0]} [инт] lv.{gear.level}"
        return gear, "✨ Редкий дроп: инт предмет из древнего контейнера."

    slot = random.choice(["weapon"] + ARMOR_SLOTS)
    gear = make_gear(slot, max(1, player.level), False)
    return gear, "Контейнер открыт: обычный предмет."


def sell_weapon_from_inventory(player, idx: int) -> int:
    if not (0 <= idx < len(player.weapon_inventory)):
        return 0

    gear = player.weapon_inventory[idx]
    value = max(15, gear.level * 6 + gear.base_stat * 3 + gear.upgrade * 25)

    del player.weapon_inventory[idx]

    if player.equipped_weapon_index is not None:
        if player.equipped_weapon_index == idx:
            player.equipped_weapon_index = None
        elif player.equipped_weapon_index > idx:
            player.equipped_weapon_index -= 1

    player.dizens += value
    return value


def make_market_weapon(player) -> Gear:
    min_level = max(1, player.level - 5)
    max_level = max(1, player.level + 5)
    weapon_level = random.randint(min_level, max_level)
    return make_gear("weapon", weapon_level, False)
