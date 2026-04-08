import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    import os
    os.chdir(sys._MEIPASS)

import arcade

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from views import GameGridMapView

# todo 积分系统
# todo GUI功能
# todo 音效


class HappyMatch(arcade.Window):
    def __init__(self, width: int, height: int, title: str) -> None:
        super().__init__(width, height)
        self.set_caption(title)


if __name__ == "__main__":
    window = HappyMatch(SCREEN_WIDTH, SCREEN_HEIGHT, "Happy Match")
    window.show_view(GameGridMapView())
    arcade.run()
