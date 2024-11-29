import pygame
import numpy as np
import random
from gensim.models import KeyedVectors
import sys
from math import cos, sin, radians

pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Game Design Constants
ASTEROID_SPAWN_RATE_PERSECOND = 2
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
        
        # Wrap around screen idk if this the move
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
        pygame.draw.polygon(screen, WHITE, points)

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
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size)

def get_angle_between_words(word1, word2):
    try:
        similarity = word_vectors.similarity(word1.lower(), word2.lower())
        angle = np.arccos(np.clip(similarity, -1.0, 1.0)) * (180/np.pi) * ANGLE_CHANGE_MULTIPLIER
        return angle%360
    except KeyError:
        return None 

def main():
    # Setup
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Word Space Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
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

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
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

        screen.fill(BLACK)
        
        ship.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)

        lives_text = font.render(f"Lives: {ship.lives}", True, WHITE)
        screen.blit(lives_text, (10, 10))
        
        word_text = font.render(f"Current Word: {current_word}", True, WHITE)
        screen.blit(word_text, (10, 50))
        
        input_surface = font.render(f"Input: {input_text}", True, WHITE)
        screen.blit(input_surface, (10, HEIGHT - 40))

        if game_over:
            game_over_text = font.render("GAME OVER - Close window to exit", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 
                                       HEIGHT//2 - game_over_text.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()