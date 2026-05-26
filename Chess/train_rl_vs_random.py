from board import Board, opposite_color
from selfplay_rl import SelfPlayRL
from random_bot import RandomBot
from figures import Color

WIN_REWARD = 500
LOSS_REWARD = -200
STALEMATE_REWARD = 200      # пат даёт положительную награду
CAPTURE_REWARD = 0           # не используем, чтобы не усложнять
CHECK_REWARD = 0
MOVE_PENALTY = -0.01

def play_game(agent, random_bot, max_moves=200):
    board = Board()
    turn = Color.WHITE
    moves = 0
    while moves < max_moves:
        if turn == Color.WHITE:
            action = agent.choose_action(board, turn, training=True)
            if action is None:
                if board.in_check(turn):
                    agent.update_q(LOSS_REWARD, None, None, True)
                    return 'loss'
                else:
                    agent.update_q(STALEMATE_REWARD, None, None, True)
                    return 'win'   # пат считается победой
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
                    return 'win'   # пат – победа для белых
            board.move(move[0], move[1])

        # Проверка окончания
        if board.checkmate(Color.BLACK):
            agent.update_q(WIN_REWARD, None, None, True)
            return 'win'
        if board.checkmate(Color.WHITE):
            agent.update_q(LOSS_REWARD, None, None, True)
            return 'loss'
        if board.stalemate(Color.WHITE) or board.stalemate(Color.BLACK):
            agent.update_q(STALEMATE_REWARD, None, None, True)
            return 'win'

        moves += 1
        turn = opposite_color(turn)

    # Лимит ходов – считаем победой (чтобы агент стремился к завершению)
    agent.update_q(STALEMATE_REWARD, None, None, True)
    return 'win'

def train(episodes=3000, save_every=200):
    agent = SelfPlayRL(alpha=0.3, gamma=0.97, epsilon=0.9, epsilon_decay=0.998, min_epsilon=0.05)
    agent.load("rl_vs_random_fixed.pkl")
    random_bot = RandomBot(color=Color.BLACK)
    wins = draws = losses = 0
    for ep in range(1, episodes+1):
        res = play_game(agent, random_bot)
        if res == 'win':
            wins += 1
        elif res == 'loss':
            losses += 1
        else:
            draws += 1
        agent.decay_epsilon()
        if ep % save_every == 0:
            total = wins + draws + losses
            print(f"Ep {ep}: W={wins} ({wins/total*100:.1f}%), D={draws} ({draws/total*100:.1f}%), L={losses} ({losses/total*100:.1f}%), eps={agent.epsilon:.3f}")
            agent.save("rl_vs_random_fixed.pkl")
            wins = draws = losses = 0
    agent.save("rl_vs_random_fixed_final.pkl")
    print("Training finished")

if __name__ == "__main__":
    train()