# CaturJawa_Final.py - Enhanced Version with Harder AI
# 4-player card stacking game with improved rules and challenging AI
import sys, random, time
import pygame

# ---------------------------------------
# Configuration & Colors
# ---------------------------------------
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

WIDTH, HEIGHT = 1920, 1080
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Catur Jawa - 4 Players")

FPS = 60
CLOCK = pygame.time.Clock()

# Colors - Made more vibrant and distinct
WHITE = (255,255,255)
BLACK = (0,0,0)
GREY = (200,200,200)
DARK = (20,20,28)
GLOW = (80,160,255)
RED = (255, 100, 100)      # Brighter red
GREEN = (100, 255, 100)    # Brighter green  
BLUE = (100, 150, 255)     # Brighter blue
YELLOW = (255, 255, 100)   # Brighter yellow

# Fonts
pygame.font.init()
FONT_BIG = pygame.font.SysFont("arial", 42, bold=True)
FONT_MED = pygame.font.SysFont("arial", 28, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 22)

# Game Difficulty Levels
EASY = 0
MEDIUM = 1
HARD = 2
DIFFICULTY_NAMES = ["Easy", "Medium", "Hard"]

# ---------------------------------------
# Synthetic Audio
# ---------------------------------------
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

CLICK_SND = _mk_tone(900, 70, 0.35)
DING_SND = _mk_tone(1200, 200, 0.4)

def s_play(snd):
    if snd:
        try: snd.play()
        except: pass

# ---------------------------------------
# Difficulty Selection Screen
# ---------------------------------------
def difficulty_selection():
    """Show difficulty selection screen and return chosen difficulty"""
    selected = EASY
    confirmed = False
    
    while not confirmed:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
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
                # Check difficulty button clicks
                for i in range(3):
                    button_y = HEIGHT//2 - 60 + i * 80
                    button_rect = pygame.Rect(WIDTH//2 - 200, button_y, 400, 60)
                    if button_rect.collidepoint(mx, my):
                        selected = i
                        s_play(CLICK_SND)
                
                # Check start button
                start_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 180, 200, 50)
                if start_rect.collidepoint(mx, my):
                    confirmed = True
                    s_play(DING_SND)

        # Draw difficulty selection screen
        draw_gradient_background()
        
        # Title
        title = FONT_BIG.render("Select Difficulty", True, WHITE)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 200))
        
        # Difficulty buttons
        for i in range(3):
            button_y = HEIGHT//2 - 60 + i * 80
            button_rect = pygame.Rect(WIDTH//2 - 200, button_y, 400, 60)
            
            # Button color based on selection
            if i == selected:
                pygame.draw.rect(SCREEN, (100, 150, 255), button_rect, border_radius=10)
                pygame.draw.rect(SCREEN, WHITE, button_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(SCREEN, (50, 60, 80), button_rect, border_radius=10)
                pygame.draw.rect(SCREEN, GREY, button_rect, 2, border_radius=10)
            
            # Difficulty name and description
            name = FONT_MED.render(f"{i+1}. {DIFFICULTY_NAMES[i]}", True, WHITE)
            SCREEN.blit(name, (button_rect.x + 20, button_rect.y + 8))
            
            # Description
            descriptions = [
                "AI plays randomly (beginner friendly)",
                "AI focuses on strategic positioning", 
                "AI uses advanced tactics and blocking"
            ]
            desc = FONT_SMALL.render(descriptions[i], True, GREY)
            SCREEN.blit(desc, (button_rect.x + 20, button_rect.y + 35))
        
        # Start button
        start_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 180, 200, 50)
        pygame.draw.rect(SCREEN, (100, 200, 100), start_rect, border_radius=8)
        pygame.draw.rect(SCREEN, WHITE, start_rect, 2, border_radius=8)
        start_text = FONT_MED.render("START", True, BLACK)
        SCREEN.blit(start_text, (start_rect.centerx - start_text.get_width()//2, 
                                start_rect.centery - start_text.get_height()//2))
        
        # Instructions
        inst1 = FONT_SMALL.render("Press 1-3 to select, ENTER/SPACE to start, or click buttons", True, GREY)
        SCREEN.blit(inst1, (WIDTH//2 - inst1.get_width()//2, HEIGHT//2 + 270))
        
        inst2 = FONT_SMALL.render("[Q] Quit", True, GREY)
        SCREEN.blit(inst2, (WIDTH - inst2.get_width() - 28, 24))
        
        pygame.display.flip()
        CLOCK.tick(FPS)
    
    return selected

# ---------------------------------------
# Board Layout
# ---------------------------------------
GRID_SIZE = 9
CELL_PAD = 3
BOARD_PIX = min(int(WIDTH*0.7), int(HEIGHT*0.85))
CELL_SIZE = BOARD_PIX // GRID_SIZE
BOARD_PIX = CELL_SIZE * GRID_SIZE
offset_x = (WIDTH - BOARD_PIX)//2
offset_y = (HEIGHT - BOARD_PIX)//2 - 20

# ---------------------------------------
# Game Model (Updated for Hand Limit)
# ---------------------------------------
PLAYER_COLORS = [YELLOW, BLUE, GREEN, RED]
PLAYER_NAMES = ["P1 (Human)", "P2 (AI)", "P3 (AI)", "P4 (AI)"]
HAND_LIMIT = 3  # Maximum cards in hand

def create_deck():
    import random
    """Create a full deck of cards: numbers 1-9, two of each"""
    # 1..9, masing-masing 2 lembar = 18 kartu
    deck = [v for v in range(1, 10) for _ in range(2)]
    random.shuffle(deck)
    return deck

# def shuffle_deck():
#     """Create and shuffle a deck"""
#     deck = create_deck()
#     return deck

def make_hand():
    """Initialize empty hand"""
    return {}

def draw_cards(deck, hand, num_cards):
    """Draw cards from deck to hand until hand has num_cards or deck is empty"""
    num_cards = 3
    cards_drawn = 0
    while get_hand_size(hand) < num_cards and deck and cards_drawn < num_cards:
        card = deck.pop()
        hand[card] = hand.get(card, 0) + 1
        cards_drawn += 1
    return cards_drawn

def draw_one(deck, hand):
    """Ambil 1 kartu dari deck (jika ada) setelah menaruh 1 kartu."""
    if deck:
        card = deck.pop()
        hand[card] = hand.get(card, 0) + 1
        return True
    return False

def get_hand_size(hand):
    """Get total number of cards in hand"""
    return sum(hand.values())

def empty_board():
    """9x9 grid, each cell is a stack of (player_id, value) tuples"""
    return [[[] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def in_bounds(r, c):
    return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

# 8-directional neighbors
NEI8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def has_any_tile(board):
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c]:
                return True
    return False

def has_filled_neighbor(board, r, c):
    """Check if cell (r,c) has any adjacent filled cells"""
    for dr, dc in NEI8:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc]:
            return True
    return False

def can_place(board, player, val, r, c, first_move_done):
    """Check if player can place card with value 'val' at position (r,c)"""
    if not in_bounds(r, c):
        return False, "Outside board"
    
    # First move must be at center (4,4) which is position (5,5) in 1-indexed
    if not first_move_done:
        if (r, c) != (GRID_SIZE//2, GRID_SIZE//2):
            return False, "First move must be at center (5,5)"
    else:
        # Must be adjacent to existing cards
        if not has_filled_neighbor(board, r, c):
            return False, "Must be placed adjacent to existing cards"
    
    stack = board[r][c]
    if not stack:
        # Empty cell - can place any card
        return True, ""
    else:
        top_owner, top_val = stack[-1]
        if top_owner == player:
            return False, "Cannot stack on own cards"
        if val <= top_val:
            return False, "Value must be higher to stack"
        return True, ""

def place_card_and_draw(board, player, val, r, c, deck, hand):
    """Place a card on the board and automatically draw a new one"""
    board[r][c].append((player, val))
    # Remove card from hand
    hand[val] -= 1
    if hand[val] == 0:
        del hand[val]
    # Automatically draw a new card to maintain hand size
    return draw_one(deck, hand)

def place_card(board, player, val, r, c):
    """Place a card on the board (kept for compatibility)"""
    board[r][c].append((player, val))

# Check for 4 in a row (horizontal, vertical, diagonal)
DIRS = [(0,1), (1,0), (1,1), (1,-1)]

def check_win(board, player):
    """Check if player has 4 cards in a row (owned on top of stacks)"""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not board[r][c]:
                continue
            top_owner, _ = board[r][c][-1]
            if top_owner != player:
                continue
            
            # Check all 4 directions from this position
            for dr, dc in DIRS:
                count = 1
                # Count forward
                rr, cc = r + dr, c + dc
                while (in_bounds(rr, cc) and board[rr][cc] and 
                       board[rr][cc][-1][0] == player):
                    count += 1
                    rr += dr
                    cc += dc
                # Count backward
                rr, cc = r - dr, c - dc
                while (in_bounds(rr, cc) and board[rr][cc] and 
                       board[rr][cc][-1][0] == player):
                    count += 1
                    rr -= dr
                    cc -= dc
                
                if count >= 4:
                    return True
    return False

def count_in_direction(board, player, r, c, dr, dc):
    """Count consecutive cells owned by player in direction (dr, dc) from (r, c)"""
    count = 0
    rr, cc = r, c
    while (in_bounds(rr, cc) and board[rr][cc] and 
           board[rr][cc][-1][0] == player):
        count += 1
        rr += dr
        cc += dc
    return count

def analyze_position(board, player, r, c):
    """Analyze how good a position is for forming lines"""
    if not board[r][c] or board[r][c][-1][0] != player:
        return 0
    
    max_line = 0
    total_potential = 0
    
    for dr, dc in DIRS:
        # Count in both directions
        forward = count_in_direction(board, player, r + dr, c + dc, dr, dc)
        backward = count_in_direction(board, player, r - dr, c - dc, -dr, -dc)
        line_length = 1 + forward + backward
        
        max_line = max(max_line, line_length)
        total_potential += line_length
    
    return max_line * 10 + total_potential

def evaluate_board_position(board, player):
    """Evaluate overall board position for a player"""
    score = 0
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] and board[r][c][-1][0] == player:
                pos_value = analyze_position(board, player, r, c)
                score += pos_value
    return score

def find_threats_and_opportunities(board, player, hands):
    """Advanced analysis of threats and opportunities"""
    opportunities = []
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            # Check all cards in player's hand
            for val in hands[player]:
                if hands[player][val] <= 0:
                    continue
                
                ok, _ = can_place(board, player, val, r, c, True)
                if not ok:
                    continue
                
                # Simulate placing the card
                board[r][c].append((player, val))
                
                # Calculate various metrics
                win_score = 1000 if check_win(board, player) else 0
                
                # Count line formations
                max_line = 0
                threat_level = 0
                
                for dr, dc in DIRS:
                    forward = count_in_direction(board, player, r + dr, c + dc, dr, dc)
                    backward = count_in_direction(board, player, r - dr, c - dc, -dr, -dc)
                    line_length = 1 + forward + backward
                    max_line = max(max_line, line_length)
                    
                    if line_length == 4:
                        threat_level = 4  # Winning move
                    elif line_length == 3:
                        threat_level = max(threat_level, 3)  # Strong threat
                    elif line_length == 2:
                        threat_level = max(threat_level, 2)  # Building
                
                # Strategic position value
                center_distance = abs(r - GRID_SIZE//2) + abs(c - GRID_SIZE//2)
                position_value = max(0, 10 - center_distance)
                
                # Control value (taking opponent's stack)
                control_value = 0
                if len(board[r][c]) > 1:  # We're stacking on someone
                    control_value = 5 + val  # Higher value cards are better for control
                
                total_score = (win_score + 
                             threat_level * 25 + 
                             max_line * 8 + 
                             position_value + 
                             control_value)
                
                opportunities.append((r, c, val, total_score, threat_level, max_line))
                
                # Remove the simulated card
                board[r][c].pop()
    
    return opportunities

def find_blocking_opportunities(board, target_player, blocking_player, hands):
    """Find critical moves to block target player"""
    blocking_moves = []
    
    # Analyze target player's potential moves
    target_opportunities = find_threats_and_opportunities(board, target_player, hands)
    
    for tr, tc, tv, score, threat, max_line in target_opportunities:
        if threat < 3 and max_line < 3:  # Only worry about serious threats
            continue
        
        # Try to block this position
        for val in hands[blocking_player]:
            if hands[blocking_player][val] <= 0:
                continue
            
            ok, _ = can_place(board, blocking_player, val, tr, tc, True)
            if ok:
                # Calculate blocking value
                block_value = threat * 30 + max_line * 10
                if threat >= 4:  # Blocking a win
                    block_value = 1000
                
                blocking_moves.append((tr, tc, val, block_value, threat))
    
    return blocking_moves

def final_scores(board):
    """Calculate final scores based on controlled cells"""
    scores = [0, 0, 0, 0]
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c]:
                owner, val = board[r][c][-1]
                scores[owner] += val
    return scores

def hands_empty(all_hands):
    """Check if all players have no cards left"""
    return all(get_hand_size(h) == 0 for h in all_hands)

def deck_empty(deck):
    """Check if deck is empty"""
    return len(deck) == 0

# ---------------------------------------
# Drawing Functions (Updated for hand display)
# ---------------------------------------
def draw_gradient_background():
    """Draw elegant dark gradient background"""
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(12 + 30*t)
        g = int(15 + 35*t)
        b = int(22 + 40*t)
        pygame.draw.line(SCREEN, (r,g,b), (0,y), (WIDTH,y))

def draw_board(board, active_player, selected_value=None, first_move_done=True):
    """Draw the game board with semi-transparent background"""
    # Semi-transparent panel behind board
    surf = pygame.Surface((BOARD_PIX+40, BOARD_PIX+40), pygame.SRCALPHA)
    pygame.draw.rect(surf, (255,255,255,22), 
                     pygame.Rect(0,0,BOARD_PIX+40, BOARD_PIX+40), 
                     border_radius=22)
    SCREEN.blit(surf, (offset_x-20, offset_y-20))

    # Draw grid
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = offset_x + c * CELL_SIZE
            y = offset_y + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            
            # Base cell color
            base_color = (34, 38, 54)
            
            # Highlight valid moves for human player
            if active_player == 0 and selected_value is not None:
                can_place_here, _ = can_place(board, 0, selected_value, r, c, first_move_done)
                if can_place_here:
                    base_color = (60, 100, 60)  # Green tint for valid moves
            
            pygame.draw.rect(SCREEN, base_color, rect)
            pygame.draw.rect(SCREEN, (60, 70, 96), rect, 1)

            # Draw top card if exists
            stack = board[r][c]
            if stack:
                owner, val = stack[-1]
                # Card background with bright player color
                card_rect = rect.inflate(-CELL_PAD*2, -CELL_PAD*2)
                
                # Use bright colors for better visibility
                card_color = PLAYER_COLORS[owner]
                pygame.draw.rect(SCREEN, card_color, card_rect, border_radius=8)
                
                # Thick black border for contrast
                pygame.draw.rect(SCREEN, BLACK, card_rect, 3, border_radius=8)
                
                # Card value with black text for readability
                text = FONT_MED.render(str(val), True, BLACK)
                tx = x + CELL_SIZE//2 - text.get_width()//2
                ty = y + CELL_SIZE//2 - text.get_height()//2
                SCREEN.blit(text, (tx, ty))
                
                # Stack indicator if more than 1 card
                if len(stack) > 1:
                    stack_text = FONT_SMALL.render(f"({len(stack)})", True, BLACK)
                    SCREEN.blit(stack_text, (x + 4, y + 4))

    # Highlight center for first move
    if not first_move_done:
        center_rect = pygame.Rect(offset_x + (GRID_SIZE//2)*CELL_SIZE,
                                  offset_y + (GRID_SIZE//2)*CELL_SIZE,
                                  CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(SCREEN, (255,255,0), center_rect, 4)

    # Active player glow around board
    glow_rect = pygame.Rect(offset_x-6, offset_y-6, BOARD_PIX+12, BOARD_PIX+12)
    color = PLAYER_COLORS[active_player]
    pygame.draw.rect(SCREEN, color, glow_rect, 6, border_radius=12)

def draw_hands(hands, deck, active_player, status_text, selected_value, difficulty):
    """Draw player hands and status (updated for hand limit)"""
    panel_h = 240  # Increased height for deck info
    panel_rect = pygame.Rect(0, HEIGHT - panel_h, WIDTH, panel_h)
    
    # Semi-transparent background
    surf = pygame.Surface((WIDTH, panel_h), pygame.SRCALPHA)
    surf.fill((0,0,0,180))
    SCREEN.blit(surf, (0, HEIGHT - panel_h))

    # Status text with difficulty indicator and deck size
    status = FONT_MED.render(f"Turn: {PLAYER_NAMES[active_player]} | Difficulty: {DIFFICULTY_NAMES[difficulty]} | Deck: {len(deck)} cards", 
                           True, PLAYER_COLORS[active_player])
    SCREEN.blit(status, (40, HEIGHT - panel_h + 20))
    
    if status_text:
        status2 = FONT_SMALL.render(status_text, True, WHITE)
        SCREEN.blit(status2, (40, HEIGHT - panel_h + 60))

    # Human hand (player 0) - Show actual cards
    human_hand = hands[0]
    label = FONT_MED.render(f"Your Cards ({get_hand_size(human_hand)}/{HAND_LIMIT}) - click cards or press keys:", True, WHITE)
    SCREEN.blit(label, (40, HEIGHT - panel_h + 100))
    
    x0 = 40
    card_idx = 0
    for val in sorted(human_hand.keys()):
        count = human_hand[val]
        for _ in range(count):
            box = pygame.Rect(x0 + card_idx*90, HEIGHT - panel_h + 130, 70, 70)
            
            # Make selected card very obvious
            if val == selected_value:
                pygame.draw.rect(SCREEN, YELLOW, box, border_radius=12)
                pygame.draw.rect(SCREEN, BLACK, box, 4, border_radius=12)
            else:
                pygame.draw.rect(SCREEN, (100, 120, 150), box, border_radius=12)
                pygame.draw.rect(SCREEN, WHITE, box, 2, border_radius=12)
            
            # Card value - make it very visible
            text_color = BLACK if val == selected_value else WHITE
            text = FONT_MED.render(str(val), True, text_color)
            SCREEN.blit(text, (box.centerx - text.get_width()//2, box.y + 8))
            
            # Key hint
            key_text = FONT_SMALL.render(f"[{card_idx+1}]", True, text_color)
            SCREEN.blit(key_text, (box.centerx - key_text.get_width()//2, box.bottom - 25))
            
            card_idx += 1

    # AI hands summary
    for pid in range(1, 4):
        hand_size = get_hand_size(hands[pid])
        color = PLAYER_COLORS[pid] if pid == active_player else GREY
        text = FONT_SMALL.render(f"{PLAYER_NAMES[pid]}: {hand_size} cards", True, color)
        SCREEN.blit(text, (WIDTH - 320, HEIGHT - panel_h + 20 + (pid-1)*28))

def draw_key_hints():
    """Draw keyboard shortcuts"""
    hints = FONT_SMALL.render("[R] Replay   [Q] Quit", True, GREY)
    SCREEN.blit(hints, (WIDTH - hints.get_width() - 28, 24))

def board_cell_from_mouse(mx, my):
    """Convert mouse coordinates to board cell"""
    if (mx < offset_x or my < offset_y or 
        mx >= offset_x + BOARD_PIX or my >= offset_y + BOARD_PIX):
        return None
    
    cx = (mx - offset_x) // CELL_SIZE
    cy = (my - offset_y) // CELL_SIZE
    
    if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
        return cy, cx
    return None

def hand_card_from_mouse(mx, my, hand):
    """Check if mouse clicked on a hand card (updated for new layout)"""
    panel_h = 240
    if my < HEIGHT - panel_h + 130 or my > HEIGHT - panel_h + 200:
        return None
    
    x0 = 40
    card_idx = 0
    for val in sorted(hand.keys()):
        count = hand[val]
        for _ in range(count):
            box_x = x0 + card_idx*90
            if box_x <= mx <= box_x + 70:
                return val
            card_idx += 1
    return None


def draw_winner_popup(winner_name, scores):
    """Draw game over popup"""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    SCREEN.blit(overlay, (0,0))

    box = pygame.Rect(0, 0, 760, 420)
    box.center = (WIDTH//2, HEIGHT//2)
    pygame.draw.rect(SCREEN, (28, 36, 48), box, border_radius=22)
    pygame.draw.rect(SCREEN, (90, 110, 160), box, 4, border_radius=22)

    title = FONT_BIG.render("End Game", True, WHITE)
    SCREEN.blit(title, (box.centerx - title.get_width()//2, box.y + 36))

    winner = FONT_MED.render(f"Winner: {winner_name}", True, (255, 235, 175))
    SCREEN.blit(winner, (box.centerx - winner.get_width()//2, box.y + 110))

    # Scores
    y = box.y + 170
    for i, score in enumerate(scores):
        color = PLAYER_COLORS[i] if i < len(PLAYER_COLORS) else WHITE
        line = FONT_SMALL.render(f"{PLAYER_NAMES[i]}: {score} points", True, color)
        SCREEN.blit(line, (box.centerx - 280 + i*140, y))

    hint = FONT_SMALL.render("Press [R] to Replay or [Q] to Quit", True, GREY)
    SCREEN.blit(hint, (box.centerx - hint.get_width()//2, box.bottom - 60))

# ---------------------------------------
# Enhanced AI Logic (Updated for hand management)
# ---------------------------------------
def potential_cells(board, first_move_done):
    """Get all valid cells where cards can be placed"""
    if not first_move_done:
        return [(GRID_SIZE//2, GRID_SIZE//2)]
    
    cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if has_filled_neighbor(board, r, c):
                cells.append((r, c))
    return list(set(cells))

def ai_choose_move_easy(board, hands, player, first_move_done):
    """Easy AI - Random but valid moves"""
    candidates = potential_cells(board, first_move_done)
    if not candidates:
        return None
    
    # Sort by distance to center
    center = (GRID_SIZE//2, GRID_SIZE//2)
    candidates.sort(key=lambda rc: abs(rc[0]-center[0]) + abs(rc[1]-center[1]))
    
    # Available cards (highest first)
    available_vals = []
    for v in sorted(hands[player].keys(), reverse=True):
        if hands[player][v] > 0:
            available_vals.append(v)
    
    if not available_vals:
        return None
    
    # Try to find a winning move
    for r, c in candidates:
        for v in available_vals:
            ok, _ = can_place(board, player, v, r, c, first_move_done)
            if ok:
                # Simulate the move
                board[r][c].append((player, v))
                wins = check_win(board, player)
                board[r][c].pop()  # Undo
                if wins:
                    return (r, c, v)
    
    # Otherwise, play first valid move with highest card
    for r, c in candidates:
        for v in available_vals:
            ok, _ = can_place(board, player, v, r, c, first_move_done)
            if ok:
                return (r, c, v)
    
    return None

def ai_choose_move_medium(board, hands, player, first_move_done):
    """Medium AI - Strategic thinking with threat analysis"""
    # Find all opportunities
    opportunities = find_threats_and_opportunities(board, player, hands)
    
    if not opportunities:
        return ai_choose_move_easy(board, hands, player, first_move_done)
    
    # Sort by total score (best moves first)
    opportunities.sort(key=lambda x: x[3], reverse=True)
    
    # Immediate win takes priority
    for r, c, v, score, threat, max_line in opportunities:
        if threat >= 4:  # Winning move
            return (r, c, v)
    
    # Block human wins if possible
    human_blocks = find_blocking_opportunities(board, 0, player, hands)
    human_blocks.sort(key=lambda x: x[3], reverse=True)
    
    for r, c, v, block_value, threat in human_blocks:
        if threat >= 4:  # Block immediate win
            return (r, c, v)
    
    # Play best strategic move
    for r, c, v, score, threat, max_line in opportunities:
        if threat >= 2 or max_line >= 3:  # Good strategic move
            return (r, c, v)
    
    # Fallback to best available move
    return (opportunities[0][0], opportunities[0][1], opportunities[0][2])

def ai_choose_move_hard(board, hands, player, first_move_done):
    """Hard AI - Advanced tactical play with multi-move planning"""
    # 1. Find all our opportunities
    opportunities = find_threats_and_opportunities(board, player, hands)
    
    if not opportunities:
        return ai_choose_move_easy(board, hands, player, first_move_done)
    
    # 2. Immediate wins always take priority
    for r, c, v, score, threat, max_line in opportunities:
        if threat >= 4:
            return (r, c, v)
    
    # 3. Critical blocking analysis for ALL opponents
    critical_blocks = []
    for opponent in range(4):
        if opponent == player:
            continue
        blocks = find_blocking_opportunities(board, opponent, player, hands)
        critical_blocks.extend(blocks)
    
    # Sort blocks by priority
    critical_blocks.sort(key=lambda x: x[3], reverse=True)
    
    # Block immediate wins first
    for r, c, v, block_value, threat in critical_blocks:
        if threat >= 4:
            return (r, c, v)
    
    # 4. Multi-step threat analysis
    best_move = None
    best_score = -1
    
    for r, c, v, score, threat, max_line in opportunities:
        # Simulate this move
        board[r][c].append((player, v))
        
        # Evaluate resulting position
        evaluation_score = score
        
        # Check if this creates multiple threats
        future_opportunities = find_threats_and_opportunities(board, player, hands)
        threat_count = sum(1 for _, _, _, _, t, _ in future_opportunities if t >= 3)
        evaluation_score += threat_count * 20
        
        # Check if this move denies opportunities to opponents
        denial_value = 0
        for opponent in range(4):
            if opponent == player:
                continue
            opp_opps_before = len(find_threats_and_opportunities(board, opponent, hands))
            # Temporarily remove our move to see original opportunities
            board[r][c].pop()
            opp_opps_after = len(find_threats_and_opportunities(board, opponent, hands))
            board[r][c].append((player, v))  # Put it back
            
            denied_opps = opp_opps_after - opp_opps_before
            denial_value += denied_opps * 5
        
        evaluation_score += denial_value
        
        # Prefer controlling high-value stacks
        if len(board[r][c]) > 1:
            stack_control_value = sum(card[1] for card in board[r][c][:-1])
            evaluation_score += stack_control_value * 2
        
        # Undo simulation
        board[r][c].pop()
        
        if evaluation_score > best_score:
            best_score = evaluation_score
            best_move = (r, c, v)
    
    # 5. If we have a great strategic move, take it
    if best_move and best_score > 50:
        return best_move
    
    # 6. Otherwise, block serious threats
    for r, c, v, block_value, threat in critical_blocks:
        if threat >= 3:
            return (r, c, v)
    
    # 7. Take our best offensive move
    opportunities.sort(key=lambda x: x[3], reverse=True)
    for r, c, v, score, threat, max_line in opportunities:
        if threat >= 2:
            return (r, c, v)
    
    # 8. Last resort - best available move
    if opportunities:
        return (opportunities[0][0], opportunities[0][1], opportunities[0][2])
    
    return None

def ai_choose_move(board, hands, player, first_move_done, difficulty):
    """Choose AI move based on difficulty level"""
    if difficulty == EASY:
        return ai_choose_move_easy(board, hands, player, first_move_done)
    elif difficulty == MEDIUM:
        return ai_choose_move_medium(board, hands, player, first_move_done)
    elif difficulty == HARD:
        return ai_choose_move_hard(board, hands, player, first_move_done)
    else:
        return ai_choose_move_easy(board, hands, player, first_move_done)

# ---------------------------------------
# Roulette Animation
# ---------------------------------------
def roulette_animation():
    """3-4 second roulette animation before game starts"""
    t_end = time.time() + random.uniform(3.0, 4.0)
    idx = 0
    names = ["Player 1...", "Player 2...", "Player 3...", "Player 4..."]
    last_tick = 0

    while time.time() < t_end:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

        draw_gradient_background()

        title = FONT_BIG.render("Determining Turn Order...", True, WHITE)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 160))

        box = pygame.Rect(0, 0, 520, 160)
        box.center = (WIDTH//2, HEIGHT//2)
        pygame.draw.rect(SCREEN, (28, 36, 48), box, border_radius=22)
        pygame.draw.rect(SCREEN, (90, 110, 160), box, 4, border_radius=22)

        text = FONT_BIG.render(names[idx % 4], True, (240, 240, 240))
        SCREEN.blit(text, (box.centerx - text.get_width()//2, 
                          box.centery - text.get_height()//2))

        if time.time() - last_tick > 0.25:
            s_play(CLICK_SND)
            idx += 1
            last_tick = time.time()

        draw_key_hints()
        pygame.display.flip()
        CLOCK.tick(FPS)

    s_play(DING_SND)
    return [0, 1, 2, 3]

# ---------------------------------------
# Game State (Updated for hand management)
# ---------------------------------------
class GameState:
    def __init__(self):
        self.difficulty = difficulty_selection()
        self.reset_all()

    def reset_all(self):
        self.board = empty_board()
        self.deck = create_deck()
        self.hands = [make_hand() for _ in range(4)]
        
        # Deal initial cards to all players
        for player in range(4):
            draw_cards(self.deck, self.hands[player], HAND_LIMIT)
        
        self.turn_order = roulette_animation()
        self.active_idx = 0
        self.active_player = self.turn_order[self.active_idx]
        self.first_move_done = False
        self.selected_value = None
        self.status_text = "Select a card (click or press 1-3), then click target cell."
        self.game_over = False
        self.winner = None
        self.scores = [0, 0, 0, 0]
        self.next_ai_time = None
        self.last_click_invalid = 0

    def next_turn(self):
        self.active_idx = (self.active_idx + 1) % 4
        self.active_player = self.turn_order[self.active_idx]
        
        # Draw cards if hand is below limit and deck has cards
        current_hand_size = get_hand_size(self.hands[self.active_player])
        if current_hand_size < HAND_LIMIT and self.deck:
            drawn = draw_cards(self.deck, self.hands[self.active_player], 
                             HAND_LIMIT - current_hand_size)
            if drawn > 0 and self.active_player == 0:  # Notify human player
                self.status_text = f"Drew {drawn} new card(s)."

    def human_can_act(self):
        return self.active_player == 0 and not self.game_over

    def ai_can_act(self):
        return self.active_player != 0 and not self.game_over

# ---------------------------------------
# Game Actions (Updated for hand management)
# ---------------------------------------
def human_try_place(gs, cell_rc):
    """Handle human player move"""
    if gs.game_over or not gs.human_can_act():
        return
    if cell_rc is None:
        gs.status_text = "Click on a valid board cell."
        return
    
    r, c = cell_rc
    v = gs.selected_value
    
    if v is None:
        gs.status_text = "Select a card first (click card or press 1-3)."
        return
    
    if v not in gs.hands[0] or gs.hands[0][v] <= 0:
        gs.status_text = f"Card {v} is not available."
        return

    ok, msg = can_place(gs.board, 0, v, r, c, gs.first_move_done)
    if not ok:
        gs.status_text = msg
        gs.last_click_invalid = time.time()
        return

    place_card(gs.board, 0, v, r, c)
    gs.hands[0][v] -= 1
    if gs.hands[0][v] == 0:
        del gs.hands[0][v]
    gs.first_move_done = True
    gs.selected_value = None

    if check_win(gs.board, 0):
        gs.game_over = True
        gs.winner = 0
        gs.scores = final_scores(gs.board)
        gs.status_text = "You win!"
        s_play(DING_SND)
        return

    if hands_empty(gs.hands) and deck_empty(gs.deck):
        gs.game_over = True
        gs.scores = final_scores(gs.board)
        gs.winner = max(range(4), key=lambda p: gs.scores[p])
        gs.status_text = "End Game - all cards played!"
        s_play(DING_SND)
        return

    gs.status_text = "Move completed. Waiting for AI..."
    gs.next_turn()
    if gs.ai_can_act():
        gs.next_ai_time = time.time() + 0.8

def human_select_card(gs, card_index):
    """Handle human card selection by index (1-3)"""
    if gs.game_over or not gs.human_can_act():
        return
    
    hand_values = sorted(gs.hands[0].keys())
    total_cards = get_hand_size(gs.hands[0])
    
    # Convert card index to actual cards considering duplicates
    card_positions = []
    for val in hand_values:
        count = gs.hands[0][val]
        for _ in range(count):
            card_positions.append(val)
    
    if 1 <= card_index <= len(card_positions):
        selected_val = card_positions[card_index - 1]
        gs.selected_value = selected_val
        gs.status_text = f"Card {selected_val} selected. Click on board to place."
        s_play(CLICK_SND)
    else:
        gs.status_text = f"Invalid card selection. You have {total_cards} cards."

def human_select_card_by_value(gs, card_value):
    """Handle human card selection by clicking on card"""
    if gs.game_over or not gs.human_can_act():
        return
    
    if card_value in gs.hands[0] and gs.hands[0][card_value] > 0:
        gs.selected_value = card_value
        gs.status_text = f"Card {card_value} selected. Click on board to place."
        s_play(CLICK_SND)
    else:
        gs.status_text = f"Card {card_value} not available."

def ai_act(gs):
    """Handle AI player move with difficulty-based logic"""
    if not gs.ai_can_act():
        return
    
    now = time.time()
    if gs.next_ai_time is None:
        gs.next_ai_time = now + 0.8
        return
    if now < gs.next_ai_time:
        return

    pid = gs.active_player
    
    # Check if AI has any cards
    if get_hand_size(gs.hands[pid]) == 0:
        gs.status_text = f"{PLAYER_NAMES[pid]} has no cards, skipping turn."
        gs.next_turn()
        if gs.ai_can_act():
            gs.next_ai_time = time.time() + 0.8
        else:
            gs.next_ai_time = None
            gs.status_text = "Your turn! Select a card then click board."
        return
    
    move = ai_choose_move(gs.board, gs.hands, pid, gs.first_move_done, gs.difficulty)
    
    if move:
        r, c, v = move
        if v in gs.hands[pid] and gs.hands[pid][v] > 0:
            ok, _ = can_place(gs.board, pid, v, r, c, gs.first_move_done)
            if ok:
                place_card(gs.board, pid, v, r, c)
                gs.hands[pid][v] -= 1
                if gs.hands[pid][v] == 0:
                    del gs.hands[pid][v]
                gs.first_move_done = True

                if check_win(gs.board, pid):
                    gs.game_over = True
                    gs.winner = pid
                    gs.scores = final_scores(gs.board)
                    gs.status_text = f"{PLAYER_NAMES[pid]} wins!"
                    s_play(DING_SND)
                    return

                if hands_empty(gs.hands) and deck_empty(gs.deck):
                    gs.game_over = True
                    gs.scores = final_scores(gs.board)
                    gs.winner = max(range(4), key=lambda p: gs.scores[p])
                    gs.status_text = "End Game - all cards played!"
                    s_play(DING_SND)
                    return

                gs.status_text = f"{PLAYER_NAMES[pid]} played card {v} at ({r+1},{c+1})."
                gs.next_turn()
                if gs.ai_can_act():
                    gs.next_ai_time = time.time() + 0.8
                else:
                    gs.next_ai_time = None
                    gs.status_text = "Your turn! Select a card then click board."
                return

    # No valid move - skip turn
    gs.status_text = f"{PLAYER_NAMES[pid]} skips turn."
    gs.next_turn()
    if gs.ai_can_act():
        gs.next_ai_time = time.time() + 0.8
    else:
        gs.next_ai_time = None
        gs.status_text = "Your turn! Select a card then click board."

# ---------------------------------------
# Main Loop (Updated)
# ---------------------------------------
def draw_everything(gs):
    """Draw complete game state"""
    draw_gradient_background()
    draw_board(gs.board, gs.active_player, gs.selected_value, gs.first_move_done)
    draw_hands(gs.hands, gs.deck, gs.active_player, gs.status_text, gs.selected_value, gs.difficulty)
    draw_key_hints()

    # Flash effect for invalid clicks
    if time.time() - gs.last_click_invalid < 0.15:
        flash_surf = pygame.Surface((BOARD_PIX, BOARD_PIX), pygame.SRCALPHA)
        flash_surf.fill((255, 64, 64, 80))
        SCREEN.blit(flash_surf, (offset_x, offset_y))

    # Winner popup
    if gs.game_over:
        winner_name = "Draw"
        if gs.winner is not None:
            winner_name = PLAYER_NAMES[gs.winner]
        draw_winner_popup(winner_name, gs.scores)

def main():
    """Main game loop"""
    gs = GameState()
    running = True

    while running:
        CLOCK.tick(FPS)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    gs = GameState()  # Restart with new difficulty selection
                elif pygame.K_1 <= event.key <= pygame.K_3:
                    if gs.human_can_act():
                        chosen = event.key - pygame.K_0
                        human_select_card(gs, chosen)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Check if clicked on hand card
                if gs.human_can_act() and not gs.game_over:
                    card_clicked = hand_card_from_mouse(mx, my, gs.hands[0])
                    if card_clicked:
                        human_select_card_by_value(gs, card_clicked)
                        continue
                
                # Check if clicked on board
                if gs.human_can_act() and not gs.game_over:
                    cell = board_cell_from_mouse(mx, my)
                    if cell:
                        human_try_place(gs, cell)

        # AI turn
        if gs.ai_can_act() and not gs.game_over:
            ai_act(gs)

        # Render
        draw_everything(gs)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
