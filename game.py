import pygame
import sys
import random
import asyncio
import platform
import math

# Initialize Pygame
pygame.init()

# Screen
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🚀 Space Shooter: Galactic Odyssey")

# Fonts
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 64)
title_font = pygame.font.SysFont(None, 80)

# Load and optimize assets
bg_img = pygame.transform.scale(pygame.image.load("space.png").convert(), (WIDTH, HEIGHT))
player_img = pygame.transform.scale(pygame.image.load("ship.png").convert_alpha(), (50, 50))
portal_img = pygame.transform.scale(pygame.image.load("portal.png").convert_alpha(), (150, 150))
boss_img = pygame.transform.scale(pygame.image.load("boss.png").convert_alpha(), (100, 100))
enemy_imgs = {
    "ene1": pygame.transform.scale(pygame.image.load("ene1.png").convert_alpha(), (50, 50)),
    "ene2": pygame.transform.scale(pygame.image.load("ene2.png").convert_alpha(), (50, 50)),
    "ene3": pygame.transform.scale(pygame.image.load("ene3.png").convert_alpha(), (50, 50)),
}

# Power-up icon
powerup_img = pygame.transform.scale(pygame.image.load("ene1.png").convert_alpha(), (30, 30))

# Particle effects
particles = []

# Laser colors
laser_colors = {
    "ene1": (255, 0, 0),
    "ene2": (255, 255, 0),
    "ene3": (0, 255, 255),
    "boss": (255, 0, 255),
    "miniboss": (255, 128, 0),
    "player": (255, 255, 255)
}

# Game constants
player_health = 100
max_player_health = 100
player_speed = 6
player_lasers = []
player_cooldown = 0
player_cooldown_max = 15
player_power = 1
player_shield = 0
player_invincible = 0
score_multiplier = 1
combo_timer = 0

enemies = []
enemy_lasers = []
enemy_fire_timer = 0

boss = None
boss_lasers = []
boss_health = 150
max_boss_health = 150
boss_attack_timer = 0
miniboss = False
boss_movement_timer = 0

portal = None
powerups = []
boss_mode = False
boss_started = False
game_won = False
game_over = False

level = 1
score = 0
high_score = 0
kills = 0
kills_to_clear = 10
level_intro_timer = 120
show_level_text = True
menu_animation_timer = 0
screen_shake = 0

bg_y = 0
bg_speed = 2
FPS = 60
game_state = "menu"

def create_particle(x, y, color, size=5, lifetime=30):
    return {"rect": pygame.Rect(x, y, size, size), "color": color, "lifetime": lifetime, "vx": random.uniform(-2, 2), "vy": random.uniform(-2, 2), "alpha": 255}

def draw_background(shake_offset=0):
    global bg_y
    bg_y = (bg_y + bg_speed) % HEIGHT
    screen.blit(bg_img, (shake_offset, bg_y - HEIGHT))
    screen.blit(bg_img, (shake_offset, bg_y))

def draw_health_bar(x, y, hp, max_hp, color):
    ratio = max(0, hp / max_hp)
    pygame.draw.rect(screen, (80, 80, 80), (x, y, 50, 6))
    pygame.draw.rect(screen, color, (x, y, 50 * ratio, 6))

def draw_player_health():
    pygame.draw.rect(screen, (80, 80, 80), (10, HEIGHT - 30, 200, 20))
    ratio = max(0, player_health / max_player_health)
    pygame.draw.rect(screen, (0, 255, 0), (10, HEIGHT - 30, 200 * ratio, 20))
    screen.blit(font.render("HP", True, (255, 255, 255)), (220, HEIGHT - 32))
    if player_shield > 0:
        screen.blit(font.render(f"Shield: {player_shield}", True, (0, 255, 255)), (10, HEIGHT - 60))
    if combo_timer > 0:
        combo_ratio = combo_timer / 120
        pygame.draw.rect(screen, (80, 80, 80), (10, HEIGHT - 90, 100, 8))
        pygame.draw.rect(screen, (255, 165, 0), (10, HEIGHT - 90, 100 * combo_ratio, 8))

def draw_level_intro(text, timer):
    fade = min(255, timer * 2)
    txt = big_font.render(text, True, (255, 255, 255))
    txt.set_alpha(fade)
    screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 100))

def spawn_enemies():
    if kills >= kills_to_clear or miniboss:
        return
    types = {
        1: ["ene1"],
        2: ["ene1", "ene2"],
        3: ["ene2", "ene3"],
        4: ["ene3"]
    }.get(level, ["ene3"])
    if len(enemies) < min(3, level + 1):
        t = random.choice(types)
        x = random.randint(50, WIDTH - 100)
        y = -50
        enemy = {
            "type": t,
            "rect": pygame.Rect(x, y, 50, 50),
            "health": 50 if t == "ene3" else 30 if t == "ene2" else 20,
            "max_health": 50 if t == "ene3" else 30 if t == "ene2" else 20,
            "speed": 4 if t == "ene1" else 3 if t == "ene2" else 2,
            "shoot_timer": random.randint(0, 30),
            "sway": random.uniform(-1, 1),
            "pause_timer": 0 if t != "ene3" else random.randint(0, 60)
        }
        enemies.append(enemy)

def spawn_powerup(x, y):
    if random.random() < 0.25:
        powerups.append({"rect": pygame.Rect(x, y, 30, 30), "type": random.choice(["health", "power", "shield"])})

def reset_game():
    global player, player_health, player_lasers, player_cooldown, player_power, player_shield, player_invincible, score_multiplier, combo_timer, enemies, enemy_lasers, boss, boss_lasers, boss_health, boss_mode, boss_started, boss_attack_timer, miniboss, portal, powerups, game_over, game_won, level, kills, kills_to_clear, score, show_level_text, level_intro_timer, screen_shake
    player = pygame.Rect(WIDTH//2 - 25, HEIGHT - 100, 50, 50)
    player_health = max_player_health
    player_lasers = []
    player_cooldown = 0
    player_power = 1
    player_shield = 0
    player_invincible = 0
    score_multiplier = 1
    combo_timer = 0
    enemies = []
    enemy_lasers = []
    boss = None
    boss_lasers = []
    boss_health = max_boss_health
    boss_mode = False
    boss_started = False
    boss_attack_timer = 0
    miniboss = False
    portal = None
    powerups = []
    game_over = False
    game_won = False
    level = 1
    kills = 0
    kills_to_clear = 10
    score = 0
    show_level_text = True
    level_intro_timer = 120
    screen_shake = 0
    particles.clear()

async def main():
    global game_state, player_cooldown, enemy_fire_timer, boss_movement_timer, game_over, game_won, level, kills, score, show_level_text, level_intro_timer, menu_animation_timer, boss_mode, boss_started, miniboss, player_health, player_power, player_shield, player_invincible, score_multiplier, combo_timer, high_score, screen_shake, kills_to_clear, boss_health, boss_lasers, boss_attack_timer, portal, powerups, enemies, enemy_lasers
    player = pygame.Rect(WIDTH//2 - 25, HEIGHT - 100, 50, 50)
    clock = pygame.time.Clock()
    running = True
    selected_menu = 0

    while running:
        clock.tick(FPS)
        shake_offset = 0
        if screen_shake > 0:
            shake_offset = random.randint(-5, 5)
            screen_shake -= 1
        draw_background(shake_offset)

        if game_state == "menu":
            menu_animation_timer = (menu_animation_timer + 1) % 60
            pulse = 1 + 0.1 * (1 if menu_animation_timer < 30 else -1)

            if random.random() < 0.1:
                particles.append(create_particle(random.randint(0, WIDTH), 0, (255, 255, 255), 2, 60))
            for p in particles[:]:
                p["rect"].y += 3
                p["lifetime"] -= 1
                p["alpha"] = max(0, p["alpha"] - 255 / 60)
                color = (*p["color"], int(p["alpha"]))
                pygame.draw.rect(screen, color, (p["rect"].x + shake_offset, p["rect"].y, p["rect"].width, p["rect"].height))
                if p["lifetime"] <= 0 or p["rect"].y > HEIGHT:
                    particles.remove(p)

            title_text = title_font.render("Space Shooter", True, (255, 255, 255))
            start_text = big_font.render("Start Game", True, (0, 255, 0) if selected_menu == 0 else (255, 255, 255))
            quit_text = big_font.render("Quit", True, (255, 0, 0) if selected_menu == 1 else (255, 255, 255))
            instruction_text = font.render("Arrows: Move, Space: Shoot, R: Restart", True, (200, 200, 200))
            high_score_text = font.render(f"High Score: {high_score}", True, (255, 215, 0))

            start_text = pygame.transform.scale(start_text, (int(start_text.get_width() * pulse), int(start_text.get_height() * pulse)))
            quit_text = pygame.transform.scale(quit_text, (int(quit_text.get_width() * pulse), int(quit_text.get_height() * pulse)))

            screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2 + shake_offset, HEIGHT//4))
            screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2 + shake_offset, HEIGHT//2))
            screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2 + shake_offset, HEIGHT//2 + 80))
            screen.blit(instruction_text, (WIDTH//2 - instruction_text.get_width()//2 + shake_offset, HEIGHT - 50))
            screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2 + shake_offset, HEIGHT//4 + 80))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_menu = 0
                    if event.key == pygame.K_DOWN:
                        selected_menu = 1
                    if event.key == pygame.K_RETURN:
                        if selected_menu == 0:
                            game_state = "playing"
                            particles.clear()
                            reset_game()
                        else:
                            running = False

        elif game_state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and not game_won and not game_over:
                    if event.key == pygame.K_SPACE and player_cooldown <= 0:
                        laser = pygame.Rect(player.centerx - 2, player.y, 4, 20)
                        player_lasers.append(laser)
                        player_cooldown = player_cooldown_max
                        particles.extend([create_particle(player.centerx, player.y, (255, 255, 255), 3, 15) for _ in range(5)])
                if event.type == pygame.KEYDOWN and (game_over or game_won) and event.key == pygame.K_r:
                    high_score = max(high_score, score)
                    reset_game()

            keys = pygame.key.get_pressed()
            if not game_over and not game_won:
                if keys[pygame.K_LEFT] and player.left > 0:
                    player.x -= player_speed
                if keys[pygame.K_RIGHT] and player.right < WIDTH:
                    player.x += player_speed
                if keys[pygame.K_UP] and player.top > 0:
                    player.y -= player_speed
                if keys[pygame.K_DOWN] and player.bottom < HEIGHT:
                    player.y += player_speed

            if player_cooldown > 0:
                player_cooldown -= 1
            if player_invincible > 0:
                player_invincible -= 1

            if show_level_text:
                txt = "MINI-BOSS!" if level == 3 and miniboss else "BOSS FIGHT!" if level == 5 and boss_mode else f"LEVEL {level}"
                draw_level_intro(txt, level_intro_timer)
                level_intro_timer -= 1
                if level_intro_timer <= 0:
                    show_level_text = False

            for laser in player_lasers[:]:
                laser.y -= 12
                pygame.draw.rect(screen, laser_colors["player"], (laser.x + shake_offset, laser.y, laser.width, laser.height))
                if laser.y < 0:
                    player_lasers.remove(laser)

            for p in particles[:]:
                p["rect"].x += p["vx"]
                p["rect"].y += p["vy"]
                p["lifetime"] -= 1
                p["alpha"] = max(0, p["alpha"] - 255 / 30)
                color = (*p["color"], int(p["alpha"]))
                pygame.draw.rect(screen, color, (p["rect"].x + shake_offset, p["rect"].y, p["rect"].width, p["rect"].height))
                if p["lifetime"] <= 0:
                    particles.remove(p)

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer <= 0:
                    score_multiplier = 1

            if not boss_mode and not game_over:
                spawn_enemies()
                for enemy in enemies[:]:
                    # Enemy movement
                    if enemy["type"] != "miniboss":
                        target_x = player.centerx
                        dx = target_x - enemy["rect"].centerx
                        if enemy["type"] == "ene1":
                            enemy["rect"].x += dx * 0.05 + enemy["sway"] * 2
                            enemy["rect"].y += enemy["speed"]
                        elif enemy["type"] == "ene2":
                            enemy["rect"].x += dx * 0.03 + math.sin(enemy["rect"].y * 0.02) * 3
                            enemy["rect"].y += enemy["speed"]
                        elif enemy["type"] == "ene3":
                            if enemy["pause_timer"] > 0:
                                enemy["pause_timer"] -= 1
                            else:
                                enemy["rect"].x += dx * 0.02 + math.cos(enemy["rect"].y * 0.01) * 2
                                enemy["rect"].y += enemy["speed"]
                                if random.random() < 0.02:
                                    enemy["pause_timer"] = 30
                    else:
                        # Mini-boss movement
                        if enemy["pause_timer"] > 0:
                            enemy["pause_timer"] -= 1
                            enemy["rect"].x += math.sin(enemy["rect"].y * 0.01) * 2
                        else:
                            enemy["rect"].y += 4
                            if enemy["rect"].y > 300:
                                enemy["rect"].y = 100
                                enemy["pause_timer"] = 60

                    # Keep enemies in bounds
                    enemy["rect"].x = max(50, min(WIDTH - 100, enemy["rect"].x))
                    if enemy["rect"].y > HEIGHT:
                        enemies.remove(enemy)
                        continue

                    screen.blit(enemy_imgs["ene3" if enemy["type"] == "miniboss" else enemy["type"]], (enemy["rect"].x + shake_offset, enemy["rect"].y))
                    draw_health_bar(enemy["rect"].x + shake_offset, enemy["rect"].y - 8, enemy["health"], enemy["max_health"], (0, 255, 0))

                    # Enemy shooting
                    enemy["shoot_timer"] -= 1
                    if enemy["shoot_timer"] <= 0:
                        if enemy["type"] == "ene1":
                            laser = pygame.Rect(enemy["rect"].centerx - 2, enemy["rect"].bottom, 4, 20)
                            enemy_lasers.append((laser, enemy["type"]))
                        elif enemy["type"] == "ene2":
                            for i in [-10, 10]:
                                laser = pygame.Rect(enemy["rect"].centerx - 2 + i, enemy["rect"].bottom, 4, 20)
                                enemy_lasers.append((laser, enemy["type"]))
                        elif enemy["type"] == "ene3" or enemy["type"] == "miniboss":
                            for i in [-20, 0, 20]:
                                laser = pygame.Rect(enemy["rect"].centerx - 2 + i, enemy["rect"].bottom, 4, 20)
                                enemy_lasers.append((laser, enemy["type"]))
                        enemy["shoot_timer"] = 50 if enemy["type"] == "ene1" else 40 if enemy["type"] == "ene2" else 30
                        particles.extend([create_particle(enemy["rect"].centerx, enemy["rect"].bottom, laser_colors[enemy["type"]], 3, 10) for _ in range(3)])

                    for laser in player_lasers[:]:
                        if laser.colliderect(enemy["rect"]):
                            player_lasers.remove(laser)
                            enemy["health"] -= 10 * player_power
                            if enemy["health"] <= 0:
                                enemies.remove(enemy)
                                kills += 1
                                score_multiplier = min(3, score_multiplier + 0.2)
                                combo_timer = 120
                                score += int(15 * level * score_multiplier)
                                spawn_powerup(enemy["rect"].centerx, enemy["rect"].centery)
                                particles.extend([create_particle(enemy["rect"].centerx, enemy["rect"].centery, laser_colors[enemy["type"]], 5, 20) for _ in range(10)])
                                screen_shake = max(screen_shake, 5)
                            else:
                                score_multiplier = 1
                                combo_timer = 0

                    if enemy["rect"].colliderect(player) and player_invincible <= 0:
                        enemies.remove(enemy)
                        damage = 20 if player_shield <= 0 else max(0, player_shield - 20)
                        player_shield = max(0, player_shield - 20)
                        player_health -= damage
                        player_invincible = 60
                        score_multiplier = 1
                        combo_timer = 0
                        particles.extend([create_particle(player.centerx, player.centery, (255, 0, 0), 5, 20) for _ in range(15)])
                        screen_shake = max(screen_shake, 8)
                        if player_health <= 0:
                            game_over = True

                for laser, etype in enemy_lasers[:]:
                    laser.y += 6 + level
                    pygame.draw.rect(screen, laser_colors[etype], (laser.x + shake_offset, laser.y, laser.width, laser.height))
                    if laser.y > HEIGHT:
                        enemy_lasers.remove((laser, etype))
                    elif laser.colliderect(player) and player_invincible <= 0:
                        enemy_lasers.remove((laser, etype))
                        damage = 10 if player_shield <= 0 else max(0, player_shield - 10)
                        player_shield = max(0, player_shield - 10)
                        player_health -= damage
                        player_invincible = 60
                        score_multiplier = 1
                        combo_timer = 0
                        particles.extend([create_particle(player.centerx, player.centery, (255, 0, 0), 3, 15) for _ in range(5)])
                        screen_shake = max(screen_shake, 5)
                        if player_health <= 0:
                            game_over = True

                if kills >= kills_to_clear and not portal and level < 5:
                    if level == 3 and not miniboss:
                        miniboss = True
                        enemies.append({
                            "type": "miniboss",
                            "rect": pygame.Rect(WIDTH//2 - 50, 100, 80, 80),
                            "health": 100,
                            "max_health": 100,
                            "speed": 2,
                            "shoot_timer": 0,
                            "pause_timer": 60
                        })
                        show_level_text = True
                        level_intro_timer = 120
                    else:
                        portal = pygame.Rect(WIDTH//2 - 75, 150, 150, 150)

                if portal:
                    screen.blit(portal_img, (portal.x + shake_offset, portal.y))
                    if player.colliderect(portal):
                        level += 1
                        kills = 0
                        kills_to_clear = 10 + level * 2
                        portal = None
                        show_level_text = True
                        level_intro_timer = 120
                        player_lasers.clear()
                        enemy_lasers.clear()
                        enemies.clear()
                        powerups.clear()
                        score_multiplier = 1
                        combo_timer = 0
                        miniboss = False
                        if level == 5:
                            boss_mode = True

                for p in powerups[:]:
                    p["rect"].y += 3
                    screen.blit(powerup_img, (p["rect"].x + shake_offset, p["rect"].y))
                    if p["rect"].colliderect(player):
                        if p["type"] == "health":
                            player_health = min(max_player_health, player_health + 30)
                        elif p["type"] == "power":
                            player_power = min(3, player_power + 1)
                        elif p["type"] == "shield":
                            player_shield = min(50, player_shield + 25)
                        powerups.remove(p)
                        particles.extend([create_particle(p["rect"].centerx, p["rect"].centery, (0, 255, 0), 5, 15) for _ in range(10)])
                        screen_shake = max(screen_shake, 3)
                    if p["rect"].y > HEIGHT:
                        powerups.remove(p)

            if boss_mode and not game_won:
                if not boss_started:
                    boss = pygame.Rect(WIDTH//2 - 50, 100, 100, 100)
                    player.x, player.y = WIDTH//2 - 25, HEIGHT - 100
                    enemies.clear()
                    boss_started = True
                    player_lasers.clear()
                    enemy_lasers.clear()
                    powerups.clear()
                    show_level_text = True
                    level_intro_timer = 120

                if boss:
                    boss_movement_timer += 1
                    if boss_movement_timer > 60:
                        boss.x += random.randint(-60, 60)
                        boss.x = max(50, min(WIDTH - 150, boss.x))
                        boss_movement_timer = 0

                    boss_attack_timer += 1
                    if boss_attack_timer % 100 < 50:
                        if random.randint(0, 60) < 7:
                            for i in range(-2, 3):
                                laser = pygame.Rect(boss.centerx - 2 + i * 20, boss.bottom, 4, 20)
                                boss_lasers.append(laser)
                    else:
                        if boss_attack_timer % 5 == 0:
                            angle = (boss_attack_timer % 360) * math.pi / 180
                            for i in range(4):
                                a = angle + i * math.pi / 2
                                laser = pygame.Rect(boss.centerx - 2, boss.centery - 2, 4, 20)
                                laser.vx = math.cos(a) * 6
                                laser.vy = math.sin(a) * 6
                                boss_lasers.append(laser)

                    screen.blit(boss_img, (boss.x + shake_offset, boss.y))
                    draw_health_bar(boss.x + shake_offset, boss.y - 10, boss_health, max_boss_health, (255, 0, 255))

                    for laser in player_lasers[:]:
                        if laser.colliderect(boss):
                            player_lasers.remove(laser)
                            boss_health -= 5 * player_power
                            particles.extend([create_particle(boss.centerx, boss.centery, (255, 0, 255), 5, 20) for _ in range(10)])
                            if boss_health <= 0:
                                boss = None
                                game_won = True
                                score += int(300 * score_multiplier)
                                particles.extend([create_particle(boss.centerx, boss.centery, (255, 0, 255), 7, 30) for _ in range(40)])
                                screen_shake = max(screen_shake, 15)

                for laser in boss_lasers[:]:
                    if hasattr(laser, "vx"):
                        laser.x += laser.vx
                        laser.y += laser.vy
                    else:
                        laser.y += 8
                    pygame.draw.rect(screen, laser_colors["boss"], (laser.x + shake_offset, laser.y, laser.width, laser.height))
                    if laser.y > HEIGHT or laser.x < 0 or laser.x > WIDTH:
                        boss_lasers.remove(laser)
                    elif laser.colliderect(player) and player_invincible <= 0:
                        boss_lasers.remove(laser)
                        damage = 10 if player_shield <= 0 else max(0, player_shield - 10)
                        player_shield = max(0, player_shield - 10)
                        player_health -= damage
                        player_invincible = 60
                        score_multiplier = 1
                        combo_timer = 0
                        particles.extend([create_particle(player.centerx, player.centery, (255, 0, 0), 3, 15) for _ in range(5)])
                        screen_shake = max(screen_shake, 5)
                        if player_health <= 0:
                            game_over = True

            if player_invincible > 0 and player_invincible % 4 < 2:
                pass
            else:
                screen.blit(player_img, (player.x + shake_offset, player.y))

            screen.blit(font.render(f"Score: {score}", True, (255, 0, 0)), (10, 10))
            screen.blit(font.render(f"Level: {level}", True, (255, 255, 0)), (10, 50))
            screen.blit(font.render(f"Enemies Left: {max(0, kills_to_clear - kills)}", True, (255, 255, 255)), (WIDTH - 150, 10))
            screen.blit(font.render(f"Power: {player_power}x", True, (0, 255, 255)), (10, 90))
            screen.blit(font.render(f"Multiplier: {score_multiplier:.1f}x", True, (255, 165, 0)), (10, 130))
            draw_player_health()

            if game_over:
                high_score = max(high_score, score)
                game_text = big_font.render("GAME OVER", True, (255, 0, 0))
                retry_text = font.render("Press R to Restart", True, (255, 255, 255))
                screen.blit(game_text, (WIDTH//2 - game_text.get_width()//2 + shake_offset, HEIGHT//2 - 50))
                screen.blit(retry_text, (WIDTH//2 - retry_text.get_width()//2 + shake_offset, HEIGHT//2 + 10))
            elif game_won:
                high_score = max(high_score, score)
                game_text = big_font.render("YOU WIN!", True, (0, 255, 0))
                retry_text = font.render("Press R to Restart", True, (255, 255, 255))
                screen.blit(game_text, (WIDTH//2 - game_text.get_width()//2 + shake_offset, HEIGHT//2 - 50))
                screen.blit(retry_text, (WIDTH//2 - retry_text.get_width()//2 + shake_offset, HEIGHT//2 + 10))

        pygame.display.update()
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()
    sys.exit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())