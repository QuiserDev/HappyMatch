import arcade

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BGM, GAMEOVER_SOUND
from managers import GameManager


class HMBaseView(arcade.View):
    def __init__(self) -> None:
        super().__init__()

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.ASH_GREY)

    def on_draw(self) -> None:
        self.clear()


class MenuView(HMBaseView):
    def __init__(self) -> None:
        super().__init__()


class GameOverView(HMBaseView):
    def __init__(self) -> None:
        super().__init__()
        self.text_game_over = arcade.Text(
            "Game Over",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            font_size=50,
            anchor_x="center",
        )
        self.text_restart = arcade.Text(
            "Press R to restart",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 100,
            font_size=30,
            anchor_x="center",
        )

    def on_show_view(self) -> None:
        super().on_show_view()
        arcade.play_sound(GAMEOVER_SOUND, volume=0.3)

    def on_draw(self) -> None:
        super().on_draw()
        self.text_game_over.draw()
        self.text_restart.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.R:
            self.window.show_view(GameGridMapView())


class GameGridMapView(HMBaseView):
    def __init__(self) -> None:
        super().__init__()
        self.manager = GameManager(self.on_game_over)
        self.map = self.manager.map
        self.bgm_player = arcade.play_sound(BGM,volume=0.3 ,loop=True)

    def on_game_over(self) -> None:
        if self.bgm_player is not None and self.bgm_player.playing:
            arcade.stop_sound(self.bgm_player)
        self.window.show_view(GameOverView())

    def on_draw(self) -> None:
        super().on_draw()
        self.map.draw()

    def on_update(self, delta_time: float) -> None:
        self.map.update()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.manager.animating_blocks != 0:
            return
        l = arcade.get_sprites_at_point((x, y), self.map.block_list)
        for blk in l:
            self.manager.clicked_block = blk
