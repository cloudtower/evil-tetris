"""
====T Block====

     #
    ###

    0 1 0
    1 1 1

    1 0
    1 1
    1 0

    1 1 1
    0 1 0

    0 1
    1 1
    0 1

====I Block====

    ####

    1 1 1 1

    1
    1
    1
    1

====O Block====

    ##
    ##

    1 1
    1 1

====S Block=====

     ##
    ##

    0 1 1
    1 1 0

    1 0
    1 1
    0 1

====L Block=====

    #
    #
    ##

    1 0
    1 0
    1 1
"""

import math
import random
import os

BEST_SCORE_FILE_NAME = "best_score"
MIN_AVG_BLOCK_APPERANCE = 0.1

block_shapes = [
    # T Block
    [[0, 1, 0],
     [1, 1, 1]],
    # L Block
    [[1, 0],
     [1, 0],
     [1, 1]],
    # S Block
    [[0, 1, 1],
     [1, 1, 0]],
    # O Block
    [[1, 1],
     [1, 1]],
    # I Block
    [[1], [1], [1], [1]]
]


class Board:
    """Board representation"""

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.board = self._get_new_board()

        self.current_block_pos = None
        self.current_block = None
        self.next_block = None
        self.past_blocks = [0, 0, 0, 0, 0]
        self.blocks_total = 0

        self.game_over = False
        self.score = None
        self.lines = None
        self.best_score = None
        self.level = None
        self.niceness = ""
        self.gap = False
        self.gap_was_closed = False

    def start(self):
        """Start game"""

        self.board = self._get_new_board()

        self.current_block_pos = None
        self.current_block = None
        self.next_block = None

        self.game_over = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.best_score = self._read_best_score()

        self._place_new_block()

    def is_game_over(self):
        """Is game over"""

        return self.game_over

    def rotate_block(self):
        rotated_shape = list(map(list, zip(*self.current_block.shape[::-1])))

        if self._can_move(self.current_block_pos, rotated_shape):
            self.current_block.shape = rotated_shape

    def move_block(self, direction):
        """Try to move block"""

        pos = self.current_block_pos
        if direction == "left":
            new_pos = [pos[0], pos[1] - 1]
        elif direction == "right":
            new_pos = [pos[0], pos[1] + 1]
        elif direction == "down":
            new_pos = [pos[0] + 1, pos[1]]
        else:
            raise ValueError("wrong directions")

        if self._can_move(new_pos, self.current_block.shape):
            self.current_block_pos = new_pos
        elif direction == "down":
            self._land_block()
            self._burn()
            self._place_new_block()

    def drop(self):
        """Move to very very bottom"""

        i = 1
        while self._can_move((self.current_block_pos[0] + 1, self.current_block_pos[1]), self.current_block.shape):
            i += 1
            self.move_block("down")

        self._land_block()
        self._burn()
        self._place_new_block()

    def _get_new_board(self):
        """Create new empty board"""

        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _place_new_block(self):
        """Place new block and generate the next one"""

        if self.blocks_total < 5:
            next_block = self._get_random_block(ign_stats=False)
        else:
            next_block = self._get_new_block()

        self.current_block = next_block
        self.next_block = self._get_random_block()

        size = Block.get_size(self.current_block.shape)
        col_pos = math.floor((self.width - size[1]) / 2)
        self.current_block_pos = [0, col_pos]

        if self._check_overlapping(self.current_block_pos, self.current_block.shape):
            self.game_over = True
            self._save_best_score()
        else:
            self.score += 5

    def _land_block(self):
        """Put block to the board and generate a new one"""

        size = Block.get_size(self.current_block.shape)
        for row in range(size[0]):
            for col in range(size[1]):
                if self.current_block.shape[row][col] == 1:
                    self.board[self.current_block_pos[0] + row][self.current_block_pos[1] + col] = 1

    def _burn(self):
        """Remove matched lines"""

        for row in range(self.height):
            if all(col != 0 for col in self.board[row]):
                for r in range(row, 0, -1):
                    self.board[r] = self.board[r - 1]
                self.board[0] = [0 for _ in range(self.width)]
                self.score += 100
                self.lines += 1
                if self.lines % 10 == 0:
                    self.level += 1

    def _check_overlapping(self, pos, shape):
        """If current block overlaps any other on the board"""

        size = Block.get_size(shape)
        for row in range(size[0]):
            for col in range(size[1]):
                if shape[row][col] == 1:
                    if self.board[pos[0] + row][pos[1] + col] == 1:
                        return True
        return False

    def _can_move(self, pos, shape):
        """Check if move is possible"""

        size = Block.get_size(shape)
        if pos[1] < 0 or pos[1] + size[1] > self.width \
                or pos[0] + size[0] > self.height:
            return False

        return not self._check_overlapping(pos, shape)

    def _save_best_score(self):
        """Save best score to file"""

        if self.best_score < self.score:
            with open(BEST_SCORE_FILE_NAME, "w") as file:
                file.write(str(self.score))

    def _check_fits(self):
        """Check if an s-piece can be placed without holes"""

        highest_blocks = [self.height] * len(self.board[0])
        check = list(range(len(self.board[0])))
        for row in range(self.height):
            if not check:
                break
            to_remove = []
            for col in check:
                if self.board[row][col]:
                    highest_blocks[col] = row
                    to_remove.append(col)
            for col in to_remove:
                check.remove(col)

        impossible = {
            (1, True),
            (1, False),
            (2, True),
            (2, False),
            (3, True),
        }

        possible = set()

        for col, row in enumerate(highest_blocks[:-1]): # s rotate
            if highest_blocks[col + 1] == row + 1:
                possible.add((2, False))
        
        for col, row in list(enumerate(highest_blocks))[2:]: # s
            if highest_blocks[col - 1] == row + 1 and highest_blocks[col - 2] == row + 1:
                possible.add((2, False))

        for col, row in list(enumerate(highest_blocks))[1:]: # s inv rotate
            if highest_blocks[col - 1] == row + 1:
                possible.add((2, True))
        
        for col, row in enumerate(highest_blocks[:-2]): # s inv
            if highest_blocks[col + 1] == row + 1 and highest_blocks[col + 2] == row + 1:
                possible.add((2, True))

        for col, row in enumerate(highest_blocks[:-1]): # l, l inv, o
            if highest_blocks[col + 1] == row:
                possible.add((1, True))
                possible.add((1, False))
                possible.add((3, True))

        for col, row in enumerate(highest_blocks[:-2]): # l rotate 3, l inv rotate 1
            if highest_blocks[col + 1] == row and highest_blocks[col + 2] == row:
                possible.add((1, True))
                possible.add((1, False))

        for col, row in list(enumerate(highest_blocks))[2:]: # l rotate 1
            if highest_blocks[col - 1] == row and highest_blocks[col - 2] == row - 1:
                possible.add((1, False))

        for col, row in enumerate(highest_blocks[:-2]): # l inv rotate 3
            if highest_blocks[col + 1] == row and highest_blocks[col + 2] == row - 1:
                possible.add((1, True))

        for col, row in enumerate(highest_blocks[:-1]): # l rotate 2
            if highest_blocks[col + 1] == row - 2:
                possible.add((1, False))

        for col, row in list(enumerate(highest_blocks))[1:]: # l inv rotate 2
            if highest_blocks[col - 1] == row - 2:
                possible.add((1, True))
        
        impossible -= possible
        possible = set()

        was_gap = self.gap
        self.gap = False

        for col, row in enumerate(highest_blocks): # l inv rotate 3
            if col == 0:
                if highest_blocks[col + 1] < row - 2:
                    self.gap = True
            elif col == len(highest_blocks) - 1:
                if highest_blocks[col - 1] < row - 2:
                    self.gap = True
            elif highest_blocks[col + 1] > row + 2 and highest_blocks[col + 2] < highest_blocks[col + 1] - 2:
                self.gap = True

        if self.gap:
            possible.add((4, True))
            possible.add((4, False))
        elif was_gap:
            self.gap_was_closed = True

        for col, row in enumerate(highest_blocks[:-1]): # l rotate 2
            if highest_blocks[col + 1] == row - 2 and (col == len(highest_blocks) - 2 or highest_blocks[col + 2] <= row):
                possible.add((1, False))

        for col, row in list(enumerate(highest_blocks))[1:]: # l inv rotate 2
            if highest_blocks[col - 1] == row - 2 and (col == 1 or highest_blocks[col - 2] <= row):
                possible.add((1, True))
        
        return list(impossible), list(possible)

    @staticmethod
    def _read_best_score():
        """Read best score from file"""

        if os.path.exists(f"./{BEST_SCORE_FILE_NAME}"):
            with open(BEST_SCORE_FILE_NAME) as file:
                return int(file.read())
        return 0

    def _get_new_block(self):
        """Get random block"""

        impossible, possible = self._check_fits()

        if self.gap_was_closed:
            self.gap_was_closed = False
            choice = 4
            flip = False
            self.niceness = ">:D"
        else:
            for i in self.past_blocks:
                if self.blocks_total and i / self.blocks_total:
                    choice = i
                    self.niceness = "!!!"
            else:
                if not impossible:
                    choice, flip = (random.randint(0, len(block_shapes) - 1), bool(random.getrandbits(1)))
                    while (choice, flip) in possible:
                        choice, flip = (random.randint(0, len(block_shapes) - 1), bool(random.getrandbits(1)))
                    self.niceness = "---"
                else:
                    choice, flip = random.choice(impossible)
                    self.niceness = ">:)"

        self.blocks_total += 1
        block = Block(choice)
        self.past_blocks[choice] += 1

        if flip:
            block.flip()

        return block

    def _get_random_block(self, ign_stats=True):
        choice, flip = (random.randint(0, len(block_shapes) - 1), bool(random.getrandbits(1)))

        block = Block(choice)

        if not ign_stats:
            self.blocks_total += 1
            self.past_blocks[choice] += 1

        if flip:
            block.flip()

        return block


class Block:
    """Block representation"""

    def __init__(self, block_type):
        self.shape = block_shapes[block_type]
        self.color = block_type + 1

    def flip(self):
        self.shape = list(map(list, self.shape[::-1]))

    def _get_rotated(self):
        return list(map(list, zip(*self.shape[::-1])))

    def size(self):
        """Get size of the block"""

        return self.get_size(self.shape)

    @staticmethod
    def get_size(shape):
        """Get size of a shape"""

        return [len(shape), len(shape[0])]
