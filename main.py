import sys
from enum import Enum
from typing import List, Tuple, Optional
import random
import pygame

# https://www.pygame.org/docs/ref/color_list.html 预设颜色预览网站

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
MAP_SIZE = 10
BLOCK_SIZE = (SCREEN_WIDTH - 100) // MAP_SIZE
SWAP_TIME = 0.5  # 方格移动动画持续时间，单位s
BACKGROUND_COLOR = pygame.Color("grey")


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other)

    def __floordiv__(self, other):
        return Vector(self.x // other, self.y // other)


class Color(Enum):
    CORAL = pygame.Color("coral")
    GREEN = pygame.Color("green")
    CYAN = pygame.Color("cyan")
    YELLOW = pygame.Color("yellow")
    PERU = pygame.Color("peru")
    WHEAT = pygame.Color("wheat")

    @classmethod
    def random(cls) -> "Color":
        return random.choice(list(cls))


class Block:
    def __init__(self, color: Color):
        self.color = color
        self.offset_vector: Vector = Vector(0, 0)  # 总位移
        self.speed = Vector(0, 0)  # 速度向量，单位：像素/s
        self.remaining_time: float = 0.0  # 动画过程还剩多长时间，必须不为负数。单位：s

    def __repr__(self):
        return f"<{self.color}>"

    def __eq__(self, other: "Block"):
        return self.color == other.color

    @property
    def offset(self) -> Vector:
        """动画中，相比原位的偏移"""
        return Vector(
            self.offset_vector.x - self.speed.x * self.remaining_time,
            self.offset_vector.y - self.speed.y * self.remaining_time,
        )


class BlockMap:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.blocks: List[List[Block]] = []
        self._container_top = (SCREEN_HEIGHT - self.height * BLOCK_SIZE) // 2
        self._container_left = 50
        for i in range(height):
            self.blocks.append([])
            for j in range(width):
                self.blocks[i].append(Block(Color.random()))

    def merge(self):
        merge_pos = set()
        for row in range(self.height - 2):
            for col in range(self.width):
                if (
                    self.blocks[row][col]
                    == self.blocks[row + 1][col]
                    == self.blocks[row + 2][col]
                ):
                    merge_pos.add((row, col))
                    merge_pos.add((row + 1, col))
                    merge_pos.add((row + 2, col))
        for row in range(self.height):
            for col in range(self.width - 2):
                if (
                    self.blocks[row][col]
                    == self.blocks[row][col + 1]
                    == self.blocks[row][col + 2]
                ):
                    merge_pos.add((row, col))
                    merge_pos.add((row, col + 1))
                    merge_pos.add((row, col + 2))

        for pos in merge_pos:
            print(pos)

    def swap(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> None:
        r1, c1 = pos1
        r2, c2 = pos2
        self.blocks[r1][c1], self.blocks[r2][c2] = (
            self.blocks[r2][c2],
            self.blocks[r1][c1],
        )

    def pos_to_pixel(self, row: int, col: int) -> Vector:
        """输入格子的下标，返回格子当前（包括动画中）实际像素"""
        base = Vector(
            self._container_left + col * BLOCK_SIZE,
            self._container_top + row * BLOCK_SIZE,
        )
        return base + self.blocks[row][col].offset

    def pixel_to_pos(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """根据鼠标的位置返回对应的下标，不存在就返回None"""
        if (
            x <= self._container_left
            or x >= SCREEN_WIDTH - self._container_left
            or y <= self._container_top
            or y >= SCREEN_HEIGHT - self._container_top
        ):  # 此处判断必须加上等于，否则在边界会列表下标超限报错
            return None
        return (
            (y - self._container_top) // BLOCK_SIZE,
            (x - self._container_left) // BLOCK_SIZE,
        )


class HappyMatch:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.block_map: BlockMap = BlockMap(MAP_SIZE, MAP_SIZE)
        self.current_chosen: Optional[Tuple[int, int]] = None  # 当前选中的格子下标
        self.is_animating: int = 0  # 正在播放动画的格子

    @staticmethod
    def is_neighbor(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """两个坐标是否相邻"""
        return (abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])) == 1

    def _draw_map(self):
        is_hover = False
        for row in range(self.block_map.height):
            for col in range(self.block_map.width):
                block: Block = self.block_map.blocks[row][col]
                pos_vec = self.block_map.pos_to_pixel(row, col)
                rect = (
                    pos_vec.x,
                    pos_vec.y,
                    BLOCK_SIZE,
                    BLOCK_SIZE,
                )
                pygame.draw.rect(self.screen, block.color.value, rect, border_radius=5)

                mouse_pos = pygame.mouse.get_pos()
                pos = self.block_map.pixel_to_pos(*mouse_pos)
                if pos is not None and pos == (row, col):
                    is_hover = True
                is_chosen = self.current_chosen == (row, col)

                border_color = BACKGROUND_COLOR  # 和背景颜色相同的边框，营造分隔的感觉
                if is_chosen:
                    border_color = pygame.Color("grey40")  # 深一点
                elif is_hover:
                    border_color = pygame.Color("grey55")  # 浅一点
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    rect,
                    border_radius=5,
                    width=2 if border_color == BACKGROUND_COLOR else 3,
                )
                is_hover = False

    def _handle_click(self, x: int, y: int) -> None:
        pos = self.block_map.pixel_to_pos(x, y)
        if pos is None:
            self.current_chosen = None
            return
        if self.current_chosen is not None and self.is_neighbor(
            pos, self.current_chosen
        ):
            print("swap")
            self.is_animating += 2
            cur_block = self.block_map.blocks[self.current_chosen[0]][
                self.current_chosen[1]
            ]
            tar_block = self.block_map.blocks[pos[0]][pos[1]]

            # 数据直接交换，ui再动画交换
            self.block_map.swap(pos, self.current_chosen)

            cur_block.target_vector = Vector(
                pos[1] - self.current_chosen[1],
                pos[0] - self.current_chosen[0],
            )
            tar_block.target_vector = Vector(
                self.current_chosen[1] - pos[1],
                self.current_chosen[0] - pos[0],
            )

            cur_block.remaining_time = SWAP_TIME
            tar_block.remaining_time = SWAP_TIME

            cur_block.speed = Vector(
                BLOCK_SIZE * cur_block.target_vector.x / SWAP_TIME,
                BLOCK_SIZE * cur_block.target_vector.y / SWAP_TIME,
            )
            tar_block.speed = Vector(
                BLOCK_SIZE * tar_block.target_vector.x / SWAP_TIME,
                BLOCK_SIZE * tar_block.target_vector.y / SWAP_TIME,
            )

        else:
            self.current_chosen = pos

    def _move_blocks(self, delta_time: float) -> None:
        """移动方格动画"""
        moving_num = 0  # 正在运动的格子数量
        for line in self.block_map.blocks:
            for block in line:
                if block.remaining_time > 0:
                    moving_num += 1
                    block.remaining_time -= delta_time
                else:
                    block.target_vector = Vector(0 ,0)
        self.is_animating = moving_num

    def loop(self):
        clock = pygame.time.Clock()
        while True:
            delta_time = clock.tick(60) / 1000.0  # 单位s
            if self.is_animating > 0:
                self._move_blocks(delta_time)
                self.current_chosen = None
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == pygame.BUTTON_LEFT:
                            self._handle_click(*event.pos)

            self.screen.fill(BACKGROUND_COLOR)

            self._draw_map()
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    happy_match = HappyMatch()
    happy_match.block_map.merge()
    happy_match.loop()
