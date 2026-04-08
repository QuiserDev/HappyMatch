import arcade

SCREEN_WIDTH = 600  # 窗口宽度
SCREEN_HEIGHT = 770  # 窗口高度
MARGIN = 50  # 边距

GRID_ROWS = 8
GRID_COLS = 6

BLOCK_WIDTH = (SCREEN_WIDTH - MARGIN * 2) // GRID_COLS

BLOCK_SCALE = BLOCK_WIDTH / 200  # 素材宽度有参差，大体为200px
BLOCK_BACKGROUND_SCALE = BLOCK_WIDTH / 64  # 素材为64px的正方形

BGM = arcade.load_sound("assets/bgm.ogg")
CLICK_SOUND = arcade.load_sound("assets/click.mp3")
GAMEOVER_SOUND = arcade.load_sound("assets/on_gameover.ogg")
