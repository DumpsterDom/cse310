"""
Gods of Kemet - An Egyptian Mythology ARPG
=========================================
A tactical action RPG set in ancient Egypt.
Play as a warrior of the gods against the forces of Chaos.

Controls:
    WASD / Arrow Keys - Move
    Left Click        - Attack
    Right Click       - Use Special Ability
    1, 2, 3           - Switch Abilities
    I                 - Toggle Inventory/Stats panel
    ESC               - Pause / Quit to Menu
"""

import arcade
import arcade.gui
import math
import random
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
#  Compatibility patch
# ─────────────────────────────────────────────

if not hasattr(arcade, "draw_rectangle_filled"):
    def draw_rectangle_filled(center_x, center_y, width, height, color):
        arcade.draw_lbwh_rectangle_filled(
            center_x - width / 2,
            center_y - height / 2,
            width,
            height,
            color
        )

    arcade.draw_rectangle_filled = draw_rectangle_filled

if not hasattr(arcade, "draw_rectangle_outline"):
    def draw_rectangle_outline(center_x, center_y, width, height, color, border_width=1):
        arcade.draw_lbwh_rectangle_outline(
            center_x - width / 2,
            center_y - height / 2,
            width,
            height,
            color,
            border_width
        )

    arcade.draw_rectangle_outline = draw_rectangle_outline

# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 800
TITLE = "Gods of Kemet"
 
TILE_SIZE   = 48
MAP_COLS    = 40
MAP_ROWS    = 30
MAP_W       = MAP_COLS * TILE_SIZE
MAP_H       = MAP_ROWS * TILE_SIZE
 
PLAYER_SPEED      = 180
ENEMY_SPEED       = 70
PLAYER_RADIUS     = 16
ENEMY_RADIUS      = 14
ATTACK_RANGE      = 60
ATTACK_COOLDOWN   = 0.55  
ABILITY_COOLDOWN  = 3.0
PROJ_SPEED        = 340
PROJ_LIFETIME     = 1.8
 
# Egyptian colour palette
COL_SAND        = (210, 180, 110)
COL_SAND_DARK   = (170, 140,  80)
COL_STONE       = (130, 120, 100)
COL_STONE_DARK  = ( 90,  82,  70)
COL_NILE        = ( 50,  90, 130)
COL_GOLD        = (212, 175,  55)
COL_GOLD_LIGHT  = (255, 220, 100)
COL_LAPIS       = ( 26,  51, 102)
COL_HIEROGLYPH  = (180, 100,  20)
COL_ANKH        = (200, 160,  40)
COL_RED_CHAOS   = (160,  20,  20)
COL_SCARAB      = ( 30, 100,  60)
COL_WHITE       = (240, 230, 210)
COL_BLACK       = ( 20,  15,  10)
COL_HP_RED      = (200,  50,  50)
COL_HP_GREEN    = ( 60, 180,  80)
COL_MANA_BLUE   = ( 60, 120, 210)
COL_XP_YELLOW   = (210, 180,  30)
 
# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────
class GameState(Enum):
    MAIN_MENU   = auto()
    CHARACTER   = auto()
    PLAYING     = auto()
    PAUSED      = auto()
    GAME_OVER   = auto()
    VICTORY     = auto()
 
class EnemyType(Enum):
    SCARAB_SWARM   = "Scarab Swarm"
    DESERT_JACKAL  = "Desert Jackal"
    MUMMY_GUARD    = "Mummy Guard"
    SETH_CULTIST   = "Seth's Cultist"
    APEP_SERPENT   = "Apep Serpent"
    ANUBIS_SHADE   = "Anubis Shade"
 
class AbilityType(Enum):
    KHEPRI_STRIKE  = "Khepri's Strike"
    RA_BEAM        = "Ra's Solar Beam"
    HORUS_SHIELD   = "Eye of Horus"
    ANUBIS_CURSE   = "Anubis Curse"
    THOTH_WISDOM   = "Thoth's Wisdom"
 
# ─────────────────────────────────────────────
#  Data classes
# ─────────────────────────────────────────────
@dataclass
class Stats:
    """Player or enemy base stats."""
    max_hp:    int   = 100
    hp:        int   = 100
    max_mana:  int   = 80
    mana:      int   = 80
    strength:  int   = 10  
    dexterity: int   = 8   
    wisdom:    int   = 8    
    armor:     int   = 5    
    level:     int   = 1
    xp:        int   = 0
    xp_next:   int   = 100
 
    def xp_to_next(self) -> int:
        return int(100 * (1.6 ** (self.level - 1)))
 
    def gain_xp(self, amount: int) -> bool:
        """Returns True if levelled up."""
        self.xp += amount
        if self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level_up()
            return True
        return False
 
    def level_up(self):
        self.level   += 1
        self.xp_next  = self.xp_to_next()
        self.max_hp  += 20
        self.hp       = self.max_hp
        self.max_mana += 10
        self.mana     = self.max_mana
        self.strength += 2
        self.wisdom   += 2
        self.armor    += 1
 
@dataclass
class Ability:
    ability_type: AbilityType
    name:         str
    mana_cost:    int
    cooldown:     float
    description:  str
    _last_used:   float = field(default=0.0, repr=False)
 
    def is_ready(self) -> bool:
        return time.time() - self._last_used >= self.cooldown
 
    def cooldown_remaining(self) -> float:
        return max(0.0, self.cooldown - (time.time() - self._last_used))
 
    def use(self):
        self._last_used = time.time()
 
# ─────────────────────────────────────────────
#  Particle
# ─────────────────────────────────────────────
class Particle:
    __slots__ = ("x","y","vx","vy","life","max_life","radius","color","fade")
 
    def __init__(self, x, y, vx, vy, life, radius, color, fade=True):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.radius = radius
        self.color = color
        self.fade = fade
 
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
 
    def draw(self):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life)) if self.fade else 200
        r, g, b = self.color[:3]
        arcade.draw_circle_filled(self.x, self.y, self.radius, (r, g, b, alpha))
 
# ─────────────────────────────────────────────
#  Tile map
# ─────────────────────────────────────────────
class TileType(Enum):
    SAND        = 0
    SAND_DARK   = 1
    STONE       = 2
    WALL        = 3
    NILE        = 4
    PILLAR      = 5
 
WALKABLE = {TileType.SAND, TileType.SAND_DARK, TileType.STONE, TileType.NILE}
SLOW_TILES = {TileType.NILE}  # tiles that slow movement
 
def generate_map() -> list[list[TileType]]:
    """Generate a simple procedural dungeon-like map."""
    grid = [[TileType.SAND for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
 
    # Outer walls
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if r == 0 or r == MAP_ROWS-1 or c == 0 or c == MAP_COLS-1:
                grid[r][c] = TileType.WALL
 
    # Scatter stone floor sections
    random.seed(42)
    for _ in range(60):
        cr = random.randint(2, MAP_ROWS-3)
        cc = random.randint(2, MAP_COLS-3)
        for dr in range(-2, 3):
            for dc in range(-3, 4):
                nr, nc = cr+dr, cc+dc
                if 1 <= nr < MAP_ROWS-1 and 1 <= nc < MAP_COLS-1:
                    grid[nr][nc] = TileType.STONE
 
    # Internal walls (rooms)
    rooms = [
        (5, 5, 8, 8), (20, 4, 26, 10), (30, 3, 37, 9),
        (3, 18, 10, 25), (16, 17, 24, 26), (28, 16, 37, 24),
        (8, 28, 15, MAP_ROWS-2), (22, 27, 30, MAP_ROWS-2),
    ]
    for (r1,c1,r2,c2) in rooms:
        for r in range(r1, r2):
            for c in range(c1, c2):
                if 1 <= r < MAP_ROWS-1 and 1 <= c < MAP_COLS-1:
                    grid[r][c] = TileType.STONE
 
    # Wall borders for rooms
    for (r1,c1,r2,c2) in rooms:
        for r in range(r1, r2):
            for c in (c1, c2-1):
                if 0 < r < MAP_ROWS-1 and 0 < c < MAP_COLS-1:
                    grid[r][c] = TileType.WALL
        for c in range(c1, c2):
            for r in (r1, r2-1):
                if 0 < r < MAP_ROWS-1 and 0 < c < MAP_COLS-1:
                    grid[r][c] = TileType.WALL
        # Door gap
        mid_r = (r1+r2)//2
        mid_c = (c1+c2)//2
        if 1 <= mid_r < MAP_ROWS-1 and 1 <= c1 < MAP_COLS-1:
            grid[mid_r][c1] = TileType.STONE
        if 1 <= mid_r < MAP_ROWS-1 and 0 < c2-1 < MAP_COLS-1:
            grid[mid_r][c2-1] = TileType.STONE
        if 1 <= r1 < MAP_ROWS-1 and 1 <= mid_c < MAP_COLS-1:
            grid[r1][mid_c] = TileType.STONE
 
    # Pillars
    for pr, pc in [(6,7),(7,22),(8,31),(20,6),(21,33),(18,20),(19,22)]:
        if 1 <= pr < MAP_ROWS-1 and 1 <= pc < MAP_COLS-1:
            grid[pr][pc] = TileType.PILLAR
 
    # Nile river strip
    for r in range(1, MAP_ROWS-1):
        grid[r][13] = TileType.NILE
        grid[r][14] = TileType.NILE
 
    # Dark sand patches
    for _ in range(80):
        r = random.randint(1, MAP_ROWS-2)
        c = random.randint(1, MAP_COLS-2)
        if grid[r][c] == TileType.SAND:
            grid[r][c] = TileType.SAND_DARK
 
    return grid
 
# ─────────────────────────────────────────────
#  Combat helpers
# ─────────────────────────────────────────────
def calc_damage(attacker_strength: int, base_dmg: int, target_armor: int) -> int:
    raw = base_dmg + attacker_strength // 2
    reduced = max(1, raw - target_armor)
    # ±20% variance
    variance = random.uniform(0.8, 1.2)
    return max(1, int(reduced * variance))
 
def spawn_hit_particles(x, y, color, count=10):
    pts = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 160)
        life  = random.uniform(0.25, 0.6)
        rad   = random.uniform(2, 5)
        pts.append(Particle(x, y,
                             math.cos(angle)*speed,
                             math.sin(angle)*speed,
                             life, rad, color))
    return pts
 
def spawn_death_particles(x, y, color, count=20):
    pts = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 220)
        life  = random.uniform(0.4, 1.0)
        rad   = random.uniform(3, 8)
        pts.append(Particle(x, y,
                             math.cos(angle)*speed,
                             math.sin(angle)*speed,
                             life, rad, color))
    return pts
 
# ─────────────────────────────────────────────
#  Floating text
# ─────────────────────────────────────────────
class FloatingText:
    def __init__(self, text, x, y, color, size=16):
        self.text  = text
        self.x     = x + random.uniform(-15, 15)
        self.y     = y
        self.vy    = 60
        self.life  = 1.2
        self.color = color
        self.size  = size
 
    def update(self, dt):
        self.y    += self.vy * dt
        self.vy   *= 0.96
        self.life -= dt
 
    def draw(self):
        if self.life <= 0:
            return
        alpha = int(255 * min(1, self.life / 0.4))
        r, g, b = self.color[:3]
        arcade.draw_text(self.text, self.x, self.y,
                         (r, g, b, alpha), self.size,
                         anchor_x="center", bold=True)
 
# ─────────────────────────────────────────────
#  Projectile
# ─────────────────────────────────────────────
class Projectile:
    def __init__(self, x, y, angle, speed, damage, color, radius=6,
                 from_player=True, ability_type=None):
        self.x = x; self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.damage      = damage
        self.color       = color
        self.radius      = radius
        self.from_player = from_player
        self.ability_type = ability_type
        self.lifetime    = PROJ_LIFETIME
        self.alive       = True
 
    def update(self, dt):
        self.x        += self.vx * dt
        self.y        += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
 
    def draw(self):
        # Glow outer
        arcade.draw_circle_filled(self.x, self.y, self.radius + 4,
                                   (*self.color[:3], 60))
        arcade.draw_circle_filled(self.x, self.y, self.radius,
                                   self.color)
 
# ─────────────────────────────────────────────
#  Enemy
# ─────────────────────────────────────────────
ENEMY_TEMPLATES = {
    EnemyType.SCARAB_SWARM: dict(
        max_hp=25, strength=5, armor=1, speed=90,
        xp_reward=15, base_dmg=6,
        color=(30, 100, 60), size=10,
        attack_range=28, attack_cd=0.8,
        description="Swarms of sacred scarabs animated by dark magic."
    ),
    EnemyType.DESERT_JACKAL: dict(
        max_hp=45, strength=9, armor=3, speed=110,
        xp_reward=25, base_dmg=10,
        color=(160, 110, 40), size=13,
        attack_range=32, attack_cd=0.9,
        description="Wild jackals twisted by Seth's corruption."
    ),
    EnemyType.MUMMY_GUARD: dict(
        max_hp=90, strength=12, armor=8, speed=50,
        xp_reward=50, base_dmg=14,
        color=(200, 185, 150), size=16,
        attack_range=38, attack_cd=1.4,
        description="Ancient guardians wrapped in cursed linen."
    ),
    EnemyType.SETH_CULTIST: dict(
        max_hp=60, strength=10, armor=4, speed=75,
        xp_reward=40, base_dmg=12,
        color=(140, 20, 20), size=14,
        attack_range=200, attack_cd=2.0,
        description="Mortal worshippers of the god of chaos."
    ),
    EnemyType.APEP_SERPENT: dict(
        max_hp=110, strength=16, armor=6, speed=85,
        xp_reward=70, base_dmg=18,
        color=(40, 80, 30), size=18,
        attack_range=45, attack_cd=1.6,
        description="Servants of the great serpent Apep."
    ),
    EnemyType.ANUBIS_SHADE: dict(
        max_hp=75, strength=13, armor=5, speed=95,
        xp_reward=60, base_dmg=15,
        color=(20, 20, 50), size=15,
        attack_range=55, attack_cd=1.2,
        description="Shadows escaped from the Duat."
    ),
}
 
class Enemy:
    _id_counter = 0
 
    def __init__(self, enemy_type: EnemyType, x: float, y: float):
        Enemy._id_counter += 1
        self.id   = Enemy._id_counter
        self.type = enemy_type
        self.x    = x
        self.y    = y
 
        t = ENEMY_TEMPLATES[enemy_type]
        self.max_hp     = t["max_hp"]
        self.hp         = t["max_hp"]
        self.strength   = t["strength"]
        self.armor      = t["armor"]
        self.speed      = t["speed"]
        self.xp_reward  = t["xp_reward"]
        self.base_dmg   = t["base_dmg"]
        self.color      = t["color"]
        self.size       = t["size"]
        self.atk_range  = t["attack_range"]
        self.attack_cd  = t["attack_cd"]
        self._atk_timer = random.uniform(0, self.attack_cd)
        self.alive      = True
 
        # AI state
        self.state        = "idle"   # idle | chase | attack | stunned
        self.stun_timer   = 0.0
        self.aggro_range  = 280
        self.target_x     = x
        self.target_y     = y
 
        # Ranged flag
        self.is_ranged = (enemy_type == EnemyType.SETH_CULTIST)
 
    def take_damage(self, amount: int) -> int:
        actual = max(1, amount - self.armor)
        self.hp -= actual
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return actual
 
    def update(self, dt, player_x, player_y, grid, projectiles):
        if not self.alive:
            return
 
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return
 
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
 
        if dist < self.aggro_range:
            self.state = "chase"
 
        if self.state == "chase":
            if dist > self.atk_range + 8:
                # Move toward player (simple steering)
                if dist > 0:
                    nx, ny = dx / dist, dy / dist
                    new_x = self.x + nx * self.speed * dt
                    new_y = self.y + ny * self.speed * dt
                    # Collision vs walls
                    if self._walkable(new_x, self.y, grid):
                        self.x = new_x
                    if self._walkable(self.x, new_y, grid):
                        self.y = new_y
            else:
                self.state = "attack"
 
        if self.state == "attack":
            self._atk_timer -= dt
            if dist > self.atk_range + 20:
                self.state = "chase"
            elif self._atk_timer <= 0:
                self._atk_timer = self.attack_cd
                if self.is_ranged:
                    # Shoot projectile at player
                    angle = math.atan2(dy, dx)
                    projectiles.append(Projectile(
                        self.x, self.y, angle, 200,
                        self.base_dmg, COL_RED_CHAOS,
                        radius=5, from_player=False
                    ))
                else:
                    # Return damage to be applied externally
                    return self.base_dmg
        return None
 
    @staticmethod
    def _walkable(x, y, grid) -> bool:
        c = int(x // TILE_SIZE)
        r = int(y // TILE_SIZE)
        if r < 0 or r >= MAP_ROWS or c < 0 or c >= MAP_COLS:
            return False
        return grid[r][c] in WALKABLE  # WALKABLE now includes NILE
 
    def draw(self):
        if not self.alive:
            return
        # Shadow
        arcade.draw_ellipse_filled(self.x, self.y - self.size + 4,
                                    self.size * 1.4, self.size * 0.5,
                                    (0, 0, 0, 60))
        # Body
        arcade.draw_circle_filled(self.x, self.y, self.size, self.color)
 
        # Type marker
        if self.type == EnemyType.MUMMY_GUARD:
            # Linen wrap lines
            for i in range(-1, 2):
                arcade.draw_line(self.x - self.size + 3,
                                  self.y + i * 5,
                                  self.x + self.size - 3,
                                  self.y + i * 5,
                                  COL_WHITE, 2)
        elif self.type == EnemyType.SETH_CULTIST:
            # Seth symbol (X)
            s = self.size - 4
            arcade.draw_line(self.x - s, self.y - s,
                              self.x + s, self.y + s, COL_GOLD, 2)
            arcade.draw_line(self.x + s, self.y - s,
                              self.x - s, self.y + s, COL_GOLD, 2)
        elif self.type == EnemyType.APEP_SERPENT:
            # Serpent coil
            arcade.draw_arc_outline(self.x, self.y, self.size * 1.2,
                                     self.size * 0.8, (100, 200, 50), 0, 300, 3)
        elif self.type == EnemyType.ANUBIS_SHADE:
            # Ankh symbol
            arcade.draw_line(self.x, self.y - self.size + 2,
                              self.x, self.y + self.size - 4,
                              COL_ANKH, 2)
            arcade.draw_line(self.x - 6, self.y + 3,
                              self.x + 6, self.y + 3,
                              COL_ANKH, 2)
            arcade.draw_circle_outline(self.x, self.y + 7, 5, COL_ANKH, 2)
        elif self.type == EnemyType.SCARAB_SWARM:
            # Dots for swarm
            for offset in [(-5, 3), (5, 3), (0, -4)]:
                arcade.draw_circle_filled(self.x + offset[0],
                                           self.y + offset[1],
                                           3, (20, 60, 30))
 
        # HP bar
        bar_w = self.size * 2.2
        bar_h = 4
        bx    = self.x - bar_w / 2
        by    = self.y + self.size + 4
        arcade.draw_rectangle_filled(bx + bar_w/2, by + bar_h/2,
                                      bar_w, bar_h, (40, 10, 10))
        hp_frac = self.hp / self.max_hp
        if hp_frac > 0:
            arcade.draw_rectangle_filled(bx + (bar_w * hp_frac)/2,
                                          by + bar_h/2,
                                          bar_w * hp_frac, bar_h,
                                          COL_HP_RED)
 
# ─────────────────────────────────────────────
#  Player
# ─────────────────────────────────────────────
CHARACTERS = {
    "Amenhotep": dict(
        desc="A warrior blessed by Ra. Balanced fighter with solar abilities.",
        stats=Stats(max_hp=120, hp=120, max_mana=80, mana=80,
                    strength=12, dexterity=10, wisdom=8, armor=6),
        color=COL_GOLD,
        abilities=[
            Ability(AbilityType.KHEPRI_STRIKE,  "Khepri's Strike",  20, 3.0,
                    "A powerful scarab-charged melee strike. +150% dmg."),
            Ability(AbilityType.RA_BEAM,         "Ra's Solar Beam",  35, 5.0,
                    "Fire a beam of solar energy that pierces enemies."),
            Ability(AbilityType.HORUS_SHIELD,    "Eye of Horus",     25, 8.0,
                    "A protective ward that absorbs 40 damage."),
        ]
    ),
    "Nefertari": dict(
        desc="A sorceress of Thoth. High mana, lower armor. Wisdom-focused.",
        stats=Stats(max_hp=90, hp=90, max_mana=140, mana=140,
                    strength=7, dexterity=12, wisdom=16, armor=3),
        color=(180, 100, 200),
        abilities=[
            Ability(AbilityType.THOTH_WISDOM,   "Thoth's Wisdom",   15, 2.0,
                    "Channel Thoth to empower your next 3 attacks."),
            Ability(AbilityType.RA_BEAM,         "Ra's Solar Beam",  25, 4.0,
                    "A focused beam of magical energy."),
            Ability(AbilityType.ANUBIS_CURSE,   "Anubis Curse",     40, 7.0,
                    "Curse nearby enemies, slowing and weakening them."),
        ]
    ),
    "Kha'em": dict(
        desc="A general of Sekhmet. High strength and armor. Slow but devastating.",
        stats=Stats(max_hp=160, hp=160, max_mana=50, mana=50,
                    strength=18, dexterity=6, wisdom=5, armor=12),
        color=(200, 60, 60),
        abilities=[
            Ability(AbilityType.KHEPRI_STRIKE,  "Khepri's Strike",  15, 2.5,
                    "A brutal scarab-charged melee strike."),
            Ability(AbilityType.HORUS_SHIELD,    "Eye of Horus",     20, 6.0,
                    "A protective ward that absorbs 80 damage."),
            Ability(AbilityType.ANUBIS_CURSE,   "Anubis Curse",     30, 8.0,
                    "Curse and weaken all nearby enemies."),
        ]
    ),
}
 
class Player:
    def __init__(self, char_name: str):
        data          = CHARACTERS[char_name]
        self.name     = char_name
        self.stats    = data["stats"]
        self.color    = data["color"]
        self.abilities = data["abilities"]
        self.selected_ability = 0
 
        self.x = MAP_W  / 2
        self.y = MAP_H  / 2
 
        self.facing_angle   = 0.0
        self.attack_timer   = 0.0
        self.attack_flash   = 0.0
        self.shield_hp      = 0
        self.empowered_hits = 0
 
        self.alive          = True
        self.invincible_t   = 0.0   # brief i-frames after hit
        self.level_up_flash = 0.0
 
        # Cosmetic
        self.walk_anim   = 0.0
        self.anim_timer  = 0.0
 
    @property
    def ability(self) -> Ability:
        return self.abilities[self.selected_ability]
 
    def take_damage(self, amount: int) -> int:
        if self.invincible_t > 0:
            return 0
        self.invincible_t = 0.4
        # Shield absorb
        if self.shield_hp > 0:
            absorbed        = min(self.shield_hp, amount)
            self.shield_hp -= absorbed
            amount         -= absorbed
        actual = max(0, amount - self.stats.armor)
        self.stats.hp = max(0, self.stats.hp - actual)
        if self.stats.hp <= 0:
            self.alive = False
        return actual
 
    def update(self, dt):
        self.attack_timer   = max(0, self.attack_timer   - dt)
        self.attack_flash   = max(0, self.attack_flash   - dt)
        self.invincible_t   = max(0, self.invincible_t   - dt)
        self.level_up_flash = max(0, self.level_up_flash - dt)
        # Mana regen
        if self.stats.mana < self.stats.max_mana:
            self.stats.mana = min(self.stats.max_mana,
                                   self.stats.mana + 3 * dt)
        self.anim_timer += dt
        self.walk_anim   = math.sin(self.anim_timer * 8) * 3
 
    def draw(self):
        x, y = self.x, self.y
 
        # Invincibility flicker
        if self.invincible_t > 0 and int(self.invincible_t * 14) % 2:
            return
 
        # Level-up aura
        if self.level_up_flash > 0:
            alpha = int(180 * self.level_up_flash / 1.5)
            arcade.draw_circle_filled(x, y, 38, (*COL_GOLD_LIGHT, alpha))
 
        # Shield aura
        if self.shield_hp > 0:
            arcade.draw_circle_outline(x, y, 32,
                                        (*COL_LAPIS, 180), 3)
 
        # Shadow
        arcade.draw_ellipse_filled(x, y - 14 + self.walk_anim * 0.3,
                                    36, 12, (0,0,0,50))
 
        # Cloak / body
        pts = [
            (x - 14, y - 18 + self.walk_anim),
            (x + 14, y - 18 + self.walk_anim),
            (x + 10, y + 20),
            (x - 10, y + 20),
        ]
        arcade.draw_polygon_filled(pts,
                                    (*COL_LAPIS, 230))
        arcade.draw_polygon_outline(pts,
                                     (*COL_GOLD, 200), 2)
 
        # Head
        arcade.draw_circle_filled(x, y + 22, 12, self.color)
        # Nemes headdress stripes
        arcade.draw_line(x - 10, y + 28, x - 14, y + 10,
                          COL_GOLD, 2)
        arcade.draw_line(x + 10, y + 28, x + 14, y + 10,
                          COL_GOLD, 2)
        # Eyes
        arcade.draw_circle_filled(x - 4, y + 24, 2, COL_BLACK)
        arcade.draw_circle_filled(x + 4, y + 24, 2, COL_BLACK)
        # Kohl eye lines
        arcade.draw_line(x - 6, y + 24, x - 8, y + 22,
                          COL_BLACK, 1)
        arcade.draw_line(x + 6, y + 24, x + 8, y + 22,
                          COL_BLACK, 1)
 
        # Weapon (khopesh sword outline)
        angle = self.facing_angle
        if self.attack_flash > 0:
            wx = x + math.cos(angle) * 28
            wy = y + math.sin(angle) * 28
            # Flash arc
            arcade.draw_arc_outline(wx, wy, 20, 20,
                                     (*COL_GOLD_LIGHT, 200),
                                     math.degrees(angle) - 60,
                                     math.degrees(angle) + 60, 4)
        wx = x + math.cos(angle) * 24
        wy = y + math.sin(angle) * 24
        arcade.draw_line(x + math.cos(angle)*10,
                          y + math.sin(angle)*10,
                          wx, wy,
                          COL_GOLD, 3)
 
    def draw_ui(self, cam_left, cam_bottom):
        """Draw HUD elements anchored to screen."""
        sx, sy = cam_left, cam_bottom
        pad = 14
 
        # ── HP Bar ──────────────────────────────
        bar_x, bar_y, bar_w, bar_h = sx + pad, sy + pad, 220, 18
        arcade.draw_rectangle_filled(bar_x + bar_w/2, bar_y + bar_h/2,
                                      bar_w, bar_h, (30, 10, 10))
        hp_frac = self.stats.hp / self.stats.max_hp
        if hp_frac > 0:
            arcade.draw_rectangle_filled(bar_x + (bar_w*hp_frac)/2,
                                          bar_y + bar_h/2,
                                          bar_w * hp_frac, bar_h,
                                          COL_HP_GREEN)
        arcade.draw_rectangle_outline(bar_x + bar_w/2, bar_y + bar_h/2,
                                       bar_w, bar_h, COL_GOLD, 1)
        arcade.draw_text(f"HP  {self.stats.hp}/{self.stats.max_hp}",
                          bar_x + 6, bar_y + 2,
                          COL_WHITE, 11, bold=True)
 
        # ── Mana Bar ─────────────────────────────
        bar_y2 = bar_y + bar_h + 5
        arcade.draw_rectangle_filled(bar_x + bar_w/2, bar_y2 + bar_h/2,
                                      bar_w, bar_h, (10, 10, 40))
        mp_frac = self.stats.mana / self.stats.max_mana
        if mp_frac > 0:
            arcade.draw_rectangle_filled(bar_x + (bar_w*mp_frac)/2,
                                          bar_y2 + bar_h/2,
                                          bar_w * mp_frac, bar_h,
                                          COL_MANA_BLUE)
        arcade.draw_rectangle_outline(bar_x + bar_w/2, bar_y2 + bar_h/2,
                                       bar_w, bar_h, COL_GOLD, 1)
        arcade.draw_text(f"MP  {int(self.stats.mana)}/{self.stats.max_mana}",
                          bar_x + 6, bar_y2 + 2,
                          COL_WHITE, 11, bold=True)
 
        # ── XP Bar ───────────────────────────────
        bar_y3 = bar_y2 + bar_h + 5
        xp_bar_h = 8
        arcade.draw_rectangle_filled(bar_x + bar_w/2, bar_y3 + xp_bar_h/2,
                                      bar_w, xp_bar_h, (20, 15, 5))
        xp_frac = self.stats.xp / max(1, self.stats.xp_next)
        if xp_frac > 0:
            arcade.draw_rectangle_filled(bar_x + (bar_w*xp_frac)/2,
                                          bar_y3 + xp_bar_h/2,
                                          bar_w * xp_frac, xp_bar_h,
                                          COL_XP_YELLOW)
        arcade.draw_text(f"LVL {self.stats.level}",
                          bar_x + bar_w + 8, bar_y + 2,
                          COL_GOLD_LIGHT, 12, bold=True)
 
        # ── Ability Slots ─────────────────────────
        slot_size = 54
        slot_y    = sy + pad
        slot_start_x = sx + SCREEN_W - (slot_size + 8) * 3 - pad
 
        for i, ab in enumerate(self.abilities):
            bx = slot_start_x + i * (slot_size + 8)
            # Background
            bg_col = COL_LAPIS if i == self.selected_ability else (20, 15, 10)
            arcade.draw_rectangle_filled(bx + slot_size/2, slot_y + slot_size/2,
                                          slot_size, slot_size, bg_col)
            arcade.draw_rectangle_outline(bx + slot_size/2, slot_y + slot_size/2,
                                           slot_size, slot_size,
                                           COL_GOLD if i == self.selected_ability
                                           else (80, 60, 20), 2)
            # Cooldown overlay
            cd_rem = ab.cooldown_remaining()
            if cd_rem > 0:
                frac = cd_rem / ab.cooldown
                arcade.draw_rectangle_filled(bx + slot_size/2,
                                              slot_y + slot_size * (1-frac) / 2 + slot_size * frac / 2,
                                              slot_size,
                                              slot_size * frac,
                                              (0, 0, 0, 160))
                arcade.draw_text(f"{cd_rem:.1f}",
                                  bx + slot_size/2, slot_y + slot_size/2 - 8,
                                  COL_WHITE, 13, anchor_x="center", bold=True)
 
            # Key label
            arcade.draw_text(str(i+1),
                              bx + 5, slot_y + slot_size - 16,
                              COL_GOLD_LIGHT, 11, bold=True)
            # Short ability name
            short = ab.name.split("'")[0][:6]
            arcade.draw_text(short,
                              bx + slot_size/2, slot_y + 6,
                              COL_WHITE, 9, anchor_x="center")
 
        # ── Shield indicator ──────────────────────
        if self.shield_hp > 0:
            arcade.draw_text(f"🛡 SHIELD: {self.shield_hp}",
                              sx + pad, sy + 110,
                              (*COL_LAPIS, 255), 14, bold=True)
 
        # ── Empowered hits ────────────────────────
        if self.empowered_hits > 0:
            arcade.draw_text(f"⚡ EMPOWERED ×{self.empowered_hits}",
                              sx + pad, sy + 130,
                              (*COL_GOLD_LIGHT, 255), 14, bold=True)
 
# ─────────────────────────────────────────────
#  Stats Panel (overlay)
# ─────────────────────────────────────────────
class StatsPanel:
    def __init__(self):
        self.visible = False
        self.w, self.h = 320, 400
 
    def toggle(self):
        self.visible = not self.visible
 
    def draw(self, player: Player, cam_left, cam_bottom):
        if not self.visible:
            return
        px = cam_left + SCREEN_W - self.w - 20
        py = cam_bottom + SCREEN_H - self.h - 20
 
        # Panel background
        arcade.draw_rectangle_filled(px + self.w/2, py + self.h/2,
                                      self.w, self.h,
                                      (15, 10, 5, 230))
        arcade.draw_rectangle_outline(px + self.w/2, py + self.h/2,
                                       self.w, self.h, COL_GOLD, 2)
 
        # Hieroglyph border dots
        for i in range(0, self.w, 20):
            arcade.draw_circle_filled(px + i, py + self.h - 2, 2, COL_GOLD)
            arcade.draw_circle_filled(px + i, py + 2, 2, COL_GOLD)
 
        # Title
        arcade.draw_text("⊕  CHARACTER  ⊕",
                          px + self.w/2, py + self.h - 30,
                          COL_GOLD_LIGHT, 18, anchor_x="center", bold=True)
        arcade.draw_line(px + 10, py + self.h - 40,
                          px + self.w - 10, py + self.h - 40,
                          COL_HIEROGLYPH, 1)
 
        s = player.stats
        lines = [
            ("Name",      player.name),
            ("Level",     str(s.level)),
            ("XP",        f"{s.xp} / {s.xp_next}"),
            ("",          ""),
            ("❤  HP",     f"{s.hp} / {s.max_hp}"),
            ("✦  Mana",   f"{int(s.mana)} / {s.max_mana}"),
            ("",          ""),
            ("⚔  Strength",  str(s.strength)),
            ("🎯 Dexterity", str(s.dexterity)),
            ("📖 Wisdom",    str(s.wisdom)),
            ("🛡  Armor",    str(s.armor)),
            ("",          ""),
        ]
        ty = py + self.h - 55
        for label, val in lines:
            if label:
                arcade.draw_text(label,
                                  px + 16, ty, COL_SAND, 13)
                arcade.draw_text(val,
                                  px + self.w - 16, ty, COL_GOLD_LIGHT, 13,
                                  anchor_x="right", bold=True)
            ty -= 22
 
        # Abilities
        arcade.draw_text("─── Abilities ───",
                          px + self.w/2, ty, COL_HIEROGLYPH, 12,
                          anchor_x="center")
        ty -= 22
        for ab in player.abilities:
            arcade.draw_text(f"• {ab.name}  (mp {ab.mana_cost})",
                              px + 14, ty, COL_SAND, 11)
            ty -= 16
            arcade.draw_text(f"  {ab.description[:44]}",
                              px + 14, ty, (150, 130, 90), 10)
            ty -= 20
 
        arcade.draw_text("[ I ] to close",
                          px + self.w/2, py + 8,
                          (120, 100, 60), 11, anchor_x="center")
 
# ─────────────────────────────────────────────
#  Main Game View
# ─────────────────────────────────────────────
class GameView(arcade.View):
    def __init__(self, char_name: str):
        super().__init__()
        self.char_name  = char_name
        self.state      = GameState.PLAYING
        self.grid       = generate_map()
        self.player     = Player(char_name)
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.particles:   list[Particle]   = []
        self.floats:      list[FloatingText] = []
        self.stats_panel = StatsPanel()
 
        # Camera
        self.cam = arcade.camera.Camera2D()
 
        self.keys_down: set = set()
        self.wave       = 0
        self.wave_timer = 0.0
        self.enemies_killed = 0
        self.total_waves    = 5
 
        self._spawn_wave()
 
    # ── Spawn ──────────────────────────────
    def _spawn_wave(self):
        self.wave += 1
        self.wave_timer = 0.0
        count = 4 + self.wave * 3
 
        # Wave composition
        pool = [EnemyType.SCARAB_SWARM, EnemyType.DESERT_JACKAL]
        if self.wave >= 2:
            pool += [EnemyType.MUMMY_GUARD, EnemyType.SETH_CULTIST]
        if self.wave >= 3:
            pool += [EnemyType.APEP_SERPENT]
        if self.wave >= 4:
            pool += [EnemyType.ANUBIS_SHADE]
 
        for _ in range(count):
            etype = random.choice(pool)
            for attempt in range(40):
                rx = random.randint(2, MAP_COLS - 2) * TILE_SIZE + TILE_SIZE // 2
                ry = random.randint(2, MAP_ROWS - 2) * TILE_SIZE + TILE_SIZE // 2
                dist = math.hypot(rx - self.player.x, ry - self.player.y)
                c = int(rx // TILE_SIZE)
                r = int(ry // TILE_SIZE)
                if self.grid[r][c] in WALKABLE and dist > 250:
                    self.enemies.append(Enemy(etype, rx, ry))
                    break
 
    def _all_enemies_dead(self) -> bool:
        return all(not e.alive for e in self.enemies)
 
    # ── Update ────────────────────────────────
    def on_update(self, dt):
        if self.state != GameState.PLAYING:
            return
 
        dt = min(dt, 0.05)  # cap dt
 
        # Player movement
        px, py = self.player.x, self.player.y
        speed  = PLAYER_SPEED
        dx = dy = 0
        if arcade.key.W in self.keys_down or arcade.key.UP in self.keys_down:
            dy += 1
        if arcade.key.S in self.keys_down or arcade.key.DOWN in self.keys_down:
            dy -= 1
        if arcade.key.A in self.keys_down or arcade.key.LEFT in self.keys_down:
            dx -= 1
        if arcade.key.D in self.keys_down or arcade.key.RIGHT in self.keys_down:
            dx += 1
        if dx != 0 and dy != 0:
            dx *= 0.707; dy *= 0.707
 
        # Slow on water tiles
        tc = int(self.player.x // TILE_SIZE)
        tr = int(self.player.y // TILE_SIZE)
        if (0 <= tr < MAP_ROWS and 0 <= tc < MAP_COLS and
                self.grid[tr][tc] in SLOW_TILES):
            speed *= 0.45
 
        new_x = px + dx * speed * dt
        new_y = py + dy * speed * dt
        if self._walkable(new_x, py):
            self.player.x = new_x
        if self._walkable(px, new_y):
            self.player.y = new_y
 
        self.player.update(dt)
 
        # Enemies
        for e in self.enemies:
            result = e.update(dt, self.player.x, self.player.y,
                               self.grid, self.projectiles)
            if result and isinstance(result, int):
                # Melee hit on player
                actual = self.player.take_damage(result)
                if actual > 0:
                    self.floats.append(
                        FloatingText(f"-{actual}", self.player.x,
                                      self.player.y + 20, COL_HP_RED, 15))
                    self.particles += spawn_hit_particles(
                        self.player.x, self.player.y, COL_HP_RED, 8)
            if not e.alive:
                self.particles += spawn_death_particles(e.x, e.y, e.color)
                levelled = self.player.stats.gain_xp(e.xp_reward)
                self.floats.append(
                    FloatingText(f"+{e.xp_reward} XP", e.x,
                                  e.y + 20, COL_XP_YELLOW))
                self.enemies_killed += 1
                if levelled:
                    self.player.level_up_flash = 1.5
                    self.floats.append(
                        FloatingText("LEVEL UP!", self.player.x,
                                      self.player.y + 50,
                                      COL_GOLD_LIGHT, 22))
 
        self.enemies = [e for e in self.enemies if e.alive]
 
        # Projectiles
        for proj in self.projectiles:
            proj.update(dt)
            if not proj.alive:
                continue
            if proj.from_player:
                for e in self.enemies:
                    if not e.alive:
                        continue
                    if math.hypot(proj.x - e.x, proj.y - e.y) < e.size + proj.radius:
                        dmg = calc_damage(self.player.stats.strength,
                                           proj.damage, e.armor)
                        if self.player.empowered_hits > 0:
                            dmg = int(dmg * 1.8)
                            self.player.empowered_hits -= 1
                        actual = e.take_damage(dmg)
                        self.floats.append(
                            FloatingText(str(actual), e.x, e.y + 20,
                                          COL_GOLD_LIGHT))
                        self.particles += spawn_hit_particles(e.x, e.y,
                                                               COL_GOLD, 6)
                        proj.alive = False
                        break
            else:
                # Enemy projectile hits player
                if math.hypot(proj.x - self.player.x,
                               proj.y - self.player.y) < PLAYER_RADIUS + proj.radius:
                    actual = self.player.take_damage(proj.damage)
                    if actual > 0:
                        self.floats.append(
                            FloatingText(f"-{actual}", self.player.x,
                                          self.player.y + 20,
                                          COL_HP_RED, 15))
                    proj.alive = False
 
            # Wall collision
            tc = int(proj.x // TILE_SIZE)
            tr = int(proj.y // TILE_SIZE)
            if (0 <= tr < MAP_ROWS and 0 <= tc < MAP_COLS and
                    self.grid[tr][tc] not in WALKABLE):
                proj.alive = False
                self.particles += spawn_hit_particles(
                    proj.x, proj.y, proj.color, 4)
 
        self.projectiles = [p for p in self.projectiles if p.alive]
 
        # Particles & floating text
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for f in self.floats:
            f.update(dt)
        self.floats = [f for f in self.floats if f.life > 0]
 
        # Wave progression
        if self._all_enemies_dead() and self.wave < self.total_waves:
            self.wave_timer += dt
            if self.wave_timer > 3.0:
                self._spawn_wave()
        elif self._all_enemies_dead() and self.wave >= self.total_waves:
            self.state = GameState.VICTORY
 
        # Player death
        if not self.player.alive:
            self.state = GameState.GAME_OVER
 
        # Camera follow
        self.cam.position = (
            max(SCREEN_W/2, min(MAP_W - SCREEN_W/2, self.player.x)),
            max(SCREEN_H/2, min(MAP_H - SCREEN_H/2, self.player.y))
        )
 
    # ── Draw ──────────────────────────────────
    def on_draw(self):
        self.clear()
        self.cam.use()
        cl = self.cam.position[0] - SCREEN_W / 2
        cb = self.cam.position[1] - SCREEN_H / 2
 
        # Tiles
        self._draw_map(cl, cb)
 
        # Game objects
        for e in self.enemies:
            e.draw()
        for p in self.projectiles:
            p.draw()
        for pt in self.particles:
            pt.draw()
        self.player.draw()
        for f in self.floats:
            f.draw()
 
        # HUD
        self.player.draw_ui(cl, cb)
        self._draw_hud_top(cl, cb)
        self.stats_panel.draw(self.player, cl, cb)
 
        # Overlay screens
        if self.state == GameState.GAME_OVER:
            self._draw_game_over(cl, cb)
        elif self.state == GameState.VICTORY:
            self._draw_victory(cl, cb)
        elif self.state == GameState.PAUSED:
            self._draw_pause(cl, cb)
 
    def _draw_map(self, cl, cb):
        # Determine visible tile range
        c_start = max(0, int(cl // TILE_SIZE) - 1)
        c_end   = min(MAP_COLS, int((cl + SCREEN_W) // TILE_SIZE) + 2)
        r_start = max(0, int(cb // TILE_SIZE) - 1)
        r_end   = min(MAP_ROWS, int((cb + SCREEN_H) // TILE_SIZE) + 2)
 
        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                tx = c * TILE_SIZE
                ty = r * TILE_SIZE
                cx = tx + TILE_SIZE / 2
                cy = ty + TILE_SIZE / 2
                t = self.grid[r][c]
 
                if t == TileType.SAND:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_SAND)
                elif t == TileType.SAND_DARK:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_SAND_DARK)
                elif t == TileType.STONE:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_STONE)
                    # Stone cracks
                    arcade.draw_line(cx-12, cy-8, cx-6, cy+4,
                                      COL_STONE_DARK, 1)
                elif t == TileType.WALL:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_STONE_DARK)
                    # Wall bricks
                    arcade.draw_rectangle_outline(cx, cy,
                                                   TILE_SIZE-2, TILE_SIZE-2,
                                                   (60, 55, 45), 1)
                    arcade.draw_line(cx-TILE_SIZE//2, cy,
                                      cx+TILE_SIZE//2, cy,
                                      (60, 55, 45), 1)
                elif t == TileType.NILE:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_NILE)
                    # Water ripple
                    arcade.draw_ellipse_outline(cx + 4, cy,
                                                 18, 6, (80, 130, 180), 1)
                elif t == TileType.PILLAR:
                    arcade.draw_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE,
                                                  COL_STONE)
                    # Pillar
                    arcade.draw_rectangle_filled(cx, cy+4,
                                                  TILE_SIZE-10, TILE_SIZE-4,
                                                  (160, 145, 115))
                    arcade.draw_rectangle_filled(cx, cy-18,
                                                  TILE_SIZE-4, 8,
                                                  (180, 160, 120))
                    # Hieroglyphs on pillar
                    arcade.draw_text("𓂀", cx - 6, cy - 6,
                                      COL_HIEROGLYPH, 12)
 
        # Tile grid lines (subtle)
        for r in range(r_start, r_end + 1):
            arcade.draw_line(c_start * TILE_SIZE, r * TILE_SIZE,
                              c_end * TILE_SIZE, r * TILE_SIZE,
                              (0, 0, 0, 15), 1)
        for c in range(c_start, c_end + 1):
            arcade.draw_line(c * TILE_SIZE, r_start * TILE_SIZE,
                              c * TILE_SIZE, r_end * TILE_SIZE,
                              (0, 0, 0, 15), 1)
 
    def _draw_hud_top(self, cl, cb):
        sx, sy = cl, cb
        # Wave info
        wave_text = (f"WAVE {self.wave} / {self.total_waves}"
                     if self.wave <= self.total_waves
                     else "FINAL WAVE CLEARED")
        arcade.draw_text(wave_text,
                          sx + SCREEN_W/2, sy + SCREEN_H - 30,
                          COL_GOLD, 20, anchor_x="center", bold=True)
        alive_count = sum(1 for e in self.enemies if e.alive)
        arcade.draw_text(f"Enemies remaining: {alive_count}",
                          sx + SCREEN_W/2, sy + SCREEN_H - 54,
                          COL_SAND, 14, anchor_x="center")
 
        # Between-wave countdown
        if self._all_enemies_dead() and self.wave < self.total_waves:
            remaining = max(0, 3.0 - self.wave_timer)
            arcade.draw_text(f"Next wave in {remaining:.1f}s…",
                              sx + SCREEN_W/2, sy + SCREEN_H/2,
                              COL_GOLD_LIGHT, 28, anchor_x="center",
                              bold=True)
 
        # Controls hint (fades after wave 1)
        if self.wave == 1:
            arcade.draw_text(
                "WASD Move  |  LMB Melee  |  E Ranged Throw  |  RMB Ability  |  1/2/3 Switch  |  I Stats",
                sx + SCREEN_W/2, sy + 6,
                (160, 140, 100, 200), 11, anchor_x="center")
 
    def _draw_game_over(self, cl, cb):
        sx, sy = cl, cb
        arcade.draw_rectangle_filled(sx + SCREEN_W/2, sy + SCREEN_H/2,
                                      SCREEN_W, SCREEN_H, (0, 0, 0, 170))
        arcade.draw_text("YOU HAVE FALLEN",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 + 60,
                          COL_RED_CHAOS, 48, anchor_x="center", bold=True)
        arcade.draw_text("The forces of Chaos have prevailed…",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 + 10,
                          COL_SAND, 20, anchor_x="center")
        arcade.draw_text(f"Waves survived: {self.wave - 1}   "
                          f"Enemies slain: {self.enemies_killed}",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 - 30,
                          COL_SAND, 16, anchor_x="center")
        arcade.draw_text("Press ESC to return to Menu",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 - 80,
                          COL_GOLD, 18, anchor_x="center")
 
    def _draw_victory(self, cl, cb):
        sx, sy = cl, cb
        arcade.draw_rectangle_filled(sx + SCREEN_W/2, sy + SCREEN_H/2,
                                      SCREEN_W, SCREEN_H, (0, 0, 0, 170))
        arcade.draw_text("MA'AT RESTORED",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 + 70,
                          COL_GOLD_LIGHT, 52, anchor_x="center", bold=True)
        arcade.draw_text("You have defeated the servants of Chaos!",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 + 20,
                          COL_SAND, 20, anchor_x="center")
        arcade.draw_text(f"Final Level: {self.player.stats.level}   "
                          f"Enemies slain: {self.enemies_killed}",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 - 20,
                          COL_GOLD, 18, anchor_x="center")
        arcade.draw_text("Press ESC to return to Menu",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 - 80,
                          COL_SAND, 16, anchor_x="center")
 
    def _draw_pause(self, cl, cb):
        sx, sy = cl, cb
        arcade.draw_rectangle_filled(sx + SCREEN_W/2, sy + SCREEN_H/2,
                                      SCREEN_W, SCREEN_H, (0, 0, 0, 140))
        arcade.draw_text("PAUSED",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 + 20,
                          COL_GOLD, 50, anchor_x="center", bold=True)
        arcade.draw_text("ESC to resume  |  Q to quit",
                          sx + SCREEN_W/2, sy + SCREEN_H/2 - 40,
                          COL_SAND, 18, anchor_x="center")
 
    # ── Input ─────────────────────────────────
    def on_key_press(self, key, mod):
        self.keys_down.add(key)
        if key == arcade.key.ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state in (GameState.PAUSED,
                                GameState.GAME_OVER,
                                GameState.VICTORY):
                main_menu = MainMenuView()
                self.window.show_view(main_menu)
        elif key == arcade.key.I:
            self.stats_panel.toggle()
        elif key == arcade.key.KEY_1:
            self.player.selected_ability = 0
        elif key == arcade.key.KEY_2:
            self.player.selected_ability = 1
        elif key == arcade.key.KEY_3:
            self.player.selected_ability = 2
        elif key == arcade.key.E:
            self._do_ranged_throw()
        elif key == arcade.key.Q and self.state == GameState.PAUSED:
            main_menu = MainMenuView()
            self.window.show_view(main_menu)
 
    def on_key_release(self, key, mod):
        self.keys_down.discard(key)
 
    def on_mouse_motion(self, x, y, dx, dy):
        # Facing angle toward cursor (world coords)
        wx = x + self.cam.position[0] - SCREEN_W / 2
        wy = y + self.cam.position[1] - SCREEN_H / 2
        self.player.facing_angle = math.atan2(wy - self.player.y,
                                               wx - self.player.x)
 
    def on_mouse_press(self, x, y, button, mod):
        if self.state != GameState.PLAYING:
            return
 
        wx = x + self.cam.position[0] - SCREEN_W / 2
        wy = y + self.cam.position[1] - SCREEN_H / 2
        angle = math.atan2(wy - self.player.y, wx - self.player.x)
 
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._do_melee(wx, wy)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self._use_ability(angle)
 
    def _do_ranged_throw(self):
        """Free ranged attack toward cursor — no mana cost, shares attack cooldown."""
        if self.player.attack_timer > 0:
            return
        self.player.attack_timer = ATTACK_COOLDOWN * 1.2
        self.player.attack_flash = 0.12
        dmg = max(4, 6 + self.player.stats.strength // 3)
        self.projectiles.append(Projectile(
            self.player.x, self.player.y,
            self.player.facing_angle,
            PROJ_SPEED * 0.85,
            dmg, COL_GOLD,
            radius=6, from_player=True
        ))
        self.particles += spawn_hit_particles(
            self.player.x, self.player.y, COL_GOLD, 4)
 
    def _do_melee(self, wx, wy):
        if self.player.attack_timer > 0:
            return
        self.player.attack_timer = ATTACK_COOLDOWN
        self.player.attack_flash = 0.18
 
        # Hit enemies in arc
        for e in self.enemies:
            if not e.alive:
                continue
            dist = math.hypot(e.x - self.player.x, e.y - self.player.y)
            if dist <= ATTACK_RANGE + e.size:
                dmg_base = 12 + self.player.stats.strength
                if self.player.empowered_hits > 0:
                    dmg_base = int(dmg_base * 1.8)
                    self.player.empowered_hits -= 1
                dmg = calc_damage(self.player.stats.strength, dmg_base,
                                   e.armor)
                actual = e.take_damage(dmg)
                self.floats.append(
                    FloatingText(str(actual), e.x, e.y + 20,
                                  COL_GOLD_LIGHT))
                self.particles += spawn_hit_particles(e.x, e.y, COL_GOLD, 8)
                e.state = "attack"
 
    def _use_ability(self, angle):
        if self.state != GameState.PLAYING:
            return
        ab = self.player.ability
        s  = self.player.stats
        if not ab.is_ready():
            return
        if s.mana < ab.mana_cost:
            self.floats.append(
                FloatingText("No Mana!", self.player.x,
                              self.player.y + 30, COL_MANA_BLUE, 14))
            return
 
        s.mana -= ab.mana_cost
        ab.use()
 
        at = ab.ability_type
 
        if at == AbilityType.KHEPRI_STRIKE:
            # Powerful melee burst
            self.particles += spawn_hit_particles(
                self.player.x, self.player.y, COL_SCARAB, 16)
            for e in self.enemies:
                if not e.alive:
                    continue
                dist = math.hypot(e.x - self.player.x, e.y - self.player.y)
                if dist <= ATTACK_RANGE * 1.6 + e.size:
                    dmg = calc_damage(s.strength,
                                       int((12 + s.strength) * 2.5), e.armor)
                    actual = e.take_damage(dmg)
                    self.floats.append(
                        FloatingText(f"⚡{actual}", e.x, e.y + 24,
                                      COL_SCARAB, 18))
                    self.particles += spawn_hit_particles(
                        e.x, e.y, COL_SCARAB, 12)
 
        elif at == AbilityType.RA_BEAM:
            # Piercing solar beam projectile
            for spread in [-0.12, 0, 0.12]:
                dmg = int((15 + s.wisdom * 2) * 1.0)
                self.projectiles.append(Projectile(
                    self.player.x, self.player.y,
                    angle + spread,
                    PROJ_SPEED * 1.2,
                    dmg, COL_GOLD_LIGHT,
                    radius=8, from_player=True,
                    ability_type=at
                ))
            self.particles += spawn_hit_particles(
                self.player.x, self.player.y, COL_GOLD_LIGHT, 12)
 
        elif at == AbilityType.HORUS_SHIELD:
            shield_amount = 40 + s.wisdom * 2
            self.player.shield_hp = shield_amount
            self.floats.append(
                FloatingText(f"SHIELD +{shield_amount}",
                              self.player.x, self.player.y + 40,
                              COL_LAPIS, 16))
            self.particles += spawn_hit_particles(
                self.player.x, self.player.y, COL_LAPIS, 20)
 
        elif at == AbilityType.ANUBIS_CURSE:
            # Slow + weaken all visible enemies
            count = 0
            for e in self.enemies:
                if not e.alive:
                    continue
                dist = math.hypot(e.x - self.player.x, e.y - self.player.y)
                if dist < 320:
                    e.stun_timer = 2.0
                    e.speed      = max(20, int(e.speed * 0.5))
                    self.particles += spawn_hit_particles(
                        e.x, e.y, (80, 30, 120), 10)
                    count += 1
            self.floats.append(
                FloatingText(f"CURSED ×{count}",
                              self.player.x, self.player.y + 40,
                              (180, 80, 220), 16))
 
        elif at == AbilityType.THOTH_WISDOM:
            self.player.empowered_hits = 3
            self.floats.append(
                FloatingText("THOTH EMPOWERS",
                              self.player.x, self.player.y + 40,
                              COL_GOLD_LIGHT, 16))
            self.particles += spawn_hit_particles(
                self.player.x, self.player.y, COL_GOLD, 16)
 
    def _walkable(self, x, y) -> bool:
        c = int(x // TILE_SIZE)
        r = int(y // TILE_SIZE)
        if r < 0 or r >= MAP_ROWS or c < 0 or c >= MAP_COLS:
            return False
        return self.grid[r][c] in WALKABLE
 
# ─────────────────────────────────────────────
#  Character Select
# ─────────────────────────────────────────────
class CharSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected = 0
        self.names    = list(CHARACTERS.keys())
 
    def on_draw(self):
        self.clear()
        arcade.draw_rectangle_filled(SCREEN_W/2, SCREEN_H/2,
                                      SCREEN_W, SCREEN_H, (10, 8, 5))
        # Title
        arcade.draw_text("CHOOSE YOUR WARRIOR",
                          SCREEN_W/2, SCREEN_H - 70,
                          COL_GOLD_LIGHT, 36, anchor_x="center", bold=True)
        arcade.draw_line(80, SCREEN_H - 90,
                          SCREEN_W - 80, SCREEN_H - 90,
                          COL_HIEROGLYPH, 2)
 
        # Cards
        card_w = 280
        spacing = 60
        total_w = len(self.names) * card_w + (len(self.names)-1) * spacing
        start_x = (SCREEN_W - total_w) / 2
 
        for i, name in enumerate(self.names):
            data    = CHARACTERS[name]
            cx      = start_x + i * (card_w + spacing) + card_w / 2
            cy      = SCREEN_H / 2
            is_sel  = (i == self.selected)
 
            # Card bg
            bg = COL_LAPIS if is_sel else (20, 15, 8)
            arcade.draw_rectangle_filled(cx, cy, card_w, 360, bg)
            arcade.draw_rectangle_outline(cx, cy, card_w, 360,
                                           COL_GOLD if is_sel else (60,45,20),
                                           3 if is_sel else 1)
            # Gold corner dots
            for dx_, dy_ in [(-1,-1),(1,-1),(-1,1),(1,1)]:
                arcade.draw_circle_filled(cx + dx_*138, cy + dy_*178,
                                           4, COL_GOLD)
 
            # Character avatar
            col = data["color"]
            arcade.draw_circle_filled(cx, cy + 70, 44, col)
            arcade.draw_circle_outline(cx, cy + 70, 44, COL_GOLD, 2)
            # Nemes stripe
            arcade.draw_line(cx-36, cy+90, cx-44, cy+50, COL_GOLD, 2)
            arcade.draw_line(cx+36, cy+90, cx+44, cy+50, COL_GOLD, 2)
            # Eyes
            arcade.draw_circle_filled(cx-10, cy+74, 4, COL_BLACK)
            arcade.draw_circle_filled(cx+10, cy+74, 4, COL_BLACK)
 
            # Name
            arcade.draw_text(name,
                              cx, cy + 22, COL_GOLD_LIGHT, 20,
                              anchor_x="center", bold=True)
            # Description
            desc = data["desc"]
            words = desc.split()
            line, lines = "", []
            for w in words:
                test = line + w + " "
                if len(test) > 30:
                    lines.append(line.strip()); line = w + " "
                else:
                    line = test
            lines.append(line.strip())
            for j, l in enumerate(lines):
                arcade.draw_text(l, cx, cy - 10 - j * 18,
                                  COL_SAND, 12, anchor_x="center")
 
            # Stats preview
            s = data["stats"]
            sy_start = cy - 100
            for label, val in [("STR", s.strength), ("DEX", s.dexterity),
                                ("WIS", s.wisdom),  ("ARM", s.armor),
                                ("HP",  s.max_hp)]:
                arcade.draw_text(f"{label}",
                                  cx - 100, sy_start, COL_SAND, 11)
                bar_len = int(val / 20 * 80)
                arcade.draw_rectangle_filled(cx - 60 + bar_len/2,
                                              sy_start + 6,
                                              bar_len, 8, col)
                arcade.draw_rectangle_outline(cx - 60 + 40,
                                               sy_start + 6, 80, 8,
                                               (60, 45, 20), 1)
                arcade.draw_text(str(val),
                                  cx + 36, sy_start, COL_GOLD, 11)
                sy_start -= 22
 
        # Navigation
        arcade.draw_text("◄ ► Arrow Keys to select   ENTER to confirm",
                          SCREEN_W/2, 40,
                          COL_SAND, 15, anchor_x="center")
 
    def on_key_press(self, key, mod):
        if key in (arcade.key.RIGHT, arcade.key.D):
            self.selected = (self.selected + 1) % len(self.names)
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.selected = (self.selected - 1) % len(self.names)
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            game = GameView(self.names[self.selected])
            self.window.show_view(game)
        elif key == arcade.key.ESCAPE:
            menu = MainMenuView()
            self.window.show_view(menu)
 
# ─────────────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────────────
class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self._t = 0.0
 
    def on_update(self, dt):
        self._t += dt
 
    def on_draw(self):
        self.clear()
        # Animated sand background
        for i in range(0, SCREEN_W, 60):
            for j in range(0, SCREEN_H, 60):
                shade = int(180 + 20 * math.sin((i + j) * 0.03 + self._t))
                arcade.draw_rectangle_filled(i+30, j+30, 60, 60,
                                              (shade, int(shade*0.87), int(shade*0.52)))
 
        # Top hieroglyph strip
        arcade.draw_rectangle_filled(SCREEN_W/2, SCREEN_H - 30,
                                      SCREEN_W, 60, (15, 10, 5, 220))
        for i in range(40, SCREEN_W, 60):
            glyph = random.choice(["𓂀","𓃭","𓅓","𓆣","𓇋","𓊽","𓏤","𓐍"])
            arcade.draw_text(glyph, i, SCREEN_H - 45,
                              (*COL_GOLD, 180), 20)
 
        # Title panel
        arcade.draw_rectangle_filled(SCREEN_W/2, SCREEN_H/2 + 60,
                                      700, 160, (10, 6, 2, 220))
        arcade.draw_rectangle_outline(SCREEN_W/2, SCREEN_H/2 + 60,
                                       700, 160, COL_GOLD, 3)
 
        # Animated scarab
        sx = SCREEN_W/2 + math.sin(self._t * 1.5) * 8
        arcade.draw_circle_filled(sx, SCREEN_H/2 + 150, 20, COL_SCARAB)
        arcade.draw_line(sx-20, SCREEN_H/2+150, sx-36, SCREEN_H/2+138,
                          COL_SCARAB, 3)
        arcade.draw_line(sx+20, SCREEN_H/2+150, sx+36, SCREEN_H/2+138,
                          COL_SCARAB, 3)
 
        arcade.draw_text("GODS  OF  KEMET",
                          SCREEN_W/2, SCREEN_H/2 + 90,
                          COL_GOLD_LIGHT, 54, anchor_x="center", bold=True)
        arcade.draw_text("An Egyptian Mythology ARPG",
                          SCREEN_W/2, SCREEN_H/2 + 44,
                          COL_SAND, 22, anchor_x="center")
 
        # Menu options
        opts = [("ENTER  — Begin Your Journey", COL_GOLD_LIGHT),
                ("ESC    — Quit",               COL_SAND)]
        for i, (text, col) in enumerate(opts):
            pulse = 0.85 + 0.15 * math.sin(self._t * 2.5 + i)
            r, g, b = [int(c * pulse) for c in col[:3]]
            arcade.draw_text(text,
                              SCREEN_W/2, SCREEN_H/2 - 40 - i * 50,
                              (r, g, b), 24, anchor_x="center", bold=True)
 
        # Lore blurb
        arcade.draw_text(
            "The servants of Chaos walk the desert sands.\n"
            "Ra's light grows dim. Ma'at's balance trembles.\n"
            "A warrior blessed by the gods must restore order.",
            SCREEN_W/2, 100,
            COL_HIEROGLYPH, 14, anchor_x="center",
            multiline=True, width=600
        )
 
        # Bottom strip
        arcade.draw_rectangle_filled(SCREEN_W/2, 28,
                                      SCREEN_W, 56, (15, 10, 5, 200))
        arcade.draw_text("CSE 310 Module Project  |  Python Arcade  |  Egyptian ARPG",
                          SCREEN_W/2, 16,
                          (100, 80, 40), 11, anchor_x="center")
 
    def on_key_press(self, key, mod):
        if key == arcade.key.RETURN or key == arcade.key.ENTER:
            char_select = CharSelectView()
            self.window.show_view(char_select)
        elif key == arcade.key.ESCAPE:
            arcade.exit()
 
# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def main():
    window = arcade.Window(SCREEN_W, SCREEN_H, TITLE, resizable=False)
    menu   = MainMenuView()
    window.show_view(menu)
    arcade.run()
 
if __name__ == "__main__":
    main()