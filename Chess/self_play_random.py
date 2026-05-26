import time
import random
import os
from board import Board
from figures import Color
from rl_agent import RLAgent
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

def save_checkpoint(ep, agent):
    agent.save_model()
    with open("checkpoint_random.txt", "w") as f:
        f.write(str(ep))
    print(f"Чекпоинт сохранён на эпизоде {ep}")

def load_checkpoint(agent):
    if os.path.exists("checkpoint_random.txt"):
        with open("checkpoint_random.txt", "r") as f:
            ep = int(f.read().strip())
        agent.load_model()
        print(f"Загружен чекпоинт с эпизода {ep}, epsilon={agent.epsilon}")
        return ep
    return 0

def self_play_vs_random(agent, num_games=5000, report_every=100):
    random_bot = RandomBot()
    print(f"\nОбучение RL (чёрные) против случайного бота (белые)")
    print(f"Всего партий: {num_games}, отчёт каждые {report_every}\n")

    start_ep = load_checkpoint(agent)
    agent.epsilon = 0.9
    agent.epsilon_min = 0.02
    agent.epsilon_decay = 0.998

    wins_in_block = 0
    results = []

    for game_idx in range(start_ep + 1, num_games + 1):
        board = Board()
        step = 0
        winner = None
        last_state = None
        last_action = None
        last_reward = 0.0

        while step < 200:
            current = board.turn
            if current == Color.WHITE:
                move = random_bot.best_move(board, Color.WHITE)
                if not move:
                    winner = 'black'
                    if last_state is not None:
                        final_reward = agent.compute_reward(board, None, winner, repeat=False)
                        agent.remember_and_train(last_state, last_action, final_reward, encode_board(board), True)
                        wins_in_block += 1
                        print(f"Игра {game_idx}: случайный бот не может ходить, победа RL", flush=True)
                    break
                board.move(move[0], move[1])
                step += 1
                winner = _check_winner(board)
                if winner:
                    if last_state is not None:
                        final_reward = agent.compute_reward(board, None, winner, repeat=False)
                        agent.remember_and_train(last_state, last_action, final_reward, encode_board(board), True)
                        if winner == 'black':
                            wins_in_block += 1
                            print(f"Игра {game_idx}: МАТ! Победа RL", flush=True)
                    break
                if last_state is not None:
                    next_state = encode_board(board)
                    agent.remember_and_train(last_state, last_action, last_reward, next_state, False)
                    last_state = None
            else:
                state = encode_board(board)
                action_idx, move = agent.act(board, Color.BLACK)
                if not move:
                    winner = 'white'
                    print(f"Игра {game_idx}: RL не может ходить, проигрыш", flush=True)
                    break
                captured = board.get(move[1])
                board.move(move[0], move[1])
                step += 1
                reward = agent.compute_reward(board, captured, None, repeat=False)
                next_state = encode_board(board)
                winner = _check_winner(board)
                if winner:
                    final_reward = agent.compute_reward(board, captured, winner, repeat=False)
                    agent.remember_and_train(state, action_idx, final_reward, next_state, True)
                    if winner == 'black':
                        wins_in_block += 1
                        print(f"Игра {game_idx}: МАТ! Победа RL", flush=True)
                    break
                last_state = state
                last_action = action_idx
                last_reward = reward

        if not winner and last_state is not None:
            agent.remember_and_train(last_state, last_action, -10, encode_board(board), True)

        agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)

        if game_idx % report_every == 0:
            win_rate = wins_in_block / report_every * 100
            results.append((game_idx, win_rate, agent.epsilon))
            print(f"Игры {game_idx-report_every+1}-{game_idx}: побед RL = {wins_in_block}/{report_every} ({win_rate:.1f}%), ε={agent.epsilon:.4f}")
            wins_in_block = 0
            save_checkpoint(game_idx, agent)

    save_checkpoint(num_games, agent)
    print("\nОбучение завершено. Результаты по блокам:")
    for ep, wr, eps in results:
        print(f"  {ep-report_every+1:4d}-{ep:4d}: {wr:5.1f}%, ε={eps:.4f}")

def _check_winner(board):
    if board.checkmate(Color.BLACK):
        return 'white'
    if board.checkmate(Color.WHITE):
        return 'black'
    return None