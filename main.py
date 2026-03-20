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
DROP_GEAR_CHANCE = 7
BOSS_CHANCE = 15

ZONES = [
    {
        "id": "alliance_outpost",
        "name": "Аванпост Альянса",
        "level_min": 1,
        "level_max": 8,
        "reward_min": 4,
        "reward_max": 10,
        "text": "Стартовая территория с патрулями, учебными мобами и первым лутом.",
        "loot": ["необработанная руда", "банка HP", "Talic Fragment"],
        "boss": {
            "name": "Командир Аванпоста",
            "level": 8,
            "drops": ["ящик офицера", "талик невежества", "талик покровительства"],
            "dizens": [20, 35],
        },
    },
    {
        "id": "haram_colony",
        "name": "Колония Харам",
        "level_min": 9,
        "level_max": 18,
        "reward_min": 10,
        "reward_max": 18,
        "text": "Более опасная колония с усиленными мобами и плотным фармом.",
        "loot": ["Blue Ore", "банка HP", "Talic Crystal", "анимус-чип"],
        "boss": {
            "name": "Хранитель Харам",
            "level": 18,
            "drops": ["редкий контейнер Харам", "талик невежества", "талик покровительства"],
            "dizens": [35, 55],
        },
    },
    {
        "id": "numerus_colony",
        "name": "Колония Нумерус",
        "level_min": 19,
        "level_max": 32,
        "reward_min": 18,
        "reward_max": 30,
        "text": "Тяжёлая зона со злыми пачками мобов и шансом на ценный дроп.",
        "loot": ["Red Ore", "банка HP", "Talic Crystal", "Intense Part"],
        "boss": {
            "name": "Тиран Нумерус",
            "level": 32,
            "drops": ["сундук Нумерус", "талик невежества", "талик покровительства", "Leon Core"],
            "dizens": [55, 85],
        },
    },
    {
        "id": "krag_mines",
        "name": "Краговые Шахты",
        "level_min": 33,
        "level_max": 50,
        "reward_min": 30,
        "reward_max": 55,
        "text": "Опаснейшие шахты с боссами, редким дропом и топовым снаряжением.",
        "loot": ["Golden Ore", "банка HP", "Rare Box", "Leon Fragment"],
        "boss": {
            "name": "Король Шахт",
            "level": 50,
            "drops": ["шахтёрская корона", "талик невежества", "талик покровительства", "Leon Relic"],
            "dizens": [90, 140],
        },
    },
]

RACES = [
    {
        "id": "bellato",
        "name": "Беллато",
        "desc": "Сбалансированная раса с хорошей выживаемостью и запасом дизен.",
        "stats": {"max_hp": 70, "attack": 7, "armor": 2, "crit": 8, "dizens": 30},
    },
    {
        "id": "cora",
        "name": "Кора",
        "desc": "Больше урона и выше шанс критического удара.",
        "stats": {"max_hp": 62, "attack": 9, "armor": 1, "crit": 15, "dizens": 25},
    },
    {
        "id": "accretia",
        "name": "Акретия",
        "desc": "Тяжелая броня и высокий запас HP.",
        "stats": {"max_hp": 78, "attack": 8, "armor": 3, "crit": 6, "dizens": 22},
    },
]

CLASSES = [
    {
        "id": "warrior",
        "name": "Штурмовик",
        "desc": "Больше HP и брони.",
        "bonus": {"max_hp": 12, "armor": 2, "attack": 1, "crit": 0, "dizens": 0, "banks": 1},
    },
    {
        "id": "ranger",
        "name": "Стрелок",
        "desc": "Больше урона и критов.",
        "bonus": {"max_hp": 0, "armor": 0, "attack": 3, "crit": 8, "dizens": 0, "banks": 0},
    },
    {
        "id": "specialist",
        "name": "Специалист",
        "desc": "Лучше экономика и восстановление.",
        "bonus": {"max_hp": 4, "armor": 1, "attack": 0, "crit": 3, "dizens": 12, "banks": 2},
    },
]

MOB_NAMES = [
    "Young Flym",
    "Wing",
    "Flym",
    "Digger",
    "Digger Captain",
    "Hobo Blade",
    "Flem Scout",
    "Flem Guard",
    "Crawler",
    "Crawler Alpha",
    "Mine Ravager",
    "Pit Stalker",
]

GEAR_TIERS = [
    {"id": "normal", "name": "обычный", "weapon_mult": 1.0, "armor_mult": 1.0, "weight": 60},
    {"id": "int", "name": "инт", "weapon_mult": 1.35, "armor_mult": 1.3, "weight": 25},
    {"id": "type_c", "name": "тип с", "weapon_mult": 1.8, "armor_mult": 1.7, "weight": 10},
    {"id": "leon", "name": "леон", "weapon_mult": 2.5, "armor_mult": 2.3, "weight": 5},
]

WEAPON_NAMES = [
    "Нож Flym",
    "Клинок Wing",
    "Пускатель Digger",
    "Копьё Flem",
    "Разрушитель Crawler",
    "Леон Блейд",
]

ARMOR_NAMES = [
    "Бронекуртка",
    "Тактический Доспех",
    "Шахтёрская Броня",
    "Комплект Колонии",
    "Флем Панцирь",
    "Леон Армор",
]

MISSION_POOL = [
    {"id": "hunt", "name": "Зачистить 3 вылазки", "target": 3, "reward": 20, "type": "clears"},
    {"id": "loot", "name": "Выбить 2 предмета", "target": 2, "reward": 18, "type": "loot"},
    {"id": "money", "name": "Заработать 30 дизен", "target": 30, "reward": 16, "type": "dizens"},
]

UPGRADE_CHANCES = {
    0: {"next": 1, "chance": 90},
    1: {"next": 2, "chance": 80},
    2: {"next": 3, "chance": 65},
    3: {"next": 4, "chance": 30},
    4: {"next": 5, "chance": 15},
    5: {"next": 6, "chance": 10},
    6: {"next": 7, "chance": 7},
}

UPGRADE_BONUSES = {
    0: 0.0,
    1: 0.05,
    2: 0.25,
    3: 0.50,
    4: 0.70,
    5: 0.90,
    6: 1.35,
    7: 2.00,
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
    dizens: int
    banks: int
    talics_ignorance: int = 0
    talics_protection: int = 0
    loot_count: int = 0
    clears: int = 0
    weapon_inventory: List[Gear] = field(default_factory=list)
    armor_inventory: List[Gear] = field(default_factory=list)
    equipped_weapon_index: Optional[int] = None
    equipped_armor_index: Optional[int] = None


@dataclass
class GameState:
    stage: str = "menu"
    selected_race: Optional[str] = None
    selected_class: Optional[str] = None
    player: Optional[Player] = None
    current_zone_id: Optional[str] = None
    enemy: Optional[dict] = None
    battle_count: int = 0
    mission: Optional[dict] = None
    mission_progress: int = 0
    mission_claimed: bool = False
    ended: bool = False
    win: bool = False
    log: List[str] = field(default_factory=lambda: [
        "Добро пожаловать в RF Online: Text Raid.",
        "Бот сохраняет прогресс и теперь поддерживает оружие, броню, талики и боссов.",
    ])


USER_GAMES: Dict[int, GameState] = {}


def exp_needed_for_next(level: int) -> int:
    return 50 * (2 ** (level - 1))


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
        game = GameState(
            stage=game_data.get("stage", "menu"),
            selected_race=game_data.get("selected_race"),
            selected_class=game_data.get("selected_class"),
            player=player,
            current_zone_id=game_data.get("current_zone_id"),
            enemy=game_data.get("enemy"),
            battle_count=game_data.get("battle_count", 0),
            mission=game_data.get("mission"),
            mission_progress=game_data.get("mission_progress", 0),
            mission_claimed=game_data.get("mission_claimed", False),
            ended=game_data.get("ended", False),
            win=game_data.get("win", False),
            log=game_data.get("log", []),
        )
        USER_GAMES[int(uid)] = game


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


def current_armor(player: Player) -> Optional[Gear]:
    if player.equipped_armor_index is None:
        return None
    if 0 <= player.equipped_armor_index < len(player.armor_inventory):
        return player.armor_inventory[player.equipped_armor_index]
    player.equipped_armor_index = None
    return None


def calc_weapon_bonus(player: Player) -> int:
    weapon = current_weapon(player)
    if not weapon:
        return 0
    mult = UPGRADE_BONUSES.get(weapon.upgrade, 0)
    return weapon.base_stat + int((player.attack + weapon.base_stat) * mult)


def calc_armor_bonus(player: Player) -> int:
    armor = current_armor(player)
    if not armor:
        return 0
    mult = UPGRADE_BONUSES.get(armor.upgrade, 0)
    return armor.base_stat + int((player.armor + armor.base_stat) * mult)


def total_attack(player: Player) -> int:
    return player.attack + calc_weapon_bonus(player)


def total_armor(player: Player) -> int:
    return player.armor + calc_armor_bonus(player)


def choose_mission() -> dict:
    return dict(random.choice(MISSION_POOL))


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
    names = WEAPON_NAMES if slot == "weapon" else ARMOR_NAMES
    base = max(1, level)
    if slot == "weapon":
        stat = max(1, int((2 + base // 2) * tier["weapon_mult"]))
    else:
        stat = max(1, int((1 + base // 3) * tier["armor_mult"]))
    return Gear(
        id=f"{slot}_{tier['id']}_{level}_{random.randint(1000,9999)}",
        name=f"{random.choice(names)} [{tier['name']}] lv.{level}",
        slot=slot,
        level=level,
        tier_id=tier["id"],
        tier_name=tier["name"],
        base_stat=stat,
        upgrade=0,
    )


def maybe_gear_drop(enemy_level: int, is_boss: bool) -> Optional[Gear]:
    chance = 100 if is_boss else DROP_GEAR_CHANCE
    if random.randint(1, 100) > chance:
        return None
    slot = random.choice(["weapon", "armor"])
    return make_gear(slot, enemy_level, is_boss)


def generate_enemy(zone: dict, battle_count: int) -> dict:
    is_boss = random.randint(1, 100) <= BOSS_CHANCE
    if is_boss:
        boss = zone["boss"]
        lvl = boss["level"]
        hp = 30 + lvl * 14
        atk = max(4, lvl // 2 + 8)
        return {
            "name": boss["name"],
            "level": lvl,
            "hp": hp,
            "max_hp": hp,
            "attack": atk,
            "exp": 2 ** (lvl - 1),
            "drops": list(boss["drops"]),
            "is_boss": True,
            "reward_min": boss["dizens"][0],
            "reward_max": boss["dizens"][1],
        }
    lvl = random.randint(zone["level_min"], zone["level_max"])
    hp = 14 + lvl * 5
    atk = max(2, lvl // 2 + 2)
    return {
        "name": random.choice(MOB_NAMES),
        "level": lvl,
        "hp": hp,
        "max_hp": hp,
        "attack": atk,
        "exp": 2 ** (lvl - 1),
        "drops": list(zone["loot"]),
        "is_boss": False,
        "reward_min": zone["reward_min"],
        "reward_max": zone["reward_max"],
    }


def level_up(player: Player, game: GameState) -> None:
    while player.level < MAX_LEVEL and player.exp >= exp_needed_for_next(player.level):
        needed = exp_needed_for_next(player.level)
        player.exp -= needed
        player.level += 1
        player.max_hp += 10
        player.hp = player.max_hp
        player.attack += 2
        player.armor += 1
        player.crit += 1
        add_log(game, f"Новый уровень: {player.level}. Нужно {exp_needed_for_next(player.level) if player.level < MAX_LEVEL else 'MAX'} опыта до следующего.")


def update_mission(game: GameState, clears: int, loot: int, dizens: int) -> None:
    if not game.mission or game.mission_claimed:
        return
    mtype = game.mission["type"]
    if mtype == "clears":
        game.mission_progress += clears
    elif mtype == "loot":
        game.mission_progress += loot
    elif mtype == "dizens":
        game.mission_progress += dizens
    if game.mission_progress >= game.mission["target"]:
        add_log(game, f"Задание выполнено: {game.mission['name']}. Забери награду на базе.")


def render_text(game: GameState) -> str:
    lines: List[str] = ["<b>RF Online: Text Raid</b>"]
    if not game.player:
        lines.append("Выбери расу и класс, затем начни кампанию.")
    else:
        p = game.player
        weapon = current_weapon(p)
        armor = current_armor(p)
        lines.append(
            f"
<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}/{MAX_LEVEL}
"
            f"HP: {p.hp}/{p.max_hp}
"
            f"Базовая атака: {p.attack} | Общая атака: {total_attack(p)}
"
            f"Базовая броня: {p.armor} | Общая броня: {total_armor(p)}
"
            f"Крит: {p.crit}%
"
            f"Дизены: {p.dizens} | Банки: {p.banks}
"
            f"Талики невежества: {p.talics_ignorance} | Талики покровительства: {p.talics_protection}
"
            f"Оружие: {esc(weapon.name + ' +' + str(weapon.upgrade) if weapon else 'нет')}
"
            f"Броня: {esc(armor.name + ' +' + str(armor.upgrade) if armor else 'нет')}
"
            f"Вылазки: {p.clears} | Лут: {p.loot_count}
"
            f"Опыт: {p.exp}/{exp_needed_for_next(p.level) if p.level < MAX_LEVEL else 'MAX'}"
        )
    if game.mission:
        status = "получена" if game.mission_claimed else "выполнено" if game.mission_progress >= game.mission["target"] else "в процессе"
        lines.append(
            f"
<b>Задание:</b> {esc(game.mission['name'])}
"
            f"Прогресс: {min(game.mission_progress, game.mission['target'])}/{game.mission['target']}
"
            f"Награда: {game.mission['reward']} дизен | Статус: {status}"
        )
    zone = get_zone(game.current_zone_id)
    if zone:
        lines.append(f"
<b>Локация:</b> {esc(zone['name'])}
{esc(zone['text'])}")
    if game.enemy:
        lines.append(
            f"
<b>Враг:</b> {esc(game.enemy['name'])} | lvl {game.enemy['level']}
"
            f"HP: {game.enemy['hp']}/{game.enemy['max_hp']} | EXP: {game.enemy['exp']}
"
            f"Типичный дроп: {esc(', '.join(game.enemy['drops']))}
"
            f"Тип: {'босс' if game.enemy['is_boss'] else 'обычный моб'}"
        )
    if game.player and game.player.weapon_inventory:
        inv = "
".join(
            f"{'✅ ' if game.player.equipped_weapon_index == i else ''}{i+1}. {g.name} +{g.upgrade} (atk +{g.base_stat})"
            for i, g in enumerate(game.player.weapon_inventory[:8])
        )
        lines.append("
<b>Оружие в инвентаре:</b>
" + esc(inv))
    if game.player and game.player.armor_inventory:
        inv = "
".join(
            f"{'✅ ' if game.player.equipped_armor_index == i else ''}{i+1}. {g.name} +{g.upgrade} (arm +{g.base_stat})"
            for i, g in enumerate(game.player.armor_inventory[:8])
        )
        lines.append("
<b>Броня в инвентаре:</b>
" + esc(inv))
    lines.append("
<b>Журнал:</b>
" + esc("
".join(game.log[-8:])))
    return "
".join(lines)


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
        zone_buttons = [InlineKeyboardButton(z["name"], callback_data=f"zone:{z['id']}") for z in ZONES]
        for i in range(0, len(zone_buttons), 2):
            rows.append(zone_buttons[i:i + 2])
        rows.append([
            InlineKeyboardButton("Отдохнуть", callback_data="rest"),
            InlineKeyboardButton("Забрать награду", callback_data="claim_mission"),
        ])
        rows.append([
            InlineKeyboardButton("Снаряжение", callback_data="equipment"),
            InlineKeyboardButton("Инфо о шансах", callback_data="rates"),
        ])
        return InlineKeyboardMarkup(rows)
    if game.stage == "zone":
        rows.append([InlineKeyboardButton("Разведка и бой", callback_data="explore")])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)
    if game.stage == "combat":
        rows.append([
            InlineKeyboardButton("Атаковать", callback_data="attack"),
            InlineKeyboardButton("Банка", callback_data="bank"),
        ])
        rows.append([InlineKeyboardButton("Отступить", callback_data="escape")])
        return InlineKeyboardMarkup(rows)
    if game.stage == "equipment":
        for i, w in enumerate(game.player.weapon_inventory[:6]):
            rows.append([InlineKeyboardButton(f"Надеть оружие {i+1}", callback_data=f"equip_weapon:{i}")])
        for i, a in enumerate(game.player.armor_inventory[:6]):
            rows.append([InlineKeyboardButton(f"Надеть броню {i+1}", callback_data=f"equip_armor:{i}")])
        rows.append([
            InlineKeyboardButton("Точить оружие", callback_data="upgrade_weapon"),
            InlineKeyboardButton("Точить броню", callback_data="upgrade_armor"),
        ])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
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
    user_id = update.effective_user.id
    game = get_game(user_id)
    await send_or_edit(update, render_text(game), render_keyboard(game))


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    USER_GAMES[update.effective_user.id] = GameState()
    save_games()
    await send_or_edit(update, render_text(USER_GAMES[update.effective_user.id]), render_keyboard(USER_GAMES[update.effective_user.id]))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start — открыть игру
"
        "/reset — сбросить прогресс
"
        "/help — помощь

"
        "Теперь в игре 50 уровней, банки, броня, оружие, боссы, талики невежества и покровительства, а прогресс сохраняется в файле."
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
                dizens=race["stats"]["dizens"] + klass["bonus"]["dizens"],
                banks=2 + klass["bonus"]["banks"],
            )
            game.stage = "hub"
            game.current_zone_id = None
            game.mission = choose_mission()
            game.mission_progress = 0
            game.mission_claimed = False
            game.log = [
                f"Ты выбрал расу {race['name']} и класс {klass['name']}.",
                race["desc"],
                klass["desc"],
                f"Текущая задача: {game.mission['name']}. Награда: {game.mission['reward']} дизен.",
                "Командование открыло доступ ко всем четырём локациям.",
            ]

    elif data.startswith("zone:") and game.player:
        zone_id = data.split(":", 1)[1]
        zone = get_zone(zone_id)
        game.current_zone_id = zone_id
        game.stage = "zone"
        add_log(game, f"Локация: {zone['name']}. {zone['text']}")

    elif data == "explore" and game.player and get_zone(game.current_zone_id):
        zone = get_zone(game.current_zone_id)
        game.enemy = generate_enemy(zone, game.battle_count)
        game.stage = "combat"
        add_log(game, f"Появляется {'босс' if game.enemy['is_boss'] else 'моб'}: {game.enemy['name']} lv.{game.enemy['level']} (HP {game.enemy['hp']}).")

    elif data == "attack" and game.player and game.enemy:
        crit = random.randint(1, 100) <= game.player.crit
        dmg = max(1, total_attack(game.player) + random.randint(0, 3) - game.enemy["attack"] // 5)
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
            else:
                if random.randint(1, 100) <= 4:
                    game.player.talics_ignorance += 1
                    add_log(game, "Доп. редкий дроп: талик невежества.")
                if random.randint(1, 100) <= 4:
                    game.player.talics_protection += 1
                    add_log(game, "Доп. редкий дроп: талик покровительства.")
            gear = maybe_gear_drop(game.enemy["level"], game.enemy["is_boss"])
            if gear:
                if gear.slot == "weapon":
                    game.player.weapon_inventory.append(gear)
                    add_log(game, f"Выпало оружие: {gear.name} +0.")
                else:
                    game.player.armor_inventory.append(gear)
                    add_log(game, f"Выпала броня: {gear.name} +0.")
            level_up(game.player, game)
            update_mission(game, 1, 1, dizens_gain)
            game.enemy = None
            game.battle_count += 1
            game.stage = "zone"
        else:
            enemy_dmg = max(1, game.enemy["attack"] + random.randint(0, 2) - total_armor(game.player) // 4)
            game.player.hp -= enemy_dmg
            add_log(game, f"{game.enemy['name']} отвечает и наносит {enemy_dmg} урона.")
            if game.player.hp <= 0:
                game.player.hp = 0
                game.ended = True
                game.win = False
                game.stage = "end"
                add_log(game, "Ты пал в бою. Прогресс сохранён, можно начать заново /reset или продолжить после правок кода.")

    elif data == "bank" and game.player:
        if game.player.banks > 0:
            game.player.banks -= 1
            heal = max(25, game.player.max_hp // 3)
            game.player.hp = min(game.player.max_hp, game.player.hp + heal)
            add_log(game, f"Ты используешь банку и восстанавливаешь {heal} HP.")
        else:
            add_log(game, "Банки закончились.")

    elif data == "escape" and game.player and game.enemy:
        game.player.hp = max(1, game.player.hp - 8)
        game.enemy = None
        game.stage = "zone"
        add_log(game, "Ты отступил и потерял 8 HP.")

    elif data == "rest" and game.player:
        game.player.hp = game.player.max_hp
        game.player.banks += 1
        add_log(game, "На базе ты полностью восстановил здоровье и получил 1 банку.")

    elif data == "claim_mission" and game.player and game.mission:
        if not game.mission_claimed and game.mission_progress >= game.mission["target"]:
            game.player.dizens += game.mission["reward"]
            game.mission_claimed = True
            add_log(game, f"Ты получил награду за задание: {game.mission['reward']} дизен.")
        else:
            add_log(game, "Награда за задание пока недоступна.")

    elif data == "equipment" and game.player:
        game.stage = "equipment"

    elif data.startswith("equip_weapon:") and game.player:
        idx = int(data.split(":", 1)[1])
        if 0 <= idx < len(game.player.weapon_inventory):
            game.player.equipped_weapon_index = idx
            add_log(game, f"Ты экипировал оружие: {game.player.weapon_inventory[idx].name} +{game.player.weapon_inventory[idx].upgrade}.")
            game.stage = "equipment"

    elif data.startswith("equip_armor:") and game.player:
        idx = int(data.split(":", 1)[1])
        if 0 <= idx < len(game.player.armor_inventory):
            game.player.equipped_armor_index = idx
            add_log(game, f"Ты экипировал броню: {game.player.armor_inventory[idx].name} +{game.player.armor_inventory[idx].upgrade}.")
            game.stage = "equipment"

    elif data == "upgrade_weapon" and game.player:
        gear = current_weapon(game.player)
        if not gear:
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
        game.stage = "equipment"

    elif data == "upgrade_armor" and game.player:
        gear = current_armor(game.player)
        if not gear:
            add_log(game, "Сначала экипируй броню.")
        elif game.player.talics_protection <= 0:
            add_log(game, "У тебя нет талика покровительства.")
        elif gear.upgrade >= 7:
            add_log(game, "Броня уже заточена на максимум +7.")
        else:
            rule = UPGRADE_CHANCES[gear.upgrade]
            game.player.talics_protection -= 1
            if random.randint(1, 100) <= rule["chance"]:
                gear.upgrade = rule["next"]
                add_log(game, f"Успех. {gear.name} теперь +{gear.upgrade}.")
            else:
                add_log(game, f"Неудача. {gear.name} осталось на +{gear.upgrade}.")
        game.stage = "equipment"

    elif data == "back_hub":
        game.enemy = None
        game.current_zone_id = None
        game.stage = "hub"
        add_log(game, "Ты возвращаешься на базу.")

    elif data == "rates":
        add_log(
            game,
            "Шанс дропа оружия или брони: 7%.",
            "Точки: +1 90%, +2 80%, +3 65%, +4 30%, +5 15%, +6 10%, +7 7%.",
            "Мобы уровня N дают 2^(N-1) опыта и дропают шмот уровня N.",
        )

    save_games()
    await send_or_edit(update, render_text(game), render_keyboard(game))


def build_application() -> Application:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    return app


def main() -> None:
    load_games()
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN environment variable or replace PUT_YOUR_BOT_TOKEN_HERE in the file.")
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
