# Project: Chess Bot Analysis GUI
# Author: Emir ÇOBAN
# License: MIT License
# Description: A GUI for chess analysis using Stockfish engine.

import pygame
import chess
import chess.engine
import os
import time

# --- Motor ve Sabitler ---
STOCKFISH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")

# Pencere boyutları
WIDTH = 840
HEIGHT = 640
BOARD_WIDTH = 640
SQUARE_SIZE = BOARD_WIDTH // 8

# Renkler
BOARD_LIGHT = (238, 238, 210)
BOARD_DARK = (118, 150, 86)

# --- Yardımcı Fonksiyonlar ---

def load_piece_images():
    """Satranç taşı resimlerini yükler ve bir sözlükte saklar."""
    # Kodun kullandığı taş isimleri (örn: wP) ile dosya adları arasındaki eşleşme
    # w -> l (light), b -> d (dark)
    # P, R, N, B, Q, K -> p, r, n, b, q, k
    piece_map = {
        'wP': 'Chess_plt60.png', 'wR': 'Chess_rlt60.png', 'wN': 'Chess_nlt60.png', 
        'wB': 'Chess_blt60.png', 'wQ': 'Chess_qlt60.png', 'wK': 'Chess_klt60.png',
        'bP': 'Chess_pdt60.png', 'bR': 'Chess_rdt60.png', 'bN': 'Chess_ndt60.png', 
        'bB': 'Chess_bdt60.png', 'bQ': 'Chess_qdt60.png', 'bK': 'Chess_kdt60.png'
    }
    
    images = {}
    for piece_key, filename in piece_map.items():
        path = os.path.join("assets", filename)
        if not os.path.exists(path):
            # Bu hata mesajı, eşleşme haritası doğruysa görünmemeli
            raise FileNotFoundError(f"HATA: Resim dosyası bulunamadı: {path}. 'assets' klasörünü ve resimleri kontrol edin.")
        
        image = pygame.image.load(path)
        images[piece_key] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
    return images

def load_sounds():
    """Ses dosyalarını yükler."""
    pygame.mixer.init()
    sounds = {}
    # Dosya adları: move.wav, capture.wav, notify.wav (şah çekme için)
    for name in ['move', 'capture', 'notify']:
        path = os.path.join("assets", f"{name}.wav")
        if os.path.exists(path):
            sounds[name] = pygame.mixer.Sound(path)
    return sounds

def draw_board(screen):
    """Satranç tahtasının karelerini çizer."""
    for r in range(8):
        for c in range(8):
            color = BOARD_LIGHT if (r + c) % 2 == 0 else BOARD_DARK
            pygame.draw.rect(screen, color, pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_highlights(screen, board, selected_square, player_color):
    """Son hamleyi ve seçili kareyi vurgular."""
    # Son hamle vurgusu (Sarı)
    if len(board.move_stack) > 0:
        move = board.peek()
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)  # Saydamlık (0-255)
        s.fill((255, 255, 0))  # Sarı
        
        for sq in [move.from_square, move.to_square]:
            if player_color == chess.WHITE:
                c = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
            else:
                c = 7 - chess.square_file(sq)
                r = chess.square_rank(sq)
            screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    # Seçili kare vurgusu (Yeşil Çerçeve)
    if selected_square is not None:
        if player_color == chess.WHITE:
            c = chess.square_file(selected_square)
            r = 7 - chess.square_rank(selected_square)
        else:
            c = 7 - chess.square_file(selected_square)
            r = chess.square_rank(selected_square)
        
        rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, (0, 255, 0), rect, 4)

def draw_pieces(screen, board, images, player_color=chess.WHITE):
    """Mevcut pozisyona göre taşları tahtaya çizer."""
    for r in range(8):
        for c in range(8):
            if player_color == chess.WHITE:
                square = chess.square(c, 7 - r) # Beyaz aşağıda (Standart)
            else:
                square = chess.square(7 - c, r) # Siyah aşağıda (Ters)
            
            piece = board.piece_at(square)
            if piece:
                # Piece symbol (örn: 'P', 'r') -> image key (örn: 'wP', 'bR')
                color = 'w' if piece.color == chess.WHITE else 'b'
                piece_key = f"{color}{piece.symbol().upper()}"
                screen.blit(images[piece_key], (c * SQUARE_SIZE, r * SQUARE_SIZE))

def draw_menu(screen):
    """Taraf seçimi için menü çizer."""
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()
    
    while True:
        screen.fill((50, 50, 50))
        
        title = font.render("Taraf Seçin / Choose Side", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        
        # Butonlar
        white_rect = pygame.Rect(WIDTH // 2 - 100, 250, 200, 60)
        black_rect = pygame.Rect(WIDTH // 2 - 100, 350, 200, 60)
        
        pygame.draw.rect(screen, (220, 220, 220), white_rect)
        pygame.draw.rect(screen, (80, 80, 80), black_rect)
        
        w_text = font.render("Beyaz", True, (0, 0, 0))
        b_text = font.render("Siyah", True, (255, 255, 255))
        
        screen.blit(w_text, (white_rect.centerx - w_text.get_width() // 2, white_rect.centery - w_text.get_height() // 2))
        screen.blit(b_text, (black_rect.centerx - b_text.get_width() // 2, black_rect.centery - b_text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if white_rect.collidepoint(event.pos):
                    return chess.WHITE
                if black_rect.collidepoint(event.pos):
                    return chess.BLACK
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
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_rect.collidepoint(event.pos): return 0.1
                if med_rect.collidepoint(event.pos): return 1.0
                if hard_rect.collidepoint(event.pos): return 3.0
        clock.tick(30)

def draw_time_menu(screen):
    """Zaman kontrolü seçimi için menü çizer."""
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()
    
    while True:
        screen.fill((50, 50, 50))
        
        title = font.render("Süre Seçin / Time Control", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        
        # Butonlar
        rects = []
        times = [60, 300, 600, 1800] # Saniye cinsinden
        labels = ["1 Dakika", "5 Dakika", "10 Dakika", "30 Dakika"]
        
        start_y = 180
        for i, label in enumerate(labels):
            rect = pygame.Rect(WIDTH // 2 - 120, start_y + i * 80, 240, 60)
            rects.append(rect)
            
            pygame.draw.rect(screen, (100, 150, 200), rect)
            text = font.render(label, True, (255, 255, 255))
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return float(times[i])
        clock.tick(30)

def draw_move_history(screen, board):
    """Hamle geçmişini sağ panelde listeler."""
    font = pygame.font.SysFont("Arial", 16)
    
    # Hamleleri SAN formatına çevir
    temp_board = chess.Board()
    san_moves = []
    for move in board.move_stack:
        san_moves.append(temp_board.san(move))
        temp_board.push(move)
        
    # Çizim alanı
    start_x = BOARD_WIDTH + 20
    start_y = 100
    line_height = 20
    max_lines = 20  # Ekrana sığacak maksimum satır sayısı
    
    # Liste çok uzunsa son hamleleri göster
    num_moves = (len(san_moves) + 1) // 2
    start_index = max(0, num_moves - max_lines)
        
    for i in range(start_index, num_moves):
        white_idx = i * 2
        black_idx = i * 2 + 1
        
        move_str = f"{i+1}. {san_moves[white_idx]}"
        if black_idx < len(san_moves):
            move_str += f" {san_moves[black_idx]}"
            
        text = font.render(move_str, True, (220, 220, 220))
        screen.blit(text, (start_x, start_y + (i - start_index) * line_height))

def draw_captured_pieces(screen, board, images):
    """Alınan taşları sağ panelde gösterir."""
    # Başlangıç taş sayıları
    initial_counts = {
        chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, 
        chess.ROOK: 2, chess.QUEEN: 1
    }
    
    piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
    
    # Küçük resim boyutu
    small_size = 25
    
    for color in [chess.WHITE, chess.BLACK]:
        captured = []
        for pt in piece_types:
            count = len(board.pieces(pt, color))
            diff = initial_counts[pt] - count
            if diff > 0:
                captured.extend([pt] * diff)
        
        # Çizim pozisyonları
        # Beyaz taşlar (Siyahın aldıkları) -> Siyah panelin altına
        # Siyah taşlar (Beyazın aldıkları) -> Beyaz panelin üstüne
        y_pos = 80 if color == chess.WHITE else HEIGHT - 90
        x_start = BOARD_WIDTH + 20
        
        for i, pt in enumerate(captured):
            # Resim anahtarını bul (örn: 'wP')
            img_key = ('w' if color == chess.WHITE else 'b') + chess.Piece(pt, color).symbol().upper()
            if img_key in images:
                # Resmi küçült
                small_img = pygame.transform.scale(images[img_key], (small_size, small_size))
                # Satır başı yapmadan yan yana çiz
                screen.blit(small_img, (x_start + (i % 8) * small_size, y_pos + (i // 8) * small_size))

def draw_gui(screen, board, white_time, black_time, player_color, piece_images):
    """Bilgi panelini çizer."""
    pygame.draw.rect(screen, (40, 40, 40), (BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, HEIGHT))
    font = pygame.font.SysFont(None, 32)
    
    # Zamanları formatla
    w_min, w_sec = divmod(max(0, int(white_time)), 60)
    b_min, b_sec = divmod(max(0, int(black_time)), 60)
    
    w_str = f"Beyaz: {w_min:02}:{w_sec:02}"
    b_str = f"Siyah: {b_min:02}:{b_sec:02}"
    
    w_color = (255, 255, 255) if board.turn == chess.WHITE else (150, 150, 150)
    b_color = (255, 255, 255) if board.turn == chess.BLACK else (150, 150, 150)
    
    screen.blit(font.render(b_str, True, b_color), (BOARD_WIDTH + 20, 50))
    screen.blit(font.render(w_str, True, w_color), (BOARD_WIDTH + 20, HEIGHT - 50))
    
    turn_text = "Sıra: Beyaz" if board.turn == chess.WHITE else "Sıra: Siyah"
    screen.blit(font.render(turn_text, True, (255, 200, 100)), (BOARD_WIDTH + 20, 15))
    
    draw_move_history(screen, board)
    draw_captured_pieces(screen, board, piece_images)

def play_game_sound(board, move, sounds, is_capture):
    """Hamleye uygun sesi çalar."""
    # Hamle yapıldıktan sonra kontrol edildiği için board.is_check() rakibin şah durumunu verir
    if board.is_check():
        if 'notify' in sounds: sounds['notify'].play()
    elif is_capture:
        if 'capture' in sounds: sounds['capture'].play()
    else:
        if 'move' in sounds: sounds['move'].play()

def draw_game_over(screen, result):
    """Oyun bittiğinde sonucu ekrana yazar."""
    overlay = pygame.Surface((BOARD_WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    font = pygame.font.SysFont(None, 64)
    text = ""
    if result == "1-0":
        text = "Beyaz Kazandı!"
    elif result == "0-1":
        text = "Siyah Kazandı!"
    else:
        text = "Berabere!"
        
    render = font.render(text, True, (255, 255, 255))
    rect = render.get_rect(center=(BOARD_WIDTH // 2, HEIGHT // 2))
    screen.blit(render, rect)
    
    # Yeniden Başlat Butonu
    btn_rect = pygame.Rect(BOARD_WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)
    pygame.draw.rect(screen, (0, 200, 0), btn_rect)
    pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2)
    
    btn_text = font.render("Restart", True, (255, 255, 255))
    screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2, btn_rect.centery - btn_text.get_height() // 2))
    return btn_rect

# --- Ana GUI Fonksiyonu ---

def main_gui():
    global WIDTH, HEIGHT, BOARD_WIDTH, SQUARE_SIZE
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Satranç Analiz Sistemi")

    try:
        piece_images = load_piece_images()
    except FileNotFoundError as e:
        print(e)
        return

    sounds = load_sounds()

    while True: # Oyun Oturumu Döngüsü (Restart için)
        # Taraf seçimi
        player_color = draw_menu(screen)

        # Zorluk seçimi
        difficulty_time = draw_difficulty_menu(screen)

        # Süre seçimi
        selected_time_limit = draw_time_menu(screen)

        board = chess.Board()
        
        # Hamle yapmak için seçilen ilk kareyi saklar
        selected_square = None
        
        # Zamanlayıcılar (Seçilen süre)
        white_time = selected_time_limit
        black_time = selected_time_limit
        last_time = time.time()
        
        running = True
        restart_game = False
        restart_rect = None

        while running:
            # Zaman güncelleme
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if not board.is_game_over():
                if board.turn == chess.WHITE:
                    white_time -= dt
                else:
                    black_time -= dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    exit()
                
                # Pencere Boyutlandırma (Resize) Olayı
                if event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = event.w, event.h
                    
                    # Tahtayı yüksekliğe göre ayarla, ancak sağ panel için en az 200px yer bırak
                    BOARD_WIDTH = HEIGHT
                    if WIDTH - BOARD_WIDTH < 200:
                        BOARD_WIDTH = WIDTH - 200
                    
                    # Yeni boyutları hesapla ve ekranı güncelle
                    SQUARE_SIZE = BOARD_WIDTH // 8
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    piece_images = load_piece_images() # Görselleri yeni boyuta göre tekrar yükle
                
                # Fare tıklaması olayını işle
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Oyun bittiyse Restart kontrolü
                    if board.is_game_over() and restart_rect and restart_rect.collidepoint(event.pos):
                        restart_game = True
                        running = False
                        break

                    if board.turn == player_color and not board.is_game_over():
                        if event.pos[0] >= BOARD_WIDTH:
                            continue

                        col = event.pos[0] // SQUARE_SIZE
                        row = event.pos[1] // SQUARE_SIZE
                        
                        if player_color == chess.WHITE:
                            clicked_square = chess.square(col, 7 - row)
                        else:
                            clicked_square = chess.square(7 - col, row)

                        # Henüz bir kare seçilmediyse, bu tıklamayı başlangıç karesi yap
                        if selected_square is None:
                            # Sadece mevcut oyuncunun taşı olan bir kareyi seç
                            piece = board.piece_at(clicked_square)
                            if piece and piece.color == board.turn:
                                selected_square = clicked_square
                        # Zaten bir kare seçildiyse, bu tıklamayı hedef kare olarak al
                        else:
                            move = chess.Move(selected_square, clicked_square)
                            
                            # Hamlenin geçerli olup olmadığını kontrol et (piyon terfileri dahil)
                            is_promotion = (board.piece_at(selected_square).piece_type == chess.PAWN and 
                                            (chess.square_rank(clicked_square) == 0 or chess.square_rank(clicked_square) == 7))

                            if is_promotion:
                                move.promotion = chess.QUEEN

                            if move in board.legal_moves:
                                print(f"Oyuncu hamlesi: {move.uci()}")
                                is_capture = board.is_capture(move)
                                board.push(move)
                                play_game_sound(board, move, sounds, is_capture)
                                
                                # Ekranı hemen güncelle
                                draw_board(screen)
                                draw_highlights(screen, board, selected_square, player_color)
                                draw_pieces(screen, board, piece_images, player_color)
                                draw_gui(screen, board, white_time, black_time, player_color, piece_images)
                                pygame.display.flip()

                            else:
                                print("Gecersiz hamle.")
                            
                            # Seçimi sıfırla
                            selected_square = None

            if restart_game:
                break

            # Ekranı çiz
            draw_board(screen)
            draw_highlights(screen, board, selected_square, player_color)
            draw_pieces(screen, board, piece_images, player_color)
            draw_gui(screen, board, white_time, black_time, player_color, piece_images)
            
            if board.is_game_over():
                restart_rect = draw_game_over(screen, board.result())
                
            pygame.display.flip()
            
            # AI Hamlesi
            if not board.is_game_over() and board.turn != player_color:
                pygame.event.pump()
                print("AI dusunuyor...")
                
                start_think = time.time()
                ai_move = analyze_position(board, time_limit=difficulty_time)
                end_think = time.time()
                
                # AI süresini düş
                duration = end_think - start_think
                if board.turn == chess.WHITE:
                    white_time -= duration
                else:
                    black_time -= duration
                last_time = time.time() # Zamanı senkronize et
                
                if ai_move:
                    print(f"AI hamlesi: {ai_move.uci()}")
                    is_capture = board.is_capture(ai_move)
                    board.push(ai_move)
                    play_game_sound(board, ai_move, sounds, is_capture)
                else:
                    print("AI hamle yapamadi.")

    pygame.quit()

# --- Analiz Fonksiyonu (Değişiklik yok) ---
def analyze_position(board, time_limit=1.0):
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            result = engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
    except Exception as e:
        print(f"Analiz sırasında hata: {e}")
        return None


if __name__ == "__main__":
    main_gui() # Eski main() yerine yeni GUI fonksiyonunu çağır