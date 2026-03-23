import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from config import ARMOR_SLOTS
from models import GameState, Gear, Player

SAVE_FILE = Path("games.json")


def save_games(user_games: Dict[int, GameState]) -> None:
    payload = {str(uid): asdict(game) for uid, game in user_games.items()}
    SAVE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_games() -> Dict[int, GameState]:
    user_games: Dict[int, GameState] = {}

    if not SAVE_FILE.exists():
        return user_games

    raw = json.loads(SAVE_FILE.read_text(encoding="utf-8"))

    for uid, game_data in raw.items():
        player_data = game_data.get("player")
        player = None

        if player_data:
            player = Player(**player_data)
            player.weapon_inventory = [
                Gear(**x) for x in player_data.get("weapon_inventory", [])
            ]
            player.armor_inventory = [
                Gear(**x) for x in player_data.get("armor_inventory", [])
            ]
            if not player.equipped_armor:
                player.equipped_armor = {slot: None for slot in ARMOR_SLOTS}

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
            equipment_page_armor=game_data.get(
                "equipment_page_armor",
                {slot: 0 for slot in ARMOR_SLOTS},
            ),
            log=game_data.get("log", []),
        )

    return user_games
