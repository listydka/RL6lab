import pickle
import random
from collections import defaultdict
from board import Board, opposite_color
from figures import Color

class SelfPlayRL:
    def __init__(self, alpha=0.5, gamma=0.95, epsilon=0.9, epsilon_decay=0.999, min_epsilon=0.05):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.last_state = None
        self.last_action = None
        self.stats = {'updates': 0, 'exploration': 0, 'exploitation': 0}

    def _state_key(self, board, turn_color):
        """Уникальный ключ состояния: позиции фигур + чей ход"""
        pieces = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p:
                    # тип фигуры: K, Q, R, B, N, P
                    type_map = {
                        'King': 'K', 'Queen': 'Q', 'Rook': 'R',
                        'Bishop': 'B', 'Knight': 'N', 'Pawn': 'P'
                    }
                    t = type_map[p.__class__.__name__]
                    col = 'w' if p.color == Color.WHITE else 'b'
                    pieces.append(f"{col}{t}{r}{c}")
        pieces.sort()
        state = ''.join(pieces) + str(turn_color == Color.WHITE)
        return state

    def _legal_actions(self, board, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p and p.color == color:
                    for to in board.valid_moves(p.pos):
                        moves.append((p.pos, to))
        return moves

    def choose_action(self, board, turn_color, training=True):
        legal = self._legal_actions(board, turn_color)
        if not legal:
            return None
        if training and random.random() < self.epsilon:
            self.stats['exploration'] += 1
            action = random.choice(legal)
        else:
            self.stats['exploitation'] += 1
            state = self._state_key(board, turn_color)
            best_q = -1e9
            best_action = None
            for act in legal:
                act_str = f"{act[0]}->{act[1]}"
                q = self.q_table[state].get(act_str, 0.0)
                if q > best_q:
                    best_q = q
                    best_action = act
            action = best_action if best_action else random.choice(legal)
        self.last_state = self._state_key(board, turn_color)
        self.last_action = f"{action[0]}->{action[1]}"
        return action

    def update_q(self, reward, next_board, next_turn, done=False):
        if self.last_state is None or self.last_action is None:
            return
        if not done and next_board:
            next_state = self._state_key(next_board, next_turn)
            best_next = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        else:
            best_next = 0.0
        old_q = self.q_table[self.last_state][self.last_action]
        new_q = old_q + self.alpha * (reward + self.gamma * best_next - old_q)
        self.q_table[self.last_state][self.last_action] = new_q
        self.stats['updates'] += 1
        self.last_state = None
        self.last_action = None

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def save(self, path):
        with open(path, "wb") as f:
            to_save = {k: dict(v) for k, v in self.q_table.items()}
            pickle.dump(to_save, f)

    def load(self, path):
        try:
            with open(path, "rb") as f:
                loaded = pickle.load(f)
                self.q_table.clear()
                for k, v in loaded.items():
                    self.q_table[k] = defaultdict(float, v)
            return True
        except FileNotFoundError:
            return False