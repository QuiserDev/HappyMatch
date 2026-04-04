import arcade
import random
from enum import Enum, auto
from typing import Optional, List

# --- 常量 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
MARGIN = 60
GRID_SIZE = 8
BLOCK_SPACING = (SCREEN_WIDTH - MARGIN * 2) // GRID_SIZE

BLOCK_SCALE = BLOCK_SPACING / 200
SELECT_SCALE = BLOCK_SPACING / 64


class GameState(Enum):
    IDLE = auto()
    ANIMATING = auto()  # 包含交换、掉落等所有动画状态


class BlockType(Enum):
    BEAR = "bear"
    CHICK = "chick"
    DOG = "dog"
    PIG = "pig"
    PARROT = "parrot"
    FROG = "frog"


class Block(arcade.Sprite):
    def __init__(self, block_type: BlockType):
        # 3.0+ 推荐显式路径
        super().__init__(f"assets/{block_type.value}.png", scale=BLOCK_SCALE)
        self.block_type = block_type
        self.target_x = 0
        self.target_y = 0

    def move_to_grid(self, r: int, c:int)->None:
        self.target_x = MARGIN + c * BLOCK_SPACING + BLOCK_SPACING // 2
        self.target_y = MARGIN + r * BLOCK_SPACING + BLOCK_SPACING // 2

    def update_animation(self) -> bool:
        """返回是否仍在移动"""
        arrived = True
        if abs(self.center_x - self.target_x) > 1:
            self.center_x += (self.target_x - self.center_x) * 0.15
            arrived = False
        else:
            self.center_x = self.target_x

        if abs(self.center_y - self.target_y) > 1:
            self.center_y += (self.target_y - self.center_y) * 0.15
            arrived = False
        else:
            self.center_y = self.target_y
        return not arrived


class HappyMatch(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Happy Match Arcade 3.0")
        arcade.set_background_color(arcade.color.AMAZON)

        # 3.0 核心：所有显示对象必须在 SpriteList 里
        self.blocks_list = arcade.SpriteList()
        self.selection_list = arcade.SpriteList()

        # 逻辑矩阵
        self.grid: List[List[Optional[Block]]] = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        self.state = GameState.IDLE
        self.selected_block: Optional[Block] = None
        self.swapping_pair: List[Block] = []
        self.is_reversing = False

        # 初始化选框并放入专门的 SpriteList
        self.selection_sprite = arcade.Sprite(":resources:/gui_basic_assets/checkbox/empty.png", scale=SELECT_SCALE)
        self.selection_list.append(self.selection_sprite)

        self.setup_game()

    def setup_game(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                while True:
                    b_type = random.choice(list(BlockType))
                    if c >= 2 and self.grid[r][c - 1].block_type == b_type and self.grid[r][
                        c - 2].block_type == b_type: continue
                    if r >= 2 and self.grid[r - 1][c].block_type == b_type and self.grid[r - 2][
                        c].block_type == b_type: continue

                    block = Block(b_type)
                    block.move_to_grid(r, c)
                    block.center_x, block.center_y = block.target_x, block.target_y
                    self.grid[r][c] = block
                    self.blocks_list.append(block)
                    break

    def get_grid_pos(self, block: Block):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == block: return r, c
        return -1, -1

    def find_matches(self):
        to_del = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                if self.grid[r][c] and self.grid[r][c + 1] and self.grid[r][c + 2]:
                    if self.grid[r][c].block_type == self.grid[r][c + 1].block_type == self.grid[r][c + 2].block_type:
                        to_del.update([self.grid[r][c], self.grid[r][c + 1], self.grid[r][c + 2]])
        for c in range(GRID_SIZE):
            for r in range(GRID_SIZE - 2):
                if self.grid[r][c] and self.grid[r + 1][c] and self.grid[r + 2][c]:
                    if self.grid[r][c].block_type == self.grid[r + 1][c].block_type == self.grid[r + 2][c].block_type:
                        to_del.update([self.grid[r][c], self.grid[r + 1][c], self.grid[r + 2][c]])
        return list(to_del)

    def on_update(self, delta_time: float):
        # 动画更新
        moving = False
        for b in self.blocks_list:
            if b.update_animation():
                moving = True

        if moving:
            self.state = GameState.ANIMATING
            return

        # 动画停下后的逻辑处理
        if self.state == GameState.ANIMATING:
            # 如果是刚结束交换动画
            if self.swapping_pair:
                b1, b2 = self.swapping_pair
                if self.find_matches():
                    self.swapping_pair = []
                    self.is_reversing = False
                    self.process_elimination()
                elif not self.is_reversing:
                    # 没匹配到，执行回换
                    self.swap_in_grid(b1, b2)
                    self.is_reversing = True
                else:
                    # 回换结束
                    self.swapping_pair = []
                    self.is_reversing = False
                    self.state = GameState.IDLE
            else:
                # 检查连消
                if not self.process_elimination():
                    self.state = GameState.IDLE

    def swap_in_grid(self, b1, b2):
        r1, c1 = self.get_grid_pos(b1)
        r2, c2 = self.get_grid_pos(b2)
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        b1.move_to_grid(r2, c2)
        b2.move_to_grid(r1, c1)

    def process_elimination(self):
        matches = self.find_matches()
        if not matches: return False

        for b in matches:
            r, c = self.get_grid_pos(b)
            self.grid[r][c] = None
            b.remove_from_sprite_lists()

        # 掉落逻辑
        for c in range(GRID_SIZE):
            column = []
            for r in range(GRID_SIZE):
                if self.grid[r][c]: column.append(self.grid[r][c])

            for r in range(GRID_SIZE):
                if r < len(column):
                    self.grid[r][c] = column[r]
                    self.grid[r][c].move_to_grid(r, c)
                else:
                    # 补新
                    new_b = Block(random.choice(list(BlockType)))
                    new_b.center_x = MARGIN + c * BLOCK_SPACING + BLOCK_SPACING // 2
                    new_b.center_y = SCREEN_HEIGHT + 50
                    new_b.move_to_grid(r, c)
                    self.grid[r][c] = new_b
                    self.blocks_list.append(new_b)
        return True

    def on_draw(self):
        self.clear()
        # 3.0 正确姿势：哪怕一个 Sprite 也要用 SpriteList.draw()
        if self.selected_block and self.state == GameState.IDLE:
            self.selection_sprite.center_x = self.selected_block.center_x
            self.selection_sprite.center_y = self.selected_block.center_y
            self.selection_list.draw()

        self.blocks_list.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.state != GameState.IDLE: return

        clicked = arcade.get_sprites_at_point((x, y), self.blocks_list)
        if not clicked: return

        current = clicked[0]
        if not self.selected_block:
            self.selected_block = current
        else:
            r1, c1 = self.get_grid_pos(self.selected_block)
            r2, c2 = self.get_grid_pos(current)
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                self.swapping_pair = [self.selected_block, current]
                self.swap_in_grid(self.swapping_pair[0], self.swapping_pair[1])
                self.state = GameState.ANIMATING
                self.selected_block = None
            else:
                self.selected_block = current


if __name__ == "__main__":
    HappyMatch().run()