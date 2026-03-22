import html
import json
import logging
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
SAVE_FILE = Path("games.json")
MAX_LEVEL = 50
ITEMS_PER_PAGE = 5
DROP_GEAR_CHANCE = 7
BOSS_CHANCE = 8
ARMOR_SLOTS = ["head", "torso", "legs", "arms", "boots"]
ARMOR_SLOT_NAMES = {
    "head": "Голова",
    "torso": "Торс",
    "legs": "Штаны",
    "arms": "Руки",
    "boots": "Тапки",
}
DODGE_UPGRADES = {0: 0, 1: 5, 2: 10, 3: 15, 4: 20, 5: 30, 6: 45, 7: 60}
UPGRADE_CHANCES = {
    0: {"next": 1, "chance": 90},
    1: {"next": 2, "chance": 80},
    2: {"next": 3, "chance": 65},
    3: {"next": 4, "chance": 30},
    4: {"next": 5, "chance": 15},
    5: {"next": 6, "chance": 10},
    6: {"next": 7, "chance": 7},
}
UPGRADE_BONUSES = {0: 0.0, 1: 0.05, 2: 0.25, 3: 0.50, 4: 0.70, 5: 0.90, 6: 1.35, 7: 2.00}

LOCATION_MONSTERS = {
    "alliance_outpost": [
        {"name": "Флем Детеныш", "level": 1},
        {"name": "Вертобот", "level": 2},
        {"name": "Клаан Детеныш", "level": 3},
        {"name": "Флем", "level": 4},
        {"name": "Вонючий Жук", "level": 5},
        {"name": "Стригой", "level": 6},
        {"name": "Армированный Вертобот", "level": 7},
        {"name": "Молодой Клаан", "level": 8},
        {"name": "Молодой Саблезуб", "level": 9},
        {"name": "Золотой Стригой Опытный", "level": 10},
        {"name": "Молотограв", "level": 11},
        {"name": "Ратозверь", "level": 12},
        {"name": "Саблезуб", "level": 13},
        {"name": "Клаан", "level": 14},
        {"name": "Молодой Раптор", "level": 15},
        {"name": "Змееголов Метатель", "level": 16},
        {"name": "Синий Молотоглав", "level": 17},
        {"name": "Аргол", "level": 18},
        {"name": "Трицератопс", "level": 19},
        {"name": "Скорпион", "level": 20},
        {"name": "Красный Раптор", "level": 21},
    ],
    "haram_colony": [
        {"name": "Штурмовой Дрон", "level": 22},
        {"name": "Клаан Берсерк", "level": 23},
        {"name": "Ядовитый Раптор", "level": 24},
        {"name": "Скарабей Харам", "level": 25},
        {"name": "Гвардеец Харам", "level": 26},
        {"name": "Костяной Стригой", "level": 27},
        {"name": "Мясник Колонии", "level": 28},
        {"name": "Пустынный Аргол", "level": 29},
        {"name": "Крушитель Харам", "level": 30},
    ],
    "numerus_colony": [
        {"name": "Охотник Нумерус", "level": 31},
        {"name": "Черный Клаан", "level": 32},
        {"name": "Резчик Пустошей", "level": 33},
        {"name": "Титан Нумерус", "level": 34},
        {"name": "Жало Сектора", "level": 35},
        {"name": "Разъяренный Аргол", "level": 36},
        {"name": "Громорог", "level": 37},
        {"name": "Пожиратель Колонии", "level": 38},
        {"name": "Стальной Раптор", "level": 39},
        {"name": "Боевой Скорпион", "level": 40},
    ],
    "krag_mines": [
        {"name": "Шахтный Разоритель", "level": 41},
        {"name": "Глубинный Крушитель", "level": 42},
        {"name": "Пещерный Тиран", "level": 43},
        {"name": "Коготь Шахт", "level": 44},
        {"name": "Леон Страж", "level": 45},
        {"name": "Безумный Трицератопс", "level": 46},
        {"name": "Горный Палач", "level": 47},
        {"name": "Каменный Раптор", "level": 48},
        {"name": "Глубинный Скорпион", "level": 49},
        {"name": "Повелитель Шахт", "level": 50},
    ],
}

ZONES = [
    {
        "id": "alliance_outpost",
        "name": "Аванпост Альянса",
        "text": "Стартовая территория с мобами 1-21 уровня.",
        "loot": ["необработанная руда", "банка HP", "Talic Fragment"],
        "bosses": [
            {"name": "Командир Аванпоста", "level": 15, "drops": ["талик невежества", "талик покровительства", "талик грации", "ящик офицера"], "dizens": [35, 55]},
            {"name": "Зверь Альянса", "level": 21, "drops": ["талик невежества", "талик грации", "редкий контейнер аванпоста"], "dizens": [45, 70]},
        ],
    },
    {
        "id": "haram_colony",
        "name": "Колония Харам",
        "text": "Средняя зона с мобами 22-30 уровня.",
        "loot": ["Blue Ore", "банка HP", "Talic Crystal", "анимус-чип"],
        "bosses": [
            {"name": "Хранитель Харам", "level": 27, "drops": ["талик невежества", "талик покровительства", "талик грации", "контейнер Харам"], "dizens": [70, 100]},
            {"name": "Кровавый Берсерк", "level": 30, "drops": ["талик невежества", "талик грации", "ядро Харам"], "dizens": [80, 115]},
        ],
    },
    {
        "id": "numerus_colony",
        "name": "Колония Нумерус",
        "text": "Тяжёлая зона с мобами 31-40 уровня.",
        "loot": ["Red Ore", "банка HP", "Talic Crystal", "Intense Part"],
        "bosses": [
            {"name": "Тиран Нумерус", "level": 38, "drops": ["талик невежества", "талик покровительства", "талик грации", "Leon Core"], "dizens": [120, 170]},
            {"name": "Палач Нумерус", "level": 40, "drops": ["талик покровительства", "талик грации", "сундук Нумерус"], "dizens": [130, 185]},
        ],
    },
    {
        "id": "krag_mines",
        "name": "Краговые Шахты",
        "text": "Эндгейм зона с мобами 41-50 уровня.",
        "loot": ["Golden Ore", "банка HP", "Rare Box", "Leon Fragment"],
        "bosses": [
            {"name": "Король Шахт", "level": 50, "drops": ["талик невежества", "талик покровительства", "талик грации", "Leon Relic"], "dizens": [200, 280]},
            {"name": "Леон Надзиратель", "level": 49, "drops": ["талик невежества", "талик грации", "набор шахт"], "dizens": [180, 250]},
        ],
    },
]

RACES = [
    {"id": "bellato", "name": "Беллато", "desc": "Сбалансированная раса с хорошей выживаемостью и запасом дизен.", "stats": {"max_hp": 70, "attack": 7, "armor": 2, "crit": 8, "dizens": 30}},
    {"id": "cora", "name": "Кора", "desc": "Больше урона и выше шанс критического удара.", "stats": {"max_hp": 62, "attack": 9, "armor": 1, "crit": 15, "dizens": 25}},
    {"id": "accretia", "name": "Акретия", "desc": "Тяжелая броня и высокий запас HP.", "stats": {"max_hp": 78, "attack": 8, "armor": 3, "crit": 6, "dizens": 22}},
]

CLASSES = [
    {"id": "warrior", "name": "Штурмовик", "desc": "Больше HP и брони.", "bonus": {"max_hp": 12, "armor": 2, "attack": 1, "crit": 0, "dizens": 0, "banks": 1}},
    {"id": "ranger", "name": "Стрелок", "desc": "Больше урона и критов.", "bonus": {"max_hp": 0, "armor": 0, "attack": 3, "crit": 8, "dizens": 0, "banks": 0}},
    {"id": "specialist", "name": "Специалист", "desc": "Лучше экономика и восстановление.", "bonus": {"max_hp": 4, "armor": 1, "attack": 0, "crit": 3, "dizens": 12, "banks": 2}},
]

GEAR_TIERS = [
    {"id": "normal", "name": "обычный", "weapon_mult": 1.0, "armor_mult": 1.0, "weight": 66},
    {"id": "int", "name": "инт", "weapon_mult": 1.28, "armor_mult": 1.25, "weight": 22},
    {"id": "type_c", "name": "тип с", "weapon_mult": 1.68, "armor_mult": 1.62, "weight": 9},
    {"id": "leon", "name": "леон", "weapon_mult": 2.25, "armor_mult": 2.1, "weight": 3},
]

WEAPON_NAMES = ["Нож Flym", "Клинок Wing", "Пускатель Digger", "Копьё Flem", "Разрушитель Crawler", "Леон Блейд"]
ARMOR_NAMES = {
    "head": ["Шлем Разведчика", "Маска Колонии", "Шахтёрский Шлем", "Флем Хелм", "Леон Хелм"],
    "torso": ["Бронекуртка", "Тактический Доспех", "Шахтёрская Броня", "Флем Панцирь", "Леон Армор"],
    "legs": ["Набедренники", "Штаны Колонии", "Шахтёрские Поножи", "Флем Легсы", "Леон Легсы"],
    "arms": ["Перчатки Бойца", "Наручи Колонии", "Шахтёрские Руки", "Флем Гаунтлеты", "Леон Гловз"],
    "boots": ["Полевые Тапки", "Сапоги Колонии", "Шахтёрские Ботинки", "Флем Бутсы", "Леон Бутсы"],
}
SET_BONUSES = {
    "normal": {"attack": 0, "armor": 0},
    "int": {"attack": 2, "armor": 2},
    "type_c": {"attack": 5, "armor": 4},
    "leon": {"attack": 9, "armor": 7},
}
CRAFT_RECIPES = {
    "weapon": {"components": 25, "dizens": 40},
    "armor": {"components": 18, "dizens": 30},
}


@dataclass
class Gear:
    id: str
    name: str
    slot: str
    level: int
    tier_id: str
    tier_name: str
    base_stat: int
    upgrade: int = 0


@dataclass
class Player:
    race_name: str
    class_name: str
    level: int
    exp: int
    max_hp: int
    hp: int
    attack: int
    armor: int
    crit: int
    dodge: int
    dizens: int
    banks: int
    talics_ignorance: int = 0
    talics_protection: int = 0
    talics_grace: int = 0
    loot_count: int = 0
    clears: int = 0
    components: int = 0
    weapon_inventory: List[Gear] = field(default_factory=list)
    armor_inventory: List[Gear] = field(default_factory=list)
    equipped_weapon_index: Optional[int] = None
    equipped_armor: Dict[str, Optional[int]] = field(default_factory=lambda: {slot: None for slot in ARMOR_SLOTS})


@dataclass
class GameState:
    stage: str = "menu"
    selected_race: Optional[str] = None
    selected_class: Optional[str] = None
    player: Optional[Player] = None
    current_zone_id: Optional[str] = None
    selected_monster_page: int = 0
    selected_monster_index: Optional[int] = None
    enemy: Optional[dict] = None
    battle_count: int = 0
    mission: Optional[dict] = None
    mission_progress: int = 0
    mission_claimed: bool = False
    ended: bool = False
    win: bool = False
    equipment_page_weapon: int = 0
    equipment_page_armor: Dict[str, int] = field(default_factory=lambda: {slot: 0 for slot in ARMOR_SLOTS})
    log: List[str] = field(default_factory=lambda: [
        "Добро пожаловать в RF Online: Text Raid.",
        "Теперь можно выбирать конкретного монстра по уровню после выбора локации.",
    ])


USER_GAMES: Dict[int, GameState] = {}


def exp_needed_for_next(level: int) -> int:
    return 80 * level + 40 * (level * level)


def mob_exp(level: int) -> int:
    return max(4, level * level + level * 3)


def save_games() -> None:
    payload = {str(uid): asdict(game) for uid, game in USER_GAMES.items()}
    SAVE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_games() -> None:
    if not SAVE_FILE.exists():
        return
    raw = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    for uid, game_data in raw.items():
        player_data = game_data.get("player")
        player = None
        if player_data:
            player = Player(**player_data)
            player.weapon_inventory = [Gear(**x) for x in player_data.get("weapon_inventory", [])]
            player.armor_inventory = [Gear(**x) for x in player_data.get("armor_inventory", [])]
            if not player.equipped_armor:
                player.equipped_armor = {slot: None for slot in ARMOR_SLOTS}
        USER_GAMES[int(uid)] = GameState(
            stage=game_data.get("stage", "menu"),
            selected_race=game_data.get("selected_race"),
            selected_class=game_data.get("selected_class"),
            player=player,
            current_zone_id=game_data.get("current_zone_id"),
            selected_monster_page=game_data.get("selected_monster_page", 0),
            selected_monster_index=game_data.get("selected_monster_index"),
            enemy=game_data.get("enemy"),
            battle_count=game_data.get("battle_count", 0),
            mission=game_data.get("mission"),
            mission_progress=game_data.get("mission_progress", 0),
            mission_claimed=game_data.get("mission_claimed", False),
            ended=game_data.get("ended", False),
            win=game_data.get("win", False),
            equipment_page_weapon=game_data.get("equipment_page_weapon", 0),
            equipment_page_armor=game_data.get("equipment_page_armor", {slot: 0 for slot in ARMOR_SLOTS}),
            log=game_data.get("log", []),
        )


def get_zone(zone_id: Optional[str]) -> Optional[dict]:
    if not zone_id:
        return None
    return next((z for z in ZONES if z["id"] == zone_id), None)


def get_race(race_id: str) -> dict:
    return next(x for x in RACES if x["id"] == race_id)


def get_class(class_id: str) -> dict:
    return next(x for x in CLASSES if x["id"] == class_id)


def get_game(user_id: int) -> GameState:
    if user_id not in USER_GAMES:
        USER_GAMES[user_id] = GameState()
    return USER_GAMES[user_id]


def esc(text: str) -> str:
    return html.escape(str(text))


def add_log(game: GameState, *lines: str) -> None:
    game.log.extend(lines)
    game.log = game.log[-20:]


def current_weapon(player: Player) -> Optional[Gear]:
    if player.equipped_weapon_index is None:
        return None
    if 0 <= player.equipped_weapon_index < len(player.weapon_inventory):
        return player.weapon_inventory[player.equipped_weapon_index]
    player.equipped_weapon_index = None
    return None


def current_armor_piece(player: Player, slot: str) -> Optional[Gear]:
    idx = player.equipped_armor.get(slot)
    if idx is None:
        return None
    if 0 <= idx < len(player.armor_inventory):
        gear = player.armor_inventory[idx]
        if gear.slot == slot:
            return gear
    player.equipped_armor[slot] = None
    return None


def set_bonus(player: Player) -> Dict[str, int]:
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


def maybe_gear_drop(enemy_level: int, is_boss: bool) -> Optional[Gear]:
    chance = 100 if is_boss else DROP_GEAR_CHANCE
    if random.randint(1, 100) > chance:
        return None
    slot = random.choice(["weapon"] + ARMOR_SLOTS)
    return make_gear(slot, enemy_level, is_boss)


def selected_monsters_for_zone(zone_id: str) -> List[dict]:
    bosses = []
    zone = get_zone(zone_id)
    if zone:
        for boss in zone["bosses"]:
            bosses.append({"name": f"[БОСС] {boss['name']}", "level": boss["level"], "boss": boss})
    monsters = [{**m, "boss": None} for m in LOCATION_MONSTERS.get(zone_id, [])]
    return monsters + bosses


def generate_enemy(zone_id: str, monster_entry: dict) -> dict:
    level = monster_entry["level"]
    is_boss = monster_entry.get("boss") is not None
    if is_boss:
        boss = monster_entry["boss"]
        hp = 120 + level * 36
        atk = 12 + level * 3
        return {
            "name": boss["name"],
            "level": level,
            "hp": hp,
            "max_hp": hp,
            "attack": atk,
            "exp": mob_exp(level) * 4,
            "drops": list(boss["drops"]),
            "is_boss": True,
            "reward_min": boss["dizens"][0],
            "reward_max": boss["dizens"][1],
        }
    zone = get_zone(zone_id)
    hp = 30 + level * 18
    atk = 4 + level * 2
    return {
        "name": monster_entry["name"],
        "level": level,
        "hp": hp,
        "max_hp": hp,
        "attack": atk,
        "exp": mob_exp(level),
        "drops": list(zone["loot"] if zone else []),
        "is_boss": False,
        "reward_min": 3 + level * 2,
        "reward_max": 6 + level * 3,
    }


def level_up(player: Player, game: GameState) -> None:
    while player.level < MAX_LEVEL and player.exp >= exp_needed_for_next(player.level):
        player.exp -= exp_needed_for_next(player.level)
        player.level += 1
        player.max_hp += 12
        player.hp = player.max_hp
        player.attack += 2
        player.armor += 1
        player.crit += 1
        add_log(game, f"Новый уровень: {player.level}. Нужно {exp_needed_for_next(player.level) if player.level < MAX_LEVEL else 'MAX'} опыта до следующего.")


def paged_items(items: List, page: int) -> List:
    start = page * ITEMS_PER_PAGE
    return items[start:start + ITEMS_PER_PAGE]


def salvage_reward(gear: Gear) -> int:
    return max(2, gear.level + gear.base_stat + gear.upgrade * 2)


def craft_item(player: Player, slot: str, level: int) -> Optional[Gear]:
    recipe = CRAFT_RECIPES["weapon" if slot == "weapon" else "armor"]
    if player.components < recipe["components"] or player.dizens < recipe["dizens"]:
        return None
    player.components -= recipe["components"]
    player.dizens -= recipe["dizens"]
    return make_gear(slot, level, False)


def render_text(game: GameState) -> str:
    lines: List[str] = ["<b>RF Online: Text Raid</b>"]
    if not game.player:
        lines.append("Выбери расу и класс, затем начни кампанию.")
    else:
        p = game.player
        weapon = current_weapon(p)
        set_info = set_bonus(p)
        armor_lines = []
        for slot in ARMOR_SLOTS:
            piece = current_armor_piece(p, slot)
            piece_name = f"{piece.name} +{piece.upgrade}" if piece else "нет"
            armor_lines.append(f"{ARMOR_SLOT_NAMES[slot]}: {piece_name}")
        lines.append(
            f"<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}/{MAX_LEVEL}\n"
            f"HP: {p.hp}/{p.max_hp}\n"
            f"Базовая атака: {p.attack} | Общая атака: {total_attack(p)}\n"
            f"Базовая броня: {p.armor} | Общая броня: {total_armor(p)}\n"
            f"Крит: {p.crit}% | Уворот: {current_dodge(p)}%\n"
            f"Дизены: {p.dizens} | Банки: {p.banks} | Компоненты: {p.components}\n"
            f"Талики невежества: {p.talics_ignorance} | Талики покровительства: {p.talics_protection} | Талики грации: {p.talics_grace}\n"
            f"Оружие: {esc(f'{weapon.name} +{weapon.upgrade}' if weapon else 'нет')}\n"
            f"{esc(chr(10).join(armor_lines))}\n"
            f"Бонус набора: ATK +{set_info['attack']}, ARM +{set_info['armor']}\n"
            f"Вылазки: {p.clears} | Лут: {p.loot_count}\n"
            f"Опыт: {p.exp}/{exp_needed_for_next(p.level) if p.level < MAX_LEVEL else 'MAX'}"
        )
    zone = get_zone(game.current_zone_id)
    if zone:
        lines.append(f"<b>Локация:</b> {esc(zone['name'])}\n{esc(zone['text'])}")
    if game.current_zone_id and game.stage == "zone_select":
        monsters = selected_monsters_for_zone(game.current_zone_id)
        page_items = paged_items(monsters, game.selected_monster_page)
        monster_text = "\n".join([f"{idx + 1}. {m['name']} ({m['level']})" for idx, m in enumerate(page_items, start=game.selected_monster_page * ITEMS_PER_PAGE)])
        lines.append(f"<b>Выбор монстра:</b> стр. {game.selected_monster_page + 1}\n{esc(monster_text or 'нет монстров')}" )
    if game.enemy:
        lines.append(
            f"<b>Враг:</b> {esc(game.enemy['name'])} | lvl {game.enemy['level']}\n"
            f"HP: {game.enemy['hp']}/{game.enemy['max_hp']} | EXP: {game.enemy['exp']}\n"
            f"Типичный дроп: {esc(', '.join(game.enemy['drops']))}\n"
            f"Тип: {'босс' if game.enemy['is_boss'] else 'обычный моб'}"
        )
    if game.player and game.player.weapon_inventory:
        page = game.equipment_page_weapon
        items = paged_items(game.player.weapon_inventory, page)
        inv = "\n".join(
            f"{'✅ ' if game.player.equipped_weapon_index == game.player.weapon_inventory.index(g) else ''}{game.player.weapon_inventory.index(g) + 1}. {g.name} +{g.upgrade} (atk +{g.base_stat})"
            for g in items
        ) or "нет"
        lines.append(f"<b>Оружие:</b> стр. {page + 1}\n" + esc(inv))
    if game.player and game.player.armor_inventory:
        sections = []
        for slot in ARMOR_SLOTS:
            slot_items = [g for g in game.player.armor_inventory if g.slot == slot]
            page = game.equipment_page_armor.get(slot, 0)
            items = paged_items(slot_items, page)
            inv = "\n".join(
                f"{'✅ ' if game.player.equipped_armor.get(slot) == game.player.armor_inventory.index(g) else ''}{game.player.armor_inventory.index(g) + 1}. {g.name} +{g.upgrade}"
                for g in items
            ) or "нет"
            sections.append(f"{ARMOR_SLOT_NAMES[slot]} стр. {page + 1}:\n{inv}")
        lines.append("<b>Броня:</b>\n" + esc("\n\n".join(sections)))
    lines.append("<b>Журнал:</b>\n" + esc("\n".join(game.log[-8:])))
    return "\n\n".join(lines)


def render_keyboard(game: GameState) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    if not game.player:
        rows.append([InlineKeyboardButton(r["name"], callback_data=f"race:{r['id']}") for r in RACES])
        rows.append([InlineKeyboardButton(c["name"], callback_data=f"class:{c['id']}") for c in CLASSES])
        rows.append([InlineKeyboardButton("Начать кампанию", callback_data="start_game")])
        return InlineKeyboardMarkup(rows)
    if game.ended:
        rows.append([InlineKeyboardButton("Начать заново", callback_data="reset")])
        return InlineKeyboardMarkup(rows)
    if game.stage == "hub":
        zone_buttons = [InlineKeyboardButton(z["name"], callback_data=f"zone:{z['id']}" ) for z in ZONES]
        for i in range(0, len(zone_buttons), 2):
            rows.append(zone_buttons[i:i + 2])
        rows.append([
            InlineKeyboardButton("Отдохнуть", callback_data="rest"),
            InlineKeyboardButton("Снаряжение", callback_data="equipment"),
        ])
        rows.append([
            InlineKeyboardButton("Крафт оружия", callback_data="craft_weapon"),
            InlineKeyboardButton("Крафт брони", callback_data="craft_armor"),
        ])
        return InlineKeyboardMarkup(rows)
    if game.stage == "zone_select":
        monsters = selected_monsters_for_zone(game.current_zone_id)
        page_items = paged_items(monsters, game.selected_monster_page)
        for idx, monster in enumerate(page_items, start=game.selected_monster_page * ITEMS_PER_PAGE):
            rows.append([InlineKeyboardButton(f"{monster['name']} ({monster['level']})", callback_data=f"pick_monster:{idx}")])
        rows.append([
            InlineKeyboardButton("◀️", callback_data="monster_page_prev"),
            InlineKeyboardButton("▶️", callback_data="monster_page_next"),
        ])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)
    if game.stage == "combat":
        rows.append([
            InlineKeyboardButton("Атаковать", callback_data="attack"),
            InlineKeyboardButton("Банка", callback_data="bank"),
        ])
        rows.append([InlineKeyboardButton("Отступить", callback_data="back_zone_select")])
        return InlineKeyboardMarkup(rows)
    if game.stage == "equipment":
        weapon_items = paged_items(game.player.weapon_inventory, game.equipment_page_weapon)
        for gear in weapon_items:
            idx = game.player.weapon_inventory.index(gear)
            rows.append([InlineKeyboardButton(f"Надеть оружие {idx + 1}", callback_data=f"equip_weapon:{idx}")])
        rows.append([
            InlineKeyboardButton("◀️ Оружие", callback_data="weapon_page_prev"),
            InlineKeyboardButton("Оружие ▶️", callback_data="weapon_page_next"),
        ])
        for slot in ARMOR_SLOTS:
            slot_items = [g for g in game.player.armor_inventory if g.slot == slot]
            items = paged_items(slot_items, game.equipment_page_armor.get(slot, 0))
            for gear in items:
                idx = game.player.armor_inventory.index(gear)
                rows.append([InlineKeyboardButton(f"{ARMOR_SLOT_NAMES[slot]} {idx + 1}", callback_data=f"equip_armor:{idx}")])
            rows.append([
                InlineKeyboardButton(f"◀️ {ARMOR_SLOT_NAMES[slot]}", callback_data=f"armor_page_prev:{slot}"),
                InlineKeyboardButton(f"{ARMOR_SLOT_NAMES[slot]} ▶️", callback_data=f"armor_page_next:{slot}"),
            ])
        rows.append([
            InlineKeyboardButton("Точить оружие", callback_data="upgrade_weapon"),
            InlineKeyboardButton("Точить броню", callback_data="upgrade_armor"),
        ])
        rows.append([
            InlineKeyboardButton("Точить тапки грацией", callback_data="upgrade_boots_grace"),
            InlineKeyboardButton("Разобрать оружие", callback_data="salvage_weapon"),
        ])
        rows.append([
            InlineKeyboardButton("Разобрать броню", callback_data="salvage_armor"),
            InlineKeyboardButton("На базу", callback_data="back_hub"),
        ])
        return InlineKeyboardMarkup(rows)
    rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
    return InlineKeyboardMarkup(rows)


async def send_or_edit(update: Update, text: str, keyboard: InlineKeyboardMarkup) -> None:
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        assert update.effective_message
        await update.effective_message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = get_game(update.effective_user.id)
    await send_or_edit(update, render_text(game), render_keyboard(game))


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    USER_GAMES[update.effective_user.id] = GameState()
    save_games()
    game = USER_GAMES[update.effective_user.id]
    await send_or_edit(update, render_text(game), render_keyboard(game))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start — открыть игру\n"
        "/reset — сбросить прогресс\n"
        "/help — помощь\n\n"
        "Теперь после выбора локации можно выбирать конкретного моба по уровню и фармить его."
    )
    await update.effective_message.reply_text(text)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    game = get_game(user_id)
    data = query.data

    if data == "reset":
        USER_GAMES[user_id] = GameState()
        game = USER_GAMES[user_id]

    elif data.startswith("race:"):
        game.selected_race = data.split(":", 1)[1]
        add_log(game, f"Выбрана раса: {get_race(game.selected_race)['name']}.")

    elif data.startswith("class:"):
        game.selected_class = data.split(":", 1)[1]
        add_log(game, f"Выбран класс: {get_class(game.selected_class)['name']}.")

    elif data == "start_game":
        if not game.selected_race or not game.selected_class:
            add_log(game, "Сначала выбери и расу, и класс.")
        else:
            race = get_race(game.selected_race)
            klass = get_class(game.selected_class)
            game.player = Player(
                race_name=race["name"],
                class_name=klass["name"],
                level=1,
                exp=0,
                max_hp=race["stats"]["max_hp"] + klass["bonus"]["max_hp"],
                hp=race["stats"]["max_hp"] + klass["bonus"]["max_hp"],
                attack=race["stats"]["attack"] + klass["bonus"]["attack"],
                armor=race["stats"]["armor"] + klass["bonus"]["armor"],
                crit=race["stats"]["crit"] + klass["bonus"]["crit"],
                dodge=0,
                dizens=race["stats"]["dizens"] + klass["bonus"]["dizens"],
                banks=2 + klass["bonus"]["banks"],
            )
            game.stage = "hub"
            game.log = [
                f"Ты выбрал расу {race['name']} и класс {klass['name']}.",
                race["desc"],
                klass["desc"],
                "Командование открыло доступ к локациям и ручному выбору мобов.",
            ]

    elif data.startswith("zone:") and game.player:
        zone_id = data.split(":", 1)[1]
        game.current_zone_id = zone_id
        game.stage = "zone_select"
        game.selected_monster_page = 0
        add_log(game, f"Локация: {get_zone(zone_id)['name']}. Теперь выбери конкретного монстра.")

    elif data == "monster_page_prev" and game.player:
        game.selected_monster_page = max(0, game.selected_monster_page - 1)

    elif data == "monster_page_next" and game.player and game.current_zone_id:
        monsters = selected_monsters_for_zone(game.current_zone_id)
        max_page = max(0, (len(monsters) - 1) // ITEMS_PER_PAGE)
        game.selected_monster_page = min(max_page, game.selected_monster_page + 1)

    elif data.startswith("pick_monster:") and game.player and game.current_zone_id:
        idx = int(data.split(":", 1)[1])
        monsters = selected_monsters_for_zone(game.current_zone_id)
        if 0 <= idx < len(monsters):
            game.selected_monster_index = idx
            game.enemy = generate_enemy(game.current_zone_id, monsters[idx])
            game.stage = "combat"
            add_log(game, f"Ты выбрал цель: {game.enemy['name']} lv.{game.enemy['level']}.")

    elif data == "attack" and game.player and game.enemy:
        crit = random.randint(1, 100) <= game.player.crit
        dmg = max(1, total_attack(game.player) + random.randint(0, 4) - game.enemy["level"])
        if crit:
            dmg *= 2
        game.enemy["hp"] -= dmg
        add_log(game, f"Ты наносишь {dmg} урона." + (" Критический удар!" if crit else ""))
        if game.enemy["hp"] <= 0:
            dizens_gain = random.randint(game.enemy["reward_min"], game.enemy["reward_max"])
            exp_gain = game.enemy["exp"]
            loot = random.choice(game.enemy["drops"])
            game.player.dizens += dizens_gain
            game.player.exp += exp_gain
            game.player.loot_count += 1
            game.player.clears += 1
            add_log(game, f"Враг повержен. Награда: {dizens_gain} дизен, {exp_gain} опыта, добыча: {loot}.")
            if loot == "талик невежества":
                game.player.talics_ignorance += 1
            elif loot == "талик покровительства":
                game.player.talics_protection += 1
            elif loot == "талик грации":
                game.player.talics_grace += 1
            else:
                if random.randint(1, 100) <= 3:
                    game.player.talics_ignorance += 1
                    add_log(game, "Доп. редкий дроп: талик невежества.")
                if random.randint(1, 100) <= 3:
                    game.player.talics_protection += 1
                    add_log(game, "Доп. редкий дроп: талик покровительства.")
                if random.randint(1, 100) <= 2:
                    game.player.talics_grace += 1
                    add_log(game, "Доп. редкий дроп: талик грации.")
            gear = maybe_gear_drop(game.enemy["level"], game.enemy["is_boss"])
            if gear:
                if gear.slot == "weapon":
                    game.player.weapon_inventory.append(gear)
                    add_log(game, f"Выпало оружие: {gear.name} +0.")
                else:
                    game.player.armor_inventory.append(gear)
                    add_log(game, f"Выпала броня ({ARMOR_SLOT_NAMES[gear.slot].lower()}): {gear.name} +0.")
            level_up(game.player, game)
            game.enemy = None
            game.stage = "zone_select"
        else:
            if random.randint(1, 100) <= current_dodge(game.player):
                add_log(game, f"Ты увернулся от атаки {game.enemy['name']}.")
            else:
                enemy_dmg = max(1, game.enemy["attack"] + random.randint(0, 4) - total_armor(game.player) // 3)
                game.player.hp -= enemy_dmg
                add_log(game, f"{game.enemy['name']} отвечает и наносит {enemy_dmg} урона.")
                if game.player.hp <= 0:
                    game.player.hp = 0
                    game.ended = True
                    game.stage = "end"
                    add_log(game, "Ты пал в бою. Прогресс сохранён.")

    elif data == "bank" and game.player:
        if game.player.banks > 0:
            game.player.banks -= 1
            heal = max(30, game.player.max_hp // 3)
            game.player.hp = min(game.player.max_hp, game.player.hp + heal)
            add_log(game, f"Ты используешь банку и восстанавливаешь {heal} HP.")
        else:
            add_log(game, "Банки закончились.")

    elif data == "rest" and game.player:
        game.player.hp = game.player.max_hp
        game.player.banks += 1
        add_log(game, "На базе ты полностью восстановил здоровье и получил 1 банку.")

    elif data == "equipment" and game.player:
        game.stage = "equipment"

    elif data.startswith("equip_weapon:") and game.player:
        idx = int(data.split(":", 1)[1])
        if 0 <= idx < len(game.player.weapon_inventory):
            game.player.equipped_weapon_index = idx
            add_log(game, f"Ты экипировал оружие: {game.player.weapon_inventory[idx].name} +{game.player.weaponInventory[idx].upgrade if False else game.player.weapon_inventory[idx].upgrade}.")

    elif data.startswith("equip_armor:") and game.player:
        idx = int(data.split(":", 1)[1])
        if 0 <= idx < len(game.player.armor_inventory):
            chosen = game.player.armor_inventory[idx]
            game.player.equipped_armor[chosen.slot] = idx
            add_log(game, f"Ты экипировал {ARMOR_SLOT_NAMES[chosen.slot].lower()}: {chosen.name} +{chosen.upgrade}.")

    elif data == "upgrade_weapon" and game.player:
        gear = current_weapon(game.player)
        if gear is None:
            add_log(game, "Сначала экипируй оружие.")
        elif game.player.talics_ignorance <= 0:
            add_log(game, "У тебя нет талика невежества.")
        elif gear.upgrade >= 7:
            add_log(game, "Оружие уже заточено на максимум +7.")
        else:
            rule = UPGRADE_CHANCES[gear.upgrade]
            game.player.talics_ignorance -= 1
            if random.randint(1, 100) <= rule["chance"]:
                gear.upgrade = rule["next"]
                add_log(game, f"Успех. {gear.name} теперь +{gear.upgrade}.")
            else:
                add_log(game, f"Неудача. {gear.name} осталось на +{gear.upgrade}.")

    elif data == "upgrade_armor" and game.player:
        upgraded = False
        for slot in ["head", "torso", "legs", "arms"]:
            piece = current_armor_piece(game.player, slot)
            if piece:
                if game.player.talics_protection <= 0:
                    add_log(game, "У тебя нет талика покровительства.")
                elif piece.upgrade >= 7:
                    add_log(game, f"{piece.name} уже на +7.")
                else:
                    rule = UPGRADE_CHANCES[piece.upgrade]
                    game.player.talics_protection -= 1
                    if random.randint(1, 100) <= rule["chance"]:
                        piece.upgrade = rule["next"]
                        add_log(game, f"Успех. {piece.name} теперь +{piece.upgrade}.")
                    else:
                        add_log(game, f"Неудача. {piece.name} осталось на +{piece.upgrade}.")
                upgraded = True
                break
        if not upgraded:
            add_log(game, "Сначала экипируй голову/торс/штаны/руки.")

    elif data == "upgrade_boots_grace" and game.player:
        boots = current_armor_piece(game.player, "boots")
        if boots is None:
            add_log(game, "Сначала экипируй тапки.")
        elif game.player.talics_grace <= 0:
            add_log(game, "У тебя нет талика грации.")
        elif boots.upgrade >= 7:
            add_log(game, "Тапки уже заточены на максимум +7.")
        else:
            rule = UPGRADE_CHANCES[boots.upgrade]
            game.player.talics_grace -= 1
            if random.randint(1, 100) <= rule["chance"]:
                boots.upgrade = rule["next"]
                add_log(game, f"Успех. {boots.name} теперь +{boots.upgrade}. Уворот: {DODGE_UPGRADES[boots.upgrade]}%.")
            else:
                add_log(game, f"Неудача. {boots.name} осталось на +{boots.upgrade}.")

    elif data == "salvage_weapon" and game.player:
        gear = current_weapon(game.player)
        if gear is None:
            add_log(game, "Сначала экипируй оружие для разборки.")
        else:
            reward = salvage_reward(gear)
            idx = game.player.equipped_weapon_index
            del game.player.weapon_inventory[idx]
            game.player.equipped_weapon_index = None
            game.player.components += reward
            add_log(game, f"Оружие разобрано на {reward} компонентов.")

    elif data == "salvage_armor" and game.player:
        salvaged = False
        for slot in ARMOR_SLOTS:
            idx = game.player.equipped_armor.get(slot)
            if idx is not None and 0 <= idx < len(game.player.armor_inventory):
                gear = game.player.armor_inventory[idx]
                reward = salvage_reward(gear)
                del game.player.armor_inventory[idx]
                game.player.equipped_armor[slot] = None
                for other_slot, other_idx in list(game.player.equipped_armor.items()):
                    if other_idx is not None and other_idx > idx:
                        game.player.equipped_armor[other_slot] = other_idx - 1
                game.player.components += reward
                add_log(game, f"{ARMOR_SLOT_NAMES[slot]} разобрана на {reward} компонентов.")
                salvaged = True
                break
        if not salvaged:
            add_log(game, "Сначала экипируй часть брони для разборки.")

    elif data == "craft_weapon" and game.player:
        gear = craft_item(game.player, "weapon", max(1, game.player.level))
        if gear:
            game.player.weapon_inventory.append(gear)
            add_log(game, f"Скрафчено оружие: {gear.name}.")
        else:
            add_log(game, "Не хватает компонентов или дизен для крафта оружия.")

    elif data == "craft_armor" and game.player:
        slot = random.choice(ARMOR_SLOTS)
        gear = craft_item(game.player, slot, max(1, game.player.level))
        if gear:
            game.player.armor_inventory.append(gear)
            add_log(game, f"Скрафчена броня: {gear.name}.")
        else:
            add_log(game, "Не хватает компонентов или дизен для крафта брони.")

    elif data == "weapon_page_prev" and game.player:
        game.equipment_page_weapon = max(0, game.equipment_page_weapon - 1)

    elif data == "weapon_page_next" and game.player:
        max_page = max(0, (len(game.player.weapon_inventory) - 1) // ITEMS_PER_PAGE)
        game.equipment_page_weapon = min(max_page, game.equipment_page_weapon + 1)

    elif data.startswith("armor_page_prev:") and game.player:
        slot = data.split(":", 1)[1]
        game.equipment_page_armor[slot] = max(0, game.equipment_page_armor.get(slot, 0) - 1)

    elif data.startswith("armor_page_next:") and game.player:
        slot = data.split(":", 1)[1]
        slot_items = [g for g in game.player.armor_inventory if g.slot == slot]
        max_page = max(0, (len(slot_items) - 1) // ITEMS_PER_PAGE)
        game.equipment_page_armor[slot] = min(max_page, game.equipment_page_armor.get(slot, 0) + 1)

    elif data == "back_zone_select":
        game.enemy = None
        game.stage = "zone_select"

    elif data == "back_hub":
        game.enemy = None
        game.stage = "hub"
        game.current_zone_id = None
        add_log(game, "Ты возвращаешься на базу.")

    save_games()
    await send_or_edit(update, render_text(game), render_keyboard(game))


def build_application() -> Application:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    return app


def _run_self_checks() -> None:
    assert exp_needed_for_next(1) == 120
    assert mob_exp(1) == 4
    assert mob_exp(10) > mob_exp(5)
    assert DODGE_UPGRADES[7] == 60
    p = Player("Беллато", "Штурмовик", 1, 0, 100, 100, 10, 5, 10, 0, 0, 1)
    boots = Gear("b1", "Test Boots", "boots", 5, "normal", "обычный", 3, 4)
    p.armor_inventory.append(boots)
    p.equipped_armor["boots"] = 0
    assert current_dodge(p) == 20
    crafted = make_gear("weapon", 10, False)
    assert crafted.slot == "weapon"
    assert salvage_reward(crafted) > 0
    monsters = selected_monsters_for_zone("alliance_outpost")
    assert monsters[0]["name"] == "Флем Детеныш"
    assert len(paged_items(monsters, 0)) == 5


def main() -> None:
    _run_self_checks()
    load_games()
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN environment variable or replace PUT_YOUR_BOT_TOKEN_HERE in the file.")
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
