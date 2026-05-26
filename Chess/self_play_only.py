import time
import random
import os
from board import Board
from figures import Color
from rl_agent_simple import RLAgent
from encoder import encode_board
from utils import move_to_index

def save_checkpoint(ep, agent):
    agent.save_model()
    with open("checkpoint_selfplay.txt", "w") as f:
        f.write(str(ep))
    print(f"Чекпоинт сохранён на эпизоде {ep}")

def load_checkpoint(agent):
    if os.path.exists("checkpoint_selfplay.txt"):
        with open("checkpoint_selfplay.txt", "r") as f:
            ep = int(f.read().strip())
        agent.load_model()
        print(f"Загружен чекпоинт с эпизода {ep}, epsilon={agent.epsilon}")
        return ep
    return 0

def self_play(agent, num_games=5000, report_every=100):
    print(f"\nСАМОИГРА: RL (белые) vs RL (чёрные)")
    print(f"Всего партий: {num_games}, отчёт каждые {report_every}\n")

    start_ep = load_checkpoint(agent)
    agent.epsilon = 0.9
    agent.epsilon_min = 0.02
    agent.epsilon_decay = 0.999

    white_wins = 0
    black_wins = 0
    draws = 0
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
            state = encode_board(board).flatten()
            action_idx, move = agent.act(board, current)
            if move is None:
                break
            captured = board.get(move[1])
            board.move(move[0], move[1])
            step += 1
            reward = -0.01  # небольшая награда за ход (или используйте compute_reward)
            next_state = encode_board(board).flatten()
            winner = _check_winner(board)
            if winner:
                final_reward = 150 if (winner == 'white' and current == Color.WHITE) or (winner == 'black' and current == Color.BLACK) else -100
                agent.remember_and_train(state, action_idx, final_reward, next_state, True)
                if winner == 'white':
                    white_wins += 1
                else:
                    black_wins += 1
                break
            if last_state is not None:
                agent.remember_and_train(last_state, last_action, last_reward, state, False)
            last_state = state
            last_action = action_idx
            last_reward = reward

        if winner is None:
            draws += 1
            if last_state is not None:
                agent.remember_and_train(last_state, last_action, -10, encode_board(board).flatten(), True)

        # Вывод каждой игры
        if winner == 'white':
            print(f"Игра {game_idx:4d}: ПОБЕДА БЕЛЫХ (RL) | Ходов: {step:3d} | ε={agent.epsilon:.4f}")
        elif winner == 'black':
            print(f"Игра {game_idx:4d}: ПОБЕДА ЧЁРНЫХ (RL) | Ходов: {step:3d} | ε={agent.epsilon:.4f}")
        else:
            print(f"Игра {game_idx:4d}: НИЧЬЯ | Ходов: {step:3d} | ε={agent.epsilon:.4f}")

        # Обновляем epsilon после каждой игры
        agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)

        if game_idx % report_every == 0:
            win_rate_white = white_wins / report_every * 100
            results.append((game_idx, win_rate_white, agent.epsilon))
            print(f"\n📊 ОТЧЁТ ЗА {report_every} ИГР [{game_idx-report_every+1}-{game_idx}]: Побед белых = {white_wins}/{report_every} ({win_rate_white:.1f}%), ε={agent.epsilon:.4f}\n")
            white_wins = 0
            black_wins = 0
            draws = 0
            save_checkpoint(game_idx, agent)

    save_checkpoint(num_games, agent)
    print("\nСамоигра завершена. Результаты по блокам:")
    for ep, wr, eps in results:
        print(f"  {ep-report_every+1:4d}-{ep:4d}: {wr:5.1f}%, ε={eps:.4f}")

def _check_winner(board):
    if board.checkmate(Color.BLACK):
        return 'white'
    if board.checkmate(Color.WHITE):
        return 'black'
    return None