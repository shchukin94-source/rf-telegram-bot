import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from config import ARMOR_SLOTS
from models import GameState, Gear, Player

SAVE_FILE = Path("games.json")
BACKUP_FILE = Path("games_backup.json")


def save_games(user_games: Dict[int, GameState]) -> None:
    payload = {str(uid): asdict(game) for uid, game in user_games.items()}

    if SAVE_FILE.exists():
        try:
            shutil.copyfile(SAVE_FILE, BACKUP_FILE)
        except Exception:
            pass

    SAVE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_player(player_data: dict) -> Player:
    player = Player(
        race_name=player_data.get("race_name", "Неизвестно"),
        class_name=player_data.get("class_name", "Неизвестно"),
        level=player_data.get("level", 1),
        exp=player_data.get("exp", 0),
        max_hp=player_data.get("max_hp", 50),
        hp=player_data.get("hp", player_data.get("max_hp", 50)),
        attack=player_data.get("attack", 5),
        armor=player_data.get("armor", 1),
        crit=player_data.get("crit", 0),
        dodge=player_data.get("dodge", 0),
        dizens=player_data.get("dizens", 0),
        banks=player_data.get("banks", 0),
        talics_ignorance=player_data.get("talics_ignorance", 0),
        talics_protection=player_data.get("talics_protection", 0),
        talics_grace=player_data.get("talics_grace", 0),
        loot_count=player_data.get("loot_count", 0),
        clears=player_data.get("clears", 0),
        components=player_data.get("components", 0),
        rare_ore=player_data.get("rare_ore", 0),
        ancient_containers=player_data.get("ancient_containers", 0),
        enhancement_cores=player_data.get("enhancement_cores", 0),
        absolute_talics=player_data.get("absolute_talics", 0),
        weapon_upgrade_buff_active=player_data.get("weapon_upgrade_buff_active", False),
    )

    player.weapon_inventory = [
        Gear(**x) for x in player_data.get("weapon_inventory", [])
    ]
    player.armor_inventory = [
        Gear(**x) for x in player_data.get("armor_inventory", [])
    ]

    player.equipped_weapon_index = player_data.get("equipped_weapon_index")

    equipped_armor = player_data.get("equipped_armor", {})
    player.equipped_armor = {
        slot: equipped_armor.get(slot) for slot in ARMOR_SLOTS
    }

    return player


def load_games() -> Dict[int, GameState]:
    user_games: Dict[int, GameState] = {}

    if not SAVE_FILE.exists():
        return user_games

    try:
        raw = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        if BACKUP_FILE.exists():
            raw = json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
        else:
            return user_games

    for uid, game_data in raw.items():
        player_data = game_data.get("player")
        player = _build_player(player_data) if player_data else None

        user_games[int(uid)] = GameState(
            stage=game_data.get("stage", "menu"),
            selected_race=game_data.get("selected_race"),
            selected_class=game_data.get("selected_class"),
            player=player,
            current_zone_id=game_data.get("current_zone_id"),
            selected_monster_page=game_data.get("selected_monster_page", 0),
            selected_monster_index=game_data.get("selected_monster_index"),
            enemy=game_data.get("enemy"),
            battle_count=game_data.get("battle_count", 0),
            dead_until_ts=game_data.get("dead_until_ts"),
            equipment_page_weapon=game_data.get("equipment_page_weapon", 0),
            market_weapon_page=game_data.get("market_weapon_page", 0),
            salvage_page=game_data.get("salvage_page", 0),
            stage_page=game_data.get("stage_page", 0),
            equipment_page_armor=game_data.get(
                "equipment_page_armor",
                {slot: 0 for slot in ARMOR_SLOTS},
            ),
            log=game_data.get(
                "log",
                [
                    "Добро пожаловать в RF Online: Text Raid.",
                    "Сохранение было загружено через безопасную миграцию.",
                ],
            ),
        )

    return user_games
