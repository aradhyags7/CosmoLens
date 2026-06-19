import pygame
import sys
import math
import random
import datetime

pygame.init()

# ============================================================
# WINDOW
# ============================================================

DEFAULT_W = 1400
DEFAULT_H = 850

screen = pygame.display.set_mode(
    (DEFAULT_W, DEFAULT_H),
    pygame.RESIZABLE
)

pygame.display.set_caption(
    "CosmoLens — Mission Control"
)

clock = pygame.time.Clock()

# ============================================================
# RESPONSIVE CARD SETTINGS
# ============================================================

CARD_W = 480
CARD_H = 390
CARD_GAP = 80

# ============================================================
# FONTS
# ============================================================

FONT_TITLE = pygame.font.SysFont(
    "Segoe UI", 68, bold=True
)

FONT_SUB = pygame.font.SysFont(
    "Consolas", 16
)

FONT_CARD = pygame.font.SysFont(
    "Consolas", 30, bold=True
)

FONT_TEXT = pygame.font.SysFont(
    "Consolas", 15
)

FONT_KEY = pygame.font.SysFont(
    "Consolas", 20, bold=True
)

FONT_FOOT = pygame.font.SysFont(
    "Consolas", 12
)

# ============================================================
# COLORS
# ============================================================

CYAN = (0, 220, 255)
GREEN = (80, 255, 180)

WHITE = (240, 250, 255)
DIM = (110, 130, 170)

# ============================================================
# CARDS
# ============================================================

CARDS = [

    {
        "key": "1",

        "title": "STAR ATLAS",

        "subtitle": "Interactive Deep Sky Simulation",

        "color": CYAN,

        "module": "sky_simulation",

        "features": [

            "9 000+ Hipparcos stars",
            "Real spectral colors",
            "Planet rendering (DE421)",
            "Milky Way simulation",
            "Constellations & labels",
            "RA / Dec grid",
            "Twinkling effects",
            "Deep Sky Objects",
            "Search system",
            "Magnitude filters"
        ]
    },

    {
        "key": "2",

        "title": "SATELLITE TRACKER",

        "subtitle": "Real-Time Orbital Visualization",

        "color": GREEN,

        "module": "satellite_tracker",

        "features": [

            "Live TLE satellites",
            "Flat Earth mode",
            "3D globe mode",
            "Orbit path rendering",
            "SGP4 propagation",
            "Satellite telemetry",
            "Day / Night overlay",
            "Footprint calculation",
            "Time warp engine",
            "Satellite filtering"
        ]
    }
]

# ============================================================
# STARS
# ============================================================

class Star:

    def __init__(self):

        self.reset()

    def reset(self):

        self.x = random.randint(0, DEFAULT_W)

        self.y = random.randint(0, DEFAULT_H)

        self.speed = random.uniform(4, 18)

        self.radius = random.uniform(0.5, 2)

        self.phase = random.uniform(
            0,
            math.pi * 2
        )

    def update(self, dt, H):

        self.y += self.speed * dt

        self.phase += dt * 2

        if self.y > H:

            self.y = -5

    def draw(self, surf):

        twinkle = (
            0.7 +
            0.3 * math.sin(self.phase)
        )

        brightness = int(170 * twinkle)

        color = (
            brightness,
            brightness + 20,
            255
        )

        pygame.draw.circle(
            surf,
            color,
            (int(self.x), int(self.y)),
            int(self.radius)
        )

stars = [Star() for _ in range(380)]

# ============================================================
# SHOOTING STARS
# ============================================================

class ShootingStar:

    def __init__(self):

        self.active = False

    def spawn(self, W, H):

        self.active = True

        self.x = random.randint(-100, W)

        self.y = random.randint(0, H // 2)

        self.vx = random.uniform(900, 1300)

        self.vy = random.uniform(180, 350)

        self.life = 1.0

    def update(self, dt):

        if not self.active:
            return

        self.x += self.vx * dt

        self.y += self.vy * dt

        self.life -= dt

        if self.life <= 0:

            self.active = False

    def draw(self, surf, W, H):

        if not self.active:
            return

        tail_x = self.x - 140
        tail_y = self.y - 40

        temp = pygame.Surface(
            (W, H),
            pygame.SRCALPHA
        )

        pygame.draw.line(
            temp,
            (180,220,255,80),
            (self.x, self.y),
            (tail_x, tail_y),
            3
        )

        surf.blit(temp, (0,0))

shoots = [ShootingStar() for _ in range(4)]

shoot_timer = 0

# ============================================================
# HELPERS
# ============================================================

def draw_text(
    surf,
    font,
    text,
    x,
    y,
    color,
    center=False
):

    rendered = font.render(
        text,
        True,
        color
    )

    if center:
        x -= rendered.get_width() // 2

    surf.blit(rendered, (x, y))

def glow(
    surf,
    x,
    y,
    radius,
    color
):

    temp = pygame.Surface(
        (radius * 2, radius * 2),
        pygame.SRCALPHA
    )

    for r in range(radius, 0, -6):

        alpha = int(
            45 * (1 - r / radius)
        )

        pygame.draw.circle(
            temp,
            (*color, alpha),
            (radius, radius),
            r
        )

    surf.blit(
        temp,
        (x - radius, y - radius)
    )

# ============================================================
# BACKGROUND
# ============================================================

def draw_background(surf, dt, t, W, H):

    # cinematic gradient
    for y in range(H):

        ratio = y / H

        r = int(2 + 4 * ratio)
        g = int(8 + 18 * ratio)
        b = int(18 + 40 * ratio)

        pygame.draw.line(
            surf,
            (r, g, b),
            (0, y),
            (W, y)
        )

    # center glow
    glow(
        surf,
        W // 2,
        H // 2,
        420,
        (0, 90, 130)
    )

    # grid
    grid = pygame.Surface(
        (W, H),
        pygame.SRCALPHA
    )

    for x in range(0, W, 80):

        pygame.draw.line(
            grid,
            (0,120,180,10),
            (x,0),
            (x,H),
            1
        )

    for y in range(0, H, 80):

        pygame.draw.line(
            grid,
            (0,120,180,10),
            (0,y),
            (W,y),
            1
        )

    surf.blit(grid, (0,0))

    # stars
    for star in stars:

        star.update(dt, H)

        star.draw(surf)

    # dust particles
    dust = pygame.Surface(
        (W, H),
        pygame.SRCALPHA
    )

    for _ in range(60):

        x = random.randint(0, W)
        y = random.randint(0, H)

        alpha = random.randint(5, 20)

        pygame.draw.circle(
            dust,
            (120,180,255,alpha),
            (x,y),
            1
        )

    surf.blit(dust, (0,0))

    # shooting stars
    global shoot_timer

    shoot_timer += dt

    if shoot_timer > random.uniform(3, 6):

        shoot_timer = 0

        for s in shoots:

            if not s.active:

                s.spawn(W, H)

                break

    for s in shoots:

        s.update(dt)

        s.draw(surf, W, H)

    # vignette
    vignette = pygame.Surface(
        (W, H),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        vignette,
        (0,0,0,110),
        (0,0,W,H)
    )

    pygame.draw.circle(
        vignette,
        (0,0,0,0),
        (W//2, H//2),
        340
    )

    surf.blit(vignette, (0,0))

# ============================================================
# MODULE LAUNCHER
# ============================================================

def launch_module(module_name):

    global screen

    try:

        mod = __import__(module_name)

        mod.main()

        current_size = screen.get_size()

        screen = pygame.display.set_mode(
            current_size,
            pygame.RESIZABLE
        )

        pygame.display.set_caption(
            "CosmoLens — Mission Control"
        )

    except Exception as e:

        print("Launch Error:", e)

# ============================================================
# CARD DRAWER
# ============================================================

def draw_card(
    surf,
    x,
    y,
    card,
    hovered
):

    width = CARD_W
    height = CARD_H

    color = card["color"]

    # glow
    if hovered:

        glow(
            surf,
            x + width // 2,
            y + height // 2,
            180,
            color
        )

    # glass panel
    panel = pygame.Surface(
        (width, height),
        pygame.SRCALPHA
    )

    panel.fill((8, 15, 35, 245))

    surf.blit(panel, (x, y))

    # border
    pygame.draw.rect(
        surf,
        color,
        (x, y, width, height),
        2,
        border_radius=6
    )

    # inner glow
    inner = pygame.Surface(
        (width - 10, height - 10),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        inner,
        (*color, 10),
        (0,0,width-10,height-10),
        border_radius=6
    )

    surf.blit(inner, (x+5, y+5))

    # key box
    pygame.draw.rect(
        surf,
        color,
        (x + 18, y + 18, 36, 36),
        1
    )

    draw_text(
        surf,
        FONT_KEY,
        card["key"],
        x + 30,
        y + 25,
        color,
        center=True
    )

    # title
    draw_text(
        surf,
        FONT_CARD,
        card["title"],
        x + 72,
        y + 18,
        color
    )

    draw_text(
        surf,
        FONT_SUB,
        card["subtitle"],
        x + 72,
        y + 58,
        DIM
    )

    pygame.draw.line(
        surf,
        color,
        (x + 20, y + 92),
        (x + width - 20, y + 92),
        1
    )

    fy = y + 122

    for feature in card["features"]:

        pygame.draw.circle(
            surf,
            color,
            (x + 26, fy + 7),
            3
        )

        draw_text(
            surf,
            FONT_TEXT,
            feature,
            x + 40,
            fy,
            WHITE if hovered else DIM
        )

        fy += 28

# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = min(
        clock.tick(60) / 1000,
        0.05
    )

    # --------------------------------------------------------
    # CURRENT WINDOW SIZE
    # --------------------------------------------------------

    W, H = screen.get_size()

    # --------------------------------------------------------
    # RESPONSIVE CARD POSITIONS
    # --------------------------------------------------------

    total_width = CARD_W * 2 + CARD_GAP

    start_x = (W - total_width) // 2

    card1_x = start_x

    card2_x = (
        start_x +
        CARD_W +
        CARD_GAP
    )

    card_y = (
        H // 2 -
        CARD_H // 2 +
        70
    )

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.VIDEORESIZE:

            screen = pygame.display.set_mode(
                (event.w, event.h),
                pygame.RESIZABLE
            )

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running = False

            elif event.key == pygame.K_1:

                launch_module(
                    "sky_simulation"
                )

            elif event.key == pygame.K_2:

                launch_module(
                    "satellite_tracker"
                )

        elif event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = pygame.mouse.get_pos()

            # CARD 1
            if (

                card1_x <= mx <= card1_x + CARD_W and
                card_y <= my <= card_y + CARD_H

            ):

                launch_module(
                    "sky_simulation"
                )

            # CARD 2
            if (

                card2_x <= mx <= card2_x + CARD_W and
                card_y <= my <= card_y + CARD_H

            ):

                launch_module(
                    "satellite_tracker"
                )

    # --------------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------------

    draw_background(
        screen,
        dt,
        pygame.time.get_ticks() * 0.001,
        W,
        H
    )

    # --------------------------------------------------------
    # TITLE GLOW
    # --------------------------------------------------------

    glow(
        screen,
        W // 2,
        95,
        280,
        (0,180,255)
    )

    glow(
        screen,
        W // 2,
        95,
        180,
        (0,255,255)
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    draw_text(
        screen,
        FONT_TITLE,
        "COSMO",
        W // 2 - 25,
        60,
        CYAN,
        center=True
    )

    draw_text(
        screen,
        FONT_TITLE,
        "LENS",
        W // 2 + 160,
        60,
        WHITE,
        center=True
    )

    draw_text(
        screen,
        FONT_SUB,
        "DEEP SKY  •  STAR ATLAS  •  SATELLITE TRACKER",
        W // 2,
        145,
        DIM,
        center=True
    )

    # --------------------------------------------------------
    # TAGS
    # --------------------------------------------------------

    tags = [

        "Hipparcos",
        "DE421",
        "SGP4",
        "Celestrak TLE",
        "pygame"
    ]

    tx = 18

    for tag in tags:

        tw = FONT_FOOT.size(tag)[0]

        pygame.draw.rect(
            screen,
            DIM,
            (tx, 18, tw + 16, 22),
            1
        )

        draw_text(
            screen,
            FONT_FOOT,
            tag,
            tx + 8,
            23,
            DIM
        )

        tx += tw + 28

    # --------------------------------------------------------
    # HOVER
    # --------------------------------------------------------

    mx, my = pygame.mouse.get_pos()

    hover1 = (

        card1_x <= mx <= card1_x + CARD_W and
        card_y <= my <= card_y + CARD_H

    )

    hover2 = (

        card2_x <= mx <= card2_x + CARD_W and
        card_y <= my <= card_y + CARD_H

    )

    # --------------------------------------------------------
    # DRAW CARDS
    # --------------------------------------------------------

    draw_card(
        screen,
        card1_x,
        card_y,
        CARDS[0],
        hover1
    )

    draw_card(
        screen,
        card2_x,
        card_y,
        CARDS[1],
        hover2
    )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    utc = datetime.datetime.utcnow().strftime(
        "UTC  %Y-%m-%d  %H:%M:%S"
    )

    draw_text(
        screen,
        FONT_FOOT,
        utc,
        W // 2,
        H - 24,
        DIM,
        center=True
    )

    draw_text(
        screen,
        FONT_FOOT,
        "Press ESC to quit",
        16,
        H - 24,
        DIM
    )

    draw_text(
        screen,
        FONT_FOOT,
        "CosmoLens v6",
        W - 130,
        H - 24,
        DIM
    )

    pygame.display.flip()

pygame.quit()
sys.exit()