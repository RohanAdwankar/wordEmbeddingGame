import pygame
import numpy as np
import random
from gensim.models import KeyedVectors
from math import cos, sin, radians
import time

pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Game Design Constants
ASTEROID_SPAWN_RATE_PERSECOND = 1
ANGLE_CHANGE_MULTIPLIER = 5

print("Loading word vectors... (this may take a minute)")
word_vectors = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin.gz', binary=True)
print("Word vectors loaded!")

class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3
        self.angle = 0
        self.size = 20
        self.lives = 5

    def move(self):
        self.x += cos(radians(self.angle)) * self.speed
        self.y -= sin(radians(self.angle)) * self.speed
        
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        points = [
            (self.x + self.size * cos(radians(self.angle)),
             self.y - self.size * sin(radians(self.angle))),
            (self.x + self.size * cos(radians(self.angle + 140)),
             self.y - self.size * sin(radians(self.angle + 140))),
            (self.x + self.size * cos(radians(self.angle - 140)),
             self.y - self.size * sin(radians(self.angle - 140)))
        ]
        pygame.draw.polygon(screen, GREEN, points, 2)

    def check_collision(self, asteroid):
        distance = ((self.x - asteroid.x) ** 2 + (self.y - asteroid.y) ** 2) ** 0.5
        return distance < (self.size + asteroid.size)

class Asteroid:
    def __init__(self):
        side = random.choice(['left', 'right', 'top', 'bottom'])
        if side == 'left':
            self.x = -20
            self.y = random.randint(0, HEIGHT)
            self.dx = random.uniform(1, 3)
            self.dy = random.uniform(-2, 2)
        elif side == 'right':
            self.x = WIDTH + 20
            self.y = random.randint(0, HEIGHT)
            self.dx = random.uniform(-3, -1)
            self.dy = random.uniform(-2, 2)
        elif side == 'top':
            self.x = random.randint(0, WIDTH)
            self.y = -20
            self.dx = random.uniform(-2, 2)
            self.dy = random.uniform(1, 3)
        else:
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + 20
            self.dx = random.uniform(-2, 2)
            self.dy = random.uniform(-3, -1)
        
        self.size = random.randint(10, 30)

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def is_offscreen(self):
        return (self.x < -50 or self.x > WIDTH + 50 or 
                self.y < -50 or self.y > HEIGHT + 50)

    def draw(self, screen):
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), self.size, 2)

def get_angle_between_words(word1, word2):
    try:
        similarity = word_vectors.similarity(word1.lower(), word2.lower())
        angle = np.arccos(np.clip(similarity, -1.0, 1.0)) * (180/np.pi) * ANGLE_CHANGE_MULTIPLIER
        return angle%360
    except KeyError:
        return None 

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def main():
    # Setup
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Word Space Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    try:
        with open('highscore.txt', 'r') as f:
            high_score = float(f.read())
    except:
        high_score = 0
    
    seed_word = input("Enter a seed word to start: ").strip()
    while seed_word not in word_vectors:
        print("Word not found in vocabulary. Try another word:")
        seed_word = input().strip()

    ship = Ship(WIDTH//2, HEIGHT//2)
    asteroids = []
    asteroid_spawn_timer = 0
    current_word = seed_word
    input_text = ""
    game_over = False
    
    countdown = 3
    countdown_start = time.time()
    game_started = False
    start_time = None

    running = True
    while running:
        current_time = time.time()
        
        # Handle countdown
        if not game_started:
            if current_time - countdown_start >= 1:
                countdown -= 1
                countdown_start = current_time
                if countdown < 0:
                    game_started = True
                    start_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and game_started:
                if not game_over:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip() in word_vectors:
                            angle = get_angle_between_words(current_word, input_text.strip())
                            if angle is not None:
                                ship.angle = angle
                                current_word = input_text.strip()
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        screen.fill(BLACK)
        if not game_started:
            # Draw countdown
            countdown_text = font.render(str(countdown + 1), True, GREEN)
            screen.blit(countdown_text, (WIDTH//2 - countdown_text.get_width()//2, 
                                     HEIGHT//2 - countdown_text.get_height()//2))
        else:
            if not game_over:
                ship.move()

                asteroid_spawn_timer += 1
                if asteroid_spawn_timer >= FPS * ASTEROID_SPAWN_RATE_PERSECOND:
                    asteroids.append(Asteroid())
                    asteroid_spawn_timer = 0

                for asteroid in asteroids[:]:
                    asteroid.move()
                    if asteroid.is_offscreen():
                        asteroids.remove(asteroid)
                    elif ship.check_collision(asteroid):
                        asteroids.remove(asteroid)
                        ship.lives -= 1
                        if ship.lives <= 0:
                            game_over = True
                            final_time = current_time - start_time
                            if final_time > high_score:
                                high_score = final_time
                                with open('highscore.txt', 'w') as f:
                                    f.write(str(high_score))

            ship.draw(screen)
            for asteroid in asteroids:
                asteroid.draw(screen)

            lives_text = font.render(f"Lives: {ship.lives}", True, GREEN)
            screen.blit(lives_text, (10, 10))
            
            word_text = font.render(f"Current Word: {current_word}", True, GREEN)
            screen.blit(word_text, (10, 50))
            
            if start_time is not None:
                time_text = font.render(f"Time: {format_time(current_time - start_time)}", True, GREEN)
                screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 10))
            
            high_score_text = font.render(f"Best: {format_time(high_score)}", True, GREEN)
            screen.blit(high_score_text, (WIDTH - 150, 10))
            
            input_surface = font.render(f"Input: {input_text}", True, GREEN)
            screen.blit(input_surface, (10, HEIGHT - 40))

            if game_over:
                final_time_text = font.render(f"Final Time: {format_time(current_time - start_time)}", True, GREEN)
                high_score_text = font.render(f"Best Time: {format_time(high_score)}", True, GREEN)
                game_over_text = font.render("GAME OVER - Press R to restart or Q to quit", True, RED)
                
                screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 
                                           HEIGHT//2 - game_over_text.get_height()//2))
                screen.blit(final_time_text, (WIDTH//2 - final_time_text.get_width()//2, 
                                            HEIGHT//2 + 40))
                screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, 
                                            HEIGHT//2 + 80))
                
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]:
                    ship = Ship(WIDTH//2, HEIGHT//2)
                    asteroids = []
                    asteroid_spawn_timer = 0
                    current_word = seed_word
                    input_text = ""
                    game_over = False
                    countdown = 3
                    countdown_start = time.time()
                    game_started = False
                    start_time = None
                elif keys[pygame.K_q]:
                    running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()