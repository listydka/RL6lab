import pickle
import random
from collections import defaultdict
from board import Board, pos_to_coord, coord_to_pos, opposite_color
from figures import Color

class RLBotTable:
    def __init__(self, color=Color.WHITE, alpha=0.1, gamma=0.99, epsilon=0.2):
        self.color = color           # цвет, за который играет агент (белые)
        self.alpha = alpha           # learning rate
        self.gamma = gamma           # discount factor
        self.epsilon = epsilon       # exploration rate
        self.q_table = defaultdict(lambda: defaultdict(float))  # state -> action -> Q
        self.prev_state = None
        self.prev_action = None

    def _state_key(self, board, turn_color):
        """
        Уникальное представление состояния:
        - позиции всех фигур (8x8) в виде строки
        - чей ход (turn_color)
        """
        pieces = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p:
                    # Кодируем тип фигуры и цвет
                    type_code = {
                        'King': 'K', 'Knight': 'N', 'Pawn': 'P',
                        'Bishop': 'B', 'Rook': 'R', 'Queen': 'Q'
                    }[p.__class__.__name__]
                    color_code = 'w' if p.color == Color.WHITE else 'b'
                    pieces.append(f"{color_code}{type_code}{r}{c}")
        pieces.sort()
        return (''.join(pieces), turn_color)

    def _get_legal_actions(self, board, color):
        """Список всех возможных ходов в виде (from_pos, to_pos)."""
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p and p.color == color:
                    for to in board.valid_moves(p.pos):
                        moves.append((p.pos, to))
        return moves

    def _action_to_str(self, action):
        return f"{action[0]}->{action[1]}"

    def _str_to_action(self, s):
        frm, to = s.split('->')
        return (frm, to)

    def get_move(self, board, turn_color, training=True):
        """Выбрать ход (ε‑жадный)."""
        legal = self._get_legal_actions(board, turn_color)
        if not legal:
            return None

        state = self._state_key(board, turn_color)
        # Если тренируемся и epsilon, то иногда случайный ход
        if training and random.random() < self.epsilon:
            action = random.choice(legal)
        else:
            # Иначе выбираем лучшее по Q
            best_q = -1e9
            best_action = None
            # Если для этого состояния нет записей, Q по умолчанию 0
            for act in legal:
                act_str = self._action_to_str(act)
                q = self.q_table[state].get(act_str, 0.0)
                if q > best_q:
                    best_q = q
                    best_action = act
            action = best_action if best_action is not None else random.choice(legal)

        self.prev_state = state
        self.prev_action = self._action_to_str(action)
        return action

    def update_q(self, reward, next_board, next_turn):
        """Обновить Q(s, a) после выполнения действия (или окончания игры)."""
        if self.prev_state is None or self.prev_action is None:
            return

        # Если игра не окончена, то будущее максимальное Q
        if next_board is not None:
            next_state = self._state_key(next_board, next_turn)
            future_q = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        else:
            future_q = 0.0   # игра окончена

        old_q = self.q_table[self.prev_state][self.prev_action]
        new_q = old_q + self.alpha * (reward + self.gamma * future_q - old_q)
        self.q_table[self.prev_state][self.prev_action] = new_q

        # Сброс для следующего шага
        self.prev_state = None
        self.prev_action = None

    def save(self, filepath="rl_qtable.pkl"):
        with open(filepath, "wb") as f:
            # Преобразуем defaultdict в обычный dict для сохранения
            to_save = {k: dict(v) for k, v in self.q_table.items()}
            pickle.dump(to_save, f)

    def load(self, filepath="rl_qtable.pkl"):
        try:
            with open(filepath, "rb") as f:
                loaded = pickle.load(f)
                self.q_table.clear()
                for state, actions in loaded.items():
                    self.q_table[state] = defaultdict(float, actions)
            return True
        except FileNotFoundError:
            return False