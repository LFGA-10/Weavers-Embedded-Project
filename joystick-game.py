import utils.session
import pygame
import serial
import serial.tools.list_ports
import random
import sys
import time


def find_usb_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if port.startswith(('/dev/tty.usb', '/dev/cu.usb', 'COM', '/dev/ttyACM')):
            return port
    return None

def connect_to_usb_port():
    while True:
        port_name = find_usb_port()
        if port_name is None:
            print("No suitable USB port found. Retrying in 2 seconds...")
            time.sleep(2)
        else:
            print(f"Connected to {port_name}")
            return serial.Serial(port_name, 9600, timeout=0.1)


def reset_game():
    global player_x, player_y, stones, dodged_stones, game_over, paused, stone_speed
    player_x, player_y = win_width // 2, win_height - player_radius - 20
    stones = [{"x": random.randint(0, win_width - stone_width), "y": -random.randint(50, 300)} for _ in range(stone_count)]
    dodged_stones = 0
    game_over = False
    paused = False
    stone_speed = 5


ser = connect_to_usb_port()


pygame.init()
win_width, win_height = 800, 600
win = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Dodge the Stones")


bg = pygame.image.load("background.jpg")  
bg = pygame.transform.scale(bg, (win_width, win_height))
player_img = pygame.image.load("player.png")  
player_img = pygame.transform.scale(player_img, (50, 50))
stone_img = pygame.image.load("stone.png")  # 
stone_img = pygame.transform.scale(stone_img, (40, 40))

pygame.mixer.init()
crash_sound = pygame.mixer.Sound("crash.mp3")
ding_sound = pygame.mixer.Sound("crash.mp3")
pygame.mixer.music.load("bg_music.mp3")
pygame.mixer.music.play(-1)  


player_radius = 25
player_x, player_y = win_width // 2, win_height - player_radius - 20


stone_width, stone_height = 40, 40
stone_speed = 5
stone_count = 5
stones = [{"x": random.randint(0, win_width - stone_width), "y": -random.randint(50, 300)} for _ in range(stone_count)]

clock = pygame.time.Clock()
running = True
game_over = False
paused = False
dodged_stones = 0


while running:
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

    if paused or game_over:
        win.blit(bg, (0, 0))
        font = pygame.font.Font(None, 74)
        if game_over:
            text = font.render("Game Over! Press R to restart", True, (255, 0, 0))
        else:
            text = font.render("Paused", True, (0, 0, 0))
        win.blit(text, (win_width // 2 - text.get_width() // 2, win_height // 2))
        pygame.display.flip()
        clock.tick(60)
        continue

    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip().split(',')
            if len(data) == 3:
                joy_x, joy_y, button_state = map(int, data)
                player_x += int((joy_x - 512) / 512 * 10)
                player_y += int((joy_y - 512) / 512 * 10)
                player_x = max(0, min(win_width - 50, player_x))
                player_y = max(0, min(win_height - 50, player_y))
    except Exception as e:
        print(f"Serial read error: {e}")
    for stone in stones:
        stone["y"] += stone_speed
        if stone["y"] > win_height:
            stone["y"] = -random.randint(50, 300)
            stone["x"] = random.randint(0, win_width - stone_width)
            dodged_stones += 1
            ding_sound.play()
            if dodged_stones % 10 == 0: 
                stone_speed += 1
        player_rect = pygame.Rect(player_x, player_y, 50, 50)
        stone_rect = pygame.Rect(stone["x"], stone["y"], stone_width, stone_height)
        if player_rect.colliderect(stone_rect):
            crash_sound.play()
            game_over = True

  
    win.blit(bg, (0, 0))
    win.blit(player_img, (player_x, player_y))
    for stone in stones:
        win.blit(stone_img, (stone["x"], stone["y"]))

    font = pygame.font.Font(None, 36)
    text = font.render(f"Stones dodged: {dodged_stones}", True, (0, 0, 0))
    win.blit(text, (10, 10))
    pygame.display.flip()

    clock.tick(60)

ser.close()
pygame.quit()
sys.exit()
