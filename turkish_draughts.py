# Project: Turkish Draughts (Türk Daması)
# Author: Emir ÇOBAN
# License: MIT License
# Description: A Turkish Draughts game with AI implemented in Python using Pygame.

import pygame
import sys
import time
import random
import copy
import os

# --- Sabitler ---
WIDTH = 840
HEIGHT = 640
BOARD_WIDTH = 640
SQUARE_SIZE = BOARD_WIDTH // 8

# Renkler
COLOR_BG = (40, 40, 40)
COLOR_BOARD_LIGHT = (238, 238, 210)
COLOR_BOARD_DARK = (118, 150, 86)
COLOR_WHITE_PIECE = (240, 240, 240)
COLOR_BLACK_PIECE = (40, 40, 40)
COLOR_HIGHLIGHT = (0, 255, 0)
COLOR_LAST_MOVE = (255, 255, 0)
COLOR_POSSIBLE_MOVE = (100, 100, 255)
COLOR_HINT = (0, 255, 255) # Turkuaz

# Temalar
THEMES = {
    "Klasik": {
        "bg": (40, 40, 40),
        "light": (238, 238, 210),
        "dark": (118, 150, 86),
        "white_p": (240, 240, 240),
        "black_p": (40, 40, 40)
    },
    "Mavi": {
        "bg": (30, 30, 50),
        "light": (200, 200, 255),
        "dark": (70, 70, 150),
        "white_p": (240, 240, 255),
        "black_p": (20, 20, 40)
    },
    "Ahşap": {
        "bg": (60, 40, 20),
        "light": (220, 190, 150),
        "dark": (140, 90, 50),
        "white_p": (255, 240, 220),
        "black_p": (50, 30, 10)
    },
    "Gri": {
        "bg": (20, 20, 20),
        "light": (180, 180, 180),
        "dark": (80, 80, 80),
        "white_p": (220, 220, 220),
        "black_p": (10, 10, 10)
    }
}

# Taş Tipleri
EMPTY = 0
WHITE = 1
BLACK = -1
WHITE_KING = 2
BLACK_KING = -2

class TurkishDraughtsGame:
    def __init__(self):
        self.board = [[0] * 8 for _ in range(8)]
        self.turn = WHITE
        self.selected_piece = None
        self.valid_moves = {} # {(r, c): [Move objects...]}
        self.winner = None
        self.chain_piece = None # Zincirleme hamle yapan taşın konumu
        self.move_history = []
        self.forced_capture = False # Zorunlu alma durumu var mı?
        self.setup_board()

    def setup_board(self):
        # Türk Daması Başlangıç Dizilimi
        # Siyahlar 2. ve 3. satırda (indeks 1, 2)
        # Beyazlar 6. ve 7. satırda (indeks 5, 6)
        for r in range(8):
            for c in range(8):
                if r == 1 or r == 2:
                    self.board[r][c] = BLACK
                elif r == 5 or r == 6:
                    self.board[r][c] = WHITE
                else:
                    self.board[r][c] = EMPTY

    def get_piece(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.board[r][c]
        return None

    def switch_turn(self):
        self.turn = BLACK if self.turn == WHITE else WHITE
        self.check_winner()

    def check_winner(self):
        whites = 0
        blacks = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p > 0: whites += 1
                if p < 0: blacks += 1
        
        if whites == 0: self.winner = BLACK
        elif blacks == 0: self.winner = WHITE
        else: self.winner = None

    def get_all_legal_moves(self, player):
        """
        Tüm yasal hamleleri döndürür.
        Zorunlu alma kuralı kaldırıldı.
        """
        possible_moves = {} # {(r, c): [Move objects...]}
        
        # Eğer zincirleme hamle zorunluluğu varsa, sadece o taşa bak
        if self.chain_piece:
            r, c = self.chain_piece
            piece = self.board[r][c]
            moves, is_capture = self.get_moves_for_piece(r, c, piece)
            # Zincir durumunda sadece yeme hamleleri geçerlidir
            if is_capture:
                capture_moves = [m for m in moves if m['captured']]
                return {self.chain_piece: capture_moves}
            return {}

        # Tüm taşları kontrol et
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if (player == WHITE and piece > 0) or (player == BLACK and piece < 0):
                    moves, is_capture = self.get_moves_for_piece(r, c, piece)
                    if moves:
                        if (r, c) not in possible_moves: possible_moves[(r, c)] = []
                        possible_moves[(r, c)].extend(moves)

        self.forced_capture = False
        return possible_moves

    def get_max_capture_chain(self, board, r, c, move):
        """Bir hamlenin sonucunda toplam kaç taş yenebileceğini hesaplar (DFS)."""
        # Simülasyon için tahtayı kopyala
        temp_board = [row[:] for row in board]
        piece = temp_board[r][c]
        
        tr, tc = move['to']
        
        # Taşı oynat ve yenilenleri kaldır
        temp_board[tr][tc] = piece
        temp_board[r][c] = EMPTY
        for cr, cc in move['captured']:
            temp_board[cr][cc] = EMPTY
            
        current_capture_count = len(move['captured'])
        
        # Eğer taş dama olduysa zincir biter (Türk daması kuralı)
        if (piece == WHITE and tr == 0) or (piece == BLACK and tr == 7):
            return current_capture_count

        # Buradan devam eden başka yeme hamlesi var mı?
        # Not: Bu simülasyon olduğu için 'self.get_moves_for_piece' yerine
        # board parametresi alan bir yardımcıya ihtiyacımız var ama
        # mevcut yapıda board'u self.board'dan okuyor.
        # Bu yüzden geçici olarak self.board'u değiştirip geri alacağız.
        
        original_board = self.board
        self.board = temp_board # Geçici değişim
        
        next_moves, is_next_capture = self.get_moves_for_piece(tr, tc, piece)
        
        max_future_captures = 0
        if is_next_capture:
            for next_move in next_moves:
                # Recursive çağrı
                future_len = self.get_max_capture_chain(temp_board, tr, tc, next_move)
                if future_len > max_future_captures:
                    max_future_captures = future_len
        
        self.board = original_board # Geri yükle
        
        return current_capture_count + max_future_captures

    def get_moves_for_piece(self, r, c, piece):
        moves = []
        is_capture = False
        
        directions = []
        is_king = abs(piece) == 2
        
        # Yönler: (dr, dc)
        if is_king:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Yukarı, Aşağı, Sol, Sağ
        else:
            # Normal taşlar
            directions = [(0, -1), (0, 1)] # Sol, Sağ
            if piece == WHITE:
                directions.append((-1, 0)) # Yukarı
            else:
                directions.append((1, 0)) # Aşağı

        # Hamleleri hesapla
        for dr, dc in directions:
            if is_king:
                # Dama Taşı Mantığı (Uzun menzil)
                for dist in range(1, 8):
                    nr, nc = r + dr * dist, c + dc * dist
                    if not (0 <= nr < 8 and 0 <= nc < 8): break
                    
                    target = self.board[nr][nc]
                    
                    if target == EMPTY:
                        moves.append({'to': (nr, nc), 'captured': []})
                    elif (piece > 0 and target < 0) or (piece < 0 and target > 0):
                        # Düşman taşı bulundu, arkası boş mu?
                        # Dama taşı yediği taşın arkasındaki herhangi bir boş kareye konabilir.
                        landing_dist = 1
                        while True:
                            nnr, nnc = nr + dr * landing_dist, nc + dc * landing_dist
                            if 0 <= nnr < 8 and 0 <= nnc < 8 and self.board[nnr][nnc] == EMPTY:
                                is_capture = True
                                moves.append({'to': (nnr, nnc), 'captured': [(nr, nc)]})
                                landing_dist += 1
                            else:
                                # Tahta dışı veya dolu kare
                                break
                        break # Düşman taşı görüldü, bu yönde daha fazla bakılamaz
                    else:
                        break # Kendi taşı
            else:
                # Normal Taş Mantığı
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.board[nr][nc]
                    
                    if target == EMPTY:
                        moves.append({'to': (nr, nc), 'captured': []})
                    elif (piece > 0 and target < 0) or (piece < 0 and target > 0):
                        # Düşman var, üstünden atla
                        nnr, nnc = nr + dr, nc + dc
                        if 0 <= nnr < 8 and 0 <= nnc < 8 and self.board[nnr][nnc] == EMPTY:
                            is_capture = True
                            moves.append({'to': (nnr, nnc), 'captured': [(nr, nc)]})

        return moves, is_capture

    def make_move(self, start_pos, move_data):
        r, c = start_pos
        tr, tc = move_data['to']
        piece = self.board[r][c]
        
        # Taşı taşı
        self.board[tr][tc] = piece
        self.board[r][c] = EMPTY
        
        # Yenilen taşları kaldır
        for cr, cc in move_data['captured']:
            self.board[cr][cc] = EMPTY
            
        promoted = False
        # Dama olma kontrolü
        if piece == WHITE and tr == 0:
            self.board[tr][tc] = WHITE_KING
            promoted = True
        elif piece == BLACK and tr == 7:
            self.board[tr][tc] = BLACK_KING
            promoted = True
            
        self.move_history.append((start_pos, (tr, tc)))
        
        # Zincirleme Yeme Kontrolü
        # Türk Daması Kuralı: Dama olan taş hemen oynamaz. Promoted ise zincir biter.
        if move_data['captured'] and not promoted: 
            # Taş yendi ve dama olmadıysa, aynı taşın devam edip edemeyeceğine bak
            next_moves, is_next_capture = self.get_moves_for_piece(tr, tc, self.board[tr][tc])
            
            # Sadece yeme hamlesi varsa zincir devam eder
            if is_next_capture:
                self.chain_piece = (tr, tc)
                # Valid moves'u sadece bu taşın yeme hamleleri olarak güncelle
                # Ancak get_moves_for_piece zaten sadece yeme varsa onları döndürür (is_capture=True ise)
                # Fakat biz yine de formatı koruyalım
                capture_moves = [m for m in next_moves if m['captured']]
                self.valid_moves = {(tr, tc): capture_moves}
                return # Sıra değişmez

        # Zincir bitti veya normal hamle yapıldı
        self.chain_piece = None
        self.switch_turn()

# --- GUI Fonksiyonları ---

def draw_rules_screen(screen):
    """Oyun kurallarını gösteren bilgi ekranı."""
    font_title = pygame.font.SysFont("Arial", 40, bold=True)
    font_text = pygame.font.SysFont("Arial", 24)
    clock = pygame.time.Clock()
    
    rules = [
        "1. Taşlar ileri, sağa ve sola bir kare hareket eder.",
        "2. Geriye doğru hareket yapılamaz (Dama hariç).",
        "3. Rakip taşın arkası boşsa üzerinden atlayarak yenir.",
        "4. Son satıra ulaşan taş 'Dama' olur.",
        "5. Dama taşı L şeklinde (Kale gibi) hareket edebilir.",
        "6. Rakibin tüm taşlarını toplayan veya hareket",
        "   kabiliyetini bitiren kazanır."
    ]
    
    while True:
        screen.fill((40, 40, 40))
        
        # Başlık
        title = font_title.render("Türk Daması Kuralları", True, (255, 200, 100))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Kurallar
        start_y = 150
        for i, line in enumerate(rules):
            text = font_text.render(line, True, (220, 220, 220))
            screen.blit(text, (100, start_y + i * 40))
            
        # Devam Butonu
        btn_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 60)
        pygame.draw.rect(screen, (0, 150, 0), btn_rect)
        pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2)
        
        btn_text = font_title.render("Başla", True, (255, 255, 255))
        screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2, btn_rect.centery - btn_text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.collidepoint(event.pos):
                    return
        clock.tick(30)

def draw_player_menu(screen):
    """Oyuncu rengi seçimi için menü çizer."""
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()
    
    while True:
        screen.fill((50, 50, 50))
        
        title = font.render("Taraf Seçin / Choose Side", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        
        # Butonlar
        white_rect = pygame.Rect(WIDTH // 2 - 100, 250, 200, 60)
        black_rect = pygame.Rect(WIDTH // 2 - 100, 350, 200, 60)
        
        pygame.draw.rect(screen, COLOR_WHITE_PIECE, white_rect)
        pygame.draw.rect(screen, COLOR_BLACK_PIECE, black_rect)
        
        w_text = font.render("Beyaz", True, COLOR_BLACK_PIECE)
        b_text = font.render("Siyah", True, COLOR_WHITE_PIECE)
        
        screen.blit(w_text, (white_rect.centerx - w_text.get_width() // 2, white_rect.centery - w_text.get_height() // 2))
        screen.blit(b_text, (black_rect.centerx - b_text.get_width() // 2, black_rect.centery - b_text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if white_rect.collidepoint(event.pos): return WHITE
                if black_rect.collidepoint(event.pos): return BLACK
        clock.tick(30)

def draw_difficulty_menu(screen):
    """Zorluk seviyesi seçimi için menü çizer."""
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()
    
    while True:
        screen.fill((50, 50, 50))
        
        title = font.render("Zorluk Seçin / Difficulty", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        
        # Butonlar
        easy_rect = pygame.Rect(WIDTH // 2 - 100, 200, 200, 60)
        med_rect = pygame.Rect(WIDTH // 2 - 100, 300, 200, 60)
        hard_rect = pygame.Rect(WIDTH // 2 - 100, 400, 200, 60)
        
        pygame.draw.rect(screen, (150, 255, 150), easy_rect)
        pygame.draw.rect(screen, (255, 255, 150), med_rect)
        pygame.draw.rect(screen, (255, 150, 150), hard_rect)
        
        e_text = font.render("Kolay", True, (0, 0, 0))
        m_text = font.render("Orta", True, (0, 0, 0))
        h_text = font.render("Zor", True, (0, 0, 0))
        
        screen.blit(e_text, (easy_rect.centerx - e_text.get_width() // 2, easy_rect.centery - e_text.get_height() // 2))
        screen.blit(m_text, (med_rect.centerx - m_text.get_width() // 2, med_rect.centery - m_text.get_height() // 2))
        screen.blit(h_text, (hard_rect.centerx - h_text.get_width() // 2, hard_rect.centery - h_text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_rect.collidepoint(event.pos): return 1
                if med_rect.collidepoint(event.pos): return 3
                if hard_rect.collidepoint(event.pos): return 5
        clock.tick(30)

def draw_theme_menu(screen):
    """Tema seçimi için menü çizer."""
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()
    
    theme_names = list(THEMES.keys())
    
    while True:
        screen.fill((50, 50, 50))
        
        title = font.render("Tema Seçin / Choose Theme", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        rects = []
        start_y = 150
        for i, name in enumerate(theme_names):
            rect = pygame.Rect(WIDTH // 2 - 120, start_y + i * 80, 240, 60)
            rects.append(rect)
            
            theme = THEMES[name]
            # Buton arka planı olarak tema renklerini kullan
            pygame.draw.rect(screen, theme["dark"], rect)
            pygame.draw.rect(screen, theme["light"], rect.inflate(-10, -10))
            
            text = font.render(name, True, (0, 0, 0))
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return THEMES[theme_names[i]]
        clock.tick(30)

def load_sounds():
    """Ses dosyalarını yükler."""
    pygame.mixer.init()
    sounds = {}
    # Dosya adları: move.wav, capture.wav, notify.wav
    for name in ['move', 'capture', 'notify']:
        path = os.path.join("assets", f"{name}.wav")
        if os.path.exists(path):
            sounds[name] = pygame.mixer.Sound(path)
    return sounds

def draw_board_grid(screen):
    for r in range(8):
        for c in range(8):
            color = COLOR_BOARD_LIGHT if (r + c) % 2 == 0 else COLOR_BOARD_DARK
            pygame.draw.rect(screen, color, (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, game):
    for r in range(8):
        for c in range(8):
            piece = game.board[r][c]
            if piece != 0:
                x = c * SQUARE_SIZE + SQUARE_SIZE // 2
                y = r * SQUARE_SIZE + SQUARE_SIZE // 2
                radius = SQUARE_SIZE // 2 - 10
                
                color = COLOR_WHITE_PIECE if piece > 0 else COLOR_BLACK_PIECE
                pygame.draw.circle(screen, color, (x, y), radius)
                
                # Çerçeve
                pygame.draw.circle(screen, (0,0,0), (x, y), radius, 2)
                
                # Dama (King) İşareti
                if abs(piece) == 2:
                    pygame.draw.circle(screen, (255, 0, 0), (x, y), radius // 4)

def draw_highlights(screen, game, hint_move=None):
    # Seçili taş
    if game.selected_piece:
        r, c = game.selected_piece
        rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, rect, 4)
        
        # Olası hamleler
        if game.selected_piece in game.valid_moves:
            for move in game.valid_moves[game.selected_piece]:
                tr, tc = move['to']
                center = (tc * SQUARE_SIZE + SQUARE_SIZE // 2, tr * SQUARE_SIZE + SQUARE_SIZE // 2)
                pygame.draw.circle(screen, COLOR_POSSIBLE_MOVE, center, 10)

    # Son hamle
    if game.move_history:
        start, end = game.move_history[-1]
        for r, c in [start, end]:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(COLOR_LAST_MOVE)
            screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))
            
    # İpucu (Hint)
    if hint_move:
        start, move_data = hint_move
        sr, sc = start
        er, ec = move_data['to']
        
        start_center = (sc * SQUARE_SIZE + SQUARE_SIZE // 2, sr * SQUARE_SIZE + SQUARE_SIZE // 2)
        end_center = (ec * SQUARE_SIZE + SQUARE_SIZE // 2, er * SQUARE_SIZE + SQUARE_SIZE // 2)
        pygame.draw.line(screen, COLOR_HINT, start_center, end_center, 5)

def to_notation(r, c):
    """Koordinatları notasyona çevirir (örn: 5,0 -> a3)."""
    # Sütun: 0->a, 1->b...
    # Satır: 7->1, 0->8 (Ters)
    col_char = chr(ord('a') + c)
    row_char = str(8 - r)
    return f"{col_char}{row_char}"

def draw_captured_pieces(screen, game):
    """Alınan taşları sağ panelde gösterir."""
    # Başlangıçta 16 taş vardır.
    w_count = sum(row.count(WHITE) + row.count(WHITE_KING) for row in game.board)
    b_count = sum(row.count(BLACK) + row.count(BLACK_KING) for row in game.board)
    
    # Beyazın aldıkları (Eksilen Siyahlar)
    captured_black = 16 - b_count
    # Siyahın aldıkları (Eksilen Beyazlar)
    captured_white = 16 - w_count
    
    start_x = BOARD_WIDTH + 20
    y_pos = 140
    radius = 10
    
    # Beyazın Aldıkları (Siyah taş ikonları)
    for i in range(captured_black):
        pygame.draw.circle(screen, COLOR_BLACK_PIECE, (start_x + i * 25, y_pos), radius)
        pygame.draw.circle(screen, (200, 200, 200), (start_x + i * 25, y_pos), radius, 1)
        
    # Siyahın Aldıkları (Beyaz taş ikonları)
    for i in range(captured_white):
        pygame.draw.circle(screen, COLOR_WHITE_PIECE, (start_x + i * 25, y_pos + 30), radius)

def draw_move_history(screen, game):
    """Hamle geçmişini sağ panelde listeler."""
    font = pygame.font.SysFont("Arial", 16)
    start_x = BOARD_WIDTH + 20
    start_y = 280 # Butonların altından başla
    line_height = 20
    max_lines = 12  # Ekrana sığacak maksimum satır sayısı (Menü butonu için yer açıldı)
    
    # Hamleleri çiftler halinde grupla (Beyaz, Siyah)
    history_lines = []
    for i in range(0, len(game.move_history), 2):
        move_num = (i // 2) + 1
        
        # Beyaz Hamlesi
        w_start, w_end = game.move_history[i]
        w_str = f"{to_notation(*w_start)}-{to_notation(*w_end)}"
        
        line = f"{move_num}. {w_str}"
        
        # Siyah Hamlesi (varsa)
        if i + 1 < len(game.move_history):
            b_start, b_end = game.move_history[i+1]
            b_str = f"{to_notation(*b_start)}-{to_notation(*b_end)}"
            line += f"   {b_str}"
            
        history_lines.append(line)
    
    # Son hamleleri göstermek için listeyi kaydır
    start_index = max(0, len(history_lines) - max_lines)
    
    for i in range(start_index, len(history_lines)):
        text = font.render(history_lines[i], True, (220, 220, 220))
        screen.blit(text, (start_x, start_y + (i - start_index) * line_height))

def draw_gui_panel(screen, game, difficulty, ai_thinking=False):
    pygame.draw.rect(screen, COLOR_BG, (BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, HEIGHT))
    font = pygame.font.SysFont("Arial", 24)
    
    turn_text = "Sıra: Beyaz" if game.turn == WHITE else "Sıra: Siyah"
    text_surf = font.render(turn_text, True, (255, 255, 255))
    screen.blit(text_surf, (BOARD_WIDTH + 20, 50))
    
    # Ana Menü Butonu (Her zaman görünür)
    menu_btn_rect = pygame.Rect(BOARD_WIDTH + 20, HEIGHT - 70, 160, 50)
    pygame.draw.rect(screen, (100, 50, 50), menu_btn_rect)
    pygame.draw.rect(screen, (200, 200, 200), menu_btn_rect, 2)
    menu_text = font.render("Menü", True, (255, 255, 255))
    screen.blit(menu_text, (menu_btn_rect.centerx - menu_text.get_width() // 2, menu_btn_rect.centery - menu_text.get_height() // 2))

    undo_btn_rect = None
    hint_btn_rect = None

    # Sadece Kolay modda (difficulty == 1) butonları göster
    if difficulty == 1:
        # Geri Al Butonu (Menü butonunun üstünde)
        undo_btn_rect = pygame.Rect(BOARD_WIDTH + 20, HEIGHT - 130, 160, 50)
        pygame.draw.rect(screen, (70, 70, 70), undo_btn_rect)
        pygame.draw.rect(screen, (200, 200, 200), undo_btn_rect, 2)
        undo_text = font.render("Geri Al", True, (255, 255, 255))
        screen.blit(undo_text, (undo_btn_rect.centerx - undo_text.get_width() // 2, undo_btn_rect.centery - undo_text.get_height() // 2))
        
        # İpucu Butonu
        hint_btn_rect = pygame.Rect(BOARD_WIDTH + 20, 200, 160, 40)
        pygame.draw.rect(screen, (0, 100, 100), hint_btn_rect)
        pygame.draw.rect(screen, (0, 200, 200), hint_btn_rect, 2)
        hint_text = font.render("İpucu", True, (255, 255, 255))
        screen.blit(hint_text, (hint_btn_rect.centerx - hint_text.get_width() // 2, hint_btn_rect.centery - hint_text.get_height() // 2))

    # Durum Bilgileri
    if ai_thinking:
        think_text = font.render("Düşünüyor...", True, (100, 255, 255))
        screen.blit(think_text, (BOARD_WIDTH + 20, 100))
    elif game.forced_capture and game.turn == WHITE:
        # Zorunlu hamle uyarısı
        warn_font = pygame.font.SysFont("Arial", 20, bold=True)
        warn_text = warn_font.render("ZORUNLU ALMA!", True, (255, 100, 100))
        screen.blit(warn_text, (BOARD_WIDTH + 20, 100))

    draw_captured_pieces(screen, game)
    draw_move_history(screen, game)

    return undo_btn_rect, hint_btn_rect, menu_btn_rect

def draw_game_over_modal(screen, winner, move_count):
    """Oyun bittiğinde ekranı kaplayan modern bir sonuç ekranı."""
    # Yarı saydam arka plan
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    font_big = pygame.font.SysFont("Arial", 64, bold=True)
    font_small = pygame.font.SysFont("Arial", 32)
    
    text = "BEYAZ KAZANDI!" if winner == WHITE else "SIYAH KAZANDI!"
    color = (0, 255, 0) if winner == WHITE else (255, 50, 50)
    
    text_surf = font_big.render(text, True, color)
    text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
    screen.blit(text_surf, text_rect)
    
    # Hamle Sayısı
    moves_surf = font_small.render(f"Toplam Hamle: {move_count}", True, (220, 220, 220))
    moves_rect = moves_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
    screen.blit(moves_surf, moves_rect)
    
    # Yeniden Başlat Butonu
    btn_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 50, 240, 60)
    pygame.draw.rect(screen, (200, 200, 200), btn_rect)
    pygame.draw.rect(screen, (50, 50, 50), btn_rect, 3)
    
    btn_text = font_small.render("Yeniden Başlat", True, (0, 0, 0))
    screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2, btn_rect.centery - btn_text.get_height() // 2))
    
    return btn_rect

def evaluate_board(game):
    """Tahtayı puanlar. Siyah (AI) için pozitif, Beyaz için negatif."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = game.board[r][c]
            if piece == 0: continue
            
            # Puanlama: Normal taş 10, Dama 50 puan
            val = 10 if abs(piece) == 1 else 50
            
            if piece < 0: score += val # Siyah (AI)
            else: score -= val # Beyaz (Oyuncu)
    return score

def minimax(game, depth, alpha, beta, maximizing_player):
    """Minimax algoritması (Alpha-Beta Pruning ile)."""
    if depth == 0 or game.winner:
        return evaluate_board(game), None

    legal_moves = game.get_all_legal_moves(game.turn)
    if not legal_moves:
        return evaluate_board(game), None

    # Hamleleri düzleştir: [(start_pos, move_data), ...]
    all_moves = []
    for start_pos, moves in legal_moves.items():
        for move in moves:
            all_moves.append((start_pos, move))

    # Optimizasyon: Yeme hamlelerini önce dene (Budama şansını artırır)
    random.shuffle(all_moves) # Eşit puanlı hamlelerde çeşitlilik için
    all_moves.sort(key=lambda x: 1 if x[1]['captured'] else 0, reverse=True)

    best_move = None
    
    if maximizing_player:
        max_eval = -float('inf')
        for start, move in all_moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(start, move)
            
            # Sıradaki oyuncu Siyah ise maximizing devam eder
            next_is_max = (new_game.turn == BLACK)
            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, next_is_max)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (start, move)
            alpha = max(alpha, eval_score)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for start, move in all_moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(start, move)
            
            next_is_max = (new_game.turn == BLACK)
            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, next_is_max)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (start, move)
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval, best_move

def get_ai_move(game, depth=3):
    """Minimax kullanarak en iyi hamleyi hesaplar."""
    # AI rengine göre maximizing_player belirle
    is_maximizing = (game.turn == BLACK)
    _, best_move = minimax(game, depth, -float('inf'), float('inf'), is_maximizing)
    
    if best_move:
        return best_move
    else:
        return None, None

def main():
    global COLOR_BG, COLOR_BOARD_LIGHT, COLOR_BOARD_DARK, COLOR_WHITE_PIECE, COLOR_BLACK_PIECE
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Türk Daması")
    clock = pygame.time.Clock()

    while True: # Ana Oturum Döngüsü (Menüye dönüş için)
        draw_rules_screen(screen)
        player_color = draw_player_menu(screen)
        difficulty = draw_difficulty_menu(screen)
        selected_theme = draw_theme_menu(screen)
        
        # Seçilen temayı uygula
        COLOR_BG = selected_theme["bg"]
        COLOR_BOARD_LIGHT = selected_theme["light"]
        COLOR_BOARD_DARK = selected_theme["dark"]
        COLOR_WHITE_PIECE = selected_theme["white_p"]
        COLOR_BLACK_PIECE = selected_theme["black_p"]
        
        ai_color = BLACK if player_color == WHITE else WHITE

        game = TurkishDraughtsGame()

        # Başlangıçta geçerli hamleleri hesapla
        game.valid_moves = game.get_all_legal_moves(game.turn)
        history = [] # Geri alma (Undo) için geçmiş
        sounds = load_sounds()
        hint_move = None
        
        undo_rect = None
        restart_rect = None
        hint_rect = None
        menu_rect = None
        
        running = True
        while running:
            screen.fill((0, 0, 0))
            
            # Olaylar
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game = TurkishDraughtsGame()
                        game.valid_moves = game.get_all_legal_moves(game.turn)
                        game.chain_piece = None
                        game.selected_piece = None
                        history = []
                        hint_move = None
                        undo_rect = None
                        restart_rect = None
                        hint_rect = None
                        # Not: 'R' tuşu mevcut renk seçimiyle oyunu yeniden başlatır.

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    # Menü Butonu
                    if menu_rect and menu_rect.collidepoint((x, y)):
                        running = False # İç döngüyü kır, dış döngü başa döner
                        break
                    
                    # Oyun bittiyse Restart kontrolü
                    if game.winner and restart_rect and restart_rect.collidepoint((x, y)):
                        game = TurkishDraughtsGame()
                        game.valid_moves = game.get_all_legal_moves(game.turn)
                        history = []
                        hint_move = None
                        undo_rect = None
                        restart_rect = None
                        hint_rect = None
                        continue

                    # Geri Al (Undo) Butonu
                    if not game.winner and undo_rect and undo_rect.collidepoint((x, y)):
                        if history:
                            game = history.pop()
                            game.selected_piece = None
                            hint_move = None
                        continue
                    
                    # İpucu (Hint) Butonu
                    if not game.winner and hint_rect and hint_rect.collidepoint((x, y)):
                        # O anki oyuncu için en iyi hamleyi hesapla
                        is_maximizing = True if game.turn == BLACK else False
                        _, hint_move = minimax(game, 3, -float('inf'), float('inf'), is_maximizing)
                        continue

                    if not game.winner and game.turn == player_color: # Sadece oyuncunun sırasıysa
                        if x < BOARD_WIDTH:
                            c = x // SQUARE_SIZE
                            r = y // SQUARE_SIZE
                            
                            # Kendi taşını seçme
                            if (r, c) in game.valid_moves:
                                game.selected_piece = (r, c)
                            
                            # Seçili taşla hamle yapma
                            elif game.selected_piece:
                                possible_moves = game.valid_moves.get(game.selected_piece, [])
                                for move in possible_moves:
                                    if move['to'] == (r, c):
                                        # Hamle yapmadan önce durumu kaydet
                                        history.append(copy.deepcopy(game))
                                        
                                        game.make_move(game.selected_piece, move)
                                        game.selected_piece = None
                                        hint_move = None # Hamle yapınca ipucunu temizle
                                        
                                        # Ses çal
                                        is_capture = len(move['captured']) > 0
                                        sound_key = 'capture' if is_capture else 'move'
                                        if sound_key in sounds: sounds[sound_key].play()
                                        
                                        # Eğer zincir yoksa tüm hamleleri hesapla, varsa make_move zaten ayarladı
                                        if not game.chain_piece:
                                            game.valid_moves = game.get_all_legal_moves(game.turn)
                                        break
            
            # AI Hamlesi (Siyah)
            if running and game.turn == ai_color and not game.winner:
                # AI düşünmeden önce ekranı çiz ki "Düşünüyor..." yazısı görünsün
                draw_board_grid(screen)
                draw_highlights(screen, game, hint_move)
                draw_pieces(screen, game)
                draw_gui_panel(screen, game, difficulty, ai_thinking=True)
                pygame.display.flip()
                
                time.sleep(0.5) # Düşünme efekti
                start_pos, move = get_ai_move(game, depth=difficulty)
                if start_pos:
                    game.make_move(start_pos, move)
                    
                    # Ses çal
                    is_capture = len(move['captured']) > 0
                    sound_key = 'capture' if is_capture else 'move'
                    if sound_key in sounds: sounds[sound_key].play()
                    hint_move = None

                    if not game.chain_piece:
                        game.valid_moves = game.get_all_legal_moves(game.turn)
                else:
                    # Yapacak hamle yoksa kaybetmiştir
                    game.winner = WHITE

            # Çizimler
            draw_board_grid(screen)
            draw_highlights(screen, game, hint_move)
            draw_pieces(screen, game)
            undo_rect, hint_rect, menu_rect = draw_gui_panel(screen, game, difficulty)
            
            if game.winner:
                restart_rect = draw_game_over_modal(screen, game.winner, len(game.move_history))
            
            pygame.display.flip()
            clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
