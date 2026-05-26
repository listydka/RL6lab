import random
from board import Board
from figures import Color

class RandomBot:
    def __init__(self, color=Color.BLACK):
        self.color = color

    def get_move(self, board):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = board.squares[r][c]
                if piece and piece.color == self.color:
                    for to in board.valid_moves(piece.pos):
                        moves.append((piece.pos, to))
        if not moves:
            return None
        return random.choice(moves)