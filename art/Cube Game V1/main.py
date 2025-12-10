import pygame
import random

# Initialize pygame
pygame.init()

# Initialize pygame mixer
pygame.mixer.init()

# Load the song
pygame.mixer.music.load("Song.mp3")

# Play the song in a loop
pygame.mixer.music.play(-1)

# Set the screen size
screen = pygame.display.set_mode((800, 600))

# Set the title of the window
pygame.display.set_caption("Cube Game")

# Create a cube object
cube = pygame.Surface((50, 50))
cube.fill((255, 0, 0))

# Create a obstacle object
obstacle = pygame.Surface((50, 50))
obstacle.fill((0, 0, 255))

# Set the initial position of the cube
x = 400
y = 300

# Create a list to store obstacles
obstacles = []

# Set the initial position of the obstacle
ob_x = 200
ob_y = 200

# Set the spawn time for obstacles
spawn_time = pygame.time.get_ticks()

# Create a font object
font = pygame.font.Font(None, 36)

# Create a score variable
score = 0

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check the state of the keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        y -= 0.3
    if keys[pygame.K_a]:
        x -= 0.3
    if keys[pygame.K_s]:
        y += 0.3
    if keys[pygame.K_d]:
        x += 0.3
    if x < 0:
        x = 0
    if x > 750:
        x = 750
    if y < 0:
        y = 0
    if y > 550:
        y = 550

    respawn = False
    # Check collision with obstacle
    for ob in obstacles:
        if x + 50 > ob[0] and x < ob[0] + 50 and y + 50 > ob[1] and y < ob[1] + 50:
            # Change variable to True to indicate player died
            respawn = True
            break
    if respawn:
        keys = pygame.key.get_pressed()
        text = font.render("You died! Press space to respawn", True, (255, 0, 0))
        screen.blit(text, (200, 300))
        pygame.display.flip()
        while not keys[pygame.K_SPACE]:
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        x = 400
        y = 300
        obstacles = []
        score = 0
        continue

        # Spawn obstacles every 5 seconds and increment score
    if pygame.time.get_ticks() - spawn_time > 5000:
        spawn_time = pygame.time.get_ticks()
        ob_x = random.randint(0, 750)
        ob_y = random.randint(0, 550)
        obstacles.append([ob_x, ob_y])
        score += 1

        # Move obstacles towards the player
    for ob in obstacles:
        if ob[0] > x:
            ob[0] = ob[0] - 0.1
        if ob[0] < x:
            ob[0] = ob[0] + 0.1
        if ob[1] > y:
            ob[1] = ob[1] - 0.1
        if ob[1] < y:
            ob[1] = ob[1] + 0.1

        # Clear the screen
    screen.fill((0, 0, 0))

    # Draw the cube
    screen.blit(cube, (x, y))

    # Draw the obstacles
    for ob in obstacles:
        screen.blit(obstacle, (ob[0], ob[1]))

    # Draw the score
    score_text = font.render("Score: " + str(score), True, (255, 255, 255))
    screen.blit(score_text, (5, 5))

    # Update the screen
    pygame.display.flip()

# Quit pygame and mixer
pygame.quit()
pygame.mixer.quit()