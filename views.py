import arcade
from managers import GameManager


class GameGridMapView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.manager = GameManager()
        self.map = self.manager.map

    def on_draw(self) -> None:
        self.clear()
        self.map.draw()

    def on_update(self, delta_time: float) -> None:
        self.map.update()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.manager.animating_blocks != 0:
            return
        l = arcade.get_sprites_at_point((x, y), self.map.block_list)
        for blk in l:
            self.manager.clicked_block = blk

        arcade.get_image()
