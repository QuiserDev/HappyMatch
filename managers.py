import random
from typing import List, Tuple, Optional, Callable

import arcade

from models import Block, GridMap, BlockType
from constants import GRID_ROWS, GRID_COLS, BLOCK_WIDTH, MARGIN, CLICK_SOUND


class GameManager:
    def __init__(self, on_game_over: Callable[[], None]) -> None:
        self._on_game_over = on_game_over
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

    def is_game_over(self) -> bool:
        for row in range(self.map.row):
            for col in range(self.map.col - 1):
                idx1 = row * self.map.col + col
                idx2 = row * self.map.col + col + 1
                self.map.block_list.swap(idx1, idx2)
                mergeable = self.get_mergeable()
                self.map.block_list.swap(idx1, idx2)
                if mergeable:
                    return False
        for row in range(self.map.row - 1):
            for col in range(self.map.col):
                idx1 = row * self.map.col + col
                idx2 = (row + 1) * self.map.col + col
                self.map.block_list.swap(idx1, idx2)
                mergeable = self.get_mergeable()
                self.map.block_list.swap(idx1, idx2)
                if mergeable:
                    return False
        return True

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
            if self.is_game_over():
                self.on_game_over()
            mergeable = self.get_mergeable()
            if mergeable:
                arcade.play_sound(CLICK_SOUND)
                self.fall_down_with_animation(mergeable)
            elif self.just_swapped_blocks:
                self.swap_with_animation(*self.just_swapped_blocks)
            self.just_swapped_blocks = []

    def on_game_over(self) -> None:
        self._on_game_over()

    def on_swap_animate_end(self, block: Block) -> None:
        self.swapping_blocks -= 1
        self.on_animate_end(block)

    def on_fall_animate_end(self, block: Block) -> None:
        self.falling_blocks -= 1
        self.on_animate_end(block)
