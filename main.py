import html
import logging
import os
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

RACES = [
    {
        "id": "bellato",
        "name": "Беллато",
        "desc": "Сбалансированная раса с хорошей выживаемостью и запасом дизен.",
        "stats": {"max_hp": 48, "attack": 7, "armor": 2, "crit": 8, "dizens": 45},
    },
    {
        "id": "cora",
        "name": "Кора",
        "desc": "Больше урона и выше шанс критического удара.",
        "stats": {"max_hp": 42, "attack": 9, "armor": 1, "crit": 16, "dizens": 30},
    },
    {
        "id": "accretia",
        "name": "Акретия",
        "desc": "Тяжелая броня и высокий запас HP.",
        "stats": {"max_hp": 54, "attack": 8, "armor": 3, "crit": 6, "dizens": 25},
    },
]

CLASSES = [
    {
        "id": "warrior",
        "name": "Штурмовик",
        "desc": "Больше HP и брони.",
        "bonus": {"max_hp": 8, "armor": 1, "attack": 1, "crit": 0, "dizens": 0, "medkits": 0},
    },
    {
        "id": "ranger",
        "name": "Стрелок",
        "desc": "Больше урона и критов.",
        "bonus": {"max_hp": 0, "armor": 0, "attack": 2, "crit": 8, "dizens": 0, "medkits": 0},
    },
    {
        "id": "specialist",
        "name": "Специалист",
        "desc": "Лучше экономика и восстановление.",
        "bonus": {"max_hp": 2, "armor": 1, "attack": 0, "crit": 3, "dizens": 20, "medkits": 1},
    },
]

ZONES = [
    {
        "id": "crag",
        "name": "Краговые пустоши",
        "difficulty": 1,
        "reward_min": 18,
        "reward_max": 28,
        "text": "Пыльная стартовая зона с легкими монстрами.",
        "loot": ["необработанная руда", "Recovery Potion", "Talic Fragment"],
    },
    {
        "id": "anabola",
        "name": "Анабола",
        "difficulty": 2,
        "reward_min": 28,
        "reward_max": 40,
        "text": "Более опасная территория с мутантами и турелями.",
        "loot": ["Blue Ore", "Talic Crystal", "анимус-чип", "MAU-плата"],
    },
    {
        "id": "outpost",
        "name": "Забытый форпост",
        "difficulty": 3,
        "reward_min": 40,
        "reward_max": 58,
        "text": "Остатки старой войны трех рас.",
        "loot": ["Red Ore", "Intense Armor Part", "Intense Weapon Core", "карта Beast Mountain"],
    },
    {
        "id": "core",
        "name": "Ядро сектора",
        "difficulty": 4,
        "reward_min": 60,
        "reward_max": 85,
        "text": "Финальная зона с главным боссом.",
        "loot": ["Golden Ore", "Talic Crystal", "Launcher Module", "Rare Armor Box"],
    },
]

ENEMIES = [
    {"name": "Young Flym", "hp": 14, "attack": 4, "exp": 8, "drops": ["необработанная руда", "Recovery Potion"]},
    {"name": "Wing", "hp": 16, "attack": 4, "exp": 9, "drops": ["Talic Fragment", "Recovery Potion"]},
    {"name": "Flym", "hp": 20, "attack": 5, "exp": 11, "drops": ["Blue Ore", "Talic Fragment", "анимус-чип"]},
    {"name": "Digger Clan", "hp": 22, "attack": 6, "exp": 12, "drops": ["Blue Ore", "MAU-плата", "Intense Weapon Core"]},
    {"name": "Hobo Blade", "hp": 28, "attack": 7, "exp": 15, "drops": ["Intense Armor Part", "Talic Crystal"]},
    {"name": "Flem Guard", "hp": 36, "attack": 8, "exp": 18, "drops": ["Red Ore", "Talic Crystal", "Rare Armor Box"]},
    {"name": "Crawler Alpha", "hp": 42, "attack": 10, "exp": 22, "drops": ["Golden Ore", "Launcher Module", "Rare Armor Box"]},
]

WEAPONS = [
    {"id": "flym_dagger", "name": "Flym Knife", "base_attack": 2, "rarity": "common"},
    {"id": "wing_blade", "name": "Wing Blade", "base_attack": 3, "rarity": "common"},
    {"id": "digger_launcher", "name": "Digger Launcher", "base_attack": 4, "rarity": "uncommon"},
    {"id": "flem_spear", "name": "Flem Spear", "base_attack": 5, "rarity": "rare"},
    {"id": "crawler_reaper", "name": "Crawler Reaper", "base_attack": 7, "rarity": "epic"},
]

MISSION_POOL = [
    {"id": "hunt", "name": "Зачистить 2 вылазки", "target": 2, "reward": 25, "type": "clears"},
    {"id": "loot", "name": "Собрать 2 предмета", "target": 2, "reward": 20, "type": "loot"},
    {"id": "money", "name": "Заработать 40 дизен", "target": 40, "reward": 22, "type": "dizens"},
]

TALIC_CHANCES = {
    0: {"next": 1, "chance": 85},
    1: {"next": 2, "chance": 65},
    2: {"next": 3, "chance": 45},
    3: {"next": 4, "chance": 30},
    4: {"next": 5, "chance": 20},
    5: {"next": 6, "chance": 12},
    6: {"next": 7, "chance": 7},
}

TALIC_MULTIPLIERS = {0: 0.0, 1: 0.05, 2: 0.25, 3: 0.50, 4: 0.70, 5: 0.90, 6: 1.35, 7: 2.00}


@dataclass
class Weapon:
    id: str
    name: str
    base_attack: int
    rarity: str
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
    medkits: int
    talics: int = 0
    loot_count: int = 0
    clears: int = 0
    weapon_inventory: List[Weapon] = field(default_factory=list)
    equipped_index: Optional[int] = None


@dataclass
class GameState:
    stage: str = "menu"
    selected_race: Optional[str] = None
    selected_class: Optional[str] = None
    player: Optional[Player] = None
    current_zone: Optional[dict] = None
    enemy: Optional[dict] = None
    battle_count: int = 0
    mission: Optional[dict] = None
    mission_progress: int = 0
    mission_claimed: bool = False
    ended: bool = False
    win: bool = False
    log: List[str] = field(default_factory=lambda: [
        "Добро пожаловать в RF Online: Text Raid.",
        "Это телеграм-бот с казуальной одиночной игрой по мотивам RF Online.",
    ])


USER_GAMES: Dict[int, GameState] = {}


def get_game(user_id: int) -> GameState:
    if user_id not in USER_GAMES:
        USER_GAMES[user_id] = GameState()
    return USER_GAMES[user_id]


def esc(text: str) -> str:
    return html.escape(str(text))


def add_log(game: GameState, *lines: str) -> None:
    game.log.extend(lines)
    game.log = game.log[-15:]


def get_race(race_id: str) -> dict:
    return next(x for x in RACES if x["id"] == race_id)


def get_class(class_id: str) -> dict:
    return next(x for x in CLASSES if x["id"] == class_id)


def is_core_unlocked(player: Player) -> bool:
    return player.clears >= 5 or player.level >= 4


def current_weapon(player: Player) -> Optional[Weapon]:
    if player.equipped_index is None:
        return None
    if not (0 <= player.equipped_index < len(player.weapon_inventory)):
        player.equipped_index = None
        return None
    return player.weapon_inventory[player.equipped_index]


def calc_weapon_attack_bonus(player: Player) -> int:
    weapon = current_weapon(player)
    if not weapon:
        return 0
    mult = TALIC_MULTIPLIERS.get(weapon.upgrade, 0)
    return weapon.base_attack + int((player.attack + weapon.base_attack) * mult)


def total_attack(player: Player) -> int:
    return player.attack + calc_weapon_attack_bonus(player)


def choose_mission() -> dict:
    return deepcopy(random.choice(MISSION_POOL))


def generate_enemy(zone: dict, battle_count: int) -> dict:
    template_index = min(len(ENEMIES) - 1, max(0, zone["difficulty"] - 1 + battle_count // 2))
    base = deepcopy(ENEMIES[min(len(ENEMIES) - 1, template_index + random.randint(0, 1))])
    hp = base["hp"] + zone["difficulty"] * 4 + battle_count * 2
    attack = base["attack"] + zone["difficulty"] + battle_count // 3
    return {
        "name": "Pit Boss: Core Keeper" if zone["id"] == "core" else base["name"],
        "hp": hp,
        "max_hp": hp,
        "attack": attack,
        "exp": base["exp"] + zone["difficulty"] * 2,
        "drops": list(base["drops"]),
    }


def maybe_weapon_drop(zone: dict) -> Optional[Weapon]:
    if random.randint(1, 100) > 22:
        return None
    max_index = min(len(WEAPONS) - 1, zone["difficulty"] + 1)
    base = WEAPONS[random.randint(0, max_index)]
    return Weapon(**base)


def maybe_talic_drop() -> bool:
    return random.randint(1, 100) <= 10


def level_up(player: Player, game: GameState) -> None:
    while player.exp >= 30:
        player.exp -= 30
        player.level += 1
        player.max_hp += 8
        player.hp = player.max_hp
        player.attack += 2
        player.armor += 1
        player.crit += 1
        add_log(game, f"Новый уровень: {player.level}. Характеристики выросли, здоровье восстановлено.")


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
        lines.append("\nВыбери расу и класс, затем начни кампанию.")
    else:
        p = game.player
        weapon = current_weapon(p)
        weapon_name = f"{weapon.name} +{weapon.upgrade}" if weapon else "нет"
        lines.append(
            f"\n<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}\n"
            f"HP: {p.hp}/{p.max_hp}\n"
            f"Базовая атака: {p.attack}\n"
            f"Общая атака: {total_attack(p)}\n"
            f"Броня: {p.armor} | Крит: {p.crit}%\n"
            f"Дизены: {p.dizens} | Аптечки: {p.medkits} | Талики: {p.talics}\n"
            f"Оружие: {esc(weapon_name)}\n"
            f"Вылазки: {p.clears} | Лут: {p.loot_count} | Опыт: {p.exp}/30"
        )

    if game.mission:
        status = "получена" if game.mission_claimed else "выполнено" if game.mission_progress >= game.mission["target"] else "в процессе"
        lines.append(
            f"\n<b>Задание:</b> {esc(game.mission['name'])}\n"
            f"Прогресс: {min(game.mission_progress, game.mission['target'])}/{game.mission['target']}\n"
            f"Награда: {game.mission['reward']} дизен | Статус: {status}"
        )

    if game.current_zone:
        lines.append(f"\n<b>Локация:</b> {esc(game.current_zone['name'])}\n{esc(game.current_zone['text'])}")

    if game.enemy:
        lines.append(
            f"\n<b>Враг:</b> {esc(game.enemy['name'])}\n"
            f"HP: {game.enemy['hp']}/{game.enemy['max_hp']} | EXP: {game.enemy['exp']}\n"
            f"Типичный дроп: {esc(', '.join(game.enemy['drops']))}"
        )

    if game.player and game.player.weapon_inventory:
        inv_lines = []
        for i, w in enumerate(game.player.weapon_inventory[:8]):
            marker = "✅ " if game.player.equipped_index == i else ""
            inv_lines.append(f"{marker}{i+1}. {w.name} +{w.upgrade} (база +{w.base_attack})")
        lines.append("\n<b>Инвентарь оружия:</b>\n" + esc("\n".join(inv_lines)))

    log_text = "\n".join(game.log[-8:])
    lines.append(f"\n<b>Журнал:</b>\n{esc(log_text)}")
    return "\n".join(lines)


def render_keyboard(game: GameState) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []

    if not game.player:
        race_row = [InlineKeyboardButton(r["name"], callback_data=f"race:{r['id']}") for r in RACES]
        class_row = [InlineKeyboardButton(c["name"], callback_data=f"class:{c['id']}") for c in CLASSES]
        rows.extend([race_row, class_row])
        rows.append([InlineKeyboardButton("Начать кампанию", callback_data="start_game")])
        return InlineKeyboardMarkup(rows)

    if game.ended:
        rows.append([InlineKeyboardButton("Начать заново", callback_data="reset")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "hub":
        zone_buttons = []
        for z in ZONES:
            if z["id"] != "core" or is_core_unlocked(game.player):
                zone_buttons.append(InlineKeyboardButton(z["name"], callback_data=f"zone:{z['id']}"))
        for i in range(0, len(zone_buttons), 2):
            rows.append(zone_buttons[i:i+2])
        rows.append([
            InlineKeyboardButton("Отдохнуть", callback_data="rest"),
            InlineKeyboardButton("Забрать награду", callback_data="claim_mission"),
        ])
        if game.player.weapon_inventory:
            rows.append([InlineKeyboardButton("Снаряжение", callback_data="equipment")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "zone":
        rows.append([InlineKeyboardButton("Разведка и бой", callback_data="explore")])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "combat":
        rows.append([
            InlineKeyboardButton("Атаковать", callback_data="attack"),
            InlineKeyboardButton("Аптечка", callback_data="medkit"),
        ])
        rows.append([InlineKeyboardButton("Отступить", callback_data="escape")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "equipment":
        weapon_rows = []
        for i, w in enumerate(game.player.weapon_inventory[:8]):
            weapon_rows.append([InlineKeyboardButton(f"Надеть: {w.name} +{w.upgrade}", callback_data=f"equip:{i}")])
        rows.extend(weapon_rows)
        rows.append([
            InlineKeyboardButton("Заточить", callback_data="upgrade_weapon"),
            InlineKeyboardButton("На базу", callback_data="back_hub"),
        ])
        return InlineKeyboardMarkup(rows)

    return InlineKeyboardMarkup([[InlineKeyboardButton("На базу", callback_data="back_hub")]])


async def send_or_edit(update: Update, text: str, keyboard: InlineKeyboardMarkup) -> None:
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        assert update.effective_message
        await update.effective_message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    USER_GAMES[user_id] = GameState()
    game = USER_GAMES[user_id]
    await send_or_edit(update, render_text(game), render_keyboard(game))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start — новая игра\n"
        "/help — помощь\n\n"
        "Играй кнопками: выбирай расу и класс, фарми зоны, надевай оружие, выбивай Талик невежества и точи пушку до +7."
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
                medkits=2 + klass["bonus"]["medkits"],
            )
            game.stage = "hub"
            game.mission = choose_mission()
            game.mission_progress = 0
            game.mission_claimed = False
            game.log = [
                f"Ты выбрал расу {race['name']} и класс {klass['name']}.",
                race["desc"],
                klass["desc"],
                f"Текущая задача: {game.mission['name']}. Награда: {game.mission['reward']} дизен.",
                "Командование открыло доступ к базовому хабу.",
            ]

    elif data.startswith("zone:") and game.player:
        zone_id = data.split(":", 1)[1]
        zone = next(z for z in ZONES if z["id"] == zone_id)
        if zone_id == "core" and not is_core_unlocked(game.player):
            add_log(game, "Финальная зона пока закрыта.")
        else:
            game.current_zone = zone
            game.stage = "zone"
            add_log(game, f"Локация: {zone['name']}. {zone['text']}")

    elif data == "explore" and game.current_zone:
        game.enemy = generate_enemy(game.current_zone, game.battle_count)
        game.stage = "combat"
        add_log(game, f"Во время разведки появляется враг: {game.enemy['name']} (HP {game.enemy['hp']}).")

    elif data == "attack" and game.player and game.enemy:
        crit = random.randint(1, 100) <= game.player.crit
        dmg = max(1, total_attack(game.player) + random.randint(0, 3) - game.enemy["attack"] // 5)
        if crit:
            dmg *= 2
        game.enemy["hp"] -= dmg
        add_log(game, f"Ты наносишь {dmg} урона." + (" Критический удар!" if crit else ""))

        if game.enemy["hp"] <= 0:
            dizens_gain = random.randint(game.current_zone["reward_min"], game.current_zone["reward_max"])
            exp_gain = game.enemy["exp"]
            loot = random.choice(game.current_zone["loot"] + game.enemy["drops"])
            game.player.dizens += dizens_gain
            game.player.exp += exp_gain
            game.player.loot_count += 1
            add_log(game, f"Враг повержен. Награда: {dizens_gain} дизен, {exp_gain} опыта, добыча: {loot}.")

            weapon = maybe_weapon_drop(game.current_zone)
            if weapon:
                game.player.weapon_inventory.append(weapon)
                add_log(game, f"С монстра выпало оружие: {weapon.name} +0.")
            if maybe_talic_drop():
                game.player.talics += 1
                add_log(game, "Редкий дроп: Талик невежества.")

            level_up(game.player, game)
            game.player.clears += 1
            game.battle_count += 1
            update_mission(game, 1, 1, dizens_gain)
            game.enemy = None
            if game.current_zone["id"] == "core":
                game.ended = True
                game.win = True
                game.stage = "end"
                add_log(game, "Ты зачистил ядро сектора и завершил кампанию победой.")
            else:
                game.stage = "zone"
                if is_core_unlocked(game.player):
                    add_log(game, "Доступ к финальной зоне открыт: Ядро сектора.")
                else:
                    add_log(game, "Сектор временно очищен. Можно продолжить фарм или вернуться на базу.")
        else:
            enemy_dmg = max(1, game.enemy["attack"] + random.randint(0, 2) - game.player.armor)
            game.player.hp -= enemy_dmg
            add_log(game, f"{game.enemy['name']} отвечает и наносит {enemy_dmg} урона.")
            if game.player.hp <= 0:
                game.player.hp = 0
                game.ended = True
                game.win = False
                game.stage = "end"
                add_log(game, "Ты пал в бою. Кампания окончена.")

    elif data == "medkit" and game.player:
        if game.player.medkits > 0:
            game.player.medkits -= 1
            game.player.hp = min(game.player.max_hp, game.player.hp + 22)
            add_log(game, "Ты используешь аптечку и восстанавливаешь 22 HP.")
        else:
            add_log(game, "Аптечки закончились.")

    elif data == "escape" and game.player and game.enemy:
        game.player.hp = max(1, game.player.hp - 6)
        game.enemy = None
        game.stage = "zone"
        add_log(game, "Ты отступил и потерял 6 HP.")

    elif data == "rest" and game.player:
        game.player.hp = game.player.max_hp
        add_log(game, "На базе ты полностью восстановил здоровье.")

    elif data == "claim_mission" and game.player and game.mission:
        if not game.mission_claimed and game.mission_progress >= game.mission["target"]:
            game.player.dizens += game.mission["reward"]
            game.mission_claimed = True
            add_log(game, f"Ты получил награду за задание: {game.mission['reward']} дизен.")
        else:
            add_log(game, "Награда за задание пока недоступна.")

    elif data == "back_hub":
        game.enemy = None
        game.current_zone = None
        game.stage = "hub"
        add_log(game, "Ты возвращаешься на базу.")

    elif data == "equipment" and game.player:
        game.stage = "equipment"

    elif data.startswith("equip:") and game.player:
        index = int(data.split(":", 1)[1])
        if 0 <= index < len(game.player.weapon_inventory):
            game.player.equipped_index = index
            w = game.player.weapon_inventory[index]
            add_log(game, f"Ты экипировал оружие: {w.name} +{w.upgrade}.")
            game.stage = "equipment"

    elif data == "upgrade_weapon" and game.player:
        weapon = current_weapon(game.player)
        if not weapon:
            add_log(game, "Сначала экипируй оружие.")
        elif game.player.talics <= 0:
            add_log(game, "У тебя нет Талика невежества.")
        elif weapon.upgrade >= 7:
            add_log(game, "Оружие уже заточено на максимум: +7.")
        else:
            rule = TALIC_CHANCES[weapon.upgrade]
            game.player.talics -= 1
            if random.randint(1, 100) <= rule["chance"]:
                weapon.upgrade = rule["next"]
                add_log(game, f"Талик невежества сработал успешно. {weapon.name} теперь +{weapon.upgrade}.")
            else:
                add_log(game, f"Заточка не удалась. {weapon.name} осталось на +{weapon.upgrade}.")
            game.stage = "equipment"

    await send_or_edit(update, render_text(game), render_keyboard(game))


def build_application() -> Application:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    return app


def main() -> None:
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN environment variable or replace PUT_YOUR_BOT_TOKEN_HERE in the file.")
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
