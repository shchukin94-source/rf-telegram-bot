from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import ARMOR_SLOTS


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
    rare_ore: int = 0
    ancient_containers: int = 0
    enhancement_cores: int = 0
    absolute_talics: int = 0
    weapon_upgrade_buff_active: bool = False
    weapon_inventory: List[Gear] = field(default_factory=list)
    armor_inventory: List[Gear] = field(default_factory=list)
    equipped_weapon_index: Optional[int] = None
    equipped_armor: Dict[str, Optional[int]] = field(
        default_factory=lambda: {slot: None for slot in ARMOR_SLOTS}
    )


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
    dead_until_ts: Optional[int] = None
    equipment_page_weapon: int = 0
    market_weapon_page: int = 0
    salvage_page: int = 0
    stage_page: int = 0
    equipment_page_armor: Dict[str, int] = field(
        default_factory=lambda: {slot: 0 for slot in ARMOR_SLOTS}
    )
    log: List[str] = field(
        default_factory=lambda: [
            "Добро пожаловать в RF Online: Text Raid.",
            "Теперь можно выбирать конкретного монстра по уровню после выбора локации.",
        ]
    )
