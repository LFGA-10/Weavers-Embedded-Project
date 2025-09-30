import pygame
import serial
import serial.tools.list_ports
import random
import sys
import time

# -------------------------
# Serial / Arduino Setup
# -------------------------
def find_usb_port():
    """Find the correct USB port for the Arduino."""
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if port.startswith(('/dev/tty.usb', '/dev/cu.usb', 'COM', '/dev/ttyACM')):
            return port
    return None

def connect_to_usb_port():
    """Continuously attempt to connect to the USB port."""
    while True:
        port_name = find_usb_port()
        if port_name is None:
            print("No suitable USB port found. Retrying in 2 seconds...")
            time.sleep(2)
        else:
            print(f"Connected to {port_name}")
            return serial.Serial(port_name, 9600, timeout=0.1)

# -------------------------
# Game Reset
# -------------------------
def reset_game():
    """Reset the game state."""
    global player_x, player_y, stones, dodged_stones, game_over, paused
    player_x, player_y = win_width // 2, win_height - player_radius - 10
    stones = [{"x": random.randint(0, win_width - stone_width), "y": -random.randint(50, 300)} for _ in range(stone_count)]
    dodged_stones = 0
    game_over = False
    paused = False

# -------------------------
# Initialize Serial
# -------------------------
ser = connect_to_usb_port()

# -------------------------
# Pygame Setup
# -------------------------
pygame.init()
win_width, win_height = 800, 600
win = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Dodge the Stones")

# Colors
bg_color = (255, 255, 255)
player_color = (0, 255, 0)
stone_color = (255, 0, 0)
failure_color = (255, 0, 0)

# Player setup
player_radius = 20
player_x, player_y = win_width // 2, win_height - player_radius - 10

# Stone setup
stone_width, stone_height = 40, 40
stone_speed = 5
stone_count = 5
stones = [{"x": random.randint(0, win_width - stone_width), "y": -random.randint(50, 300)} for _ in range(stone_count)]

# Game variables
clock = pygame.time.Clock()
running = True
game_over = False
paused = False
dodged_stones = 0  # Count how many stones successfully dodged

# -------------------------
# Game Loop
# -------------------------
while running:
    # -------------------------
    # Event Handling
    # -------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
            elif event.key == pygame.K_q:
                running = False
            elif event.key == pygame.K_p:
                paused = not paused

    # -------------------------
    # Skip game updates if paused or game over
    # -------------------------
    if paused or game_over:
        # Still need to draw current screen
        win.fill(bg_color)
        if game_over:
            font = pygame.font.Font(None, 74)
            text = font.render("Game Over! Press R to restart", True, failure_color)
            win.blit(text, (win_width // 2 - text.get_width() // 2, win_height // 2 - text.get_height() // 2))
        else:
            font = pygame.font.Font(None, 74)
            text = font.render("Paused", True, (0, 0, 0))
            win.blit(text, (win_width // 2 - text.get_width() // 2, win_height // 2 - text.get_height() // 2))
        pygame.display.flip()
        clock.tick(60)
        continue

    # -------------------------
    # Handle serial data for joystick input
    # -------------------------
    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip().split(',')
            if len(data) == 3:
                joy_x, joy_y, button_state = map(int, data)
                # Scale joystick input (-512 to +512) to movement speed
                player_x += int((joy_x - 512) / 512 * 10)
                player_y += int((joy_y - 512) / 512 * 10)
                # Keep player inside window
                player_x = max(player_radius, min(win_width - player_radius, player_x))
                player_y = max(player_radius, min(win_height - player_radius, player_y))
    except Exception as e:
        print(f"Serial read error: {e}")

    # -------------------------
    # Move stones
    # -------------------------
    for stone in stones:
        stone["y"] += stone_speed
        if stone["y"] > win_height:
            stone["y"] = -random.randint(50, 300)
            stone["x"] = random.randint(0, win_width - stone_width)
            dodged_stones += 1  # Successfully dodged
        # Collision detection
        if (
            player_x - player_radius < stone["x"] + stone_width
            and player_x + player_radius > stone["x"]
            and player_y - player_radius < stone["y"] + stone_height
            and player_y + player_radius > stone["y"]
        ):
            game_over = True

    # -------------------------
    # Drawing
    # -------------------------
    win.fill(bg_color)
    pygame.draw.circle(win, player_color, (player_x, player_y), player_radius)
    for stone in stones:
        pygame.draw.rect(win, stone_color, (stone["x"], stone["y"], stone_width, stone_height))
    font = pygame.font.Font(None, 36)
    text = font.render(f"Stones dodged: {dodged_stones}", True, (0, 0, 0))
    win.blit(text, (10, 10))
    pygame.display.flip()

    clock.tick(60)

# -------------------------
# Cleanup
# -------------------------
ser.close()
pygame.quit()
sys.exit()
