import sys
from board import Board, opposite_color
from selfplay_rl import SelfPlayRL
from random_bot import RandomBot
from figures import Color, King, Bishop, Knight, Pawn

# ---------- Параметры ----------
WIN_REWARD = 500          # мат
LOSS_REWARD = -200        # мат белым
STALEMATE_REWARD = 10     # пат (ничья)
MAX_MOVES_REWARD = 0      # лимит ходов (ничья)
MAX_MOVES = 200
EPISODES = 5000
SAVE_EVERY = 500
START_EPS = 0.9
MIN_EPS = 0.05
EPS_DECAY = (MIN_EPS / START_EPS) ** (1 / EPISODES)  # ≈ 0.9994

# ---------- Функция игры с детальной классификацией ----------
def play_game(agent, random_bot):
    board = Board()
    turn = Color.WHITE
    moves = 0
    while moves < MAX_MOVES:
        if turn == Color.WHITE:
            action = agent.choose_action(board, turn, training=True)
            if action is None:
                if board.in_check(turn):
                    agent.update_q(LOSS_REWARD, None, None, True)
                    return 'loss'
                else:
                    agent.update_q(STALEMATE_REWARD, None, None, True)
                    return 'stalemate'
            if not board.move(action[0], action[1]):
                agent.update_q(LOSS_REWARD, None, None, True)
                return 'loss'
        else:
            move = random_bot.get_move(board)
            if move is None:
                if board.in_check(Color.BLACK):
                    agent.update_q(WIN_REWARD, None, None, True)
                    return 'win'
                else:
                    agent.update_q(STALEMATE_REWARD, None, None, True)
                    return 'stalemate'
            board.move(move[0], move[1])

        if board.checkmate(Color.BLACK):
            agent.update_q(WIN_REWARD, None, None, True)
            return 'win'
        if board.checkmate(Color.WHITE):
            agent.update_q(LOSS_REWARD, None, None, True)
            return 'loss'
        if board.stalemate(Color.WHITE) or board.stalemate(Color.BLACK):
            agent.update_q(STALEMATE_REWARD, None, None, True)
            return 'stalemate'

        moves += 1
        turn = opposite_color(turn)

    agent.update_q(MAX_MOVES_REWARD, None, None, True)
    return 'max_moves'

# ---------- Обучение одной конфигурации ----------
def train_config(name, init_func, save_file):
    original_init = Board._init_pieces
    Board._init_pieces = init_func

    try:
        agent = SelfPlayRL(alpha=0.3, gamma=0.97, epsilon=START_EPS,
                           epsilon_decay=EPS_DECAY, min_epsilon=MIN_EPS)
        agent.load(save_file)
        random_bot = RandomBot(Color.BLACK)

        print(f"\n{'='*70}")
        print(f"Тренировка: {name}")
        print(f"Файл сохранения: {save_file}")
        print(f"{'='*70}")
        print(f"{'Ep':>5} {'Wins':>7} {'Losses':>7} {'Stalemate':>9} {'MaxMoves':>9} {'Epsilon':>9}")
        print("-" * 55)

        wins = losses = stalemates = max_moves_draws = 0
        for ep in range(1, EPISODES + 1):
            res = play_game(agent, random_bot)
            if res == 'win':
                wins += 1
            elif res == 'loss':
                losses += 1
            elif res == 'stalemate':
                stalemates += 1
            else:  # max_moves
                max_moves_draws += 1

            agent.decay_epsilon()

            if ep % SAVE_EVERY == 0:
                total = wins + losses + stalemates + max_moves_draws
                if total > 0:
                    print(f"{ep:5}  {wins:4} ({wins/total*100:5.1f}%)   "
                          f"{losses:4} ({losses/total*100:5.1f}%)   "
                          f"{stalemates:5} ({stalemates/total*100:5.1f}%)   "
                          f"{max_moves_draws:5} ({max_moves_draws/total*100:5.1f}%)   "
                          f"{agent.epsilon:.4f}")
                agent.save(save_file)
                wins = losses = stalemates = max_moves_draws = 0

        agent.save(save_file.replace('.pkl', '_final.pkl'))
        print(f"\nОбучение '{name}' завершено.\n")
    finally:
        Board._init_pieces = original_init

# ---------- Расстановка 1: 6 фигур (конь + пешка у чёрных) ----------
def init_6pieces(self):
    self.squares[4][4] = King("e4", Color.WHITE)
    self.squares[4][3] = Bishop("d4", Color.WHITE)
    self.squares[5][5] = Bishop("f3", Color.WHITE)
    self.squares[0][0] = King("a8", Color.BLACK)
    self.squares[0][1] = Knight("b8", Color.BLACK)
    self.squares[1][0] = Pawn("a7", Color.BLACK)

# ---------- Расстановка 2: только чёрный король ----------
def init_1king(self):
    self.squares[4][4] = King("e4", Color.WHITE)
    self.squares[4][3] = Bishop("d4", Color.WHITE)
    self.squares[5][5] = Bishop("f3", Color.WHITE)
    self.squares[0][0] = King("a8", Color.BLACK)

# ---------- Запуск ----------
if __name__ == "__main__":
    train_config("6 фигур (король+2 слона vs король+конь+пешка)",
                 init_6pieces, "rl_6pieces.pkl")
    train_config("Только король (белые два слона против одинокого короля)",
                 init_1king, "rl_1king.pkl")
    print("Все обучения завершены!")