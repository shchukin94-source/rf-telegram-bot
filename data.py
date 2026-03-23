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
    ],
    "haram_colony": [
        {"name": "Гиперморф", "level": 21},
        {"name": "Взрослый Трицератопс", "level": 22},
        {"name": "Змееголов Убийца", "level": 23},
        {"name": "Змееголов Ракетчик", "level": 24},
        {"name": "Слизень", "level": 25},
        {"name": "Наяда", "level": 26},
        {"name": "Древний Скарабей", "level": 27},
        {"name": "Брутальная Медведка", "level": 28},
        {"name": "Болотный Гиперморф", "level": 29},
        {"name": "Богомол", "level": 30},
        {"name": "Богомол Доминант", "level": 31},
        {"name": "Король Змееголовов", "level": 34},
        {"name": "Создатель Убийц Альфа (А)", "level": 40, "elite": True},
    ],
    "volcano": [
        {"name": "Магмойд", "level": 40},
        {"name": "Мотылек", "level": 41},
        {"name": "Сверкающий Мотылек", "level": 42},
        {"name": "Капитан Клувер", "level": 43},
        {"name": "Магмовый Убийца", "level": 44},
        {"name": "Орк Предводитель", "level": 45},
        {"name": "Гигансткий Орк (А)", "level": 46, "elite": True},
        {"name": "Красный Псевдодракон", "level": 47},
    ],
    "krag_mines": [
        {"name": "Шахтный Разоритель", "level": 48},
        {"name": "Глубинный Крушитель", "level": 49},
        {"name": "Пещерный Тиран", "level": 50},
    ],
}

ZONES = [
    {
        "id": "alliance_outpost",
        "name": "Аванпост Альянса",
        "text": "Стартовая территория с мобами 1-20 уровня.",
        "loot": ["необработанная руда", "банка HP", "Talic Fragment"],
        "bosses": [
            {
                "name": "Командир Аванпоста",
                "level": 15,
                "drops": ["талик невежества", "талик покровительства", "талик грации", "ящик офицера"],
                "dizens": [35, 55],
            },
            {
                "name": "Зверь Альянса",
                "level": 20,
                "drops": ["талик невежества", "талик грации", "редкий контейнер аванпоста"],
                "dizens": [45, 70],
            },
        ],
    },
    {
        "id": "haram_colony",
        "name": "Колония Харам",
        "text": "Болотная локация с мобами 21-40 уровня.",
        "loot": ["Blue Ore", "банка HP", "Talic Crystal", "анимус-чип"],
        "bosses": [
            {
                "name": "Хранитель Харам",
                "level": 31,
                "drops": ["талик невежества", "талик покровительства", "талик грации", "контейнер Харам"],
                "dizens": [70, 100],
            },
            {
                "name": "Кровавый Берсерк",
                "level": 34,
                "drops": ["талик невежества", "талик грации", "ядро Харам"],
                "dizens": [80, 115],
            },
        ],
    },
    {
        "id": "volcano",
        "name": "Вулкан",
        "text": "Огненная локация с мобами 40-47 уровня.",
        "loot": ["Red Ore", "банка HP", "Talic Crystal", "Intense Part"],
        "bosses": [
            {
                "name": "Властитель Вулкана",
                "level": 47,
                "drops": ["талик невежества", "талик покровительства", "талик грации", "Leon Core"],
                "dizens": [120, 170],
            },
            {
                "name": "Пылающий Тиран",
                "level": 48,
                "drops": ["талик покровительства", "талик грации", "сундук Вулкана"],
                "dizens": [130, 185],
            },
        ],
    },
    {
        "id": "krag_mines",
        "name": "Краговые Шахты",
        "text": "Эндгейм зона с топовым дропом.",
        "loot": ["Golden Ore", "банка HP", "Rare Box", "Leon Fragment"],
        "bosses": [
            {
                "name": "Король Шахт",
                "level": 50,
                "drops": ["талик невежества", "талик покровительства", "талик грации", "Leon Relic"],
                "dizens": [200, 280],
            },
            {
                "name": "Леон Надзиратель",
                "level": 50,
                "drops": ["талик невежества", "талик грации", "набор шахт"],
                "dizens": [180, 250],
            },
        ],
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

GEAR_TIERS = [
    {"id": "normal", "name": "обычный", "weapon_mult": 1.0, "armor_mult": 1.0, "weight": 66},
    {"id": "int", "name": "инт", "weapon_mult": 1.28, "armor_mult": 1.25, "weight": 22},
    {"id": "type_c", "name": "тип с", "weapon_mult": 1.68, "armor_mult": 1.62, "weight": 9},
    {"id": "leon", "name": "леон", "weapon_mult": 2.25, "armor_mult": 2.10, "weight": 3},
]

WEAPON_NAMES = [
    "Нож Flym",
    "Клинок Wing",
    "Пускатель Digger",
    "Копьё Flem",
    "Разрушитель Crawler",
    "Леон Блейд",
]

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

MARKET_PRICES = {
    "buy_bank": 20,
    "buy_components_pack": 25,      # +5 компонентов
    "buy_random_weapon": 120,
    "sell_bank": 8,
    "sell_components_pack": 15,     # -5 компонентов
}

SUPER_DROP_CHANCES = {
    "ancient_container": 10,   # 1.0% из 1000
    "enhancement_core": 5,     # 0.5%
    "absolute_talic": 2,       # 0.2%
}

MARKET_PRICES = {
    "buy_bank": 20,
    "buy_components_pack": 25,
    "buy_random_weapon": 120,
    "sell_bank": 8,
    "sell_components_pack": 15,
    "rare_ore_for_container": 30,
}

SUPER_DROP_CHANCES = {
    "ancient_container": 10,
    "enhancement_core": 5,
    "absolute_talic": 2,
}
