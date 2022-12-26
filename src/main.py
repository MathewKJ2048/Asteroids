import pygame
import math
import random

pygame.init()

height = 720
width = 1200
max_frame_rate = 60

n = 16
max_asteroid_velocity = 0.16
max_asteroid_angular_velocity = 0.4

screen = pygame.display.set_mode((width, height))

pygame.display.set_caption("Space Invaders")
icon = pygame.image.load("assets/spaceship_cyan.png")
pygame.display.set_icon(icon)

# all distances are in pixels
# all angles are in degrees
# all time is in milliseconds

asteroid_colors = ["grey", "blue", "red"]


class Asteroid:
    size = 2
    sprite = 0
    color = -1
    x = 200
    y = 200
    theta = 0
    v_x = 0
    v_y = 0
    omega = 0
    is_valid = True
    to_split = False

    def __init__(self, sprite_path, color):
        self.sprite = pygame.image.load(sprite_path)
        self.color = color


class Bullet:
    sprite = 0
    x = 0
    y = 0
    v = 0.8
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

    def __init__(self, source, target):
        self.theta = source.theta
        self.target = target
        self.x = source.x
        self.y = source.y
        self.v_x = source.v_x
        self.v_y = source.v_y


class Spaceship:
    sprite = pygame.image.load("assets/spaceship_cyan.png")
    bullet_sprite = pygame.image.load("assets/bullet_blue.png")
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

    collisions_large = 0
    collisions_small = 0
    hits = 0
    missile_hits = 0

    is_valid = True

    max_fire = 4
    avg_fire_rate = 0.001
    capacity = max_fire
    missiles = 3

    def __init__(self, name, sprite_path, x, y):
        self.name = name
        self.sprite = pygame.image.load(sprite_path)
        self.x = x
        self.y = y

    def __health__(self):
        h = 1 - 0.2 * self.hits - 0.4 * self.collisions_large - 0.2 * self.collisions_small - 0.8 * self.missile_hits
        if h >= 0:
            return h
        return 0

    def __capacity__(self):
        return self.capacity / self.max_fire if self.__health__() > 0 else 0


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
    missile.theta %= 360
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
    asteroid.theta %= 360

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
    if dist <= 0.5 * (m.sprite.get_rect().width + m.sprite.get_rect().height):
        m.is_valid = False
        b.is_valid = False


def collide_missile_asteroid(a, m):
    dist = abs(a.x - m.x) + abs(a.y - m.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        a.is_valid = False
        m.is_valid = False
        a.to_split = True


def collide_missile_spaceship(m, s):
    if not s.is_valid:
        return
    dist = abs(m.x - s.x) + abs(m.y - s.y)
    if dist <= 0.9 * s.sprite.get_rect().width and s == m.target:
        m.is_valid = False
        s.missile_hits += 1


def collide_missile_missile(m2, m1):
    dist = abs(m2.x - m1.x) + abs(m2.y - m1.y)
    if dist <= m1.sprite.get_rect().width:
        m1.is_valid = False
        m2.is_valid = False


def collide_bullet_asteroid(b, a):
    dist = abs(b.x - a.x) + abs(b.y - a.y)
    if dist <= 0.9 * a.sprite.get_rect().width:
        b.is_valid = False
        a.is_valid = False
        if a.size == 2:
            a.to_split = True


def collide_bullet_spaceship(b, p):
    if b.origin == p or not p.is_valid:
        return
    dist = abs(b.x - p.x) + abs(b.y - p.y)
    if dist <= 0.9 * p.sprite.get_rect().width:
        b.is_valid = False
        p.hits += 1


def collide_asteroid_spaceship(a, p):
    if not p.is_valid:
        return
    dist = abs(a.x - p.x) + abs(a.y - p.y)
    if dist <= a.sprite.get_rect().width:
        a.is_valid = False
        if a.size == 2:
            p.collisions_large += 1
        elif a.size == 1:
            p.collisions_small += 1


def breakup(asteroid, v):
    angle = 30
    x = list()
    a1 = Asteroid("assets/asteroid_" + asteroid_colors[int(asteroid.color)] + "_small.png", asteroid.color)
    a2 = Asteroid("assets/asteroid_" + asteroid_colors[int(asteroid.color)] + "_small.png", asteroid.color)
    a1.x = asteroid.x
    a2.x = asteroid.x
    a1.y = asteroid.y
    a2.y = asteroid.y
    theta = math.degrees(math.atan2(asteroid.v_y, asteroid.v_x))
    a1.v_x = v * math.cos(math.radians(theta+angle))
    a2.v_x = v * math.cos(math.radians(theta-angle))
    a1.v_y = v * math.sin(math.radians(theta+angle))
    a2.v_y = v * math.sin(math.radians(theta-angle))
    a1.color = asteroid.color
    a2.color = asteroid.color
    a1.size = 1
    a2.size = 1
    x.append(a1)
    x.append(a2)
    return x


def meter(t, x, y, fore_color, back_color, border_color):  # t is a real number between 0 and 1, x and y are centres
    length = 80
    width = 5
    border = 2
    l = length + 2 * border
    w = width + 2 * border
    pygame.draw.rect(screen,
                     border_color,
                     pygame.Rect((x - l / 2, y - w / 2), (l, w)),
                     0)
    l_filled = t * length
    l_empty = (1 - t) * length
    pygame.draw.rect(screen,
                     fore_color,
                     pygame.Rect((x - length / 2, y - width / 2), (l_filled, width)),
                     0)
    pygame.draw.rect(screen,
                     back_color,
                     pygame.Rect((x - length / 2 + l_filled, y - width / 2), (l_empty, width)),
                     0)


def spaceship(spaceship, dt):
    if not spaceship.is_valid:
        return

    d_v_x = (spaceship.a * -math.sin(math.radians(spaceship.theta)) - spaceship.bv * spaceship.v_x) * dt
    d_v_y = (spaceship.a * -math.cos(math.radians(spaceship.theta)) - spaceship.bv * spaceship.v_y) * dt
    d_omega = (spaceship.alpha - spaceship.bw * spaceship.omega) * dt

    spaceship.v_x += d_v_x
    spaceship.v_y += d_v_y
    spaceship.omega += d_omega

    spaceship.theta += spaceship.omega * dt
    spaceship.theta %= 360
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

p = Spaceship("P", "assets/spaceship_cyan.png", 3*width / 4, height / 2)
q = Spaceship("Q", "assets/spaceship_orange.png", width / 4, height / 2)

q.bullet_sprite = pygame.image.load("assets/bullet_red.png")
asteroids = list()
bullets = list()
missiles = list()
for i in range(n):
    color = (random.random() * 1000) % 3
    a = Asteroid("assets/asteroid_" + asteroid_colors[int(color)] + ".png", color)
    a.x = width / 2
    a.y = ((i + 0.5) / n) * height
    v = (2 * random.random() - 1) * max_asteroid_velocity
    theta = random.random() * 360
    a.v_x = v * math.sin(math.radians(theta))
    a.v_y = v * math.cos(math.radians(theta))
    a.omega = (2 * random.random() - 1) * max_asteroid_angular_velocity
    asteroids.append(a)

running = True
while running:

    dt = c.tick(max_frame_rate)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP:
            if p.is_valid:
                if event.key == pygame.K_j or event.key == pygame.K_l:
                    p.alpha = 0
                elif event.key == pygame.K_i or event.key == pygame.K_k:
                    p.a = 0
            if q.is_valid:
                if event.key == pygame.K_a or event.key == pygame.K_d:
                    q.alpha = 0
                elif event.key == pygame.K_w or event.key == pygame.K_s:
                    q.a = 0

        if event.type == pygame.KEYDOWN:
            if p.is_valid:
                if event.key == pygame.K_j:
                    p.alpha = p.angular_sensitivity
                elif event.key == pygame.K_l:
                    p.alpha = -p.angular_sensitivity
                elif event.key == pygame.K_i:
                    p.a = p.linear_sensitivity
                elif event.key == pygame.K_k:
                    p.a = -p.linear_sensitivity
                elif event.key == pygame.K_m:
                    if p.capacity > 1:
                        bullets.append(Bullet(p, p.bullet_sprite, p.theta, p.x, p.y))
                        p.capacity -= 1
                elif event.key == pygame.K_COMMA and p.capacity == 4:
                    if p.missiles > 0:
                        missiles.append(Missile(p, q))
                        p.missiles -= 1
                        p.capacity -= 4
            if q.is_valid:
                if event.key == pygame.K_a:
                    q.alpha = q.angular_sensitivity
                elif event.key == pygame.K_d:
                    q.alpha = -q.angular_sensitivity
                elif event.key == pygame.K_w:
                    q.a = q.linear_sensitivity
                elif event.key == pygame.K_s:
                    q.a = -q.linear_sensitivity
                elif event.key == pygame.K_z:
                    if q.capacity > 1:
                        bullets.append(Bullet(q, q.bullet_sprite, q.theta, q.x, q.y))
                        q.capacity -= 1
                elif event.key == pygame.K_x:
                    if q.missiles > 0 and q.capacity == 4:
                        missiles.append(Missile(q, p))
                        q.missiles -= 1
                        q.capacity -= 4

    screen.fill((0, 0, 0))

    # movement
    spaceship(p, dt)
    spaceship(q, dt)
    for m in missiles:
        missile(m, dt)
    for a in asteroids:
        asteroid(a, dt)
        if a.color == "":
            print("error")
    for b in bullets:
        bullet(b, dt)

    # collision checking
    for m in missiles:
        for m_ in missiles:
            if m_ != m:
                collide_missile_missile(m, m_)
        for b in bullets:
            collide_missile_bullet(b, m)
        for a in asteroids:
            collide_missile_asteroid(a, m)
        collide_missile_spaceship(m, p)
        collide_missile_spaceship(m, q)

    for a in asteroids:
        for b in bullets:
            collide_bullet_asteroid(b, a)
        collide_asteroid_spaceship(a, p)
        collide_asteroid_spaceship(a, q)

    for b in bullets:
        collide_bullet_spaceship(b, p)
        collide_bullet_spaceship(b, q)

    # consequences
    for m in missiles:
        if not m.is_valid:
            missiles.remove(m)
    for b in bullets:
        if not b.is_valid:
            bullets.remove(b)
    for a in asteroids:
        if not a.is_valid:
            if a.to_split:
                st = breakup(a, max_asteroid_velocity)
                for s in st:
                    asteroids.append(s)
            asteroids.remove(a)
    if p.__health__() == 0:
        p.is_valid = False
    if q.__health__() == 0:
        q.is_valid = False

    x_offset = 60
    meter(p.__health__(), width - x_offset, 20, (0, 255, 0), (255, 0, 0), (160, 160, 160))
    meter(p.__capacity__(), width - x_offset, 40, (255, 255, 0), (96, 96, 0), (160, 160, 160))
    meter(q.__health__(), x_offset, 20, (0, 255, 0), (255, 0, 0), (160, 160, 160))
    meter(q.__capacity__(), x_offset, 40, (255, 255, 0), (96, 96, 0), (160, 160, 160))

    pygame.display.update()
    pass
