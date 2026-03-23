import html
import time
from typing import List

from models import GameState


def now_ts() -> int:
    return int(time.time())


def cooldown_left(game: GameState) -> int:
    if not game.dead_until_ts:
        return 0
    return max(0, game.dead_until_ts - now_ts())


def esc(text: str) -> str:
    return html.escape(str(text))


def add_log(game: GameState, *lines: str) -> None:
    game.log.extend(lines)
    game.log = game.log[-8:]


def paged_items(items: List, page: int, items_per_page: int) -> List:
    start = page * items_per_page
    return items[start:start + items_per_page]
