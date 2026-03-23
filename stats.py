from config import ARMOR_SLOTS, DODGE_UPGRADES, MAX_LEVEL, UPGRADE_BONUSES
from data import SET_BONUSES
from models import GameState, Player


def exp_needed_for_next(level: int) -> int:
    return 80 * level + 40 * (level * level)


def mob_exp(level: int, elite: bool = False) -> int:
    base = max(4, level * level + level * 3)
    return base * 10 if elite else base


def current_weapon(player: Player):
    if player.equipped_weapon_index is None:
        return None
    if 0 <= player.equipped_weapon_index < len(player.weapon_inventory):
        return player.weapon_inventory[player.equipped_weapon_index]
    player.equipped_weapon_index = None
    return None


def current_armor_piece(player: Player, slot: str):
    idx = player.equipped_armor.get(slot)
    if idx is None:
        return None
    if 0 <= idx < len(player.armor_inventory):
        gear = player.armor_inventory[idx]
        if gear.slot == slot:
            return gear
    player.equipped_armor[slot] = None
    return None


def set_bonus(player: Player) -> dict:
    tiers = []
    for slot in ARMOR_SLOTS:
        piece = current_armor_piece(player, slot)
        if piece:
            tiers.append(piece.tier_id)
    if len(tiers) == 5 and len(set(tiers)) == 1:
        return SET_BONUSES.get(tiers[0], {"attack": 0, "armor": 0})
    return {"attack": 0, "armor": 0}


def calc_weapon_bonus(player: Player) -> int:
    weapon = current_weapon(player)
    if not weapon:
        return 0
    mult = UPGRADE_BONUSES.get(weapon.upgrade, 0)
    return weapon.base_stat + int((player.attack + weapon.base_stat) * mult)


def calc_armor_bonus(player: Player) -> int:
    total = 0
    for slot in ARMOR_SLOTS:
        armor = current_armor_piece(player, slot)
        if armor is None:
            continue
        mult = UPGRADE_BONUSES.get(armor.upgrade, 0)
        total += armor.base_stat + int((player.armor + armor.base_stat) * mult)
    return total


def current_dodge(player: Player) -> int:
    boots = current_armor_piece(player, "boots")
    bonus = DODGE_UPGRADES.get(boots.upgrade, 0) if boots else 0
    return player.dodge + bonus


def total_attack(player: Player) -> int:
    return player.attack + calc_weapon_bonus(player) + set_bonus(player)["attack"]


def total_armor(player: Player) -> int:
    return player.armor + calc_armor_bonus(player) + set_bonus(player)["armor"]


def level_up(player: Player, game: GameState, add_log_fn) -> None:
    while player.level < MAX_LEVEL and player.exp >= exp_needed_for_next(player.level):
        player.exp -= exp_needed_for_next(player.level)
        player.level += 1
        player.max_hp += 12
        player.hp = player.max_hp
        player.attack += 2
        player.armor += 1
        player.crit += 1
        next_req = exp_needed_for_next(player.level) if player.level < MAX_LEVEL else "MAX"
        add_log_fn(game, f"Новый уровень: {player.level}. До следующего: {next_req} exp.")
