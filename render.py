from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ARMOR_SLOT_NAMES, ARMOR_SLOTS, ITEMS_PER_PAGE, MAX_LEVEL
from data import CLASSES, MARKET_PRICES, RACES, ZONES
from enemies import selected_monsters_for_zone
from stats import current_dodge, exp_needed_for_next, set_bonus, total_armor, total_attack
from utils import cooldown_left, esc, paged_items


def render_text(game) -> str:
    lines = ["<b>RF Online: Text Raid</b>"]

    if not game.player:
        lines.append("Выбери расу и класс, затем начни кампанию.")
    else:
        p = game.player
        set_info = set_bonus(p)
        buff_line = "Бафф ядра активен\n" if p.weapon_upgrade_buff_active else ""

        lines.append(
            f"<b>{esc(p.race_name)} / {esc(p.class_name)}</b> | lvl {p.level}/{MAX_LEVEL}\n"
            f"HP: {p.hp}/{p.max_hp}\n"
            f"ATK: {total_attack(p)} | ARM: {total_armor(p)}\n"
            f"Крит: {p.crit}% | Уворот: {current_dodge(p)}%\n"
            f"Дизены: {p.dizens} | Банки: {p.banks} | Компоненты: {p.components}\n"
            f"Талики: Н {p.talics_ignorance} / П {p.talics_protection} / Г {p.talics_grace}\n"
            f"Супер-дропы: Контейнеры {p.ancient_containers} / Ядра {p.enhancement_cores} / Абсолют {p.absolute_talics}\n"
            f"{buff_line}"
            f"Опыт: {p.exp}/{exp_needed_for_next(p.level) if p.level < MAX_LEVEL else 'MAX'}\n"
            f"Бонус набора: ATK +{set_info['attack']}, ARM +{set_info['armor']}"
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

    if game.stage == "market" and game.player:
        lines.append(
            "<b>Рынок:</b>\n"
            f"Банка: купить {MARKET_PRICES['buy_bank']}, продать {MARKET_PRICES['sell_bank']}\n"
            f"5 компонентов: купить {MARKET_PRICES['buy_components_pack']}, продать {MARKET_PRICES['sell_components_pack']}\n"
            f"Случайное оружие: {MARKET_PRICES['buy_random_weapon']}"
        )

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
                InlineKeyboardButton("Ядро → буст оружия", callback_data="use_enhancement_core"),
                InlineKeyboardButton("Абсолют +1 оружию", callback_data="use_absolute_talic"),
            ]
        )

        weapon_items = paged_items(
            game.player.weapon_inventory,
            game.market_weapon_page,
            ITEMS_PER_PAGE,
        )
        for gear in weapon_items:
            idx = game.player.weapon_inventory.index(gear)
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
        rows.append(
            [
                InlineKeyboardButton("Разобрать оружие", callback_data="salvage_weapon"),
                InlineKeyboardButton("Разобрать броню", callback_data="salvage_armor"),
            ]
        )
        rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
        return InlineKeyboardMarkup(rows)

    rows.append([InlineKeyboardButton("На базу", callback_data="back_hub")])
    return InlineKeyboardMarkup(rows)
