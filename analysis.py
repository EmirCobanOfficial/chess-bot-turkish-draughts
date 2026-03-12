# Project: Chess Bot Analysis Script
# Author: Emir ÇOBAN
# License: MIT License
# Description: Command line interface for analyzing chess positions with Stockfish.

import chess
import chess.engine
import os

# Stockfish 'exe' dosyasının bulunduğu tam yolu belirtin.
# Script ile aynı dizinde bir 'stockfish' klasörü oluşturup içine 'stockfish.exe' koyduğunuz varsayılıyor.
STOCKFISH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")
# Önemli Not: Yukarıdaki satırın çalışması için, bu script'in bulunduğu dizinde 'stockfish'
# adında bir klasör ve içinde de 'stockfish.exe' olmalıdır.

def analyze_position(board, time_limit=2.0):
    """
    Verilen pozisyonu analiz eder ve en iyi hamleyi döndürür.
    """
    try:
        # Satranç motorunu başlat
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            # Belirtilen süre kadar analiz yap ve sonucu al
            result = engine.play(board, chess.engine.Limit(time=time_limit))
            best_move = result.move
            return best_move
    except FileNotFoundError:
        print(f"HATA: Stockfish motoru '{STOCKFISH_PATH}' yolunda bulunamadı.")
        print("Lütfen STOCKFISH_PATH değişkenini ve dosya konumunu kontrol edin.")
        return None
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return None

def main():
    """
    Ana oyun döngüsü.
    """
    board = chess.Board()
    print("Satranç Analiz Sistemine Hoş Geldiniz!")
    print("Hamleleri Standart Cebirsel Notasyon (SAN) formatında girin (örn: e4, Nf3, Bb5).")
    print("Çıkmak için 'quit' yazın.")
    print("-" * 30)

    while not board.is_game_over():
        # Tahtanın mevcut durumunu göster
        print("\n" + str(board))
        
        # Sıradaki oyuncuyu belirle
        player = "Beyaz" if board.turn == chess.WHITE else "Siyah"
        
        # Kullanıcıdan hamle al veya analiz yap
        user_input = input(f"Sıra {player}'da. Hamlenizi girin (veya '{player}' için analiz yapmak isterseniz 'analyze' yazın): ")

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'analyze':
            print("Analiz yapılıyor...")
            best_move = analyze_position(board)
            if best_move:
                print(f"Stockfish'e göre en iyi hamle: {board.san(best_move)}")
        else:
            try:
                # Kullanıcının girdiği hamleyi yap
                move = board.push_san(user_input)
                print(f"Yapılan hamle: {board.san(move)}")
            except chess.IllegalMoveError:
                print(f"Hatalı hamle: '{user_input}'. Lütfen geçerli bir hamle girin.")
            except Exception as e:
                print(f"Beklenmedik bir hata: {e}")

    print("\nOyun bitti.")
    print(f"Sonuç: {board.result()}")

if __name__ == "__main__":
    main()