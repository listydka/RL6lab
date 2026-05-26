import time
import random
import os
from board import Board
from figures import Color
from rl_agent_simple import RLAgent
from encoder import encode_board
from utils import move_to_index


class RandomBot:
    def best_move(self, board, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p and p.color == color:
                    for to in board.valid_moves(p.pos):
                        moves.append((p.pos, to))
        return random.choice(moves) if moves else None


def train(agent, num_games=3000, report_every=50):
    random_bot = RandomBot()
    wins = 0
    print("Обучение RL (чёрные) против случайного бота (белые)")
    print(f"Всего партий: {num_games}, отчёт каждые {report_every}\n")

    for game in range(1, num_games + 1):
        board = Board()
        step = 0
        winner = None
        last_state = None
        last_action = None

        while step < 100:
            if board.turn == Color.WHITE:
                move = random_bot.best_move(board, Color.WHITE)
                if not move:
                    winner = 'black'
                    if last_state is not None:
                        agent.remember_and_train(last_state, last_action, 100, encode_board(board).flatten(), True)
                        wins += 1
                    break
                board.move(move[0], move[1])
                step += 1
                if board.checkmate(Color.BLACK):
                    winner = 'white'
                    if last_state is not None:
                        agent.remember_and_train(last_state, last_action, -100, encode_board(board).flatten(), True)
                    break
                if board.checkmate(Color.WHITE):
                    winner = 'black'
                    if last_state is not None:
                        agent.remember_and_train(last_state, last_action, 100, encode_board(board).flatten(), True)
                        wins += 1
                    break
                if last_state is not None:
                    next_state = encode_board(board).flatten()
                    agent.remember_and_train(last_state, last_action, 0, next_state, False)
                    last_state = None
            else:
                state = encode_board(board).flatten()
                action_idx, move = agent.act(board, Color.BLACK)
                if not move:
                    winner = 'white'
                    if last_state is not None:
                        agent.remember_and_train(last_state, last_action, -100, encode_board(board).flatten(), True)
                    break
                board.move(move[0], move[1])
                step += 1
                if board.checkmate(Color.WHITE):
                    winner = 'black'
                    agent.remember_and_train(state, action_idx, 100, encode_board(board).flatten(), True)
                    wins += 1
                    break
                if board.checkmate(Color.BLACK):
                    winner = 'white'
                    agent.remember_and_train(state, action_idx, -100, encode_board(board).flatten(), True)
                    break
                last_state = state
                last_action = action_idx

        if winner is None and last_state is not None:
            agent.remember_and_train(last_state, last_action, -10, encode_board(board).flatten(), True)

        # Вывод каждой игры
        if winner == 'black':
            print(f"Игра {game:4d}: ПОБЕДА RL (чёрные) | Ходов: {step:3d} | ε={agent.epsilon:.4f}")
        elif winner == 'white':
            print(f"Игра {game:4d}: ПОБЕДА БЕЛЫХ (random) | Ходов: {step:3d} | ε={agent.epsilon:.4f}")
        else:
            print(f"Игра {game:4d}: НИЧЬЯ | Ходов: {step:3d} | ε={agent.epsilon:.4f}")

        # Обновляем epsilon после каждой игры
        agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)

        if game % report_every == 0:
            win_rate = wins / report_every * 100
            print(
                f"\n📊 ОТЧЁТ ЗА {report_every} ИГР [{game - report_every + 1}-{game}]: Побед RL = {wins}/{report_every} ({win_rate:.1f}%), ε={agent.epsilon:.4f}\n")
            wins = 0
            agent.save_model()

    agent.save_model()
    print("Обучение завершено")


if __name__ == "__main__":
    agent = RLAgent()
    train(agent, num_games=3000, report_every=50)