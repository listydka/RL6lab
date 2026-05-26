from figures import *
import copy

class Board:
    def __init__(self):
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.turn = Color.WHITE
        self._init_pieces()

    def _init_pieces(self):
        # Белые: король e4, слоны d4 (чёрное поле) и f3 (белое поле)
        self.squares[4][4] = King("e4", Color.WHITE)
        self.squares[4][3] = Bishop("d4", Color.WHITE)  # чёрное поле
        self.squares[5][5] = Bishop("f3", Color.WHITE)  # белое поле

        # Чёрные: король a8, конь b8, пешка a7
        self.squares[0][0] = King("a8", Color.BLACK)
        self.squares[0][1] = Knight("b8", Color.BLACK)
        self.squares[1][0] = Pawn("a7", Color.BLACK)

    def get(self, pos):
        r, c = pos_to_coord(pos)
        return self.squares[r][c] if 0 <= r < 8 and 0 <= c < 8 else None

    def all_pieces(self, color):
        return [p for row in self.squares for p in row if p and p.color == color]

    def attacked(self, color):
        attacked = set()
        for r in range(8):
            for c in range(8):
                piece = self.squares[r][c]
                if piece and piece.color == color:
                    if isinstance(piece, King):
                        for dr in (-1,0,1):
                            for dc in (-1,0,1):
                                if dr==0 and dc==0: continue
                                rr, cc = r+dr, c+dc
                                if 0<=rr<8 and 0<=cc<8:
                                    attacked.add(coord_to_pos(rr, cc))
                    elif isinstance(piece, Knight):
                        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                            rr, cc = r+dr, c+dc
                            if 0<=rr<8 and 0<=cc<8:
                                attacked.add(coord_to_pos(rr, cc))
                    elif isinstance(piece, Pawn):
                        direction = -1 if piece.color == Color.WHITE else 1
                        for dc in (-1,1):
                            rr, cc = r+direction, c+dc
                            if 0<=rr<8 and 0<=cc<8:
                                attacked.add(coord_to_pos(rr, cc))
                    else:
                        # Слон, ладья, ферзь
                        directions = []
                        if isinstance(piece, Bishop) or isinstance(piece, Queen):
                            directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
                        if isinstance(piece, Rook) or isinstance(piece, Queen):
                            directions += [(-1,0),(1,0),(0,-1),(0,1)]
                        for dr, dc in directions:
                            rr, cc = r+dr, c+dc
                            while 0<=rr<8 and 0<=cc<8:
                                attacked.add(coord_to_pos(rr, cc))
                                if self.squares[rr][cc] is not None:
                                    break
                                rr += dr
                                cc += dc
        return attacked

    def _raw_moves(self, piece):
        moves = []
        r, c = pos_to_coord(piece.pos)
        if isinstance(piece, King):
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    rr, cc = r+dr, c+dc
                    if 0<=rr<8 and 0<=cc<8:
                        t = coord_to_pos(rr, cc)
                        tp = self.get(t)
                        if not tp or tp.color != piece.color:
                            moves.append(t)
            return moves
        if isinstance(piece, Knight):
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                rr, cc = r+dr, c+dc
                if 0<=rr<8 and 0<=cc<8:
                    t = coord_to_pos(rr, cc)
                    tp = self.get(t)
                    if not tp or tp.color != piece.color:
                        moves.append(t)
            return moves
        if isinstance(piece, Pawn):
            direction = -1 if piece.color == Color.WHITE else 1
            # ход вперёд на 1
            rr, cc = r+direction, c
            if 0<=rr<8 and 0<=cc<8 and self.squares[rr][cc] is None:
                moves.append(coord_to_pos(rr, cc))
                # ход на 2 с начальной позиции
                if (piece.color == Color.WHITE and r == 6) or (piece.color == Color.BLACK and r == 1):
                    rr2, cc2 = r+2*direction, c
                    if 0<=rr2<8 and self.squares[rr2][cc2] is None:
                        moves.append(coord_to_pos(rr2, cc2))
            # взятие по диагонали
            for dc in (-1,1):
                rr, cc = r+direction, c+dc
                if 0<=rr<8 and 0<=cc<8:
                    tp = self.squares[rr][cc]
                    if tp and tp.color != piece.color:
                        moves.append(coord_to_pos(rr, cc))
            return moves
        # Слон, ладья, ферзь
        directions = []
        if isinstance(piece, Bishop) or isinstance(piece, Queen):
            directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
        if isinstance(piece, Rook) or isinstance(piece, Queen):
            directions += [(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in directions:
            rr, cc = r+dr, c+dc
            while 0<=rr<8 and 0<=cc<8:
                t = coord_to_pos(rr, cc)
                tp = self.squares[rr][cc]
                if tp is None:
                    moves.append(t)
                else:
                    if tp.color != piece.color and not isinstance(tp, King):
                        moves.append(t)
                    break
                rr += dr
                cc += dc
        return moves

    def valid_moves(self, pos):
        piece = self.get(pos)
        if not piece:
            return []
        legal = []
        for to in self._raw_moves(piece):
            board_copy = self.copy()
            if board_copy._force_move(piece.pos, to) and not board_copy.in_check(piece.color):
                legal.append(to)
        return legal

    def _force_move(self, frm, to):
        fr, fc = pos_to_coord(frm)
        tr, tc = pos_to_coord(to)
        piece = self.squares[fr][fc]
        if not piece:
            return False
        if self.squares[tr][tc] and isinstance(self.squares[tr][tc], King):
            return False
        self.squares[tr][tc] = piece
        self.squares[fr][fc] = None
        piece.pos = to
        return True

    def move(self, frm, to):
        if to not in self.valid_moves(frm):
            return False
        fr, fc = pos_to_coord(frm)
        tr, tc = pos_to_coord(to)
        piece = self.get(frm)
        # взятие на проходе
        if isinstance(piece, Pawn) and abs(ord(to[0])-ord(frm[0])) == 1 and not self.get(to):
            capture_row = fr
            capture_col = tc
            self.squares[capture_row][capture_col] = None
        # превращение
        if isinstance(piece, Pawn) and piece.can_promote(to):
            self.squares[tr][tc] = Queen(to, piece.color)
            self.squares[fr][fc] = None
            self.turn = opposite_color(self.turn)
            return True
        self.squares[tr][tc] = piece
        self.squares[fr][fc] = None
        piece.pos = to
        self.turn = opposite_color(self.turn)
        return True

    def in_check(self, color):
        king_pos = self.king_pos(color)
        if not king_pos:
            return False
        return king_pos in self.attacked(opposite_color(color))

    def checkmate(self, color):
        if not self.in_check(color):
            return False
        for p in self.all_pieces(color):
            if self.valid_moves(p.pos):
                return False
        return True

    def stalemate(self, color):
        if self.in_check(color):
            return False
        for p in self.all_pieces(color):
            if self.valid_moves(p.pos):
                return False
        return True

    def king_pos(self, color):
        for r in range(8):
            for c in range(8):
                p = self.squares[r][c]
                if p and isinstance(p, King) and p.color == color:
                    return coord_to_pos(r, c)
        return None

    def copy(self):
        new_board = Board.__new__(Board)
        new_board.squares = [[None for _ in range(8)] for _ in range(8)]
        new_board.turn = self.turn
        for r in range(8):
            for c in range(8):
                p = self.squares[r][c]
                if p:
                    cls = p.__class__
                    new_piece = cls(p.pos, p.color)
                    if isinstance(new_piece, Pawn):
                        new_piece.jump = p.jump
                    new_board.squares[r][c] = new_piece
        return new_board

def pos_to_coord(pos):
    return 8 - int(pos[1]), ord(pos[0]) - ord('a')

def coord_to_pos(r, c):
    return chr(ord('a') + c) + str(8 - r)

def opposite_color(color):
    return Color.BLACK if color == Color.WHITE else Color.WHITE