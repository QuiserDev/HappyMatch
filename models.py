from enum import Enum
import random
import arcade
from typing import Any, Callable, Tuple, Optional
from pyglet.math import Vec2

from constants import MARGIN, BLOCK_SCALE, BLOCK_BACKGROUND_SCALE, BLOCK_WIDTH


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

    def draw(self) -> None:
        if self.clicked_block is not None:
            self.background_sprite.position = self.clicked_block.position
            self.bg_sprite_list.draw()
        self.block_list.draw()

    def update(self, delta_time: float = 1 / 60, *args: Any, **kwargs: Any) -> None:
        self.block_list.update()
