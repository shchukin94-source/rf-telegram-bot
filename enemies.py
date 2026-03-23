from typing import List

from data import LOCATION_MONSTERS, ZONES
from stats import mob_exp


def get_zone(zone_id: str | None):
    if not zone_id:
        return None
    return next((z for z in ZONES if z["id"] == zone_id), None)


def selected_monsters_for_zone(zone_id: str) -> List[dict]:
    monsters = [{**m, "boss": None} for m in LOCATION_MONSTERS.get(zone_id, [])]
    zone = get_zone(zone_id)
    if zone:
        for boss in zone["bosses"]:
            monsters.append(
                {
                    "name": f"[БОСС] {boss['name']}",
                    "level": boss["level"],
                    "boss": boss,
                }
            )
    return monsters


def generate_enemy(zone_id: str, monster_entry: dict) -> dict:
    level = monster_entry["level"]
    is_boss = monster_entry.get("boss") is not None
    elite = monster_entry.get("elite", False)

    if is_boss:
        boss = monster_entry["boss"]
        hp = 180 + level * 42
        atk = 16 + level * 3
        return {
            "name": boss["name"],
            "level": level,
            "hp": hp,
            "max_hp": hp,
            "attack": atk,
            "exp": mob_exp(level) * 5,
            "drops": list(boss["drops"]),
            "is_boss": True,
            "elite": False,
            "reward_min": boss["dizens"][0],
            "reward_max": boss["dizens"][1],
        }

    zone = get_zone(zone_id)
    hp = 40 + level * 22
    atk = 5 + level * 2
    exp = mob_exp(level, elite)
    reward_min = 4 + level * 2
    reward_max = 7 + level * 3

    if elite:
        hp *= 5
        atk *= 3
        reward_min *= 10
        reward_max *= 10

    return {
        "name": monster_entry["name"],
        "level": level,
        "hp": hp,
        "max_hp": hp,
        "attack": atk,
        "exp": exp,
        "drops": list(zone["loot"] if zone else []),
        "is_boss": False,
        "elite": elite,
        "reward_min": reward_min,
        "reward_max": reward_max,
    }
