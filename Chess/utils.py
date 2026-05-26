from board import pos_to_coord

def square_to_index(pos: str) -> int:
    row, col = pos_to_coord(pos)
    return row * 8 + col

def move_to_index(frm: str, to: str) -> int:
    return square_to_index(frm) * 64 + square_to_index(to)

def index_to_move(index: int) -> tuple[str, str]:
    from_idx = index // 64
    to_idx = index % 64
    from_row = from_idx // 8
    from_col = from_idx % 8
    to_row = to_idx // 8
    to_col = to_idx % 8
    frm = chr(ord('a') + from_col) + str(8 - from_row)
    to = chr(ord('a') + to_col) + str(8 - to_row)
    return frm, to