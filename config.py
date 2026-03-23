MAX_LEVEL = 50
ITEMS_PER_PAGE = 5
DROP_GEAR_CHANCE = 7
DEATH_COOLDOWN_SECONDS = 60

ARMOR_SLOTS = ["head", "torso", "legs", "arms", "boots"]

ARMOR_SLOT_NAMES = {
    "head": "Голова",
    "torso": "Торс",
    "legs": "Штаны",
    "arms": "Руки",
    "boots": "Тапки",
}

DODGE_UPGRADES = {
    0: 0,
    1: 5,
    2: 10,
    3: 15,
    4: 20,
    5: 30,
    6: 45,
    7: 60,
}

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
