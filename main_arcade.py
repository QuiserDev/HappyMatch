import random
from enum import Enum
from typing import Optional, Tuple, Callable, List, Any
import arcade
from pyglet.math import Vec2

# todo 积分系统
# todo GUI功能
# todo 音效

SCREEN_WIDTH = 800  # 窗口宽度
SCREEN_HEIGHT = 800  # 窗口高度
MARGIN = 50  # 边距

GRID_ROWS = 10
GRID_COLS = GRID_ROWS

BLOCK_WIDTH = (SCREEN_WIDTH - MARGIN * 2) // GRID_COLS

BLOCK_SCALE = BLOCK_WIDTH / 200  # 素材宽度有参差，大体为200px
BLOCK_BACKGROUND_SCALE = BLOCK_WIDTH / 64  # 素材为64px的正方形


class BlockType(Enum):
    BEAR = "bear"
    CHICK = "chick"
    DOG = "dog"
    PIG = "pig"
    PARROT = "parrot"
    FROG = "frog"


class Block(arcade.Sprite):
    def __init__(self, block_type: BlockType, scale: float = BLOCK_SCALE) -> None:
        super().__init__(f"assets/{block_type.value}.png", scale)
        self.block_type = block_type
        self.target: Optional[Tuple[float | int, float | int] | Vec2] = None
        self.on_animation_end: Optional[Callable[["Block"], None]] = None

    def update(self, delta_time: float = 1 / 60, *args: Any, **kwargs: Any) -> None:
        if self.target is not None:
            self.center_x = arcade.math.lerp(self.center_x, self.target[0], 0.1)
            self.center_y = arcade.math.lerp(self.center_y, self.target[1], 0.1)
            if (
                abs(self.target[0] - self.center_x) < 1
                and abs(self.target[1] - self.center_y) < 1
            ):
                # 极度接近，设置为目标值
                self.center_x = self.target[0]
                self.center_y = self.target[1]
                self.target = None
                if self.on_animation_end is not None:
                    self.on_animation_end(self)


class GridMap(arcade.Sprite):
    def __init__(self, row: int, col: int) -> None:
        super().__init__()
        self.clicked_block: Optional[Block] = None

        self.row = row
        self.col = col
        self.block_list: arcade.SpriteList[Block] = arcade.SpriteList()
        self.background_sprite = arcade.Sprite(
            arcade.load_texture(":resources:/gui_basic_assets/checkbox/empty.png"),
            BLOCK_BACKGROUND_SCALE,
        )
        self.bg_sprite_list: arcade.SpriteList[arcade.Sprite] = arcade.SpriteList()
        self.setup()

    def get_rc(self, row: int, col: int) -> Block:
        """通过row col行列的二维信息获取一维列表中的block"""
        return self.block_list[row * self.col + col]

    def is_neighbor(self, block1: Block, block2: Block) -> bool:
        """两个block在画面上是否相邻"""
        idx1 = self.block_list.index(block1)
        idx2 = self.block_list.index(block2)
        r1, c1 = divmod(idx1, self.col)
        r2, c2 = divmod(idx2, self.col)
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def setup(self) -> None:
        self.bg_sprite_list.append(self.background_sprite)

        for row in range(self.row):
            for col in range(self.col):

                bottom_type = None
                left_type = None
                if row >= 2 and (
                    self.get_rc(row - 1, col).block_type
                    == self.get_rc(row - 2, col).block_type
                ):
                    bottom_type = self.get_rc(row - 1, col).block_type
                if col >= 2 and (
                    self.get_rc(row, col - 1).block_type
                    == self.get_rc(row, col - 2).block_type
                ):
                    left_type = self.get_rc(row, col - 1).block_type
                final_type = random.choice(list(BlockType))
                while final_type == bottom_type or final_type == left_type:
                    final_type = random.choice(list(BlockType))

                blk = Block(final_type)
                blk.center_x = MARGIN + col * BLOCK_WIDTH + BLOCK_WIDTH // 2
                blk.center_y = MARGIN + row * BLOCK_WIDTH + BLOCK_WIDTH // 2
                self.block_list.append(blk)
        # todo 避免初始化死局

    def draw(self) -> None:
        if self.clicked_block is not None:
            self.background_sprite.position = self.clicked_block.position
            self.bg_sprite_list.draw()
        self.block_list.draw()

    def update(self, delta_time: float = 1 / 60, *args: Any, **kwargs: Any) -> None:
        self.block_list.update()


class GameManager:
    def __init__(self) -> None:
        self.map = GridMap(GRID_ROWS, GRID_COLS)
        for block in self.map.block_list:
            block.on_animation_end = self.on_fall_animate_end

        self.falling_blocks: int = 0
        self.swapping_blocks: int = 0

        self.just_swapped_blocks: List[Block] = []  # 刚刚交换的两个方块

    @property
    def animating_blocks(self) -> int:
        return self.falling_blocks + self.swapping_blocks

    @property
    def clicked_block(self) -> Optional[Block]:
        return self.map.clicked_block

    @clicked_block.setter
    def clicked_block(self, block: Block) -> None:

        if self.map.clicked_block is None or not self.map.is_neighbor(
            block, self.map.clicked_block
        ):
            self.map.clicked_block = block
        else:
            self.swap_with_animation(self.map.clicked_block, block)
            self.just_swapped_blocks = [block, self.map.clicked_block]
            self.map.clicked_block = None

    def get_mergeable(self) -> List[Tuple[int, int]]:
        mergeable: List[Tuple[int, int]] = []
        for row in range(self.map.row - 2):
            for col in range(self.map.col):
                if (
                    self.map.get_rc(row, col).block_type
                    == self.map.get_rc(row + 1, col).block_type
                    == self.map.get_rc(row + 2, col).block_type
                ):
                    mergeable.append((row, col))
                    mergeable.append((row + 1, col))
                    mergeable.append((row + 2, col))

        for row in range(self.map.row):
            for col in range(self.map.col - 2):
                if (
                    self.map.get_rc(row, col).block_type
                    == self.map.get_rc(row, col + 1).block_type
                    == self.map.get_rc(row, col + 2).block_type
                ):
                    mergeable.append((row, col))
                    mergeable.append((row, col + 1))
                    mergeable.append((row, col + 2))
        return list(set(mergeable))

    def check_game_over(self) -> bool:
        return False
        # todo 无可交换检测

    def swap_with_animation(self, b1: Block, b2: Block) -> None:
        b1.target = b2.center_x, b2.center_y
        b2.target = b1.center_x, b1.center_y
        b1.on_animation_end = self.on_swap_animate_end
        b2.on_animation_end = self.on_swap_animate_end
        idx1 = self.map.block_list.index(b1)
        idx2 = self.map.block_list.index(b2)
        self.swapping_blocks += 2
        self.map.block_list.swap(idx1, idx2)

    def fall_down_with_animation(self, mergeable: List[Tuple[int, int]]) -> None:
        # 统计每列需要消除几个，即生成几个
        count_list: List[int] = [0 for _ in range(self.map.col)]
        for _, col in mergeable:
            count_list[col] += 1

        # 画面外生成
        y_offset = GRID_ROWS * BLOCK_WIDTH  # y轴偏置，加上后会到画面外

        for col in range(self.map.col):
            will_fall_list: List[Block] = []
            first_empty_row = -1
            for row in range(self.map.row):
                if first_empty_row == -1 and (row, col) in mergeable:
                    first_empty_row = row
                    continue
                if first_empty_row != -1 and (row, col) not in mergeable:
                    will_fall_list.append(self.map.get_rc(row, col))
            if first_empty_row == -1:
                continue  # 说明这一列没有空格
            for i in range(count_list[col]):
                block = Block(random.choice(list(BlockType)))
                block.on_animation_end = self.on_fall_animate_end
                block.center_x = MARGIN + col * BLOCK_WIDTH + BLOCK_WIDTH // 2
                block.center_y = MARGIN + i * BLOCK_WIDTH + BLOCK_WIDTH // 2 + y_offset
                will_fall_list.append(block)
            for block in will_fall_list:
                # 给target
                x = MARGIN + col * BLOCK_WIDTH + BLOCK_WIDTH // 2
                y = MARGIN + first_empty_row * BLOCK_WIDTH + BLOCK_WIDTH // 2
                block.target = (x, y)
                if block in self.map.block_list:
                    self.map.block_list.swap(
                        self.map.block_list.index(block),
                        self.map.col * first_empty_row + col,
                    )
                else:
                    self.map.block_list[self.map.col * first_empty_row + col] = block
                self.falling_blocks += 1
                first_empty_row += 1

    def on_animate_end(self, block: Block) -> None:
        """block动画结束的回调函数"""
        if self.animating_blocks == 0:
            mergeable = self.get_mergeable()
            if mergeable:
                self.fall_down_with_animation(mergeable)
            elif self.just_swapped_blocks:
                self.swap_with_animation(*self.just_swapped_blocks)
            self.just_swapped_blocks = []

    def on_swap_animate_end(self, block: Block) -> None:
        self.swapping_blocks -= 1
        self.on_animate_end(block)

    def on_fall_animate_end(self, block: Block) -> None:
        self.falling_blocks -= 1
        self.on_animate_end(block)


class HappyMatch(arcade.Window):
    def __init__(self, width: int, height: int, title: str) -> None:
        super().__init__(width, height)
        self.set_caption(title)
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


if __name__ == "__main__":
    window = HappyMatch(SCREEN_WIDTH, SCREEN_HEIGHT, "Happy Match")
    arcade.run()
