import asyncio
import logging
import os
import random
import time
from collections import defaultdict

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import (
    ARMOR_SLOTS,
    ARMOR_SLOT_NAMES,
    DODGE_UPGRADES,
    ITEMS_PER_PAGE,
    UPGRADE_CHANCES,
    DEATH_COOLDOWN_SECONDS,
)
from data import CLASSES, MARKET_PRICES, RACES, SUPER_DROP_CHANCES
from enemies import generate_enemy, get_zone, selected_monsters_for_zone
from loot import (
    craft_item,
    make_market_weapon,
    maybe_gear_drop,
    open_ancient_container,
    salvage_reward,
    sell_weapon_from_inventory,
)
from models import GameState, Gear, Player
from render import render_keyboard, render_text
from stats import (
    current_armor_piece,
    current_dodge,
    current_weapon,
    exp_needed_for_next,
    level_up,
    total_armor,
    total_attack,
)
from storage import load_games, save_games
from utils import add_log, cooldown_left

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "8728647250:AAHX_qXXsCPLbMaCrrtO_80BSa2HlG-KIC8")
USER_GAMES = load_games()
MAX_BANKS = 20
USER_LOCKS = defaultdict(asyncio.Lock)
LAST_ACTION_TS = {}
SAVE_TASK: asyncio.Task | None = None
SAVE_DELAY_SECONDS = 0.6
ACTION_DEBOUNCE_SECONDS = 0.35

def get_race(race_id: str) -> dict:
    return next(x for x in RACES if x["id"] == race_id)


def get_class(class_id: str) -> dict:
    return next(x for x in CLASSES if x["id"] == class_id)


def get_game(user_id: int) -> GameState:
    if user_id not in USER_GAMES:
        USER_GAMES[user_id] = GameState()
    return USER_GAMES[user_id]



def should_throttle(user_id: int) -> bool:
    now = time.time()
    last = LAST_ACTION_TS.get(user_id, 0.0)
    if now - last < ACTION_DEBOUNCE_SECONDS:
        return True
    LAST_ACTION_TS[user_id] = now
    return False


async def _delayed_save() -> None:
    await asyncio.sleep(SAVE_DELAY_SECONDS)
    save_games(USER_GAMES)


def schedule_save() -> None:
    global SAVE_TASK
    if SAVE_TASK and not SAVE_TASK.done():
        SAVE_TASK.cancel()
    SAVE_TASK = asyncio.create_task(_delayed_save())


def build_leaderboard_text() -> str:
    players = []
    for _, game in USER_GAMES.items():
        if not game.player:
            continue
        p = game.player
        players.append(
            {
                "name": f"{p.race_name}/{p.class_name}",
                "level": p.level,
                "atk": total_attack(p),
                "def": total_armor(p),
            }
        )

    players.sort(key=lambda x: (-x["level"], -x["atk"], -x["def"]))

    if not players:
        return "Пока нет игроков."

    lines = []
    for i, p in enumerate(players[:20], start=1):
        lines.append(
            f"{i}. {p['name']} | lvl {p['level']} | ATK {p['atk']} | DEF {p['def']}"
        )
    return "\n".join(lines)


async def send_or_edit(update: Update, text: str) -> None:
    keyboard = render_keyboard(get_game(update.effective_user.id))

    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            assert update.effective_message
            await update.effective_message.reply_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.exception("send_or_edit failed: %s", e)
        try:
            if update.effective_message:
                await update.effective_message.reply_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
        except Exception as e2:
            logger.exception("fallback reply_text failed: %s", e2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = get_game(update.effective_user.id)
    await send_or_edit(update, render_text(game))


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with USER_LOCKS[user_id]:
        USER_GAMES[user_id] = GameState()
        save_games(USER_GAMES)
        game = USER_GAMES[user_id]
    await send_or_edit(update, render_text(game))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start — открыть игру\n"
        "/reset — полный сброс прогресса\n"
        "/help — помощь\n\n"
        "После выбора локации можно выбрать конкретного монстра и фармить его без повторного выбора после победы."
    )
    await update.effective_message.reply_text(text)


def random_roll_percent(chance: int) -> bool:
    return random.randint(1, 100) <= chance


def random_int(a: int, b: int) -> int:
    return random.randint(a, b)


def random_choice(items):
    return random.choice(items)


def time_now() -> int:
    return int(time.time())


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    user_id = query.from_user.id

    if should_throttle(user_id):
        return

    async with USER_LOCKS[user_id]:
        try:
                query = update.callback_query
                await query.answer()

                user_id = query.from_user.id
                game = get_game(user_id)
                data = query.data

                if cooldown_left(game) > 0 and data not in {"back_hub", "reset"}:
                    add_log(game, f"Ты мертв. Подожди {cooldown_left(game)} сек.")
                    schedule_save()
                    await send_or_edit(update, render_text(game))
                    return

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
                            "Открыт ручной выбор мобов по уровню.",
                        ]

                elif data.startswith("zone:") and game.player:
                    zone_id = data.split(":", 1)[1]
                    game.current_zone_id = zone_id
                    game.stage = "zone_select"
                    game.selected_monster_page = 0
                    zone = get_zone(zone_id)
                    add_log(game, f"Локация: {zone['name']}. Выбери монстра.")

                elif data == "monster_page_prev":
                    game.selected_monster_page = max(0, game.selected_monster_page - 1)

                elif data == "monster_page_next" and game.current_zone_id:
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
                        add_log(game, f"Цель: {game.enemy['name']} lv.{game.enemy['level']}.")
                        if game.enemy.get("legendary"):
                            add_log(game, "👑 Появился легендарный моб!")

                elif data == "attack" and game.player and game.enemy:
                    crit = random_roll_percent(game.player.crit)
                    dmg = max(1, total_attack(game.player) + random_int(0, 4) - game.enemy["level"])
                    if crit:
                        dmg *= 2
                    game.enemy["hp"] -= dmg
                    add_log(game, f"Ты наносишь {dmg} урона." + (" Крит!" if crit else ""))

                    if game.enemy["hp"] <= 0:
                        dizens_gain = random_int(game.enemy["reward_min"], game.enemy["reward_max"])
                        exp_gain = game.enemy["exp"]
                        loot = random_choice(game.enemy["drops"])

                        game.player.dizens += dizens_gain
                        game.player.exp += exp_gain
                        game.player.loot_count += 1
                        game.player.clears += 1
                        add_log(game, f"Победа. +{dizens_gain} дизен, +{exp_gain} exp, дроп: {loot}.")

            if loot == "Талика Невежества":
                game.player.talics_ignorance += 1
                add_log(game, "Получена Талика Невежества.")
            elif loot == "Талика Покровительства":
                game.player.talics_protection += 1
                add_log(game, "Получена Талика Покровительства.")
            elif loot == "Талика Грации":
                game.player.talics_grace += 1
                add_log(game, "Получена Талика Грации.")
            elif loot == "Компонент":
                game.player.components += 1
                add_log(game, "Получен Компонент.")
            elif loot == "Редкая Руда":
                game.player.rare_ore += 1
                add_log(game, "Получена Редкая Руда.")
            elif loot == "банка HP":
                if game.player.banks < MAX_BANKS:
                    game.player.banks += 1
                    add_log(game, "Получена Банка.")
                else:
                    add_log(game, f"Банка выпала, но инвентарь полон ({MAX_BANKS}).")

            # Доп. дроп таликов теперь работает ВСЕГДА, независимо от основного дропа
            extra_rolls = 10 if game.enemy.get("elite") else 1

            for _ in range(extra_rolls):
                if random_roll_percent(3):
                    game.player.talics_ignorance += 1
                    add_log(game, "Доп. дроп: талик невежества.")
                    break

            for _ in range(extra_rolls):
                if random_roll_percent(3):
                    game.player.talics_protection += 1
                    add_log(game, "Доп. дроп: талик покровительства.")
                    break

            for _ in range(extra_rolls):
                if random_roll_percent(2):
                    game.player.talics_grace += 1
                    add_log(game, "Доп. дроп: талик грации.")
                    break

                            for _ in range(extra_rolls):
                                if random_roll_percent(3):
                                    game.player.talics_protection += 1
                                    add_log(game, "Доп. дроп: талик покровительства.")
                                    break

                            for _ in range(extra_rolls):
                                if random_roll_percent(2):
                                    game.player.talics_grace += 1
                                    add_log(game, "Доп. дроп: талик грации.")
                                    break

                        if game.enemy["name"] == "Гора Руды":
                            if random_roll_percent(15):
                                game.player.rare_ore += 1
                                add_log(game, "⛏ Выпала Редкая Руда (Гора Руды).")

                            if random_roll_percent(15):
                                talic_type = random_choice(["ignorance", "protection", "grace"])
                                if talic_type == "ignorance":
                                    game.player.talics_ignorance += 1
                                    add_log(game, "💠 Выпал талик невежества (Гора Руды).")
                                elif talic_type == "protection":
                                    game.player.talics_protection += 1
                                    add_log(game, "🛡 Выпал талик покровительства (Гора Руды).")
                                else:
                                    game.player.talics_grace += 1
                                    add_log(game, "💨 Выпал талик грации (Гора Руды).")

                        if random_roll_percent(15):
                            game.player.rare_ore += 1
                            add_log(game, "Выпала Редкая Руда.")

                        gear = maybe_gear_drop(
                            game.enemy["level"],
                            game.enemy["is_boss"],
                            game.enemy.get("elite", False),
                        )
                        if gear:
                            if gear.slot == "weapon":
                                game.player.weapon_inventory.append(gear)
                                add_log(game, f"Выпало оружие: {gear.name} +0.")
                            else:
                                game.player.armor_inventory.append(gear)
                                add_log(game, f"Выпала броня: {gear.name} +0.")

                        super_mult = 10 if game.enemy.get("elite") else (5 if game.enemy["is_boss"] else 1)
                        if game.enemy.get("legendary"):
                            super_mult = max(super_mult, 7)

                        if random.randint(1, 1000) <= SUPER_DROP_CHANCES["ancient_container"] * super_mult:
                            game.player.ancient_containers += 1
                            add_log(game, "🔥 Супер-дроп: Древний контейнер.")

                        if random.randint(1, 1000) <= SUPER_DROP_CHANCES["enhancement_core"] * super_mult:
                            game.player.enhancement_cores += 1
                            add_log(game, "✨ Супер-дроп: Ядро усиления.")

                        if random.randint(1, 1000) <= SUPER_DROP_CHANCES["absolute_talic"] * super_mult:
                            game.player.absolute_talics += 1
                            add_log(game, "💎 Супер-дроп: Талик Абсолюта.")

                        level_up(game.player, game, add_log)

                        if game.selected_monster_index is not None and game.current_zone_id:
                            monsters = selected_monsters_for_zone(game.current_zone_id)
                            if 0 <= game.selected_monster_index < len(monsters):
                                game.enemy = generate_enemy(game.current_zone_id, monsters[game.selected_monster_index])
                                add_log(game, f"Следующая цель: {game.enemy['name']} lv.{game.enemy['level']}.")
                                if game.enemy.get("legendary"):
                                    add_log(game, "👑 Появился легендарный моб!")
                            else:
                                game.enemy = None
                                game.stage = "zone_select"
                        else:
                            game.enemy = None
                            game.stage = "zone_select"

                    else:
                        if random_roll_percent(current_dodge(game.player)):
                            add_log(game, f"Ты увернулся от атаки {game.enemy['name']}.")
                        else:
                            enemy_dmg = max(1, game.enemy["attack"] + random_int(0, 4) - total_armor(game.player) // 3)
                            game.player.hp -= enemy_dmg
                            add_log(game, f"{game.enemy['name']} наносит {enemy_dmg} урона.")
                            if game.player.hp <= 0:
                                game.player.hp = 0
                                game.dead_until_ts = time_now() + DEATH_COOLDOWN_SECONDS
                                game.stage = "hub"
                                game.enemy = None
                                add_log(game, "Ты погиб. Все сохранено. Откат 60 секунд.")

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
                    old_banks = game.player.banks
                    game.player.banks = min(MAX_BANKS, game.player.banks + 3)
                    if game.player.banks > old_banks:
                        add_log(game, "На базе ты восстановил здоровье и получил 3 банки.")
                    else:
                        add_log(game, f"На базе ты восстановил здоровье. Лимит банок: {MAX_BANKS}.")

                elif data == "buy_bank" and game.player:
                    price = MARKET_PRICES["buy_bank"]
                    if game.player.banks >= MAX_BANKS:
                        add_log(game, f"Лимит банок: {MAX_BANKS}.")
                    elif game.player.dizens >= price:
                        game.player.dizens -= price
                        game.player.banks = min(MAX_BANKS, game.player.banks + 1)
                        add_log(game, "Куплена 1 банка.")
                    else:
                        add_log(game, "Не хватает дизен.")

                elif data == "buy_components_pack" and game.player:
                    price = MARKET_PRICES["buy_components_pack"]
                    if game.player.dizens >= price:
                        game.player.dizens -= price
                        game.player.components += 5
                        add_log(game, "Куплено 5 компонентов.")
                    else:
                        add_log(game, "Не хватает дизен.")

                elif data == "buy_random_weapon" and game.player:
                    price = MARKET_PRICES["buy_random_weapon"]
                    if game.player.dizens >= price:
                        game.player.dizens -= price
                        gear = make_market_weapon(game.player)
                        game.player.weapon_inventory.append(gear)
                        add_log(game, f"Куплено случайное оружие: {gear.name}.")
                    else:
                        add_log(game, "Не хватает дизен.")

                elif data == "sell_bank" and game.player:
                    if game.player.banks > 0:
                        game.player.banks -= 1
                        add_log(game, "Банка выброшена. Цена продажи: 0.")
                    else:
                        add_log(game, "У тебя нет лишней банки.")

                elif data == "sell_components_pack" and game.player:
                    if game.player.components >= 5:
                        game.player.components -= 5
                        game.player.dizens += MARKET_PRICES["sell_components_pack"]
                        add_log(game, "Продано 5 компонентов.")
                    else:
                        add_log(game, "Не хватает компонентов.")

                elif data == "exchange_rare_ore" and game.player:
                    if game.player.rare_ore >= 30:
                        game.player.rare_ore -= 30
                        game.player.ancient_containers += 1
                        add_log(game, "30 Редкая Руда обменяны на 1 Контейнер.")
                    else:
                        add_log(game, "Не хватает Редкой Руды.")

                elif data.startswith("sell_weapon:") and game.player:
                    idx = int(data.split(":", 1)[1])
                    if 0 <= idx < len(game.player.weapon_inventory):
                        gear_name = game.player.weapon_inventory[idx].name
                        price = sell_weapon_from_inventory(game.player, idx)
                        add_log(game, f"Продано оружие {gear_name} за {price} дизен.")

                elif data == "market_weapon_prev" and game.player:
                    game.market_weapon_page = max(0, game.market_weapon_page - 1)

                elif data == "market_weapon_next" and game.player:
                    max_page = max(0, (len(game.player.weapon_inventory) - 1) // ITEMS_PER_PAGE)
                    game.market_weapon_page = min(max_page, game.market_weapon_page + 1)

                elif data == "open_container" and game.player:
                    if game.player.ancient_containers <= 0:
                        add_log(game, "У тебя нет древнего контейнера.")
                    else:
                        game.player.ancient_containers -= 1
                        gear, text = open_ancient_container(game.player)
                        if gear.slot == "weapon":
                            game.player.weapon_inventory.append(gear)
                        else:
                            game.player.armor_inventory.append(gear)
                        add_log(game, text, f"Получен предмет: {gear.name} +0.")

                elif data == "use_enhancement_core" and game.player:
                    if game.player.enhancement_cores <= 0:
                        add_log(game, "У тебя нет ядра усиления.")
                    elif game.player.weapon_upgrade_buff_active:
                        add_log(game, "Бафф ядра уже активен.")
                    else:
                        game.player.enhancement_cores -= 1
                        game.player.weapon_upgrade_buff_active = True
                        add_log(game, "Ядро активировано. Следующая заточка оружия получит двойной шанс.")

                elif data == "use_absolute_talic" and game.player:
                    gear = current_weapon(game.player)
                    if gear is None:
                        add_log(game, "Сначала экипируй оружие.")
                    elif game.player.absolute_talics <= 0:
                        add_log(game, "У тебя нет Талика Абсолюта.")
                    elif gear.upgrade >= 7:
                        add_log(game, "Оружие уже +7.")
                    else:
                        game.player.absolute_talics -= 1
                        gear.upgrade += 1
                        add_log(game, f"Абсолютная заточка успешна. {gear.name} теперь +{gear.upgrade}.")

                elif data == "equipment" and game.player:
                    game.stage = "equipment"

                elif data == "market" and game.player:
                    game.stage = "market"

                elif data == "leaderboard":
                    game.stage = "leaderboard"
                    game.leaderboard_text = build_leaderboard_text()
                    add_log(game, "Открыт leaderboard.")

                elif data == "salvage_menu" and game.player:
                    game.stage = "salvage"
                    game.salvage_page = 0

                elif data == "salvage_prev" and game.player:
                    game.salvage_page = max(0, game.salvage_page - 1)

                elif data == "salvage_next" and game.player:
                    total_items = len(game.player.weapon_inventory) + len(game.player.armor_inventory)
                    max_page = max(0, (total_items - 1) // ITEMS_PER_PAGE)
                    game.salvage_page = min(max_page, game.salvage_page + 1)

                elif data.startswith("salvage_weapon_pick:") and game.player:
                    idx = int(data.split(":", 1)[1])
                    if 0 <= idx < len(game.player.weapon_inventory):
                        gear = game.player.weapon_inventory[idx]
                        reward = salvage_reward(gear)
                        del game.player.weapon_inventory[idx]
                        if game.player.equipped_weapon_index is not None:
                            if game.player.equipped_weapon_index == idx:
                                game.player.equipped_weapon_index = None
                            elif game.player.equipped_weapon_index > idx:
                                game.player.equipped_weapon_index -= 1
                        game.player.components += reward
                        add_log(game, f"Разобрано оружие {gear.name}. Получено {reward} компонентов.")

                elif data.startswith("salvage_armor_pick:") and game.player:
                    idx = int(data.split(":", 1)[1])
                    if 0 <= idx < len(game.player.armor_inventory):
                        gear = game.player.armor_inventory[idx]
                        reward = salvage_reward(gear)
                        del game.player.armor_inventory[idx]
                        for slot, equipped_idx in list(game.player.equipped_armor.items()):
                            if equipped_idx is not None:
                                if equipped_idx == idx:
                                    game.player.equipped_armor[slot] = None
                                elif equipped_idx > idx:
                                    game.player.equipped_armor[slot] = equipped_idx - 1
                        game.player.components += reward
                        add_log(game, f"Разобрана броня {gear.name}. Получено {reward} компонентов.")

                elif data.startswith("equip_weapon:") and game.player:
                    idx = int(data.split(":", 1)[1])
                    if 0 <= idx < len(game.player.weapon_inventory):
                        game.player.equipped_weapon_index = idx
                        weapon = game.player.weapon_inventory[idx]
                        add_log(game, f"Экипировано оружие: {weapon.name} +{weapon.upgrade}.")

                elif data.startswith("equip_armor:") and game.player:
                    idx = int(data.split(":", 1)[1])
                    if 0 <= idx < len(game.player.armor_inventory):
                        chosen = game.player.armor_inventory[idx]
                        game.player.equipped_armor[chosen.slot] = idx
                        add_log(game, f"Экипировано: {ARMOR_SLOT_NAMES[chosen.slot]} {chosen.name} +{chosen.upgrade}.")

                elif data == "upgrade_weapon" and game.player:
                    gear = current_weapon(game.player)
                    if gear is None:
                        add_log(game, "Сначала экипируй оружие.")
                    elif game.player.talics_ignorance <= 0:
                        add_log(game, "Нет талика невежества.")
                    elif gear.upgrade >= 7:
                        add_log(game, "Оружие уже +7.")
                    else:
                        rule = UPGRADE_CHANCES[gear.upgrade]
                        chance = rule["chance"]

                        if game.player.weapon_upgrade_buff_active:
                            chance = min(100, chance * 2)
                            game.player.weapon_upgrade_buff_active = False
                            add_log(game, f"Ядро усиления сработало. Шанс заточки: {chance}%.")

                        game.player.talics_ignorance -= 1
                        if random_roll_percent(chance):
                            gear.upgrade = rule["next"]
                            add_log(game, f"Успех. {gear.name} теперь +{gear.upgrade}.")
                        else:
                            add_log(game, f"Неудача. {gear.name} осталось на +{gear.upgrade}.")

                elif data.startswith("upgrade_armor_slot:") and game.player:
                    slot = data.split(":", 1)[1]
                    piece = current_armor_piece(game.player, slot)
                    if piece is None:
                        add_log(game, f"Сначала экипируй {ARMOR_SLOT_NAMES[slot].lower()}.")
                    elif slot == "boots":
                        add_log(game, "Тапки точатся только таликами грации.")
                    elif game.player.talics_protection <= 0:
                        add_log(game, "Нет талика покровительства.")
                    elif piece.upgrade >= 7:
                        add_log(game, f"{piece.name} уже +7.")
                    else:
                        rule = UPGRADE_CHANCES[piece.upgrade]
                        game.player.talics_protection -= 1
                        if random_roll_percent(rule["chance"]):
                            piece.upgrade = rule["next"]
                            add_log(game, f"Успех. {piece.name} теперь +{piece.upgrade}.")
                        else:
                            add_log(game, f"Неудача. {piece.name} осталось на +{piece.upgrade}.")

                elif data == "upgrade_boots_grace" and game.player:
                    boots = current_armor_piece(game.player, "boots")
                    if boots is None:
                        add_log(game, "Сначала экипируй тапки.")
                    elif game.player.talics_grace <= 0:
                        add_log(game, "Нет талика грации.")
                    elif boots.upgrade >= 7:
                        add_log(game, "Тапки уже +7.")
                    else:
                        rule = UPGRADE_CHANCES[boots.upgrade]
                        game.player.talics_grace -= 1
                        if random_roll_percent(rule["chance"]):
                            boots.upgrade = rule["next"]
                            add_log(game, f"Успех. {boots.name} теперь +{boots.upgrade}. Уворот: {DODGE_UPGRADES[boots.upgrade]}%.")
                        else:
                            add_log(game, f"Неудача. {boots.name} осталось на +{boots.upgrade}.")

                elif data == "craft_weapon" and game.player:
                    gear = craft_item(game.player, "weapon", max(1, game.player.level))
                    if gear:
                        game.player.weapon_inventory.append(gear)
                        add_log(game, f"Скрафчено оружие: {gear.name}. Стоимость: {game.player.level * 10} компонентов.")
                    else:
                        add_log(game, f"Не хватает компонентов. Нужно: {game.player.level * 10}.")

                elif data == "craft_armor" and game.player:
                    slot = random_choice(ARMOR_SLOTS)
                    gear = craft_item(game.player, slot, max(1, game.player.level))
                    if gear:
                        game.player.armor_inventory.append(gear)
                        add_log(game, f"Скрафчена броня: {gear.name}. Стоимость: {game.player.level * 10} компонентов.")
                    else:
                        add_log(game, f"Не хватает компонентов. Нужно: {game.player.level * 10}.")

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

                schedule_save()
                await send_or_edit(update, render_text(game))
        except Exception as e:
            logger.exception("on_button failed for user %s data=%s: %s", user_id, query.data if query else None, e)
            try:
                game = get_game(user_id)
                add_log(game, "Произошла ошибка. Попробуй ещё раз.")
                await send_or_edit(update, render_text(game))
            except Exception:
                pass


def _run_self_checks() -> None:
    assert exp_needed_for_next(2) > exp_needed_for_next(1)
    assert len(selected_monsters_for_zone("alliance_outpost")) >= 20

    player = Player("Беллато", "Штурмовик", 1, 0, 100, 100, 10, 5, 10, 0, 0, 1)
    boots = Gear("b1", "Test Boots", "boots", 5, "normal", "обычный", 3, 4)
    player.armor_inventory.append(boots)
    player.equipped_armor["boots"] = 0
    assert current_dodge(player) == 20

    elite = generate_enemy(
        "haram_colony",
        {"name": "Создатель Убийц Альфа (А)", "level": 40, "elite": True, "boss": None},
    )
    assert elite["hp"] > 4000
    assert elite["attack"] > 100

    empty_game = GameState()
    rendered = render_text(empty_game)
    assert "RF Online: Text Raid" in rendered
    assert "Выбери расу и класс" in rendered


def main() -> None:
    _run_self_checks()

    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError(
            "Set BOT_TOKEN environment variable or replace PUT_YOUR_BOT_TOKEN_HERE in the file."
        )

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling()


if __name__ == "__main__":
    main()
