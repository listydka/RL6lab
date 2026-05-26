from abc import ABC, abstractmethod
from enum import Enum, auto
import pygame
import items as ci

class Color(Enum):
    WHITE = auto()
    BLACK = auto()

class Piece(ABC):
    def __init__(self, pos, color, symbol, img_key):
        self.pos = pos
        self.color = color
        self.symbol = symbol
        self.is_clicked = False
        self.img = pygame.transform.scale(getattr(ci, img_key), (70, 70))

    @staticmethod
    def in_board(t):
        return len(t) == 2 and t[0] in "abcdefgh" and t[1] in "12345678"

    @abstractmethod
    def can_move(self, t):
        pass

class Rook(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wR" if c==Color.WHITE else "bR",
                         "WHITE_ROOK" if c==Color.WHITE else "BLACK_ROOK")
    def can_move(self, t):
        return self.in_board(t) and (t[0]==self.pos[0] or t[1]==self.pos[1])

class Bishop(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wB" if c==Color.WHITE else "bB",
                         "WHITE_BISHOP" if c==Color.WHITE else "BLACK_BISHOP")
    def can_move(self, t):
        if not self.in_board(t):
            return False
        return abs(ord(t[0])-ord(self.pos[0])) == abs(int(t[1])-int(self.pos[1]))

class Queen(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wQ" if c==Color.WHITE else "bQ",
                         "WHITE_QUEEN" if c==Color.WHITE else "BLACK_QUEEN")
    def can_move(self, t):
        if not self.in_board(t):
            return False
        return (t[0]==self.pos[0] or t[1]==self.pos[1]) or \
               (abs(ord(t[0])-ord(self.pos[0])) == abs(int(t[1])-int(self.pos[1])))

class King(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wK" if c==Color.WHITE else "bK",
                         "WHITE_KING" if c==Color.WHITE else "BLACK_KING")
        self.in_check = False
    def can_move(self, t):
        if not self.in_board(t):
            return False
        dx = abs(ord(t[0])-ord(self.pos[0]))
        dy = abs(int(t[1])-int(self.pos[1]))
        return dx <= 1 and dy <= 1

class Knight(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wN" if c==Color.WHITE else "bN",
                         "WHITE_KNIGHT" if c==Color.WHITE else "BLACK_KNIGHT")
    def can_move(self, t):
        if not self.in_board(t):
            return False
        dx = abs(ord(t[0])-ord(self.pos[0]))
        dy = abs(int(t[1])-int(self.pos[1]))
        return (dx==2 and dy==1) or (dx==1 and dy==2)

class Pawn(Piece):
    def __init__(self, p, c):
        super().__init__(p, c, "wP" if c==Color.WHITE else "bP",
                         "WHITE_PAWN" if c==Color.WHITE else "BLACK_PAWN")
        self.jump = False
    def can_promote(self, t):
        return (self.color==Color.WHITE and t[1]=='8') or (self.color==Color.BLACK and t[1]=='1')
    def can_move(self, t):
        if not self.in_board(t):
            return False
        dx = ord(t[0]) - ord(self.pos[0])
        dy = int(t[1]) - int(self.pos[1])
        if self.color == Color.WHITE:
            if t[0] == self.pos[0]:
                if dy == 1:
                    return True
                if dy == 2 and self.pos[1] == '2':
                    self.jump = True
                    return True
            elif abs(dx) == 1 and dy == 1:
                return True
        else:
            if t[0] == self.pos[0]:
                if dy == -1:
                    return True
                if dy == -2 and self.pos[1] == '7':
                    self.jump = True
                    return True
            elif abs(dx) == 1 and dy == -1:
                return True
        return False