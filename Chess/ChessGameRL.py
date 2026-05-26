import pygame, tkinter as tk, os, time, random
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
from figures import Color, Pawn, Knight, Bishop, Rook, Queen, King
from board import Board, pos_to_coord, coord_to_pos, opposite_color
import items as ci

from selfplay_rl import SelfPlayRL

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

def init():
    pygame.font.init()
    try: pygame.mixer.init()
    except: pass
    global SC, F
    SC = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Шахматы с обученным RL-ботом")
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

    # Загружаем обученного RL-агента
    model_path = "rl_6pieces_final.pkl"   
    rl_agent = SelfPlayRL(epsilon=0.0)    
    if not rl_agent.load(model_path):
        print(f"Ошибка: не удалось загрузить модель {model_path}. Завершение работы.")
        pygame.quit()
        return
    print(f"RL-агент загружен из {model_path}")

    board = Board()
    clock = Clock()
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

        if state['game_over']:
            draw(board, state)
            pygame.display.update()
            pygame.time.wait(3000)
            break

        cur_color = Color.WHITE if state['player'] == 'white' else Color.BLACK
        if board.checkmate(cur_color):
            state['game_over'] = True
            state['checkmate'] = True
            state['winner'] = 'black' if state['player'] == 'white' else 'white'
            continue
        if board.stalemate(cur_color):
            state['game_over'] = True
            state['checkmate'] = False
            state['winner'] = None
            continue

        # Ход чёрных (RL-агент)
        if state['player'] == 'black':
            action = rl_agent.choose_action(board, Color.BLACK, training=False)
            if action:
                frm, to = action
                if board.move(frm, to):
                    if ci.MOVE_SOUND: ci.MOVE_SOUND.play()
                    clock.switch()
                    state['player'] = 'white'
            draw(board, state)
            continue

        # Ход белых (человек)
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
