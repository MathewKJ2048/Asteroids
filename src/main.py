import pygame
import math
import random

pygame.init()

height = 720
width = 1200
max_frame_rate = 60

n = 0
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


class Missile:
    sprite = pygame.image.load("assets/missile.png")
    target = 0
    x = 0
    y = 0
    v_x = 0
    v_y = 0
    theta = 0
    omega = 0
    alpha = 0
    a = 0.0005
    angular_sensitivity = 0.001
    terminal_angular_velocity = 0.5
    terminal_linear_velocity = 0.5
    bv = a / terminal_linear_velocity
    bw = angular_sensitivity / terminal_angular_velocity

    is_valid = True

    def __init__(self, x, y, theta, target):
        self.theta = theta
        self.target = target
        self.x = x
        self.y = y


class Spaceship:
    sprite = pygame.image.load("assets/spaceship_7.png")
    bullet_sprite = pygame.image.load("assets/bullet_flame.png")
    name = ""

    x = 400
    y = 550
    v_x = 0
    v_y = 0
    theta = 0
    omega = 0
    alpha = 0
    linear_sensitivity = 0.0005
    a = 0
    angular_sensitivity = 0.001
    terminal_angular_velocity = 0.5
    terminal_linear_velocity = 0.5
    bv = linear_sensitivity / terminal_linear_velocity
    bw = angular_sensitivity / terminal_angular_velocity

    collisions = 0
    hits = 0
    missile_hits = 0

    max_fire = 4
    avg_fire_rate = 0.001
    capacity = max_fire
    missiles = 3

    def __init__(self, name, sprite_path, x, y):
        self.name = name
        self.sprite = pygame.image.load(sprite_path)
        self.x = x
        self.y = y


def missile(missile, dt):
    prediction = 0
    y = missile.target.y + missile.target.v_y * dt * prediction
    x = missile.target.x + missile.target.v_x * dt * prediction
    t = math.degrees(math.atan2((missile.y - y), (missile.x - x)))
    u = missile.theta % 360
    m = abs((t + u - 90) % 360)
    x = m - 360 if m > 180 else m
    missile.alpha = missile.angular_sensitivity if x < 0 else -missile.angular_sensitivity

    d_v_x = (missile.a * -math.sin(math.radians(missile.theta)) - missile.bv * missile.v_x) * dt
    d_v_y = (missile.a * -math.cos(math.radians(missile.theta)) - missile.bv * missile.v_y) * dt
    d_omega = (missile.alpha - missile.bw * missile.omega) * dt

    missile.v_x += d_v_x
    missile.v_y += d_v_y
    missile.omega += d_omega

    missile.theta += missile.omega * dt
    missile.x += missile.v_x * dt
    missile.y += missile.v_y * dt

    if missile.x >= width or missile.x <= 0:
        if missile.x < 0:
            missile.x = 0
        if missile.x > width:
            missile.x = width
        missile.v_x = -missile.v_x
    if missile.y >= height or missile.y <= 0:
        if missile.y < 0:
            missile.y = 0
        if missile.y > height:
            missile.y = height
        missile.v_y = -missile.v_y

    img = pygame.transform.rotate(missile.sprite, missile.theta)
    rect = img.get_rect()
    screen.blit(img, (missile.x - (rect.width / 2), (missile.y - rect.height / 2)))


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


def collide_missile_bullet(b, m):
    dist = abs(b.x - m.x) + abs(b.y - m.y)
    if dist <= 0.9 * m.sprite.get_rect().width:
        m.is_valid = False
        b.is_valid = False


def collide_missile_asteroid(a, m):
    dist = abs(a.x - m.x) + abs(a.y - m.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        a.is_valid = False
        m.is_valid = False


def collide_missile_spaceship(m, s):
    dist = abs(m.x - s.x) + abs(m.y - s.y)
    if dist <= 0.9 * s.sprite.get_rect().width and s == m.target:
        m.is_valid = False
        s.missile_hits += 1
        print("explosion!! - spaceship "+s.name)


def collide_bullet_asteroid(b, a):
    dist = abs(b.x - a.x) + abs(b.y - a.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        b.is_valid = False
        a.is_valid = False


def collide_bullet_spaceship(b, p):
    if b.origin == p:
        return
    dist = abs(b.x - p.x) + abs(b.y - p.y)
    if dist <= 0.9 * p.sprite.get_rect().width:
        b.is_valid = False
        p.hits += 1
        print("hit! - spaceship " + p.name)


def collide_asteroid_spaceship(a, p):
    dist = abs(a.x - p.x) + abs(a.y - p.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        a.is_valid = False
        p.collisions += 1
        print("collision! - spaceship " + p.name)


def spaceship(spaceship, dt):
    d_v_x = (spaceship.a * -math.sin(math.radians(spaceship.theta)) - spaceship.bv * spaceship.v_x) * dt
    d_v_y = (spaceship.a * -math.cos(math.radians(spaceship.theta)) - spaceship.bv * spaceship.v_y) * dt
    d_omega = (spaceship.alpha - spaceship.bw * spaceship.omega) * dt

    spaceship.v_x += d_v_x
    spaceship.v_y += d_v_y
    spaceship.omega += d_omega

    spaceship.theta += spaceship.omega * dt
    spaceship.x += spaceship.v_x * dt
    spaceship.y += spaceship.v_y * dt

    if spaceship.x >= width or spaceship.x <= 0:
        if spaceship.x < 0:
            spaceship.x = 0
        if spaceship.x > width:
            spaceship.x = width
        spaceship.v_x = -spaceship.v_x
    if spaceship.y >= height or spaceship.y <= 0:
        if spaceship.y < 0:
            spaceship.y = 0
        if spaceship.y > height:
            spaceship.y = height
        spaceship.v_y = -spaceship.v_y

    spaceship.capacity += spaceship.avg_fire_rate * dt
    if spaceship.capacity > spaceship.max_fire:
        spaceship.capacity = spaceship.max_fire

    img = pygame.transform.rotate(spaceship.sprite, spaceship.theta)
    rect = img.get_rect()
    screen.blit(img, (spaceship.x - (rect.width / 2), (spaceship.y - rect.height / 2)))


c = pygame.time.Clock()

p = Spaceship("P", "assets/spaceship_3.png", width / 4, height / 2)
q = Spaceship("Q", "assets/spaceship_2.png", 3 * width / 4, height / 2)

q.bullet_sprite = pygame.image.load("assets/bullet_blue.png")
asteroids = list()
bullets = list()
missiles = list()
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
                if p.capacity > 1:
                    bullets.append(Bullet(p, p.bullet_sprite, p.theta, p.x, p.y))
                    p.capacity -= 1
            elif event.key == pygame.K_m:
                if p.missiles > 0:
                    missiles.append(Missile(p.x, p.y, p.theta, q))
                    p.missiles -= 1
            elif event.key == pygame.K_a:
                q.alpha = q.angular_sensitivity
            elif event.key == pygame.K_d:
                q.alpha = -q.angular_sensitivity
            elif event.key == pygame.K_w:
                q.a = q.linear_sensitivity
            elif event.key == pygame.K_s:
                q.a = -q.linear_sensitivity
            elif event.key == pygame.K_g:
                if q.capacity > 1:
                    bullets.append(Bullet(q, q.bullet_sprite, q.theta, q.x, q.y))
                    q.capacity -= 1
            elif event.key == pygame.K_t:
                if q.missiles > 0:
                    missiles.append(Missile(q.x, q.y, q.theta, p))
                    q.missiles -= 1

    screen.fill((0, 0, 0))

    spaceship(p, dt)
    spaceship(q, dt)
    for m in missiles:
        for b in bullets:
            collide_missile_bullet(b, m)
        for a in asteroids:
            collide_missile_asteroid(a, m)
        collide_missile_spaceship(m, p)
        collide_missile_spaceship(m, q)
        if not m.is_valid:
            missiles.remove(m)
        missile(m, dt)
    for a in asteroids:
        collide_asteroid_spaceship(a, p)
        collide_asteroid_spaceship(a, q)
        if not a.is_valid:
            asteroids.remove(a)
        asteroid(a, dt)
    for b in bullets:
        collide_bullet_spaceship(b, p)
        collide_bullet_spaceship(b, q)
        if not b.is_valid:
            bullets.remove(b)
        bullet(b, dt)
    for a in asteroids:
        for b in bullets:
            collide_bullet_asteroid(b, a)

    pygame.display.update()
    pass
