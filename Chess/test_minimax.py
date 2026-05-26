from board import Board
from ChessGameMain import Bot as MinimaxBot

board = Board()
print("Начальная доска:")
for row in board.squares:
    print([p.symbol if p else '..' for p in row])

minimax = MinimaxBot(depth=4)

print("\nХод белых (должен быть легальный ход):")
move = minimax.best_move(board)
print(f"Минимакс вернул: {move}")

if move:
    print(f"Ход: {move[0]} -> {move[1]}")
    # Проверяем, легальный ли ход для белых
    piece = board.get(move[0])
    if piece and piece.color == Color.WHITE:
        print(f"Фигура: {piece.symbol}, цвет: белые - OK")
        if move[1] in board.valid_moves(move[0]):
            print("Ход легальный")
        else:
            print("Ход НЕЛЕГАЛЬНЫЙ!")
    else:
        print(f"На клетке {move[0]} нет белой фигуры! Проблема!")
else:
    print("Минимакс вернул None - не может ходить!")