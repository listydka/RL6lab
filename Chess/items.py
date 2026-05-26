import pygame, os
pygame.mixer.init()
SIZE = (70, 70)
def load(path): return pygame.transform.smoothscale(pygame.image.load(path), SIZE)

CHESS_BOARD = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "blue.png")), (600, 600))
WHITE_PAWN = load(os.path.join("Assets/chesspieces", "wP.png"))
WHITE_ROOK = load(os.path.join("Assets/chesspieces", "wR.png"))
WHITE_KNIGHT = load(os.path.join("Assets/chesspieces", "wN.png"))
WHITE_BISHOP = load(os.path.join("Assets/chesspieces", "wB.png"))
WHITE_QUEEN = load(os.path.join("Assets/chesspieces", "wQ.png"))
WHITE_KING = load(os.path.join("Assets/chesspieces", "wK.png"))
BLACK_PAWN = load(os.path.join("Assets/chesspieces", "bp.png"))
BLACK_ROOK = load(os.path.join("Assets/chesspieces", "bR.png"))
BLACK_KNIGHT = load(os.path.join("Assets/chesspieces", "bN.png"))
BLACK_BISHOP = load(os.path.join("Assets/chesspieces", "bB.png"))
BLACK_QUEEN = load(os.path.join("Assets/chesspieces", "bQ.png"))
BLACK_KING = load(os.path.join("Assets/chesspieces", "bK.png"))
try:
    MOVE_SOUND = pygame.mixer.Sound(os.path.join("Assets", "Move.wav"))
    CAPTURE_SOUND = pygame.mixer.Sound(os.path.join("Assets", "Capture.wav"))
except:
    MOVE_SOUND = CAPTURE_SOUND = None
