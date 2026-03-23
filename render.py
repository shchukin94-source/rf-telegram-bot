from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ARMOR_SLOT_NAMES, ARMOR_SLOTS, ITEMS_PER_PAGE, MAX_LEVEL
from data import CLASSES, MARKET_PRICES, RACES, ZONES
from enemies import selected_monsters_for_zone
from stats import (
    current_armor_piece,
    current_dodge,
    current_weapon,
    exp_needed_for_next,
    set_bonus,
    total_armor,
    total_attack,
)
from utils import cooldown_left, esc, paged_items


def render_text(game) -> str:
    lines = ["<b>RF Online: Text Raid</b>"]

    if not game.player:
        lines.append("Выбери расу и класс, затем начни кампанию.")
        lines.append("<b>Журнал:</b>\n" + esc("\n".join(game.log[-8:])))
        return "\n\n".join(lines)

    p = game.player
    set_info = set_bonus(p)

    if game.stage == "combat":
        lines.append(
            f"<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}/{MAX_LEVEL}\n"
            f"HP: {p.hp}/{p.max_hp}\n"
            f"ATK: {total_attack(p)} | DEF: {total_armor(p)}\n"
            f"Крит: {p.crit}% | Уворот: {current_dodge(p)}%\n"
            f"Дизены: {p.dizens} | Банки: {p.banks} | Компоненты: {p.components}\n"
            f"Талики: Невежества {p.talics_ignorance} / Покровительства {p.talics_protection} / Грации {p.talics_grace}\n"
            f"Опыт: {p.exp}/{exp_needed_for_next(p.level) if p.level < MAX_LEVEL else 'MAX'}"
        )
    else:
        weapon = current_weapon(p)
        armor_lines = []
        for slot in ARMOR_SLOTS:
            piece = current_armor_piece(p, slot)
            piece_name = f"{piece.name} +{piece.upgrade}" if piece else "нет"
            armor_lines.append(f"{ARMOR_SLOT_NAMES[slot]}: {piece_name}")

        buff_line = "Бафф ядра активен\n" if p.weapon_upgrade_buff_active else ""

        lines.append(
            f"<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}/{MAX_LEVEL}\n"
            f"HP: {p.hp}/{p.max_hp}\n"
            f"ATK: {total_attack(p)} | DEF: {total_armor(p)}\n"
            f"Крит: {p.crit}% | Уворот: {current_dodge(p)}%\n"
            f"Дизены: {p.dizens} | Банки: {p.banks} | Компоненты: {p.components} | Редкая Руда: {p.rare_ore}\n"
            f"Талики: Невежества {p.talics_ignorance} / Покровительства {p.talics_protection} / Грации {p.talics_grace}\n"
            f"Супер-дропы: Контейнеры {p.ancient_containers} / Ядра {p.enhancement_cores} / Абсолют {p.absolute_talics}\n"
            f"{buff_line}"
            f"Оружие: {esc(f'{weapon.name} +{weapon.upgrade}' if weapon else 'нет')}\n"
            f"{esc(chr(10).join(armor_lines))}\n"
            f"Опыт: {p.exp}/{exp_needed_for_next(p.level) if p.level < MAX_LEVEL else 'MAX'}\n"
            f"Бонус набора: ATK +{set_info['attack']}, DEF +{set_info['armor']}"
        )

    if game.current_zone_id and game.stage == "zone_select":
        monsters = selected_monsters_for_zone(game.current_zone_id)
        page_items = paged_items(monsters, game.selected_monster_page, ITEMS_PER_PAGE)
        monster_text = "\n".join(
            f"{idx + 1}. {m['name']} ({m['level']})"
            for idx, m in enumerate(
                page_items,
                start=game.selected_monster_page * ITEMS_PER_PAGE,
            )
        )
        lines.append(
            f"<b>Выбор монстра:</b> стр. {game.selected_monster_page + 1}\n"
            f"{esc(monster_text or 'нет монстров')}"
        )

    if game.enemy:
        lines.append(
            f"<b>Монстр:</b> {esc(game.enemy['name'])} | lvl {game.enemy['level']}\n"
            f"HP: {game.enemy['hp']}/{game.enemy['max_hp']} | EXP: {game.enemy['exp']}\n"
            f"Дроп: {esc(', '.join(game.enemy['drops']))}"
        )

    if game.stage == "market":
        lines.append(
            "<b>Рынок:</b>\n"
            f"Банка: купить {MARKET_PRICES['buy_bank']}, продать {MARKET_PRICES['sell_bank']}\n"
            f"5 компонентов: купить {MARKET_PRICES['buy_components_pack']}, продать {MARKET_PRICES['sell_components_pack']}\n"
            f"Случайное оружие: {MARKET_PRICES['buy_random_weapon']}\n"
            "30 Редкая Руда -> 1 Контейнер"
        )

    if game.stage == "salvage":
        all_items = []

        for i, gear in enumerate(p.weapon_inventory):
            if i == p.equipped_weapon_index:
                continue
            all_items.append(("weapon", i, gear))

        equipped_armor_indexes = {
            idx for idx in p.equipped_armor.values() if idx is not None
        }

        for i, gear in enumerate(p.armor_inventory):
            if i in equipped_armor_indexes:
                continue
            all_items.append(("armor", i, gear))

        page_items = paged_items(all_items, game.salvage_page, ITEMS_PER_PAGE)
        salvage_text = "\n".join(
            f"{idx + 1}. {gear.name} +{gear.upgrade} -> {gear.level} комп."
            for idx, (_, _, gear) in enumerate(
                page_items,
                start=game.salvage_page * ITEMS_PER_PAGE,
            )
        )
        lines.append(
            f"<b>Разборка:</b> стр. {game.salvage_page + 1}\n"
            f"{esc(salvage_text or 'Нет предметов для разборки')}"
        )

    if game.stage == "leaderboard" and hasattr(game, "leaderboard_text"):
        lines.append(f"<b>Leaderboard:</b>\n{esc(game.leaderboard_text)}")

    if cooldown_left(game) > 0:
        lines.append(f"<b>Откат после смерти:</b> {cooldown_left(game)} сек.")

    lines.append("<b>Журнал:</b>\n" + esc("\n".join(game.log[-8:])))
    return "\n\n".join(lines)


def render_keyboard(game) -> InlineKeyboardMarkup:
    rows = []

    if not game.player:
        rows.append(
            [InlineKeyboardButton(r["name"], callback_data=f"race:{r['id']}") for r in RACES]
        )
        rows.append(
            [InlineKeyboardButton(c["name"], callback_data=f"class:{c['id']}") for c in CLASSES]
        )
        rows.append([InlineKeyboardButton("Начать кампанию", callback_data="start_game")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "hub":
        zone_buttons = [InlineKeyboardButton(z["name"], callback_data=f"zone:{z['id']}") for z in ZONES]
        for i in range(0, len(zone_buttons), 2):
            rows.append(zone_buttons[i:i + 2])

        rows.append(
            [
                InlineKeyboardButton("Отдохнуть", callback_data="rest"),
                InlineKeyboardButton("Снаряжение", callback_data="equipment"),
            ]
        )
        rows.append([InlineKeyboardButton("Рынок", callback_data="market")])
        rows.append([InlineKeyboardButton("Leaderboard", callback_data="leaderboard")])
        rows.append(
            [
                InlineKeyboardButton("Крафт оружия", callback_data="craft_weapon"),
                InlineKeyboardButton("Крафт брони", callback_data="craft_armor"),
            ]
        )
        return InlineKeyboardMarkup(rows)

    if game.stage == "zone_select":
        monsters = selected_monsters_for_zone(game.current_zone_id)
        page_items = paged_items(monsters, game.selected_monster_page, ITEMS_PER_PAGE)

        for idx, monster in enumerate(
            page_items,
            start=game.selected_monster_page * ITEMS_PER_PAGE,
        ):
            rows.append(
                [
                    InlineKeyboardButton(
                        f"{monster['name']} ({monster['level']})",
                        callback_data=f"pick_monster:{idx}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton("◀️", callback_data="monster_page_prev"),
                InlineKeyboardButton("▶️", callback_data="monster_page_next"),
            ]
        )
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "combat":
        rows.append(
            [
                InlineKeyboardButton("Атаковать", callback_data="attack"),
                InlineKeyboardButton("Банка", callback_data="bank"),
            ]
        )
        rows.append([InlineKeyboardButton("Сменить монстра", callback_data="back_zone_select")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "market":
        rows.append(
            [
                InlineKeyboardButton(f"Купить банку ({MARKET_PRICES['buy_bank']})", callback_data="buy_bank"),
                InlineKeyboardButton("Купить 5 комп. (25)", callback_data="buy_components_pack"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(f"Случайное оружие ({MARKET_PRICES['buy_random_weapon']})", callback_data="buy_random_weapon"),
                InlineKeyboardButton("Открыть контейнер", callback_data="open_container"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton("Продать 1 банку", callback_data="sell_bank"),
                InlineKeyboardButton("Продать 5 комп.", callback_data="sell_components_pack"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton("30 Редкая Руда -> Контейнер", callback_data="exchange_rare_ore"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton("Ядро -> буст оружия", callback_data="use_enhancement_core"),
                InlineKeyboardButton("Абсолют +1 оружию", callback_data="use_absolute_talic"),
            ]
        )

        market_weapons = [
            (idx, gear)
            for idx, gear in enumerate(game.player.weapon_inventory)
            if idx != game.player.equipped_weapon_index
        ]

        weapon_items = paged_items(
            market_weapons,
            game.market_weapon_page,
            ITEMS_PER_PAGE,
        )
        for idx, gear in weapon_items:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"Продать {gear.name} +{gear.upgrade}",
                        callback_data=f"sell_weapon:{idx}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton("◀️ Продажа", callback_data="market_weapon_prev"),
                InlineKeyboardButton("Продажа ▶️", callback_data="market_weapon_next"),
            ]
        )
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "salvage":
        all_items = []

        for i, gear in enumerate(game.player.weapon_inventory):
            if i == game.player.equipped_weapon_index:
                continue
            all_items.append(("weapon", i, gear))

        equipped_armor_indexes = {
            idx for idx in game.player.equipped_armor.values() if idx is not None
        }

        for i, gear in enumerate(game.player.armor_inventory):
            if i in equipped_armor_indexes:
                continue
            all_items.append(("armor", i, gear))

        page_items = paged_items(all_items, game.salvage_page, ITEMS_PER_PAGE)
        for item_type, idx, gear in page_items:
            if item_type == "weapon":
                rows.append([InlineKeyboardButton(f"Разобрать {gear.name} +{gear.upgrade}", callback_data=f"salvage_weapon_pick:{idx}")])
            else:
                rows.append([InlineKeyboardButton(f"Разобрать {gear.name} +{gear.upgrade}", callback_data=f"salvage_armor_pick:{idx}")])

        rows.append(
            [
                InlineKeyboardButton("◀️", callback_data="salvage_prev"),
                InlineKeyboardButton("▶️", callback_data="salvage_next"),
            ]
        )
        rows.append([InlineKeyboardButton("Назад в снаряжение", callback_data="equipment")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "leaderboard":
        rows.append([InlineKeyboardButton("Обновить", callback_data="leaderboard")])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    if game.stage == "equipment":
        weapon_items = paged_items(
            game.player.weapon_inventory,
            game.equipment_page_weapon,
            ITEMS_PER_PAGE,
        )
        for gear in weapon_items:
            idx = game.player.weapon_inventory.index(gear)
            rows.append(
                [InlineKeyboardButton(f"Надеть оружие {idx + 1}", callback_data=f"equip_weapon:{idx}")]
            )

        rows.append(
            [
                InlineKeyboardButton("◀️ Оружие", callback_data="weapon_page_prev"),
                InlineKeyboardButton("Оружие ▶️", callback_data="weapon_page_next"),
            ]
        )

        for slot in ARMOR_SLOTS:
            slot_items = [g for g in game.player.armor_inventory if g.slot == slot]
            items = paged_items(
                slot_items,
                game.equipment_page_armor.get(slot, 0),
                ITEMS_PER_PAGE,
            )

            for gear in items:
                idx = game.player.armor_inventory.index(gear)
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"{ARMOR_SLOT_NAMES[slot]} {idx + 1}",
                            callback_data=f"equip_armor:{idx}",
                        )
                    ]
                )

            rows.append(
                [
                    InlineKeyboardButton(
                        f"◀️ {ARMOR_SLOT_NAMES[slot]}",
                        callback_data=f"armor_page_prev:{slot}",
                    ),
                    InlineKeyboardButton(
                        f"{ARMOR_SLOT_NAMES[slot]} ▶️",
                        callback_data=f"armor_page_next:{slot}",
                    ),
                ]
            )

            rows.append(
                [
                    InlineKeyboardButton(
                        f"Точить {ARMOR_SLOT_NAMES[slot]}",
                        callback_data=f"upgrade_armor_slot:{slot}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton("Точить оружие", callback_data="upgrade_weapon"),
                InlineKeyboardButton("Точить тапки грацией", callback_data="upgrade_boots_grace"),
            ]
        )
        rows.append([InlineKeyboardButton("Разобрать предмет", callback_data="salvage_menu")])
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
    return InlineKeyboardMarkup(rows)
