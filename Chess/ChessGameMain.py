import pygame, tkinter as tk, os, time, random
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
from figures import Color, Pawn, Knight, Bishop, Rook, Queen, King
from board import Board, pos_to_coord, coord_to_pos, opposite_color
import items as ci
W, H, CELL = 800, 600, 75
COLORS = {'bg':(0,0,0), 'light':(173,170,166), 'dark':(124,115,115), 'yellow':(255,255,0),
          'white':(255,255,255), 'red':(199,0,0), 'green':(0,255,0), 'brown':(210,180,140)}

class Auth:
    def __init__(self):
        if not os.path.exists("secret.key"):
            key = Fernet.generate_key()
            with open("secret.key","wb") as f: f.write(key)
            self.cipher = Fernet(key)
        else:
            with open("secret.key","rb") as f: self.cipher = Fernet(f.read())
    def register(self, u, p):
        with open("credentials.txt","a") as f: f.write(f"{u}:{self.cipher.encrypt(p.encode()).decode()}\n")
    def login(self, u, p):
        try:
            with open("credentials.txt","r") as f:
                for l in f:
                    uu, pp = l.strip().split(":")
                    if uu==u and self.cipher.decrypt(pp.encode()).decode()==p: return True
        except: pass
        return False

def show_login():
    auth = Auth()
    root = tk.Tk()
    root.title("Шахматы - Вход")
    root.geometry("500x500")
    root.configure(bg='#2c3e50')
    root.resizable(False, False)
    status = [False]
    tk.Label(root, text="ШАХМАТЫ", font=('Arial',24,'bold'), fg='#e74c3c', bg='#2c3e50').pack(pady=20)
    nb = ttk.Notebook(root); nb.pack(expand=1, fill="both", padx=20, pady=10)
    rf = ttk.Frame(nb); nb.add(rf, text="Регистрация")
    tk.Label(rf, text="Имя:").pack(pady=5); ru = tk.Entry(rf); ru.pack(pady=5)
    tk.Label(rf, text="Пароль:").pack(pady=5); rp = tk.Entry(rf, show="*"); rp.pack(pady=5)
    def reg():
        if ru.get() and rp.get():
            auth.register(ru.get(), rp.get())
            messagebox.showinfo("Успех", "Регистрация успешна!")
            ru.delete(0,tk.END); rp.delete(0,tk.END)
        else: messagebox.showwarning("Ошибка", "Заполните поля")
    ttk.Button(rf, text="Зарегистрироваться", command=reg).pack(pady=20)
    lf = ttk.Frame(nb); nb.add(lf, text="Вход")
    tk.Label(lf, text="Имя:").pack(pady=5); lu = tk.Entry(lf); lu.pack(pady=5)
    tk.Label(lf, text="Пароль:").pack(pady=5); lp = tk.Entry(lf, show="*"); lp.pack(pady=5)
    def log():
        if auth.login(lu.get(), lp.get()): status[0]=True; root.destroy()
        else: messagebox.showerror("Ошибка", "Неверные данные")
    ttk.Button(lf, text="Войти", command=log).pack(pady=20)
    tk.Label(root, text="♔ ♕ ♖ ♗ ♘ ♙", font=('Arial',16), fg='#7f8c8d', bg='#2c3e50').pack(pady=10)
    root.mainloop()
    return status[0]

class Clock:
    def __init__(self, m=5):
        self.t = {'white': m*60, 'black': m*60}
        self.c = 'white'
        self.l = time.time()
        self.r = False
    def start(self, p='white'): self.c=p; self.l=time.time(); self.r=True
    def switch(self): self.update(); self.c = 'black' if self.c=='white' else 'white'
    def update(self):
        if self.r:
            e = time.time() - self.l
            self.t[self.c] = max(0, self.t[self.c] - e)
            self.l = time.time()
    def get(self, c): m,s = int(self.t[c])//60, int(self.t[c])%60; return f"{m:02d}:{s:02d}"
    def winner(self): return 'black' if self.t['white']<=0 else 'white' if self.t['black']<=0 else None

class Bot:
    def __init__(self, depth=4):
        self.depth = depth
        self.values = {Pawn: 1, Knight: 3, Bishop: 3, Rook: 5, Queen: 9, King: 1000}
        self.cache = {}

    def _state_key(self, board, color):
        pieces = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p:
                    pieces.append(f"{p.symbol}{r}{c}")
        pieces.sort()
        return ';'.join(pieces) + str(board.turn) + str(color)

    def evaluate(self, board, color):
        score = 0
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p:
                    val = self.values[type(p)]
                    if p.color == color:
                        score += val
                    else:
                        score -= val
        return score

    def get_moves(self, board, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p and p.color == color:
                    for to in board.valid_moves(p.pos):
                        moves.append((p.pos, to))
        moves.sort(key=lambda m: 1 if board.get(m[1]) else 0, reverse=True)
        return moves

    def minimax(self, board, depth, alpha, beta, maximizing, color):
        key = (self._state_key(board, color), depth, alpha, beta, maximizing, color)
        if key in self.cache:
            return self.cache[key]

        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE

        if board.checkmate(color):
            res = (-10000 + depth, None)
            self.cache[key] = res
            return res
        if board.checkmate(opponent):
            res = (10000 - depth, None)
            self.cache[key] = res
            return res
        if board.stalemate(color) or board.stalemate(opponent):
            res = (0, None)
            self.cache[key] = res
            return res
        if depth == 0:
            res = (self.evaluate(board, color), None)
            self.cache[key] = res
            return res

        if maximizing:
            max_eval = -float('inf')
            best_move = None
            for move in self.get_moves(board, color):
                b = board.copy()
                b.move(move[0], move[1])
                eval, _ = self.minimax(b, depth - 1, alpha, beta, False, color)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            res = (max_eval, best_move)
            self.cache[key] = res
            return res
        else:
            min_eval = float('inf')
            best_move = None
            for move in self.get_moves(board, opponent):
                b = board.copy()
                b.move(move[0], move[1])
                eval, _ = self.minimax(b, depth - 1, alpha, beta, True, color)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            res = (min_eval, best_move)
            self.cache[key] = res
            return res

    def best_move(self, board, color=Color.BLACK, max_time=5.0):
        start = time.time()
        best_move = None
        best_value = None

        moves = self.get_moves(board, color)
        if not moves:
            return None

        for depth in range(1, self.depth + 1):
            if time.time() - start > max_time:
                break
            current_best = None
            current_best_value = -float('inf') if color == Color.BLACK else float('inf')
            alpha = -float('inf')
            beta = float('inf')
            for move in moves:
                if time.time() - start > max_time:
                    break
                b = board.copy()
                b.move(move[0], move[1])
                if color == Color.BLACK:
                    value, _ = self.minimax(b, depth - 1, alpha, beta, False, color)
                else:
                    value, _ = self.minimax(b, depth - 1, alpha, beta, True, color)
                if color == Color.BLACK:
                    if value > current_best_value:
                        current_best_value = value
                        current_best = move
                    alpha = max(alpha, value)
                else:
                    if value < current_best_value:
                        current_best_value = value
                        current_best = move
                    beta = min(beta, value)
                if beta <= alpha:
                    break
            if current_best is not None:
                best_move = current_best
                best_value = current_best_value
            if best_value and abs(best_value) > 9000:
                break

        if best_move is None and moves:
            best_move = moves[0]
        return best_move
def init():
    pygame.font.init()
    try: pygame.mixer.init()
    except: pass
    global SC, F
    SC = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Шахматы с ботом")
    F = {'n':pygame.font.SysFont("Tahoma",24), 's':pygame.font.SysFont("Tahoma",20), 'b':pygame.font.SysFont("Verdana",40)}

def draw(board, state):
    SC.fill(COLORS['bg'])
    SC.blit(ci.CHESS_BOARD, (0,0))
    pygame.draw.rect(SC, COLORS['light'], (600,0,200,200))
    pygame.draw.rect(SC, COLORS['dark'], (600,200,200,5))
    for i,cl in enumerate(['black','white']):
        y = 220 + (70 if cl=='white' else 0)
        active = (state['player'] == cl)
        frame = COLORS['yellow'] if active else COLORS['brown']
        pygame.draw.rect(SC, frame, (610,y,180,60),3)
        pygame.draw.rect(SC, COLORS['light'], (612,y+2,176,56))
        t = F['s'].render(f"{cl.capitalize()}: {state['clock'].get(cl)}", True,
                          COLORS['red'] if active else COLORS['bg'])
        SC.blit(t, (620,y+20))
    pygame.draw.rect(SC, COLORS['white'], (600,360,200,80))
    pygame.draw.rect(SC, COLORS['bg'], (600,360,200,80),2)
    t = F['n'].render(f"Ход: {state['player'].upper()}", True, COLORS['bg'])
    SC.blit(t, t.get_rect(center=(700,400)))
    if state['check'] and int(time.time()*2)%2==0:
        SC.blit(F['n'].render("ШАХ!", True, COLORS['red']), (650,530))
    if state.get('game_over'):
        ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,128)); SC.blit(ov,(0,0))
        if state.get('checkmate'):
            txt = F['b'].render(f"{state['winner'].upper()} ПОБЕДИЛИ!", True, COLORS['green'])
        else:
            txt = F['b'].render("ПАТ!", True, COLORS['dark'])
        SC.blit(txt, txt.get_rect(center=(W//2,H//2)))
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p:
                x,y = c*CELL, r*CELL
                if state['selected'] and p.pos == state['selected'].pos:
                    pygame.draw.rect(SC, COLORS['yellow'], (x,y,CELL,CELL),3)
                SC.blit(p.img, (x,y))
    if state['moves'] and not state.get('game_over'):
        for m in state['moves']:
            rr, cc = pos_to_coord(m)
            pygame.draw.circle(SC, COLORS['dark'], (cc*CELL+37, rr*CELL+37), 10)
    pygame.display.update()

def game():
    init()
    board = Board()
    clock = Clock()
    bot = Bot(depth=4)
    state = {'player':'white', 'selected':None, 'moves':[], 'clock':clock,
             'check':False, 'game_over':False, 'checkmate':False, 'winner':None}
    clock.start('white')
    running = True

    while running:
        clock.update()

        # Победа по времени
        if winner := clock.winner():
            state['game_over'] = True
            state['checkmate'] = True
            state['winner'] = winner

        # Если игра уже окончена – показываем сообщение и выходим
        if state['game_over']:
            draw(board, state)
            pygame.display.update()
            pygame.time.wait(3000)
            break

        # Проверка мата/пата для текущего игрока
        cur_color = Color.WHITE if state['player'] == 'white' else Color.BLACK
        if board.checkmate(cur_color):
            state['game_over'] = True
            state['checkmate'] = True
            state['winner'] = 'black' if state['player'] == 'white' else 'white'
            continue   # сразу переходим к отрисовке конца игры
        if board.stalemate(cur_color):
            state['game_over'] = True
            state['checkmate'] = False
            state['winner'] = None
            continue

        # Ход бота (чёрные)
        if state['player'] == 'black':
            move = bot.best_move(board)
            if move:
                from_pos, to_pos = move
                if board.move(from_pos, to_pos):
                    if ci.MOVE_SOUND: ci.MOVE_SOUND.play()
                    clock.switch()
                    state['player'] = 'white'
            draw(board, state)
            continue

        # Обработка событий (ход игрока – белые)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN and state['player'] == 'white':
                x, y = pygame.mouse.get_pos()
                if x < 600:
                    col, row = x // CELL, y // CELL
                    if 0 <= row < 8 and 0 <= col < 8:
                        if not state['selected']:
                            piece = board.squares[row][col]
                            if piece and piece.color == Color.WHITE:
                                state['selected'] = piece
                                state['moves'] = board.valid_moves(piece.pos)
                        else:
                            target = coord_to_pos(row, col)
                            if target in state['moves'] and board.move(state['selected'].pos, target):
                                if ci.MOVE_SOUND: ci.MOVE_SOUND.play()
                                clock.switch()
                                state['player'] = 'black'
                            state['selected'] = None
                            state['moves'] = []

        if state['player'] == 'white':
            state['check'] = board.in_check(Color.WHITE)
        else:
            state['check'] = board.in_check(Color.BLACK)

        draw(board, state)
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    if show_login():
        game()