import sys, random, time
import pygame
import asyncio

# Konfigurasi & Warna
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# Resolusi dikurangi untuk performa web yang lebih baik
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Punto - 4 Pemain")

FPS = 60
CLOCK = pygame.time.Clock()

WHITE = (255,255,255)
BLACK = (0,0,0)
GREY = (200,200,200)
DARK = (20,20,28)
GLOW = (80,160,255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
BLUE = (100, 150, 255)
YELLOW = (255, 255, 100)

# Font
pygame.font.init()
FONT_BIG = pygame.font.SysFont("arial", 32, bold=True)  
FONT_MED = pygame.font.SysFont("arial", 24, bold=True) 
FONT_SMALL = pygame.font.SysFont("arial", 18)       

# Level Kesulitan Permainan
EASY = 0
MEDIUM = 1
HARD = 2
DIFFICULTY_NAMES = ["Mudah", "Sedang", "Sulit"]

CLICK_SND = None
DING_SND = None

def _mk_tone(freq=880, ms=120, volume=0.3):
    try:
        import numpy as np
        sr = 44100
        n = int(sr * (ms/1000.0))
        t = np.linspace(0, ms/1000.0, n, False)
        wave = (0.5*np.sign(np.sin(2*np.pi*freq*t)) + 0.5*np.sin(2*np.pi*freq*t*0.5))
        audio = (wave * 32767 * volume).astype(np.int16)
        snd = pygame.sndarray.make_sound(audio)
        return snd
    except Exception:
        return None

try:
    CLICK_SND = _mk_tone(900, 70, 0.35)
    DING_SND = _mk_tone(1200, 200, 0.4)
except:
    CLICK_SND = None
    DING_SND = None

def s_play(snd):
    if snd:
        try: 
            snd.play()
        except: 
            pass

# Layout Papan
GRID_SIZE = 9
CELL_PAD = 2
BOARD_PIX = min(int(WIDTH*0.6), int(HEIGHT*0.75))
CELL_SIZE = BOARD_PIX // GRID_SIZE
BOARD_PIX = CELL_SIZE * GRID_SIZE
offset_x = (WIDTH - BOARD_PIX)//2
offset_y = (HEIGHT - BOARD_PIX)//2 - 10

# Model Permainan (Diperbarui sesuai aturan)
PLAYER_COLORS = [YELLOW, BLUE, GREEN, RED]
PLAYER_NAMES = ["P1 (ANDA)", "P2 (AI)", "P3 (AI)", "P4 (AI)"]
HAND_LIMIT = 3

def create_deck():
    """Buat deck penuh kartu: angka 1-9, dua dari masing-masing"""
    deck = [v for v in range(1, 10) for _ in range(2)]
    random.shuffle(deck)
    return deck

def make_hand():
    """Inisialisasi tangan kosong"""
    return {}

def draw_cards(deck, hand, target_size):
    """Ambil kartu dari deck sampai tangan mencapai target_size atau deck kosong"""
    initial_size = get_hand_size(hand)
    while get_hand_size(hand) < target_size and deck:
        card = deck.pop()
        hand[card] = hand.get(card, 0) + 1
    return get_hand_size(hand) - initial_size

def draw_one(deck, hand):
    """Ambil satu kartu dari deck"""
    if deck:
        card = deck.pop()
        hand[card] = hand.get(card, 0) + 1
        return True
    return False

def get_hand_size(hand):
    """Dapatkan jumlah total kartu di tangan"""
    return sum(hand.values())

def empty_board():
    """Grid 9x9, setiap sel adalah tumpukan dari tuple (player_id, value)"""
    return [[[] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def in_bounds(r, c):
    return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

# 8 tetangga arah
NEI8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def has_any_tile(board):
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c]:
                return True
    return False

def has_filled_neighbor(board, r, c):
    """Periksa apakah sel (r,c) memiliki sel tetangga yang terisi"""
    for dr, dc in NEI8:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc]:
            return True
    return False

def can_place(board, player, val, r, c, first_move_done):
    """Periksa apakah pemain dapat menempatkan kartu dengan nilai 'val' di posisi (r,c)"""
    if not in_bounds(r, c):
        return False, "Di luar papan"
    
    if not first_move_done:
        if (r, c) != (GRID_SIZE//2, GRID_SIZE//2):
            return False, "Gerakan pertama harus di tengah (4,4)"
    else:
        # Harus bersebelahan dengan kartu yang ada ATAU di sel kosong yang dikelilingi
        if not board[r][c]:  # Sel kosong
            if not has_filled_neighbor(board, r, c):
                return False, "Harus ditempatkan bersebelahan dengan kartu yang ada"
    
    stack = board[r][c]
    if not stack:
        return True, ""
    else:
        top_owner, top_val = stack[-1]
        if top_owner == player:
            return False, "Tidak dapat menumpuk kartu sendiri"
        if val <= top_val:
            return False, "Nilai harus lebih tinggi untuk menumpuk"
        return True, ""

def place_card(board, player, val, r, c):
    """Tempatkan kartu di papan"""
    board[r][c].append((player, val))

# Periksa 4 berturut-turut
DIRS = [(0,1), (1,0), (1,1), (1,-1)]

def check_win(board, player):
   # Periksa kondisi menang: 4 kartu berjejeran (horizontal/vertikal/diagonal) milik pemain yang sama
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not board[r][c]:
                continue
            top_owner, _ = board[r][c][-1]
            if top_owner != player:
                continue
            
            # Periksa 4 arah dari posisi ini
            for dr, dc in DIRS:
                count = 1  # Mulai dengan kartu di posisi (r,c)
                
                # Cek ke depan
                rr, cc = r + dr, c + dc
                while in_bounds(rr, cc) and board[rr][cc] and board[rr][cc][-1][0] == player:
                    count += 1
                    rr += dr
                    cc += dc
                
                # Cek ke belakang
                rr, cc = r - dr, c - dc
                while in_bounds(rr, cc) and board[rr][cc] and board[rr][cc][-1][0] == player:
                    count += 1
                    rr -= dr
                    cc -= dc
                
                # Jika ada 4 kartu berjejeran, pemain menang
                if count >= 4:
                    return True
    
    return False


def calculate_tiebreaker_score(board, player):
    # Hitung skor tiebreaker untuk pemain
    max_line_sum = 0
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not board[r][c]:
                continue
            top_owner, start_val = board[r][c][-1]
            if top_owner != player:
                continue
            
            for dr, dc in DIRS:
                # Kumpulkan nilai dalam garis
                line_sum = start_val
                
                # Cek ke depan
                rr, cc = r + dr, c + dc
                while in_bounds(rr, cc) and board[rr][cc] and board[rr][cc][-1][0] == player:
                    line_sum += board[rr][cc][-1][1]
                    rr += dr
                    cc += dc
                
                # Cek ke belakang
                rr, cc = r - dr, c - dc
                while in_bounds(rr, cc) and board[rr][cc] and board[rr][cc][-1][0] == player:
                    line_sum += board[rr][cc][-1][1]
                    rr -= dr
                    cc -= dc
                
                max_line_sum = max(max_line_sum, line_sum)
    
    return max_line_sum

def final_scores(board):
    """Hitung skor akhir berdasarkan tiebreaker"""
    scores = [0, 0, 0, 0]
    for i in range(4):
        scores[i] = calculate_tiebreaker_score(board, i)
    return scores

def hands_empty(all_hands):
    """Periksa apakah semua pemain kehabisan kartu"""
    return all(get_hand_size(h) == 0 for h in all_hands)

def deck_empty(deck):
    """Periksa apakah deck kosong"""
    return len(deck) == 0

def all_decks_empty(all_decks):
    """Periksa apakah semua deck kosong"""
    return all(len(deck) == 0 for deck in all_decks)

# Layar Pemilihan Level (Async)
async def difficulty_selection():
    selected = EASY
    confirmed = False
    
    while not confirmed:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return None
                elif event.key == pygame.K_1:
                    selected = EASY
                    s_play(CLICK_SND)
                elif event.key == pygame.K_2:
                    selected = MEDIUM
                    s_play(CLICK_SND)
                elif event.key == pygame.K_3:
                    selected = HARD
                    s_play(CLICK_SND)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    confirmed = True
                    s_play(DING_SND)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Periksa klik tombol level
                for i in range(3):
                    button_y = HEIGHT//2 - 60 + i * 60 
                    button_rect = pygame.Rect(WIDTH//2 - 150, button_y, 300, 50) 
                    if button_rect.collidepoint(mx, my):
                        selected = i
                        s_play(CLICK_SND)
                
                # cek tombol mulai
                start_rect = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 + 120, 150, 40)
                if start_rect.collidepoint(mx, my):
                    confirmed = True
                    s_play(DING_SND)

        draw_gradient_background()
        
        title = FONT_BIG.render("Pilih Kesulitan", True, WHITE)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
        
        # Tombol Level
        for i in range(3):
            button_y = HEIGHT//2 - 60 + i * 60
            button_rect = pygame.Rect(WIDTH//2 - 150, button_y, 300, 50)
            
            # Warna tombol berdasarkan pilihan
            if i == selected:
                pygame.draw.rect(SCREEN, (100, 150, 255), button_rect, border_radius=8)
                pygame.draw.rect(SCREEN, WHITE, button_rect, 2, border_radius=8)
            else:
                pygame.draw.rect(SCREEN, (50, 60, 80), button_rect, border_radius=8)
                pygame.draw.rect(SCREEN, GREY, button_rect, 1, border_radius=8)
            
            # Nama level
            name = FONT_MED.render(f"{i+1}. {DIFFICULTY_NAMES[i]}", True, WHITE)
            SCREEN.blit(name, (button_rect.x + 10, button_rect.y + 8))
            
            # Deskripsi
            descriptions = [
                "",
                "", 
                ""
            ]
            desc = FONT_SMALL.render(descriptions[i], True, GREY)
            SCREEN.blit(desc, (button_rect.x + 10, button_rect.y + 28))
        
        # Tombol mulai
        start_rect = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 + 120, 150, 40)
        pygame.draw.rect(SCREEN, (100, 200, 100), start_rect, border_radius=6)
        pygame.draw.rect(SCREEN, WHITE, start_rect, 2, border_radius=6)
        start_text = FONT_MED.render("MULAI", True, BLACK)
        SCREEN.blit(start_text, (start_rect.centerx - start_text.get_width()//2, 
                                start_rect.centery - start_text.get_height()//2))
        
        # Instruksi
        inst1 = FONT_SMALL.render("Tekan 1-3 untuk memilih, ENTER/SPACE untuk mulai, atau klik tombol", True, GREY)
        SCREEN.blit(inst1, (WIDTH//2 - inst1.get_width()//2, HEIGHT//2 + 180))
        
        pygame.display.flip()
        await asyncio.sleep(0) 
        CLOCK.tick(FPS)
    
    return selected

# background
    def draw_gradient_background():
    for y in range(0, HEIGHT, 4): 
        t = y / HEIGHT
        r = int(12 + 30*t)
        g = int(15 + 35*t)
        b = int(22 + 40*t)
        pygame.draw.rect(SCREEN, (r,g,b), (0, y, WIDTH, 4))
        

def draw_board(board, active_player, selected_value=None, first_move_done=True):
    # Background belakang papan
    board_rect = pygame.Rect(offset_x-8, offset_y-8, BOARD_PIX+16, BOARD_PIX+16)
    pygame.draw.rect(SCREEN, (40, 45, 60), board_rect, border_radius=8)
    
    # Gambar grid
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = offset_x + c * CELL_SIZE
            y = offset_y + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            
            base_color = (34, 38, 54)
            
            # Sorot gerakan valid
            if active_player == 0 and selected_value is not None:
                can_place_here, _ = can_place(board, 0, selected_value, r, c, first_move_done)
                if can_place_here:
                    base_color = (60, 100, 60)
            
            pygame.draw.rect(SCREEN, base_color, rect)
            pygame.draw.rect(SCREEN, (60, 70, 96), rect, 1)

            # Gambar kartu teratas
            stack = board[r][c]
            if stack:
                owner, val = stack[-1]
                card_rect = rect.inflate(-CELL_PAD*2, -CELL_PAD*2)
                
                card_color = PLAYER_COLORS[owner]
                pygame.draw.rect(SCREEN, card_color, card_rect, border_radius=3)
                pygame.draw.rect(SCREEN, BLACK, card_rect, 2, border_radius=3)
                
                text = FONT_SMALL.render(str(val), True, BLACK)
                tx = x + CELL_SIZE//2 - text.get_width()//2
                ty = y + CELL_SIZE//2 - text.get_height()//2
                SCREEN.blit(text, (tx, ty))
                
                if len(stack) > 1:
                    stack_text = FONT_SMALL.render(f"({len(stack)})", True, BLACK)
                    SCREEN.blit(stack_text, (x + 1, y + 1))

    # Sorot tengah untuk gerakan pertama
    if not first_move_done:
        center_rect = pygame.Rect(offset_x + (GRID_SIZE//2)*CELL_SIZE,
                                  offset_y + (GRID_SIZE//2)*CELL_SIZE,
                                  CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(SCREEN, (255,255,0), center_rect, 2)

    # Border pemain aktif
    border_rect = pygame.Rect(offset_x-3, offset_y-3, BOARD_PIX+6, BOARD_PIX+6)
    color = PLAYER_COLORS[active_player]
    pygame.draw.rect(SCREEN, color, border_rect, 3, border_radius=6)

def draw_hands(hands, decks, active_player, status_text, selected_value, difficulty):
    panel_h = 180
    panel_rect = pygame.Rect(0, HEIGHT - panel_h, WIDTH, panel_h)
    
    # Latar belakang
    pygame.draw.rect(SCREEN, (0,0,0,180), panel_rect)

    # Teks status
    deck_counts = [len(deck) for deck in decks]
    color_names = {
        tuple(YELLOW): "Kuning",
        tuple(BLUE): "Biru", 
        tuple(GREEN): "Hijau",
        tuple(RED): "Merah"
    }
    
    current_color = PLAYER_COLORS[active_player]
    color_text = color_names.get(tuple(current_color), "Tidak Dikenal")

    status = FONT_MED.render(f"Giliran: {PLAYER_NAMES[active_player]} | Warna: {color_text} | Deck: {deck_counts[0]} | {DIFFICULTY_NAMES[difficulty]} ", 
                       True, PLAYER_COLORS[active_player])
    SCREEN.blit(status, (20, HEIGHT - panel_h + 10))
    
    if status_text:
        status2 = FONT_SMALL.render(status_text, True, WHITE)
        SCREEN.blit(status2, (20, HEIGHT - panel_h + 40))

    human_hand = hands[0]
    label = FONT_MED.render(f"Kartu Anda ({get_hand_size(human_hand)}/{HAND_LIMIT}):", True, WHITE)
    SCREEN.blit(label, (20, HEIGHT - panel_h + 70))
    
    x0 = 20
    card_idx = 0
    for val in sorted(human_hand.keys()):
        count = human_hand[val]
        for _ in range(count):
            box = pygame.Rect(x0 + card_idx*60, HEIGHT - panel_h + 100, 50, 50)  # Kartu lebih kecil
            
            if val == selected_value:
                pygame.draw.rect(SCREEN, YELLOW, box, border_radius=8)
                pygame.draw.rect(SCREEN, BLACK, box, 3, border_radius=8)
            else:
                pygame.draw.rect(SCREEN, (100, 120, 150), box, border_radius=8)
                pygame.draw.rect(SCREEN, WHITE, box, 2, border_radius=8)
            
            text_color = BLACK if val == selected_value else WHITE
            text = FONT_MED.render(str(val), True, text_color)
            SCREEN.blit(text, (box.centerx - text.get_width()//2, box.y + 5))
            
            key_text = FONT_SMALL.render(f"[{card_idx+1}]", True, text_color)
            SCREEN.blit(key_text, (box.centerx - key_text.get_width()//2, box.bottom - 18))
            
            card_idx += 1

    # Ringkasan tangan AI
    for pid in range(1, 4):
        hand_size = get_hand_size(hands[pid])
        deck_size = len(decks[pid])
        color = PLAYER_COLORS[pid] if pid == active_player else GREY
        text = FONT_SMALL.render(f"{PLAYER_NAMES[pid]}: {hand_size} kartu, deck: {deck_size}", True, color)
        SCREEN.blit(text, (WIDTH - 250, HEIGHT - panel_h + 20 + (pid-1)*25))

def draw_key_hints():
    hints = FONT_SMALL.render("[R] Ulang Permainan", True, GREY)
    SCREEN.blit(hints, (WIDTH - hints.get_width() - 10, 10))
    
    restart_button = pygame.Rect(WIDTH - 200, 40, 190, 35)
    pygame.draw.rect(SCREEN, (200, 80, 80), restart_button, border_radius=8)
    pygame.draw.rect(SCREEN, WHITE, restart_button, 2, border_radius=8)
    restart_text = FONT_SMALL.render("ULANG PERMAINAN", True, WHITE)
    SCREEN.blit(restart_text, (restart_button.centerx - restart_text.get_width()//2,
                              restart_button.centery - restart_text.get_height()//2))

def draw_winner_popup(winner_name, scores):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    SCREEN.blit(overlay, (0,0))

    box = pygame.Rect(0, 0, 500, 300)  # Popup lebih kecil
    box.center = (WIDTH//2, HEIGHT//2)
    pygame.draw.rect(SCREEN, (28, 36, 48), box, border_radius=15)
    pygame.draw.rect(SCREEN, (90, 110, 160), box, 3, border_radius=15)

    title = FONT_BIG.render("Permainan Selesai", True, WHITE)
    SCREEN.blit(title, (box.centerx - title.get_width()//2, box.y + 30))

    winner = FONT_MED.render(f"Pemenang: {winner_name}", True, (255, 235, 175))
    SCREEN.blit(winner, (box.centerx - winner.get_width()//2, box.y + 80))

    # Tombol restart
    restart_btn = pygame.Rect(box.centerx - 100, box.bottom - 80, 200, 40)
    pygame.draw.rect(SCREEN, (100, 200, 100), restart_btn, border_radius=8)
    pygame.draw.rect(SCREEN, WHITE, restart_btn, 2, border_radius=8)
    
    restart_text = FONT_MED.render("MAIN LAGI", True, BLACK)
    SCREEN.blit(restart_text, (restart_btn.centerx - restart_text.get_width()//2,
                              restart_btn.centery - restart_text.get_height()//2))

    hint = FONT_SMALL.render("Tekan [R] atau klik tombol untuk Ulang", True, GREY)
    SCREEN.blit(hint, (box.centerx - hint.get_width()//2, box.bottom - 40))

def check_restart_button_click(mx, my):
    box = pygame.Rect(0, 0, 500, 300)
    box.center = (WIDTH//2, HEIGHT//2)
    restart_btn = pygame.Rect(box.centerx - 100, box.bottom - 80, 200, 40)
    return restart_btn.collidepoint(mx, my)

def board_cell_from_mouse(mx, my):
    """Konversi koordinat mouse ke sel papan"""
    if (mx < offset_x or my < offset_y or 
        mx >= offset_x + BOARD_PIX or my >= offset_y + BOARD_PIX):
        return None
    
    cx = (mx - offset_x) // CELL_SIZE
    cy = (my - offset_y) // CELL_SIZE
    
    if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
        return cy, cx
    return None

def hand_card_from_mouse(mx, my, hand):
    """Periksa apakah mouse mengklik kartu tangan"""
    panel_h = 180
    if my < HEIGHT - panel_h + 100 or my > HEIGHT - panel_h + 150:
        return None
    
    x0 = 20
    card_idx = 0
    for val in sorted(hand.keys()):
        count = hand[val]
        for _ in range(count):
            box_x = x0 + card_idx*60
            if box_x <= mx <= box_x + 50:
                return val
            card_idx += 1
    return None

# Logika AI
def potential_cells(board, first_move_done):
    """Dapatkan semua sel valid tempat kartu dapat ditempatkan"""
    if not first_move_done:
        return [(GRID_SIZE//2, GRID_SIZE//2)]
    
    cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not board[r][c]:  # Sel kosong
                if has_filled_neighbor(board, r, c):
                    cells.append((r, c))
            else:  # Sel yang sudah terisi (untuk menumpuk)
                cells.append((r, c))
    return list(set(cells))

def get_line_cells(x, y, direction, length=4):
    """Dapatkan sel-sel dalam garis dari posisi (x,y) dengan arah tertentu"""
    cells = []
    dx, dy = direction
    
    # Mulai dari posisi awal dan extend ke kedua arah
    for i in range(-length+1, length):
        nx, ny = x + i*dx, y + i*dy
        if in_bounds(nx, ny):
            cells.append((nx, ny))
    return cells

def check_consecutive_sequence_in_line(board, player, line_cells):
    """Periksa apakah ada 4 kartu berturut-turut dari pemain yang sama dalam garis"""
    consecutive_count = 0
    max_consecutive = 0
    
    for x, y in line_cells:
        if board[x][y] and board[x][y][-1][0] == player:
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 0
    
    return 1 if max_consecutive >= 4 else 0

def count_potential_sequences(board, player, line_cells):
    """Hitung potensi sequence (3 kartu berturut-turut dari pemain yang sama)"""
    consecutive_count = 0
    max_consecutive = 0
    
    for x, y in line_cells:
        if board[x][y] and board[x][y][-1][0] == player:
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 0
    
    return 1 if max_consecutive >= 3 else 0

def heuristic_function(board, player, x, y, z):
    """
    Fungsi heuristik berdasarkan spesifikasi yang diberikan
    h(p, x, y, z) = 20000f1 + 5000f2 + 1000f3 + 500f4 + 750f5 + 150f6 + 75f7
    """
    # Simulasi penempatan kartu
    temp_board = [row[:] for row in board]
    temp_board[x][y] = temp_board[x][y] + [(player, z)]
    
    # Definisi arah: horizontal, vertikal, diagonal
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    # Dapatkan garis yang melalui (x, y)
    lines_through_xy = []
    for direction in directions:
        line_cells = get_line_cells(x, y, direction)
        lines_through_xy.append((direction, line_cells))
    
    # f1: Reward winning move (4 consecutive cards from same player)
    f1 = 0
    for _, line_cells in lines_through_xy:
        sequences = check_consecutive_sequence_in_line(temp_board, player, line_cells)
        f1 += sequences
    f1 = f1 / 5  # Normalisasi sesuai rumus
    
    # f2: Prevent opponent from winning
    f2 = 0
    for opponent in range(4):
        if opponent == player:
            continue
        for _, line_cells in lines_through_xy:
            sequences = check_consecutive_sequence_in_line(temp_board, opponent, line_cells)
            f2 += sequences
    
    # f3: Reward near completion (3 consecutive cards from same player)
    f3 = 0
    for _, line_cells in lines_through_xy:
        potential = count_potential_sequences(temp_board, player, line_cells)
        f3 += potential
    
    # f4: Sum of consecutive sequences length
    f4 = 0
    for _, line_cells in lines_through_xy:
        # Hitung jumlah kartu pemain dalam garis
        consecutive_count = 0
        for px, py in line_cells:
            if temp_board[px][py] and temp_board[px][py][-1][0] == player:
                consecutive_count += 1
            else:
                if consecutive_count > 0:
                    f4 += consecutive_count
                consecutive_count = 0
        if consecutive_count > 0:
            f4 += consecutive_count
    
    # f5: Prevent opponent from forming 3-cell lines
    f5 = 0
    for opponent in range(4):
        if opponent == player:
            continue
        for _, line_cells in lines_through_xy:
            pre_potential = count_potential_sequences(board, opponent, line_cells)
            post_potential = count_potential_sequences(temp_board, opponent, line_cells)
            if pre_potential >= 1 and post_potential < 1:
                f5 += 1
    
    # f6: Card value + adjacent own cells sum
    f6 = z
    for dx, dy in directions:
        adjacent_sum = 0
        for i in range(1, 4):  # Up to 3 adjacent cells
            nx, ny = x + i*dx, y + i*dy
            if in_bounds(nx, ny) and temp_board[nx][ny]:
                if temp_board[nx][ny][-1][0] == player:
                    adjacent_sum += temp_board[nx][ny][-1][1]
                else:
                    break
            else:
                break
        f6 += adjacent_sum
    
    # f7: Position preference (central vs edge)
    center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
    distance_to_center = abs(x - center_x) + abs(y - center_y)
    
    if distance_to_center <= 2:
        f7 = 1.0
    elif 3 <= distance_to_center <= 5:
        f7 = 0.5
    elif x == 0 or x == GRID_SIZE-1 or y == 0 or y == GRID_SIZE-1:
        f7 = -0.5
    else:
        f7 = 0
    
    # Hitung heuristik final
    h = 20000*f1 + 5000*f2 + 1000*f3 + 500*f4 + 750*f5 + 150*f6 + 75*f7
    
    return h

def ai_choose_move(board, hands, player, first_move_done, difficulty):
    """Pilih gerakan AI berdasarkan level kesulitan dengan heuristik yang ditingkatkan"""
    candidates = potential_cells(board, first_move_done)
    if not candidates:
        return None
    
    available_vals = []
    for v in sorted(hands[player].keys(), reverse=True):
        if hands[player][v] > 0:
            available_vals.append(v)
    
    if not available_vals:
        return None
    
    # Periksa gerakan menang terlebih dahulu (prioritas tertinggi)
    for r, c in candidates:
        for v in available_vals:
            ok, _ = can_place(board, player, v, r, c, first_move_done)
            if ok:
                temp_board = [row[:] for row in board]
                temp_board[r][c] = temp_board[r][c] + [(player, v)]
                if check_win(temp_board, player):
                    return (r, c, v)
    
    # Periksa gerakan untuk memblokir lawan menang
    for r, c in candidates:
        for v in available_vals:
            ok, _ = can_place(board, player, v, r, c, first_move_done)
            if ok:
                temp_board = [row[:] for row in board]
                temp_board[r][c] = temp_board[r][c] + [(player, v)]
                
                # Periksa apakah ada lawan yang bisa menang jika tidak diblokir
                for opponent in range(4):
                    if opponent == player:
                        continue
                    if check_win(board, opponent):
                        return (r, c, v)  # Blokir gerakan menang lawan
    
    # Strategi berdasarkan kesulitan
    if difficulty == EASY:
        # Gerakan acak yang valid
        valid_moves = []
        for r, c in candidates:
            for v in available_vals:
                ok, _ = can_place(board, player, v, r, c, first_move_done)
                if ok:
                    valid_moves.append((r, c, v))
        
        if valid_moves:
            return random.choice(valid_moves)
    
    elif difficulty == MEDIUM:
        # Gunakan heuristik dengan bobot yang dikurangi
        best_move = None
        best_score = -float('inf')
        
        for r, c in candidates:
            for v in available_vals:
                ok, _ = can_place(board, player, v, r, c, first_move_done)
                if ok:
                    score = heuristic_function(board, player, r, c, v) * 0.5
                    score += random.uniform(-100, 100)  # Tambahkan randomness
                    
                    if score > best_score:
                        best_score = score
                        best_move = (r, c, v)
        
        return best_move
    
    elif difficulty == HARD:
        # Gunakan heuristik penuh
        best_move = None
        best_score = -float('inf')
        
        for r, c in candidates:
            for v in available_vals:
                ok, _ = can_place(board, player, v, r, c, first_move_done)
                if ok:
                    score = heuristic_function(board, player, r, c, v)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (r, c, v)
        
        return best_move
    
    # Fallback: gerakan valid pertama yang ditemukan
    for r, c in candidates:
        for v in available_vals:
            ok, _ = can_place(board, player, v, r, c, first_move_done)
            if ok:
                return (r, c, v)
    
    return None

# Animasi Roulette (Async)
    async def roulette_animation():
    """Animasi roulette async"""
    t_end = time.time() + 2.0  
    idx = 0
    names = ["Pemain 1...", "Pemain 2...", "Pemain 3...", "Pemain 4..."]
    last_tick = 0

    while time.time() < t_end:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        draw_gradient_background()

        title = FONT_BIG.render("Menentukan Urutan Giliran...", True, WHITE)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))

        box = pygame.Rect(0, 0, 300, 80)
        box.center = (WIDTH//2, HEIGHT//2)
        pygame.draw.rect(SCREEN, (28, 36, 48), box, border_radius=15)
        pygame.draw.rect(SCREEN, (90, 110, 160), box, 3, border_radius=15)

        text = FONT_MED.render(names[idx % 4], True, (240, 240, 240))
        SCREEN.blit(text, (box.centerx - text.get_width()//2, 
                          box.centery - text.get_height()//2))

        if time.time() - last_tick > 0.3:
            s_play(CLICK_SND)
            idx += 1
            last_tick = time.time()

        pygame.display.flip()
        await asyncio.sleep(0)
        CLOCK.tick(FPS)

    s_play(DING_SND)
    return [0, 1, 2, 3]

# Status Permainan (Diperbarui)
    class GameState:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.reset_all()

    def reset_all(self):
        self.board = empty_board()
        # s0: Setiap pemain memiliki deck 18 kartu (2 dari setiap angka 1-9)
        self.decks = [create_deck() for _ in range(4)]
        self.hands = [make_hand() for _ in range(4)]
        
        # Bagikan kartu awal: setiap pemain mengambil 3 kartu
        for player in range(4):
            draw_cards(self.decks[player], self.hands[player], HAND_LIMIT)
        
        self.turn_order = [0, 1, 2, 3]
        self.active_idx = 0
        self.active_player = 0
        # s1: Gerakan pertama harus di tengah
        self.first_move_done = False
        self.selected_value = None
        self.status_text = "Pilih kartu (klik atau tekan 1-3), lalu klik sel target."
        self.game_over = False
        self.winner = None
        self.scores = [0, 0, 0, 0]
        self.next_ai_time = None

    def next_turn(self):
        """s6: Beralih pemain dan isi ulang tangan"""
        self.active_idx = (self.active_idx + 1) % 4
        self.active_player = self.turn_order[self.active_idx]
        # Isi ulang tangan pemain aktif jika kurang dari batas
        current_hand_size = get_hand_size(self.hands[self.active_player])
        if current_hand_size < HAND_LIMIT and self.decks[self.active_player]:
            draw_cards(self.decks[self.active_player], self.hands[self.active_player], HAND_LIMIT)
    
    def check_end_game(self):
        """s5 & s7: Periksa kondisi akhir permainan"""
        # Periksa kondisi menang
        if check_win(self.board, self.active_player):
            self.game_over = True
            self.winner = self.active_player
            self.scores = final_scores(self.board)
            self.status_text = f"{PLAYER_NAMES[self.active_player]} menang!"
            return True
        
        # Periksa apakah semua tangan dan deck kosong
        all_hands_empty = hands_empty(self.hands)
        all_decks_empty_check = all_decks_empty(self.decks)
        
        if all_hands_empty and all_decks_empty_check:
            self.game_over = True
            self.scores = final_scores(self.board)
            # Pemenang berdasarkan skor tiebreaker tertinggi
            self.winner = max(range(4), key=lambda p: self.scores[p])
            self.status_text = "Permainan selesai! Pemenang berdasarkan skor tertinggi."
            return True
        
        return False

    def human_can_act(self):
        return self.active_player == 0 and not self.game_over

    def ai_can_act(self):
        return self.active_player != 0 and not self.game_over

# Aksi Permainan (Logika sama, disederhanakan)
    def human_try_place(gs, cell_rc):
    """s2, s3, s4: Coba tempatkan kartu manusia"""
    if gs.game_over or not gs.human_can_act():
        return
    if cell_rc is None:
        gs.status_text = "Klik pada sel papan yang valid."
        return
    
    r, c = cell_rc
    v = gs.selected_value
    
    if v is None:
        gs.status_text = "Pilih kartu terlebih dahulu."
        return
    
    if v not in gs.hands[0] or gs.hands[0][v] <= 0:
        gs.status_text = f"Kartu {v} tidak tersedia."
        return

    # s3: Validasi gerakan
    ok, msg = can_place(gs.board, 0, v, r, c, gs.first_move_done)
    if not ok:
        gs.status_text = msg
        return

    # s4: Tempatkan kartu
    place_card(gs.board, 0, v, r, c)
    gs.hands[0][v] -= 1
    if gs.hands[0][v] == 0:
        del gs.hands[0][v]
    
    # TAMBAHAN: Langsung ambil 1 kartu setelah memainkan kartu agar tangan selalu 3
    if gs.decks[0]:
        draw_one(gs.decks[0], gs.hands[0])
    
    gs.first_move_done = True
    gs.selected_value = None

    # s5: Periksa kondisi menang
    if gs.check_end_game():
        s_play(DING_SND)
        return

    gs.status_text = "AI berpikir..."
    gs.next_turn()
    if gs.ai_can_act():
        gs.next_ai_time = time.time() + 0.5

def ai_act(gs):
    """s2, s3, s4, s5: Aksi AI"""
    if not gs.ai_can_act():
        return
    
    now = time.time()
    if gs.next_ai_time is None:
        gs.next_ai_time = now + 0.5
        return
    if now < gs.next_ai_time:
        return

    pid = gs.active_player
    
    if get_hand_size(gs.hands[pid]) == 0:
        gs.next_turn()
        return
    
    move = ai_choose_move(gs.board, gs.hands, pid, gs.first_move_done, gs.difficulty)
    
    if move:
        r, c, v = move
        if v in gs.hands[pid] and gs.hands[pid][v] > 0:
            ok, _ = can_place(gs.board, pid, v, r, c, gs.first_move_done)
            if ok:
                # s4: Tempatkan kartu
                place_card(gs.board, pid, v, r, c)
                gs.hands[pid][v] -= 1
                if gs.hands[pid][v] == 0:
                    del gs.hands[pid][v]
                
                # TAMBAHAN: Langsung isi ulang tangan AI setelah memainkan kartu
                current_hand_size = get_hand_size(gs.hands[pid])
                if current_hand_size < HAND_LIMIT and gs.decks[pid]:
                    draw_cards(gs.decks[pid], gs.hands[pid], HAND_LIMIT - current_hand_size)
                
                gs.first_move_done = True

                # s5: Periksa kondisi menang
                if gs.check_end_game():
                    s_play(DING_SND)
                    return

                gs.status_text = f"{PLAYER_NAMES[pid]} memainkan {v}."
                gs.next_turn()
                if gs.ai_can_act():
                    gs.next_ai_time = time.time() + 0.5
                else:
                    gs.status_text = "Giliran Anda!"
                return

    gs.next_turn()

# def human_try_place(gs, cell_rc):
#     """s2, s3, s4: Coba tempatkan kartu manusia"""
#     if gs.game_over or not gs.human_can_act():
#         return
#     if cell_rc is None:
#         gs.status_text = "Klik pada sel papan yang valid."
#         return
    
#     r, c = cell_rc
#     v = gs.selected_value
    
#     if v is None:
#         gs.status_text = "Pilih kartu terlebih dahulu."
#         return
    
#     if v not in gs.hands[0] or gs.hands[0][v] <= 0:
#         gs.status_text = f"Kartu {v} tidak tersedia."
#         return

    # s3: Validasi gerakan
    ok, msg = can_place(gs.board, 0, v, r, c, gs.first_move_done)
    if not ok:
        gs.status_text = msg
        return

    # s4: Tempatkan kartu
    place_card(gs.board, 0, v, r, c)
    gs.hands[0][v] -= 1
    if gs.hands[0][v] == 0:
        del gs.hands[0][v]
    gs.first_move_done = True
    gs.selected_value = None

    # s5: Periksa kondisi menang
    if gs.check_end_game():
        s_play(DING_SND)
        return

    gs.status_text = "AI berpikir..."
    gs.next_turn()
    if gs.ai_can_act():
        gs.next_ai_time = time.time() + 0.5

def human_select_card(gs, card_index):
    if gs.game_over or not gs.human_can_act():
        return
    
    hand_values = sorted(gs.hands[0].keys())
    card_positions = []
    for val in hand_values:
        count = gs.hands[0][val]
        for _ in range(count):
            card_positions.append(val)
    
    if 1 <= card_index <= len(card_positions):
        selected_val = card_positions[card_index - 1]
        gs.selected_value = selected_val
        gs.status_text = f"Kartu {selected_val} dipilih. Klik papan untuk menempatkan."
        s_play(CLICK_SND)

def human_select_card_by_value(gs, card_value):
    if gs.game_over or not gs.human_can_act():
        return
    
    if card_value in gs.hands[0] and gs.hands[0][card_value] > 0:
        gs.selected_value = card_value
        gs.status_text = f"Kartu {card_value} dipilih. Klik papan untuk menempatkan."
        s_play(CLICK_SND)

# def ai_act(gs):
#     """s2, s3, s4, s5: Aksi AI"""
#     if not gs.ai_can_act():
#         return
    
#     now = time.time()
#     if gs.next_ai_time is None:
#         gs.next_ai_time = now + 0.5
#         return
#     if now < gs.next_ai_time:
#         return

#     pid = gs.active_player
    
#     if get_hand_size(gs.hands[pid]) == 0:
#         gs.next_turn()
#         return
    
#     move = ai_choose_move(gs.board, gs.hands, pid, gs.first_move_done, gs.difficulty)
    
#     if move:
#         r, c, v = move
#         if v in gs.hands[pid] and gs.hands[pid][v] > 0:
#             ok, _ = can_place(gs.board, pid, v, r, c, gs.first_move_done)
#             if ok:
#                 # s4: Tempatkan kartu
#                 place_card(gs.board, pid, v, r, c)
#                 gs.hands[pid][v] -= 1
#                 if gs.hands[pid][v] == 0:
#                     del gs.hands[pid][v]
#                 gs.first_move_done = True

#                 # s5: Periksa kondisi menang
#                 if gs.check_end_game():
#                     s_play(DING_SND)
#                     return

#                 gs.status_text = f"{PLAYER_NAMES[pid]} memainkan {v}."
#                 gs.next_turn()
#                 if gs.ai_can_act():
#                     gs.next_ai_time = time.time() + 0.5
#                 else:
#                     gs.status_text = "Giliran Anda!"
#                 return

#     gs.next_turn()

def draw_everything(gs):
    """Gambar seluruh status permainan"""
    draw_gradient_background()
    
    # Tambahkan title di bagian atas
    title_text = FONT_MED.render("Tugas Kecerdasan Komputasional", True, WHITE)
    title_x = WIDTH // 2 - title_text.get_width() // 2
    SCREEN.blit(title_text, (title_x, 10))
    
    subtitle_text = FONT_SMALL.render("By: Samuel Ivan Gunadi, Kristoforus Iubileagung Hanang Pradipta, Event Valentina Manik", True, GREY)
    subtitle_x = WIDTH // 2 - subtitle_text.get_width() // 2
    SCREEN.blit(subtitle_text, (subtitle_x, 40))
    
    draw_board(gs.board, gs.active_player, gs.selected_value, gs.first_move_done)
    draw_hands(gs.hands, gs.decks, gs.active_player, gs.status_text, gs.selected_value, gs.difficulty)
    draw_key_hints()

    if gs.game_over:
        winner_name = "Seri"
        if gs.winner is not None:
            winner_name = PLAYER_NAMES[gs.winner]
        draw_winner_popup(winner_name, gs.scores)

    async def main():
    """Loop permainan async utama"""
    # Tampilkan pemilihan level
    difficulty = await difficulty_selection()
    if difficulty is None:
        return
    
    # Tampilkan animasi roulettex
    turn_order = await roulette_animation()
    if turn_order is None:
        return
    
    gs = GameState(difficulty)
    running = True

    while running:
        # Tangani event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    # Restart
                    difficulty = await difficulty_selection()
                    if difficulty is None:
                        running = False
                        continue
                    gs = GameState(difficulty)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Periksa klik tombol restart di popup
                if gs.game_over and check_restart_button_click(mx, my):
                    difficulty = await difficulty_selection()
                    if difficulty is None:
                        running = False
                        continue
                    gs = GameState(difficulty)
                    continue
                
                # Periksa klik kartu tangan
                if gs.human_can_act() and not gs.game_over:
                    card_clicked = hand_card_from_mouse(mx, my, gs.hands[0])
                    if card_clicked:
                        human_select_card_by_value(gs, card_clicked)
                        continue
                
                # Periksa klik tombol restart di game (bukan popup)
                restart_button = pygame.Rect(WIDTH - 100, 40, 80, 30)
                if restart_button.collidepoint(mx, my):
                    difficulty = await difficulty_selection()
                    if difficulty is None:
                        running = False
                        continue
                    gs = GameState(difficulty)
                    continue
                
                # Periksa klik papan
                if gs.human_can_act() and not gs.game_over:
                    cell = board_cell_from_mouse(mx, my)
                    if cell:
                        human_try_place(gs, cell)

        # Giliran AI
        if gs.ai_can_act() and not gs.game_over:
            ai_act(gs)

        # Render
        draw_everything(gs)
        pygame.display.flip()
        
        # Serahkan kontrol ke browser
        await asyncio.sleep(0)
        CLOCK.tick(FPS)

    pygame.quit()

# Entry point untuk pygbag
if __name__ == "__main__":
    asyncio.run(main())
