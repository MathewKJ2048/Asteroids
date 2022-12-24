import pygame
import math
import random

pygame.init()

height = 720
width = 1200
max_frame_rate = 60

n = 25
max_asteroid_velocity = 0.2 / math.sqrt(2)
max_asteroid_angular_velocity = 0.5 / math.sqrt(2)

screen = pygame.display.set_mode((width, height))

pygame.display.set_caption("Space Invaders")
icon = pygame.image.load("assets/spaceship_7.png")
pygame.display.set_icon(icon)


# all distances are in pixels
# all angles are in degrees
# all time is in milliseconds


class Asteroid:
    sprite = pygame.image.load("assets/asteroid.png")
    x = 200
    y = 200
    theta = 0
    v_x = 0
    v_y = 0
    omega = 0
    is_valid = True


class Bullet:
    sprite = pygame.image.load("assets/bullet_blue.png")
    x = 0
    y = 0
    v = 0.5
    theta = 0
    is_valid = True
    origin = 0

    def __init__(self, origin, sprite, theta, x, y):
        self.origin = origin
        self.sprite = sprite
        self.theta = theta
        self.x = x
        self.y = y


class Player:
    sprite = pygame.image.load("assets/spaceship_7.png")
    bullet_sprite = pygame.image.load("assets/bullet_flame.png")
    name = ""

    x = 400
    y = 550
    v_x = 0
    v_y = 0
    a = 0
    theta = 0
    omega = 0
    alpha = 0
    linear_sensitivity = 0.0005
    angular_sensitivity = 0.001
    terminal_angular_velocity = 0.5
    terminal_linear_velocity = 0.5
    bv = linear_sensitivity / terminal_linear_velocity
    bw = angular_sensitivity / terminal_angular_velocity

    collisions = 0
    hits = 0

    max_fire = 4
    avg_fire_rate = 0.001
    capacity = max_fire


    def __init__(self, name, sprite_path, x, y):
        self.name = name
        self.sprite = pygame.image.load(sprite_path)
        self.x = x
        self.y = y


def bullet(bullet, dt):
    if not bullet.is_valid:
        return
    bullet.x += bullet.v * -math.sin(math.radians(bullet.theta)) * dt
    bullet.y += bullet.v * -math.cos(math.radians(bullet.theta)) * dt

    if bullet.x >= width or bullet.x <= 0 or bullet.y >= height or bullet.y <= 0:
        bullet.is_valid = False

    img = pygame.transform.rotate(bullet.sprite, bullet.theta)
    rect = img.get_rect()
    screen.blit(img, (bullet.x - (rect.width / 2), (bullet.y - rect.height / 2)))


def asteroid(asteroid, dt):
    asteroid.x += asteroid.v_x * dt
    asteroid.y += asteroid.v_y * dt
    asteroid.theta += asteroid.omega * dt

    if asteroid.x >= width or asteroid.x <= 0:
        if asteroid.x < 0:
            asteroid.x = 0
        if asteroid.x > width:
            asteroid.x = width
        asteroid.v_x = -asteroid.v_x
    if asteroid.y >= height or asteroid.y <= 0:
        if asteroid.y < 0:
            asteroid.y = 0
        if asteroid.y > height:
            asteroid.y = height
        asteroid.v_y = -asteroid.v_y

    img = pygame.transform.rotate(asteroid.sprite, asteroid.theta)
    rect = img.get_rect()
    screen.blit(img, (asteroid.x - (rect.width / 2), (asteroid.y - rect.height / 2)))


def collide_bullet_asteroid(b, a):
    dist = abs(b.x - a.x) + abs(b.y - a.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        b.is_valid = False
        a.is_valid = False


def collide_bullet_player(b, p):
    if b.origin == p:
        return
    dist = abs(b.x - p.x) + abs(b.y - p.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        b.is_valid = False
        p.hits += 1
        print("hit! - player " + p.name)


def collide_asteroid_player(a, p):
    dist = abs(a.x - p.x) + abs(a.y - p.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        a.is_valid = False
        p.collisions += 1
        print("collision! - player "+p.name)


def player(player, dt):
    d_v_x = (player.a * -math.sin(math.radians(player.theta)) - player.bv * player.v_x) * dt
    d_v_y = (player.a * -math.cos(math.radians(player.theta)) - player.bv * player.v_y) * dt
    d_omega = (player.alpha - player.bw * player.omega) * dt

    player.v_x += d_v_x
    player.v_y += d_v_y
    player.omega += d_omega

    player.theta += player.omega * dt
    player.x += player.v_x * dt
    player.y += player.v_y * dt

    if player.x >= width or player.x <= 0:
        if player.x < 0:
            player.x = 0
        if player.x > width:
            player.x = width
        player.v_x = -player.v_x
    if player.y >= height or player.y <= 0:
        if player.y < 0:
            player.y = 0
        if player.y > height:
            player.y = height
        player.v_y = -player.v_y

    player.capacity += player.avg_fire_rate*dt
    if player.capacity > player.max_fire:
        player.capacity = player.max_fire

    img = pygame.transform.rotate(player.sprite, player.theta)
    rect = img.get_rect()
    screen.blit(img, (player.x - (rect.width / 2), (player.y - rect.height / 2)))


c = pygame.time.Clock()

p = Player("P","assets/spaceship_1.png", width / 4, height / 2)
q = Player("Q","assets/spaceship_2.png", 3 * width / 4, height / 2)
q.bullet_sprite = pygame.image.load("assets/bullet_blue.png")
asteroids = list()
bullets = list()
for i in range(n):
    a = Asteroid()
    a.x = width / 2
    a.y = ((i + 0.5) / n) * height
    a.v_x = (2 * random.random() - 1) * max_asteroid_velocity
    a.v_y = (2 * random.random() - 1) * max_asteroid_velocity
    a.omega = (2 * random.random() - 1) * max_asteroid_angular_velocity
    asteroids.append(a)

running = True
while running:

    dt = c.tick(max_frame_rate)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                p.alpha = 0
            elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                p.a = 0
            elif event.key == pygame.K_a or event.key == pygame.K_d:
                q.alpha = 0
            elif event.key == pygame.K_w or event.key == pygame.K_s:
                q.a = 0

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                p.alpha = p.angular_sensitivity
            elif event.key == pygame.K_RIGHT:
                p.alpha = -p.angular_sensitivity
            elif event.key == pygame.K_UP:
                p.a = p.linear_sensitivity
            elif event.key == pygame.K_DOWN:
                p.a = -p.linear_sensitivity
            elif event.key == pygame.K_SPACE:
                if p.capacity>1:
                    bullets.append(Bullet(p, p.bullet_sprite, p.theta, p.x, p.y))
                    p.capacity-= 1
            elif event.key == pygame.K_a:
                q.alpha = q.angular_sensitivity
            elif event.key == pygame.K_d:
                q.alpha = -q.angular_sensitivity
            elif event.key == pygame.K_w:
                q.a = q.linear_sensitivity
            elif event.key == pygame.K_s:
                q.a = -q.linear_sensitivity
            elif event.key == pygame.K_g:
                bullets.append(Bullet(q, q.bullet_sprite, q.theta, q.x, q.y))
                q.capacity -= 1

    screen.fill((0, 0, 0))

    player(p, dt)
    player(q, dt)
    for a in asteroids:
        collide_asteroid_player(a, p)
        collide_asteroid_player(a, q)
        if not a.is_valid:
            asteroids.remove(a)
        asteroid(a, dt)
    for b in bullets:
        collide_bullet_player(b, p)
        collide_bullet_player(b, q)
        if not b.is_valid:
            bullets.remove(b)
        bullet(b, dt)
    for a in asteroids:
        for b in bullets:
            collide_bullet_asteroid(b, a)

    pygame.display.update()

    pass
