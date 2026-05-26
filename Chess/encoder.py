import numpy as np
from board import Board
from figures import Color, Pawn, Knight, Bishop, Rook, Queen, King

def encode_board(board: Board) -> np.ndarray:
    channels = np.zeros((8, 8, 13), dtype=np.float32)
    piece_order = [Pawn, Knight, Bishop, Rook, Queen, King]
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p is None:
                continue
            idx = piece_order.index(type(p))
            if p.color == Color.WHITE:
                channels[r, c, idx] = 1.0
            else:
                channels[r, c, idx + 6] = 1.0
    if board.turn == Color.WHITE:
        channels[:, :, 12] = 1.0
    return channels